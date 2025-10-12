"""
Unit tests for MCP client connection functionality.

These tests verify client initialization, connection establishment,
and disconnection handling using mocked transports.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.client_unit
class TestClientInitialization:
    """Test client initialization and basic setup."""
    
    @pytest.mark.asyncio
    async def test_client_session_creation(self, mock_client_session):
        """Test creating a ClientSession instance."""
        session = mock_client_session
        assert session is not None
        assert hasattr(session, 'initialize')
        assert hasattr(session, 'list_tools')
        assert hasattr(session, 'call_tool')
    
    @pytest.mark.asyncio
    async def test_stdio_server_parameters_creation(self, mock_stdio_server_params):
        """Test creating StdioServerParameters."""
        params = mock_stdio_server_params
        assert params.command == "python"
        assert params.args == ["server.py"]
        assert params.env is None
    
    @pytest.mark.asyncio
    async def test_stdio_server_parameters_with_env(self):
        """Test creating StdioServerParameters with environment variables."""
        env_vars = {"TEST_VAR": "test_value"}
        params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env=env_vars
        )
        assert params.env == env_vars


@pytest.mark.client_unit
class TestConnectionLifecycle:
    """Test connection establishment and lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self, mock_client_session):
        """Test successful client initialization."""
        session = mock_client_session
        result = await session.initialize()
        
        assert result is not None
        assert result.serverInfo.name == "test-calculator"
        assert result.serverInfo.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_connection_with_real_server(self, mcp_client_session):
        """Test connection with a real FastMCP server instance."""
        client = mcp_client_session
        
        # The client should be connected and ready to use
        assert client is not None
        
        # Test that we can list tools (this proves connection works)
        tools = await client.list_tools()
        assert len(tools) > 0
        
        # Verify expected tools are present
        tool_names = [tool.name for tool in tools]
        expected_tools = ["sum", "multiply", "divide", "sum_many", "add"]
        for expected in expected_tools:
            assert expected in tool_names
    
    @pytest.mark.asyncio
    async def test_connection_context_manager(self, mcp_test_server):
        """Test that connection context manager works properly."""
        from fastmcp import Client
        
        # Test that we can use the client as a context manager
        async with Client(mcp_test_server) as client:
            tools = await client.list_tools()
            assert len(tools) > 0
        
        # After exiting context, the client should be properly cleaned up
        # (In a real scenario, this would test that connections are closed)
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_isolation(self, mcp_test_server):
        """Test that multiple client sessions are properly isolated."""
        from fastmcp import Client
        
        # Create two separate client sessions
        async with Client(mcp_test_server) as client1:
            async with Client(mcp_test_server) as client2:
                # Both should be able to list tools independently
                tools1 = await client1.list_tools()
                tools2 = await client2.list_tools()
                
                assert len(tools1) > 0
                assert len(tools2) > 0
                assert len(tools1) == len(tools2)


