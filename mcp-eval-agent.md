# MCP Evaluation Agent

## Overview

This system automatically generates evaluation suites and mock MCP servers from real MCP server implementations. It enables automated testing of LLM agents against standardized MCP tool interfaces without side effects.

## Architecture

### Workflow

```
1. Discovery Phase:
   Real MCP Server (e.g., Gmail) 
        ↓
   mcp_eval_generator.py connects
        ↓
   Retrieves tools via initialize() + list_tools()
        ↓

2. Generation Phase:
   Tool Schemas analyzed
        ↓
   Generates two outputs:
   ├── generated/mock_server.py (Mock MCP with same signatures)
   └── generated/evaluations.json (Test cases from schemas)

3. Evaluation Phase:
   Any LLM/Agent 
        ↓
   run_evaluations.py orchestrates
        ↓
   Agent connects to mock_server.py
        ↓
   Executes test cases from evaluations.json
        ↓
   Generates eval_results.md report
```

## Components

### 1. mcp_eval_generator.py
**Purpose**: Discovers MCP tools and generates mock server + evaluations

**Key Functions**:
- `discover_mcp_server(server_path)`: Connect to MCP server and retrieve tools
- `generate_mock_server(tools, output_path)`: Create mock with identical signatures
- `generate_evaluations(tools, output_path)`: Create test cases from schemas
- `parse_tool_schema(tool)`: Extract parameter types and constraints

**Supported Types**:
- Primitives: string, number, boolean, float, int
- Complex: array, object
- Optional parameters
- Default values

### 2. generated/mock_server.py (Auto-Generated)
**Purpose**: FastMCP server mimicking discovered tools

**Features**:
- Identical tool signatures to source
- Predictable mock responses
- Request logging for verification
- Parameter validation
- No side effects

**Example Generated Tool**:
```python
@mcp.tool()
def list_messages(max_results: Optional[int] = None, query: Optional[str] = None) -> str:
    """List messages in Gmail inbox."""
    log_request("list_messages", locals())
    
    # Return realistic mock response
    return "Mock messages: [ID:msg001] Subject: Meeting Tomorrow, [ID:msg002] Subject: Project Update, [ID:msg003] Subject: Weekly Report"

@mcp.tool()
def list_files(max_results: Optional[int] = None) -> str:
    """List files in Google Drive.""" 
    log_request("list_files", locals())
    
    # Return realistic mock response
    return "Mock files: document1.pdf, spreadsheet2.xlsx, presentation3.pptx, image4.jpg, notes5.txt"
```

**Smart Mock Response Generation**:
- **File/folder lists**: Returns comma-separated realistic filenames
- **Message lists**: Returns formatted message previews with IDs
- **Search results**: Returns "Found X items matching query"  
- **Read operations**: Returns formatted content (email body, file content, etc.)
- **Math operations**: Returns calculation results
- **Create/send operations**: Returns success with generated IDs

### 3. generated/evaluations.json (Auto-Generated)
**Purpose**: Test cases derived from tool schemas

**Test Case Types**:
- **valid_params**: All required parameters with valid values
- **missing_required**: Missing required parameters
- **invalid_types**: Wrong parameter types
- **edge_cases**: Empty strings, nulls, boundary values

**Example Structure**:
```json
{
  "server_info": {
    "source": "gmail_mcp_server.py",
    "generated_at": "2024-01-15T10:00:00Z",
    "tools_count": 5
  },
  "evaluations": [
    {
      "tool": "send_email",
      "description": "Send an email",
      "test_cases": [
        {
          "id": "send_email_valid",
          "type": "valid_params",
          "params": {
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test body content"
          },
          "expected_result": "success",
          "expected_contains": ["Successfully", "test@example.com"]
        },
        {
          "id": "send_email_missing_to",
          "type": "missing_required",
          "params": {
            "subject": "Test Subject",
            "body": "Test body"
          },
          "expected_result": "error",
          "expected_contains": ["Error", "Missing", "required"]
        }
      ]
    }
  ]
}
```

