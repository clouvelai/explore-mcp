# MCP Interceptor & Mock Generator - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR APPLICATION                                │
│                                                                         │
│  from mcp_interceptor import install_interceptor                       │
│  logger = install_interceptor(trace_file="trace.jsonl")                │
│                                                                         │
│  from mcp import ClientSession  ◄── Now returns InterceptedClientSession│
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  │ uses
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTERCEPTED CLIENT SESSION                           │
│                    (mcp_interceptor.py)                                 │
│                                                                         │
│  Monkeypatched MCP ClientSession that wraps all methods:               │
│   ├─ initialize()                                                       │
│   ├─ list_tools() ──────────────┐                                      │
│   ├─ call_tool()                │                                      │
│   ├─ list_resources()           │ All intercepted                     │
│   ├─ read_resource()            │                                      │
│   ├─ list_prompts()             │                                      │
│   └─ get_prompt()  ─────────────┘                                      │
│                                                                         │
│  For each call:                                                         │
│   1. Log request → InterceptionLogger                                   │
│   2. Call original method                                               │
│   3. Log response → InterceptionLogger                                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  │ logs to
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INTERCEPTION LOGGER                                │
│                      (mcp_interceptor.py)                               │
│                                                                         │
│  Manages session tracking and dual output:                             │
│                                                                         │
│  ┌──────────────────┐          ┌──────────────────┐                   │
│  │  Session State   │          │  Output Formats  │                   │
│  ├──────────────────┤          ├──────────────────┤                   │
│  │ - session_id     │          │ - Legacy NDJSON  │→ debug.log        │
│  │ - server_info    │          │   (for humans)   │                   │
│  │ - pending calls  │          │                  │                   │
│  │ - call pairs     │          │ - Structured     │→ trace.jsonl      │
│  └──────────────────┘          │   Sessions       │                   │
│                                │   (for mocks)    │                   │
│                                └──────────────────┘                   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  │ writes
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      TRACE FILE (trace.jsonl)                           │
│                      (trace_format.py)                                  │
│                                                                         │
│  NDJSON Format - One MCPSession per line:                              │
│                                                                         │
│  Line 1: {session_id: "...", calls: [{request: {...}, response: {...}}]}│
│  Line 2: {session_id: "...", calls: [{...}, {...}]}                    │
│  Line 3: {session_id: "...", calls: [{...}]}                           │
│                                                                         │
│  Each session contains:                                                │
│   ├─ session_id (unique identifier)                                    │
│   ├─ server_info (URL, name, description, etc.)                        │
│   ├─ calls (array of request-response pairs)                           │
│   │   ├─ request (method, args, kwargs, timestamp)                     │
│   │   ├─ response (success, result/error, timestamp)                   │
│   │   └─ duration_ms (timing information)                              │
│   ├─ started_at (ISO timestamp)                                        │
│   ├─ ended_at (ISO timestamp)                                          │
│   └─ metadata (custom key-value pairs)                                 │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  │ reads
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MOCK SERVER GENERATOR                              │
│                      (mock_generator.py)                                │
│                                                                         │
│  Pipeline:                                                              │
│                                                                         │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│  │   Read       │      │   Analyze    │      │   Generate   │         │
│  │   Trace      │─────▶│   Sessions   │─────▶│   Code       │         │
│  └──────────────┘      └──────────────┘      └──────────────┘         │
│        │                      │                      │                 │
│        │                      │                      │                 │
│        ▼                      ▼                      ▼                 │
│  Parse JSONL          Extract patterns        Build Python file        │
│  sessions             - Methods used          - Import statements      │
│                       - Request/response      - Response data          │
│                         pairs                 - Server class           │
│                       - Tool schemas          - Handler methods        │
│                                               - Main block             │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  │ generates
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   GENERATED MOCK SERVER (mock_server.py)                │
│                                                                         │
│  #!/usr/bin/env python3                                                │
│  """Auto-generated Mock MCP Server"""                                  │
│                                                                         │
│  # Static response data extracted from trace                           │
│  MOCK_RESPONSES = {                                                    │
│      "list_tools": [...],                                              │
│      "call_tool": [...]                                                │
│  }                                                                      │
│                                                                         │
│  class MockMCPServer:                                                  │
│      def __init__(self):                                               │
│          self.server = Server(name='mock-server')                      │
│          self._setup_handlers()                                        │
│                                                                         │
│      async def handle_list_tools(self):                                │
│          result = self._find_matching_response('list_tools', [], {})   │
│          return ListToolsResult(tools=[...])                           │
│                                                                         │
│      async def handle_call_tool(self, name, arguments):                │
│          result = self._find_matching_response(                        │
│              'call_tool', [name], {'arguments': arguments}             │
│          )                                                             │
│          return CallToolResult(content=[...])                          │
│                                                                         │
│      def _find_matching_response(self, method, args, kwargs):          │
│          # Smart matching logic                                        │
│          ...                                                           │
│                                                                         │
│  if __name__ == "__main__":                                            │
│      server = MockMCPServer()                                          │
│      asyncio.run(server.run())                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. CAPTURE PHASE
   ┌─────────────┐
   │ Your App    │
   │  MCP Call   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Interceptor │◄── Captures request
   │             │
   │ + timing    │◄── Captures response
   │ + pairing   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ MCPSession  │
   │  object     │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ trace.jsonl │
   │  (NDJSON)   │
   └─────────────┘

