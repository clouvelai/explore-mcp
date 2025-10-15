# MCP Learning Project

Multi-server MCP implementation with chat interface demonstrating calculator, Gmail, and Google Drive integration.

## MCP Evaluation Agent

**Auto-generates evaluation suites and mock servers from any MCP implementation**

```
┌─────────────────┐    Discovery    ┌──────────────────┐    Generation    ┌─────────────────┐
│   Real MCP      │ ─────────────►  │  Eval Generator  │ ─────────────►  │  Generated      │
│   Server        │   initialize()  │                  │                 │  Outputs        │
│ ┌─────────────┐ │   list_tools()  │ ┌──────────────┐ │                 │ ┌─────────────┐ │
│ │• list_files │ │                 │ │ Discovers    │ │                 │ │ Mock Server │ │
│ │• send_email │ │◄────────────────│ │ Tools &      │ │────────────────►│ │ - Same APIs │ │
│ │• read_msg   │ │                 │ │ Schemas      │ │                 │ │ - No Effects│ │
│ │• calculate  │ │                 │ │              │ │                 │ │ - Realistic │ │
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

### Key Benefits
- **Zero Setup**: Point at any MCP server, get instant evaluation suite
- **Safe Testing**: Mock servers have no side effects (no real emails sent, files created)
- **Realistic**: Smart mock responses that match expected tool outputs
- **Isolated**: Each MCP server gets its own namespaced test environment
- **Comprehensive**: Tests valid inputs, missing params, wrong types, edge cases

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

## Critical Commands

### Setup
```bash
# Install dependencies
uv sync
cd chat-frontend && npm install

# Configure environment
cp ENV_TEMPLATE .env
# Edit .env with OpenAI API key and Google OAuth credentials
```

### Run Full Application
```bash
# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start frontend
./start_frontend.sh
```

### Test MCP Servers
```bash
# Test calculator server directly
uv run python client.py

# Test all servers
uv run python chat_backend.py
```

### Development
```bash
# Run tests
./run_tests.sh

# Individual server testing
uv run python mcp_servers/calculator/server.py
uv run python mcp_servers/gmail/server.py
uv run python mcp_servers/google_drive/server.py
```

## Dependencies

**Python** (managed by uv):
- `mcp>=1.0.0` - Core MCP protocol
- `fastmcp>=0.2.0` - High-level framework
- `openai>=1.0.0` - OpenAI API
- `flask>=3.0.0` - Backend server
- `google-api-python-client>=2.0.0` - Google APIs

**Frontend**:
- React 18.2.0
- react-scripts 5.0.1

## Ports
- Frontend: `localhost:3000`
- Backend: `localhost:5001`


