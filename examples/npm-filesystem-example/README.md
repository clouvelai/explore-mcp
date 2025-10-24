# NPM MCP Server Example: Filesystem Operations

This example demonstrates how to install, configure, and use an npm-published MCP server with the MCP Registry.

## Package Used
- **Package**: `@modelcontextprotocol/server-filesystem`
- **Version**: Latest from npm registry
- **Purpose**: File system operations (read, write, list files)

## Quick Start

### 1. Install and Add Server
```bash
# Add the npm MCP server to registry (explicit --source npm required)
./mcp add filesystem @modelcontextprotocol/server-filesystem --source npm --category Storage --description "File system operations MCP server"
```

### 2. Discover Available Tools
```bash
# Discover what tools the server provides
./mcp discover filesystem
```

### 3. Generate Mock Server
```bash
# Generate a mock server for testing/development
./mcp generate filesystem
```

### 4. Test the Server
```bash
# Run evaluation tests
./mcp test filesystem
```

### 5. Inspect Server Details
```bash
# View complete server information
./mcp inspect filesystem
```

## Expected Output

### Installation
```
📦 Installing npm package: @modelcontextprotocol/server-filesystem
✅ Package installed successfully
🔍 Found binary: mcp-server-filesystem at /usr/local/bin/mcp-server-filesystem
📋 Package version: 2025.8.21
✅ Added server: filesystem (filesystem)
   Type: npm
   Package: @modelcontextprotocol/server-filesystem
   Binary: /usr/local/bin/mcp-server-filesystem
   Generated path: mcp_registry/servers/filesystem/generated
```

### Discovery Results
The filesystem server typically provides tools like:
- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `create_directory` - Create directories
- `delete_file` - Delete files
- `move_file` - Move/rename files

### Server Information
```
📋 Server: filesystem
==================================================
Name: filesystem
Description: File system operations MCP server
Category: Storage
Provider: npm
Version: 1.0.0

📍 Source:
Type: npm
Package: @modelcontextprotocol/server-filesystem
Version: 2025.8.21
Binary: mcp-server-filesystem
Binary Path: /usr/local/bin/mcp-server-filesystem
Transport: stdio

🛠️ Tools (14):
  • read_file: Read the complete contents of a file as text
  • write_file: Create a new file or completely overwrite an existing file
  • list_directory: List the contents of a directory
  • create_directory: Create a new directory
  • delete_file: Delete a file
  ... and 9 more tools
```

## Directory Structure

After running the example, you'll see:
```
mcp_registry/servers/filesystem/
├── config.json           # Server configuration
├── discovery.json        # Discovered tools and capabilities
└── generated/            # Generated mock server files
    ├── server.py         # Mock MCP server
    ├── tools.py          # Mock tool implementations
    └── evaluations.json  # Test evaluations
```

## Key Features Demonstrated

1. **NPM Package Installation**: Automatic global npm installation
2. **Binary Detection**: Automatic binary path discovery
3. **Version Tracking**: Package version capture from npm registry
4. **Tool Discovery**: MCP protocol discovery of available tools
5. **Mock Generation**: AI-powered mock server creation
6. **Testing**: Automated evaluation of server capabilities

## Configuration Details

The server configuration is stored in `mcp_registry/servers/filesystem/config.json`:

```json
{
  "id": "filesystem",
  "name": "filesystem",
  "source": {
    "type": "npm",
    "package_name": "@modelcontextprotocol/server-filesystem",
    "package_version": "2025.8.21",
    "binary_path": "/usr/local/bin/mcp-server-filesystem",
    "transport": "stdio"
  },
  "metadata": {
    "category": "Storage",
    "provider": "npm",
    "description": "File system operations MCP server"
  }
}
```

## Requirements

- Node.js and npm installed
- Python 3.8+
- MCP Registry CLI (`./mcp` script)

## Troubleshooting

### npm not found
```bash
# Install Node.js and npm first
brew install node  # macOS
# or
apt install nodejs npm  # Ubuntu
```

### Binary not found after installation
```bash
# Check npm global bin directory
npm config get prefix
# Add to PATH if needed
export PATH="$(npm config get prefix)/bin:$PATH"
```

### Permission errors
```bash
# Fix npm permissions (recommended)
npm config set prefix '~/.npm-global'
export PATH="~/.npm-global/bin:$PATH"
```