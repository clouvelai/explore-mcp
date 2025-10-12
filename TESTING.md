# MCP Project Testing Guide

This document describes the comprehensive testing setup for the MCP calculator project, with clear separation between server, client, and integration testing.

## Testing Architecture Overview

The testing framework is organized by component responsibility:

```
tests/
├── server/                     # MCP Server Tests (FastMCP)
│   ├── unit/                   # Individual tool logic tests
│   │   └── test_mcp_tools.py   # Tool function testing via MCP
│   ├── integration/            # MCP protocol & workflow tests
│   │   ├── test_mcp_server.py  # Protocol compliance & tool registration
│   │   └── test_mcp_workflows.py # Multi-step calculation workflows
│   └── conftest.py            # Server-specific fixtures
│
├── client/                     # MCP Client Tests (future)
│   ├── unit/                   # Client connection & parsing logic
│   ├── integration/            # Client-server integration  
│   └── conftest.py            # Client-specific fixtures
│
├── backend/                    # Chat Backend Tests (future)
│   ├── unit/                   # Flask app functions
│   ├── integration/            # Backend-MCP integration
│   └── conftest.py            # Backend-specific fixtures
│
├── e2e/                        # True End-to-End Tests (future)
│   └── test_full_workflows.py # Complete user journeys
│
├── fixtures/                   # Shared test data
├── conftest.py                # Global fixtures and configuration
└── pytest.ini                # Pytest settings
```

## Current Implementation: MCP Server Tests

The current testing implementation focuses on the **MCP Server** component using FastMCP best practices.

### Server Test Structure

#### **Unit Tests** (`tests/server/unit/`)
- **Purpose**: Test individual MCP tool functions
- **Approach**: Direct tool calls via in-memory MCP client
- **File**: `test_mcp_tools.py`

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_sum_positive_numbers(self, mcp_client):
    """Test addition of two positive numbers."""
    result = await mcp_client.call_tool('sum', {'a': 5.0, 'b': 3.0})
    content_text = result.content[0].text if result.content else ""
    assert "The sum of 5.0 and 3.0 is 8.0" in content_text
```

#### **Integration Tests** (`tests/server/integration/`)
- **Purpose**: Test MCP protocol compliance and multi-step workflows
- **Files**: 
  - `test_mcp_server.py` - Protocol compliance, tool registration, error handling
  - `test_mcp_workflows.py` - Complex calculation scenarios, realistic use cases

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tools(self, mcp_client):
    """Test that all tools are properly registered."""
    tools = await mcp_client.list_tools()
    assert len(tools) == 5  # add, sum, sum_many, multiply, divide
```

### Key Testing Patterns

#### **1. FastMCP In-Memory Testing**
All server tests use FastMCP's in-memory transport for optimal performance:

```python
@pytest.fixture
async def mcp_client(mcp_server) -> AsyncGenerator[Client, None]:
    """Create an MCP client connected to the test server via in-memory transport."""
    async with Client(mcp_server) as client:
        yield client
```

Benefits:
- Sub-second test execution
- No network or process management overhead
- Perfect test isolation

#### **2. Proper Content Access**
Tests correctly extract content from MCP responses:

```python
content_text = result.content[0].text if result.content else ""
assert "expected text" in content_text
```

## Test Dependencies

```toml
[tool.uv.dependency-groups]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0", 
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0"
]
```

## Running Tests

### Current Server Tests

```bash
# Run all server tests
./run_tests.sh

# Run specific server test categories  
./run_tests.sh -u           # Unit tests only
./run_tests.sh -i           # Integration tests only

# Run with coverage
./run_tests.sh -c

# Generate HTML coverage report
./run_tests.sh --html-coverage

# Watch mode for TDD
./run_tests.sh -w
```

### Direct pytest Commands

```bash
# Run all server tests
uv run pytest tests/server/ -v

# Run specific test files
uv run pytest tests/server/unit/test_mcp_tools.py
uv run pytest tests/server/integration/test_mcp_server.py

# With coverage
uv run pytest tests/server/ --cov=. --cov-report=html
```

## Future Component Testing Plans

### Client Tests (`tests/client/` - Not Yet Implemented)

When implementing MCP client tests (for `client.py`):

#### **Unit Tests** (`tests/client/unit/`)
- Connection logic testing
- Response parsing validation  
- Error handling scenarios

```python
# Example structure for future client tests
def test_parse_tool_result():
    """Test client's ability to parse MCP responses."""
    mock_result = create_mock_tool_result()
    parsed = parse_tool_result(mock_result)
    assert parsed.success is True

async def test_connection_retry_logic():
    """Test client reconnection handling."""
    # Test connection failure scenarios
```

