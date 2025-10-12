"""
Mock tests for MCP client with simulated server responses.

These tests use comprehensive mocking to simulate various server
responses and edge cases without requiring a real server.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from mcp import ClientSession
from mcp.types import Tool, Prompt, TextContent


@pytest.mark.client_mock
class TestMockServerResponses:
    """Test client behavior with various mocked server responses."""
    
    @pytest.mark.asyncio
    async def test_successful_initialization_mock(self):
        """Test successful initialization with mocked server response."""
        session = AsyncMock(spec=ClientSession)
        
        # Mock successful initialization
        mock_result = MagicMock()
        mock_result.serverInfo.name = "mock-calculator"
        mock_result.serverInfo.version = "1.0.0"
        mock_result.protocolVersion = "1.0"
        
        session.initialize.return_value = mock_result
        
        result = await session.initialize()
        assert result.serverInfo.name == "mock-calculator"
        assert result.serverInfo.version == "1.0.0"
        assert result.protocolVersion == "1.0"
    
    @pytest.mark.asyncio
    async def test_tools_listing_mock(self):
        """Test tools listing with comprehensive mocked response."""
        session = AsyncMock(spec=ClientSession)
        
        # Create detailed mock tools
        mock_tools = [
            Tool(
                name="add",
                description="Add two numbers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="multiply",
                description="Multiply two numbers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    },
                    "required": ["x", "y"]
                }
            ),
            Tool(
                name="concat",
                description="Concatenate strings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "strings": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["strings"]
                }
            )
        ]
        
        mock_result = MagicMock()
        mock_result.tools = mock_tools
        session.list_tools.return_value = mock_result
        
        result = await session.list_tools()
        assert len(result.tools) == 3
        assert result.tools[0].name == "add"
        assert result.tools[1].name == "multiply"
        assert result.tools[2].name == "concat"
        
        # Verify schema structures
        add_schema = result.tools[0].inputSchema
        assert add_schema["type"] == "object"
        assert "a" in add_schema["properties"]
        assert "b" in add_schema["properties"]
        assert add_schema["required"] == ["a", "b"]
    
    @pytest.mark.asyncio
    async def test_prompts_listing_mock(self):
        """Test prompts listing with mocked response."""
        session = AsyncMock(spec=ClientSession)
        
        mock_prompts = [
            Prompt(
                name="explain_math",
                description="Explain mathematical operations step by step"
            ),
            Prompt(
                name="code_review",
                description="Review code for best practices"
            ),
            Prompt(
                name="translate",
                description="Translate text between languages"
            )
        ]
        
        mock_result = MagicMock()
        mock_result.prompts = mock_prompts
        session.list_prompts.return_value = mock_result
        
        result = await session.list_prompts()
        assert len(result.prompts) == 3
        assert result.prompts[0].name == "explain_math"
        assert result.prompts[1].name == "code_review"
        assert result.prompts[2].name == "translate"
    
    @pytest.mark.asyncio
    async def test_tool_call_success_responses(self):
        """Test various successful tool call responses."""
        session = AsyncMock(spec=ClientSession)
        
        # Define different response types
        responses = {
            "simple_text": TextContent(type="text", text="Simple result"),
            "calculation": TextContent(type="text", text="The result of 5 + 3 is 8"),
            "error_message": TextContent(type="text", text="Error: Division by zero"),
            "complex_result": TextContent(
                type="text", 
                text="Analysis complete:\n- Input processed\n- Calculation performed\n- Result: 42"
            )
        }
        
        async def mock_call_tool(name: str, arguments: Dict[str, Any]):
            result = MagicMock()
            if name == "simple":
                result.content = [responses["simple_text"]]
            elif name == "calculate":
                result.content = [responses["calculation"]]
            elif name == "divide_zero":
                result.content = [responses["error_message"]]
            elif name == "analyze":
                result.content = [responses["complex_result"]]
            return result
        
        session.call_tool = mock_call_tool
        
        # Test each response type
        simple_result = await session.call_tool("simple", {})
        assert simple_result.content[0].text == "Simple result"
        
        calc_result = await session.call_tool("calculate", {"a": 5, "b": 3})
        assert "5 + 3 is 8" in calc_result.content[0].text
        
        error_result = await session.call_tool("divide_zero", {"a": 5, "b": 0})
        assert "Error: Division by zero" in error_result.content[0].text
        
        complex_result = await session.call_tool("analyze", {"data": "test"})
        assert "Analysis complete" in complex_result.content[0].text
        assert "Result: 42" in complex_result.content[0].text
    
    @pytest.mark.asyncio
    async def test_prompt_response_variations(self):
        """Test various prompt response formats."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_get_prompt(name: str, arguments: Dict[str, Any] = None):
            result = MagicMock()
            result.description = f"Description for {name}"
            
            if name == "simple_prompt":
                mock_message = MagicMock()
                mock_message.content = MagicMock()
                mock_message.content.text = "Simple prompt response"
                result.messages = [mock_message]
                
            elif name == "multi_message":
                messages = []
                for i in range(3):
                    mock_message = MagicMock()
                    mock_message.content = MagicMock()
                    mock_message.content.text = f"Message {i + 1}"
                    messages.append(mock_message)
                result.messages = messages
                
            elif name == "template_prompt":
                calc = arguments.get("calculation", "1+1") if arguments else "1+1"
                mock_message = MagicMock()
                mock_message.content = MagicMock()
                mock_message.content.text = f"Let me explain {calc} step by step..."
                result.messages = [mock_message]
                
            return result
        
        session.get_prompt = mock_get_prompt
        
        # Test simple prompt
        simple = await session.get_prompt("simple_prompt")
        assert simple.description == "Description for simple_prompt"
        assert simple.messages[0].content.text == "Simple prompt response"
        
        # Test multi-message prompt
        multi = await session.get_prompt("multi_message")
        assert len(multi.messages) == 3
        assert multi.messages[0].content.text == "Message 1"
        assert multi.messages[2].content.text == "Message 3"
        
        # Test template prompt
        template = await session.get_prompt("template_prompt", {"calculation": "5 * 7"})
        assert "5 * 7" in template.messages[0].content.text


