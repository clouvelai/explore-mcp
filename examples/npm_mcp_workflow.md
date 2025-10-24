# NPM MCP Server Workflow

## Example: Filesystem Server

```bash
# Add filesystem operations server from npm (--source npm required)
./mcp add fs @modelcontextprotocol/server-filesystem --source npm --category "Storage"

# Discover tools (finds 14 filesystem tools)
./mcp discover fs

# Generate mock server for testing
./mcp generate fs

# Run tests
./mcp test fs
```

**Key features:**
- Installs npm package globally and detects binary automatically
- Captures package version from npm registry  
- Works like local servers after installation (stdio transport)
- Must use `--source npm` flag explicitly