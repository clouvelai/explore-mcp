# Authentication Discovery Findings

## Summary
Investigation into MCP server discovery with authentication reveals the following:

## Local Server Authentication
1. **Gmail/Google Drive servers**: Use environment variables for OAuth tokens (GOOGLE_ACCESS_TOKEN, GOOGLE_REFRESH_TOKEN)
2. **Discovery works WITHOUT authentication**: The MCP protocol allows tool schema discovery without auth - only actual tool execution requires valid credentials
3. This is by design - allows clients to understand server capabilities before authentication

## Remote Server Authentication Types

### Tested Servers:
1. **Microsoft Learn** (https://learn.microsoft.com/api/mcp)
   - No authentication required
   - Successfully discovers 3 tools

2. **Alpha Vantage** (https://mcp.alphavantage.co/mcp)
   - Requires API key via URL parameter: `?apikey=YOUR_API_KEY`
   - Returns 401 without key
   - OAuth option also available

3. **GitHub** (https://api.githubcopilot.com/mcp/)
   - Requires Bearer token authentication
   - Returns 401 with WWW-Authenticate header
   - Has readonly endpoint at `/mcp/readonly` for limited access

## MCP Inspector Support
- Supports `--header` parameter for HTTP headers
- Can pass authentication as: `--header "Authorization: Bearer TOKEN"`
- Supports both HTTP and SSE transports with headers

## Current Discovery Implementation
- `ai_generation/discovery.py` uses MCP Inspector CLI
- Does NOT currently support authentication headers
- Fails gracefully on 401 responses but cannot discover authenticated tools

## Next Steps
To enable authenticated discovery:
1. Add `auth_headers` parameter to DiscoveryEngine.discover()
2. Pass headers to MCP Inspector via `--header` flag
3. Support different auth methods:
   - Bearer tokens (GitHub, most OAuth servers)
   - API keys in URL (Alpha Vantage)
   - Basic auth headers
   - Custom headers

## Implications
- Many public MCP servers require authentication even for discovery
- Without auth support, we cannot generate mock servers for these services
- Adding auth support would significantly expand the platform's capabilities