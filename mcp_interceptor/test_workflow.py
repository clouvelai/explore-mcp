#!/usr/bin/env python3
"""
Complete Workflow Test

Tests the entire interceptor -> mock generation pipeline:
1. Capture MCP session using interceptor
2. Generate mock server from trace
3. Verify mock server code
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_interceptor.mcp_interceptor import install_interceptor
from mcp_interceptor.mock_generator import MockServerGenerator
from mcp_interceptor.trace_format import TraceReader


def test_trace_format():
    """Test that we can write and read trace format"""
    print("\n" + "="*80)
    print("TEST 1: Trace Format Read/Write")
    print("="*80)

    from mcp_interceptor.trace_format import (
        MCPSession, MCPRequest, MCPResponse, MCPCallPair,
        TraceWriter, TraceReader
    )

    # Create a sample session
    session = MCPSession(
        session_id="test-123",
        server_info={"url": "http://test.com", "name": "test-server"}
    )

    # Add some sample calls
    request = MCPRequest(
        method="list_tools",
        args=[],
        kwargs={}
    )
    response = MCPResponse(
        success=True,
        result={
            "_type": "ListToolsResult",
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        }
    )
    session.calls.append(MCPCallPair(request, response, duration_ms=123.45))

    # Write to file
    test_file = "test_trace.jsonl"
    writer = TraceWriter(test_file)
    writer.write_session(session)
    print(f"✓ Wrote session to {test_file}")

    # Read back
    reader = TraceReader(test_file)
    sessions = reader.read_sessions()
    print(f"✓ Read {len(sessions)} session(s)")

    assert len(sessions) == 1, "Should have 1 session"
    assert sessions[0].session_id == "test-123", "Session ID should match"
    assert len(sessions[0].calls) == 1, "Should have 1 call"
    print(f"✓ Session verified: {sessions[0].session_id}")

    # Cleanup
    Path(test_file).unlink()
    print("✓ Test trace file cleaned up")


def test_mock_generation():
    """Test mock server generation"""
    print("\n" + "="*80)
    print("TEST 2: Mock Server Generation")
    print("="*80)

    from mcp_interceptor.trace_format import (
        MCPSession, MCPRequest, MCPResponse, MCPCallPair, TraceWriter
    )

    # Create a more complete session for testing
    session = MCPSession(
        session_id="mock-test-456",
        server_info={
            "url": "http://example.com/mcp",
            "name": "example-server",
            "description": "Example MCP Server"
        }
    )

    # Add initialize call
    session.calls.append(MCPCallPair(
        request=MCPRequest(method="initialize", args=[], kwargs={}),
        response=MCPResponse(
            success=True,
            result={
                "_type": "InitializeResult",
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "example-server", "version": "1.0.0"}
            }
        ),
        duration_ms=50.0
    ))

    # Add list_tools call
    session.calls.append(MCPCallPair(
        request=MCPRequest(method="list_tools", args=[], kwargs={}),
        response=MCPResponse(
            success=True,
            result={
                "_type": "ListToolsResult",
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echo back the input",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            },
                            "required": ["message"]
                        }
                    }
                ]
            }
        ),
        duration_ms=25.0
    ))

    # Add call_tool call
    session.calls.append(MCPCallPair(
        request=MCPRequest(
            method="call_tool",
            args=["echo"],
            kwargs={"arguments": {"message": "Hello, World!"}}
        ),
        response=MCPResponse(
            success=True,
            result={
                "_type": "CallToolResult",
                "content": [
                    {
                        "type": "text",
                        "text": "Echo: Hello, World!"
                    }
                ],
                "isError": False
            }
        ),
        duration_ms=100.0
    ))

    # Write session to trace file
    trace_file = "test_mock_trace.jsonl"
    writer = TraceWriter(trace_file)
    writer.write_session(session)
    print(f"✓ Created test trace: {trace_file}")

    # Generate mock server
    generator = MockServerGenerator(trace_file)
    analysis = generator.analyze_sessions()

    print(f"✓ Analysis complete:")
    print(f"  - Methods: {', '.join(analysis['methods'])}")
    print(f"  - Total sessions: {analysis['total_sessions']}")

    mock_file = "test_mock_server.py"
    generator.generate_mock_server(mock_file, "TestMockServer")
    print(f"✓ Generated mock server: {mock_file}")

    # Verify the generated file
    assert Path(mock_file).exists(), "Mock server file should exist"
    content = Path(mock_file).read_text()

    # Check for key components
    assert "class TestMockServer" in content, "Should have server class"
    assert "MOCK_RESPONSES" in content, "Should have response data"
    assert "handle_call_tool" in content, "Should have call_tool handler"
    assert "echo" in content, "Should contain our test tool"
    print("✓ Mock server code verified")

    # Cleanup
    Path(trace_file).unlink()
    Path(mock_file).unlink()
    print("✓ Test files cleaned up")


def test_interceptor_integration():
    """Test that interceptor can be installed without errors"""
    print("\n" + "="*80)
    print("TEST 3: Interceptor Installation")
    print("="*80)

    logger = install_interceptor(
        trace_file="test_integration.jsonl",
        verbose=False
    )
    print("✓ Interceptor installed successfully")

    # Start a session
    logger.start_session(server_info={"test": "integration"})
    print("✓ Session started")

    # Simulate some calls
    logger.log_request("test_method", "arg1", kwarg1="value1")
    logger.log_response("test_method", {"result": "success"})
    print("✓ Logged request/response pair")

    # End session
    logger.end_session()
    print("✓ Session ended and saved")

    # Verify file was created
    trace_file = Path("test_integration.jsonl")
    assert trace_file.exists(), "Trace file should be created"

    # Read back the session
    reader = TraceReader(str(trace_file))
    sessions = reader.read_sessions()
    assert len(sessions) == 1, "Should have 1 session"
    assert len(sessions[0].calls) == 1, "Should have 1 call"
    print(f"✓ Verified session data")

    # Cleanup
    trace_file.unlink()
    print("✓ Integration test files cleaned up")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("MCP INTERCEPTOR & MOCK GENERATOR - WORKFLOW TEST")
    print("="*80)

    try:
        test_trace_format()
        test_mock_generation()
        test_interceptor_integration()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nThe complete workflow is working:")
        print("  1. ✓ Interceptor captures MCP sessions")
        print("  2. ✓ Sessions are saved in machine-parsable format")
        print("  3. ✓ Mock servers are generated from traces")
        print("\nNext steps:")
        print("  - Run: python capture_example.py (to capture real MCP session)")
        print("  - Run: python mock_generator.py mcp_sessions.jsonl")
        print("="*80 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
