import os
import sys
import json
import asyncio
import streamlit as st

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)


# ---------------- CONFIG ----------------

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing in .env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------- MCP SERVERS ----------------

SERVERS = {
    "math": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [
            os.path.join(BASE_DIR, "servers/math/main.py")
        ],
    },

    "expense": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [
            os.path.join(BASE_DIR, "servers/expense/server.py")
        ],
    },

    "manim-server": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [
            os.path.join(BASE_DIR, "servers/manim/server.py")
        ],
    },
}


SYSTEM_PROMPT = """
You have access to MCP tools for mathematics, expenses, and Manim.

Use the appropriate MCP tool when needed.
Do not narrate tool calls.
Return only the useful final answer.
"""


# ---------------- CHAT HISTORY ----------------

HISTORY_FILE = os.path.join(
    BASE_DIR,
    "chat_history.json"
)


def get_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
        )

    return str(content)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return []


def save_history(history):
    data = []

    for msg in history:

        if isinstance(msg, HumanMessage):
            data.append({
                "role": "user",
                "content": get_text(msg.content)
            })

        elif isinstance(msg, AIMessage) and not msg.tool_calls:
            data.append({
                "role": "assistant",
                "content": get_text(msg.content)
            })

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


# ---------------- MCP + GEMINI ----------------

async def chat(history):

    video_path = None

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=GOOGLE_API_KEY,
    )

    client = MultiServerMCPClient(SERVERS)

    tools = await client.get_tools()

    tool_map = {
        tool.name: tool
        for tool in tools
    }

    llm_with_tools = llm.bind_tools(tools)

    # Ask Gemini
    response = await llm_with_tools.ainvoke(history)

    # No tool required
    if not response.tool_calls:
        return response, None

    messages = history + [response]

    # Execute MCP tools
    for call in response.tool_calls:

        tool = tool_map.get(call["name"])

        if tool is None:
            raise ValueError(
                f"Tool not found: {call['name']}"
            )

        result = await tool.ainvoke(call["args"])

        # ---------------- MANIM VIDEO ----------------

        if call["name"] == "execute_manim_code":

            result_text = str(result)

            if ".mp4" in result_text:

                start = result_text.find("/app")
                end = result_text.find(".mp4") + 4

                if start != -1:
                    video_path = result_text[start:end]

        # ---------------- TOOL MESSAGE ----------------

        messages.append(
            ToolMessage(
                tool_call_id=call["id"],
                content=json.dumps(
                    result,
                    default=str
                ),
            )
        )

    # Ask Gemini for final answer
    final_response = await llm.ainvoke(messages)

    return final_response, video_path


# ---------------- STREAMLIT ----------------

st.set_page_config(
    page_title="MCP Chat",
    page_icon="🧰",
)

st.title("🧰 MCP Chat")


# ---------------- LOAD HISTORY ----------------

if "history" not in st.session_state:

    st.session_state.history = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]

    for msg in load_history():

        if msg["role"] == "user":

            st.session_state.history.append(
                HumanMessage(
                    content=msg["content"]
                )
            )

        elif msg["role"] == "assistant":

            st.session_state.history.append(
                AIMessage(
                    content=msg["content"]
                )
            )


# ---------------- DISPLAY HISTORY ----------------

for msg in st.session_state.history:

    if isinstance(msg, HumanMessage):

        with st.chat_message("user"):
            st.markdown(
                get_text(msg.content)
            )

    elif isinstance(msg, AIMessage):

        if not msg.tool_calls:

            with st.chat_message("assistant"):
                st.markdown(
                    get_text(msg.content)
                )


# ---------------- CHAT INPUT ----------------

user_text = st.chat_input(
    "Type a message..."
)


if user_text:

    with st.chat_message("user"):
        st.markdown(user_text)

    st.session_state.history.append(
        HumanMessage(content=user_text)
    )

    try:

        response, video_path = asyncio.run(
            chat(st.session_state.history)
        )

        with st.chat_message("assistant"):

            st.markdown(
                get_text(response.content)
            )

            # Display Manim video
            if (
                video_path
                and os.path.exists(video_path)
            ):
                st.video(video_path)

        st.session_state.history.append(
            response
        )

        save_history(
            st.session_state.history
        )

    except Exception as e:

        with st.chat_message("assistant"):
            st.error(
                f"Error: {e}"
            )