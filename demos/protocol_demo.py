"""
Demo script to show the actual MCP protocol messages.

This shows the JSON-RPC messages sent between client and server.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demo_protocol():
    """Show the actual protocol messages."""
    print("🔍 MCP Protocol Demo")
    print("=" * 50)
    
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            print("\n📡 Step 1: Initialize Connection")
            print("-" * 30)
            
            # This sends a JSON-RPC message
            init_result = await session.initialize()
            print("✅ Initialized successfully")
            print(f"   Server: {init_result.serverInfo.name}")
            print(f"   Version: {init_result.serverInfo.version}")
            
            print("\n📋 Step 2: List Available Tools")
            print("-" * 30)
            
            # This sends another JSON-RPC message
            tools_response = await session.list_tools()
            print(f"✅ Found {len(tools_response.tools)} tools:")
            for tool in tools_response.tools:
                print(f"   - {tool.name}: {tool.description}")
            
            print("\n🔧 Step 3: Call a Tool")
            print("-" * 30)
            
            # This sends a tool call JSON-RPC message
            result = await session.call_tool("sum", {"a": 5, "b": 3})
            print("✅ Tool call completed")
            print(f"   Result: {result.content[0].text}")


if __name__ == "__main__":
    print("This demo shows the MCP protocol in action.")
    print("The actual JSON-RPC messages are handled by the MCP SDK.")
    print("Below is what happens at a high level:\n")
    asyncio.run(demo_protocol())
