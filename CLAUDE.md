# CLAUDE.md

This file provides guidance to Claude Code when working with this MCP automation platform.

## Platform Overview

This is an **MCP automation platform for CI/CD** that uses AI to generate mock servers and evaluations from any MCP server implementation. The platform consists of:

- **AI Generation System** (`ai_generation/`): Discovers MCP tools and generates mock servers + test suites
- **Modular Backend** (`backend/`): Flask application bridging OpenAI GPT-4 with MCP servers  
- **MCP Servers** (`mcp_servers/`): Example implementations (calculator, Gmail, Google Drive)
- **Chat Interface** (`chat-frontend/`): React frontend for testing and interaction

## Core Automation Workflow

```
Real MCP Server → AI Discovery → Mock Server + Evaluations → CI/CD Testing
```

The platform automatically generates safe, side-effect-free test environments from production MCP servers.

## Essential Commands

### AI Generation (Core Platform Feature)
```bash
# Generate mock server + evaluations from local MCP server
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py

# Generate from public MCP server (Microsoft Learn documentation)
uv run python -m ai_generation.cli --server https://learn.microsoft.com/api/mcp --name microsoft-docs

# Generate from local HTTP MCP server
uv run python -m ai_generation.cli --server http://localhost:8080/sse --name my-server

# Custom output location
uv run python -m ai_generation.cli --server <path> --name custom --output-dir custom_output
```

### Evaluation Runner
```bash
# Run generated test suite against mock server
uv run python -m ai_generation.evaluation_runner --evaluations generated/calculator/evaluations.json --mock-server generated/calculator/server.py
```

### Backend Development
```bash
# Start backend (includes all MCP servers)
uv run python main.py

# Start frontend (optional)
cd chat-frontend && npm start
```

### Testing MCP Servers
```bash
# Direct server testing
uv run python client.py

# Individual server (stdio mode)
uv run python mcp_servers/calculator/server.py
```

## Architecture

### Backend Structure (`backend/`)
- **`app.py`**: Flask application factory with dependency injection
- **`auth/`**: OAuth handlers and token storage (GoogleOAuthHandler, TokenStore)
- **`api/`**: REST endpoints (chat.py, tools.py, servers.py, auth.py)
- **`services/`**: Business logic (MCPService, OpenAIService)

### MCP Servers (`mcp_servers/`)
- **`calculator/`**: Math operations (add, multiply, divide, sum_many)
- **`gmail/`**: Email operations (list, search, read, mark_read, create_draft)
- **`google_drive/`**: File operations (list, search, read, create, sheets)

### AI Generation (`ai_generation/`)
- **`cli.py`**: Main orchestrator for discovery and generation
- **`server_generator.py`**: Creates mock MCP servers with realistic responses
- **`evals_generator.py`**: Generates comprehensive test suites
- **`evaluation_runner.py`**: Executes tests and generates reports

## Environment Setup

```bash
# Dependencies
uv sync
cd chat-frontend && npm install

# Environment
cp ENV_TEMPLATE .env
# Add OPENAI_API_KEY and Google OAuth credentials
```

## Key Development Patterns

### Prompt Management
**IMPORTANT: Prompt Version Control Rules**
1. **Isolated Commits**: Each prompt change MUST be in its own commit
2. **Version Updates**: Always increment version in the JSON file when modifying a prompt
3. **Semantic Versioning**: Use semantic versioning (major.minor.patch):
   - Major: Breaking changes to prompt structure or expected output
   - Minor: New features or significant improvements
   - Patch: Bug fixes or minor tweaks
4. **Commit Message Format**: `prompt: update [prompt_name] to v[version] - [description]`

Example workflow:
```bash
# Edit prompt file
vi ai_generation/prompts/mock_responses.json
# Update "version": "1.0.0" to "version": "1.0.1"

# Commit ONLY the prompt change
git add ai_generation/prompts/mock_responses.json
git commit -m "prompt: update mock_responses to v1.0.1 - improve response realism"
```

### Adding New MCP Tools
1. **Add to appropriate server**: `mcp_servers/{server}/tools.py`
2. **Use FastMCP decorator**:
   ```python
   @mcp.tool()
   def your_tool(param: type) -> str:
       """Tool description."""
       return "result"
   ```
3. **Restart backend**: Changes auto-discovered by OpenAI integration

### Modifying Backend Services
- **MCP connections**: `backend/services/mcp_service.py`
- **OpenAI integration**: `backend/services/openai_service.py`  
- **Authentication**: `backend/auth/oauth_handler.py`
- **API endpoints**: `backend/api/{chat,tools,servers,auth}.py`

### File Import Patterns
MCP servers require proper Python path setup:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

## Common Issues

### Port Conflicts
Backend runs on `localhost:5001`, frontend on `localhost:3000`. Kill existing processes:
```bash
lsof -ti:5001 | xargs kill -9
```

### MCP Server Authentication
Google-based servers (Gmail, Drive) require OAuth. Check `/api/servers` for auth status.

### Import Errors
Ensure MCP servers have proper sys.path configuration and use absolute imports from project root.

## Dependencies

**Core Platform**:
- `mcp>=1.0.0`, `fastmcp>=0.2.0` - MCP protocol
- `openai>=1.0.0` - AI generation
- `flask>=3.0.0` - Backend API

**Development**:
- `uv` - Python package manager
- `claude` CLI - AI generation (install separately)

## Port Configuration
- Backend: `localhost:5001`
- Frontend: `localhost:3000`

## Testing Public MCP Servers

The platform supports discovering and generating mocks from **any public MCP server** on the internet:

### Microsoft Learn MCP Server
Microsoft provides a public MCP server with documentation tools:
```bash
# Discover Microsoft Learn MCP server
uv run python -m ai_generation.discovery https://learn.microsoft.com/api/mcp

# Generate complete mock + evaluations
uv run python -m ai_generation.cli --server https://learn.microsoft.com/api/mcp --name microsoft-docs

# Available tools:
# - microsoft_docs_search: Search official Microsoft/Azure documentation
# - microsoft_code_sample_search: Find code examples with language filtering  
# - microsoft_docs_fetch: Fetch complete documentation pages
```

### Automatic Transport Detection
The platform automatically detects the correct transport protocol:
- **HTTP URLs** → Tries HTTP transport first, falls back to SSE if needed
- **Local files** → Uses stdio transport
- **Manual override** → Use `--transport [http|sse|stdio]` flag

## Quick Reference

```bash
# Check available tools
curl http://localhost:5001/api/tools

# Clear chat history  
curl -X POST http://localhost:5001/api/clear

# Test with local server
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py
uv run python -m ai_generation.evaluation_runner --evaluations generated/calculator/evaluations.json --mock-server generated/calculator/server.py

# Test with public server  
uv run python -m ai_generation.cli --server https://learn.microsoft.com/api/mcp --name microsoft-docs
uv run python -m ai_generation.evaluation_runner --evaluations generated/microsoft-docs/evaluations.json --mock-server generated/microsoft-docs/server.py
```