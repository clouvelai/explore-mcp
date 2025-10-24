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

Examples:
    # Add a local server
    mcp add calculator mcp_servers/calculator/server.py --category Utilities
    
    # Add a remote server
    mcp add microsoft-docs https://learn.microsoft.com/api/mcp --category Documentation
    
    # Add an npm package (EXPLICIT --source npm REQUIRED)
    mcp add memory @modelcontextprotocol/server-memory --source npm --category Memory
    
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


class MCPRegistryCLI:
    """Unified CLI for MCP server registry management."""
    
    def __init__(self):
        self.manager = ServerManager()
    
    def add_server(self, name: str, source: str, category: Optional[str] = None, 
                   description: Optional[str] = None, transport: str = "stdio", source_type: str = "auto"):
        """Add a server to the registry (supports local, remote, and explicit npm sources)."""
        try:
            # Handle explicit source types only - no auto-detection
            source_type_param = None if source_type == "auto" else source_type
            
            success = self.manager.add_server(
                server_id=name,
                name=name,
                source=source,
                description=description or f"{name} MCP server",
                category=category or "General",
                source_type=source_type_param
            )
            
            # Manager already prints success/failure details
            pass
                
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
            elif server.source.type == "npm":
                print(f"Package: {server.source.package_name}")
                print(f"Version: {server.source.package_version or 'unknown'}")
                print(f"Binary: {server.source.binary_name}")
                print(f"Binary Path: {server.source.binary_path}")
            else:
                print(f"URL: {server.source.url}")
            print(f"Transport: {server.source.transport}")
            
            print(f"\n🔍 Discovery:")
            print(f"Enabled: {server.discovery.enabled}")
            print(f"Last discovered: {server.discovery.last_discovered or 'Never'}")
            print(f"Cache TTL: {server.discovery.cache_ttl}s")
            
            print(f"\n⚙️ Generation:")
            print(f"Enabled: {server.generation.enabled}")
            print(f"Last generated: {server.generation.last_generated or 'Never'}")
            print(f"Output directory: {server.generation.output_dir}")
            
            # Show discovery data if available
            discovery_file = Path(self.manager.base_dir) / "servers" / name / "discovery.json"
            if discovery_file.exists():
                with open(discovery_file) as f:
                    discovery = json.load(f)
                    tools = discovery.get("tools", [])
                    print(f"\n🛠️ Tools ({len(tools)}):")
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"  • {tool['name']}: {tool['description'][:60]}...")
                    if len(tools) > 5:
                        print(f"  ... and {len(tools) - 5} more tools")
            
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
    
    def run_interactive_session(self, server_id: str, capture_session: bool = False, session_name: Optional[str] = None):
        """Run an interactive session with a server, optionally capturing for better generation."""
        try:
            server = self.manager.get_server(server_id)
            if not server:
                print(f"❌ Server '{server_id}' not found in registry")
                return
            
            print(f"🚀 Starting interactive session with '{server_id}'")
            
            if capture_session:
                from datetime import datetime
                if not session_name:
                    session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create sessions directory in registry
                sessions_dir = Path(f"mcp_registry/servers/{server_id}/sessions")
                sessions_dir.mkdir(parents=True, exist_ok=True)
                
                log_file = sessions_dir / f"{session_name}.jsonl"
                print(f"📝 Capturing session to: {log_file}")
                
                # Enable MITM interceptor
                try:
                    from mcp_interceptor.mcp_interceptor import install_interceptor
                    install_interceptor(log_file=str(log_file), verbose=True)
                    print(f"🔍 MITM interceptor enabled")
                except ImportError:
                    print(f"⚠️ MITM interceptor not available - session will not be captured")
                    capture_session = False
            
            # Start interactive client
            import asyncio
            asyncio.run(self._run_client_session(server_id, server))
            
            if capture_session:
                print(f"\n✅ Session captured successfully!")
                print(f"📊 Use captured data: ./mcp generate {server_id} --use-real-sessions")
            
        except Exception as e:
            handle_error(f"Failed to run interactive session: {e}")
    
    async def _run_client_session(self, server_id: str, server: dict):
        """Run the actual client session with the server."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        print(f"🔌 Connecting to {server.source.type} server...")
        
        if server.source.type == 'npm':
            # Use npm binary
            binary_path = server.source.binary_path
            if not binary_path or not Path(binary_path).exists():
                print(f"❌ Binary not found: {binary_path}")
                return
            
            # Set up allowed directories for filesystem server
            current_dir = Path.cwd()
            server_params = StdioServerParameters(
                command=binary_path,
                args=[str(current_dir), "/private/tmp"]  # Allow current dir and tmp
            )
            
            async with stdio_client(server_params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    
                    # List available tools
                    tools = await session.list_tools()
                    print(f"\n📋 Available tools ({len(tools.tools)}):")
                    for i, tool in enumerate(tools.tools, 1):
                        print(f"  {i}. {tool.name} - {tool.description}")
                    
                    # Interactive prompt
                    print(f"\n💬 Interactive session started. Type 'help' for commands, 'quit' to exit.")
                    
                    while True:
                        try:
                            user_input = input(f"\n{server_id}> ").strip()
                            
                            if user_input.lower() in ['quit', 'exit', 'q']:
                                break
                            elif user_input.lower() == 'help':
                                print("Commands:")
                                print("  tools - List available tools")
                                print("  call <tool_name> <args> - Call a tool")
                                print("  quit - Exit session")
                                continue
                            elif user_input.lower() == 'tools':
                                for i, tool in enumerate(tools.tools, 1):
                                    print(f"  {i}. {tool.name}")
                                continue
                            elif user_input.startswith('call '):
                                # Parse call command
                                parts = user_input[5:].split(' ', 1)
                                tool_name = parts[0]
                                args = {}
                                if len(parts) > 1:
                                    try:
                                        args = json.loads(parts[1]) if parts[1].startswith('{') else {"path": parts[1]}
                                    except json.JSONDecodeError:
                                        args = {"path": parts[1]}
                                
                                # Call the tool
                                try:
                                    result = await session.call_tool(tool_name, args)
                                    print(f"✅ Result: {result}")
                                except Exception as e:
                                    print(f"❌ Error: {e}")
                            else:
                                print("Unknown command. Type 'help' for available commands.")
                                
                        except KeyboardInterrupt:
                            print("\n👋 Session interrupted")
                            break
                        except EOFError:
                            print("\n👋 Session ended")
                            break
        else:
            print(f"❌ Interactive sessions not yet supported for {server.source.type} servers")


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
    add_parser.add_argument("source", help="Server path, URL, or npm package name")
    add_parser.add_argument("--category", help="Server category")
    add_parser.add_argument("--description", help="Server description")
    add_parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse"], help="Transport protocol")
    add_parser.add_argument("--source", dest="source_type", choices=["local", "remote", "npm", "auto"], default="auto", help="Source type (explicit --source npm required for npm packages)")
    
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
    
    # Interactive Commands
    run_parser = subparsers.add_parser("run", help="Run an interactive session with a server")
    run_parser.add_argument("server_id", help="Server identifier")
    run_parser.add_argument("--capture-session", action="store_true", help="Capture real session interactions for better generation")
    run_parser.add_argument("--session-name", help="Name for the captured session (default: timestamp)")
    
    # CI/CD Commands
    subparsers.add_parser("sync", help="Sync all servers (discover + regenerate if changed)")
    subparsers.add_parser("status", help="Show registry health overview")
    
    publish_parser = subparsers.add_parser("publish", help="Publish a server with auto-discovery")
    publish_parser.add_argument("path", help="Path to server file or directory")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = MCPRegistryCLI()
    
    # Route commands
    if args.command == "add":
        cli.add_server(args.name, args.source, args.category, args.description, args.transport, args.source_type)
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
    elif args.command == "run":
        cli.run_interactive_session(args.server_id, args.capture_session, args.session_name)
    elif args.command == "sync":
        cli.sync_registry()
    elif args.command == "status":
        cli.show_status()
    elif args.command == "publish":
        cli.publish_server(args.path)


if __name__ == "__main__":
    main()