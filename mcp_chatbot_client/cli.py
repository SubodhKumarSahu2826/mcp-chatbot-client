from __future__ import annotations

from .chatbot import MCPChatbot, MCPToolRouter
from .config import AppConfig
from .gemini import GeminiPlanner


def main() -> int:
    config = AppConfig.from_env()
    if not config.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY must be set")

    planner = GeminiPlanner(api_key=config.gemini_api_key, model=config.gemini_model)
    router = MCPToolRouter.from_server_configs(config.servers)
    chatbot = MCPChatbot(router=router, planner=planner)

    print("MCP chatbot ready. Type 'exit' to quit.")
    try:
        while True:
            user_message = input("You: ").strip()
            if user_message.lower() in {"exit", "quit"}:
                break
            if not user_message:
                continue
            reply = chatbot.respond(user_message)
            print(f"Bot: {reply}")
    finally:
        router.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
