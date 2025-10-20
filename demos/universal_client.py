"""
Universal MCP client that can connect to either stdio or HTTP servers.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client


async def test_stdio_server():
    """Test your local stdio server."""
    print("🔌 Testing stdio server...")
    
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print(f"✅ stdio server tools: {[t.name for t in tools.tools]}")
            
            result = await session.call_tool("sum", {"a": 5, "b": 3})
            print(f"✅ stdio result: {result.content[0].text}")


async def test_http_server():
    """Test the HTTP server (if running)."""
    print("\n🌐 Testing HTTP server...")
    
    try:
        async with sse_client("http://localhost:8000/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                print(f"✅ HTTP server tools: {[t.name for t in tools.tools]}")
                
                result = await session.call_tool("sum", {"a": 5, "b": 3})
                print(f"✅ HTTP result: {result.content[0].text}")
                
    except Exception as e:
        print(f"❌ HTTP server not available: {e}")
        print("💡 Start HTTP server with: python http_server.py")


async def main():
    """Test both server types."""
    print("🧪 Testing Universal MCP Client")
    print("=" * 50)
    
    # Test stdio server (your current setup)
    await test_stdio_server()
    
    # Test HTTP server (if running)
    await test_http_server()
    
    print("\n💡 Key Point:")
    print("   Same client code works with both transports!")
    print("   Only the connection method changes.")


if __name__ == "__main__":
    asyncio.run(main())