#### **Integration Tests** (`tests/client/integration/`)
- Real client-server communication
- Subprocess-based server testing
- stdio protocol validation

```python
# Example structure for future client integration tests  
async def test_client_server_stdio_connection():
    """Test client.py connecting to actual server via stdio."""
    # Start server subprocess, test real stdio connection
    server_process = await start_server_subprocess()
    client_output = await run_client_against_server()
    assert "Connected to server" in client_output
```

### Backend Tests (`tests/backend/` - Not Yet Implemented)

When implementing Flask backend tests (for `chat_backend.py`):

#### **Unit Tests** (`tests/backend/unit/`)
- Tool format conversion (MCP ↔ OpenAI)
- Message handling logic
- API endpoint validation

```python
# Example structure for future backend tests
def test_mcp_to_openai_tool_conversion():
    """Test converting MCP tools to OpenAI format."""
    mcp_tool = create_mock_mcp_tool()
    openai_tool = convert_to_openai_format(mcp_tool)
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == mcp_tool.name

def test_chat_endpoint_validation():
    """Test Flask chat endpoint input validation."""
    with app.test_client() as client:
        response = client.post('/api/chat', json={})
        assert response.status_code == 400
```

#### **Integration Tests** (`tests/backend/integration/`)
- Backend ↔ MCP server communication
- OpenAI API integration (with mocking)
- Full request/response cycles

```python
# Example structure for future backend integration tests
async def test_backend_calls_mcp_tools():
    """Test Flask backend successfully calls MCP server."""
    with app.test_client() as client:
        response = client.post('/api/chat', json={'message': 'Add 5 + 3'})
        data = response.get_json()
        assert "tool_calls" in data
        assert any(tc["name"] == "sum" for tc in data["tool_calls"])
```

### True End-to-End Tests (`tests/e2e/` - Not Yet Implemented)

For complete user journey testing:

```python
# Example structure for future E2E tests
async def test_complete_chat_calculation_workflow():
    """Test: User message → Flask → OpenAI → MCP → Response."""
    # Start all services (Flask backend, MCP server)
    # Mock OpenAI API calls
    # Send real HTTP request to backend
    # Verify complete flow works
    
async def test_error_recovery_across_components():
    """Test error handling across all components."""
    # Test scenarios where MCP server fails
    # Verify backend gracefully handles failures
    # Test client recovery mechanisms
```

## Test Markers and Organization

```python
# Current markers for server tests
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # MCP protocol tests  
@pytest.mark.slow          # Performance/stress tests

# Future markers for expanded testing
@pytest.mark.server        # MCP server tests
@pytest.mark.client        # MCP client tests  
@pytest.mark.backend       # Flask backend tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.requires_openai # Tests needing OpenAI API
```

## Coverage Goals

- **Server Tests**: >80% coverage (currently achieved)
- **Client Tests**: >70% coverage (when implemented)
- **Backend Tests**: >75% coverage (when implemented)  
- **E2E Tests**: Critical user paths covered (when implemented)

## Adding New Components

When adding new test components:

1. **Create component directory**: `tests/{component}/`
2. **Add component conftest**: Component-specific fixtures
3. **Update run_tests.sh**: Add component-specific options
4. **Update this documentation**: Add component-specific guidance
5. **Create example tests**: Establish patterns for the team

## Best Practices

### Server Testing (Current)
1. ✅ Use FastMCP in-memory transport
2. ✅ Test via MCP protocol, not direct function calls
3. ✅ Verify both success and error scenarios
4. ✅ Test realistic multi-step workflows
5. ✅ Maintain fast test execution (<1s total)

### Future Component Testing
1. **Client Testing**: Use subprocess for real server interaction
2. **Backend Testing**: Mock external APIs, test real MCP integration
3. **E2E Testing**: Start all services, test complete user journeys
4. **Performance Testing**: Monitor memory usage and response times

## Continuous Integration

```yaml
# Example CI configuration for complete test suite
- name: Run Server Tests
  run: uv run pytest tests/server/ --cov=. --cov-report=xml
  
- name: Run Client Tests  
  run: uv run pytest tests/client/ --cov=. --cov-append
  
- name: Run Backend Tests
  run: uv run pytest tests/backend/ --cov=. --cov-append
  
- name: Run E2E Tests
  run: uv run pytest tests/e2e/ --cov=. --cov-append
  
- name: Upload Coverage
  uses: codecov/codecov-action@v2
```

This structured approach ensures each component is thoroughly tested while maintaining clear separation of concerns and fast feedback loops during development.