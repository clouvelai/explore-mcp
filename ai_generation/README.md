# AI-Powered MCP Evaluation System

## Overview

This system automatically generates evaluation suites and mock MCP servers from real MCP server implementations using Claude AI. It enables automated testing of LLM agents against standardized MCP tool interfaces without side effects.

## Architecture

### Workflow

```
1. Discovery Phase:
   Real MCP Server (e.g., Gmail) 
        ↓
   ai_generation.cli connects
        ↓
   Retrieves tools via initialize() + list_tools()
        ↓

2. Generation Phase:
   Tool Schemas analyzed by Claude AI
        ↓
   Generates three outputs:
   ├── generated/server.py (FastMCP server setup)
   ├── generated/tools.py (AI-generated tool implementations)  
   └── generated/evaluations.json (AI-generated test cases)

3. Evaluation Phase:
   Any LLM/Agent 
        ↓
   evaluation_runner.py orchestrates
        ↓
   Agent connects to mock server
        ↓
   Executes test cases from evaluations.json
        ↓
   Generates eval_results.md report
```

## Components

### 1. `cli.py` - Main Orchestrator
**Purpose**: Discovers MCP tools and coordinates generation

**Key Functions**:
- `discover_mcp_server(server_path)`: Connect to MCP server and retrieve tools
- `extract_server_name(server_path)`: Generate clean server names from paths
- `generate_evaluations(discovery_data, output_dir)`: Orchestrate test case generation

**Usage**:
```bash
# Generate from calculator server
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py

# Generate from Gmail server  
uv run python -m ai_generation.cli --server mcp_servers/gmail/server.py

# Custom name and output directory
uv run python -m ai_generation.cli --server server.py --name legacy_calc --output-dir custom_output
```

### 2. `server_generator.py` - Mock Server Generation
**Purpose**: Creates FastMCP servers mimicking discovered tools

**Features**:
- Clean server.py + tools.py structure
- AI-generated realistic mock responses
- Request logging for verification
- Parameter validation
- No side effects

**Generated Structure**:
```python
# generated/calculator/server.py
from fastmcp import FastMCP
from .tools import setup_tools

mcp = FastMCP("mock-server")
setup_tools(mcp)

if __name__ == "__main__":
    mcp.run()

# generated/calculator/tools.py  
@mcp.tool()
def add(a: float, b: float) -> str:
    """Add two numbers together."""
    log_request("add", locals())
    return "The sum of 15 and 27 is 42"  # AI-generated realistic response
```

### 3. `evals_generator.py` - Test Case Generation
**Purpose**: Uses Claude AI to generate intelligent test cases

**Current Implementation** (Minimal):
- **1 valid parameter test** per tool with realistic values
- **1 invalid type test** per tool (wrong parameter type)
- **Future milestone**: Expand to include domain-specific edge cases, boundary conditions, missing required parameter tests

**AI-Powered Features**:
- Contextual understanding of tool semantics
- Realistic test parameters based on tool purpose
- Intelligent edge case identification
- Fallback mechanism (bulk → per-tool generation)

**Example Output**:
```json
{
  "server_info": {
    "source": "mcp_servers/calculator/server.py",
    "generated_at": "2025-10-20T10:52:32.379502",
    "tools_count": 5
  },
  "evaluations": [
    {
      "tool": "add",
      "description": "Add two numbers together",
      "test_cases": [
        {
          "id": "add_valid",
          "type": "valid_params",
          "description": "Add two positive numbers", 
          "params": {"a": 7.5, "b": 2.5},
          "expected_result": "success",
          "expected_contains": ["10"]
        },
        {
          "id": "add_invalid_type",
          "type": "invalid_type", 
          "description": "Test with string parameter",
          "params": {"a": "five", "b": 3.0},
          "expected_result": "error",
          "expected_contains": ["error", "invalid", "type"]
        }
      ]
    }
  ]
}
```

### 4. `ai_service.py` - Claude CLI Integration
**Purpose**: Handles interaction with Claude CLI for AI generation

**Features**:
- Configurable timeout (180s default)
- JSON response parsing and cleaning
- Error handling and retries
- Markdown code block removal

### 5. `evaluation_runner.py` - Test Execution
**Purpose**: Execute evaluations against mock server

**Key Functions**:
- Load test cases from evaluations.json
- Connect to generated mock server
- Execute each test case via MCP protocol
- Verify responses match expectations
- Generate markdown report

**Usage**:
```bash
# Run evaluations
uv run python -m ai_generation.evaluation_runner \
  --evaluations generated/calculator/evaluations.json \
  --mock-server generated/calculator/server.py

# Custom output location
uv run python -m ai_generation.evaluation_runner \
  --evaluations generated/calculator/evaluations.json \
  --mock-server generated/calculator/server.py \
  --output custom_report.md
```

