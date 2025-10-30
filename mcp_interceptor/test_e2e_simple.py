#!/usr/bin/env python3
"""
Simplified End-to-End Test

Verifies the complete workflow works:
1. Capture from real server → trace file
2. Generate mock from trace → Python file
3. Verify mock contains the captured data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import tempfile
from mcp_interceptor import install_interceptor, MockServerGenerator, TraceReader
from mcp.client.streamable_http import streamablehttp_client

async def main():
    print("="*80)
    print("SIMPLIFIED END-TO-END TEST")
    print("="*80)

    # Step 1: Capture
    print("\n📝 Step 1: Capturing from Microsoft Learn MCP Server...")
    trace_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False).name
    
    logger = install_interceptor(trace_file=trace_file, verbose=False)
    from mcp import ClientSession
    
    url = "https://learn.microsoft.com/api/mcp"
    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            logger.start_session(server_info={'url': url})
            
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("microsoft_docs_search", {"query": "python"})
            
            logger.end_session()
    
    print(f"✅ Captured {len(tools.tools)} tools and 1 tool call")
    
    # Step 2: Verify trace
    print("\n🔍 Step 2: Verifying trace data...")
    reader = TraceReader(trace_file)
    sessions = reader.read_sessions()
    
    assert len(sessions) == 1, "Should have 1 session"
    assert len(sessions[0].calls) >= 3, "Should have at least 3 calls (init, list_tools, call_tool)"
    
    call_tool_calls = [c for c in sessions[0].calls if c.request.method == 'call_tool']
    assert len(call_tool_calls) >= 1, "Should have at least 1 call_tool"
    assert call_tool_calls[0].response.success, "call_tool should succeed"
    
    print(f"✅ Trace contains {len(sessions[0].calls)} calls")
    
    # Step 3: Generate mock
    print("\n🎭 Step 3: Generating mock server...")
    mock_file = "e2e_test_mock.py"
    
    generator = MockServerGenerator(trace_file)
    analysis = generator.analyze_sessions()
    generator.generate_mock_server(mock_file, "E2ETestMock")
    
    assert Path(mock_file).exists(), "Mock file should exist"
    assert 'call_tool' in analysis['methods'], "Should have call_tool method"
    
    print(f"✅ Generated mock with methods: {', '.join(analysis['methods'])}")
    
    # Step 4: Verify mock content
    print("\n✅ Step 4: Verifying mock file content...")
    mock_content = Path(mock_file).read_text()
    
    assert 'MOCK_RESPONSES' in mock_content, "Should have MOCK_RESPONSES"
    assert 'microsoft_docs_search' in mock_content, "Should contain tool name"
    assert 'python' in mock_content, "Should contain search query"
    assert 'isError' in mock_content, "Should contain isError flag"
    assert 'class E2ETestMock' in mock_content, "Should have correct class name"
    
    print("✅ Mock file contains all expected data")
    
    # Cleanup
    Path(trace_file).unlink()
    Path(mock_file).unlink()
    
    print("\n" + "="*80)
    print("🎉 SIMPLIFIED E2E TEST PASSED!")
    print("="*80)
    print("\n✅ Complete workflow verified:")
    print("  1. Real server → trace file")
    print("  2. Trace file → mock server code")
    print("  3. Mock contains captured data")
    print("\nThe mock generation pipeline works correctly!")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    try:
        exit(asyncio.run(main()))
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
