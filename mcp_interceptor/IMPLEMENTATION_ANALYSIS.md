# MCP Interceptor Implementation Analysis

## Executive Summary

The MCP Interceptor is a transparent monkeypatch system that intercepts and logs all MCP client-server communication without requiring code modifications. It captures detailed request/response data in JSON format and can output to file, console, or both.

---

## Current Interception Mechanism

### Implementation Strategy
**File**: `/Users/yevhenii/projects/explore-mcp/mcp_interceptor/mcp_interceptor.py`

The interceptor uses class-based monkeypatching:

1. **Subclassing Pattern** (lines 95-182):
   - Creates `InterceptedClientSession` that extends the original `mcp.ClientSession`
   - Overrides 8 key async methods with interception wrappers
   - Maintains full API compatibility with original ClientSession

2. **Global Replacement** (lines 184-219):
   - `install_interceptor()` replaces `mcp.ClientSession` globally in two locations:
     - `mcp.ClientSession`
     - `mcp.client.session.ClientSession`
   - Works because clients import ClientSession AFTER calling `install_interceptor()`

3. **Method Interception Pattern** (lines 119-148):
   - `_intercept_call()` wraps all method invocations
   - Executes: log_request → run_hooks → execute_original → log_response → run_hooks
   - Preserves exceptions and return values transparently

### Intercepted Methods (lines 151-182)
```
- initialize()              - Session initialization
- list_tools()             - Tool discovery
- call_tool(*args, **kwargs) - Tool execution
- list_resources()         - Resource discovery
- read_resource(*args, **kwargs) - Resource reading
- list_prompts()           - Prompt discovery
- get_prompt(*args, **kwargs)    - Prompt retrieval
- send_roots_list_changed() - Root change notifications
```

### Critical Requirement
**Installation must occur BEFORE importing ClientSession** (lines 3-8 of example.py):
```python
# CORRECT order
from mcp_interceptor import install_interceptor
install_interceptor()  # Install first
from mcp import ClientSession  # Then import
```

---

## Data Format Currently Being Saved

### Log Structure (lines 24-92)

#### Request Log Entry
**Fields** (lines 29-36):
```json
{
  "type": "request",
  "timestamp": "2025-10-23T10:30:45.123456",  # ISO format
  "count": 1,                                  # Sequential counter
  "method": "call_tool",                       # Method name
  "args": ["tool_name"],                       # Positional arguments
  "kwargs": {"arguments": {"param": "value"}}  # Keyword arguments
}
```

#### Response Log Entry
**Fields** (lines 45-52):
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

#### Error Response
```json
{
  "type": "response",
  "timestamp": "2025-10-23T10:30:45.789012",
  "count": 2,
  "method": "list_tools",
  "result": null,
  "error": "ConnectionError: Failed to connect"
}
```

### Serialization Logic (lines 56-70)
- **Objects with `__dict__`**: Converted to dict with `"_type"` field containing class name, non-private fields included recursively
- **Lists/Tuples**: Recursively serialized
- **Dicts**: Keys and values recursively serialized
- **Primitives** (str, int, float, bool, None): Returned as-is
- **Other types**: Converted to string representation

### Output Format
**File Format** (line 92): Newline-delimited JSON (NDJSON/JSON Lines)
- Each log entry on a single line
- Append mode (opens with 'a')
- One entry per request or response

---

## Structure of MCP Client-Server Communication Captured

### Complete Communication Flow Captured

The interceptor captures both:
1. **Input Layer**: Everything the client sends (method name, args, kwargs)
2. **Output Layer**: Everything the server returns (result or error)
3. **Metadata**: Timestamps and request/response pairing via method name

### Tool Execution Example
From example.py (lines 18-37):
```python
# This sequence is captured:
await session.initialize()        # Request: {"type": "request", "method": "initialize", ...}
                                  # Response: {"type": "response", "method": "initialize", ...}
tools = await session.list_tools() # Request/Response pair for list_tools
await session.call_tool(name, args) # Request/Response pair for call_tool
```

### Data Accessibility
The `InterceptionLogger` tracks:
- `request_count`: Total requests made (line 21)
- `response_count`: Total responses received (line 22)
- Can be queried after execution (test_interceptor.py, lines 31-32)

---

## Existing Mock Server & Generation Code

### Related Systems

#### 1. Discovery System
**Files**: 
- `/Users/yevhenii/projects/explore-mcp/ai_generation/discovery.py` (lines 1-50)
- `/Users/yevhenii/projects/explore-mcp/ai_generation/discovery_models.py`

