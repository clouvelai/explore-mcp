# Explore MCP - Learning Model Context Protocol

This project is a hands-on introduction to building MCP (Model Context Protocol) servers and clients. It starts with a simple example and can be extended to explore more complex functionality.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). It enables:

- **Tools**: Functions that LLMs can call to take actions
- **Resources**: Data sources that can be read and monitored
- **Prompts**: Reusable prompt templates

## Project Structure

```
explore-mcp/
├── server.py          # MCP server with sum tool
├── client.py          # Test client for the server
├── pyproject.toml     # Project dependencies
└── README.md          # This file
```

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

## Setup

1. **Install dependencies:**

```bash
uv sync
```

This will:
- Create a virtual environment
- Install all required packages (mcp, fastmcp)
- Lock dependency versions

## Running the Example

### Option 1: Run the client (recommended)

The client automatically starts the server and tests the sum tool:

```bash
uv run python client.py
```

Expected output:
```
🚀 Connecting to MCP server...
✅ Connected to server

📋 Available tools:
  - sum: Add two numbers together

🧮 Testing sum tool:
  5 + 3 → The sum of 5 and 3 is 8
  10 + 20 → The sum of 10 and 20 is 30
  -5 + 15 → The sum of -5 and 15 is 10
  3.14 + 2.86 → The sum of 3.14 and 2.86 is 6.0

✨ All tests completed successfully!
```

### Option 2: Run the server standalone

```bash
uv run python server.py
```

The server will run in stdio mode, waiting for input. This is useful for debugging or connecting with other MCP clients.

## Understanding the Code

### Server (`server.py`)

The server uses **FastMCP**, a high-level framework that makes MCP servers simple:

1. **Server Creation**: 
   ```python
   from fastmcp import FastMCP
   mcp = FastMCP("simple-calculator")
   ```

2. **Tool Definition**: Use the `@mcp.tool()` decorator with type hints
   ```python
   @mcp.tool()
   def sum(a: float, b: float) -> str:
       """Add two numbers together.
       
       Args:
           a: The first number
           b: The second number
       """
       result = a + b
       return f"The sum of {a} and {b} is {result}"
   ```

FastMCP automatically:
- ✨ Generates JSON Schema from type hints
- 🎯 Handles message routing
- 📝 Uses docstrings for descriptions
- 🚀 Sets up stdio transport

### Client (`client.py`)

The client demonstrates how to:

1. **Connect to a server** via stdio
2. **List available tools** 
3. **Call tools** with arguments
4. **Parse results** from tool calls

## MCP Concepts Demonstrated

### Tools

Tools are functions that can be called by LLMs. Each tool has:
- **Name**: Unique identifier (e.g., "sum")
- **Description**: What the tool does
- **Input Schema**: JSON Schema defining expected parameters
- **Output**: Results returned to the caller

In this example, the `sum` tool:
- Takes two numbers (`a` and `b`)
- Returns their sum as text
- FastMCP auto-generates JSON Schema from type hints (`float`)

### Why FastMCP?

We use **FastMCP** instead of the core MCP library because:
- ✅ **Less boilerplate**: 31 lines vs 92 lines for the same functionality
- ✅ **Type safety**: Uses Python type hints (no manual JSON Schema)
- ✅ **Pythonic**: Decorators like `@mcp.tool()` feel natural
- ✅ **Auto-documentation**: Extracts descriptions from docstrings
- ✅ **Production-ready**: Used by real-world MCP servers

Want to see how the core MCP library works? Check `NEXT_STEPS.md` for examples!

## Next Steps - Building Up Complexity

Now that you have a basic server working, here are some ideas to expand your learning:

### 1. Add More Tools

```python
@mcp.tool()
def multiply(a: float, b: float) -> str:
    """Multiply two numbers together."""
    result = a * b
    return f"The product of {a} and {b} is {result}"

@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide one number by another."""
    if b == 0:
        return "Error: Cannot divide by zero"
    result = a / b
    return f"{a} divided by {b} is {result}"
```

### 2. Add Resources

Resources expose data that can be read:
```python
# Store calculation history
history = []

@mcp.resource("calc://history")
def get_history() -> str:
    """Get the calculation history."""
    if not history:
        return "No calculations yet"
    return "\n".join(history)

# Update tools to record history
@mcp.tool()
def sum(a: float, b: float) -> str:
    result = a + b
    history.append(f"{a} + {b} = {result}")
    return f"The sum of {a} and {b} is {result}"
```

### 3. Add Prompts

Prompts are reusable templates:
```python
@mcp.prompt()
def math_tutor(problem: str) -> str:
    """Help solve a math problem step by step.
    
    Args:
        problem: The math problem to solve
    """
    return f"Let's solve this step by step: {problem}"
```

### 4. Add Error Handling

Improve error handling for invalid inputs:
```python
@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide one number by another."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    return f"{a} divided by {b} is {result}"
```

### 5. Add Context and Dependencies

Use FastMCP's context system for shared state:
```python
from fastmcp import Context

# Create a context class to hold shared state
class CalculatorContext:
    def __init__(self):
        self.history = []

@mcp.tool()
def sum_with_history(a: float, b: float, ctx: Context[CalculatorContext]) -> str:
    """Add two numbers and save to history."""
    result = a + b
    ctx.history.append(f"{a} + {b} = {result}")
    return f"Result: {result}"
```

### 6. Add More Complex Types

Use Pydantic models for complex inputs:
```python
from pydantic import BaseModel

class Calculation(BaseModel):
    operation: str
    numbers: list[float]

@mcp.tool()
def calculate(calc: Calculation) -> str:
    """Perform calculations on a list of numbers."""
    if calc.operation == "sum":
        result = sum(calc.numbers)
        return f"Sum: {result}"
    elif calc.operation == "product":
        result = 1
        for num in calc.numbers:
            result *= num
        return f"Product: {result}"
```

## Resources

- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Core MCP vs FastMCP Comparison](NEXT_STEPS.md)

## Troubleshooting

### Import Errors

If you see import errors, make sure you're running commands with `uv run`:
```bash
uv run python client.py
```

### Connection Issues

If the client can't connect to the server:
1. Check that `server.py` is in the same directory
2. Verify Python is in your PATH
3. Try running the server standalone first

### Dependency Issues

If dependencies aren't installing:
```bash
# Clear cache and reinstall
rm -rf .venv uv.lock
uv sync
```

## License

MIT License - Feel free to use this for learning and experimentation!

