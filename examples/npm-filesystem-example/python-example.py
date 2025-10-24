#!/usr/bin/env python3
"""
Python example showing programmatic use of NPM MCP servers.

This example demonstrates how to:
1. Add an npm MCP server programmatically
2. Discover its capabilities
3. Generate a mock server
4. Inspect the configuration
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_registry import ServerManager, ServerSource


def main():
    print("🐍 Python NPM MCP Server Example")
    print("=" * 40)
    print()
    
    # Initialize the server manager
    manager = ServerManager()
    
    print("📦 Step 1: Adding npm MCP server programmatically...")
    
    # Add the filesystem server
    server_id = manager.add_server(
        server_id="filesystem-python",
        name="filesystem-python",
        source="@modelcontextprotocol/server-filesystem",
        source_type="npm",
        description="Filesystem MCP server added via Python",
        category="Storage"
    )
    
    print(f"✅ Added server: {server_id}")
    print()
    
    print("🔍 Step 2: Discovering server capabilities...")
    discovery_result = manager.discover_server("filesystem-python")
    
    if discovery_result:
        print(f"✅ Discovered {len(discovery_result.tools)} tools:")
        for tool in discovery_result.tools[:5]:  # Show first 5 tools
            print(f"   • {tool.name}: {tool.description[:60]}...")
        if len(discovery_result.tools) > 5:
            print(f"   ... and {len(discovery_result.tools) - 5} more tools")
    print()
    
    print("🏗️  Step 3: Generating mock server...")
    mock_path = manager.generate_mock("filesystem-python")
    
    if mock_path:
        print(f"✅ Mock server generated at: {mock_path}")
    print()
    
    print("📋 Step 4: Inspecting server configuration...")
    config = manager.get_server("filesystem-python")
    
    if config:
        print(f"Server ID: {config.id}")
        print(f"Package: {config.source.package_name}")
        print(f"Version: {config.source.package_version}")
        print(f"Binary: {config.source.binary_name}")
        print(f"Binary Path: {config.source.binary_path}")
        print(f"Category: {config.metadata.category}")
        print(f"Provider: {config.metadata.provider}")
    print()
    
    print("📊 Step 5: Listing all servers...")
    servers = manager.list_servers()
    print(f"Total servers: {len(servers)}")
    
    npm_servers = [s for s in servers if s['type'] == 'npm']
    print(f"NPM servers: {len(npm_servers)}")
    
    for server in npm_servers:
        print(f"   • {server['name']} ({server['id']})")
    print()
    
    print("✅ Python example completed successfully!")
    print()
    print("🧪 Next steps:")
    print("   - Run: python examples/npm-filesystem-example/python-example.py")
    print("   - Remove: manager.remove_server('filesystem-python')")


if __name__ == "__main__":
    main()