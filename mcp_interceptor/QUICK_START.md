# MCP Interceptor - Quick Start Card

## 30-Second Overview

Capture MCP server communication → Generate mock servers → Run without backend

## Installation

None needed! Already part of the project.

## 3-Step Usage

### 1️⃣ Capture

```python
from mcp_interceptor import install_interceptor

logger = install_interceptor(trace_file="trace.jsonl")
logger.start_session()

# Your MCP code here (automatically captured)

logger.end_session()
```

### 2️⃣ Generate

```bash
uv run python mcp_interceptor/mock_generator.py trace.jsonl -o mock.py
```

### 3️⃣ Run

```bash
uv run python mock.py
```

## Complete Example

```python
#!/usr/bin/env python3
import asyncio
from mcp_interceptor import install_interceptor
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Install interceptor FIRST
logger = install_interceptor(trace_file="session.jsonl", verbose=True)

async def main():
    url = "https://learn.microsoft.com/api/mcp"

    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            logger.start_session(server_info={'url': url})

            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool(tools.tools[0].name, {})

            logger.end_session()
            print("✓ Captured!")

asyncio.run(main())
```

Then:
```bash
uv run python mock_generator.py session.jsonl -o mock_server.py
uv run python mock_server.py
```

## Verify Installation

```bash
uv run python mcp_interceptor/test_workflow.py
```

Should see:
```
✅ ALL TESTS PASSED!
```

## File Outputs

| File | Format | Purpose |
|------|--------|---------|
| `*.jsonl` | NDJSON sessions | Machine-parsable traces |
| `*.log` | NDJSON requests/responses | Human debugging |
| `*_mock.py` | Python | Generated mock server |

## Common Commands

```bash
# Capture real MCP session
uv run python mcp_interceptor/capture_example.py

# Generate mock from trace
uv run python mcp_interceptor/mock_generator.py trace.jsonl -o mock.py

# Run generated mock
uv run python mock.py

# Test everything works
uv run python mcp_interceptor/test_workflow.py
```

## API Cheat Sheet

```python
# Install
logger = install_interceptor(
    trace_file="sessions.jsonl",  # For mock generation
    log_file="debug.log",         # For human debugging (optional)
    verbose=True                   # Print to console
)

# Session
logger.start_session(server_info={'url': '...', 'name': '...'})
logger.end_session()

# Hooks (optional)
logger.add_request_hook(my_function)
logger.add_response_hook(my_function)
```

```python
# Read traces
from mcp_interceptor import TraceReader

reader = TraceReader("trace.jsonl")
sessions = reader.read_sessions()

for session in sessions:
    print(f"{session.session_id}: {len(session.calls)} calls")
```

```python
# Generate mocks programmatically
from mcp_interceptor import MockServerGenerator

generator = MockServerGenerator("trace.jsonl")
generator.generate_mock_server("mock.py", "MyMock")
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Empty trace file | Call `start_session()` and `end_session()` |
| Module not found | Run from project root or add to `sys.path` |
| Interceptor not working | Install BEFORE importing `ClientSession` |
| Mock doesn't match | Check generated `_find_matching_response()` |

## Key Files

| File | Purpose |
|------|---------|
| `trace_format.py` | Data structures |
| `mcp_interceptor.py` | Monkeypatch implementation |
| `mock_generator.py` | Code generator |
| `capture_example.py` | Working example |
| `test_workflow.py` | Integration tests |
| `README.md` | Full documentation |
| `USAGE_GUIDE.md` | Detailed examples |

## What Gets Captured

✅ All MCP methods:
- `initialize()`
- `list_tools()`, `call_tool()`
- `list_resources()`, `read_resource()`
- `list_prompts()`, `get_prompt()`
- `send_roots_list_changed()`

✅ For each call:
- Request (method, args, kwargs, timestamp)
- Response (result or error, timestamp)
- Duration (milliseconds)

## Mock Server Features

✅ Standalone Python file
✅ No dependencies on original server
✅ Replays all recorded responses
✅ Proper MCP protocol implementation
✅ Easy to customize

## Learn More

- **README.md** - Architecture and overview
- **USAGE_GUIDE.md** - Detailed workflows and examples
- **SUMMARY.md** - Implementation details

## Support

Run into issues? Check:
1. `USAGE_GUIDE.md` - Troubleshooting section
2. `test_workflow.py` - Verify installation
3. `capture_example.py` - Working example

---

**Ready to start?**

```bash
uv run python mcp_interceptor/capture_example.py
```
