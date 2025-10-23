"""
Chat API endpoints.
"""

import asyncio
import json

from flask import Blueprint, jsonify, request

from backend.services.mcp_service import MCPService
from backend.services.openai_service import OpenAIService

chat_bp = Blueprint('chat', __name__)

# Store conversation history
conversation_history = []


def setup_chat_routes(mcp_service: MCPService, openai_service: OpenAIService):
    """Setup chat routes with services."""
    
    @chat_bp.route('/api/chat', methods=['POST'])
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
            openai_tools = loop.run_until_complete(mcp_service.get_tools())
            
            # Call OpenAI with tools
            response = openai_service.chat_completion(
                messages=conversation_history,
                tools=openai_tools
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
                        mcp_service.call_tool(function_name, function_args, server_key)
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
                final_response = openai_service.chat_completion_with_tools(
                    messages=conversation_history
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

    @chat_bp.route('/api/history', methods=['GET'])
    def get_history():
        """Get conversation history."""
        return jsonify({"history": conversation_history})

    @chat_bp.route('/api/clear', methods=['POST'])
    def clear_history():
        """Clear conversation history."""
        global conversation_history
        conversation_history = []
        return jsonify({"message": "History cleared"})
    
    return chat_bp