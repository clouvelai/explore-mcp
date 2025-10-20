"""
API endpoints module.

This module contains all RESTful API endpoints for the backend application.

Endpoints:
- chat.py: /api/chat - Main chat interface with OpenAI
- tools.py: /api/tools - MCP tool discovery and listing
- servers.py: /api/servers - MCP server status and authentication
- auth.py: /api/oauth/* - OAuth authentication flow

Each module exports a setup function that returns a configured Flask Blueprint:
    setup_*_routes(services...) -> Blueprint

Usage:
    from backend.api.chat import setup_chat_routes
    
    chat_bp = setup_chat_routes(mcp_service, openai_service)
    app.register_blueprint(chat_bp)
"""