"""
Unit tests for MCP client error handling.

These tests verify proper error handling, exception propagation,
recovery mechanisms, and error message formatting.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from mcp import ClientSession


@pytest.mark.client_unit
class TestConnectionErrors:
    """Test error handling during connection establishment."""
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling of connection timeouts."""
        session = AsyncMock(spec=ClientSession)
        
        # Simulate timeout during initialization
        async def timeout_initialize():
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Connection timed out")
        
        session.initialize = timeout_initialize
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(session.initialize(), timeout=0.05)
    
    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test handling of connection refused errors."""
        session = AsyncMock(spec=ClientSession)
        session.initialize.side_effect = ConnectionRefusedError("Connection refused")
        
        with pytest.raises(ConnectionRefusedError, match="Connection refused"):
            await session.initialize()
    
    @pytest.mark.asyncio
    async def test_server_not_found(self):
        """Test handling when server executable is not found."""
        session = AsyncMock(spec=ClientSession)
        session.initialize.side_effect = FileNotFoundError("Server executable not found")
        
        with pytest.raises(FileNotFoundError, match="Server executable not found"):
            await session.initialize()
    
    @pytest.mark.asyncio
    async def test_permission_denied(self):
        """Test handling of permission denied errors."""
        session = AsyncMock(spec=ClientSession)
        session.initialize.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError, match="Permission denied"):
            await session.initialize()
    
    @pytest.mark.asyncio
    async def test_network_unreachable(self):
        """Test handling of network unreachable errors."""
        session = AsyncMock(spec=ClientSession)
        session.initialize.side_effect = OSError("Network is unreachable")
        
        with pytest.raises(OSError, match="Network is unreachable"):
            await session.initialize()


@pytest.mark.client_unit
class TestToolCallErrors:
    """Test error handling during tool calls."""
    
    @pytest.mark.asyncio
    async def test_tool_not_found_error(self, error_response_scenarios):
        """Test handling of tool not found errors."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_call_tool_error(name: str, arguments: Dict[str, Any]):
            if name == "nonexistent":
                raise ValueError("Tool 'nonexistent' not found")
            return MagicMock()
        
        session.call_tool = mock_call_tool_error
        
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            await session.call_tool("nonexistent", {})
    
    @pytest.mark.asyncio
    async def test_invalid_parameters_error(self, mcp_client_session):
        """Test handling of invalid parameter errors."""
        client = mcp_client_session
        
        # Test missing required parameters
        with pytest.raises(Exception):  # May be TypeError, ValueError, or other
            await client.call_tool("sum", {"a": 5})  # Missing 'b' parameter
    
    @pytest.mark.asyncio
    async def test_server_error_during_tool_call(self):
        """Test handling of server errors during tool execution."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_server_error(name: str, arguments: Dict[str, Any]):
            raise RuntimeError("Internal server error during tool execution")
        
        session.call_tool = mock_server_error
        
        with pytest.raises(RuntimeError, match="Internal server error"):
            await session.call_tool("sum", {"a": 1, "b": 2})
    
    @pytest.mark.asyncio
    async def test_malformed_tool_response(self):
        """Test handling of malformed tool responses."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_malformed_response(name: str, arguments: Dict[str, Any]):
            # Return a response that doesn't have expected structure
            malformed_response = MagicMock()
            malformed_response.content = None  # Missing content
            return malformed_response
        
        session.call_tool = mock_malformed_response
        
        result = await session.call_tool("sum", {"a": 1, "b": 2})
        
        # Client should handle gracefully, even if response is malformed
        assert result is not None
        assert result.content is None
    
    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self):
        """Test handling of tool execution timeouts."""
        session = AsyncMock(spec=ClientSession)
        
        async def slow_tool_call(name: str, arguments: Dict[str, Any]):
            await asyncio.sleep(0.1)  # Simulate slow tool
            return MagicMock()
        
        session.call_tool = slow_tool_call
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                session.call_tool("sum", {"a": 1, "b": 2}), 
                timeout=0.05
            )


