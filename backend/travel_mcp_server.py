import json
import logging
from typing import Dict, Any

# mock 模拟实时排队与价格数据
MOCK_DATA = {
    "disneyland": {"queue_minutes": 120, "ticket_price_usd": 150},
    "universal_studios": {"queue_minutes": 85, "ticket_price_usd": 130},
    "eiffel_tower": {"queue_minutes": 45, "ticket_price_usd": 30},
    "louvre_museum": {"queue_minutes": 60, "ticket_price_usd": 20}
}

class TravelMCPServer:
    """
    轻量级的 Travel MCP Server 模拟器
    提供 `get_scenic_data` 工具供大模型调用
    遵循标准输入输出 (stdio) 等接口的思想提供数据层抽象
    """

    def __init__(self):
        self.logger = logging.getLogger("trip_agent.mcp")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """执行声明的工具并返回 JSON 字符串结果"""
        if tool_name == "get_scenic_data":
            location_id = arguments.get("location_id", "").lower()
            if location_id in MOCK_DATA:
                return json.dumps({
                    "success": True, 
                    "location_id": location_id,
                    "data": MOCK_DATA[location_id]
                })
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Location {location_id} not found."
                })
        
        return json.dumps({"success": False, "error": f"Tool {tool_name} not found."})

    def get_supported_tools(self) -> list:
        return [
            {
                "name": "get_scenic_data",
                "description": "Fetch real-time queue minutes and ticket prices for a given location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location_id": {
                            "type": "string",
                            "description": "The ID of the location (e.g., 'disneyland')."
                        }
                    },
                    "required": ["location_id"]
                }
            }
        ]

# 简单的实例化模拟
# 在真实 MCP 场景下，会使用 mcp-server 类似框架，通过 stdio/sse 提供给 LangChain
mcp_server = TravelMCPServer()