2. GENERATION PHASE
   ┌─────────────┐
   │ trace.jsonl │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Generator   │
   │ - parse     │
   │ - analyze   │
   │ - codegen   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ mock.py     │
   │ (runnable)  │
   └─────────────┘

3. REPLAY PHASE
   ┌─────────────┐
   │ mock.py     │◄── Runs as real MCP server
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Client App  │◄── Gets recorded responses
   │             │
   └─────────────┘
```

## Component Responsibilities

### trace_format.py
**Purpose**: Data structures for session traces

**Classes**:
- `MCPRequest` - Single request container
- `MCPResponse` - Single response container
- `MCPCallPair` - Request-response pair
- `MCPSession` - Complete session with metadata
- `TraceWriter` - Write sessions to NDJSON
- `TraceReader` - Read sessions from NDJSON

**Key Features**:
- JSON serialization/deserialization
- Type safety with dataclasses
- NDJSON streaming support

### mcp_interceptor.py
**Purpose**: Transparent MCP call interception

**Classes**:
- `InterceptionLogger` - Session tracking and logging
- `InterceptedClientSession` - Monkeypatched ClientSession

**Functions**:
- `install_interceptor()` - Global installation
- `uninstall_interceptor()` - Restoration

**Key Features**:
- Monkeypatch-based (no code changes needed)
- Dual output (legacy + structured)
- Hook support for custom logic
- Automatic request-response correlation

### mock_generator.py
**Purpose**: Generate mock servers from traces

**Classes**:
- `MockServerGenerator` - Main generator class

**Methods**:
- `analyze_sessions()` - Extract patterns
- `generate_mock_server()` - Create Python file
- Various `_generate_*()` helpers

**Key Features**:
- Complete code generation
- Smart request matching
- Proper MCP type handling
- CLI tool included

## File Formats

### Trace File (JSONL)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "server_info": {
    "url": "https://example.com/mcp",
    "name": "example-server"
  },
  "calls": [
    {
      "request": {
        "method": "call_tool",
        "args": ["tool_name"],
        "kwargs": {"arguments": {"param": "value"}},
        "timestamp": "2025-10-30T10:30:45.123456"
      },
      "response": {
        "success": true,
        "result": {
          "_type": "CallToolResult",
          "content": [{"type": "text", "text": "result"}]
        },
        "error": null,
        "timestamp": "2025-10-30T10:30:45.234567"
      },
      "duration_ms": 111.234
    }
  ],
  "started_at": "2025-10-30T10:30:45.000000",
  "ended_at": "2025-10-30T10:31:00.000000",
  "metadata": {}
}
```

