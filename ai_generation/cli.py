#!/usr/bin/env python3
"""
MCP Generator - Main orchestrator for generating mock MCP servers and evaluations.

This is the primary CLI tool for the MCP CI/CD automation platform. It performs
end-to-end generation of mock servers and test suites from real MCP servers.

Workflow:
1. **Discovery**: Uses MCP Inspector CLI to discover server capabilities
2. **Mock Generation**: Creates AI-powered mock server with realistic responses
3. **Evaluation Generation**: Creates comprehensive test suites
4. **Output**: Produces ready-to-use mock server and evaluation files

Usage:
    # Basic generation
    uv run python -m ai_generation.cli --server mcp_servers/calculator/server.py
    
    # With caching for faster development
    uv run python -m ai_generation.cli --server server.py --cache
    
    # Custom output location
    uv run python -m ai_generation.cli --server server.py --output-dir custom_output
    
    # Clear cache and regenerate
    uv run python -m ai_generation.cli --server server.py --clear-cache

Generated Files:
    output_dir/server_name/
    ├── discovery.json      # Raw discovery data from MCP Inspector
    ├── server.py           # Mock MCP server implementation
    ├── tools.py            # Mock tool implementations
    └── evaluations.json    # Test suite for validation

Dependencies:
    - Node.js + npx (for MCP Inspector)
    - Claude CLI (for AI generation)
    - uv or python (for running servers)

Cache Control:
    Caching is DISABLED by default during development. Enable with --cache flag
    for CI/production environments where performance matters more than freshness.
"""

import argparse
import json
import sys
from pathlib import Path

from mcp_registry import (
    MCPRegistryError,
    ServerConfig,
    ServerManager,
    ServerNotFoundError,
    ServerSource,
    handle_error,
)

from .ai_service import test_claude_cli
from .discovery import DependencyError, DiscoveryEngine, DiscoveryError, Transport
from .discovery_models import DiscoveryResult
from .evals_generator import generate_ai_test_cases
from .server_generator import generate_ai_mock_server


def extract_server_name(server_path: str) -> str:
    """
    Extract a clean server name from the server path for use as output directory.
    
    Handles common MCP server naming patterns:
    - mcp_servers/calculator/server.py → "calculator"
    - my_server.py → "my"
    - server.py → parent directory name or "mcp"
    
    Args:
        server_path (str): Path to the MCP server file
        
    Returns:
        str: Clean server name suitable for directory naming
        
    Examples:
        extract_server_name("mcp_servers/calculator/server.py") → "calculator"
        extract_server_name("my_awesome_server.py") → "my_awesome"
        extract_server_name("./server.py") → current directory name
    """
    path = Path(server_path)
    
    # Check if it's in the mcp_servers directory structure
    # e.g., mcp_servers/calculator/server.py -> calculator
    parts = path.parts
    if len(parts) >= 3 and parts[-3] == "mcp_servers" and parts[-1] == "server.py":
        return parts[-2]  # Return the directory name (e.g., "calculator")
    
    # Otherwise, extract from filename
    # Remove common suffixes and clean up
    filename = path.stem
    for suffix in ["_mcp_server", "_server", "server"]:
        filename = filename.replace(suffix, "")
    
    # If we end up with an empty string, use the parent directory name or "mcp"
    if not filename:
        if path.parent.name and path.parent.name != ".":
            return path.parent.name
        return "mcp"
    
    return filename




