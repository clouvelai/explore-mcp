# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) learning project that demonstrates building MCP servers and clients. The project consists of:
- A FastMCP-based server exposing calculator tools
- A Python client for testing the MCP server
- A Flask backend that bridges OpenAI GPT-4 with the MCP server
- A React frontend chat interface

## Architecture

### MCP Server Flow
```
User → React Frontend → Flask Backend → OpenAI GPT-4
                              ↓
                         MCP Server (tools)
                              ↓
                      Tool execution result
```

### Key Components

**MCP Server** (`server.py`): FastMCP server with tools:
- `add(a, b)`: Adds two numbers
- `sum_many(numbers)`: Adds multiple numbers
- `explain_calculation` prompt: Educational calculation explanations

**Chat Backend** (`chat_backend.py`): Flask server that:
- Receives messages from frontend (port 5001)
- Connects to MCP server to get available tools
- Calls OpenAI with tool definitions
- Executes MCP tools when requested
- Returns responses to frontend

**Frontend** (`chat-frontend/`): React application for chat UI

## Development Commands

### Dependencies Installation
```bash
# Install Python dependencies (uses uv)
uv sync

# Install frontend dependencies
cd chat-frontend && npm install
```

### Running the Application

#### Full Chat Interface (Recommended)
```bash
# Terminal 1: Start backend (includes MCP server)
./start_backend.sh
# Or manually: uv run python chat_backend.py

# Terminal 2: Start frontend  
./start_frontend.sh
# Or manually: cd chat-frontend && npm start
```

#### Testing MCP Server Directly
```bash
# Run client test
uv run python client.py

# Run server standalone (stdio mode)
uv run python server.py
```

#### Protocol Demos
```bash
# HTTP server demo
uv run python http_server.py

# Protocol demonstration
uv run python protocol_demo.py

# Raw protocol demonstration
uv run python raw_protocol_demo.py

# Universal client
uv run python universal_client.py
```

### Environment Setup
```bash
# Create .env file from template
cp ENV_TEMPLATE .env
# Edit .env and add your OpenAI API key
```

## Testing

Run tests to verify the setup:
```bash
# Test the MCP client-server connection
uv run python client.py

# For chat interface testing, follow TEST_GUIDE.md
```

## Key Files to Modify

When adding new MCP tools:
1. Add tool to `server.py` using `@mcp.tool()` decorator
2. Restart the backend to pick up changes
3. Tools automatically appear in OpenAI function calls

## Dependencies

Python packages (managed by uv):
- `mcp>=1.0.0` - Core MCP protocol
- `fastmcp>=0.2.0` - High-level MCP framework
- `openai>=1.0.0` - OpenAI API client
- `flask>=3.0.0` - Web backend
- `flask-cors>=4.0.0` - CORS support

Frontend packages:
- React 18.2.0
- react-scripts 5.0.1

## Port Configuration

- Backend/API: `localhost:5001`
- Frontend: `localhost:3000`
- HTTP demo server: `localhost:8000`

## Common Tasks

### Add a new MCP tool
Edit `server.py` and add:
```python
@mcp.tool()
def your_tool(param: type) -> str:
    """Tool description."""
    # Implementation
    return "Result"
```

### Clear chat history
Use the "Clear Chat" button in UI or call:
```bash
curl -X POST http://localhost:5001/api/clear
```

### Check available MCP tools
```bash
curl http://localhost:5001/api/tools
```