# MCP Interceptor - Quick Reference Card

## Installation & Usage

```python
# BEFORE any ClientSession imports
from mcp_interceptor import install_interceptor
logger = install_interceptor(
    log_file="mcp_trace.log",  # Optional
    verbose=True               # Optional
)

# NOW import ClientSession
from mcp import ClientSession
```

## Key Classes

### InterceptionLogger
- Handles all logging and serialization
- Tracks `request_count` and `response_count`
- Writes newline-delimited JSON

### InterceptedClientSession
- Extends original ClientSession
- All methods transparently intercepted
- Added request/response hooks support

## Intercepted Methods

| Method | Purpose |
|--------|---------|
| initialize() | Start session |
| list_tools() | Get available tools |
| call_tool(name, args) | Execute tool |
| list_resources() | Get resources |
| read_resource(uri) | Read resource content |
| list_prompts() | Get prompts |
| get_prompt(name, args) | Get prompt |
| send_roots_list_changed() | Notify roots changed |

## Log Entry Structure

### Request
```json
{
  "type": "request",
  "timestamp": "ISO-8601",
  "count": 1,
  "method": "call_tool",
  "args": [...],
  "kwargs": {...}
}
```

### Response
```json
{
  "type": "response",
  "timestamp": "ISO-8601",
  "count": 1,
  "method": "call_tool",
  "result": {...},
  "error": null
}
```

## File Paths

| File | Purpose |
|------|---------|
| `/Users/yevhenii/projects/explore-mcp/mcp_interceptor/mcp_interceptor.py` | Main implementation |
| `/Users/yevhenii/projects/explore-mcp/mcp_interceptor/example.py` | Working example |
| `/Users/yevhenii/projects/explore-mcp/mcp_interceptor/test_interceptor.py` | Test example |
| `/Users/yevhenii/projects/explore-mcp/mcp_interceptor/INTERCEPTOR_README.md` | Full docs |

## Custom Hooks

```python
from mcp_interceptor import InterceptedClientSession

# Pre-request hook
async def on_request(method_name, args, kwargs):
    print(f"Calling {method_name}")

# Post-response hook  
async def on_response(method_name, result):
    print(f"Response from {method_name}")

InterceptedClientSession.add_request_hook(on_request)
InterceptedClientSession.add_response_hook(on_response)
```

## Output Format

- **File format**: Newline-delimited JSON (one entry per line)
- **Timestamps**: ISO-8601 format
- **Serialization**: Objects → dict with "_type" field, primitives as-is
- **Console**: Pretty-printed with separators (when verbose=True)

## Related Systems

| System | Location | Purpose |
|--------|----------|---------|
| Discovery | `ai_generation/discovery.py` | Discovers server tools/resources |
| Models | `ai_generation/discovery_models.py` | Pydantic models for discovery |
| Generation | `ai_generation/server_generator.py` | Generates mock servers |

