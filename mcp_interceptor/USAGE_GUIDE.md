# MCP Interceptor & Mock Generator - Usage Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Detailed Workflows](#detailed-workflows)
5. [API Reference](#api-reference)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)

## Introduction

This toolkit enables you to:
- **Capture** MCP client-server communication transparently
- **Record** interactions in a machine-parsable format
- **Generate** mock MCP servers that replay recorded responses

### Use Cases

- 🧪 **Testing**: Create deterministic test environments
- 📊 **Development**: Work offline with recorded responses
- 🔍 **Debugging**: Analyze MCP communication patterns
- 📚 **Documentation**: Generate examples from real interactions
- 🚀 **CI/CD**: Run tests without external dependencies

## Installation

The interceptor is already part of this project. No additional installation needed!

```bash
# Verify installation
uv run python mcp_interceptor/test_workflow.py
```

## Quick Start

### 3-Step Workflow

#### Step 1: Capture an MCP Session

```python
# my_capture.py
import asyncio
from mcp_interceptor import install_interceptor
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Install interceptor FIRST
logger = install_interceptor(trace_file="session.jsonl")

async def capture():
    url = "https://learn.microsoft.com/api/mcp"

    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            # Start tracking
            logger.start_session(server_info={'url': url})

            # Your normal MCP code - all calls are captured
            await session.initialize()
            tools = await session.list_tools()

            for tool in tools.tools[:3]:  # Test first 3 tools
                result = await session.call_tool(tool.name, {})

            # Save to file
            logger.end_session()

asyncio.run(capture())
```

#### Step 2: Generate Mock Server

```bash
uv run python mcp_interceptor/mock_generator.py session.jsonl -o my_mock.py
```

#### Step 3: Run Mock Server

```bash
uv run python my_mock.py
```

Done! Your mock server now replays all recorded responses.

## Detailed Workflows

### Workflow 1: Capturing from Public MCP Server

**Goal**: Create a mock of Microsoft's documentation MCP server

```python
# capture_microsoft.py
import asyncio
from mcp_interceptor import install_interceptor
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = install_interceptor(
    trace_file="microsoft_sessions.jsonl",
    log_file="microsoft_debug.log",  # Optional: for debugging
    verbose=True
)

async def main():
    url = "https://learn.microsoft.com/api/mcp"

    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            logger.start_session(server_info={
                'url': url,
                'name': 'microsoft-learn',
                'description': 'Microsoft Learn Documentation Server'
            })

            # Initialize
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools")

            # Test each tool with sample data
            for tool in tools.tools:
                print(f"Testing: {tool.name}")

                # Build sample arguments
                schema = tool.inputSchema
                args = {}
                for prop, details in schema.get('properties', {}).items():
                    if details.get('type') == 'string':
                        args[prop] = "test"

                try:
                    await session.call_tool(tool.name, args)
                except Exception as e:
                    print(f"  Error: {e}")

            logger.end_session()
            print("✓ Session captured!")

asyncio.run(main())
```

Run it:
```bash
uv run python capture_microsoft.py
uv run python mcp_interceptor/mock_generator.py microsoft_sessions.jsonl -o microsoft_mock.py
```

### Workflow 2: Capturing from Local MCP Server

**Goal**: Create a mock of your custom MCP server

```python
# capture_local.py
import asyncio
from mcp_interceptor import install_interceptor
from mcp import ClientSession
from mcp.client.stdio import stdio_client

logger = install_interceptor(trace_file="local_sessions.jsonl")

async def main():
    # Connect to local server via stdio
    server_params = {
        "command": "uv",
        "args": ["run", "python", "mcp_servers/calculator/server.py"]
    }

    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            logger.start_session(server_info={
                'type': 'stdio',
                'command': server_params['command'],
                'args': server_params['args']
            })

            await session.initialize()
            tools = await session.list_tools()

            # Test calculator tools
            if tools.tools:
                # Test add
                await session.call_tool("add", {"a": 5, "b": 3})
                # Test multiply
                await session.call_tool("multiply", {"a": 4, "b": 7})

            logger.end_session()

asyncio.run(main())
```

### Workflow 3: Batch Capturing Multiple Scenarios

**Goal**: Capture different usage patterns for comprehensive mocks

```python
# capture_scenarios.py
import asyncio
from mcp_interceptor import install_interceptor
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = install_interceptor(trace_file="all_scenarios.jsonl")

async def scenario_1_basic():
    """Basic usage scenario"""
    async with streamablehttp_client("http://example.com/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            logger.start_session(server_info={'scenario': 'basic'})
            await session.initialize()
            await session.list_tools()
            logger.end_session()

async def scenario_2_advanced():
    """Advanced usage with tool calls"""
    async with streamablehttp_client("http://example.com/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            logger.start_session(server_info={'scenario': 'advanced'})
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                await session.call_tool(tool.name, {})
            logger.end_session()

async def main():
    await scenario_1_basic()
    await scenario_2_advanced()
    print("✓ All scenarios captured!")

asyncio.run(main())
```

This creates a trace file with multiple sessions - one per scenario.

### Workflow 4: Customizing Generated Mocks

After generating a mock, you can customize it:

```python
# Customize mock_server.py

# Add custom logic
class MyCustomMock(MockMCPServer):
    async def handle_call_tool(self, name: str, arguments: dict):
        # Add logging
        print(f"Tool called: {name}")

        # Add custom behavior for specific tools
        if name == "special_tool":
            return self._custom_special_logic(arguments)

        # Fall back to recorded responses
        return await super().handle_call_tool(name, arguments)

    def _custom_special_logic(self, arguments):
        # Your custom logic here
        return CallToolResult(
            content=[TextContent(type='text', text='Custom response')],
            isError=False
        )
```

## API Reference

### install_interceptor()

```python
logger = install_interceptor(
    log_file: Optional[str] = None,      # Legacy NDJSON format
    trace_file: Optional[str] = None,    # Structured session format
    verbose: bool = True                  # Print to console
) -> InterceptionLogger
```

**Returns**: `InterceptionLogger` instance

**Example**:
```python
logger = install_interceptor(
    trace_file="trace.jsonl",
    verbose=False
)
```

### InterceptionLogger

```python
class InterceptionLogger:
    def start_session(self, server_info: dict = None)
    def end_session(self)
    def log_request(self, method: str, *args, **kwargs)
    def log_response(self, method: str, result: Any, error: Exception = None)
    def add_request_hook(self, hook: Callable)
    def add_response_hook(self, hook: Callable)
```

**Example**:
```python
logger = install_interceptor(trace_file="trace.jsonl")

# Start session
logger.start_session(server_info={'url': 'http://example.com'})

# Automatic logging happens via monkeypatch
# ...

# End session
logger.end_session()
```

### MockServerGenerator

```python
class MockServerGenerator:
    def __init__(self, trace_file: str)
    def analyze_sessions(self) -> Dict[str, Any]
    def generate_mock_server(self, output_file: str, server_name: str = "MockMCPServer")
```

**Example**:
```python
from mcp_interceptor import MockServerGenerator

generator = MockServerGenerator("trace.jsonl")

# Analyze
analysis = generator.analyze_sessions()
print(f"Methods captured: {analysis['methods']}")

# Generate
generator.generate_mock_server("my_mock.py", "MyMock")
```

### TraceReader / TraceWriter

```python
class TraceWriter:
    def __init__(self, output_file: str)
    def write_session(self, session: MCPSession, append: bool = True)
    def write_sessions(self, sessions: List[MCPSession])

class TraceReader:
    def __init__(self, trace_file: str)
    def read_sessions(self) -> List[MCPSession]
    def read_latest_session(self) -> Optional[MCPSession]
```

**Example**:
```python
from mcp_interceptor import TraceReader, MCPSession

# Read sessions
reader = TraceReader("trace.jsonl")
sessions = reader.read_sessions()

for session in sessions:
    print(f"Session {session.session_id}: {len(session.calls)} calls")
```

## Advanced Usage

### Custom Hooks

Add custom logic before/after each MCP call:

```python
logger = install_interceptor(trace_file="trace.jsonl")

# Log to external system
async def send_to_analytics(method, args, kwargs):
    await analytics_client.track(f"mcp.{method}", {
        'args': args,
        'kwargs': kwargs
    })

logger.add_request_hook(send_to_analytics)

# Validate responses
def validate_result(method, result):
    if method == "call_tool" and not result:
        raise ValueError(f"Null result for {method}")

logger.add_response_hook(validate_result)
```

### Analyzing Traces Programmatically

```python
from mcp_interceptor import TraceReader

reader = TraceReader("trace.jsonl")
sessions = reader.read_sessions()

# Performance analysis
for session in sessions:
    total_time = sum(call.duration_ms for call in session.calls)
    print(f"Session {session.session_id}: {total_time:.2f}ms total")

    # Find slow calls
    slow_calls = [c for c in session.calls if c.duration_ms > 1000]
    if slow_calls:
        print(f"  Slow calls: {len(slow_calls)}")
        for call in slow_calls:
            print(f"    - {call.request.method}: {call.duration_ms:.2f}ms")

# Method usage statistics
method_counts = {}
for session in sessions:
    for call in session.calls:
        method = call.request.method
        method_counts[method] = method_counts.get(method, 0) + 1

print("\nMethod usage:")
for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
    print(f"  {method}: {count} calls")
```

### Filtering Traces

```python
from mcp_interceptor import TraceReader, TraceWriter

# Read all sessions
reader = TraceReader("all_sessions.jsonl")
sessions = reader.read_sessions()

# Filter successful sessions only
successful = [s for s in sessions if all(c.response.success for c in s.calls)]

# Write filtered sessions
writer = TraceWriter("successful_sessions.jsonl")
writer.write_sessions(successful)
```

### Merging Multiple Traces

```python
from mcp_interceptor import TraceReader, TraceWriter

# Read from multiple files
readers = [
    TraceReader("trace1.jsonl"),
    TraceReader("trace2.jsonl"),
    TraceReader("trace3.jsonl")
]

all_sessions = []
for reader in readers:
    all_sessions.extend(reader.read_sessions())

# Write merged trace
writer = TraceWriter("merged.jsonl")
writer.write_sessions(all_sessions)

print(f"Merged {len(all_sessions)} sessions")
```

## Troubleshooting

### Problem: "Module not found: mcp_interceptor"

**Solution**: Make sure you're running from the project root:

```bash
cd /Users/yevhenii/projects/explore-mcp
uv run python mcp_interceptor/your_script.py
```

Or add to Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Problem: Trace file is empty

**Solution**: Make sure to call `start_session()` and `end_session()`:

```python
logger = install_interceptor(trace_file="trace.jsonl")
logger.start_session()  # ← Don't forget!

# ... your MCP code ...

logger.end_session()    # ← Don't forget!
```

### Problem: Mock server doesn't match requests

**Solution**: The generator uses flexible matching. Check the generated code:

```python
# In generated mock_server.py
def _find_matching_response(self, method, args, kwargs):
    # Add debug logging
    print(f"Looking for: method={method}, args={args}, kwargs={kwargs}")
    # ... rest of method
```

### Problem: Interceptor not capturing calls

**Solution**: Install interceptor BEFORE importing ClientSession:

```python
# ✗ WRONG ORDER
from mcp import ClientSession
from mcp_interceptor import install_interceptor
install_interceptor()

# ✓ CORRECT ORDER
from mcp_interceptor import install_interceptor
install_interceptor()
from mcp import ClientSession
```

### Problem: Generated mock has syntax errors

**Solution**: The generator escapes strings, but complex nested structures might need manual fixes. Check:

```bash
# Validate Python syntax
python -m py_compile mock_server.py
```

## Best Practices

### 1. Organize Traces by Purpose

```bash
traces/
  ├── production/
  │   ├── microsoft_learn.jsonl
  │   └── github_api.jsonl
  ├── development/
  │   ├── local_calculator.jsonl
  │   └── test_server.jsonl
  └── ci/
      └── regression_tests.jsonl
```

### 2. Include Metadata

```python
logger.start_session(server_info={
    'url': url,
    'environment': 'production',
    'date': datetime.now().isoformat(),
    'purpose': 'regression-testing',
    'author': 'team@example.com'
})
```

### 3. Version Your Traces

```bash
# Tag traces with versions
mv trace.jsonl traces/v1.0.0/microsoft_learn.jsonl
git add traces/v1.0.0/microsoft_learn.jsonl
git commit -m "Add Microsoft Learn MCP trace v1.0.0"
```

### 4. Test Generated Mocks

```python
# test_mock.py
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def test():
    async with stdio_client({"command": "python", "args": ["mock_server.py"]}) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) > 0, "Should have tools"
            print("✓ Mock server works!")

asyncio.run(test())
```

## Examples

All examples are in the `mcp_interceptor/` directory:

- **`capture_example.py`** - Complete capture workflow
- **`test_workflow.py`** - Automated tests
- **`example.py`** - Simple usage example

Run them:

```bash
uv run python mcp_interceptor/capture_example.py
uv run python mcp_interceptor/test_workflow.py
```

## Next Steps

1. **Capture your first session**: Use `capture_example.py` as a template
2. **Generate a mock**: Run the mock generator on your trace
3. **Test the mock**: Verify it works with your application
4. **Customize**: Modify the generated code for your needs

Happy mocking! 🎭
