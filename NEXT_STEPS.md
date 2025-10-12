# Next Steps: Building More Complex MCP Servers

Now that you have a working MCP server with a basic tool, here's a guide to expanding its capabilities.

## 1. Adding More Tools

### Example: Calculator with Multiple Operations

```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sum",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        ),
        Tool(
            name="multiply",
            description="Multiply two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
        ),
        Tool(
            name="power",
            description="Raise a number to a power",
            inputSchema={
                "type": "object",
                "properties": {
                    "base": {"type": "number", "description": "Base number"},
                    "exponent": {"type": "number", "description": "Exponent"},
                },
                "required": ["base", "exponent"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "sum":
        result = arguments["a"] + arguments["b"]
        return [TextContent(type="text", text=f"Sum: {result}")]
    
    elif name == "multiply":
        result = arguments["a"] * arguments["b"]
        return [TextContent(type="text", text=f"Product: {result}")]
    
    elif name == "power":
        result = arguments["base"] ** arguments["exponent"]
        return [TextContent(type="text", text=f"Result: {result}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")
```

## 2. Adding Resources

Resources allow you to expose data that can be read. This is useful for providing context to LLMs.

```python
from mcp.types import Resource, ResourceContents, TextResourceContents

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="calc://history",
            name="Calculation History",
            description="History of all calculations performed",
            mimeType="text/plain",
        )
    ]

# Store calculation history
calculation_history = []

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri == "calc://history":
        if not calculation_history:
            return "No calculations yet"
        return "\n".join(calculation_history)
    else:
        raise ValueError(f"Unknown resource: {uri}")

# Update call_tool to record history
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "sum":
        result = arguments["a"] + arguments["b"]
        # Record in history
        calculation_history.append(f"{arguments['a']} + {arguments['b']} = {result}")
        return [TextContent(type="text", text=f"Sum: {result}")]
    # ... other tools
```

## 3. Adding Prompts

Prompts are reusable templates that can be invoked by users or LLMs.

```python
from mcp.types import Prompt, PromptMessage, GetPromptResult

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="explain-calculation",
            description="Explain a mathematical calculation step by step",
            arguments=[
                {
                    "name": "calculation",
                    "description": "The calculation to explain (e.g., '5 + 3')",
                    "required": True,
                }
            ],
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Get a prompt by name."""
    if name == "explain-calculation":
        calc = arguments.get("calculation", "")
        return GetPromptResult(
            description=f"Explain the calculation: {calc}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Please explain step-by-step how to calculate: {calc}",
                    ),
                )
            ],
        )
    else:
        raise ValueError(f"Unknown prompt: {name}")
```

## 4. Adding Server Capabilities

Declare what your server can do during initialization:

```python
from mcp.server.models import InitializationOptions

async def main():
    """Run the MCP server with capabilities."""
    options = InitializationOptions(
        server_name="advanced-calculator",
        server_version="1.0.0",
        capabilities={
            "tools": {},  # Supports tools
            "resources": {"subscribe": True},  # Supports resources with subscriptions
            "prompts": {},  # Supports prompts
        },
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            options,
        )
```

## 5. Error Handling Best Practices

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "divide":
            a = arguments.get("a")
            b = arguments.get("b")
            
            # Validate inputs
            if a is None or b is None:
                raise ValueError("Both 'a' and 'b' are required")
            
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                raise TypeError("Arguments must be numbers")
            
            if b == 0:
                raise ValueError("Cannot divide by zero")
            
            result = a / b
            return [TextContent(type="text", text=f"Result: {result}")]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        # Return error as text content
        return [TextContent(type="text", text=f"Error: {str(e)}")]
```

## 6. Using Different Transport Layers

### HTTP/SSE Transport (for web applications)

```python
from mcp.server.sse import sse_server
from starlette.applications import Starlette
from starlette.routing import Route

async def handle_sse(request):
    """Handle SSE connections."""
    async with sse_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

# Create Starlette app
routes = [Route("/sse", endpoint=handle_sse)]
web_app = Starlette(routes=routes)
```

## 7. State Management

```python
class CalculatorState:
    """Manage calculator state."""
    def __init__(self):
        self.history: list[str] = []
        self.variables: dict[str, float] = {}
    
    def add_to_history(self, operation: str, result: float):
        self.history.append(f"{operation} = {result}")
    
    def set_variable(self, name: str, value: float):
        self.variables[name] = value
    
    def get_variable(self, name: str) -> float:
        return self.variables.get(name, 0)

# Global state
state = CalculatorState()

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "store_variable":
        name = arguments["name"]
        value = arguments["value"]
        state.set_variable(name, value)
        return [TextContent(type="text", text=f"Stored {name} = {value}")]
    
    elif name == "recall_variable":
        name = arguments["name"]
        value = state.get_variable(name)
        return [TextContent(type="text", text=f"{name} = {value}")]
```

## 8. Testing Your Server

Create a test file `test_server.py`:

```python
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_sum_tool():
    """Test the sum tool."""
    server_params = StdioServerParameters(
        command="python", args=["server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool("sum", {"a": 5, "b": 3})
            assert result.content[0].text == "The sum of 5 and 3 is 8"

@pytest.mark.asyncio
async def test_list_tools():
    """Test listing tools."""
    server_params = StdioServerParameters(
        command="python", args=["server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            assert "sum" in tool_names
```

Run tests with:
```bash
uv run pytest
```

## 9. Real-World Examples

### File System Server

```python
Tool(
    name="read_file",
    description="Read contents of a file",
    inputSchema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"],
    },
)
```

### API Integration Server

```python
Tool(
    name="fetch_weather",
    description="Get weather for a location",
    inputSchema={
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "country": {"type": "string"},
        },
        "required": ["city"],
    },
)
```

### Database Query Server

```python
Tool(
    name="query_users",
    description="Query user database",
    inputSchema={
        "type": "object",
        "properties": {
            "filter": {"type": "string"},
            "limit": {"type": "integer"},
        },
    },
)
```

## Additional Resources

- **Official Examples**: Check `examples/` directory in the [python-sdk repo](https://github.com/modelcontextprotocol/python-sdk)
- **MCP Specification**: [spec.modelcontextprotocol.io](https://spec.modelcontextprotocol.io/)
- **Community Servers**: Browse the [MCP Registry](https://github.com/modelcontextprotocol/servers)

## Tips for Building Complex Servers

1. **Start simple**: Add one feature at a time
2. **Test thoroughly**: Write tests for each tool
3. **Handle errors gracefully**: Always validate inputs
4. **Document your schema**: Use clear descriptions in JSON Schema
5. **Think about state**: Decide if your server needs to maintain state
6. **Consider security**: Validate all inputs, be careful with file access
7. **Use logging**: Add logging to debug issues
8. **Performance**: Use async/await properly for I/O operations

Happy building! 🚀

