import asyncio

# FIRST: Install interceptor BEFORE importing ClientSession
from mcp_interceptor import install_interceptor
logger = install_interceptor(log_file="mcp_trace.log", verbose=True)

# SECOND: Now import ClientSession (should get the intercepted version)
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

print(f"ClientSession class: {ClientSession}")
print(f"ClientSession module: {ClientSession.__module__}")
print(f"Is intercepted: {ClientSession.__name__}")


async def test():
    url = "https://learn.microsoft.com/api/mcp"

    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            print("\n=== Calling initialize ===")
            await session.initialize()

            print("\n=== Calling list_tools ===")
            tools = await session.list_tools()

            print(f"\n=== Found {len(tools.tools)} tools ===")
            for tool in tools.tools[:1]:  # Just first tool
                print(f"Tool: {tool.name}")

    print(f"\n\nTotal requests logged: {logger.request_count}")
    print(f"Total responses logged: {logger.response_count}")


if __name__ == "__main__":
    asyncio.run(test())
