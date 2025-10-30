#!/usr/bin/env python3
"""
Example: Capturing MCP Communication for Mock Generation

This example shows how to use the interceptor to capture MCP server
communication in a structured format suitable for mock server generation.
"""

import sys
from pathlib import Path

# Add parent directory to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

# STEP 1: Install interceptor BEFORE importing ClientSession
from mcp_interceptor import install_interceptor

# Configure interceptor to save both formats:
# - trace_file: Structured session data for mock generation
# - log_file: Legacy NDJSON for human debugging
logger = install_interceptor(
    trace_file="mcp_sessions.jsonl",  # Machine-parsable format
    log_file="mcp_trace.log",         # Human-readable format
    verbose=True                       # Print to console
)

# STEP 2: Now import MCP components (ClientSession is now intercepted)
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def capture_mcp_session(url: str):
    """
    Capture a complete MCP session with all interactions
    """
    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            # Start session tracking
            logger.start_session(server_info={
                'url': url,
                'transport': 'http',
                'description': 'Microsoft Learn MCP Server'
            })

            # All these calls are automatically intercepted and recorded
            await session.initialize()

            tools = await session.list_tools()
            print(f"\n📋 Found {len(tools.tools)} tools\n")

            # Call each tool with sample arguments
            for tool in tools.tools:
                print(f"🔧 Testing tool: {tool.name}")

                # Extract required parameters
                schema = tool.inputSchema
                required = schema.get('required', [])
                props = schema.get('properties', {})

                # Build sample arguments
                args = {}
                for param in required:
                    param_type = props.get(param, {}).get('type', 'string')
                    if param_type == 'string':
                        args[param] = "test query"
                    elif param_type == 'number':
                        args[param] = 1
                    elif param_type == 'boolean':
                        args[param] = True

                # Call the tool (response is captured automatically)
                try:
                    result = await session.call_tool(tool.name, args)
                    print(f"  ✓ Success: {len(result.content)} content items")
                except Exception as e:
                    print(f"  ✗ Error: {e}")

            # End session and write to trace file
            logger.end_session()
            print("\n✓ Session captured successfully!")


async def main():
    """Run the capture example"""
    # Example with public Microsoft Learn MCP server
    url = "https://learn.microsoft.com/api/mcp"

    print("=" * 80)
    print("MCP Session Capture Example")
    print("=" * 80)
    print(f"\nConnecting to: {url}\n")

    await capture_mcp_session(url)

    print("\n" + "=" * 80)
    print("Capture complete! Files generated:")
    print("  📄 mcp_sessions.jsonl - Structured session data (for mock generation)")
    print("  📄 mcp_trace.log - Human-readable trace (for debugging)")
    print("\nNext steps:")
    print("  1. Generate mock server:")
    print("     python mock_generator.py mcp_sessions.jsonl -o mock_server.py")
    print("  2. Run the mock server:")
    print("     python mock_server.py")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