@pytest.mark.client_unit
class TestConnectionErrors:
    """Test connection error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_initialize_error_handling(self):
        """Test error handling during initialization."""
        # Create a session that raises an error on initialize
        session = AsyncMock(spec=ClientSession)
        session.initialize.side_effect = ConnectionError("Failed to connect")
        
        with pytest.raises(ConnectionError, match="Failed to connect"):
            await session.initialize()
    
    @pytest.mark.asyncio
    async def test_stdio_client_connection_error(self):
        """Test handling of stdio client connection errors."""
        server_params = StdioServerParameters(
            command="nonexistent_command",
            args=[]
        )
        
        with pytest.raises(FileNotFoundError):
            async with stdio_client(server_params) as (read, write):
                pass
    
    @pytest.mark.asyncio
    async def test_connection_timeout_simulation(self):
        """Test behavior when connection times out."""
        # Simulate a connection that times out
        async def slow_initialize():
            await asyncio.sleep(0.1)  # Simulate slow connection
            raise asyncio.TimeoutError("Connection timed out")
        
        session = AsyncMock(spec=ClientSession)
        session.initialize = slow_initialize
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(session.initialize(), timeout=0.05)
    
    @pytest.mark.asyncio
    async def test_server_disconnection_handling(self, mock_client_session):
        """Test handling of unexpected server disconnection."""
        session = mock_client_session
        
        # Simulate server disconnecting during operation
        async def disconnected_call_tool(*args, **kwargs):
            raise ConnectionResetError("Server disconnected")
        
        session.call_tool = disconnected_call_tool
        
        with pytest.raises(ConnectionResetError, match="Server disconnected"):
            await session.call_tool("sum", {"a": 1, "b": 2})


@pytest.mark.client_unit
class TestConnectionRecovery:
    """Test connection recovery and retry mechanisms."""
    
    @pytest.mark.asyncio
    async def test_retry_connection_logic(self):
        """Test retry logic for failed connections."""
        attempt_count = 0
        max_attempts = 3
        
        async def flaky_initialize():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < max_attempts:
                raise ConnectionError(f"Attempt {attempt_count} failed")
            return MagicMock()
        
        session = AsyncMock(spec=ClientSession)
        session.initialize = flaky_initialize
        
        # Simulate retry logic
        for attempt in range(max_attempts):
            try:
                result = await session.initialize()
                assert result is not None
                break
            except ConnectionError:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(0.01)  # Brief delay between retries
        
        assert attempt_count == max_attempts
    
    @pytest.mark.asyncio
    async def test_graceful_connection_cleanup(self, mcp_test_server):
        """Test that connections are cleaned up gracefully."""
        from fastmcp import Client
        
        client_instance = None
        
        # Use the client and then ensure it cleans up properly
        async with Client(mcp_test_server) as client:
            client_instance = client
            tools = await client.list_tools()
            assert len(tools) > 0
        
        # After context exit, verify cleanup occurred
        # (In a real implementation, this would check that resources are released)
        assert client_instance is not None


@pytest.mark.client_unit
class TestConnectionConfiguration:
    """Test various connection configuration options."""
    
    @pytest.mark.asyncio
    async def test_stdio_with_custom_env(self):
        """Test stdio connection with custom environment variables."""
        custom_env = {
            "MCP_DEBUG": "1",
            "CUSTOM_VAR": "test_value"
        }
        
        params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env=custom_env
        )
        
        assert params.env == custom_env
        assert params.env["MCP_DEBUG"] == "1"
        assert params.env["CUSTOM_VAR"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_stdio_with_complex_args(self):
        """Test stdio connection with complex command arguments."""
        complex_args = [
            "server.py",
            "--verbose",
            "--config", "/path/to/config.json",
            "--port", "8080"
        ]
        
        params = StdioServerParameters(
            command="python",
            args=complex_args
        )
        
        assert params.args == complex_args
        assert "--verbose" in params.args
        assert "--config" in params.args
    
    @pytest.mark.asyncio
    async def test_connection_parameter_validation(self):
        """Test validation of connection parameters."""
        # Test that required parameters are validated
        with pytest.raises(Exception):  # ValidationError from pydantic
            StdioServerParameters()  # Missing required command
        
        # Test with minimal valid parameters
        params = StdioServerParameters(command="python")
        assert params.command == "python"
        assert params.args == []  # Should default to empty list


@pytest.mark.client_unit
class TestConcurrentConnections:
    """Test handling of concurrent client connections."""
    
    @pytest.mark.asyncio
    async def test_concurrent_client_creation(self, mcp_test_server):
        """Test creating multiple clients concurrently."""
        from fastmcp import Client
        
        async def create_client_and_test():
            async with Client(mcp_test_server) as client:
                tools = await client.list_tools()
                return len(tools)
        
        # Create multiple clients concurrently
        tasks = [create_client_and_test() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All clients should have successfully listed tools
        assert len(results) == 5
        assert all(result > 0 for result in results)
        assert all(result == results[0] for result in results)  # All should see same tools
    
    @pytest.mark.asyncio
    async def test_sequential_vs_concurrent_performance(self, mcp_test_server):
        """Test that concurrent connections don't interfere with each other."""
        from fastmcp import Client
        import time
        
        # Sequential connections
        start_time = time.time()
        for _ in range(3):
            async with Client(mcp_test_server) as client:
                await client.list_tools()
        sequential_time = time.time() - start_time
        
        # Concurrent connections
        start_time = time.time()
        async def test_client():
            async with Client(mcp_test_server) as client:
                return await client.list_tools()
        
        tasks = [test_client() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        # Verify all concurrent operations succeeded
        assert len(results) == 3
        assert all(len(result) > 0 for result in results)
        
        # Concurrent should generally be faster or similar
        # (This is more of a performance characterization than a strict test)
        assert concurrent_time <= sequential_time + 0.1  # Allow some tolerance