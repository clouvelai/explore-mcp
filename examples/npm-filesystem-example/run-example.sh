#!/bin/bash
set -e

echo "🚀 NPM Filesystem MCP Server Example"
echo "===================================="
echo

# Move to project root
cd "$(dirname "$0")/../.."

echo "📦 Step 1: Installing npm MCP server..."
./mcp add filesystem-example @modelcontextprotocol/server-filesystem --source npm --category Storage --description "File system operations MCP server (example)"

echo
echo "🔍 Step 2: Discovering server capabilities..."
./mcp discover filesystem-example

echo
echo "🏗️  Step 3: Generating mock server..."
./mcp generate filesystem-example

echo
echo "📋 Step 4: Inspecting server details..."
./mcp inspect filesystem-example

echo
echo "📊 Step 5: Listing all servers..."
./mcp list

echo
echo "✅ Example completed successfully!"
echo
echo "📁 Generated files:"
echo "   - Configuration: mcp_registry/servers/filesystem-example/config.json"
echo "   - Discovery: mcp_registry/servers/filesystem-example/discovery.json"
echo "   - Mock server: mcp_registry/servers/filesystem-example/generated/"
echo
echo "🧪 Next steps:"
echo "   - Run tests: ./mcp test filesystem-example"
echo "   - Remove server: ./mcp remove filesystem-example"