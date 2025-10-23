# Backend Documentation

## Overview

The backend is a Flask application that bridges OpenAI's GPT-4 with multiple MCP (Model Context Protocol) servers, providing a RESTful API for the chat frontend.

## Architecture

```
backend/
├── __init__.py
├── app.py                 # Application factory and Flask setup
├── auth/                  # Authentication module
│   ├── __init__.py
│   ├── oauth_handler.py   # Google OAuth 2.0 implementation
│   └── token_store.py     # Secure token persistence with SQLite
├── api/                   # API endpoints
│   ├── __init__.py
│   ├── chat.py           # Chat message handling
│   ├── tools.py          # MCP tool discovery
│   ├── servers.py        # Server status management
│   └── auth.py           # OAuth endpoints
└── services/             # Business logic
    ├── __init__.py
    ├── mcp_service.py    # MCP server management
    └── openai_service.py # OpenAI API integration
```

## Key Components

### Application Entry (`app.py`)

The main Flask application factory that:
- Initializes all services with dependency injection
- Registers API blueprints
- Configures CORS for frontend communication
- Sets up the application context

```python
def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    # Service initialization
    # Blueprint registration
    return app
```

### Authentication (`auth/`)

#### `oauth_handler.py`
- Implements Google OAuth 2.0 flow
- Manages authorization URLs and token exchange
- Handles token refresh for expired credentials
- Supports multiple Google scopes (Drive, Gmail, Sheets)

#### `token_store.py`
- SQLite-based persistent storage for OAuth tokens
- Automatic token expiration checking
- Secure storage with encryption support (future enhancement)
- Multi-server token management

### API Endpoints (`api/`)

#### Chat Endpoint (`chat.py`)
- **POST /api/chat**: Main chat interface
  - Accepts user messages
  - Retrieves available MCP tools
  - Sends to OpenAI with tool definitions
  - Executes tool calls via MCP servers
  - Returns AI response with tool execution results

#### Tools Endpoint (`tools.py`)
- **GET /api/tools**: Lists all available MCP tools
  - Connects to all configured MCP servers
  - Aggregates tool definitions
  - Returns OpenAI-compatible function schemas

#### Servers Endpoint (`servers.py`)
- **GET /api/servers**: Server status and authentication
  - Lists all configured MCP servers
  - Reports authentication status for each
  - Indicates which servers require OAuth

#### Auth Endpoints (`auth.py`)
- **GET /api/oauth/start/<server>**: Initiate OAuth flow
- **GET /api/oauth/callback**: Handle OAuth callback
- **POST /api/oauth/disconnect/<server>**: Revoke tokens

### Services (`services/`)

#### MCP Service (`mcp_service.py`)
Manages all MCP server interactions:
- Server discovery and initialization
- Tool schema retrieval
- Tool execution with proper server routing
- Authentication token injection
- Error handling and retry logic

Key methods:
- `get_tools()`: Aggregate tools from all servers
- `call_tool()`: Execute tool on appropriate server
- `get_server_info()`: Server status and auth state

#### OpenAI Service (`openai_service.py`)
Handles OpenAI API communication:
- Chat completion requests
- Tool/function calling support
- Response streaming (future enhancement)
- Error handling and retries

## Configuration

### Environment Variables
Required in `.env`:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Google OAuth (for Gmail/Drive servers)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key  # For session management
```

### MCP Server Configuration
Servers are configured in `mcp_service.py`:
```python
self.servers = {
    "calculator": {
        "name": "Calculator",
        "command": "python",
        "args": ["mcp_servers/calculator/server.py"],
        "requires_auth": False,
    },
    "google-drive": {
        "name": "Google Drive",
        "command": "python",
        "args": ["mcp_servers/google_drive/server.py"],
        "requires_auth": True,
        "auth_type": "google_oauth"
    },
    # ... more servers
}
```

## Data Flow

1. **User Message** → Frontend → `/api/chat`
2. **Tool Discovery** → MCPService connects to all servers
3. **OpenAI Call** → OpenAIService with tools as functions
4. **Tool Execution** → MCPService routes to correct server
5. **Response** → Aggregated result back to frontend

## Authentication Flow

1. Frontend requests `/api/oauth/start/google-drive`
2. Backend generates OAuth URL with state parameter
3. User authenticates with Google
4. Google redirects to `/api/oauth/callback`
5. Backend exchanges code for tokens
6. Tokens stored in SQLite database
7. Future requests include tokens automatically

## Error Handling

- **MCP Connection Errors**: Logged, server skipped
- **Tool Execution Errors**: Returned to OpenAI for handling
- **OAuth Errors**: User-friendly error pages
- **Token Expiration**: Automatic refresh attempts

## Testing

```bash
# Test API endpoints
curl http://localhost:5001/api/servers
curl http://localhost:5001/api/tools

# Test chat endpoint
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 5 + 3?"}'
```

## Running the Backend

```bash
# Development mode
uv run python main.py

# Production (with gunicorn)
gunicorn backend.app:create_app() --bind 0.0.0.0:5001
```

## Future Enhancements

See `development_notes/BACKEND_IMPROVEMENTS.md` for planned improvements including:
- Async/await throughout
- Redis caching layer
- WebSocket support for streaming
- Rate limiting
- Enhanced security measures
- Comprehensive test suite