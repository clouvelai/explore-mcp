# MCP CI/CD Automation Platform

**AI-powered mock server generation and testing for MCP servers**

Automatically generates safe, side-effect-free test environments from any MCP server implementation using Claude AI.

## Quick Start

```bash
# Setup
uv sync && cp ENV_TEMPLATE .env
# Add your OPENAI_API_KEY to .env

# Add and test a server
./mcp publish mcp_servers/calculator/server.py
./mcp test calculator

# Check registry status
./mcp status
```

## Core Workflow

```
Real MCP Server → AI Discovery → Mock Server + Evaluations → CI/CD Testing
```

## Key Features

### 🤖 **AI-Powered Generation**
- **Zero Setup**: Point at any MCP server, get instant evaluation suite
- **Smart Mocks**: Claude generates realistic responses with no side effects
- **Comprehensive Tests**: Auto-generated test cases for validation, edge cases, and errors

### 🛠️ **npm/docker-style Registry**
```bash
# Server Management
./mcp add calculator mcp_servers/calculator/server.py --category Utilities
./mcp list
./mcp inspect calculator
./mcp remove old-server

# Operations  
./mcp discover --all
./mcp generate --all
./mcp test --all

# CI/CD Workflows
./mcp sync                    # Discover + regenerate if changed
./mcp status                  # Registry health overview
```

### 🌐 **Multi-Transport Support**
- **Local servers**: stdio transport
- **Remote servers**: HTTP/SSE auto-detection  
- **npm packages**: Global installation with binary detection
- **Public APIs**: Microsoft Learn, custom endpoints

*Find more servers at https://github.com/modelcontextprotocol/servers*

## Examples

### Local Server
```bash
./mcp publish mcp_servers/calculator/server.py
./mcp test calculator
```

### Remote Server
```bash
./mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
./mcp sync && ./mcp test microsoft-docs
```

### npm Package Server
```bash
./mcp add fs @modelcontextprotocol/server-filesystem --source npm --category Storage
./mcp sync && ./mcp test fs
```

### Batch Operations
```bash
./mcp add gmail mcp_servers/gmail/server.py --category Communication
./mcp add google-drive mcp_servers/google_drive/server.py --category Storage
./mcp sync && ./mcp test --all
```

## Chat Interface

Interactive testing with GPT-4 integration:

```bash
# Terminal 1: Backend
uv run python main.py

# Terminal 2: Frontend
cd chat-frontend && npm install && npm start
# Opens http://localhost:3000
```

Try: *"What's 25 + 17?"* - Watch GPT-4 automatically use your MCP tools!

## Architecture

```
┌─────────────────┐    Discovery    ┌──────────────────┐    Generation    ┌─────────────────┐
│   Real MCP      │ ─────────────►  │  AI Generator    │ ─────────────►  │  Generated      │
│   Server        │                 │                  │                 │  Outputs        │
│ ┌─────────────┐ │                 │ ┌──────────────┐ │                 │ ┌─────────────┐ │
│ │• tool_alpha │ │                 │ │ Discovers    │ │                 │ │ Mock Server │ │
│ │• tool_beta  │ │◄────────────────│ │ Tools &      │ │────────────────►│ │ - Same APIs │ │
│ │• tool_gamma │ │                 │ │ Schemas      │ │                 │ │ - No Effects│ │
│ └─────────────┘ │                 │ └──────────────┘ │                 │ │ - Realistic │ │
└─────────────────┘                 │                  │                 │ │   Responses │ │
                                    │ ┌──────────────┐ │                 │ └─────────────┘ │
                                    │ │ Generates    │ │                 │                 │
                                    │ │ Test Cases   │ │────────────────►│ ┌─────────────┐ │
                                    │ └──────────────┘ │                 │ │ Eval Suite  │ │
                                    └──────────────────┘                 │ │ - Valid     │ │
                                                                         │ │ - Invalid   │ │
                                                                         │ │ - Edge      │ │
                                                                         │ └─────────────┘ │
                                                                         └─────────────────┘
```

## Platform Components

- **MCP Registry CLI** (`./mcp`): npm/docker-style server management
- **AI Generation** (`ai_generation/`): Claude-powered mock & test generation  
- **Backend API** (`backend/`): Flask app bridging GPT-4 with MCP servers
- **Chat Interface** (`chat-frontend/`): React frontend for interactive testing
- **Example Servers** (`mcp_servers/`): Calculator, Gmail, Google Drive implementations

## Environment Setup

```bash
# Dependencies
uv sync
cd chat-frontend && npm install

# Environment
cp ENV_TEMPLATE .env
# Add OPENAI_API_KEY and Google OAuth credentials
```

## Registry Status

Check your current registry:
```bash
./mcp status
```

Example output:
```
📊 MCP Registry Status
==================================================
Total servers: 5
Discovered: 3/5
Generated: 3/5

📂 By Category:
  Communication: 1
  Documentation: 1  
  Storage: 1
  Utilities: 2
```

## Development

### Adding New Tools
```python
# mcp_servers/{server}/tools.py
@mcp.tool()
def your_tool(param: str) -> str:
    """Tool description."""
    return "result"
```

### Testing Changes
```bash
./mcp discover calculator  # Rediscover after changes
./mcp generate calculator  # Regenerate mocks
./mcp test calculator      # Run evaluations
```

## Key Benefits

- **Safe Testing**: Mock servers with no side effects or external dependencies
- **Domain Agnostic**: Works with any MCP server regardless of purpose  
- **CI/CD Ready**: Registry management with health monitoring and batch operations
- **AI-Powered**: Claude generates intelligent tests and realistic responses
- **Developer Friendly**: npm/docker-style commands developers already know

---

**Get started**: `./mcp publish mcp_servers/calculator/server.py && ./mcp test calculator`