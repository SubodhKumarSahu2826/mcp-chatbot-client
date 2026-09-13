from __future__ import annotations

from dataclasses import dataclass
from os import getenv
import shlex


@dataclass(frozen=True)
class ServerConfig:
    name: str
    command: list[str]


@dataclass(frozen=True)
class AppConfig:
    gemini_api_key: str | None
    gemini_model: str
    servers: list[ServerConfig]

    @staticmethod
    def _parse_command(value: str | None) -> list[str]:
        if not value:
            return []
        return shlex.split(value)

    @classmethod
    def from_env(cls) -> "AppConfig":
        calculator_cmd = cls._parse_command(getenv("CALCULATOR_MCP_COMMAND"))
        expense_cmd = cls._parse_command(getenv("EXPENSE_MCP_COMMAND"))
        manim_cmd = cls._parse_command(getenv("MANIM_MCP_COMMAND"))

        servers = [
            ServerConfig(name="calculator", command=calculator_cmd),
            ServerConfig(name="expense", command=expense_cmd),
            ServerConfig(name="manim", command=manim_cmd),
        ]

        missing = [server.name for server in servers if not server.command]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(
                f"Missing MCP server command(s): {joined}. "
                "Set CALCULATOR_MCP_COMMAND, EXPENSE_MCP_COMMAND, and MANIM_MCP_COMMAND."
            )

        return cls(
            gemini_api_key=getenv("GEMINI_API_KEY"),
            gemini_model=getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            servers=servers,
        )
