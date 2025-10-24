# MCP Client Interceptor

A transparent monkeypatch for the Claude MCP SDK that intercepts all client-server communication.

## Features

- **Transparent interception**: Works with existing code, no API changes required
- **Comprehensive logging**: Captures all requests/responses with timestamps
- **Custom hooks**: Add pre-request and post-response callbacks
- **Flexible output**: Log to file, console, or both
- **Zero side effects**: Can be enabled/disabled without code changes

## Quick Start

```python
from mcp_interceptor import install_interceptor
from mcp import ClientSession

# Install interceptor (monkeypatches globally)
install_interceptor(verbose=True)

# Use MCP client normally - all communication is now intercepted
async with ClientSession(reader, writer) as session:
    await session.initialize()  # Intercepted
    tools = await session.list_tools()  # Intercepted
    result = await session.call_tool("tool_name", {})  # Intercepted
```

## Installation

The interceptor is a single module with no additional dependencies beyond the MCP SDK:

```bash
# Just ensure mcp is installed
pip install mcp
```

## Usage Patterns

### Basic Interception (Console Output)

```python
from mcp_interceptor import install_interceptor

# Enable interception with console output
install_interceptor(verbose=True)

# All ClientSession operations are now intercepted
```

### Log to File

```python
from mcp_interceptor import install_interceptor

# Log all communications to a JSON file
install_interceptor(
    log_file="mcp_trace.log",
    verbose=False  # Disable console output
)
```

### Add Custom Hooks

```python
from mcp_interceptor import install_interceptor, InterceptedClientSession

install_interceptor()

# Pre-request hook
async def on_request(method_name, args, kwargs):
    print(f"Calling {method_name}")
    # Modify args/kwargs if needed

# Post-response hook
async def on_response(method_name, result):
    print(f"Got response from {method_name}")
    # Process result

InterceptedClientSession.add_request_hook(on_request)
InterceptedClientSession.add_response_hook(on_response)
```

### Disable Interception

```python
from mcp_interceptor import uninstall_interceptor

# Restore original ClientSession
uninstall_interceptor()
```

## Intercepted Methods

The following `ClientSession` methods are intercepted:

- `initialize()` - Session initialization
- `list_tools()` - Tool discovery
- `call_tool()` - Tool execution
- `list_resources()` - Resource discovery
- `read_resource()` - Resource reading
- `list_prompts()` - Prompt discovery
- `get_prompt()` - Prompt retrieval
- `send_roots_list_changed()` - Root change notifications

## Log Format

Logs are written as newline-delimited JSON:

### Request Log Entry
```json
{
  "type": "request",
  "timestamp": "2025-10-23T10:30:45.123456",
  "count": 1,
  "method": "call_tool",
  "args": ["tool_name"],
  "kwargs": {"arguments": {"param": "value"}}
}
```

### Response Log Entry
```json
{
  "type": "response",
  "timestamp": "2025-10-23T10:30:45.456789",
  "count": 1,
  "method": "call_tool",
  "result": {
    "_type": "CallToolResult",
    "content": [{"type": "text", "text": "Result data"}]
  },
  "error": null
}
```

## Use Cases

### Debugging
```python
# See exactly what's being sent to/from MCP servers
install_interceptor(verbose=True)
```

### Testing
```python
# Verify request/response patterns
logger = install_interceptor(log_file="test_trace.log")
# ... run tests ...
print(f"Made {logger.request_count} requests")
```

### Monitoring
```python
# Track MCP usage in production
async def track_metrics(method_name, result):
    metrics.increment(f"mcp.{method_name}")

InterceptedClientSession.add_response_hook(track_metrics)
```

### Request Modification
```python
# Add authentication, rate limiting, etc.
async def add_auth(method_name, args, kwargs):
    kwargs['headers'] = {'Authorization': f'Bearer {token}'}

InterceptedClientSession.add_request_hook(add_auth)
```

## Architecture

The interceptor works by:

1. Subclassing `ClientSession` as `InterceptedClientSession`
2. Overriding all key async methods to add interception logic
3. Replacing `mcp.ClientSession` with the intercepted version

The monkeypatch is transparent because:
- The intercepted class maintains the same API
- All method signatures are preserved
- Exceptions propagate correctly
- Return values are unchanged

## Examples

See the example files:

- `example_with_interceptor.py` - Complete working example
- `traverse_ressource_intercepted.py` - Modified version of existing code

## Performance

The interceptor adds minimal overhead:
- Request logging: ~1ms
- Response logging: ~1-5ms (depending on result size)
- Custom hooks: Depends on hook implementation

For production use, disable verbose mode and use selective hooks.

## Thread Safety

The interceptor is async-safe and works with concurrent MCP sessions.

## Limitations

- Only intercepts `ClientSession` methods (not transport-level communication)
- Custom hooks must be async or sync (not generators)
- Logged data is serialized (complex objects become strings)

## Troubleshooting

### Interceptor not working
Ensure `install_interceptor()` is called **before** importing/using `ClientSession`:

```python
# CORRECT
from mcp_interceptor import install_interceptor
install_interceptor()
from mcp import ClientSession

# WRONG - ClientSession already imported
from mcp import ClientSession
from mcp_interceptor import install_interceptor
install_interceptor()  # Too late!
```

### Import errors
The interceptor requires the MCP SDK's `ClientSession` to be available:

```python
pip install mcp>=1.0.0
```

### Hook errors breaking execution
Wrap hooks in try/except to prevent failures:

```python
async def safe_hook(method_name, result):
    try:
        # Your hook logic
        pass
    except Exception as e:
        print(f"Hook error: {e}")
```

## License

Same as the MCP automation platform.
