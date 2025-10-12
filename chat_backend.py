"""
Chat backend that connects OpenAI to multiple MCP servers.

This Flask backend:
1. Receives chat messages from the frontend
2. Connects to multiple MCP servers (calculator + Google Drive)
3. Calls OpenAI with tool definitions from all servers
4. Executes MCP tools when OpenAI requests them
5. Handles OAuth flow for Google Drive authentication
6. Returns responses to the frontend
"""

import asyncio
import json
import os
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from token_store import TokenStore
from oauth_handler import GoogleOAuthHandler

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
CORS(app, supports_credentials=True)  # Enable CORS with credentials

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize token store
token_store = TokenStore()

# Initialize OAuth handler
oauth_handler = GoogleOAuthHandler(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_uri="http://localhost:5001/api/oauth/callback"
)

# Store conversation history
conversation_history = []

# MCP Server configurations
MCP_SERVERS = {
    "calculator": {
        "name": "Calculator",
        "command": "python",
        "args": ["server.py"],
        "requires_auth": False,
    },
    "google-drive": {
        "name": "Google Drive",
        "command": "python",
        "args": ["google_drive_mcp_server.py"],
        "requires_auth": True,
        "auth_type": "google_oauth"
    }
}


async def get_server_env(server_key: str) -> dict:
    """Get environment variables for a specific MCP server."""
    env = dict(os.environ)
    
    server_config = MCP_SERVERS.get(server_key)
    if not server_config:
        return env
    
    # Add auth tokens if needed
    if server_config.get("requires_auth") and server_config.get("auth_type") == "google_oauth":
        tokens = token_store.get_tokens(server_key)
        if tokens:
            # Check if expired and refresh
            if token_store.is_token_expired(server_key):
                print(f"🔄 Token expired for {server_key}, refreshing...")
                try:
                    new_tokens = oauth_handler.refresh_access_token(tokens['refresh_token'])
                    token_store.save_tokens(server_key, new_tokens)
                    tokens = new_tokens
                except Exception as e:
                    print(f"❌ Token refresh failed: {e}")
                    return None
            
            env["GOOGLE_ACCESS_TOKEN"] = tokens['access_token']
            if tokens.get('refresh_token'):
                env["GOOGLE_REFRESH_TOKEN"] = tokens['refresh_token']
    
    return env


async def get_mcp_tools():
    """Connect to all available MCP servers and get tools."""
    all_tools = []
    
    for server_key, server_config in MCP_SERVERS.items():
        # Skip servers that require auth but don't have tokens
        if server_config.get("requires_auth"):
            if not token_store.get_tokens(server_key):
                print(f"⏭️  Skipping {server_config['name']} - not authenticated")
                continue
        
        try:
            # Get environment for this server
            env = await get_server_env(server_key)
            if env is None:  # Auth failed
                continue
            
            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config["args"],
                env=env
            )
            
            async with stdio_client(server_params) as (read, write):
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


async def call_mcp_tool(tool_name: str, arguments: dict, server_key: str = None):
    """Execute an MCP tool on the appropriate server."""
    # Find which server has this tool
    if not server_key:
        # Try to find the tool in any server
        for key, config in MCP_SERVERS.items():
            if config.get("requires_auth") and not token_store.get_tokens(key):
                continue
            server_key = key
            break
    
    if not server_key or server_key not in MCP_SERVERS:
        raise ValueError(f"No server found for tool {tool_name}")
    
    server_config = MCP_SERVERS[server_key]
    
    # Get environment for this server
    env = await get_server_env(server_key)
    if env is None:
        raise ValueError(f"Authentication failed for {server_config['name']}")
    
    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"],
        env=env
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            
            # Extract text from result
            result_text = ""
            for content in result.content:
                if hasattr(content, 'text'):
                    result_text += content.text
            
            return result_text


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the frontend."""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Get MCP tools in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        openai_tools = loop.run_until_complete(get_mcp_tools())
        
        # Call OpenAI with tools
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            tools=openai_tools if openai_tools else None,
            tool_choice="auto",
        )
        
        assistant_message = response.choices[0].message
        
        # Handle tool calls
        if assistant_message.tool_calls:
            # Add assistant's tool call to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            # Execute each tool call and collect results
            tool_calls_made = []
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Find which server owns this tool
                server_key = None
                for tool in openai_tools:
                    if tool['function']['name'] == function_name:
                        server_key = tool.get('_server')
                        break
                
                # Call MCP tool
                result = loop.run_until_complete(
                    call_mcp_tool(function_name, function_args, server_key)
                )
                
                # Store tool call details
                tool_calls_made.append({
                    "name": function_name,
                    "args": function_args,
                    "result": result,
                    "id": tool_call.id
                })
                
                # Add tool result to history
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            
            # Get final response from OpenAI
            final_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,
            )
            
            final_message = final_response.choices[0].message.content
            conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            loop.close()
            return jsonify({
                "response": final_message,
                "tool_calls": tool_calls_made  # Send all tool calls
            })
        else:
            # No tool call, just return the response
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content
            })
            
            loop.close()
            return jsonify({
                "response": assistant_message.content
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history."""
    return jsonify({"history": conversation_history})


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return jsonify({"message": "History cleared"})


