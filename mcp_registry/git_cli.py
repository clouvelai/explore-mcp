"""
Git CLI Module - Handles all git-related CLI commands.

Provides a clean separation of git commands from the main CLI.
"""

from typing import Optional

from .exceptions import handle_error
from .git_server_manager import GitServerManager


class GitCLI:
    """CLI interface for git-based MCP server operations."""
    
    def __init__(self, server_manager):
        """
        Initialize git CLI.
        
        Args:
            server_manager: Main ServerManager instance
        """
        self.git_server_manager = GitServerManager(server_manager)
    
    def add_server(self, name: str, git_url: str, branch: str = "main", 
                   category: Optional[str] = None, description: Optional[str] = None):
        """Add a git-based MCP server to the registry."""
        try:
            added_servers = self.git_server_manager.add_git_server(
                git_url=git_url,
                name=name,
                branch=branch,
                category=category or "General", 
                description=description
            )
            
            if added_servers:
                print(f"\n✅ Successfully added {len(added_servers)} server(s) from git repository:")
                for server_id in added_servers:
                    print(f"   • {server_id}")
            else:
                print(f"❌ No servers were added from {git_url}")
                
        except Exception as e:
            handle_error(f"Failed to add git server: {e}")
    
    def update_server(self, name: str):
        """Update a git-based server by pulling latest changes."""
        try:
            success = self.git_server_manager.update_git_server(name)
            if not success:
                print(f"❌ Failed to update git server '{name}'")
                
        except Exception as e:
            handle_error(f"Failed to update git server: {e}")
    
    def show_status(self, name: str):
        """Show git status for a server."""
        try:
            status = self.git_server_manager.get_git_status(name)
            
            if "error" in status:
                print(f"❌ {status['error']}")
                return
            
            print(f"\n📋 Git Status: {name}")
            print("=" * 50)
            print(f"Repository: {status['git_url']}")
            print(f"Branch: {status['branch']}")
            print(f"Current Commit: {status['current_commit'][:8] if status['current_commit'] else 'Unknown'}")
            print(f"Clone Path: {status['clone_path']}")
            print(f"Subpath: {status['subpath'] or 'Root'}")
            print(f"Clone Exists: {'✅' if status['clone_exists'] else '❌'}")
            
            if "latest_commit" in status:
                print(f"Latest Commit: {status['latest_commit'][:8] if status['latest_commit'] else 'Unknown'}")
                up_to_date = status.get('up_to_date', False)
                print(f"Up to Date: {'✅' if up_to_date else '❌ Update available'}")
                
        except Exception as e:
            handle_error(f"Failed to get git status: {e}")
    
    def discover_servers(self, git_url: str, branch: str = "main"):
        """Discover MCP servers in a git repository without adding them."""
        try:
            servers = self.git_server_manager.discover_git_servers(git_url, branch)
            
            if not servers:
                print(f"❌ No MCP servers found in repository: {git_url}")
                return
            
            print(f"\n🔍 Found {len(servers)} MCP server(s) in {git_url}:")
            print("=" * 70)
            
            for server in servers:
                print(f"\n📦 {server['name']}")
                print(f"   Entry Point: {server['entry_point']}")
                print(f"   Type: {server['server_type']}")
                print(f"   Category: {server['category']}")
                if server['description']:
                    print(f"   Description: {server['description']}")
                
                # Show package info
                package_info = server.get('package_info', {})
                if package_info.get('language') != 'unknown':
                    print(f"   Language: {package_info['language']}")
                    if package_info.get('dependencies'):
                        deps = package_info['dependencies'][:3]  # Show first 3
                        deps_str = ', '.join(deps)
                        if len(package_info['dependencies']) > 3:
                            deps_str += f" (+{len(package_info['dependencies']) - 3} more)"
                        print(f"   Dependencies: {deps_str}")
            
            print(f"\n💡 To add these servers to your registry, run:")
            print(f"   mcp git add <name> {git_url} --branch {branch}")
                
        except Exception as e:
            handle_error(f"Failed to discover git servers: {e}")
    
    def discover_documentation(self, name: str):
        """Run documentation discovery on a git server."""
        try:
            success = self.git_server_manager.discover_documentation(name)
            if not success:
                print(f"❌ Failed to run documentation discovery for '{name}'")
                
        except Exception as e:
            handle_error(f"Failed to run documentation discovery: {e}")
    
    def list_git_servers(self):
        """List all git-based servers."""
        try:
            git_servers = self.git_server_manager.list_git_servers()
            
            if not git_servers:
                print("No git-based servers found")
                return
            
            print(f"\n📦 Git-based Servers ({len(git_servers)}):")
            print("=" * 60)
            
            for server in git_servers:
                print(f"📍 {server['id']}")
                print(f"   Category: {server['category']}")
                print(f"   Last Doc Discovery: {server.get('last_doc_discovered', 'Never')}")
                
        except Exception as e:
            handle_error(f"Failed to list git servers: {e}")
    
    def cleanup_repository(self, name: str):
        """Remove git repository for a server."""
        try:
            success = self.git_server_manager.cleanup_git_repository(name)
            if success:
                print(f"✅ Cleaned up git repository for '{name}'")
            else:
                print(f"❌ Failed to cleanup git repository for '{name}'")
                
        except Exception as e:
            handle_error(f"Failed to cleanup git repository: {e}")
    
    @staticmethod
    def setup_git_subparser(subparsers):
        """
        Setup git subparser for the main CLI.
        
        Args:
            subparsers: Main CLI subparsers
            
        Returns:
            Git subparser for command routing
        """
        # Git Commands
        git_parser = subparsers.add_parser("git", help="Git-based server management")
        git_subparsers = git_parser.add_subparsers(dest="git_command", help="Git sub-commands")
        
        # git add
        git_add_parser = git_subparsers.add_parser("add", help="Add a git-based MCP server")
        git_add_parser.add_argument("name", help="Server name")
        git_add_parser.add_argument("git_url", help="Git repository URL")
        git_add_parser.add_argument("--branch", default="main", help="Git branch to use")
        git_add_parser.add_argument("--category", help="Server category")
        git_add_parser.add_argument("--description", help="Server description")
        
        # git update
        git_update_parser = git_subparsers.add_parser("update", help="Update a git-based server")
        git_update_parser.add_argument("name", help="Server name to update")
        
        # git status
        git_status_parser = git_subparsers.add_parser("status", help="Show git status for a server")
        git_status_parser.add_argument("name", help="Server name")
        
        # git discover
        git_discover_parser = git_subparsers.add_parser("discover", help="Discover servers in a git repository")
        git_discover_parser.add_argument("git_url", help="Git repository URL")
        git_discover_parser.add_argument("--branch", default="main", help="Git branch to check")
        
        # git doc
        git_doc_parser = git_subparsers.add_parser("doc", help="Run documentation discovery on a git server")
        git_doc_parser.add_argument("name", help="Server name")
        
        # git list
        git_list_parser = git_subparsers.add_parser("list", help="List all git-based servers")
        
        # git cleanup
        git_cleanup_parser = git_subparsers.add_parser("cleanup", help="Remove git repository for a server")
        git_cleanup_parser.add_argument("name", help="Server name")
        
        return git_parser
    
    def route_command(self, args):
        """
        Route git subcommands to appropriate methods.
        
        Args:
            args: Parsed command line arguments
        """
        if args.git_command == "add":
            self.add_server(args.name, args.git_url, args.branch, args.category, args.description)
        elif args.git_command == "update":
            self.update_server(args.name)
        elif args.git_command == "status":
            self.show_status(args.name)
        elif args.git_command == "discover":
            self.discover_servers(args.git_url, args.branch)
        elif args.git_command == "doc":
            self.discover_documentation(args.name)
        elif args.git_command == "list":
            self.list_git_servers()
        elif args.git_command == "cleanup":
            self.cleanup_repository(args.name)
        else:
            print("❌ Unknown git command. Use 'mcp git --help' for available commands.")