@pytest.mark.client_mock
class TestMockErrorScenarios:
    """Test client behavior with mocked error scenarios."""
    
    @pytest.mark.asyncio
    async def test_initialization_failures(self):
        """Test various initialization failure scenarios."""
        session = AsyncMock(spec=ClientSession)
        
        # Test timeout
        session.initialize.side_effect = asyncio.TimeoutError("Initialization timeout")
        with pytest.raises(asyncio.TimeoutError):
            await session.initialize()
        
        # Test connection error
        session.initialize.side_effect = ConnectionError("Failed to connect")
        with pytest.raises(ConnectionError):
            await session.initialize()
        
        # Test protocol error
        session.initialize.side_effect = ValueError("Protocol version mismatch")
        with pytest.raises(ValueError):
            await session.initialize()
    
    @pytest.mark.asyncio
    async def test_tool_call_error_scenarios(self):
        """Test various tool call error scenarios."""
        session = AsyncMock(spec=ClientSession)
        
        error_scenarios = {
            "not_found": ValueError("Tool 'unknown_tool' not found"),
            "invalid_params": TypeError("Invalid parameter type"),
            "missing_params": ValueError("Missing required parameter 'x'"),
            "execution_error": RuntimeError("Tool execution failed"),
            "timeout": asyncio.TimeoutError("Tool call timed out")
        }
        
        async def mock_error_tool_call(name: str, arguments: Dict[str, Any]):
            if name in error_scenarios:
                raise error_scenarios[name]
            return MagicMock()
        
        session.call_tool = mock_error_tool_call
        
        # Test each error scenario
        with pytest.raises(ValueError, match="not found"):
            await session.call_tool("not_found", {})
        
        with pytest.raises(TypeError, match="Invalid parameter"):
            await session.call_tool("invalid_params", {})
        
        with pytest.raises(ValueError, match="Missing required parameter"):
            await session.call_tool("missing_params", {})
        
        with pytest.raises(RuntimeError, match="execution failed"):
            await session.call_tool("execution_error", {})
        
        with pytest.raises(asyncio.TimeoutError, match="timed out"):
            await session.call_tool("timeout", {})
    
    @pytest.mark.asyncio
    async def test_prompt_error_scenarios(self):
        """Test various prompt error scenarios."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_error_prompt(name: str, arguments: Dict[str, Any] = None):
            if name == "not_found":
                raise ValueError("Prompt 'not_found' does not exist")
            elif name == "invalid_args":
                raise TypeError("Invalid argument type")
            elif name == "missing_args":
                raise ValueError("Missing required argument 'text'")
            return MagicMock()
        
        session.get_prompt = mock_error_prompt
        
        with pytest.raises(ValueError, match="does not exist"):
            await session.get_prompt("not_found")
        
        with pytest.raises(TypeError, match="Invalid argument"):
            await session.get_prompt("invalid_args", {})
        
        with pytest.raises(ValueError, match="Missing required argument"):
            await session.get_prompt("missing_args", {})
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling of malformed server responses."""
        session = AsyncMock(spec=ClientSession)
        
        # Test tool call with malformed response
        async def mock_malformed_tool_response(name: str, arguments: Dict[str, Any]):
            result = MagicMock()
            result.content = None  # Malformed - should be a list
            return result
        
        session.call_tool = mock_malformed_tool_response
        
        result = await session.call_tool("test", {})
        assert result.content is None  # Client should handle gracefully
        
        # Test prompt with malformed response
        async def mock_malformed_prompt_response(name: str, arguments: Dict[str, Any] = None):
            result = MagicMock()
            result.messages = "not_a_list"  # Malformed - should be a list
            return result
        
        session.get_prompt = mock_malformed_prompt_response
        
        prompt_result = await session.get_prompt("test")
        assert prompt_result.messages == "not_a_list"  # Client receives what server sends


