# MCP Learning Project

Multi-server MCP implementation with chat interface and AI-powered evaluation system for testing any MCP server.


## 🤖 MCP Evaluation Agent

**Auto-generates evaluation suites and mock servers from any MCP implementation using Claude AI**

```
┌─────────────────┐    Discovery    ┌──────────────────┐    Generation    ┌─────────────────┐
│   Real MCP      │ ─────────────►  │  Eval Generator  │ ─────────────►  │  Generated      │
│   Server        │   initialize()  │                  │                 │  Outputs        │
│ ┌─────────────┐ │   list_tools()  │ ┌──────────────┐ │                 │ ┌─────────────┐ │
│ │• tool_alpha │ │                 │ │ Discovers    │ │                 │ │ Mock Server │ │
│ │• tool_beta  │ │◄────────────────│ │ Tools &      │ │────────────────►│ │ - Same APIs │ │
│ │• tool_gamma │ │                 │ │ Schemas      │ │                 │ │ - No Effects│ │
│ │• tool_delta │ │                 │ │              │ │                 │ │ - Realistic │ │
│ └─────────────┘ │                 │ └──────────────┘ │                 │ │   Responses │ │
└─────────────────┘                 │                  │                 │ └─────────────┘ │
                                    │ ┌──────────────┐ │                 │                 │
                                    │ │ Generates    │ │                 │ ┌─────────────┐ │
                                    │ │ Test Cases   │ │────────────────►│ │ Eval Suite  │ │
                                    │ │ from Schemas │ │                 │ │ - Valid     │ │
                                    │ └──────────────┘ │                 │ │ - Invalid   │ │
                                    └──────────────────┘                 │ │ - Edge      │ │
                                                                         │ │ - Missing   │ │
                                                                         │ └─────────────┘ │
                                                                         └─────────────────┘
                                                ▼
┌─────────────────┐    Executes    ┌──────────────────┐    Connects     ┌─────────────────┐
│   Any LLM/      │ ─────────────► │  Eval Runner     │ ─────────────►  │  Mock Server    │
│   Agent         │                │                  │                 │                 │
│                 │◄───────────────│ ┌──────────────┐ │◄────────────────│ ┌─────────────┐ │
│ ┌─────────────┐ │    Results     │ │ Loads Tests  │ │   Tool Calls    │ │ Returns     │ │
│ │ GPT-4       │ │                │ │ Calls Tools  │ │                 │ │ Mock Data   │ │
│ │ Claude      │ │                │ │ Verifies     │ │                 │ │ No Side     │ │
│ │ Custom Bot  │ │                │ │ Responses    │ │                 │ │ Effects     │ │
│ └─────────────┘ │                │ └──────────────┘ │                 │ └─────────────┘ │
└─────────────────┘                └──────────────────┘                 └─────────────────┘
                                                ▼
                                   ┌──────────────────┐
                                   │   Markdown       │
                                   │   Report         │
                                   │ ┌──────────────┐ │
                                   │ │ Pass/Fail    │ │
                                   │ │ Metrics      │ │
                                   │ │ Error        │ │
                                   │ │ Details      │ │
                                   │ │ Suggestions  │ │
                                   │ └──────────────┘ │
                                   └──────────────────┘
```

### Quick Start

```bash
# Generate evaluations for any MCP server
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py

# Run the generated evaluations
uv run python -m ai_generation.evaluation_runner --evaluations generated/calculator/evaluations.json --mock-server generated/calculator/server.py
```

### Key Benefits
- **AI-Powered**: Claude generates intelligent tests and realistic mock responses
- **Zero Setup**: Point at any MCP server, get instant evaluation suite
- **Safe Testing**: Mock servers with no side effects or external dependencies
- **Domain Agnostic**: Works with any MCP server regardless of purpose

## Chat Interface Architecture

