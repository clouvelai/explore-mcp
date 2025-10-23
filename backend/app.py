"""
Main Flask application for the MCP chat backend.
"""

import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from backend.api.auth import setup_auth_routes
from backend.api.chat import setup_chat_routes
from backend.api.servers import setup_servers_routes
from backend.api.tools import setup_tools_routes
from backend.auth.oauth_handler import GoogleOAuthHandler
from backend.auth.token_store import TokenStore
from backend.services.mcp_service import MCPService
from backend.services.openai_service import OpenAIService

# Load environment variables
load_dotenv()


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    CORS(app, supports_credentials=True)  # Enable CORS with credentials
    
    # Initialize services
    token_store = TokenStore()
    oauth_handler = GoogleOAuthHandler(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_uri="http://localhost:5001/api/oauth/callback"
    )
    mcp_service = MCPService(token_store, oauth_handler)
    openai_service = OpenAIService(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Setup route blueprints
    chat_bp = setup_chat_routes(mcp_service, openai_service)
    tools_bp = setup_tools_routes(mcp_service)
    servers_bp = setup_servers_routes(mcp_service)
    auth_bp = setup_auth_routes(oauth_handler, token_store, mcp_service.servers)
    
    # Register blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(servers_bp)
    app.register_blueprint(auth_bp)
    
    return app


def run_app():
    """Run the Flask application."""
    app = create_app()
    
    print("🚀 Starting chat backend...")
    print("📡 Connecting to MCP servers...")
    print("🌐 Backend running on http://localhost:5001")
    print("\n📋 Available servers:")
    
    # Create a temporary MCP service to get server info
    token_store = TokenStore()
    oauth_handler = GoogleOAuthHandler(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    mcp_service = MCPService(token_store, oauth_handler)
    
    for key, config in mcp_service.servers.items():
        auth_status = "🔐 Requires auth" if config.get("requires_auth") else "✅ No auth needed"
        print(f"  - {config['name']}: {auth_status}")
    
    app.run(debug=True, port=5001)


if __name__ == '__main__':
    run_app()