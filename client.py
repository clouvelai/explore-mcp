"""
Simple MCP Client to test the server.

This client connects to the MCP server and demonstrates how to:
1. Initialize a connection
2. List available tools
3. Call a tool with arguments
4. Parse the results
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_client():
    """Run the MCP client and test the sum tool."""
    # Configure the server connection
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )
    
    print("🚀 Connecting to MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            print("✅ Connected to server\n")
            
            # List available tools
            print("📋 Available tools:")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # List available prompts
            print("💡 Available prompts:")
            prompts_response = await session.list_prompts()
            for prompt in prompts_response.prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            print()
            
            # Test the sum tool with different inputs
            test_cases = [
                {"a": 5, "b": 3},
                {"a": 10, "b": 20},
                {"a": -5, "b": 15},
                {"a": 3.14, "b": 2.86},
            ]
            
            print("🧮 Testing sum tool:")
            for test_case in test_cases:
                result = await session.call_tool("sum", test_case)
                
                # Parse the result
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(f"  {test_case['a']} + {test_case['b']} → {content.text}")
            
            # Test the prompt
            print("\n📝 Testing explain_calculation prompt:")
            prompt_result = await session.get_prompt(
                "explain_calculation",
                arguments={"calculation": "25 + 17"}
            )
            
            print(f"  Description: {prompt_result.description}")
            print(f"\n  Generated prompt text:")
            print("  " + "-" * 60)
            for message in prompt_result.messages:
                if hasattr(message.content, 'text'):
                    # Print with indentation
                    for line in message.content.text.split('\n'):
                        print(f"  {line}")
            print("  " + "-" * 60)
            
            print("\n✨ All tests completed successfully!")


def main():
    """Entry point for the client."""
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("\n👋 Client stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

