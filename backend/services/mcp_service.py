"""
MCP service for managing connections to MCP servers.
"""

import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from backend.auth.oauth_handler import GoogleOAuthHandler
from backend.auth.token_store import TokenStore


class MCPService:
    """Service for managing MCP server connections and tools."""
    
    def __init__(self, token_store: TokenStore, oauth_handler: GoogleOAuthHandler):
        self.token_store = token_store
        self.oauth_handler = oauth_handler
        
        # MCP Server configurations
        self.servers = {
            "calculator": {
                "name": "Calculator",
                "transport": "stdio",
                "command": "python",
                "args": ["mcp_servers/calculator/server.py"],
                "requires_auth": False,
            },
            "google-drive": {
                "name": "Google Drive",
                "transport": "stdio",
                "command": "python",
                "args": ["mcp_servers/google_drive/server.py"],
                "requires_auth": True,
                "auth_type": "google_oauth"
            },
            "gmail": {
                "name": "Gmail",
                "transport": "stdio",
                "command": "python",
                "args": ["mcp_servers/gmail/server.py"],
                "requires_auth": True,
                "auth_type": "google_oauth"
            },
            "air-fryer": {
                "name": "Air Fryer (HTTP)",
                "transport": "sse",
                "url": "http://localhost:8080/sse",
                "requires_auth": False,
            }
            # Example HTTP server configuration:
            # "remote-mcp-server": {
            #     "name": "Remote MCP Server",
            #     "transport": "sse",
            #     "url": "https://api.example.com/mcp",
            #     "requires_auth": False,
            # }
        }
    
    async def get_server_env(self, server_key: str) -> dict:
        """Get environment variables for a specific MCP server."""
        env = dict(os.environ)
        
        server_config = self.servers.get(server_key)
        if not server_config:
            return env
        
        # Add auth tokens if needed
        if server_config.get("requires_auth") and server_config.get("auth_type") == "google_oauth":
            tokens = self.token_store.get_tokens(server_key)
            if tokens:
                # Check if expired and refresh
                if self.token_store.is_token_expired(server_key):
                    print(f"🔄 Token expired for {server_key}, refreshing...")
                    try:
                        new_tokens = self.oauth_handler.refresh_access_token(tokens['refresh_token'])
                        self.token_store.save_tokens(server_key, new_tokens)
                        tokens = new_tokens
                    except Exception as e:
                        print(f"❌ Token refresh failed: {e}")
                        return None
                
                env["GOOGLE_ACCESS_TOKEN"] = tokens['access_token']
                if tokens.get('refresh_token'):
                    env["GOOGLE_REFRESH_TOKEN"] = tokens['refresh_token']
        
        return env

    async def _create_client_session(self, server_config: dict, env: dict):
        """Create appropriate client session based on transport type."""
        transport = server_config.get("transport", "stdio")
        
        if transport == "stdio":
            # Stdio transport
            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config["args"],
                env=env
            )
            return stdio_client(server_params)
        elif transport == "sse":
            # SSE/HTTP transport
            url = server_config["url"]
            return sse_client(url)
        else:
            raise ValueError(f"Unsupported transport type: {transport}")

    async def get_tools(self):
        """Connect to all available MCP servers and get tools."""
        all_tools = []
        
        for server_key, server_config in self.servers.items():
            # Skip servers that require auth but don't have tokens
            if server_config.get("requires_auth"):
                if not self.token_store.get_tokens(server_key):
                    print(f"⏭️  Skipping {server_config['name']} - not authenticated")
                    continue
            
            try:
                # Get environment for this server
                env = await self.get_server_env(server_key)
                if env is None:  # Auth failed
                    continue
                
                # Create appropriate client based on transport
                async with self._create_client_session(server_config, env) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        # Get tools
                        tools_response = await session.list_tools()
                        
                        # Convert MCP tools to OpenAI function format
                        for tool in tools_response.tools:
                            all_tools.append({
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.inputSchema,
                                },
                                "_server": server_key  # Track which server owns this tool
                            })
                        
                        print(f"✅ Loaded {len(tools_response.tools)} tools from {server_config['name']}")
            
            except Exception as e:
                print(f"❌ Failed to load tools from {server_config['name']}: {e}")
                continue
        
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict, server_key: str = None):
        """Execute an MCP tool on the appropriate server."""
        # Find which server has this tool
        if not server_key:
            # Try to find the tool in any server
            for key, config in self.servers.items():
                if config.get("requires_auth") and not self.token_store.get_tokens(key):
                    continue
                server_key = key
                break
        
        if not server_key or server_key not in self.servers:
            raise ValueError(f"No server found for tool {tool_name}")
        
        server_config = self.servers[server_key]
        
        # Get environment for this server
        env = await self.get_server_env(server_key)
        if env is None:
            raise ValueError(f"Authentication failed for {server_config['name']}")
        
        # Create appropriate client based on transport
        async with self._create_client_session(server_config, env) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                
                # Extract text from result
                result_text = ""
                for content in result.content:
                    if hasattr(content, 'text'):
                        result_text += content.text
                
                return result_text

    def get_server_info(self):
        """Get list of available MCP servers and their auth status."""
        servers = []
        for key, config in self.servers.items():
            server_info = {
                "key": key,
                "name": config["name"],
                "transport": config.get("transport", "stdio"),
                "requires_auth": config.get("requires_auth", False),
                "authenticated": False
            }
            
            if config.get("requires_auth"):
                tokens = self.token_store.get_tokens(key)
                server_info["authenticated"] = tokens is not None and not self.token_store.is_token_expired(key)
            else:
                server_info["authenticated"] = True  # No auth needed
            
            servers.append(server_info)
        
        return servers