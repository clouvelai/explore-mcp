"""
Backend services module.

This module contains the business logic and external service integrations.

Services:
- MCPService: Manages connections to MCP servers, tool discovery, and execution
- OpenAIService: Handles OpenAI API interactions for chat completions

These services are designed to be:
- Testable: Easy to mock for unit testing
- Reusable: Can be used across different endpoints
- Maintainable: Clear separation of concerns

Usage:
    from backend.services.mcp_service import MCPService
    from backend.services.openai_service import OpenAIService
    
    mcp_service = MCPService(token_store, oauth_handler)
    openai_service = OpenAIService(api_key)
"""