def generate_evaluations(discovery_data: DiscoveryResult, output_dir: Path):
    """
    Generate AI-powered evaluation test cases for discovered tools.
    
    Creates comprehensive test suites that can validate both real and mock
    MCP servers. The evaluations include positive tests, negative tests,
    edge cases, and error conditions.
    
    Args:
        discovery_data (Dict[str, Any]): Discovery results containing tools info
        output_dir (Path): Directory to save evaluations.json file
        
    Returns:
        Path: Path to the saved evaluations.json file
        
    Generated Test Types:
        - Valid input tests with expected outputs
        - Invalid input tests (type errors, missing params)
        - Edge cases (boundary values, empty inputs)
        - Error conditions (malformed requests)
        
    Usage:
        The generated evaluations.json can be run with:
        uv run python -m ai_generation.evaluation_runner \
            --evaluations output/evaluations.json \
            --mock-server output/server.py
    """
    print(f"📝 Generating evaluations...")
    
    tools = [tool.model_dump() for tool in discovery_data.tools]  # Convert to dict for AI generation
    
    # Generate AI test cases
    ai_test_cases = generate_ai_test_cases(tools)
    
    # Wrap in evaluation structure
    evaluations = {
        "server_info": {
            "source": discovery_data.server_path,
            "generated_at": discovery_data.metadata.discovered_at.isoformat(),
            "tools_count": discovery_data.tool_count
        },
        "evaluations": ai_test_cases
    }
    
    # Write to file
    eval_path = output_dir / "evaluations.json"
    with open(eval_path, "w") as f:
        json.dump(evaluations, f, indent=2)
    
    total_tests = sum(len(t.get("test_cases", [])) for t in evaluations["evaluations"])
    print(f"✅ Generated {total_tests} AI test cases for {discovery_data.tool_count} tools")
    return eval_path