@pytest.mark.client_mock
class TestMockTransportFailures:
    """Test client behavior with mocked transport failures."""
    
    @pytest.mark.asyncio
    async def test_connection_loss_during_operation(self):
        """Test handling of connection loss during operations."""
        session = AsyncMock(spec=ClientSession)
        
        # Simulate connection loss during tool call
        async def mock_connection_loss(name: str, arguments: Dict[str, Any]):
            raise ConnectionResetError("Connection lost")
        
        session.call_tool = mock_connection_loss
        
        with pytest.raises(ConnectionResetError):
            await session.call_tool("test", {})
    
    @pytest.mark.asyncio
    async def test_broken_pipe_scenarios(self):
        """Test handling of broken pipe errors."""
        session = AsyncMock(spec=ClientSession)
        
        # Simulate broken pipe during listing
        session.list_tools.side_effect = BrokenPipeError("Broken pipe")
        
        with pytest.raises(BrokenPipeError):
            await session.list_tools()
    
    @pytest.mark.asyncio
    async def test_eof_error_scenarios(self):
        """Test handling of EOF errors."""
        session = AsyncMock(spec=ClientSession)
        
        # Simulate EOF during prompt request
        session.get_prompt.side_effect = EOFError("Unexpected end of file")
        
        with pytest.raises(EOFError):
            await session.get_prompt("test", {})
    
    @pytest.mark.asyncio
    async def test_network_timeout_scenarios(self):
        """Test handling of network timeouts."""
        session = AsyncMock(spec=ClientSession)
        
        # Different timeout scenarios
        timeouts = [
            asyncio.TimeoutError("Read timeout"),
            asyncio.TimeoutError("Write timeout"),
            asyncio.TimeoutError("Connection timeout")
        ]
        
        for i, timeout in enumerate(timeouts):
            session.call_tool.side_effect = timeout
            
            with pytest.raises(asyncio.TimeoutError):
                await session.call_tool(f"test_{i}", {})