```
┌─────────────────┐    ┌──────────────────────────────────┐    ┌─────────────────┐
│  React Frontend │    │       Flask Backend (backend/)   │    │   OpenAI GPT-4  │
│   (port 3000)   │◄──►│         (port 5001)              │◄──►│                 │
└─────────────────┘    │                                  │    └─────────────────┘
                       │  ┌────────────────────────────┐  │
                       │  │ API Layer (backend/api/)   │  │
                       │  │ • /api/chat                │  │
                       │  │ • /api/tools               │  │
                       │  │ • /api/servers             │  │
                       │  │ • /api/oauth/*             │  │
                       │  └────────────────────────────┘  │
                       │                                  │
                       │  ┌────────────────────────────┐  │
                       │  │ Services (backend/services/)│  │
                       │  │ • MCPService               │  │
                       │  │ • OpenAIService            │  │
                       │  └────────────────────────────┘  │
                       │                                  │
                       │  ┌────────────────────────────┐  │
                       │  │ Auth (backend/auth/)       │  │
                       │  │ • GoogleOAuthHandler       │  │
                       │  │ • TokenStore               │  │
                       │  └────────────────────────────┘  │
                       └──────────────────────────────────┘
                                        │
                                        ▼
                       ┌──────────────────────────────────┐
                       │      MCP Servers (mcp_servers/)  │
                       │                                  │
                       │ ┌──────────────┐                 │
                       │ │ Calculator   │                 │
                       │ │ - add()      │                 │
                       │ │ - multiply() │                 │
                       │ │ - divide()   │                 │
                       │ │ - sum_many() │                 │
                       │ └──────────────┘                 │
                       │                                  │
                       │ ┌──────────────┐                 │
                       │ │ Gmail        │                 │
                       │ │ - list_msgs  │                 │
                       │ │ - search     │                 │
                       │ │ - read_msg   │                 │
                       │ │ - mark_read  │                 │
                       │ │ - create_drf │                 │
                       │ └──────────────┘                 │
                       │                                  │
                       │ ┌──────────────┐                 │
                       │ │ Google Drive │                 │
                       │ │ - list_files │                 │
                       │ │ - search     │                 │
                       │ │ - read_file  │                 │
                       │ │ - create_txt │                 │
                       │ │ - sheets_ops │                 │
                       │ └──────────────┘                 │
                       └──────────────────────────────────┘
```

## Backend Architecture

The Flask backend has been refactored into a modular, maintainable structure:

### Module Overview

- **`backend/app.py`**: Main Flask application factory and configuration
- **`backend/api/`**: RESTful API endpoints
  - `chat.py`: Handles chat messages, OpenAI integration, and tool execution
  - `tools.py`: Discovers and lists available MCP tools
  - `servers.py`: Reports MCP server status and authentication state
  - `auth.py`: Manages OAuth flow for Google services
- **`backend/services/`**: Business logic and external integrations
  - `mcp_service.py`: Manages MCP server connections, tool discovery, and execution
  - `openai_service.py`: Handles OpenAI API calls and chat completions
- **`backend/auth/`**: Authentication and security
  - `oauth_handler.py`: Google OAuth 2.0 flow implementation
  - `token_store.py`: SQLite-based secure token persistence

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message to OpenAI with MCP tools |
| `/api/tools` | GET | List all available MCP tools |
| `/api/servers` | GET | Get MCP server status and auth state |
| `/api/history` | GET | Retrieve conversation history |
| `/api/clear` | POST | Clear conversation history |
| `/api/oauth/start/<server>` | GET | Initiate OAuth flow |
| `/api/oauth/callback` | GET | Handle OAuth callback |
| `/api/oauth/disconnect/<server>` | POST | Revoke OAuth tokens |

## MCP Servers & Tools

### Calculator Server (`mcp_servers/calculator/`)
- **add(a, b)** - Add two numbers
- **multiply(a, b)** - Multiply two numbers  
- **divide(a, b)** - Divide with zero check
- **sum_many(numbers)** - Add multiple numbers
- **explain_calculation** - Educational prompt

### Gmail Server (`mcp_servers/gmail/`)
- **list_messages** - List inbox messages with unread indicators
- **search_messages** - Search with Gmail query syntax
- **read_message** - Get full message content
- **get_unread_count** - Count unread messages
- **create_draft** - Create email draft
- **mark_as_read/unread** - Update message status
- **list_labels** - Show all Gmail labels

