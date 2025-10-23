#!/usr/bin/env python3
"""
MCP Registry CLI - npm/docker-style registry management for MCP servers.

A unified CLI tool for managing MCP servers in CI/CD environments, providing
npm/docker-like commands for server management, discovery, and testing.

Usage:
    # Server Management
    mcp add calculator mcp_servers/calculator/server.py
    mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
    mcp list
    mcp list --category Utilities
    mcp search "math calculator"
    mcp inspect calculator
    mcp remove old-server

    # Operations  
    mcp discover calculator
    mcp discover --all
    mcp generate calculator --force
    mcp test calculator
    
    # CI/CD Workflows
    mcp sync                    # Discover all + regenerate if changed
    mcp status                  # Registry health overview
    mcp publish ./my-server.py  # Easy server addition
    
    # Git-based servers
    mcp git add gleanwork https://github.com/gleanwork/mcp-server.git
    mcp git update gleanwork
    mcp git status gleanwork
    mcp git discover https://github.com/gleanwork/mcp-server.git

Examples:
    # Add a local server
    mcp add calculator mcp_servers/calculator/server.py --category Utilities
    
    # Add a remote server
    mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
    
    # Add a git-based server
    mcp git add gleanwork https://github.com/gleanwork/mcp-server.git --category Development
    
    # Run full CI/CD sync
    mcp sync && mcp test --all
    
    # Check registry health
    mcp status
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from ai_generation.discovery import Transport
from mcp_registry import ServerManager, ServerSource, handle_error, handle_warning
from mcp_registry.git_cli import GitCLI


class MCPRegistryCLI:
    """Unified CLI for MCP server registry management."""
    
    def __init__(self):
        self.manager = ServerManager()
        self.git_cli = GitCLI(self.manager)
    
    def add_server(self, name: str, source: str, category: Optional[str] = None, 
                   description: Optional[str] = None, transport: str = "stdio"):
        """Add a server to the registry (like npm install)."""
        try:
            # Determine if source is local or remote
            if source.startswith(("http://", "https://")):
                server_source = ServerSource(type="remote", url=source, transport=transport)
                provider = "Remote"
            else:
                server_source = ServerSource(type="local", path=source, transport=transport)
                provider = "Local"
            
            # Add to registry with proper parameters
            success = self.manager.add_server(
                server_id=name,
                name=name,
                source=server_source,
                description=description or f"{name} MCP server",
                category=category or "General",
                provider=provider
            )
            if success:
                print(f"✅ Added server '{name}' to registry")
                print(f"   Source: {source}")
                print(f"   Category: {category or 'General'}")
                print(f"   Provider: {provider}")
            else:
                print(f"❌ Failed to add server '{name}'")
                
        except Exception as e:
            handle_error(f"Failed to add server: {e}")
    
    def remove_server(self, name: str):
        """Remove a server from the registry (like npm uninstall)."""
        try:
            success = self.manager.remove_server(name)
            if success:
                print(f"✅ Removed server '{name}' from registry")
            else:
                print(f"❌ Server '{name}' not found in registry")
        except Exception as e:
            handle_error(f"Failed to remove server: {e}")
    
    def list_servers(self, category: Optional[str] = None, format_type: str = "table"):
        """List all servers in the registry (like docker ps)."""
        try:
            servers = self.manager.list_servers()
            
            if category:
                servers = [s for s in servers if s["category"] == category]
            
            if not servers:
                category_msg = f" in category '{category}'" if category else ""
                print(f"No servers found{category_msg}")
                return
            
            if format_type == "json":
                print(json.dumps(servers, indent=2))
            else:
                # Table format (default)
                print(f"\n{'NAME':<20} {'CATEGORY':<15} {'PROVIDER':<10} {'STATUS':<10} {'LAST DISCOVERED'}")
                print("─" * 85)
                
                for server in servers:
                    # Determine status based on discovery/generation state
                    if server["last_discovered"] and server["last_generated"]:
                        status = "✅ Ready"
                    elif server["last_discovered"]:
                        status = "🔍 Discovered"
                    else:
                        status = "⭕ New"
                    
                    last_discovered = server["last_discovered"]
                    if last_discovered:
                        last_discovered = str(last_discovered)
                        if len(last_discovered) > 19:
                            last_discovered = last_discovered[:16] + "..."
                    else:
                        last_discovered = "Never"
                    provider = server['provider'] or "Unknown"
                    print(f"{server['id']:<20} {server['category']:<15} {provider:<10} {status:<10} {last_discovered}")
                
                print(f"\nTotal: {len(servers)} servers")
                
        except Exception as e:
            handle_error(f"Failed to list servers: {e}")
    
    def search_servers(self, query: str):
        """Search servers by name or description."""
        try:
            servers = self.manager.list_servers()
            query_lower = query.lower()
            
            matches = [
                s for s in servers 
                if query_lower in s["id"].lower() or 
                   query_lower in s["name"].lower() or
                   query_lower in s["category"].lower()
            ]
            
            if not matches:
                print(f"No servers found matching '{query}'")
                return
            
            print(f"\n🔍 Found {len(matches)} server(s) matching '{query}':")
            print(f"{'NAME':<20} {'CATEGORY':<15} {'PROVIDER':<10}")
            print("─" * 50)
            
            for server in matches:
                print(f"{server['id']:<20} {server['category']:<15} {server['provider']:<10}")
                
        except Exception as e:
            handle_error(f"Failed to search servers: {e}")
    
    def inspect_server(self, name: str):
        """Show detailed information about a server (like docker inspect)."""
        try:
            server = self.manager.get_server(name)
            if not server:
                print(f"❌ Server '{name}' not found")
                return
            
            print(f"\n📋 Server: {server.id}")
            print("=" * 50)
            print(f"Name: {server.id}")
            print(f"Description: {server.metadata.description}")
            print(f"Category: {server.metadata.category}")
            print(f"Provider: {server.metadata.provider}")
            print(f"Version: {server.metadata.version}")
            print(f"Created: {server.metadata.created_at}")
            print(f"Updated: {server.metadata.updated_at}")
            
            print(f"\n📍 Source:")
            print(f"Type: {server.source.type}")
            if server.source.type == "local":
                print(f"Path: {server.source.path}")
            elif server.source.type == "git":
                print(f"Git URL: {server.source.git_url}")
                print(f"Branch: {server.source.git_branch}")
                print(f"Commit: {server.source.git_commit}")
                print(f"Clone Path: {server.source.clone_path}")
                if server.source.git_subpath:
                    print(f"Subpath: {server.source.git_subpath}")
            else:
                print(f"URL: {server.source.url}")
            print(f"Transport: {server.source.transport}")
            
            print(f"\n🔍 Runtime Discovery:")
            print(f"Enabled: {server.discovery.enabled}")
            print(f"Last discovered: {server.discovery.last_discovered or 'Never'}")
            print(f"Cache TTL: {server.discovery.cache_ttl}s")
            
            # Show documentation discovery for git servers
            if server.source.type == "git":
                print(f"\n📚 Documentation Discovery:")
                print(f"Enabled: {server.doc_discovery.enabled}")
                print(f"Last discovered: {server.doc_discovery.last_doc_discovered or 'Never'}")
            
            print(f"\n⚙️ Generation:")
            print(f"Enabled: {server.generation.enabled}")
            print(f"Last generated: {server.generation.last_generated or 'Never'}")
            print(f"Output directory: {server.generation.output_dir}")
            
            # Show runtime discovery data if available
            discovery_file = Path(self.manager.base_dir) / "servers" / name / "discovery.json"
            if discovery_file.exists():
                with open(discovery_file) as f:
                    discovery = json.load(f)
                    tools = discovery.get("tools", [])
                    print(f"\n🛠️ Runtime Tools ({len(tools)}):")
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"  • {tool['name']}: {tool['description'][:60]}...")
                    if len(tools) > 5:
                        print(f"  ... and {len(tools) - 5} more tools")
            
            # Show documentation discovery data if available (git servers only)
            if server.source.type == "git":
                doc_discovery_file = Path(self.manager.base_dir) / "servers" / name / "doc_discovery.json"
                if doc_discovery_file.exists():
                    with open(doc_discovery_file) as f:
                        doc_discovery = json.load(f)
                        doc_tools = doc_discovery.get("tools", [])
                        doc_resources = doc_discovery.get("resources", [])
                        print(f"\n📋 Documentation Tools ({len(doc_tools)}):")
                        for tool in doc_tools[:5]:  # Show first 5 tools
                            confidence = tool.get("confidence", 1.0)
                            conf_indicator = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                            print(f"  {conf_indicator} {tool['name']}: {tool['description'][:60]}...")
                        if len(doc_tools) > 5:
                            print(f"  ... and {len(doc_tools) - 5} more tools")
                        
                        if doc_resources:
                            print(f"\n📁 Documentation Resources ({len(doc_resources)}):")
                            for resource in doc_resources[:3]:  # Show first 3 resources
                                confidence = resource.get("confidence", 1.0)
                                conf_indicator = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                                print(f"  {conf_indicator} {resource['name']}: {resource['description'][:60]}...")
                            if len(doc_resources) > 3:
                                print(f"  ... and {len(doc_resources) - 3} more resources")
            
        except Exception as e:
            handle_error(f"Failed to inspect server: {e}")
    
    def discover_servers(self, name: Optional[str] = None, all_servers: bool = False):
        """Run discovery on server(s) (like docker build)."""
        try:
            if all_servers:
                servers = self.manager.list_servers()
                print(f"🔍 Discovering {len(servers)} servers...")
                
                for server in servers:
                    print(f"\n📡 Discovering {server['id']}...")
                    success = self.manager.discover_server(server['id'])
                    if success:
                        print(f"✅ Discovery completed for {server['id']}")
                    else:
                        print(f"❌ Discovery failed for {server['id']}")
                        
            elif name:
                print(f"📡 Discovering server '{name}'...")
                success = self.manager.discover_server(name)
                if success:
                    print(f"✅ Discovery completed for '{name}'")
                else:
                    print(f"❌ Discovery failed for '{name}'")
            else:
                print("❌ Please specify --all or a server name")
                
        except Exception as e:
            handle_error(f"Failed to discover servers: {e}")
    
    def generate_mocks(self, name: Optional[str] = None, all_servers: bool = False, force: bool = False):
        """Generate mock servers and evaluations."""
        try:
            if all_servers:
                servers = self.manager.list_servers()
                print(f"⚙️ Generating mocks for {len(servers)} servers...")
                
                for server in servers:
                    print(f"\n🔨 Generating mocks for {server['id']}...")
                    result = self.manager.generate_mock(server['id'])
                    if result:
                        print(f"✅ Generation completed for {server['id']}")
                    else:
                        print(f"❌ Generation failed for {server['id']}")
                        
            elif name:
                print(f"🔨 Generating mocks for server '{name}'...")
                result = self.manager.generate_mock(name)
                if result:
                    print(f"✅ Generation completed for '{name}'")
                else:
                    print(f"❌ Generation failed for '{name}'")
            else:
                print("❌ Please specify --all or a server name")
                
        except Exception as e:
            handle_error(f"Failed to generate mocks: {e}")
    
    def test_servers(self, name: Optional[str] = None, all_servers: bool = False):
        """Run evaluations on server(s) (like npm test)."""
        try:
            if all_servers:
                servers = self.manager.list_servers()
                print(f"🧪 Testing {len(servers)} servers...")
                
                for server in servers:
                    print(f"\n🔬 Testing {server['id']}...")
                    success = self.manager.test_server(server['id'])
                    if success:
                        print(f"✅ Tests passed for {server['id']}")
                    else:
                        print(f"❌ Tests failed for {server['id']}")
                        
            elif name:
                print(f"🔬 Testing server '{name}'...")
                success = self.manager.test_server(name)
                if success:
                    print(f"✅ Tests passed for '{name}'")
                else:
                    print(f"❌ Tests failed for '{name}'")
            else:
                print("❌ Please specify --all or a server name")
                
        except Exception as e:
            handle_error(f"Failed to test servers: {e}")
    
    def sync_registry(self):
        """Synchronize all servers: discover + regenerate if changed (like npm audit)."""
        try:
            servers = self.manager.list_servers()
            print(f"🔄 Syncing registry with {len(servers)} servers...")
            
            for server in servers:
                print(f"\n🔄 Syncing {server['id']}...")
                
                # Discover
                print(f"  📡 Running discovery...")
                discover_success = self.manager.discover_server(server['id'])
                
                if discover_success:
                    # Check if regeneration needed (this would check MD5 hashes)
                    print(f"  🔨 Checking if regeneration needed...")
                    generate_result = self.manager.generate_mock(server['id'])
                    
                    if generate_result:
                        print(f"✅ {server['id']} synchronized")
                    else:
                        print(f"⚠️ {server['id']} discovery ok, generation failed")
                else:
                    print(f"❌ {server['id']} discovery failed")
            
            print(f"\n✅ Registry sync completed")
            
        except Exception as e:
            handle_error(f"Failed to sync registry: {e}")
    
    def show_status(self):
        """Show registry health overview (like docker stats)."""
        try:
            servers = self.manager.list_servers()
            
            print("📊 MCP Registry Status")
            print("=" * 50)
            
            # Count by category
            categories = {}
            discovered = 0
            generated = 0
            
            for server in servers:
                cat = server["category"]
                categories[cat] = categories.get(cat, 0) + 1
                
                if server["last_discovered"]:
                    discovered += 1
                if server["last_generated"]:
                    generated += 1
            
            print(f"Total servers: {len(servers)}")
            print(f"Discovered: {discovered}/{len(servers)}")
            print(f"Generated: {generated}/{len(servers)}")
            
            print(f"\n📂 By Category:")
            for cat, count in sorted(categories.items()):
                print(f"  {cat}: {count}")
            
            # Show recent activity (first 5 servers)
            print(f"\n📈 Recent Servers:")
            for server in servers[:5]:
                status = "Ready" if server["last_discovered"] and server["last_generated"] else "Partial"
                print(f"  {server['id']} ({server['category']}): {status}")
            
        except Exception as e:
            handle_error(f"Failed to show status: {e}")
    
    def publish_server(self, path: str):
        """Publish a server to the registry with auto-discovery (like npm publish)."""
        try:
            # Auto-detect server name from path
            server_path = Path(path)
            if server_path.is_file():
                # Extract name from file/directory structure
                if server_path.parent.name != "." and server_path.parent.name != server_path.parent.parent.name:
                    name = server_path.parent.name
                else:
                    name = server_path.stem.replace("_server", "").replace("server", "")
            else:
                name = server_path.name
            
            print(f"📦 Publishing server '{name}' from {path}")
            
            # Add server
            self.add_server(name, str(path))
            
            # Auto-discover
            print(f"📡 Auto-discovering...")
            self.discover_servers(name)
            
            # Auto-generate
            print(f"🔨 Auto-generating mocks...")
            result = self.manager.generate_mock(name)
            if result:
                print(f"✅ Mock generation completed")
            else:
                print(f"⚠️ Mock generation failed")
            
            print(f"✅ Server '{name}' published successfully!")
            
        except Exception as e:
            handle_error(f"Failed to publish server: {e}")
    


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Registry CLI - npm/docker-style registry management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server Management Commands
    add_parser = subparsers.add_parser("add", help="Add a server to the registry")
    add_parser.add_argument("name", help="Server name")
    add_parser.add_argument("source", help="Server path or URL")
    add_parser.add_argument("--category", help="Server category")
    add_parser.add_argument("--description", help="Server description")
    add_parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse"], help="Transport protocol")
    
    remove_parser = subparsers.add_parser("remove", help="Remove a server from the registry")
    remove_parser.add_argument("name", help="Server name to remove")
    
    list_parser = subparsers.add_parser("list", help="List servers in the registry")
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    
    search_parser = subparsers.add_parser("search", help="Search servers")
    search_parser.add_argument("query", help="Search query")
    
    inspect_parser = subparsers.add_parser("inspect", help="Show detailed server information")
    inspect_parser.add_argument("name", help="Server name to inspect")
    
    # Operation Commands
    discover_parser = subparsers.add_parser("discover", help="Run discovery on server(s)")
    discover_group = discover_parser.add_mutually_exclusive_group(required=True)
    discover_group.add_argument("name", nargs="?", help="Server name to discover")
    discover_group.add_argument("--all", action="store_true", help="Discover all servers")
    
    generate_parser = subparsers.add_parser("generate", help="Generate mock servers and evaluations")
    generate_group = generate_parser.add_mutually_exclusive_group(required=True)
    generate_group.add_argument("name", nargs="?", help="Server name to generate")
    generate_group.add_argument("--all", action="store_true", help="Generate for all servers")
    generate_parser.add_argument("--force", action="store_true", help="Force regeneration even if up to date")
    
    test_parser = subparsers.add_parser("test", help="Run evaluations on server(s)")
    test_group = test_parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument("name", nargs="?", help="Server name to test")
    test_group.add_argument("--all", action="store_true", help="Test all servers")
    
    # CI/CD Commands
    subparsers.add_parser("sync", help="Sync all servers (discover + regenerate if changed)")
    subparsers.add_parser("status", help="Show registry health overview")
    
    publish_parser = subparsers.add_parser("publish", help="Publish a server with auto-discovery")
    publish_parser.add_argument("path", help="Path to server file or directory")
    
    # Git Commands (setup via GitCLI module)
    GitCLI.setup_git_subparser(subparsers)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = MCPRegistryCLI()
    
    # Route commands
    if args.command == "add":
        cli.add_server(args.name, args.source, args.category, args.description, args.transport)
    elif args.command == "remove":
        cli.remove_server(args.name)
    elif args.command == "list":
        cli.list_servers(args.category, args.format)
    elif args.command == "search":
        cli.search_servers(args.query)
    elif args.command == "inspect":
        cli.inspect_server(args.name)
    elif args.command == "discover":
        cli.discover_servers(args.name, args.all)
    elif args.command == "generate":
        cli.generate_mocks(args.name, args.all, args.force)
    elif args.command == "test":
        cli.test_servers(args.name, args.all)
    elif args.command == "sync":
        cli.sync_registry()
    elif args.command == "status":
        cli.show_status()
    elif args.command == "publish":
        cli.publish_server(args.path)
    elif args.command == "git":
        cli.git_cli.route_command(args)


if __name__ == "__main__":
    main()