### 4. run_evaluations.py
**Purpose**: Execute evaluations against mock server

**Key Functions**:
- `load_evaluations(path)`: Load test cases
- `connect_to_mock_server()`: Establish MCP connection
- `run_test_case(session, test_case)`: Execute single test
- `verify_result(result, expected)`: Check test outcome
- `generate_report(results)`: Create markdown report

**Process**:
1. Start mock MCP server
2. Load evaluations.json
3. Connect test agent/LLM to mock
4. Execute each test case
5. Verify responses match expectations
6. Generate results report

### 5. eval_results.md (Generated Output)
**Purpose**: Human-readable evaluation report

**Contents**:
- Summary statistics (pass/fail rates)
- Per-tool results
- Failed test details
- Recommendations

## Usage

### Generate Mock and Evaluations

```bash
# From calculator server (auto-names as "calculator")
uv run python mcp_eval_generator.py --server server.py --name calculator

# From Gmail server (auto-names as "gmail")
uv run python mcp_eval_generator.py --server gmail_mcp_server.py

# From Google Drive server (auto-names as "google_drive")
uv run python mcp_eval_generator.py --server google_drive_mcp_server.py

# Custom name
uv run python mcp_eval_generator.py --server my_server.py --name my_custom_name
```

### Generated Structure

Each server gets its own namespaced directory:
```
generated/
├── calculator/
│   ├── mock_server.py
│   ├── evaluations.json
│   └── eval_results.md
├── gmail/
│   ├── mock_server.py
│   ├── evaluations.json
│   └── eval_results.md
└── google_drive/
    ├── mock_server.py
    ├── evaluations.json
    └── eval_results.md
```

### Run Evaluations

```bash
# Run evaluations for specific server
uv run python run_evaluations.py --evaluations generated/gmail/evaluations.json --mock-server generated/gmail/mock_server.py

# Output goes to namespaced directory automatically
# Results saved to generated/gmail/eval_results.md
```

## Test Case Generation Strategy

### For Each Tool:
1. **Analyze Input Schema**:
   - Required vs optional parameters
   - Parameter types
   - Constraints (min/max, enums, patterns)

2. **Generate Valid Test**:
   - All required parameters
   - Reasonable default values
   - Type-appropriate data

3. **Generate Invalid Tests**:
   - Missing each required parameter
   - Wrong types for each parameter
   - Boundary conditions

4. **Generate Edge Cases**:
   - Empty strings/arrays
   - Very long strings
   - Special characters
   - Null values (where applicable)

## Example Tool Mappings

### Calculator Server
- `add(a: float, b: float)` → Test numeric operations
- `divide(a: float, b: float)` → Test division by zero handling
- `sum_many(numbers: list[float])` → Test array handling

### Gmail Server  
- `send_email(to, subject, body)` → Test string parameters
- `search_emails(query, max_results)` → Test optional parameters
- `get_email_by_id(email_id)` → Test ID validation

### Google Drive Server
- `list_files(max_results)` → Test pagination
- `create_document(name, content)` → Test content creation
- `search_files(query)` → Test search functionality

## MVP Limitations & Future Enhancements

### Current MVP Scope:
- Basic parameter validation
- Simple success/error checking
- Single-tool tests only
- Synchronous execution

### Future Enhancements:
- Multi-tool workflow tests
- Stateful testing scenarios
- Performance benchmarks
- Complex mock responses
- Async tool testing
- LLM-specific evaluations
- Coverage metrics

## Development Status

- [x] Planning document created
- [ ] mcp_eval_generator.py implemented
- [ ] Mock server generation working
- [ ] Evaluation generation working
- [ ] run_evaluations.py implemented
- [ ] Tested with calculator server
- [ ] Tested with Gmail server
- [ ] Tested with Google Drive server

## Notes

- Mock servers run on stdio by default (same as source servers)
- All generated files go in `generated/` directory
- Logs are written to `generated/logs/` for debugging
- Mock servers are stateless (each request independent)