import sys
import os

# 确保路径能够导入 backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.agent.graph import app

def main():
    print("==================================================")
    print("🚀 开始模拟 VTP A2A 协商流程: Planner vs Budget")
    print("==================================================\n")
    
    initial_state = {
        "user_query": "I want a 7-day luxurious trip to Paris.",
        "messages": ["User: I want a 7-day luxurious trip to Paris."],
        "current_plan": None,
        "negotiation_rounds": 0,
        "feedback": None,
        "is_approved": False,
        "final_output": None
    }
    
    # 使用 LangGraph 的 stream 执行图结构，监控每次节点运转
    for step_data in app.stream(initial_state):
        for node_name, state_update in step_data.items():
            print(f"\n✅ [LangGraph Node Finished]: -> {node_name.upper()}")
            print("-" * 50)
            
            # 打印当前节点的输出变动
            if "messages" in state_update:
                for msg in state_update["messages"]:
                    print(f"💬 Message: {msg}")
                    
            if "feedback" in state_update and state_update["feedback"]:
                print(f"⚠️ Explicit Constraint (Feedback): {state_update['feedback']}")
                
            if "negotiation_rounds" in state_update:
                print(f"🔄 Negotiation Rounds Updated To: {state_update['negotiation_rounds']}")
                
            if "final_output" in state_update:
                print(f"🎯 Final Output Generated: {state_update['final_output']}")
                
            print("-" * 50)

    print("\n==================================================")
    print("🎉 协商流程演示结束！")
    print("==================================================")

if __name__ == "__main__":
    main()