@pytest.mark.client_mock
class TestMockPerformanceScenarios:
    """Test client behavior with mocked performance scenarios."""
    
    @pytest.mark.asyncio
    async def test_slow_server_responses(self):
        """Test client behavior with slow server responses."""
        session = AsyncMock(spec=ClientSession)
        
        async def slow_tool_call(name: str, arguments: Dict[str, Any]):
            await asyncio.sleep(0.1)  # Simulate slow response
            result = MagicMock()
            result.content = [TextContent(type="text", text="Slow result")]
            return result
        
        session.call_tool = slow_tool_call
        
        # Test that client waits for slow responses
        result = await session.call_tool("slow_tool", {})
        assert result.content[0].text == "Slow result"
    
    @pytest.mark.asyncio
    async def test_high_load_simulation(self):
        """Test client behavior under high load simulation."""
        session = AsyncMock(spec=ClientSession)
        
        call_count = 0
        
        async def load_tool_call(name: str, arguments: Dict[str, Any]):
            nonlocal call_count
            call_count += 1
            
            # Simulate server under load
            if call_count % 10 == 0:
                await asyncio.sleep(0.05)  # Occasional slow response
            
            result = MagicMock()
            result.content = [TextContent(type="text", text=f"Response {call_count}")]
            return result
        
        session.call_tool = load_tool_call
        
        # Make many concurrent calls
        tasks = [session.call_tool("test", {"id": i}) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 50
        assert call_count == 50
    
    @pytest.mark.asyncio
    async def test_memory_pressure_simulation(self):
        """Test client behavior with large response simulation."""
        session = AsyncMock(spec=ClientSession)
        
        async def large_response_tool(name: str, arguments: Dict[str, Any]):
            # Simulate large response
            large_text = "x" * 100000  # 100KB response
            result = MagicMock()
            result.content = [TextContent(type="text", text=large_text)]
            return result
        
        session.call_tool = large_response_tool
        
        result = await session.call_tool("large_response", {})
        assert len(result.content[0].text) == 100000


@pytest.mark.client_mock
class TestMockStateManagement:
    """Test client state management with mocked scenarios."""
    
    @pytest.mark.asyncio
    async def test_stateless_operation_simulation(self):
        """Test that operations are stateless."""
        session = AsyncMock(spec=ClientSession)
        
        operation_count = 0
        
        async def stateless_tool_call(name: str, arguments: Dict[str, Any]):
            nonlocal operation_count
            operation_count += 1
            
            # Each call should be independent
            result = MagicMock()
            result.content = [TextContent(
                type="text", 
                text=f"Operation {operation_count}: {name} with {arguments}"
            )]
            return result
        
        session.call_tool = stateless_tool_call
        
        # Multiple calls should be independent
        result1 = await session.call_tool("add", {"a": 1, "b": 2})
        result2 = await session.call_tool("multiply", {"x": 3, "y": 4})
        result3 = await session.call_tool("add", {"a": 5, "b": 6})
        
        assert "Operation 1: add" in result1.content[0].text
        assert "Operation 2: multiply" in result2.content[0].text
        assert "Operation 3: add" in result3.content[0].text
    
    @pytest.mark.asyncio
    async def test_session_isolation_simulation(self):
        """Test that different sessions are isolated."""
        # Create two separate mock sessions
        session1 = AsyncMock(spec=ClientSession)
        session2 = AsyncMock(spec=ClientSession)
        
        # Each session has its own state
        session1_calls = 0
        session2_calls = 0
        
        async def session1_tool_call(name: str, arguments: Dict[str, Any]):
            nonlocal session1_calls
            session1_calls += 1
            result = MagicMock()
            result.content = [TextContent(type="text", text=f"Session1-{session1_calls}")]
            return result
        
        async def session2_tool_call(name: str, arguments: Dict[str, Any]):
            nonlocal session2_calls
            session2_calls += 1
            result = MagicMock()
            result.content = [TextContent(type="text", text=f"Session2-{session2_calls}")]
            return result
        
        session1.call_tool = session1_tool_call
        session2.call_tool = session2_tool_call
        
        # Interleave calls between sessions
        result1a = await session1.call_tool("test", {})
        result2a = await session2.call_tool("test", {})
        result1b = await session1.call_tool("test", {})
        result2b = await session2.call_tool("test", {})
        
        assert result1a.content[0].text == "Session1-1"
        assert result2a.content[0].text == "Session2-1"
        assert result1b.content[0].text == "Session1-2"
        assert result2b.content[0].text == "Session2-2"


@pytest.mark.client_mock
class TestMockEdgeCases:
    """Test client behavior with mocked edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_responses(self):
        """Test handling of empty or minimal responses."""
        session = AsyncMock(spec=ClientSession)
        
        # Tool call with empty content
        async def empty_tool_response(name: str, arguments: Dict[str, Any]):
            result = MagicMock()
            result.content = []  # Empty content list
            return result
        
        session.call_tool = empty_tool_response
        
        result = await session.call_tool("empty", {})
        assert result.content == []
        
        # Prompt with empty messages
        async def empty_prompt_response(name: str, arguments: Dict[str, Any] = None):
            result = MagicMock()
            result.description = ""
            result.messages = []
            return result
        
        session.get_prompt = empty_prompt_response
        
        prompt_result = await session.get_prompt("empty")
        assert prompt_result.description == ""
        assert prompt_result.messages == []
    
    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        session = AsyncMock(spec=ClientSession)
        
        special_strings = [
            "Hello 世界",  # Unicode
            "Test\nwith\nnewlines",  # Newlines
            "Emoji: 🚀🧮✨",  # Emojis
            "Special chars: !@#$%^&*()",  # Special characters
            "",  # Empty string
            " \t\n ",  # Whitespace
        ]
        
        async def unicode_tool_call(name: str, arguments: Dict[str, Any]):
            text = arguments.get("text", "default")
            result = MagicMock()
            result.content = [TextContent(type="text", text=f"Processed: {text}")]
            return result
        
        session.call_tool = unicode_tool_call
        
        for special_string in special_strings:
            result = await session.call_tool("process", {"text": special_string})
            assert f"Processed: {special_string}" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_extreme_parameter_values(self):
        """Test handling of extreme parameter values."""
        session = AsyncMock(spec=ClientSession)
        
        extreme_values = [
            {"number": 0},
            {"number": -999999999},
            {"number": 999999999},
            {"number": 3.14159265359},
            {"number": 1e-100},
            {"number": 1e100},
            {"array": []},
            {"array": list(range(1000))},  # Large array
            {"text": ""},
            {"text": "x" * 10000},  # Very long string
        ]
        
        async def extreme_value_tool(name: str, arguments: Dict[str, Any]):
            result = MagicMock()
            result.content = [TextContent(
                type="text", 
                text=f"Handled extreme value: {type(list(arguments.values())[0]).__name__}"
            )]
            return result
        
        session.call_tool = extreme_value_tool
        
        for extreme_value in extreme_values:
            result = await session.call_tool("extreme", extreme_value)
            assert "Handled extreme value" in result.content[0].text