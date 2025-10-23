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
./mcp publish mcp_servers/calculator/server.py

# Generate from public MCP server (Microsoft Learn documentation)  
./mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
./mcp discover microsoft-docs && ./mcp generate microsoft-docs

# Add and generate from local server
./mcp add my-server ./my-server.py --category Utilities
./mcp discover my-server && ./mcp generate my-server
```

**Change Detection**: Discovery automatically tracks two hash types for schema intelligence:
- `server_file_hash`: MD5 of server file (local servers only) 
- `discovery_content_hash`: MD5 of API schema (all server types - primary for change detection)

### Evaluation Runner
```bash
# Run generated test suite against mock server
./mcp test calculator
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

### MCP Registry CLI (npm/docker-style)
**NEW**: Unified CLI for managing MCP servers like npm/docker registry with **seamless git integration**:

```bash
# Server Management
./mcp add calculator mcp_servers/calculator/server.py --category Utilities
./mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
./mcp list
./mcp list --category Utilities
./mcp search "math calculator"
./mcp inspect calculator
./mcp remove old-server

# Operations
./mcp discover calculator
./mcp discover --all
./mcp generate calculator --force
./mcp test calculator

# CI/CD Workflows
./mcp sync                    # Discover all + regenerate if changed
./mcp status                  # Registry health overview
./mcp publish ./my-server.py  # Easy server addition with auto-discovery

# Git-based Servers (NEW!)
./mcp git add gleanwork https://github.com/gleanwork/mcp-server.git --category Development
./mcp git update gleanwork    # Pull latest changes
./mcp git status gleanwork    # Show git status
./mcp git discover https://github.com/modelcontextprotocol/servers.git  # Preview servers
```

**Key Features**:
- **npm-like commands**: `add`, `remove`, `list`, `search`, `inspect`
- **docker-like operations**: `sync`, `status` for CI/CD health monitoring
- **Auto-discovery**: `publish` command auto-detects and configures servers
- **Category management**: Organize servers by function (Utilities, Communication, etc.)
- **Batch operations**: `--all` flag for discover/generate/test across all servers

**Usage**: Use the `./mcp` wrapper script for all commands:
```bash
./mcp list                          # List all servers
./mcp status                        # Registry health overview
./mcp sync && ./mcp test --all      # CI/CD pipeline
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
- **`server_generator.py`**: Creates mock MCP servers with realistic responses
- **`evals_generator.py`**: Generates comprehensive test suites
- **`evaluation_runner.py`**: Executes tests and generates reports
- **`discovery.py`**: MCP server discovery engine

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
./mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
./mcp discover microsoft-docs

# Generate complete mock + evaluations
./mcp generate microsoft-docs

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
./mcp publish mcp_servers/calculator/server.py
./mcp test calculator

# Test with public server  
./mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
./mcp sync && ./mcp test microsoft-docs
```