### Google Drive Server (`mcp_servers/google_drive/`)
- **list_files** - List Drive files
- **search_files** - Search with natural language or API format
- **get_file_info** - Detailed file metadata
- **list_folders** - Show folders only
- **recent_files** - Files modified in last N days
- **read_file** - Read/export file content
- **create_text_file** - Upload new text file
- **read_spreadsheet_cells** - Read Google Sheets data
- **update_spreadsheet_cells** - Write to Google Sheets

## Project Structure

```
explore-mcp/
├── backend/                # Organized Flask backend application
│   ├── __init__.py
│   ├── app.py             # Main Flask application setup
│   ├── auth/              # Authentication & token management
│   │   ├── __init__.py
│   │   ├── oauth_handler.py  # Google OAuth 2.0 handler
│   │   └── token_store.py    # SQLite token persistence
│   ├── api/               # API endpoint definitions
│   │   ├── __init__.py
│   │   ├── auth.py        # OAuth endpoints (/api/oauth/*)
│   │   ├── chat.py        # Chat endpoints (/api/chat)
│   │   ├── servers.py     # Server status (/api/servers)
│   │   └── tools.py       # Tool discovery (/api/tools)
│   └── services/          # Business logic layer
│       ├── __init__.py
│       ├── mcp_service.py    # MCP server connection management
│       └── openai_service.py # OpenAI API integration
├── ai_generation/         # AI-powered MCP evaluation system
│   ├── cli.py            # Main command-line interface
│   ├── ai_service.py     # Claude CLI interface
│   ├── server_generator.py # Mock server generation
│   ├── evals_generator.py  # Test case generation
│   └── evaluation_runner.py # Evaluation execution
├── mcp_servers/           # MCP server implementations
│   ├── calculator/       # Calculator MCP server
│   │   ├── server.py     # FastMCP server setup
│   │   └── tools.py      # Calculator tool implementations
│   ├── gmail/           # Gmail MCP server  
│   │   ├── server.py    # FastMCP server setup
│   │   └── tools.py     # Gmail tool implementations
│   ├── google_drive/    # Google Drive MCP server
│   │   ├── server.py    # FastMCP server setup
│   │   └── tools.py     # Drive tool implementations
│   └── shared/          # Shared utilities
│       └── google_auth.py # Google API authentication
├── chat-frontend/       # React chat interface
├── generated/           # AI-generated mock servers & tests
├── main.py             # Backend entry point (backward compatible)
├── client.py           # Test client for MCP servers
└── README.md           # This file
```

## 🚀 Setup & Usage

### Prerequisites
```bash
pip install claude-cli  # For AI generation
uv sync                 # Python dependencies
cd chat-frontend && npm install  # Frontend (optional)
```

### Environment Setup
```bash
cp ENV_TEMPLATE .env
# Edit .env with OPENAI_API_KEY and Google OAuth credentials
```

### Generate MCP Evaluations
```bash
# Generate with Claude AI for calculator
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py

# For other servers  
uv run python -m ai_generation.cli --server mcp_servers/gmail/server.py
uv run python -m ai_generation.cli --server mcp_servers/google_drive/server.py

# Custom name and output directory
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py --name custom_calc --output-dir custom_output
```


### Run Evaluations
```bash
# Execute generated test suite
uv run python -m ai_generation.evaluation_runner --evaluations generated/calculator/evaluations.json --mock-server generated/calculator/server.py
```


### Run Chat Interface
```bash
# Terminal 1: Start backend
uv run python main.py

# Terminal 2: Start frontend  
cd chat-frontend && npm start

# Access at http://localhost:3000
```

### Test MCP Servers
```bash
# Test with client
uv run python client.py

# Run individual servers
uv run python mcp_servers/calculator/server.py
```


## Dependencies

- `uv` - Python package manager
- `claude` CLI - For AI generation
- `mcp>=1.0.0`, `fastmcp>=0.2.0` - MCP protocol
- `openai>=1.0.0`, `flask>=3.0.0` - Chat backend
- `google-api-python-client>=2.0.0` - Google APIs
- React 18.2.0 - Frontend

## Ports
- Frontend: `localhost:3000`
- Backend: `localhost:5001`