def main():
    """
    Main CLI entry point for the MCP Generator.
    
    Supports unified server management for both local and remote MCP servers.
    """
    parser = argparse.ArgumentParser(
        description="Generate AI-powered mock MCP server and evaluations from local or remote MCP servers",
        epilog="""Examples:
  # Local MCP server generation
  %(prog)s local --server mcp_servers/calculator/server.py
  
  # Unified server management
  %(prog)s server list
  %(prog)s server add microsoft-learn --type remote --url "https://learn.microsoft.com/api/mcp"
  %(prog)s server add calculator --type local --path "mcp_servers/calculator/server.py"
  %(prog)s server discover-all
  %(prog)s server generate-all
  %(prog)s server status microsoft-learn
  %(prog)s server update-templates
  
  # Auto-discovery and migration (NEW!)
  %(prog)s server auto-discover-local mcp_servers --dry-run
  %(prog)s server auto-discover-local mcp_servers
  %(prog)s server migrate-local mcp_servers --discover --generate
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Local server generation (existing functionality)
    local_parser = subparsers.add_parser('local', help='Generate mock server from local MCP server')
    local_parser.add_argument(
        "--server", 
        required=True, 
        help="Path to local MCP server"
    )
    local_parser.add_argument(
        "--output-dir", 
        default="generated", 
        help="Base output directory for generated files"
    )
    local_parser.add_argument(
        "--name", 
        help="Name for the server (auto-detected if not provided)"
    )
    local_parser.add_argument(
        "--transport",
        default=Transport.AUTO,
        choices=[Transport.AUTO, Transport.STDIO, Transport.HTTP, Transport.SSE],
        help="Transport type for the MCP server (default: auto-detect)"
    )
    local_parser.add_argument(
        "--cache",
        action="store_true",
        help="Enable discovery caching (recommended for CI/production)"
    )
    local_parser.add_argument(
        "--cache-ttl",
        type=int,
        default=900,
        help="Cache TTL in seconds (default: 900 = 15 minutes)"
    )
    local_parser.add_argument(
        "--cache-dir",
        default=".mcp-ci/cache",
        help="Directory for cache storage (default: .mcp-ci/cache)"
    )
    local_parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cache before running discovery"
    )
    
    # Unified server management
    server_parser = subparsers.add_parser('server', help='Manage MCP servers (unified)')
    server_subparsers = server_parser.add_subparsers(dest='server_command', help='Server management commands')
    
    # server list
    server_subparsers.add_parser('list', help='List all servers')
    
    # server add
    add_parser = server_subparsers.add_parser('add', help='Add a new server')
    add_parser.add_argument('server_id', help='Unique identifier for the server')
    add_parser.add_argument('--name', required=True, help='Server name')
    add_parser.add_argument('--type', required=True, choices=['local', 'remote'], help='Server type')
    add_parser.add_argument('--path', help='Path to local server file')
    add_parser.add_argument('--url', help='URL to remote server')
    add_parser.add_argument('--transport', default='stdio', help='Transport type')
    add_parser.add_argument('--description', help='Server description')
    add_parser.add_argument('--category', default='General', help='Server category')
    add_parser.add_argument('--provider', help='Server provider')
    add_parser.add_argument('--auth-required', action='store_true', help='Server requires authentication')
    add_parser.add_argument('--auth-type', help='Authentication type (OAuth, API Key, etc.)')
    
    # server discover
    discover_parser = server_subparsers.add_parser('discover', help='Discover server capabilities')
    discover_parser.add_argument('server_id', help='Server ID to discover')
    
    # server discover-all
    discover_all_parser = server_subparsers.add_parser('discover-all', help='Discover all servers')
    discover_all_parser.add_argument('--type', choices=['local', 'remote'], help='Only discover servers of this type')
    discover_all_parser.add_argument('--auth-required', action='store_true', help='Only discover servers requiring authentication')
    
    # server generate
    generate_parser = server_subparsers.add_parser('generate', help='Generate mock server')
    generate_parser.add_argument('server_id', help='Server ID to generate mock for')
    
    # server generate-all
    generate_all_parser = server_subparsers.add_parser('generate-all', help='Generate mocks for all servers')
    generate_all_parser.add_argument('--type', choices=['local', 'remote'], help='Only generate for servers of this type')
    generate_all_parser.add_argument('--auth-required', action='store_true', help='Only generate for servers requiring authentication')
    
    # server status
    status_parser = server_subparsers.add_parser('status', help='Get server status')
    status_parser.add_argument('server_id', help='Server ID to get status for')
    
    # server remove
    remove_parser = server_subparsers.add_parser('remove', help='Remove server definition')
    remove_parser.add_argument('server_id', help='Server ID to remove')
    
    # server update-templates
    server_subparsers.add_parser('update-templates', help='Update templates from data models')
    
    # server auto-discover-local
    auto_discover_parser = server_subparsers.add_parser('auto-discover-local', help='Auto-discover and add all local servers')
    auto_discover_parser.add_argument('servers_dir', help='Directory containing MCP servers (e.g., mcp_servers, servers, ./local-mcp)')
    auto_discover_parser.add_argument('--dry-run', action='store_true', help='Show what would be added without actually adding')
    
    # server migrate-local
    migrate_parser = server_subparsers.add_parser('migrate-local', help='Migrate all local servers to unified system')
    migrate_parser.add_argument('servers_dir', help='Directory containing MCP servers (e.g., mcp_servers, servers, ./local-mcp)')
    migrate_parser.add_argument('--discover', action='store_true', help='Run discovery on all servers after adding')
    migrate_parser.add_argument('--generate', action='store_true', help='Generate mock servers for all servers after discovery')
    
    args = parser.parse_args()
    
    if args.command == 'local':
        handle_local_command(args)
    elif args.command == 'server':
        handle_server_command(args)
    else:
        parser.print_help()


def handle_local_command(args):
    """Handle local server generation (existing functionality)."""
    
    # Check Claude CLI availability (required for AI generation)
    if not test_claude_cli():
        print("❌ Claude CLI not found or not working.")
        print("   Please install and configure Claude CLI:")
        print("   https://docs.anthropic.com/claude/docs/claude-cli")
        print("   Ensure OPENAI_API_KEY environment variable is set.")
        sys.exit(1)
    print("✅ Claude CLI available - AI generation ready")
    
    # Determine server name for output directory
    if args.name:
        server_name = args.name
        print(f"📦 Using custom server name: {server_name}")
    else:
        server_name = extract_server_name(args.server)
        print(f"📦 Auto-detected server name: {server_name}")
    
    # Create output directory
    output_dir = Path(args.output_dir) / server_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize discovery engine with custom cache settings
        engine = DiscoveryEngine(cache_dir=args.cache_dir)
        engine.cache_ttl = args.cache_ttl
        
        # Clear cache if requested (useful for debugging or fresh starts)
        if args.clear_cache:
            engine.clear_cache()
            print("🧹 Cache cleared - will perform fresh discovery")
        
        # Discover MCP server capabilities using Inspector CLI
        # Note: Caching is disabled by default during prototyping phase
        # Enable with --cache flag for CI environments or production use
        if args.cache:
            if args.cache_ttl != 900:
                print(f"📦 Cache enabled with custom TTL: {args.cache_ttl}s")
            else:
                print(f"📦 Cache enabled with default TTL: {args.cache_ttl}s")
        
        discovery_data = engine.discover(
            args.server,
            transport=args.transport,
            use_cache=args.cache
        )
        
        # Save discovery data using the model's save method
        discovery_path = discovery_data.save(output_dir / "discovery.json")
        
        # Generate mock server with server.py + tools.py structure  
        # Convert to dict format for AI generation (backward compatibility)
        generate_ai_mock_server(discovery_data.model_dump(), output_dir)
        
        # Generate evaluations
        eval_path = generate_evaluations(discovery_data, output_dir)
        
        print(f"\n✨ Generation complete for '{server_name}'!")
        print(f"\n📁 Generated Files:")
        print(f"   📋 Output directory: {output_dir}")
        print(f"   🔍 Discovery data: {discovery_path}")
        print(f"   🤖 Mock server: {output_dir}/server.py")
        print(f"   🛠️  Tools implementation: {output_dir}/tools.py")
        print(f"   🧪 Evaluations: {eval_path}")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Test mock server:")
        print(f"      uv run python {output_dir}/server.py")
        print(f"   2. Run evaluations:")
        print(f"      uv run python -m ai_generation.evaluation_runner \\")
        print(f"          --evaluations {eval_path} \\")
        print(f"          --mock-server {output_dir}/server.py")
        print(f"   3. Compare with real server (optional):")
        print(f"      # Test real server with same evaluations for comparison")
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        
        # Provide specific guidance for common error types
        if isinstance(e, DependencyError):
            print("\n💡 Dependency Issue:")
            print("   - Ensure Node.js and npx are installed")
            print("   - Try: npm install -g npx")
        elif isinstance(e, DiscoveryError):
            print("\n💡 Discovery Issue:")
            print("   - Check that the server file exists and is executable")
            print("   - Try running the server manually first")
            print(f"   - Use --transport flag to specify transport type")
        else:
            print("\n💡 Unexpected Error:")
            print("   - Check that Claude CLI is properly configured")
            print("   - Ensure OPENAI_API_KEY environment variable is set")
            print("   - Try running with --clear-cache flag")
            import traceback
            traceback.print_exc()
        
        sys.exit(1)


class BaseCommand:
    """Base class for CLI commands."""
    
    def __init__(self, manager: 'ServerManager'):
        self.manager = manager
    
    def execute(self, args) -> None:
        """Execute the command with given arguments."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def _get_filter_args(self, args):
        """Extract common filter arguments."""
        return {
            'server_type': getattr(args, 'type', None),
            'auth_required': getattr(args, 'auth_required', None)
        }


class ListCommand(BaseCommand):
    """Handle server list command."""
    
    def execute(self, args) -> None:
        servers = self.manager.list_servers()
        if not servers:
            print("📋 No servers defined")
            return
        
        print("📋 MCP Servers:")
        print(f"{'ID':<20} {'Name':<30} {'Type':<8} {'Status':<10} {'Auth':<8} {'Category':<15}")
        print("-" * 95)
        for server in servers:
            auth_status = "Yes" if server.get('auth_required') else "No"
            print(f"{server['id']:<20} {server['name']:<30} {server['type']:<8} {server['status']:<10} {auth_status:<8} {server['category']:<15}")


class AddCommand(BaseCommand):
    """Handle server add command."""
    
    def execute(self, args) -> None:
        # Validate required arguments
        if args.type == 'local' and not args.path:
            print("❌ --path is required for local servers")
            sys.exit(1)
        elif args.type == 'remote' and not args.url:
            print("❌ --url is required for remote servers")
            sys.exit(1)
        
        # Create server source
        if args.type == 'local':
            source = ServerSource(type='local', path=args.path, transport=args.transport)
        else:
            source = ServerSource(type='remote', url=args.url, transport=args.transport)
        
        self.manager.add_server(
            server_id=args.server_id,
            name=args.name,
            source=source,
            description=args.description,
            category=args.category,
            provider=args.provider,
            auth_required=args.auth_required,
            auth_type=args.auth_type
        )


class DiscoverCommand(BaseCommand):
    """Handle server discover command."""
    
    def execute(self, args) -> None:
        try:
            result = self.manager.discover_server(args.server_id)
            if result:
                print(f"✅ Discovery successful for {args.server_id}")
            else:
                # Warning case (discovery disabled) - don't exit
                pass
        except MCPRegistryError as e:
            handle_error(e, "server discovery", exit_on_error=True)


class DiscoverAllCommand(BaseCommand):
    """Handle server discover-all command."""
    
    def execute(self, args) -> None:
        filters = self._get_filter_args(args)
        results = self.manager.discover_all(**filters)
        print(f"✅ Discovery completed: {len(results)} servers successful")


class GenerateCommand(BaseCommand):
    """Handle server generate command."""
    
    def execute(self, args) -> None:
        result = self.manager.generate_mock(args.server_id)
        if result:
            print(f"✅ Mock generation successful for {args.server_id}")
        else:
            print(f"❌ Mock generation failed for {args.server_id}")
            sys.exit(1)


class GenerateAllCommand(BaseCommand):
    """Handle server generate-all command."""
    
    def execute(self, args) -> None:
        filters = self._get_filter_args(args)
        results = self.manager.generate_all(**filters)
        print(f"✅ Generation completed: {len(results)} servers successful")


class StatusCommand(BaseCommand):
    """Handle server status command."""
    
    def execute(self, args) -> None:
        status = self.manager.get_server_status(args.server_id)
        if "error" in status:
            print(f"❌ {status['error']}")
            sys.exit(1)
        
        print(f"📊 Server Status: {status['name']}")
        print(f"   ID: {status['id']}")
        print(f"   Type: {status['type']}")
        print(f"   Source: {status['source']}")
        print(f"   Transport: {status['transport']}")
        print(f"   Auth Required: {status['auth_required']}")
        print(f"   Category: {status['category']}")
        print(f"   Provider: {status['provider']}")
        print(f"   Discovery: {'Enabled' if status['discovery']['enabled'] else 'Disabled'}")
        print(f"   Last Discovered: {status['discovery']['last_discovered']}")
        print(f"   Has Discovery Results: {status['discovery']['has_results']}")
        print(f"   Generation: {'Enabled' if status['generation']['enabled'] else 'Disabled'}")
        print(f"   Last Generated: {status['generation']['last_generated']}")
        print(f"   Generated Path: {status['generation']['output_dir']}")
        print(f"   Has Generated Files: {status['generation']['has_files']}")


class RemoveCommand(BaseCommand):
    """Handle server remove command."""
    
    def execute(self, args) -> None:
        success = self.manager.remove_server(args.server_id)
        if not success:
            sys.exit(1)


class UpdateTemplatesCommand(BaseCommand):
    """Handle server update-templates command."""
    
    def execute(self, args) -> None:
        self.manager.update_templates()


class AutoDiscoverLocalCommand(BaseCommand):
    """Handle server auto-discover-local command."""
    
    def execute(self, args) -> None:
        servers_dir = args.servers_dir
        dry_run = getattr(args, 'dry_run', False)
        
        added_servers = self.manager.auto_discover_and_add_local_servers(
            mcp_servers_dir=servers_dir,
            dry_run=dry_run
        )
        
        if dry_run:
            print(f"\n🔍 Dry run complete - would add {len(added_servers)} servers")
            print("   Run without --dry-run to actually add the servers")
        else:
            print(f"\n✅ Auto-discovery complete - added {len(added_servers)} servers")
            if added_servers:
                print("   Next steps:")
                print("   1. Run discovery: python -m ai_generation.cli server discover-all --type local")
                print("   2. Generate mocks: python -m ai_generation.cli server generate-all --type local")


class MigrateLocalCommand(BaseCommand):
    """Handle server migrate-local command."""
    
    def execute(self, args) -> None:
        servers_dir = args.servers_dir
        run_discovery = getattr(args, 'discover', False)
        run_generation = getattr(args, 'generate', False)
        
        print("🚀 Starting local server migration...")
        
        # Step 1: Auto-discover and add servers
        print("\n📋 Step 1: Auto-discovering local servers...")
        added_servers = self.manager.auto_discover_and_add_local_servers(
            mcp_servers_dir=servers_dir,
            dry_run=False
        )
        
        if not added_servers:
            print("❌ No servers found to migrate")
            return
        
        # Step 2: Run discovery if requested
        if run_discovery:
            print(f"\n🔍 Step 2: Running discovery on {len(added_servers)} servers...")
            discovery_results = self.manager.discover_all(server_type='local')
            print(f"✅ Discovery completed: {len(discovery_results)}/{len(added_servers)} servers successful")
        else:
            print(f"\n⏭️  Step 2: Skipping discovery (use --discover to enable)")
        
        # Step 3: Generate mocks if requested
        if run_generation:
            print(f"\n🏗️  Step 3: Generating mock servers...")
            generation_results = self.manager.generate_all(server_type='local')
            print(f"✅ Generation completed: {len(generation_results)}/{len(added_servers)} servers successful")
        else:
            print(f"\n⏭️  Step 3: Skipping generation (use --generate to enable)")
        
        print(f"\n🎉 Migration complete!")
        print(f"   Added: {len(added_servers)} servers")
        print(f"   Discovery: {'✅ Completed' if run_discovery else '⏭️  Skipped'}")
        print(f"   Generation: {'✅ Completed' if run_generation else '⏭️  Skipped'}")
        
        if not run_discovery or not run_generation:
            print(f"\n💡 To complete the migration:")
            if not run_discovery:
                print(f"   python -m ai_generation.cli server discover-all --type local")
            if not run_generation:
                print(f"   python -m ai_generation.cli server generate-all --type local")


class ServerCommandHandler:
    """Centralized handler for server commands using command pattern."""
    
    def __init__(self, manager: 'ServerManager'):
        self.manager = manager
        self.commands = {
            'list': ListCommand(manager),
            'add': AddCommand(manager),
            'discover': DiscoverCommand(manager),
            'discover-all': DiscoverAllCommand(manager),
            'generate': GenerateCommand(manager),
            'generate-all': GenerateAllCommand(manager),
            'status': StatusCommand(manager),
            'remove': RemoveCommand(manager),
            'update-templates': UpdateTemplatesCommand(manager),
            'auto-discover-local': AutoDiscoverLocalCommand(manager),
            'migrate-local': MigrateLocalCommand(manager),
        }
    
    def handle(self, args) -> None:
        """Handle server command using command pattern."""
        command_name = args.server_command
        
        if command_name not in self.commands:
            print(f"❌ Unknown server command: {command_name}")
            sys.exit(1)
        
        self.commands[command_name].execute(args)


def handle_server_command(args):
    """Handle unified server management commands using command pattern."""
    manager = ServerManager()
    handler = ServerCommandHandler(manager)
    handler.handle(args)


if __name__ == "__main__":
    """
    CLI Entry Point
    
    This module can be run directly or via python -m:
        python ai_generation/cli.py --server server.py
        python -m ai_generation.cli --server server.py
    
    For comprehensive help:
        python -m ai_generation.cli --help
    """
    main()