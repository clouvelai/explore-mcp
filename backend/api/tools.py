"""
Tools API endpoints.
"""

import asyncio

from flask import Blueprint, jsonify

from backend.services.mcp_service import MCPService

tools_bp = Blueprint('tools', __name__)


def setup_tools_routes(mcp_service: MCPService):
    """Setup tools routes with services."""
    
    @tools_bp.route('/api/tools', methods=['GET'])
    def get_tools():
        """Get available MCP tools."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            openai_tools = loop.run_until_complete(mcp_service.get_tools())
            loop.close()
            return jsonify({"tools": openai_tools})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return tools_bp