**Output Format** (discovery.py lines 34-49):
```json
{
  "server_path": "path/to/server.py",
  "transport": "stdio",
  "command": "uv run python path/to/server.py",
  "tools": [
    {
      "name": "tool_name",
      "description": "...",
      "inputSchema": {...},
      "outputSchema": {...}
    }
  ],
  "resources": [{"uri": "...", "name": "...", "mimeType": "..."}],
  "prompts": [{"name": "...", "description": "...", "arguments": [...]}],
  "server_info": {"name": "...", "version": "..."},
  "metadata": {
    "discovered_at": "2024-10-21T...",
    "discovery_method": "mcp-inspector",
    "cache_hit": false,
    "discovery_time_ms": 4500
  }
}
```

**DiscoveryResult Model** (discovery_models.py lines 109-259):
- Type-safe Pydantic models for all components
- Methods: `get_tool_by_name()`, `get_tool_names()`, `summary()`
- Hashing: `compute_file_hash()`, `compute_discovery_hash()`
- Persistence: `save()` method

#### 2. Server Generation System
**File**: `/Users/yevhenii/projects/explore-mcp/ai_generation/server_generator.py`

**Generated Functions** (lines 16-57):
- `generate_ai_mock_responses(tools)` - Creates mock responses for tools
- `generate_ai_mock_resource_content(resources)` - Creates mock resource content
- Uses AIService to call Claude for realistic response generation

**Input**: Tool definitions from discovery
**Output**: Dict mapping tool names to mock response strings

---

## Key Integration Points

### Current Integration Status
The interceptor is **NOT YET integrated** with the generation system:
- Interceptor is standalone in `mcp_interceptor/` directory
- Discovery and generation systems use `ai_generation/` independent pipeline
- No imports between the two systems

### Potential Integration Path
1. **Capture Phase**: Run interceptor against real MCP server to capture actual request/response patterns
2. **Augmentation Phase**: Use captured data to enhance mock response generation (more realistic behavior)
3. **Testing Phase**: Compare intercepted data against mock server behavior for validation

---

## File Reference Summary

### Core Interceptor Files

| File | Purpose | Key Lines |
|------|---------|-----------|
| `mcp_interceptor.py` | Main interceptor logic | 15-219 |
| `example.py` | Working example with HTTP server | 1-42 |
| `test_interceptor.py` | Verification test | 1-36 |
| `INTERCEPTOR_README.md` | Usage documentation | 1-249 |

### Supporting Files

| File | Purpose | Key Lines |
|------|---------|-----------|
| `discovery.py` | MCP server discovery | 101-300+ |
| `discovery_models.py` | Pydantic data models | 30-259 |
| `server_generator.py` | Mock server generation | 16-100+ |

### Data Model Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `InterceptionLogger` | mcp_interceptor.py:15-92 | Handles logging and serialization |
| `InterceptedClientSession` | mcp_interceptor.py:95-182 | Monkeypatched ClientSession |
| `DiscoveryResult` | discovery_models.py:109-285 | Complete discovery output |
| `MCPTool` | discovery_models.py:30-41 | Tool definition model |

---

## Output Characteristics

### Console Output Example
When `verbose=True` (lines 74-88):
```
================================================================================
[MCP REQUEST] call_tool
Timestamp: 2025-10-23T10:30:45.123456
Args: ["my_tool_name"]
Kwargs: {"arguments": {"param": "value"}}
================================================================================

================================================================================
[MCP RESPONSE] call_tool
Timestamp: 2025-10-23T10:30:45.456789
Result: {
  "_type": "CallToolResult",
  "content": [{"type": "text", "text": "..."}]
}
================================================================================
```

### File Output Example
When `log_file="mcp_trace.log"`:
```
{"type": "request", "timestamp": "...", "count": 1, "method": "initialize", ...}
{"type": "response", "timestamp": "...", "count": 1, "method": "initialize", ...}
{"type": "request", "timestamp": "...", "count": 2, "method": "list_tools", ...}
{"type": "response", "timestamp": "...", "count": 2, "method": "list_tools", ...}
```

---

## Performance Notes

- Request logging: ~1ms overhead
- Response logging: ~1-5ms (varies with result size)
- Custom hooks: Variable depending on implementation
- Recommended for production: Disable verbose, use selective hooks

---

## Limitations & Considerations

1. **Only intercepts application layer**: Doesn't capture raw transport-level data
2. **Object serialization**: Complex objects become strings, losing original type info
3. **Hook execution**: Must be async or sync (not generators)
4. **Installation timing**: Must be called before any ClientSession imports
5. **No request/response modification**: Can log and hook, but doesn't modify in-flight data

