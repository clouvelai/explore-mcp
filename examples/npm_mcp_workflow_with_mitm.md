# NPM MCP Server Workflow with MITM Interception

## Complete Architecture Flow

```
┌─────────────────┐    ./mcp add    ┌─────────────────┐    npm install    ┌─────────────────┐
│ MCP Registry    │ ──────────────→ │ NPM Package     │ ──────────────→   │ Local Binary    │
│ Entry Created   │                 │ @mcp/server-fs  │                   │ ~/.npm/bin/     │
└─────────────────┘                 └─────────────────┘                   └─────────────────┘
         │                                                                          │
         ▼                                                                          │
┌─────────────────┐                                                                │
│ config.json     │                                                                │
│ discovery.json  │                                                                │
│ generated/      │ ◄──────────────── MITM Interception ──────────────────────────┤
│ intercepted_    │                                                                │
│ logs.jsonl      │                                                                ▼
└─────────────────┘                                                   ┌─────────────────┐
                                                                       │ Running Server  │
┌─────────────────────────────────────────────────────────────────┐   │ stdio transport │
│ Interceptor Script (intercept_filesystem_server.py)            │   │ + directories   │
│                                                                 │   │ allowed         │
│ install_interceptor() ──────── Monkeypatch ──────────────────┐ │   └─────────────────┘
│                                                               │ │            │
│ InterceptedClientSession ──── Transparent Proxy ────────────┤ │            │
│   ├─ log_request()                                           │ │            │
│   ├─ call real server ──────────────────────────────────────┼─┼────────────┘
│   └─ log_response()                                          │ │
│                                                              │ │
│ Logs written to: mcp_registry/servers/filesystem/           │ │
└──────────────────────────────────────────────────────────────┘ │
                                                                 │
                Real File Operations: read_file, list_directory, write_file
```

## Core MITM Features

- **Transparent Proxy** - Zero code changes to existing MCP workflows
- **Real Server Communication** - Actual npm server process, not mocks  
- **Complete Logging** - All requests/responses with timestamps
- **Registry Integration** - Logs stored alongside discovery.json and config.json

## Working Example

```bash
# 1. Add npm server to registry
./mcp add fs @modelcontextprotocol/server-filesystem --source npm --category Storage

# 2. Current approach: Basic operations  
./mcp discover fs
./mcp generate fs  
./mcp test fs

# 3. Enhanced: With MITM interception
python intercept_filesystem_server.py
# Creates: mcp_registry/servers/filesystem/intercepted_logs.jsonl
# Result: 14 log entries capturing real server communication
```

## Key Benefits

- **Zero Modification** - Works with any existing npm MCP server
- **Real Operations** - Captures actual server behavior, not mocks
- **Complete Audit Trail** - Every request/response logged with timestamps  
- **Registry Integration** - Logs stored alongside discovery.json and config.json
- **Debug Visibility** - See exact communication flow for troubleshooting

## Log Output Example

```json
{"type": "request", "timestamp": "2025-10-23T22:20:24.355888", "method": "call_tool", "args": ["read_file", {"path": "README.md"}]}
{"type": "response", "timestamp": "2025-10-23T22:20:24.358219", "method": "call_tool", "result": {"content": [...6267 chars...]}}
```

This transforms npm MCP server management into a comprehensive debugging and monitoring platform.