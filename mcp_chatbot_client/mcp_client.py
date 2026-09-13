from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass


class MCPProtocolError(RuntimeError):
    """Raised when MCP responses are malformed or missing."""


@dataclass
class MCPServerClient:
    name: str
    command: list[str]
    startup_timeout: float = 10.0

    def __post_init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._request_id = 0

    def start(self) -> None:
        if self._process:
            return

        self._process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def stop(self) -> None:
        if not self._process:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=2)
        finally:
            if self._process.stdin:
                self._process.stdin.close()
            if self._process.stdout:
                self._process.stdout.close()
            if self._process.stderr:
                self._process.stderr.close()
            self._process = None

    def initialize(self) -> dict:
        return self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "mcp-chatbot-client", "version": "0.1.0"},
            },
        )

    def list_tools(self) -> list[dict]:
        response = self.request("tools/list")
        tools = response.get("tools", [])
        if not isinstance(tools, list):
            raise MCPProtocolError(f"Invalid tools response from {self.name}: {response!r}")
        return tools

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return self.request("tools/call", {"name": tool_name, "arguments": arguments})

    def request(self, method: str, params: dict | None = None) -> dict:
        if not self._process:
            self.start()
        assert self._process is not None

        if self._process.stdin is None:
            raise MCPProtocolError(f"{self.name} stdin is not available")
        if self._process.stdout is None:
            raise MCPProtocolError(f"{self.name} stdout is not available")

        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }

        self._process.stdin.write(json.dumps(payload) + "\n")
        self._process.stdin.flush()

        deadline = time.time() + self.startup_timeout
        while time.time() < deadline:
            line = self._process.stdout.readline()
            if not line:
                if self._process.poll() is not None:
                    stderr = ""
                    if self._process.stderr:
                        stderr = self._process.stderr.read().strip()
                    raise MCPProtocolError(f"{self.name} exited unexpectedly. {stderr}")
                time.sleep(0.05)
                continue

            message = json.loads(line)
            if "id" in message and message["id"] == self._request_id:
                if "error" in message:
                    raise MCPProtocolError(f"{self.name} error: {message['error']}")
                return message.get("result", {})

        raise TimeoutError(f"Timed out waiting for {self.name} response to '{method}'")
