import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# 初始化日志与跟踪 (可选)
try:
    from backend.observability import init_tracing
    init_tracing()
except ImportError:
    pass

logger = logging.getLogger("trip_agent")

app = FastAPI(title="Trip Agent API")

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
    try:
        while True:
            # 接收前端消息
            data = await websocket.receive_text()
            import json
            import os
            
            # Keep-Alive
            if data == '{"type":"ping"}':
                await websocket.send_text('{"type":"pong"}')
                continue
                
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text("Invalid payload format. Expected JSON.")
                continue
                
            # 从 payload 中剥离 api_key 并设置为当前线程/请求的环境变量！
            api_key = payload.get("api_key")
            query = payload.get("query")
            
            if not api_key:
                await websocket.send_text('⚠️ [System]: API Key was not provided. Please enter your API Key.')
                continue
                
            os.environ["DEEPSEEK_API_KEY"] = api_key # 使得 nodes 中 get_llm 能读取
            os.environ["GEMINI_API_KEY"] = api_key # 兼容旧版，如果需要
            
            if not query:
                await websocket.send_text("Missing query in payload.")
                continue
            
            logger.info(f"Received query: {query}")
            await websocket.send_text('[System]: LangGraph A2A engine started... 🚀')
            
            # 初始化状态机跑 LangGraph
            from backend.agent.graph import app as a2a_graph
            
            # 重用之前保存的对话状态，清空由于上一次妥协导致的状态锁定
            current_state = chat_sessions[session_id]
            current_state["user_query"] = query
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
                        await websocket.send_text(f"--- Node [{node_name.upper()}] Executed ---")
                        
                        if "messages" in state_update:
                            for msg in state_update["messages"]:
                                await websocket.send_text(f"💡 {msg}")
                        
                        if "feedback" in state_update and state_update["feedback"]:
                            await websocket.send_text(f"⚠️ [Constraint Check Failed]: {state_update['feedback']}")
                        
                        # 如果达到了最终输出，给用户最终展示
                        if "final_output" in state_update and state_update["final_output"]:
                            await websocket.send_text(f"\n🎉 [Final Travel Plan Generated] {state_update['final_output']}")
                
                # 保存最新的状态回写给会话对象，包含历史消息，使得下一次聊天保持记忆
                if final_state:
                     chat_sessions[session_id].update(final_state)
                     
                await websocket.send_text('[System]: Process finished. ✅')
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Graph execution failed: {error_msg}")
                if "403" in error_msg or "API_KEY_INVALID" in error_msg or "billing" in error_msg.lower():
                    await websocket.send_text(f"❌ [API Key Error]: It seems your Gemini API key is invalid or lacks billing setup. Details: {error_msg}")
                else:
                    await websocket.send_text(f"❌ [System Error]: An unexpected error occurred during reasoning. Details: {error_msg}")
            
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

# 挂载前端静态文件 (必须在所有 API 路由之后)
import os
from fastapi.staticfiles import StaticFiles

# 获取 frontend/dist 的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(os.path.dirname(current_dir), "frontend", "dist")

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    logger.warning(f"Static directory {static_dir} not found. Ensure frontend is built before deploying.")
