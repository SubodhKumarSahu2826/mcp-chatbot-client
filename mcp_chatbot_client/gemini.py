from __future__ import annotations

import json
from typing import Any
from urllib import error, request


class GeminiPlanner:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiPlanner")
        self.api_key = api_key
        self.model = model

    def plan_tool_call(self, user_message: str, tools: list[dict[str, Any]]) -> dict[str, Any]:
        tool_list = json.dumps(tools, indent=2)
        prompt = (
            "You are an MCP tool planner. Choose at most one tool call for the user message. "
            "Return strict JSON with keys: tool (string|null), arguments (object), direct_response (string|null)."
            "If no tool is needed, set tool to null and put your answer in direct_response.\n"
            f"Available tools:\n{tool_list}\n"
            f"User message: {user_message}"
        )
        content = self._generate_content(prompt)
        parsed = self._extract_json(content)
        return {
            "tool": parsed.get("tool"),
            "arguments": parsed.get("arguments", {}),
            "direct_response": parsed.get("direct_response"),
        }

    def compose_final_response(
        self,
        user_message: str,
        tool_name: str,
        tool_arguments: dict[str, Any],
        tool_result: dict[str, Any],
    ) -> str:
        prompt = (
            "You are an AI assistant responding to a user after an MCP tool call. "
            "Explain the result clearly and concisely.\n"
            f"User message: {user_message}\n"
            f"Tool used: {tool_name}\n"
            f"Tool arguments: {json.dumps(tool_arguments)}\n"
            f"Tool result: {json.dumps(tool_result)}"
        )
        return self._generate_content(prompt)

    def _generate_content(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini API request failed: {exc.code} {detail}") from exc

        candidates = body.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {body}")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_chunks = [part.get("text", "") for part in parts if isinstance(part, dict)]
        text = "\n".join(chunk for chunk in text_chunks if chunk).strip()
        if not text:
            raise RuntimeError(f"Gemini returned empty text: {body}")
        return text

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError(f"Gemini returned non-JSON planner output: {text}")
        return json.loads(text[start : end + 1])