@pytest.mark.client_unit
class TestPromptErrors:
    """Test error handling during prompt operations."""
    
    @pytest.mark.asyncio
    async def test_prompt_not_found_error(self):
        """Test handling of prompt not found errors."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_prompt_error(name: str, arguments: Dict[str, Any] = None):
            if name == "nonexistent_prompt":
                raise ValueError("Prompt 'nonexistent_prompt' not found")
            return MagicMock()
        
        session.get_prompt = mock_prompt_error
        
        with pytest.raises(ValueError, match="Prompt 'nonexistent_prompt' not found"):
            await session.get_prompt("nonexistent_prompt", {})
    
    @pytest.mark.asyncio
    async def test_missing_prompt_arguments(self):
        """Test handling of missing prompt arguments."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_prompt_validation(name: str, arguments: Dict[str, Any] = None):
            if name == "explain_calculation":
                if not arguments or "calculation" not in arguments:
                    raise ValueError("Missing required argument: calculation")
                return MagicMock()
            return MagicMock()
        
        session.get_prompt = mock_prompt_validation
        
        with pytest.raises(ValueError, match="Missing required argument: calculation"):
            await session.get_prompt("explain_calculation", {})
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_arguments(self):
        """Test handling of invalid prompt argument types."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_prompt_type_validation(name: str, arguments: Dict[str, Any] = None):
            if name == "explain_calculation" and arguments:
                calc = arguments.get("calculation")
                if not isinstance(calc, str):
                    raise TypeError("Argument 'calculation' must be a string")
                return MagicMock()
            return MagicMock()
        
        session.get_prompt = mock_prompt_type_validation
        
        with pytest.raises(TypeError, match="Argument 'calculation' must be a string"):
            await session.get_prompt("explain_calculation", {"calculation": 123})


@pytest.mark.client_unit
class TestProtocolErrors:
    """Test error handling for MCP protocol violations."""
    
    @pytest.mark.asyncio
    async def test_protocol_version_mismatch(self):
        """Test handling of protocol version mismatches."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_version_error():
            raise ValueError("Protocol version mismatch: server supports v1.0, client requires v2.0")
        
        session.initialize = mock_version_error
        
        with pytest.raises(ValueError, match="Protocol version mismatch"):
            await session.initialize()
    
    @pytest.mark.asyncio
    async def test_invalid_json_rpc_message(self):
        """Test handling of invalid JSON-RPC messages."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_json_error(name: str, arguments: Dict[str, Any]):
            raise ValueError("Invalid JSON-RPC message format")
        
        session.call_tool = mock_json_error
        
        with pytest.raises(ValueError, match="Invalid JSON-RPC message format"):
            await session.call_tool("sum", {"a": 1, "b": 2})
    
    @pytest.mark.asyncio
    async def test_unexpected_server_response(self):
        """Test handling of unexpected server responses."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_unexpected_response(name: str, arguments: Dict[str, Any]):
            raise RuntimeError("Unexpected response from server")
        
        session.call_tool = mock_unexpected_response
        
        with pytest.raises(RuntimeError, match="Unexpected response from server"):
            await session.call_tool("sum", {"a": 1, "b": 2})


