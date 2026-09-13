import sys
import unittest
from pathlib import Path

from mcp_chatbot_client.mcp_client import MCPServerClient


class MCPServerClientTests(unittest.TestCase):
    def setUp(self) -> None:
        server_path = Path(__file__).parent / "fake_mcp_server.py"
        self.client = MCPServerClient(
            name="fake",
            command=[sys.executable, "-u", str(server_path)],
            startup_timeout=5,
        )

    def tearDown(self) -> None:
        self.client.stop()

    def test_initialize_list_tools_and_call_tool(self) -> None:
        init = self.client.initialize()
        self.assertEqual(init["protocolVersion"], "2024-11-05")

        tools = self.client.list_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "calculator.add")

        result = self.client.call_tool("calculator.add", {"a": 2, "b": 5})
        self.assertEqual(result["sum"], 7.0)


if __name__ == "__main__":
    unittest.main()
