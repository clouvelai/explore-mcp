# Core MCP vs FastMCP: Side-by-Side Comparison

This document shows the same functionality implemented with both approaches.

## 📊 Quick Stats

| Metric | Core MCP | FastMCP |
|--------|----------|---------|
| **Lines of code** | 92 | 31 |
| **Code reduction** | - | **66% less code** |
| **Manual schema** | Yes | No (auto-generated) |
| **Learning curve** | Steeper | Gentler |
| **Control level** | Full | High-level |

---

## Example 1: Basic Sum Tool

### Core MCP (92 lines)

```python
"""Simple MCP Server with a sum tool."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create the MCP server instance
app = Server("simple-calculator")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="sum",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "The first number",
                    },
                    "b": {
                        "type": "number",
                        "description": "The second number",
                    },
                },
                "required": ["a", "b"],
            },
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "sum":
        a = arguments.get("a")
        b = arguments.get("b")
        
        if a is None or b is None:
            raise ValueError("Both 'a' and 'b' arguments are required")
        
        result = a + b
        return [
            TextContent(
                type="text",
                text=f"The sum of {a} and {b} is {result}",
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### FastMCP (31 lines)

```python
"""Simple MCP Server with a sum tool using FastMCP."""

from fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP("simple-calculator")

@mcp.tool()
def sum(a: float, b: float) -> str:
    """Add two numbers together.
    
    Args:
        a: The first number
        b: The second number
        
    Returns:
        A message with the sum of the two numbers
    """
    result = a + b
    return f"The sum of {a} and {b} is {result}"

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()
```

---

## Example 2: Multiple Tools with State

### Core MCP

```python
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, ResourceContents

app = Server("advanced-calculator")

# Global state
calculation_history = []

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sum",
            description="Add two numbers",
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
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "sum":
        result = arguments["a"] + arguments["b"]
        calculation_history.append(f"{arguments['a']} + {arguments['b']} = {result}")
        return [TextContent(type="text", text=f"Sum: {result}")]
    
    elif name == "multiply":
        result = arguments["a"] * arguments["b"]
        calculation_history.append(f"{arguments['a']} * {arguments['b']} = {result}")
        return [TextContent(type="text", text=f"Product: {result}")]
    
    raise ValueError(f"Unknown tool: {name}")

@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="calc://history",
            name="Calculation History",
            mimeType="text/plain",
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "calc://history":
        return "\n".join(calculation_history) if calculation_history else "No history"
    raise ValueError(f"Unknown resource: {uri}")
```

### FastMCP

```python
from fastmcp import FastMCP

mcp = FastMCP("advanced-calculator")

# Global state
calculation_history = []

@mcp.tool()
def sum(a: float, b: float) -> str:
    """Add two numbers together."""
    result = a + b
    calculation_history.append(f"{a} + {b} = {result}")
    return f"Sum: {result}"

@mcp.tool()
def multiply(a: float, b: float) -> str:
    """Multiply two numbers together."""
    result = a * b
    calculation_history.append(f"{a} * {b} = {result}")
    return f"Product: {result}"

@mcp.resource("calc://history")
def get_history() -> str:
    """Get the calculation history."""
    return "\n".join(calculation_history) if calculation_history else "No history"
```

**Difference**: FastMCP reduces ~80 lines to ~25 lines (70% reduction)

---

## Example 3: Complex Input Validation

### Core MCP

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "divide":
        # Manual validation
        a = arguments.get("a")
        b = arguments.get("b")
        
        if a is None or b is None:
            raise ValueError("Both arguments required")
        
        if not isinstance(a, (int, float)):
            raise TypeError("'a' must be a number")
        
        if not isinstance(b, (int, float)):
            raise TypeError("'b' must be a number")
        
        if b == 0:
            raise ValueError("Cannot divide by zero")
        
        result = a / b
        return [TextContent(type="text", text=f"Result: {result}")]
```

