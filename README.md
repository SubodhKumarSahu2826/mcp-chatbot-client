# mcp-chatbot-client

AI-powered MCP chatbot client that connects Gemini with multiple FastMCP servers for:
- calculations
- expense management
- Manim animation generation

## Features

- Connects to three FastMCP servers (`calculator`, `expense`, `manim`) over stdio JSON-RPC.
- Uses Gemini to decide whether a tool call is needed and to produce the final response.
- Supports multi-server tool routing with duplicate-tool detection.

## Environment variables

Required:

- `CALCULATOR_MCP_COMMAND` (e.g. `python -m calculator_server`)
- `EXPENSE_MCP_COMMAND` (e.g. `python -m expense_server`)
- `MANIM_MCP_COMMAND` (e.g. `python -m manim_server`)
- `GEMINI_API_KEY`

Optional:

- `GEMINI_MODEL` (default: `gemini-1.5-flash`)

## Run

```bash
python -m mcp_chatbot_client
```

Then chat interactively. The chatbot can invoke tools from any connected FastMCP server.

## Tests

```bash
python -m unittest discover -s tests -v
```
