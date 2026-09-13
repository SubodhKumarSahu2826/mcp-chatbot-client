# MCP Chatbot Client

An AI-powered chatbot built around the Model Context Protocol (MCP),
using Google Gemini, LangChain, FastMCP, Streamlit, SQLite, Manim, and
Docker.

The application acts as an MCP client that connects an LLM with multiple
specialized MCP servers. Gemini interprets the user's request, selects
the appropriate tool, the MCP client executes it, and the result is
returned through the Streamlit chat interface.

## Live Demo

https://mcp-chatbot-client.onrender.com/

## Features

-   Gemini-powered conversational AI
-   Model Context Protocol (MCP) client architecture
-   Multiple independent FastMCP servers
-   Math operations through an MCP tool server
-   Expense tracking backed by SQLite
-   Expense categories exposed as an MCP resource
-   Manim code execution and MP4 animation generation
-   Generated Manim videos displayed directly in Streamlit
-   Persistent local chat history
-   Dockerized application
-   Render deployment
-   Environment-variable based API-key management

## Architecture

``` text
User
  |
  v
Streamlit Chat UI
  |
  v
LangChain MCP Client
  |
  v
Google Gemini
  |
  +-------------------+-------------------+
  |                   |                   |
  v                   v                   v
Math MCP          Expense MCP         Manim MCP
Server             Server              Server
  |                   |                   |
  v                   v                   v
Calculations       SQLite DB          Manim Render
                                      |
                                      v
                                    MP4 Video
                                      |
                                      v
                                 Streamlit UI
```

The MCP servers currently run as subprocesses using `stdio` transport.

## Technology Stack

### AI and LLM

-   Google Gemini
-   `gemini-3.6-flash`
-   LangChain
-   `langchain-google-genai`

### MCP

-   Model Context Protocol
-   FastMCP
-   `langchain-mcp-adapters`

### Application

-   Python 3.13
-   Streamlit
-   python-dotenv

### Data

-   SQLite

### Animation

-   Manim Community Edition

### Deployment

-   Docker
-   Render

## MCP Servers

### 1. Math MCP Server

Location:

``` text
servers/math/main.py
```

Exposes:

``` text
add(a, b)
subtract(a, b)
multiply(a, b)
divide(a, b)
power(a, b)
modulus(a, b)
```

The server validates numeric inputs and prevents division or modulus by
zero.

Example:

``` text
Calculate 25 * 48
```

Gemini can select the appropriate MCP tool and return the result.

### 2. Expense Tracker MCP Server

Location:

``` text
servers/expense/server.py
```

Uses SQLite to manage financial entries.

Available tools:

``` text
add_expense()
list_expenses()
summarize()
edit_expense()
delete_expense()
add_credit()
```

The server also exposes categories through the MCP resource:

``` text
expense://categories
```

Stored fields include:

``` text
id
date
amount
category
subcategory
description
note
type
```

The `type` field distinguishes expenses from credits.

Example requests:

``` text
Add an expense of 500 for food today.
```

``` text
Show my expenses between 2026-01-01 and 2026-01-31.
```

``` text
Summarize my expenses by category.
```

### 3. Manim MCP Server

Location:

``` text
servers/manim/server.py
```

The Manim server allows Gemini to generate and execute Manim code.

Workflow:

``` text
User request
    |
    v
Gemini generates Manim code
    |
    v
execute_manim_code()
    |
    v
Manim renders scene
    |
    v
MP4 generated
    |
    v
Path returned to MCP client
    |
    v
Streamlit displays video
```

The server renders Manim with:

``` text
manim -ql
```

and stores generated media under the server's media directory.

The server also provides a cleanup tool for temporary Manim files.

## Tool Calling Flow

The client uses `MultiServerMCPClient` to connect to the configured MCP
servers.

The tools are discovered with:

``` python
tools = await client.get_tools()
```

and provided to Gemini using:

``` python
llm_with_tools = llm.bind_tools(tools)
```

When Gemini requests a tool, the client:

1.  Identifies the requested MCP tool.
2.  Executes the tool with the supplied arguments.
3.  Adds the tool result to the conversation.
4.  Sends the result back to Gemini.
5.  Receives the final response.
6.  Displays the response in Streamlit.

This allows the LLM to use capabilities that are implemented outside the
core chatbot.

## Project Structure