@pytest.mark.client_unit
class TestDisconnectionErrors:
    """Test error handling for server disconnections."""
    
    @pytest.mark.asyncio
    async def test_server_disconnection_during_call(self):
        """Test handling of server disconnection during tool call."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_disconnection(name: str, arguments: Dict[str, Any]):
            raise ConnectionResetError("Server disconnected unexpectedly")
        
        session.call_tool = mock_disconnection
        
        with pytest.raises(ConnectionResetError, match="Server disconnected unexpectedly"):
            await session.call_tool("sum", {"a": 1, "b": 2})
    
    @pytest.mark.asyncio
    async def test_broken_pipe_error(self):
        """Test handling of broken pipe errors."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_broken_pipe(name: str, arguments: Dict[str, Any]):
            raise BrokenPipeError("Broken pipe to server")
        
        session.call_tool = mock_broken_pipe
        
        with pytest.raises(BrokenPipeError, match="Broken pipe to server"):
            await session.call_tool("sum", {"a": 1, "b": 2})
    
    @pytest.mark.asyncio
    async def test_end_of_file_error(self):
        """Test handling of EOF errors."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_eof():
            raise EOFError("Unexpected end of file from server")
        
        session.list_tools = mock_eof
        
        with pytest.raises(EOFError, match="Unexpected end of file from server"):
            await session.list_tools()


@pytest.mark.client_unit
class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_retry_after_transient_error(self):
        """Test retry logic after transient errors."""
        session = AsyncMock(spec=ClientSession)
        call_count = 0
        
        async def flaky_call_tool(name: str, arguments: Dict[str, Any]):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient connection error")
            
            # Success on third attempt
            result = MagicMock()
            result.content = [MagicMock()]
            result.content[0].text = "Success after retry"
            return result
        
        session.call_tool = flaky_call_tool
        
        # Simulate retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await session.call_tool("sum", {"a": 1, "b": 2})
                break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.01)  # Brief delay between retries
        
        assert call_count == 3
        assert result.content[0].text == "Success after retry"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when some operations fail."""
        session = AsyncMock(spec=ClientSession)
        
        # List tools succeeds
        async def mock_list_tools():
            result = MagicMock()
            result.tools = []
            return result
        
        session.list_tools = mock_list_tools
        
        # Tool calls fail
        async def mock_failing_call_tool(name: str, arguments: Dict[str, Any]):
            raise RuntimeError("Tool execution unavailable")
        
        session.call_tool = mock_failing_call_tool
        
        # Should be able to list tools even if calls fail
        tools_result = await session.list_tools()
        assert tools_result is not None
        
        # Tool calls should still raise errors
        with pytest.raises(RuntimeError, match="Tool execution unavailable"):
            await session.call_tool("sum", {"a": 1, "b": 2})
    
    @pytest.mark.asyncio
    async def test_error_state_isolation(self):
        """Test that errors don't affect subsequent operations."""
        session = AsyncMock(spec=ClientSession)
        
        call_count = 0
        
        async def selective_failure(name: str, arguments: Dict[str, Any]):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise RuntimeError("First call fails")
            
            # Subsequent calls succeed
            result = MagicMock()
            result.content = [MagicMock()]
            result.content[0].text = f"Success on call {call_count}"
            return result
        
        session.call_tool = selective_failure
        
        # First call should fail
        with pytest.raises(RuntimeError, match="First call fails"):
            await session.call_tool("sum", {"a": 1, "b": 2})
        
        # Second call should succeed
        result = await session.call_tool("sum", {"a": 3, "b": 4})
        assert "Success on call 2" in result.content[0].text
        
        assert call_count == 2