### Legacy Log File (NDJSON)

```json
{"type": "request", "timestamp": "...", "method": "call_tool", "args": [...], "kwargs": {...}}
{"type": "response", "timestamp": "...", "method": "call_tool", "result": {...}}
```

## Extension Points

### Custom Request Hooks

```python
logger = install_interceptor(trace_file="trace.jsonl")

def my_hook(method, args, kwargs):
    print(f"Calling {method}")

logger.add_request_hook(my_hook)
```

### Custom Response Hooks

```python
def validate_hook(method, result):
    assert result is not None

logger.add_response_hook(validate_hook)
```

### Custom Mock Matching

Modify generated `_find_matching_response()`:

```python
def _find_matching_response(self, method, args, kwargs):
    # Add custom logic here
    if method == "special_tool":
        return self._custom_logic(args, kwargs)

    # Fall back to default
    return super()._find_matching_response(method, args, kwargs)
```

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Intercept call | O(1) | Minimal overhead |
| Log request | O(1) | In-memory append |
| Log response | O(1) | In-memory append |
| Write session | O(n) | n = number of calls in session |
| Read sessions | O(n) | n = number of sessions (streaming) |
| Generate mock | O(n*m) | n = sessions, m = avg calls per session |
| Match request | O(k) | k = responses for method (usually small) |

**Memory Usage**:
- Interceptor: O(n) where n = calls in current session
- Generator: O(m) where m = total calls across all sessions
- Mock server: O(k) where k = total unique responses

## Thread Safety

- ✅ Interceptor: Safe (uses asyncio, single-threaded)
- ✅ Logger: Safe (no shared mutable state)
- ✅ TraceWriter: Safe (writes are atomic per line)
- ✅ Mock server: Safe (asyncio-based)

## Testing Strategy

**Unit tests** (via test_workflow.py):
- Trace format read/write
- Session serialization
- Mock generation

**Integration tests**:
- Full capture → generate → run workflow
- Real MCP server interaction (capture_example.py)

**Validation**:
- All tests pass ✅
- Works with real MCP servers ✅
- Generates runnable mocks ✅

## Error Handling

| Error Scenario | Handling |
|---------------|----------|
| MCP call fails | Recorded in response.error |
| Session not started | Warning, no trace written |
| Invalid trace file | Exception with helpful message |
| Generation fails | Exception with stack trace |
| Mock server match fails | Returns first response or error |

## Backwards Compatibility

✅ Existing code works unchanged
✅ Legacy log format still supported
✅ Original example.py still works
✅ Can run with or without tracing

## Dependencies

**Core**:
- `mcp` - MCP protocol library
- Python 3.8+ - For asyncio, dataclasses

**Optional**:
- None! Pure Python implementation

## Project Structure

```
mcp_interceptor/
├── Core Implementation
│   ├── trace_format.py      # Data structures
│   ├── mcp_interceptor.py   # Interception logic
│   ├── mock_generator.py    # Code generation
│   └── __init__.py          # Package exports
│
├── Examples & Tests
│   ├── example.py           # Simple example
│   ├── capture_example.py   # Complete workflow
│   └── test_workflow.py     # Integration tests
│
└── Documentation
    ├── README.md            # Main documentation
    ├── USAGE_GUIDE.md       # Detailed examples
    ├── QUICK_START.md       # Quick reference
    ├── SUMMARY.md           # Implementation summary
    └── ARCHITECTURE.md      # This file
```

## Design Philosophy

1. **Transparency**: Interceptor is invisible to application code
2. **Simplicity**: Clear, readable code generation
3. **Flexibility**: Easy to customize and extend
4. **Standards**: Use NDJSON, JSON, standard formats
5. **Testing**: Comprehensive tests ensure reliability

---

**Questions?** Check:
- USAGE_GUIDE.md - Detailed examples
- README.md - API reference
- SUMMARY.md - Implementation details
