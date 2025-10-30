# MCP Interceptor & Mock Generator

A complete toolkit for capturing MCP (Model Context Protocol) server communication and generating mock servers from recorded traces.

## Overview

This toolkit provides two main programs:

1. **MCP Interceptor** (`mcp_interceptor.py`) - Monkeypatches the MCP client to capture all communication with MCP servers
2. **Mock Server Generator** (`mock_generator.py`) - Generates fully functional mock MCP servers from trace files

## Architecture

```
┌─────────────────┐
│  Your MCP App   │
└────────┬────────┘
         │ uses
         ▼
┌─────────────────────────┐
│ Intercepted ClientSession│ ◄── Monkeypatch installed here
└────────┬────────────────┘
         │ captures
         ▼
┌─────────────────────────┐
│   Trace File (JSONL)    │  ◄── Machine-parsable format
│  - Session metadata     │
│  - Request/response     │
│  - Timing data          │
└────────┬────────────────┘
         │ reads
         ▼
┌─────────────────────────┐
│  Mock Generator         │
└────────┬────────────────┘
         │ generates
         ▼
┌─────────────────────────┐
│  Mock MCP Server (.py)  │  ◄── Standalone server
│  - Replays responses    │
│  - No backend needed    │
└─────────────────────────┘
```

## Quick Start

### 1. Capture MCP Session

```python
# capture_session.py
import asyncio
from mcp_interceptor import install_interceptor
from mcp import ClientSession

# Install interceptor BEFORE importing ClientSession
logger = install_interceptor(
    trace_file="sessions.jsonl",  # For mock generation
    verbose=True
)

# Your MCP code here - all calls are captured
async with ClientSession(reader, writer) as session:
    logger.start_session(server_info={'url': 'http://example.com'})

    await session.initialize()
    tools = await session.list_tools()
    result = await session.call_tool("some_tool", {"arg": "value"})

    logger.end_session()  # Writes to trace file
```

### 2. Generate Mock Server

```bash
python mock_generator.py sessions.jsonl -o mock_server.py
```

### 3. Run Mock Server

```bash
python mock_server.py
```

The mock server will replay all recorded responses without needing the original backend!

## Data Format

### Trace File Format

The interceptor saves sessions in **NDJSON** (newline-delimited JSON) format - one `MCPSession` object per line:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "server_info": {
    "url": "https://learn.microsoft.com/api/mcp",
    "transport": "http",
    "description": "Microsoft Learn MCP Server"
  },
  "calls": [
    {
      "request": {
        "method": "initialize",
        "args": [],
        "kwargs": {},
        "timestamp": "2025-10-30T10:30:45.123456"
      },
      "response": {
        "success": true,
        "result": {
          "_type": "InitializeResult",
          "protocolVersion": "2024-11-05",
          "capabilities": {...}
        },
        "error": null,
        "timestamp": "2025-10-30T10:30:45.234567"
      },
      "duration_ms": 111.234
    },
    {
      "request": {
        "method": "call_tool",
        "args": ["microsoft_docs_search"],
        "kwargs": {
          "arguments": {"query": "python async"}
        },
        "timestamp": "2025-10-30T10:30:46.123456"
      },
      "response": {
        "success": true,
        "result": {
          "_type": "CallToolResult",
          "content": [...]
        },
        "error": null,
        "timestamp": "2025-10-30T10:30:47.456789"
      },
      "duration_ms": 1333.333
    }
  ],
  "started_at": "2025-10-30T10:30:45.000000",
  "ended_at": "2025-10-30T10:31:00.000000",
  "metadata": {}
}
```

### Key Features

- ✅ **Session-based**: Groups related calls together
- ✅ **Request-response pairs**: Perfect for mock generation
- ✅ **Timing data**: Includes duration in milliseconds
- ✅ **Server metadata**: Captures connection details
- ✅ **Error handling**: Records both successes and failures
- ✅ **Streaming friendly**: NDJSON allows processing large files

## Files

### Core Components

- **`trace_format.py`** - Data structures for structured trace format
  - `MCPSession` - Complete session container
  - `MCPCallPair` - Request-response pair
  - `TraceWriter` / `TraceReader` - I/O utilities

- **`mcp_interceptor.py`** - Monkeypatch implementation
  - `InterceptionLogger` - Captures and logs calls
  - `InterceptedClientSession` - Patched ClientSession
  - `install_interceptor()` - Global installation

- **`mock_generator.py`** - Code generation
  - `MockServerGenerator` - Analyzes traces and generates code
  - CLI tool for easy generation

### Examples

- **`capture_example.py`** - Complete capture workflow
- **`example.py`** - Original simple example

## API Reference

### InterceptionLogger

```python
logger = InterceptionLogger(
    log_file="trace.log",        # Legacy NDJSON format
    trace_file="sessions.jsonl",  # Structured format
    verbose=True                  # Print to console
)

