import os
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
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
    """获取 DeepSeek 模型实例，确保环境变量中存在 DEEPSEEK_API_KEY"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in environment!")
        
    return ChatOpenAI(
        model="deepseek-chat",
        temperature=0.7,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from backend.travel_mcp_server import mcp_server

@tool
def get_scenic_data(location_id: str) -> str:
    """Fetch real-time queue minutes and ticket prices for a given location (e.g., 'disneyland', 'universal_studios', 'eiffel_tower', 'louvre_museum')."""
    return mcp_server.execute_tool("get_scenic_data", {"location_id": location_id})

@trace_node
def node_planner(state: TripState) -> Dict[str, Any]:
    """
    Planner 节点:
    负责根据 user_query 生成初步规划。
    强制逻辑：发现状态内有 feedback 时，生成必然需基于该反馈进行（Explicit Constraint Injection）。
    """
    user_query = state.get("user_query")
    feedback = state.get("feedback")
    user_preferences = state.get("user_preferences", "")
    
    print(f"\n[Planner] Generating plan for: {user_query}")
    
    system_prompt = (
        "You are a senior travel planner. Draft a comprehensive daily itinerary and estimate the total costs.\n"
        "Use the get_scenic_data tool to get real-time queue and price data for locations.\n\n"
        "CRITICAL INSTRUCTION: Your final output MUST be a valid raw JSON object string ONLY (no markdown backticks, no markdown code blocks). "
        "The JSON must have exactly two keys:\n"
        "- 'message': A markdown string containing your detailed itinerary text.\n"
        "- 'cards': An array of up to 3 place objects representing the highlights. Each object must have keys: 'type' (always 'place'), 'name', 'image' (use empty string), 'description' (short), 'tags' (array of strings like ['Family', 'Outdoor']), 'price' (string), and 'rating' (number or string)."
    )
    
    if user_preferences:
        print("[Planner] 🧠 Injecting long-term user preferences from Persistent Memory.")
        system_prompt += f"\n\nLONG-TERM USER PREFERENCES YOU MUST RESPECT: {user_preferences}"
        
    if feedback:
        print(f"[Planner] ⚠️ Received constraint feedack: {feedback}. Adjusting plan...")
        system_prompt += f"\n\nCRITICAL FEEDBACK FROM BUDGET INSPECTOR YOU MUST SATISFY BEFORE APPROVAL: {feedback}"
        
    chat_history = "\n".join(state.get("messages", []))
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Conversation History:\n{history}\n\nLatest Request: {query}")
    ])
    
    llm = get_llm().bind_tools([get_scenic_data])
    messages = prompt.format_prompt(history=chat_history, query=user_query).to_messages()
    
    response = llm.invoke(messages)
    
    # 处理内置工具调用循环
    while response.tool_calls:
        messages.append(response)
        for tc in response.tool_calls:
            print(f"[Planner] 🛠️ Calling tool {tc['name']} with args {tc['args']}")
            if tc['name'] == 'get_scenic_data':
                tool_result = get_scenic_data.invoke(tc['args'])
                messages.append(ToolMessage(content=tool_result, tool_call_id=tc['id']))
        response = llm.invoke(messages)
        
    new_plan = response.content
    
    return {
        "current_plan": new_plan,
        "messages": [f"Planner proposed a plan (Snippet: {new_plan[:50]}...)"],
        "feedback": None # 只要执行 Planner，证明发起了一次新提案，清空上一轮的拒绝 feedback
    }

from langchain_core.output_parsers import JsonOutputParser

@trace_node
def node_budget_inspector(state: TripState) -> Dict[str, Any]:
    """
    Budget 节点:
    负责审核 current_plan 是否超标。
    如果拒接，则填入详细的 feedback 给出超支数额。
    改为使用 JsonOutputParser 以兼容所有大模型（如 DeepSeek 不支持原生的 structured_output 时）。
    """
    plan = state.get("current_plan", "")
    rounds = state.get("negotiation_rounds", 0)
    
    parser = JsonOutputParser(pydantic_object=BudgetDecision)
    chat_history_text = "\n".join(state.get("messages", []))
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Budget Inspector for a travel agency. Analyze the provided travel plan and the user's chat history.\n"
                   "CRITICAL RULE: If the user explicitly stated they want 'luxury' or 'cost is not a concern', DO NOT reject it for being expensive. Approve it.\n"
                   "Otherwise, if it seems unreasonably expensive or lacking logical details for a standard traveler, reject it and provide precise feedback to the Planner on what to fix.\n"
                   "If it is reasonable and matches the user's vibe, approve it.\n\n"
                   "{format_instructions}"),
        ("human", "Conversation History:\n{history}\n\nPlan to review:\n{plan}")
    ])
    
    llm = get_llm()
    chain = prompt | llm | parser
    
    try:
        decision_dict = chain.invoke({
            "history": chat_history_text,
            "plan": plan,
            "format_instructions": parser.get_format_instructions()
        })
        decision = BudgetDecision(**decision_dict)
    except Exception as e:
         return {"messages": [f"Budget Inspector failed to parse JSON: {str(e)}"]}
    
    if not decision.is_approved:
        return {
            "is_approved": False,
            "feedback": decision.feedback,
            "negotiation_rounds": rounds + 1,
            "messages": [f"Budget REJECTED plan. Reason: {decision.feedback}"]
        }
    
    # To ensure final output remains a parsable JSON string
    return {
        "is_approved": True,
        "final_output": plan,
        "messages": [f"Budget APPROVED the plan. Final thought: {decision.feedback}"]
    }

@trace_node
def node_fallback(state: TripState) -> Dict[str, Any]:
    """
    Fallback 节点 (防死锁妥协节点):
    当 negotiation_rounds 达到阈值时强制触发，直接给出一个可行的通用低成本方案。
    """
    print("[Fallback] 🛑 Max rounds reached! Forcing a compromise plan.")
    compromise_plan = "The system could not reach an agreement within the maximum negotiation rounds. Please consider summarizing your priorities (e.g., lower hotel class, fewer paid attractions) and requesting a more budget-friendly baseline."
    import json
    fallback_json = json.dumps({"message": compromise_plan, "cards": []})
    
    return {
        "is_approved": True,
        "current_plan": fallback_json,
        "final_output": fallback_json,
        "messages": ["System forced a fallback compromise plan due to infinite loop prevention."]
    }
