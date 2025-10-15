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
uv run python mcp_eval_generator.py --server server.py --name calculator --use-agent

# Run the generated evaluations
uv run python run_evaluations.py --evaluations generated/calculator/evaluations.json --mock-server generated/calculator/mock_server.py
```

### Key Benefits
- **AI-Powered**: Claude analyzes tool semantics for intelligent test generation (75+ tests vs 19 hardcoded)
- **Fully Agnostic**: Works with any MCP server regardless of domain or purpose
- **Zero Setup**: Point at any MCP server, get instant evaluation suite
- **Safe Testing**: Mock servers have no side effects or external dependencies
- **Smart Responses**: AI generates realistic, contextual mock responses
- **Isolated**: Each MCP server gets its own namespaced test environment
- **Comprehensive**: Tests valid inputs, missing params, wrong types, mathematical edge cases

## Chat Interface Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  React Frontend │    │  Flask Backend   │    │   OpenAI GPT-4  │
│   (port 3000)   │◄──►│   (port 5001)    │◄──►│                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   MCP Servers    │
                       │                  │
                       │ ┌──────────────┐ │
                       │ │ Calculator   │ │
                       │ │ - add()      │ │
                       │ │ - multiply() │ │
                       │ │ - divide()   │ │
                       │ │ - sum_many() │ │
                       │ └──────────────┘ │
                       │                  │
                       │ ┌──────────────┐ │
                       │ │ Gmail        │ │
                       │ │ - list_msgs  │ │
                       │ │ - search     │ │
                       │ │ - read_msg   │ │
                       │ │ - mark_read  │ │
                       │ │ - create_drf │ │
                       │ └──────────────┘ │
                       │                  │
                       │ ┌──────────────┐ │
                       │ │ Google Drive │ │
                       │ │ - list_files │ │
                       │ │ - search     │ │
                       │ │ - read_file  │ │
                       │ │ - create_txt │ │
                       │ │ - sheets_ops │ │
                       │ └──────────────┘ │
                       └──────────────────┘
```

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
├── mcp_servers/
│   ├── calculator/     # Calculator MCP server
│   ├── gmail/         # Gmail MCP server  
│   └── google_drive/  # Google Drive MCP server
├── chat-frontend/     # React chat interface
├── chat_backend.py    # Flask server bridging GPT-4 and MCP
├── server.py          # Legacy standalone calculator server
├── client.py          # Test client
└── README.md          # This file
```

## 🚀 Setup & Usage

### Prerequisites
```bash
# Install Claude CLI (required for AI generation)
pip install claude-cli

# Install Python dependencies
uv sync

# Install frontend dependencies (optional, for chat interface)
cd chat-frontend && npm install
```

### Environment Setup
```bash
# Copy environment template
cp ENV_TEMPLATE .env

# Edit .env with your API keys:
# - OPENAI_API_KEY (for chat interface)
# - Google OAuth credentials (for Gmail/Drive servers)
```

### Generate MCP Evaluations

#### AI-Enhanced Generation (Recommended)
```bash
# Generate with Claude AI (requires claude CLI)
uv run python mcp_eval_generator.py --server server.py --name calculator --use-agent

# For other servers
uv run python mcp_eval_generator.py --server mcp_servers/gmail/server.py --name gmail --use-agent
uv run python mcp_eval_generator.py --server mcp_servers/google_drive/server.py --name gdrive --use-agent
```

#### Hardcoded Generation (Fallback)
```bash
# Generate without AI (basic pattern matching)
uv run python mcp_eval_generator.py --server server.py --name calculator
```

### Run Evaluations
```bash
# Execute generated test suite
uv run python run_evaluations.py --evaluations generated/calculator/evaluations.json --mock-server generated/calculator/mock_server.py

# Results saved to generated/calculator/eval_results.md
```

### Generated File Structure
```
generated/
├── calculator/
│   ├── mock_server.py      # Mock MCP server with same API
│   ├── evaluations.json    # Test cases (75+ with AI, 19 without)
│   └── eval_results.md     # Evaluation report
├── gmail/
│   └── ...
└── gdrive/
    └── ...
```

### Run Chat Interface (Optional)
```bash
# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start frontend  
./start_frontend.sh

# Access at http://localhost:3000
```

### Test Individual MCP Servers
```bash
# Test calculator server directly
uv run python client.py

# Test individual servers
uv run python mcp_servers/calculator/server.py
uv run python mcp_servers/gmail/server.py
uv run python mcp_servers/google_drive/server.py
```

## 🔍 AI vs Hardcoded Comparison

| Feature | AI-Enhanced | Hardcoded |
|---------|-------------|-----------|
| **Test Cases** | 75+ comprehensive tests | 19 basic tests |
| **Mock Responses** | `"The sum of 42 and 17 is 59"` | `"Mock: Operation completed"` |
| **Edge Cases** | Division by zero, infinity, precision | Basic type validation |
| **Domain Awareness** | Understands calculator semantics | Pattern matching only |
| **Setup** | Requires Claude CLI | No additional dependencies |

## Dependencies

**Core**:
- `uv` - Python package manager
- `claude` CLI - For AI generation (optional but recommended)

**Python** (managed by uv):
- `mcp>=1.0.0` - Core MCP protocol
- `fastmcp>=0.2.0` - High-level framework  
- `openai>=1.0.0` - OpenAI API (chat interface)
- `flask>=3.0.0` - Backend server (chat interface)
- `google-api-python-client>=2.0.0` - Google APIs (Gmail/Drive)

**Frontend** (optional):
- React 18.2.0
- react-scripts 5.0.1

## Ports
- Frontend: `localhost:3000`
- Backend: `localhost:5001`