# Session management
logger.start_session(server_info={'url': '...'})
logger.end_session()

# Manual logging (usually automatic)
logger.log_request(method, *args, **kwargs)
logger.log_response(method, result, error)
```

### install_interceptor()

```python
logger = install_interceptor(
    log_file=None,       # Optional legacy log
    trace_file=None,     # Optional structured trace
    verbose=True         # Console output
)
```

### MockServerGenerator

```python
from mock_generator import MockServerGenerator

generator = MockServerGenerator("sessions.jsonl")

# Analyze captured sessions
analysis = generator.analyze_sessions()
print(f"Methods: {analysis['methods']}")
print(f"Total calls: {sum(len(c) for c in analysis['method_calls'].values())}")

# Generate mock server
generator.generate_mock_server(
    output_file="mock_server.py",
    server_name="MyMockServer"
)
```

## Advanced Usage

### Custom Request/Response Hooks

```python
logger = install_interceptor(trace_file="trace.jsonl")

# Add custom processing before requests
async def log_to_external(method, args, kwargs):
    await send_to_analytics(method, args)

logger.add_request_hook(log_to_external)

# Add custom processing after responses
def validate_response(method, result):
    assert result is not None, f"Null result for {method}"

logger.add_response_hook(validate_response)
```

### Reading and Analyzing Traces

```python
from trace_format import TraceReader

reader = TraceReader("sessions.jsonl")

# Read all sessions
sessions = reader.read_sessions()

# Analyze patterns
for session in sessions:
    print(f"Session {session.session_id}:")
    print(f"  Duration: {session.ended_at - session.started_at}")
    print(f"  Calls: {len(session.calls)}")

    for call in session.calls:
        print(f"    - {call.request.method} ({call.duration_ms:.2f}ms)")
```

### Generating Multiple Mock Servers

```bash
# Capture sessions from different servers
python capture_example.py --url https://server1.com --output server1.jsonl
python capture_example.py --url https://server2.com --output server2.jsonl

# Generate separate mock servers
python mock_generator.py server1.jsonl -o mock_server1.py -n Server1Mock
python mock_generator.py server2.jsonl -o mock_server2.py -n Server2Mock
```

## Design Decisions

### Why NDJSON for Trace Format?

- **Streaming**: Process large traces without loading entire file
- **Append-friendly**: New sessions can be appended without parsing
- **Tool support**: Standard format, works with `jq`, `grep`, etc.
- **Machine-parsable**: Easy for programs to consume

### Why Session-based Structure?

- **Context preservation**: Keep related calls together
- **Easier mock generation**: Complete interaction patterns
- **Better debugging**: Understand full conversation flow
- **Metadata support**: Server info, timing, etc.

### Why Monkeypatching?

- **Zero code changes**: Works with existing MCP apps
- **Transparent**: Application code remains clean
- **Complete coverage**: Captures all ClientSession calls
- **Easy toggle**: Install/uninstall at runtime

## Troubleshooting

### "Module 'trace_format' not found"

Make sure you're running from the `mcp_interceptor/` directory or add it to your Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Mock Server Doesn't Match Requests

The mock generator uses a flexible matching strategy:
1. Tries exact match on args + kwargs
2. Falls back to first recorded response for that method

For strict matching, you can modify `_find_matching_response()` in generated code.

### No Sessions in Trace File

Remember to call `logger.start_session()` and `logger.end_session()`:

```python
logger = install_interceptor(trace_file="trace.jsonl")
logger.start_session()  # ← Don't forget this!

# ... your MCP code ...

logger.end_session()    # ← And this!
```

## Testing

Run the complete example:

```bash
# Capture session
python capture_example.py

# Generate mock
python mock_generator.py mcp_sessions.jsonl -o test_mock.py

# Run mock server
python test_mock.py
```

## Comparison with Legacy Format

| Feature | Legacy (log_file) | New (trace_file) |
|---------|------------------|------------------|
| Format | NDJSON requests/responses | NDJSON sessions |
| Human readable | ✅ Yes | ⚠️ Verbose |
| Machine parsable | ⚠️ Requires correlation | ✅ Perfect |
| Mock generation | ❌ No | ✅ Yes |
| Timing data | ❌ No | ✅ Yes |
| Session grouping | ❌ No | ✅ Yes |
| Streaming | ✅ Yes | ✅ Yes |

**Recommendation**: Use both formats:
- `trace_file` for mock generation
- `log_file` for human debugging

## License

Same as the parent project.

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Support for MCP prompts and resources
- [ ] More sophisticated request matching in mocks
- [ ] Mock server with configurable responses
- [ ] Web UI for browsing traces
- [ ] Performance benchmarking tools
