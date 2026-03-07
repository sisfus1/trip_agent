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

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    标准的 WebSocket 文本接口
    已配置基础的心跳响应机制防止 HuggingFace 代理层超时断连。
    """
    await websocket.accept()
    logger.info("Chat WebSocket connected.")
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
                
            query = payload.get("query", "")
            api_key = payload.get("api_key", "")
            
            if not query or not api_key:
                await websocket.send_text("Missing query or api_key in payload.")
                continue
                
            # 动态注入本次请求的 API Key，使得 nodes 中 get_llm 能读取
            os.environ["GEMINI_API_KEY"] = api_key
            
            logger.info(f"Received query: {query}")
            await websocket.send_text('[System]: LangGraph A2A engine started... 🚀')
            
            # 初始化状态机跑 LangGraph
            from backend.agent.graph import app as a2a_graph
            
            initial_state = {
                "user_query": query,
                "messages": [f"User: {query}"],
                "current_plan": None,
                "negotiation_rounds": 0,
                "feedback": None,
                "is_approved": False,
                "final_output": None
            }
            
            # 流式获取 graph 执行中的每个节点的步骤输出
            for step_data in a2a_graph.stream(initial_state):
                for node_name, state_update in step_data.items():
                    # 推送流转信息
                    await websocket.send_text(f"--- Node [{node_name.upper()}] Executed ---")
                    
                    if "messages" in state_update:
                        for msg in state_update["messages"]:
                            await websocket.send_text(f"💡 {msg}")
                    
                    if "feedback" in state_update and state_update["feedback"]:
                        await websocket.send_text(f"⚠️ [Constraint Check Failed]: {state_update['feedback']}")
                    
                    # 如果达到了最终输出，给用户最终展示
                    if "final_output" in state_update and state_update["final_output"]:
                        await websocket.send_text(f"\n🎉 [Final Travel Plan Generated]\n\n{state_update['final_output']}")
                        
            await websocket.send_text('[System]: Process finished. ✅')
            
    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected.")
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