@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get available MCP tools."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        openai_tools = loop.run_until_complete(get_mcp_tools())
        loop.close()
        return jsonify({"tools": openai_tools})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/servers', methods=['GET'])
def get_servers():
    """Get list of available MCP servers and their auth status."""
    servers = []
    for key, config in MCP_SERVERS.items():
        server_info = {
            "key": key,
            "name": config["name"],
            "requires_auth": config.get("requires_auth", False),
            "authenticated": False
        }
        
        if config.get("requires_auth"):
            tokens = token_store.get_tokens(key)
            server_info["authenticated"] = tokens is not None and not token_store.is_token_expired(key)
        else:
            server_info["authenticated"] = True  # No auth needed
        
        servers.append(server_info)
    
    return jsonify({"servers": servers})


@app.route('/api/oauth/start/<server_key>', methods=['GET'])
def start_oauth(server_key):
    """Start OAuth flow for a server."""
    if server_key not in MCP_SERVERS:
        return jsonify({"error": "Invalid server"}), 400
    
    server_config = MCP_SERVERS[server_key]
    
    if not server_config.get("requires_auth"):
        return jsonify({"error": "Server doesn't require authentication"}), 400
    
    if server_config.get("auth_type") == "google_oauth":
        try:
            # Get authorization URL with server key in state
            auth_url, state = oauth_handler.get_authorization_url()
            
            # Encode server key into the state parameter
            import base64
            import json
            state_data = {
                "server_key": server_key,
                "random_state": state
            }
            encoded_state = base64.b64encode(json.dumps(state_data).encode()).decode()
            
            # Replace state in URL
            auth_url = auth_url.replace(f"state={state}", f"state={encoded_state}")
            
            return jsonify({
                "auth_url": auth_url,
                "state": encoded_state
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Unsupported auth type"}), 400


@app.route('/api/oauth/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback from Google."""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
            <h1>❌ Authentication Failed</h1>
            <p>Error: {error}</p>
            <p><a href="http://localhost:3000">Return to chat</a></p>
        </body>
        </html>
        """
    
    if not code:
        return "No authorization code received", 400
    
    # Decode state parameter
    try:
        import base64
        import json
        state_data = json.loads(base64.b64decode(state.encode()).decode())
        server_key = state_data.get('server_key')
        random_state = state_data.get('random_state')
    except Exception as e:
        return f"Invalid state parameter format: {str(e)}", 400
    
    if not server_key:
        return "No server key in state", 400
    
    try:
        # Exchange code for tokens (use the original random state)
        tokens = oauth_handler.exchange_code_for_tokens(code, random_state)
        
        # Save tokens
        token_store.save_tokens(server_key, tokens)
        
        # Return success page with auto-close
        return f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
            <h1>✅ Authentication Successful!</h1>
            <p>You can now use {MCP_SERVERS[server_key]['name']} tools.</p>
            <p>This window will close automatically...</p>
            <script>
                setTimeout(function() {{
                    window.close();
                }}, 2000);
            </script>
            <p><a href="http://localhost:3000">Return to chat</a></p>
        </body>
        </html>
        """
    
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
            <h1>❌ Authentication Failed</h1>
            <p>Error: {str(e)}</p>
            <p><a href="http://localhost:3000">Return to chat</a></p>
        </body>
        </html>
        """


@app.route('/api/oauth/disconnect/<server_key>', methods=['POST'])
def disconnect_oauth(server_key):
    """Disconnect/remove authentication for a server."""
    if server_key not in MCP_SERVERS:
        return jsonify({"error": "Invalid server"}), 400
    
    try:
        token_store.delete_tokens(server_key)
        return jsonify({"message": f"Disconnected from {MCP_SERVERS[server_key]['name']}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting chat backend...")
    print("📡 Connecting to MCP servers...")
    print("🌐 Backend running on http://localhost:5001")
    print("\n📋 Available servers:")
    for key, config in MCP_SERVERS.items():
        auth_status = "🔐 Requires auth" if config.get("requires_auth") else "✅ No auth needed"
        print(f"  - {config['name']}: {auth_status}")
    app.run(debug=True, port=5001)

