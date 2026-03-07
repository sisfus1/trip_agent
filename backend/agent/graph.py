from langgraph.graph import StateGraph, END
from backend.agent.state import TripState
from backend.agent.nodes import node_planner, node_budget_inspector, node_fallback

MAX_ROUNDS = 3

def route_after_budget(state: TripState) -> str:
    """
    Conditional Edge: 决定 Budget 计算之后下一步去哪。
    """
    is_approved = state.get("is_approved", False)
    rounds = state.get("negotiation_rounds", 0)
    
    if is_approved:
        return "end" # 批准则结束
        
    if rounds >= MAX_ROUNDS:
        # 防死循环拦截：如果大于等于最大协商轮次仍未批准，强制走妥协节点
        return "fallback"
        
    # 继续返工 Planner
    return "planner"

def build_workflow() -> StateGraph:
    """构建 VTP A2A 协商机工作流"""
    
    workflow = StateGraph(TripState)
    
    # 注册节点
    workflow.add_node("planner", node_planner)
    workflow.add_node("budget", node_budget_inspector)
    workflow.add_node("fallback", node_fallback)
    
    # 设置入口
    workflow.set_entry_point("planner")
    
    # 定义常规线性执行: planner -> budget
    workflow.add_edge("planner", "budget")
    
    # 定义条件流转：Budget -> 返回 Planner，或者到达 Fallback，或者结束
    workflow.add_conditional_edges(
        "budget",
        route_after_budget,
        {
            "planner": "planner",
            "fallback": "fallback",
            "end": END
        }
    )
    
    # 定义强制妥协：Fallback -> 结束
    workflow.add_edge("fallback", END)
    
    return workflow.compile()

# 向外暴露 graph
app = build_workflow()