### FastMCP

```python
@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide one number by another.
    
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return f"Result: {a / b}"

# Type validation happens automatically via type hints!
```

---

## Example 4: Using Pydantic Models

### Core MCP

```python
from pydantic import BaseModel

class CalculationInput(BaseModel):
    operation: str
    numbers: list[float]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "bulk_calculate":
        # Manual parsing and validation
        try:
            input_data = CalculationInput(**arguments)
        except Exception as e:
            return [TextContent(type="text", text=f"Invalid input: {e}")]
        
        if input_data.operation == "sum":
            result = sum(input_data.numbers)
        elif input_data.operation == "product":
            result = 1
            for num in input_data.numbers:
                result *= num
        else:
            return [TextContent(type="text", text="Unknown operation")]
        
        return [TextContent(type="text", text=f"Result: {result}")]
```

### FastMCP

```python
from pydantic import BaseModel

class CalculationInput(BaseModel):
    operation: str
    numbers: list[float]

@mcp.tool()
def bulk_calculate(calc: CalculationInput) -> str:
    """Perform calculations on multiple numbers."""
    if calc.operation == "sum":
        result = sum(calc.numbers)
    elif calc.operation == "product":
        result = 1
        for num in calc.numbers:
            result *= num
    else:
        raise ValueError("Unknown operation")
    
    return f"Result: {result}"

# Pydantic model is automatically converted to JSON Schema!
```

---

## Key Differences Summary

### Core MCP Advantages ✅

1. **Full Protocol Control**: Direct access to all MCP protocol features
2. **Explicit Message Handling**: See exactly how messages are processed
3. **Better for Learning**: Understand MCP internals deeply
4. **Official SDK**: Canonical implementation, always up-to-date with spec
5. **No Abstractions**: What you see is what you get

### FastMCP Advantages ✅

1. **Massive Code Reduction**: 60-70% less boilerplate
2. **Type Safety**: Leverages Python type hints
3. **Auto Schema Generation**: No manual JSON Schema writing
4. **Pythonic API**: Natural decorators and functions
5. **Pydantic Integration**: Seamless model validation
6. **Faster Development**: Rapid prototyping and iteration
7. **Production Ready**: Battle-tested patterns built-in

---

## When to Use Each?

### Use Core MCP When:

- 🎓 **Learning MCP Protocol**: Want to understand how MCP works under the hood
- 🔧 **Custom Protocol Features**: Need access to low-level protocol details
- 📚 **Following Official Docs**: Working through official MCP examples
- 🛠️ **Custom Transports**: Building custom transport layers
- 🔍 **Debugging Protocol Issues**: Need visibility into message flow

### Use FastMCP When:

- ⚡ **Building Servers Quickly**: Want to ship fast
- 🚀 **Production Applications**: Need proven patterns
- 🐍 **Pythonic Code**: Prefer decorator-based APIs
- 📦 **Complex Types**: Using Pydantic models
- 🔌 **Web Integration**: Already using FastAPI/Starlette
- 👥 **Team Projects**: Want readable, maintainable code

---

## Migration Path

Start with Core MCP to learn, migrate to FastMCP for production:

1. **Phase 1 - Learn** (1-2 days)
   - Build simple servers with Core MCP
   - Understand tools, resources, prompts
   - Learn JSON Schema and protocol flow

2. **Phase 2 - Transition** (1 day)
   - Rewrite examples with FastMCP
   - Compare code reduction
   - Learn FastMCP decorators

3. **Phase 3 - Build** (ongoing)
   - Use FastMCP for new servers
   - Leverage type hints and Pydantic
   - Focus on business logic, not protocol

---

## Conclusion

Both libraries have their place:

- **Core MCP** = 🎓 Learning, understanding, protocol work
- **FastMCP** = 🚀 Production, rapid development, maintainability

**Recommendation**: Start with Core MCP to learn, then use FastMCP for real projects!

