import os
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from backend.agent.state import TripState

# 注入 observability (如果是生产则配置 LANGCHAIN_TRACING_V2=true)
try:
    from backend.observability import trace_node
except ImportError:
    # Fallback to no-op decorator
    def trace_node(func): return func

class BudgetDecision(BaseModel):
    """用于强制 Budget 节点输出结构化判断和 Feedback"""
    is_approved: bool = Field(description="Whether the travel plan is within a reasonable budget and logical limits.")
    feedback: str = Field(description="If not approved, the explicit reason why (e.g., 'Hotel is $50 over limit'). If approved, a short confirmation.")

def get_llm():
    """获取 Gemini 模型实例，必须确保环境变量中存在 GEMINI_API_KEY"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment!")
        
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        google_api_key=api_key
    )

@trace_node
def node_planner(state: TripState) -> Dict[str, Any]:
    """
    Planner 节点:
    负责根据 user_query 生成初步规划。
    强制逻辑：发现状态内有 feedback 时，生成必然需基于该反馈进行（Explicit Constraint Injection）。
    """
    user_query = state.get("user_query")
    feedback = state.get("feedback")
    
    print(f"\n[Planner] Generating plan for: {user_query}")
    
    # 构造能够注入约束的 Prompt
    system_prompt = "You are a senior travel planner. Draft a comprehensive daily itinerary and estimate the total costs."
    if feedback:
        print(f"[Planner] ⚠️ Received constraint feedack: {feedback}. Adjusting plan...")
        system_prompt += f"\n\nCRITICAL FEEDBACK FROM BUDGET INSPECTOR YOU MUST SATISFY: {feedback}"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "User request: {query}")
    ])
    
    try:
        llm = get_llm()
        chain = prompt | llm
        response = chain.invoke({"query": user_query})
        new_plan = response.content
        
        return {
            "current_plan": new_plan,
            "messages": [f"Planner proposed a plan (Snippet: {new_plan[:50]}...)"],
            "feedback": None # 只要执行 Planner，证明发起了一次新提案，清空上一轮的拒绝 feedback
        }
    except Exception as e:
        return {"messages": [f"Planner encountered an error: {e}"]}

@trace_node
def node_budget_inspector(state: TripState) -> Dict[str, Any]:
    """
    Budget 节点:
    负责审核 current_plan 是否超标。
    如果拒接，则填入详细的 feedback 给出超支数额。
    """
    plan = state.get("current_plan", "")
    rounds = state.get("negotiation_rounds", 0)
    
    print(f"[Budget] Inspecting plan (Round {rounds})...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict Budget Inspector for a travel agency. Analyze the provided travel plan. "
                   "If it seems unreasonably expensive or lacking cost details for a standard traveler, reject it and provide precise feedback on what to cut. "
                   "If it is reasonable, approve it."),
        ("human", "Plan to review:\n{plan}")
    ])
    
    try:
        llm = get_llm()
        # 强制 Gemini 结构化输出
        chain = prompt | llm.with_structured_output(schema=BudgetDecision)
        decision: BudgetDecision = chain.invoke({"plan": plan})
        
        if not decision.is_approved:
            return {
                "is_approved": False,
                "feedback": decision.feedback,
                "negotiation_rounds": rounds + 1,
                "messages": [f"Budget REJECTED plan. Reason: {decision.feedback}"]
            }
        
        return {
            "is_approved": True,
            "final_output": f"Final Approved Plan:\n\n{plan}",
            "messages": [f"Budget APPROVED the plan. Final thought: {decision.feedback}"]
        }
    except Exception as e:
        return {"messages": [f"Budget Inspector encountered an error: {e}"]}

@trace_node
def node_fallback(state: TripState) -> Dict[str, Any]:
    """
    Fallback 节点 (防死锁妥协节点):
    当 negotiation_rounds 达到阈值时强制触发，直接给出一个可行的通用低成本方案。
    """
    print("[Fallback] 🛑 Max rounds reached! Forcing a compromise plan.")
    compromise_plan = "The system could not reach an agreement within the maximum negotiation rounds. Please consider summarizing your priorities (e.g., lower hotel class, fewer paid attractions) and requesting a more budget-friendly baseline."
    return {
        "is_approved": True,
        "current_plan": compromise_plan,
        "final_output": f"Forced Compromise Result:\n\n{compromise_plan}",
        "messages": ["System forced a fallback compromise plan due to infinite loop prevention."]
    }
