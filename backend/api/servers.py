"""
Servers API endpoints.
"""

from flask import Blueprint, jsonify
from backend.services.mcp_service import MCPService

servers_bp = Blueprint('servers', __name__)


def setup_servers_routes(mcp_service: MCPService):
    """Setup servers routes with services."""
    
    @servers_bp.route('/api/servers', methods=['GET'])
    def get_servers():
        """Get list of available MCP servers and their auth status."""
        servers = mcp_service.get_server_info()
        return jsonify({"servers": servers})
    
    return servers_bp