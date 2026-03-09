import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend import models
from backend.database import engine
from backend.auth import auth_router, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

# 确保加载所有环境变量 (包含静态的 DEEPSEEK_API_KEY 等)
load_dotenv()

# 初始化数据库表 (如果不存在)
models.Base.metadata.create_all(bind=engine)

# 初始化日志与跟踪 (可选)
try:
    from backend.observability import init_tracing
    init_tracing()
except ImportError:
    pass

logger = logging.getLogger("trip_agent")

app = FastAPI(title="Trip Agent SaaS API")

# 挂载路由
app.include_router(auth_router)

from backend.sessions import session_router
app.include_router(session_router)

# 配置 CORS 中间件，适配当前开发环境或 HuggingFace Spaces 的跨域诉求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产中建议缩小范围
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局会话状态缓存 (针对单用户快速 Demo)
# 在真实的生产环境中应使用 Checkpointer (如 MemorySaver 或 PostgresSaver) 以及 thread_id
chat_sessions = {}

async def extract_and_save_preference(query: str, session_id: str, user_id: int):
    """后台任务：使用小号 LLM 调用分析用户的输入，提取长期偏好并存入 ChromaDB"""
    try:
        from backend.agent.nodes import get_llm
        from backend.memory_manager import memory_manager
        import time
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Analyze the user's travel query and extract any LONG-TERM travel preferences (e.g., allergies, hotel class, preferred airlines, travel style). Output ONLY the extracted preference as a concise sentence. If there are no clear persistent preferences (e.g. just a specific destination request), output EXACTLY the word 'NONE'."),
            ("human", "{query}")
        ])
        llm = get_llm()
        chain = prompt | llm
        
        # 使用 ainvoke 避免阻塞 asyncio loop
        res = await chain.ainvoke({"query": query})
        pref = res.content.strip()
        
        if pref and pref != "NONE" and "NONE" not in pref:
            doc_id = f"pref_{session_id}_{int(time.time())}"
            # 存入对应 user_id 的记忆
            memory_manager.add_memory(doc_id=doc_id, text=pref, user_id=user_id, metadata={"source": "auto_extraction"})
            logger.info(f"[Persistent Memory] Extracted & Saved new preference: {pref} for User: {user_id}")
    except Exception as e:
        logger.error(f"[Persistent Memory] Extraction failed: {e}")

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    标准的 WebSocket 文本接口
    已配置基础的心跳响应机制防止 HuggingFace 代理层超时断连。
    """
    await websocket.accept()
    session_id = id(websocket)
    chat_sessions[session_id] = {
        "user_query": "",
        "messages": [],
        "current_plan": None,
        "negotiation_rounds": 0,
        "feedback": None,
        "is_approved": False,
        "final_output": None
    }
    logger.info(f"Chat WebSocket connected. Session: {session_id}")
    async def send_structured(msg: str, cards: list = None):
        """统一发送结构化 JSON payload"""
        await websocket.send_text(json.dumps({"message": msg, "cards": cards or []}, ensure_ascii=False))

    try:
        while True:
            data = await websocket.receive_text()
            
            # Keep-Alive
            if data == '{"type":"ping"}':
                await websocket.send_text('{"type":"pong"}')
                continue
                
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await send_structured("Invalid payload format. Expected JSON.")
                continue
                
            # 从 payload 中剥离 JWT Token 和 查询内容
            token = payload.get("token")
            query = payload.get("query")
            is_persistent = payload.get("is_persistent", True)  # 默认长期记忆
            
            if not token:
                await send_structured('Access Token was not provided. Please log in first.')
                continue
                
            # JWT 验证获取 user_id
            try:
                decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = decoded_payload.get("user_id")
                username = decoded_payload.get("sub")
                if not user_id:
                    raise ValueError("user_id not in token")
            except Exception as e:
                await send_structured(f'Authentication Error: Invalid token. {e}')
                continue
            
            if not query:
                await send_structured("Missing query in payload.")
                continue
            
            logger.info(f"Received query from user {username} (ID: {user_id}), Persistent: {is_persistent}: {query}")
            await send_structured(f'Welcome {username}! LangGraph A2A engine started...')
            
            # 初始化状态机跑 LangGraph
            from backend.agent.graph import app as a2a_graph
            from backend.memory_manager import memory_manager
            
            long_term_prefs = ""
            if is_persistent:
                # 1. 仅当持久化聊天时检索长期记忆 (ChromaDB)
                try:
                    # 传入 user_id 确保隔离其他租户的向量
                    results = memory_manager.search_memory(query, user_id=user_id, n_results=2)
                    docs = results.get("documents", [[]])[0]
                    if docs:
                        long_term_prefs = " | ".join(docs)
                        await send_structured(f"Persistent Memory Retrieved: {long_term_prefs}")
                except Exception as e:
                    logger.error(f"Memory search error: {e}")
            
            # 重用之前保存的对话状态，清空由于上一次妥协导致的状态锁定
            current_state = chat_sessions[session_id]
            current_state["user_query"] = query
            current_state["user_preferences"] = long_term_prefs
            current_state["messages"].append(f"User: {query}")
            current_state["negotiation_rounds"] = 0
            current_state["feedback"] = None
            current_state["is_approved"] = False
            current_state["final_output"] = None
            
            # 流式获取 graph 执行中的每个节点的步骤输出
            try:
                # 记录这轮结束后的最终状态
                final_state = None
                
                for step_data in a2a_graph.stream(current_state):
                    for node_name, state_update in step_data.items():
                        final_state = state_update
                        # 推送流转信息
                        await send_structured(f"Node [{node_name.upper()}] executed.")
                        
                        if "messages" in state_update:
                            for msg in state_update["messages"]:
                                await send_structured(msg)
                        
                        if "feedback" in state_update and state_update["feedback"]:
                            await send_structured(f"Constraint Check Failed: {state_update['feedback']}")
                        
                        # 如果达到了最终输出，给用户最终展示（以纯 JSON 形式发送供前端渲染 Cards）
                        if "final_output" in state_update and state_update["final_output"]:
                            # final_output 是 planner 产出的 JSON 字符串，直接转发
                            try:
                                parsed = json.loads(state_update["final_output"])
                                await websocket.send_text(json.dumps(parsed, ensure_ascii=False))
                            except (json.JSONDecodeError, TypeError):
                                await send_structured(state_update["final_output"])
                
                # 保存最新的状态回写给会话对象，包含历史消息，使得下一次聊天保持记忆
                if final_state:
                     chat_sessions[session_id].update(final_state)
                     
                await send_structured('Process finished.')
                
                if is_persistent:
                    # 2. 异步触发偏好抽取与保存 (注意传入 user_id 以便 ChromaDB 进行安全隔离)
                    asyncio.create_task(extract_and_save_preference(query, str(session_id), user_id))

                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Graph execution failed: {error_msg}")
                if "403" in error_msg or "API_KEY_INVALID" in error_msg or "billing" in error_msg.lower():
                    await send_structured(f"API Key Error: It seems your API key is invalid or lacks billing setup. Details: {error_msg}")
                else:
                    await send_structured(f"System Error: An unexpected error occurred during reasoning. Details: {error_msg}")
            
    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket disconnected for session {session_id}.")
        if session_id in chat_sessions:
             del chat_sessions[session_id]
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")

@app.websocket("/ws/gemini-live")
async def websocket_gemini_live_endpoint(websocket: WebSocket):
    """
    预留给 Gemini Live 的流式语音交互接口
    """
    await websocket.accept()
    logger.info("Gemini Live WebSocket connected.")
    try:
        while True:
            # 接收前端发送的音频数据流
            audio_bytes = await websocket.receive_bytes()
            
            # TODO: 将音频流通过 Gemini SDK 转发至模型，再将 TTS 的流式返回发给客户端
            pass
            
    except WebSocketDisconnect:
        logger.info("Gemini Live WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Gemini Live WebSocket error: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "vtp-backend"}

# 挂载前端静态文件 (仅在生产部署时启用，本地开发由 Vite 服务)
# 重要: root-mount 的 StaticFiles 会拦截 WebSocket 升级请求，开发时必须关闭
import os as _os
from fastapi.staticfiles import StaticFiles

if _os.environ.get("SERVE_STATIC", "0") == "1":
    current_dir = _os.path.dirname(_os.path.abspath(__file__))
    static_dir = _os.path.join(_os.path.dirname(current_dir), "frontend", "dist")
    if _os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    else:
        logger.warning(f"Static directory {static_dir} not found.")

