from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any

from .config import ServerConfig
from .mcp_client import MCPServerClient


class Planner(Protocol):
    def plan_tool_call(self, user_message: str, tools: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    def compose_final_response(
        self,
        user_message: str,
        tool_name: str,
        tool_arguments: dict[str, Any],
        tool_result: dict[str, Any],
    ) -> str:
        ...


@dataclass
class MCPToolRouter:
    clients: dict[str, MCPServerClient]
    tools: dict[str, tuple[str, dict[str, Any]]]

    @classmethod
    def from_server_configs(cls, server_configs: list[ServerConfig]) -> "MCPToolRouter":
        clients: dict[str, MCPServerClient] = {}
        tool_map: dict[str, tuple[str, dict[str, Any]]] = {}

        for config in server_configs:
            client = MCPServerClient(name=config.name, command=config.command)
            client.start()
            client.initialize()
            clients[config.name] = client

            for tool in client.list_tools():
                name = tool["name"]
                if name in tool_map:
                    raise ValueError(f"Duplicate tool name '{name}' across MCP servers")
                tool_map[name] = (config.name, tool)

        return cls(clients=clients, tools=tool_map)

    def shutdown(self) -> None:
        for client in self.clients.values():
            client.stop()

    def tool_descriptions(self) -> list[dict[str, Any]]:
        descriptions = []
        for tool_name, (server_name, tool_schema) in self.tools.items():
            descriptions.append(
                {
                    "name": tool_name,
                    "description": tool_schema.get("description", ""),
                    "server": server_name,
                    "inputSchema": tool_schema.get("inputSchema", {}),
                }
            )
        return descriptions

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        server_name, _ = self.tools[tool_name]
        return self.clients[server_name].call_tool(tool_name, arguments)


@dataclass
class MCPChatbot:
    router: MCPToolRouter
    planner: Planner

    def respond(self, user_message: str) -> str:
        tools = self.router.tool_descriptions()
        plan = self.planner.plan_tool_call(user_message=user_message, tools=tools)

        tool_name = plan.get("tool")
        if not tool_name:
            return str(plan.get("direct_response") or "I couldn't determine a tool action.")

        if tool_name not in self.router.tools:
            return f"The requested tool '{tool_name}' is not available."

        arguments = plan.get("arguments", {})
        if not isinstance(arguments, dict):
            return "Tool arguments must be a JSON object."

        tool_result = self.router.call_tool(tool_name, arguments)
        return self.planner.compose_final_response(user_message, tool_name, arguments, tool_result)