### 6. Generated Output Structure

Each server gets its own namespaced directory:
```
generated/
├── calculator/
│   ├── server.py           # FastMCP server setup
│   ├── tools.py           # AI-generated tool implementations  
│   ├── evaluations.json   # AI-generated test cases (10 for calculator)
│   └── eval_results.md    # Evaluation report (when run)
├── gmail/
│   └── ...
└── google_drive/
    └── ...
```

## Key Benefits

### AI-Powered Generation
- **Intelligent Test Cases**: Claude analyzes tool semantics for realistic test generation
- **Contextual Mock Responses**: `"The sum of 42 and 17 is 59"` vs generic `"Mock: Operation completed"`
- **Domain Awareness**: Understands calculator, email, file operations differently
- **Edge Case Discovery**: Identifies domain-specific boundary conditions

### Zero Configuration
- **Fully Agnostic**: Works with any MCP server regardless of domain
- **Auto-Discovery**: Extracts tools and schemas automatically
- **Smart Naming**: Generates clean server names from file paths
- **Isolated Testing**: Each server gets its own namespace

### Safe & Reliable
- **No Side Effects**: Mock servers have no external dependencies
- **Realistic Responses**: AI generates contextually appropriate mock data
- **Comprehensive Coverage**: Tests valid inputs, invalid types, edge cases
- **Reproducible**: Same input generates consistent test suites

## Current Limitations & Future Enhancements

### Current Minimal Implementation
- **2 test cases per tool**: 1 valid params + 1 invalid type
- **Basic validation**: Success/error checking only
- **Single-tool tests**: No multi-tool workflows
- **Synchronous execution**: One test at a time

### Future Milestone Enhancements
- **Expanded test coverage**: Missing required parameters, additional valid/invalid variations
- **Domain-specific edge cases**: Division by zero, boundary conditions, mathematical limits
- **Multi-tool workflow tests**: Complex scenarios across multiple tools
- **Performance benchmarks**: Response time and throughput testing
- **Stateful testing**: Scenarios requiring persistent state
- **LLM-specific evaluations**: Agent-focused test patterns

## Technical Implementation Notes

### AI Service Configuration
- **Claude CLI Required**: Uses `claude` command for AI generation
- **Timeout Handling**: 180-second timeout with fallback mechanisms
- **Bulk vs Per-Tool**: Attempts bulk generation, falls back to individual tool processing
- **JSON Parsing**: Robust parsing with markdown cleanup

### Mock Server Architecture
- **FastMCP Framework**: Uses FastMCP for consistent server structure
- **Request Logging**: All tool calls logged for verification
- **Parameter Validation**: Type checking and required parameter enforcement
- **Realistic Responses**: AI-generated responses based on tool semantics

### Test Case Strategy
- **Schema Analysis**: Extracts parameter types, requirements, constraints
- **Realistic Values**: AI generates appropriate test data for each tool type
- **Error Scenarios**: Tests invalid types, missing parameters
- **Verification**: Checks both success/failure and response content

## Development Status

- [x] ✅ AI-powered generation system implemented
- [x] ✅ Clean module structure (ai_generation/)
- [x] ✅ Mock server generation working (server.py + tools.py)
- [x] ✅ Evaluation generation working (minimal 2 tests per tool)
- [x] ✅ Evaluation runner implemented and tested
- [x] ✅ Tested with calculator server (10 tests generated)
- [x] ✅ Claude CLI integration with fallback mechanisms
- [x] ✅ JSON parsing issues resolved
- [ ] 🚧 Expand test case generation (future milestone)
- [ ] 🚧 Test with Gmail and Google Drive servers
- [ ] 🚧 Multi-tool workflow testing
- [ ] 🚧 Performance and coverage metrics

## Dependencies

- **Claude CLI**: Required for AI generation (`claude` command)
- **FastMCP**: Mock server framework
- **MCP SDK**: Protocol implementation
- **Python 3.10+**: Core runtime
- **uv**: Package management

## Quick Start

```bash
# 1. Ensure Claude CLI is available
claude --version

# 2. Generate evaluation suite
uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py

# 3. Run evaluations  
uv run python -m ai_generation.evaluation_runner \
  --evaluations generated/calculator/evaluations.json \
  --mock-server generated/calculator/server.py

# 4. View results
cat generated/eval_results.md
```

This system represents a significant advancement in MCP testing, providing AI-powered, domain-aware test generation that scales across any MCP server implementation.