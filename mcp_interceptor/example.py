import asyncio

# IMPORTANT: Install interceptor BEFORE importing ClientSession
from mcp_interceptor import install_interceptor
install_interceptor(
    log_file="mcp_trace.log",
    verbose=True
)

# Now import MCP components (ClientSession is now intercepted)
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

tools_queries = {
    'microsoft_docs_search'
}

async def list_tools(url):
    async with streamablehttp_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()

            for tool in tools.tools:

                # Get required params from schema
                schema = tool.inputSchema
                required = schema.get('required', [])
                props = schema.get('properties', {})

                # Build sample args
                args = {}
                for param in required:
                    args[param] = "test"  # Use sample value


                await session.call_tool(tool.name, args)


if __name__ == "__main__":
    url = "https://learn.microsoft.com/api/mcp"
    asyncio.run(list_tools(url))