``` text
mcp-chatbot-client/
|
├── servers/
│   ├── math/
│   │   └── main.py
│   ├── expense/
│   │   ├── server.py
│   │   ├── categories.json
│   │   └── data/
│   │       └── expenses.db
│   └── manim/
│       ├── server.py
│       └── media/
|
├── src/
│   └── mcp_client/
│       └── __init__.py
|
├── client1.py
├── main.py
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

## Chat History

The Streamlit client stores conversational history in:

``` text
chat_history.json
```

This file is intentionally excluded from Git so personal/local
conversation history is not committed to the repository.

## Environment Variables

Create a local `.env` file:

``` env
GOOGLE_API_KEY=your_api_key_here
```

The application loads the key using `python-dotenv`.

The `.env` file is excluded by both Git and Docker:

``` text
.gitignore  -> prevents committing the secret
.dockerignore -> prevents copying the secret into the Docker build context
```

For Render, configure:

``` text
GOOGLE_API_KEY
```

through Render's Environment Variables settings.

Never put the API key directly in source code, the Dockerfile, or this
README.

## Running Locally

### Prerequisites

-   Python 3.13
-   Git
-   `uv`
-   Manim Community Edition
-   Gemini API key
-   Docker, if container testing is required

### Install dependencies

``` bash
uv sync
```

Activate the environment:

``` bash
source .venv/bin/activate
```

Create `.env`:

``` env
GOOGLE_API_KEY=your_api_key_here
```

Start Streamlit:

``` bash
streamlit run client1.py
```

Open:

``` text
http://localhost:8501
```

## Docker

The application uses:

``` text
manimcommunity/manim:v0.21.0
```

as its base image so the container includes the Manim environment
required by the Manim MCP server.

Build:

``` bash
docker build -t mcp-chatbot-client .
```

Run locally:

``` bash
docker run --rm -p 8501:8501 --env-file .env mcp-chatbot-client
```

The container runs Streamlit on `0.0.0.0` and supports the `PORT`
environment variable used by cloud platforms.

## Deployment on Render

The project is deployed as a Docker Web Service on Render.

Deployment flow:

``` text
GitHub
   |
   v
Render
   |
   v
Docker Build
   |
   v
Streamlit
   |
   v
MCP Client
   |
   v
Gemini + MCP Servers
```

Render configuration:

``` text
Runtime: Docker
Branch: main
Docker Build Context: .
Dockerfile: ./Dockerfile
```

The Gemini API key is configured as a Render environment variable rather
than being stored in GitHub or the Docker image.

Live application:

https://mcp-chatbot-client.onrender.com/

## Git and Docker Security

The project uses both `.gitignore` and `.dockerignore`.

`.gitignore` prevents local/private files from being committed:

``` text
.venv/
.env
__pycache__/
*.pyc
chat_history.json
.DS_Store
```

`.dockerignore` prevents unnecessary or sensitive files from entering
the Docker build context:

``` text
.venv
.env
.git
__pycache__
*.pyc
chat_history.json
```

## Design Decisions

### Modular MCP servers

Math, Expense, and Manim are separate MCP servers instead of being
tightly coupled to the Streamlit application.

This makes the architecture easier to extend with additional tools.

### Stdio transport

The current architecture runs the MCP servers as local subprocesses and
communicates through `stdio`.

This works well for the current single-container deployment.

### SQLite

SQLite provides a simple, self-contained database for the Expense
Tracker without requiring an external database service.

### Docker

Docker provides a consistent runtime environment and is particularly
useful for Manim because Manim requires additional system dependencies.

## Example Prompts

### Math

``` text
Calculate 125 * 36.
```

``` text
What is 1024 divided by 16?
```

### Expense Tracker

``` text
Add an expense of 250 for food today.
```

``` text
Show my expenses for this month.
```

``` text
Give me a summary of my expenses by category.
```

### Manim

``` text
Create a Manim animation showing a circle expanding.
```

``` text
Create a simple animation explaining the Pythagorean theorem.
```

## Limitations

This project is primarily a demonstration of MCP, LLM tool calling, and
multi-server integration.

The current deployment has several production limitations:

-   Render's free service uses an ephemeral filesystem.
-   SQLite data should not be treated as permanent cloud storage.
-   Generated Manim files are stored locally in the container.
-   The application does not currently implement user authentication.
-   Expense data is not separated by user accounts.
-   Complex Manim renders may require more CPU/RAM than a free instance
    provides.

For a production version, persistent database storage, object storage,
authentication, monitoring, stronger validation, and automated tests
would be appropriate.

## Future Improvements

-   PostgreSQL or another persistent database
-   User authentication and authorization
-   Per-user expense data
-   Persistent object storage for Manim videos
-   Streaming LLM responses
-   Better MCP tool-call visualization
-   More MCP servers and external integrations
-   Automated tests
-   GitHub Actions CI/CD
-   Structured logging and monitoring
-   Production-grade error handling
-   Resource controls for complex Manim rendering

## Project Goal

The goal of this project is to demonstrate how an LLM can be extended
with modular tools through MCP.

The complete flow is:

``` text
Natural Language
      |
      v
Gemini Reasoning
      |
      v
Tool Selection
      |
      v
LangChain MCP Client
      |
      v
MCP Server
      |
      v
Tool Execution
      |
      v
Tool Result
      |
      v
Gemini Final Response
      |
      v
Streamlit UI
```

The project shows how MCP can separate AI reasoning from tool
implementation while allowing a single conversational interface to
interact with multiple capabilities.

## License

No license has currently been specified for this repository.
