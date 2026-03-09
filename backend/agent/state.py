from typing import TypedDict, Annotated, List, Optional
import operator

class TripState(TypedDict):
    """
    Trip Agent (VTP) 的 LangGraph 核心状态
    包含 A2A 协商必须的防死循环字段与显式约束反馈字段。
    """
    # 用户最初的需求文本记录
    user_query: str
    
    # 存长期记忆的地方（来自 ChromaDB 的分析）
    user_preferences: str

    # 对话历史，或者中间的步骤流
    # 使用 Annotated 和 add 保证可以做追加而不是替换
    messages: Annotated[List[str], operator.add]
    
    # Planner 当前给出的方案文本/JSON串
    current_plan: Optional[str]
    
    # 防死循环计数器
    negotiation_rounds: int
    
    # 显式约束注入（Explicit Constraint Injection）: 
    # Budget 驳回时填写的具体问题，如 "Hotel in plan costs 500, but daily limit is 300"
    feedback: Optional[str]
    
    # 是否协商成功标志
    is_approved: bool
    
    # 最终结果
    final_output: Optional[str]
