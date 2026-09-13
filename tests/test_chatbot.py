import unittest

from mcp_chatbot_client.chatbot import MCPChatbot, MCPToolRouter


class StubClient:
    def __init__(self):
        self.called = None

    def call_tool(self, tool_name, arguments):
        self.called = (tool_name, arguments)
        return {"content": [{"type": "text", "text": "7"}], "sum": 7}

    def stop(self):
        return None


class StubPlanner:
    def plan_tool_call(self, user_message, tools):
        return {"tool": "calculator.add", "arguments": {"a": 3, "b": 4}, "direct_response": None}

    def compose_final_response(self, user_message, tool_name, tool_arguments, tool_result):
        return f"Result is {tool_result['sum']}"


class StubDirectPlanner:
    def plan_tool_call(self, user_message, tools):
        return {"tool": None, "arguments": {}, "direct_response": "Hello directly"}

    def compose_final_response(self, user_message, tool_name, tool_arguments, tool_result):
        raise AssertionError("Should not be called")


class ChatbotTests(unittest.TestCase):
    def test_uses_tool_when_planner_returns_tool(self):
        client = StubClient()
        router = MCPToolRouter(
            clients={"calculator": client},
            tools={
                "calculator.add": (
                    "calculator",
                    {"name": "calculator.add", "description": "add", "inputSchema": {}},
                )
            },
        )
        bot = MCPChatbot(router=router, planner=StubPlanner())

        output = bot.respond("add numbers")

        self.assertEqual(output, "Result is 7")
        self.assertEqual(client.called, ("calculator.add", {"a": 3, "b": 4}))

    def test_responds_directly_when_no_tool(self):
        router = MCPToolRouter(clients={}, tools={})
        bot = MCPChatbot(router=router, planner=StubDirectPlanner())

        output = bot.respond("hello")

        self.assertEqual(output, "Hello directly")


if __name__ == "__main__":
    unittest.main()
