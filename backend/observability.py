import os
import logging
from langsmith import traceable

# 配置基础日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("trip_agent")

def init_tracing():
    """
    初始化 LangSmith 监控配置与可观测性
    确保相关 tracing 环境变量已设置。
    """
    os.environ["LANGCHAIN_TRACING_V2"] = os.environ.get("LANGCHAIN_TRACING_V2", "true")
    os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "trip_agent_vtp")
    
    if "LANGCHAIN_API_KEY" not in os.environ:
        logger.warning("LANGCHAIN_API_KEY not found in environment. Tracing will be disabled or fail.")
    else:
        logger.info(f"LangSmith tracing initialized for project: {os.environ['LANGCHAIN_PROJECT']}")

# 导出 trace_node 装饰器供 LangGraph 各节点 (如 Planner, Budget) 直接使用
trace_node = traceable
