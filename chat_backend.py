"""
Chat backend that connects OpenAI to the MCP server.

This Flask backend:
1. Receives chat messages from the frontend
2. Connects to the MCP server to get available tools
3. Calls OpenAI with tool definitions
4. Executes MCP tools when OpenAI requests them
5. Returns responses to the frontend
"""

import asyncio
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store conversation history
conversation_history = []


async def get_mcp_tools():
    """Connect to MCP server and get available tools."""
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get tools
            tools_response = await session.list_tools()
            
            # Convert MCP tools to OpenAI function format
            openai_tools = []
            for tool in tools_response.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    }
                })
            
            return openai_tools, session


async def call_mcp_tool(tool_name: str, arguments: dict):
    """Execute an MCP tool."""
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
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
        openai_tools, _ = loop.run_until_complete(get_mcp_tools())
        
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
                
                # Call MCP tool
                result = loop.run_until_complete(
                    call_mcp_tool(function_name, function_args)
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
        openai_tools, _ = loop.run_until_complete(get_mcp_tools())
        loop.close()
        return jsonify({"tools": openai_tools})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting chat backend...")
    print("📡 Connecting to MCP server on startup...")
    print("🌐 Backend running on http://localhost:5001")
    app.run(debug=True, port=5001)

