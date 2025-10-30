#!/usr/bin/env python3
"""
End-to-End Test: Real Server → Mock Server Verification

This test verifies the complete workflow:
1. Connect to Microsoft Learn MCP server (real)
2. Capture interactions to trace file
3. Generate mock server from trace
4. Run mock server locally
5. Execute same queries against mock
6. Verify outputs are identical
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
import tempfile
import subprocess
import time
from typing import List, Dict, Any

from mcp_interceptor import install_interceptor, MockServerGenerator
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.stdio import stdio_client, StdioServerParameters


class E2ETest:
    """End-to-end test orchestrator"""

    def __init__(self):
        self.real_server_url = "https://learn.microsoft.com/api/mcp"
        self.trace_file = None
        self.mock_file = None
        self.real_results = []
        self.mock_results = []
        self.test_queries = [
            {"tool": "microsoft_docs_search", "args": {"query": "python"}},
            {"tool": "microsoft_docs_search", "args": {"query": "async"}},
        ]

    async def step1_capture_from_real_server(self):
        """Step 1: Connect to real server and capture interactions"""
        print("\n" + "="*80)
        print("STEP 1: Capturing from Real Microsoft Learn MCP Server")
        print("="*80)

        # Create temporary trace file
        self.trace_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jsonl', delete=False
        ).name

        # Install interceptor BEFORE importing ClientSession
        logger = install_interceptor(
            trace_file=self.trace_file,
            verbose=False
        )

        # NOW import ClientSession (after interception is installed)
        from mcp import ClientSession

        print(f"📝 Trace file: {self.trace_file}")
        print(f"🌐 Connecting to: {self.real_server_url}")

        try:
            async with streamablehttp_client(self.real_server_url) as (reader, writer, _):
                async with ClientSession(reader, writer) as session:
                    # Start session tracking
                    logger.start_session(server_info={
                        'url': self.real_server_url,
                        'type': 'real',
                        'description': 'Microsoft Learn MCP Server'
                    })

                    print("  ✓ Connected")

                    # Initialize
                    init_result = await session.initialize()
                    print(f"  ✓ Initialized (protocol: {init_result.protocolVersion})")

                    # List tools
                    tools_result = await session.list_tools()
                    print(f"  ✓ Listed {len(tools_result.tools)} tools")

                    # Call tools with our test queries
                    for query in self.test_queries:
                        tool_name = query["tool"]
                        args = query["args"]

                        print(f"  🔧 Calling: {tool_name}({args})")
                        result = await session.call_tool(tool_name, args)

                        # Store result for comparison
                        self.real_results.append({
                            'tool': tool_name,
                            'args': args,
                            'result': self._serialize_result(result)
                        })
                        print(f"     ✓ Got {len(result.content)} content items")

                    # End session
                    logger.end_session()
                    print("  ✓ Session captured")

            print("\n✅ Step 1 Complete: Captured real server interactions")
            return True

        except Exception as e:
            print(f"\n❌ Step 1 Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def step2_generate_mock_server(self):
        """Step 2: Generate mock server from trace"""
        print("\n" + "="*80)
        print("STEP 2: Generating Mock Server")
        print("="*80)

        try:
            # Create mock file in current directory for debugging
            self.mock_file = "debug_mock_server.py"

            print(f"📝 Reading trace: {self.trace_file}")
            print(f"🎭 Mock output: {self.mock_file}")

            # Generate mock server
            generator = MockServerGenerator(self.trace_file)
            analysis = generator.analyze_sessions()

            print(f"  ✓ Analyzed {analysis['total_sessions']} session(s)")
            print(f"  ✓ Found methods: {', '.join(analysis['methods'])}")

            generator.generate_mock_server(self.mock_file, "E2EMockServer")
            print(f"  ✓ Generated mock server")

            # Verify the file exists and is valid Python
            mock_path = Path(self.mock_file)
            assert mock_path.exists(), "Mock file should exist"
            assert mock_path.stat().st_size > 0, "Mock file should not be empty"

            # Quick syntax check
            with open(self.mock_file, 'r') as f:
                content = f.read()
                compile(content, self.mock_file, 'exec')
            print("  ✓ Mock server syntax is valid")

            print("\n✅ Step 2 Complete: Mock server generated")
            return True

        except Exception as e:
            print(f"\n❌ Step 2 Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def step3_query_mock_server(self):
        """Step 3: Run mock server and query it with same requests"""
        print("\n" + "="*80)
        print("STEP 3: Querying Mock Server")
        print("="*80)

        # Import ClientSession (no interceptor needed for mock)
        from mcp import ClientSession

        print(f"🎭 Starting mock server: {self.mock_file}")

        # Start mock server as subprocess
        mock_process = subprocess.Popen(
            [sys.executable, self.mock_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            # Give server a moment to start
            await asyncio.sleep(0.5)

            # Check if process started successfully
            if mock_process.poll() is not None:
                stderr = mock_process.stderr.read().decode()
                raise RuntimeError(f"Mock server failed to start: {stderr}")

            print("  ✓ Mock server started")

            # Connect to mock server via stdio
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[self.mock_file]
            )
            async with stdio_client(server_params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    print("  ✓ Connected to mock")

                    # Initialize
                    init_result = await session.initialize()
                    print(f"  ✓ Initialized mock (protocol: {init_result.protocolVersion})")

                    # List tools
                    tools_result = await session.list_tools()
                    print(f"  ✓ Listed {len(tools_result.tools)} tools from mock")

                    # Call tools with same queries
                    for query in self.test_queries:
                        tool_name = query["tool"]
                        args = query["args"]

                        print(f"  🔧 Calling: {tool_name}({args})")
                        result = await session.call_tool(tool_name, args)

                        # Debug: check the actual result object
                        print(f"     [DEBUG] Raw result isError: {result.isError if hasattr(result, 'isError') else 'NO ATTR'}")

                        # Store result for comparison
                        self.mock_results.append({
                            'tool': tool_name,
                            'args': args,
                            'result': self._serialize_result(result)
                        })
                        print(f"     ✓ Got {len(result.content)} content items")

            print("\n✅ Step 3 Complete: Queried mock server")
            return True

        except Exception as e:
            print(f"\n❌ Step 3 Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up mock server process
            if mock_process.poll() is None:
                mock_process.terminate()
                try:
                    mock_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    mock_process.kill()

    def step4_compare_results(self):
        """Step 4: Compare real vs mock results"""
        print("\n" + "="*80)
        print("STEP 4: Comparing Real vs Mock Results")
        print("="*80)

        if len(self.real_results) != len(self.mock_results):
            print(f"❌ Result count mismatch:")
            print(f"   Real: {len(self.real_results)} results")
            print(f"   Mock: {len(self.mock_results)} results")
            return False

        print(f"📊 Comparing {len(self.real_results)} result(s)...\n")

        all_match = True
        for i, (real, mock) in enumerate(zip(self.real_results, self.mock_results)):
            print(f"Result #{i+1}: {real['tool']}({real['args']})")

            # Compare tool name
            if real['tool'] != mock['tool']:
                print(f"  ❌ Tool name mismatch: {real['tool']} vs {mock['tool']}")
                all_match = False
                continue

            # Compare args
            if real['args'] != mock['args']:
                print(f"  ❌ Args mismatch: {real['args']} vs {mock['args']}")
                all_match = False
                continue

            # Compare result structure
            real_result = real['result']
            mock_result = mock['result']

            # Check content count
            real_content_count = len(real_result.get('content', []))
            mock_content_count = len(mock_result.get('content', []))

            if real_content_count != mock_content_count:
                print(f"  ❌ Content count mismatch: {real_content_count} vs {mock_content_count}")
                all_match = False
                continue

            # Check isError flag
            real_is_error = real_result.get('isError')
            mock_is_error = mock_result.get('isError')
            print(f"  [DEBUG] real isError: {real_is_error} (type: {type(real_is_error)})")
            print(f"  [DEBUG] mock isError: {mock_is_error} (type: {type(mock_is_error)})")
            print(f"  [DEBUG] real result keys: {list(real_result.keys())}")
            print(f"  [DEBUG] mock result keys: {list(mock_result.keys())}")

            if real_is_error != mock_is_error:
                print(f"  ❌ Error flag mismatch: {real_is_error} vs {mock_is_error}")
                all_match = False
                continue

            # Deep compare content
            if not self._compare_content(real_result['content'], mock_result['content']):
                print(f"  ❌ Content mismatch")
                all_match = False
                continue

            print(f"  ✅ Results match!")

        if all_match:
            print("\n✅ Step 4 Complete: All results match!")
            return True
        else:
            print("\n❌ Step 4 Failed: Some results don't match")
            return False

    def _serialize_result(self, result) -> Dict[str, Any]:
        """Serialize MCP result to comparable dict"""
        if hasattr(result, '__dict__'):
            serialized = {}
            for key, value in result.__dict__.items():
                if key.startswith('_'):
                    continue
                if isinstance(value, list):
                    serialized[key] = [self._serialize_result(item) for item in value]
                elif hasattr(value, '__dict__'):
                    serialized[key] = self._serialize_result(value)
                else:
                    serialized[key] = value
            return serialized
        return result

    def _compare_content(self, real_content: List, mock_content: List) -> bool:
        """Compare content arrays item by item"""
        if len(real_content) != len(mock_content):
            return False

        for real_item, mock_item in zip(real_content, mock_content):
            # Compare types
            real_type = real_item.get('type')
            mock_type = mock_item.get('type')
            if real_type != mock_type:
                print(f"    Content type mismatch: {real_type} vs {mock_type}")
                return False

            # For text content, compare text
            if real_type == 'text':
                real_text = real_item.get('text', '')
                mock_text = mock_item.get('text', '')
                if real_text != mock_text:
                    print(f"    Text mismatch:")
                    print(f"      Real: {real_text[:100]}...")
                    print(f"      Mock: {mock_text[:100]}...")
                    return False

        return True

    def cleanup(self):
        """Clean up temporary files"""
        print("\n" + "="*80)
        print("CLEANUP")
        print("="*80)

        if self.trace_file and Path(self.trace_file).exists():
            Path(self.trace_file).unlink()
            print(f"  ✓ Removed trace file: {self.trace_file}")

        # Keep mock file for debugging
        if self.mock_file and Path(self.mock_file).exists():
            print(f"  ℹ️  Kept mock file for inspection: {self.mock_file}")

    async def run(self):
        """Run the complete end-to-end test"""
        print("\n" + "="*80)
        print("END-TO-END TEST: Real Server → Mock Server Verification")
        print("="*80)
        print("\nThis test will:")
        print("  1. Capture interactions from Microsoft Learn MCP server")
        print("  2. Generate a mock server from the trace")
        print("  3. Query the mock server with same requests")
        print("  4. Verify the outputs are identical")

        try:
            # Step 1: Capture from real server
            if not await self.step1_capture_from_real_server():
                return False

            # Step 2: Generate mock
            if not self.step2_generate_mock_server():
                return False

            # Step 3: Query mock
            if not await self.step3_query_mock_server():
                return False

            # Step 4: Compare
            if not self.step4_compare_results():
                return False

            # Success!
            print("\n" + "="*80)
            print("🎉 END-TO-END TEST PASSED! 🎉")
            print("="*80)
            print("\nVerification complete:")
            print("  ✅ Real server interactions captured")
            print("  ✅ Mock server generated")
            print("  ✅ Mock server produces identical output")
            print("  ✅ Complete workflow validated")
            print("\nThe mock server is a perfect replica!")
            print("="*80)

            return True

        except Exception as e:
            print("\n" + "="*80)
            print("❌ END-TO-END TEST FAILED")
            print("="*80)
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.cleanup()


async def main():
    """Run the end-to-end test"""
    test = E2ETest()
    success = await test.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