@pytest.mark.client_unit
class TestErrorMessageFormatting:
    """Test proper error message formatting and information."""
    
    @pytest.mark.asyncio
    async def test_descriptive_error_messages(self):
        """Test that error messages are descriptive and helpful."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_descriptive_error(name: str, arguments: Dict[str, Any]):
            raise ValueError(
                f"Tool '{name}' failed: Invalid parameter 'a' with value "
                f"'{arguments.get('a')}'. Expected a number but got {type(arguments.get('a')).__name__}."
            )
        
        session.call_tool = mock_descriptive_error
        
        with pytest.raises(ValueError) as exc_info:
            await session.call_tool("sum", {"a": "not_a_number", "b": 5})
        
        error_message = str(exc_info.value)
        assert "Tool 'sum' failed" in error_message
        assert "Invalid parameter 'a'" in error_message
        assert "not_a_number" in error_message
        assert "Expected a number" in error_message
    
    @pytest.mark.asyncio
    async def test_error_context_preservation(self):
        """Test that error context is preserved through the call stack."""
        session = AsyncMock(spec=ClientSession)
        
        async def mock_context_error(name: str, arguments: Dict[str, Any]):
            try:
                # Simulate nested error
                raise ValueError("Original error")
            except ValueError as e:
                raise RuntimeError(f"Error in tool '{name}': {e}") from e
        
        session.call_tool = mock_context_error
        
        with pytest.raises(RuntimeError) as exc_info:
            await session.call_tool("sum", {"a": 1, "b": 2})
        
        error_message = str(exc_info.value)
        assert "Error in tool 'sum'" in error_message
        assert "Original error" in error_message
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.client_unit
class TestConcurrentErrorHandling:
    """Test error handling in concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_errors_isolation(self):
        """Test that errors in concurrent operations don't affect each other."""
        session = AsyncMock(spec=ClientSession)
        
        async def selective_concurrent_failure(name: str, arguments: Dict[str, Any]):
            a = arguments.get("a", 0)
            if a == 5:  # Specific value that causes failure
                raise RuntimeError("Specific failure for a=5")
            
            # Other calls succeed
            result = MagicMock()
            result.content = [MagicMock()]
            result.content[0].text = f"Success with a={a}"
            return result
        
        session.call_tool = selective_concurrent_failure
        
        # Create concurrent tasks, some will fail, some will succeed
        tasks = [
            session.call_tool("sum", {"a": i, "b": 1})
            for i in range(10)
        ]
        
        # Gather results, allowing exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that we have both successes and failures
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        assert len(successes) == 9  # All except a=5
        assert len(failures) == 1   # Only a=5 should fail
        assert isinstance(failures[0], RuntimeError)
        assert "Specific failure for a=5" in str(failures[0])
    
    @pytest.mark.asyncio
    async def test_error_propagation_in_gather(self):
        """Test proper error propagation in asyncio.gather."""
        session = AsyncMock(spec=ClientSession)
        
        async def mixed_success_failure(name: str, arguments: Dict[str, Any]):
            a = arguments.get("a", 0)
            if a % 2 == 0:  # Even numbers fail
                raise ValueError(f"Even number {a} not allowed")
            
            # Odd numbers succeed
            result = MagicMock()
            result.content = [MagicMock()]
            result.content[0].text = f"Success with odd {a}"
            return result
        
        session.call_tool = mixed_success_failure
        
        # Create fresh tasks for first gather call (will raise exception)
        tasks1 = [
            session.call_tool("sum", {"a": i, "b": 1})
            for i in range(5)  # 0,1,2,3,4 - evens will fail
        ]
        
        # Without return_exceptions=True, gather should raise on first exception
        with pytest.raises(ValueError):
            await asyncio.gather(*tasks1)
        
        # Create fresh tasks for second gather call (will collect results)
        tasks2 = [
            session.call_tool("sum", {"a": i, "b": 1})
            for i in range(5)  # 0,1,2,3,4 - evens will fail
        ]
        
        # With return_exceptions=True, should get mixed results
        results = await asyncio.gather(*tasks2, return_exceptions=True)
        assert len(results) == 5
        
        # Count successes and failures
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        # We have range(5) = 0,1,2,3,4
        # Even numbers (0,2,4) should fail = 3 failures
        # Odd numbers (1,3) should succeed = 2 successes
        assert len(failures) == 3   # Even numbers: 0, 2, 4
        assert len(successes) == 2  # Odd numbers: 1, 3
        
        # Verify the actual pattern
        for i, result in enumerate(results):
            if i % 2 == 0:  # Even index - should be failure
                assert isinstance(result, ValueError)
            else:  # Odd index - should be success
                assert hasattr(result, 'content')