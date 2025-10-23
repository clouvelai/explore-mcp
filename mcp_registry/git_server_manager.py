"""
Git Server Manager - Handles all git-specific server operations.

Separates git server management from general server management for better modularity.
"""

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .doc_discovery import DocumentationDiscovery
from .exceptions import FileOperationError, handle_error
from .git_manager import GitManager
from .models import ServerConfig, ServerSource
from .simple_runtime import get_execution_command, can_execute, get_runtime_type


class GitServerManager:
    """Manages git-specific MCP server operations."""
    
    def __init__(self, server_manager, base_dir: str = "mcp_registry"):
        """
        Initialize git server manager.
        
        Args:
            server_manager: Reference to main ServerManager for server operations
            base_dir: Base directory for registry
        """
        self.server_manager = server_manager
        self.base_dir = Path(base_dir)
        
        # Initialize git-specific components
        self.git_manager = GitManager()
        self.doc_discovery = DocumentationDiscovery()
    
    def _auto_build_if_needed(self, repo_path: Path) -> bool:
        """
        Automatically build Node.js projects if needed.
        
        Args:
            repo_path: Path to the git repository
            
        Returns:
            bool: True if build was successful or not needed, False if failed
        """
        package_json = repo_path / "package.json"
        
        if not package_json.exists():
            return True  # Not a Node.js project, continue
        
        # Check if npm is available
        if not shutil.which("npm"):
            print(f"⚠️  npm not found, skipping build for {repo_path.name}")
            return True
        
        print(f"📦 Installing dependencies for {repo_path.name}...")
        
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Dependencies installed for {repo_path.name}")
                return True
            else:
                print(f"⚠️  Dependency installation failed for {repo_path.name}: {result.stderr}")
                return True  # Continue anyway - might still work
                
        except subprocess.TimeoutExpired:
            print(f"⚠️  Dependency installation timeout for {repo_path.name}")
            return True  # Continue anyway
        except Exception as e:
            print(f"⚠️  Dependency installation error for {repo_path.name}: {e}")
            return True  # Continue anyway
    
    def add_git_server(
        self,
        git_url: str,
        name: Optional[str] = None,
        branch: str = "main",
        subpath: Optional[str] = None,
        category: str = "General",
        description: Optional[str] = None
    ) -> List[str]:
        """
        Add a git-based MCP server to the registry.
        
        Args:
            git_url: Git repository URL
            name: Optional server name (auto-detected if not provided)
            branch: Git branch to use
            subpath: Path within repository to server (if not root)
            category: Server category
            description: Server description
            
        Returns:
            List of server IDs that were added
        """
        try:
            # Generate name from URL if not provided
            if not name:
                name = git_url.split('/')[-1].replace('.git', '')
                name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
            
            print(f"📦 Cloning git repository: {git_url}")
            
            # Clone or update the repository
            success, clone_path = self.git_manager.clone_or_update_repo(git_url, name, branch)
            
            if not success:
                print(f"❌ Failed to clone repository: {git_url}")
                return []
            
            # Get current commit hash
            commit_hash = self.git_manager.get_current_commit(clone_path)
            
            # Auto-build if needed (npm install for Node.js projects)
            self._auto_build_if_needed(clone_path)
            
            # Detect MCP servers in the repository
            print(f"🔍 Detecting MCP servers in repository...")
            detected_servers = self.git_manager.detect_mcp_servers(clone_path)
            
            if not detected_servers:
                print(f"⚠️ No MCP servers detected in repository: {git_url}")
                return []
            
            print(f"✅ Found {len(detected_servers)} MCP server(s)")
            
            added_server_ids = []
            
            for server_info in detected_servers:
                # Create server ID
                server_id = f"{name}-{server_info.name}" if len(detected_servers) > 1 else name
                
                # Create git server source
                server_source = ServerSource(
                    type="git",
                    git_url=git_url,
                    git_branch=branch,
                    git_commit=commit_hash,
                    git_subpath=server_info.entry_point,
                    clone_path=str(clone_path),
                    path=str(clone_path / server_info.entry_point),
                    transport="stdio"
                )
                
                # Add server to registry via main server manager
                self.server_manager.add_server(
                    server_id=server_id,
                    name=server_info.name,
                    source=server_source,
                    description=server_info.description or description,
                    category=server_info.category or category,
                    provider="Git"
                )
                
                added_server_ids.append(server_id)
                
                print(f"   ✅ Added: {server_info.name} ({server_id})")
                print(f"      Entry point: {server_info.entry_point}")
                print(f"      Type: {server_info.server_type}")
                
                # Simple runtime verification
                entry_path = clone_path / server_info.entry_point
                if can_execute(entry_path):
                    cmd = get_execution_command(entry_path)
                    print(f"      Execution: {' '.join(cmd)}")
                    print(f"✅ Runtime verified")
                else:
                    print(f"⚠️ Runtime verification failed")
                
                # Automatically run documentation discovery for git servers
                print(f"📚 Running documentation discovery for {server_id}...")
                self.discover_documentation(server_id)
            
            return added_server_ids
            
        except Exception as e:
            handle_error(f"Failed to add git server: {e}")
            return []
    
    def update_git_server(self, server_id: str) -> bool:
        """
        Update a git-based server by pulling latest changes.
        
        Args:
            server_id: Server ID to update
            
        Returns:
            True if successful
        """
        try:
            config = self.server_manager.get_server(server_id)
            if not config:
                print(f"❌ Server not found: {server_id}")
                return False
            
            if config.source.type != "git":
                print(f"❌ Server {server_id} is not a git-based server")
                return False
            
            git_url = config.source.git_url
            git_branch = config.source.git_branch or "main"
            clone_name = config.source.clone_path.split('/')[-1] if config.source.clone_path else server_id
            
            print(f"🔄 Updating git server: {config.name}")
            
            # Update the repository
            success, clone_path = self.git_manager.clone_or_update_repo(git_url, clone_name, git_branch)
            
            if not success:
                print(f"❌ Failed to update repository for {server_id}")
                return False
            
            # Get new commit hash
            new_commit = self.git_manager.get_current_commit(clone_path)
            old_commit = config.source.git_commit
            
            if new_commit == old_commit:
                print(f"✅ Server {server_id} is already up to date")
                return True
            
            # Update server configuration with new commit
            config.source.git_commit = new_commit
            config.metadata.updated_at = datetime.now()
            
            # Update the path in case it changed
            if config.source.git_subpath:
                config.source.path = str(clone_path / config.source.git_subpath)
            else:
                config.source.path = str(clone_path)
            
            # Save updated configuration
            with open(config.config_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
            
            print(f"✅ Server {server_id} updated to commit {new_commit[:8]}")
            
            # Optionally re-run discovery if the server has changed significantly
            if old_commit != new_commit:
                print(f"🔍 Re-running discovery due to code changes...")
                self.server_manager.discover_server(server_id)
            
            return True
            
        except Exception as e:
            handle_error(f"Failed to update git server {server_id}: {e}")
            return False
    
    def get_git_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get git status for a git-based server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Git status information
        """
        config = self.server_manager.get_server(server_id)
        if not config or config.source.type != "git":
            return {"error": "Not a git server"}
        
        try:
            clone_path = Path(config.source.clone_path) if config.source.clone_path else None
            
            status = {
                "server_id": server_id,
                "git_url": config.source.git_url,
                "branch": config.source.git_branch,
                "current_commit": config.source.git_commit,
                "clone_path": str(clone_path) if clone_path else None,
                "subpath": config.source.git_subpath,
                "clone_exists": clone_path.exists() if clone_path else False
            }
            
            # Get latest commit from remote if clone exists
            if clone_path and clone_path.exists():
                latest_commit = self.git_manager.get_current_commit(clone_path)
                status["latest_commit"] = latest_commit
                status["up_to_date"] = latest_commit == config.source.git_commit
            
            return status
            
        except Exception as e:
            return {"error": str(e)}
    
    def discover_git_servers(self, git_url: str, branch: str = "main") -> List[Dict[str, Any]]:
        """
        Discover MCP servers in a git repository without adding them.
        
        Args:
            git_url: Git repository URL
            branch: Git branch to check
            
        Returns:
            List of detected server information
        """
        try:
            # Generate temp name for discovery
            temp_name = f"temp_{git_url.split('/')[-1].replace('.git', '')}"
            
            print(f"🔍 Discovering servers in git repository: {git_url}")
            
            # Clone repository temporarily
            success, clone_path = self.git_manager.clone_or_update_repo(git_url, temp_name, branch)
            
            if not success:
                return []
            
            # Detect servers
            detected_servers = self.git_manager.detect_mcp_servers(clone_path)
            
            # Get package info
            package_info = self.git_manager.get_package_info(clone_path)
            
            # Convert to dict format
            results = []
            for server_info in detected_servers:
                results.append({
                    "name": server_info.name,
                    "entry_point": server_info.entry_point,
                    "server_type": server_info.server_type,
                    "description": server_info.description,
                    "category": server_info.category,
                    "transport": server_info.transport,
                    "auth_required": server_info.auth_required,
                    "package_info": package_info
                })
            
            return results
            
        except Exception as e:
            handle_error(f"Failed to discover git servers: {e}")
            return []
    
    def discover_documentation(self, server_id: str) -> bool:
        """
        Perform documentation-based discovery on a git server.
        
        Args:
            server_id: Server ID to discover documentation for
            
        Returns:
            True if successful
        """
        try:
            config = self.server_manager.get_server(server_id)
            if not config:
                print(f"❌ Server not found: {server_id}")
                return False
            
            if config.source.type != "git":
                print(f"❌ Documentation discovery only supported for git servers")
                return False
            
            if not config.doc_discovery.enabled:
                print(f"⚠️ Documentation discovery disabled for server: {server_id}")
                return False
            
            clone_path = Path(config.source.clone_path) if config.source.clone_path else None
            if not clone_path or not clone_path.exists():
                print(f"❌ Git repository not found. Clone the repository first.")
                return False
            
            print(f"📚 Running documentation discovery on: {config.name}")
            
            # Perform documentation discovery
            result = self.doc_discovery.discover_from_repository(clone_path)
            
            print(f"✅ Documentation discovery completed:")
            print(f"   📋 Found {len(result.tools)} tools")
            print(f"   📁 Found {len(result.resources)} resources") 
            print(f"   💬 Found {len(result.prompts)} prompts")
            
            # Save documentation discovery results
            try:
                with open(config.doc_discovery_path, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2, default=str)
            except (IOError, OSError) as e:
                raise FileOperationError(str(config.doc_discovery_path), "write", str(e))
            
            # Update server configuration
            config.doc_discovery.last_doc_discovered = datetime.now()
            config.metadata.updated_at = datetime.now()
            
            try:
                with open(config.config_path, 'w') as f:
                    json.dump(config.model_dump(), f, indent=2, default=str)
            except (IOError, OSError) as e:
                raise FileOperationError(str(config.config_path), "write", str(e))
            
            print(f"   📝 Documentation discovery saved to: {config.doc_discovery_path}")
            
            return True
            
        except Exception as e:
            handle_error(f"Failed to discover documentation for {server_id}: {e}")
            return False
    
    def is_git_server(self, server_id: str) -> bool:
        """Check if a server is git-based."""
        config = self.server_manager.get_server(server_id)
        return config and config.source.type == "git"
    
    def list_git_servers(self) -> List[Dict[str, Any]]:
        """List all git-based servers."""
        all_servers = self.server_manager.list_servers()
        return [s for s in all_servers if s.get("type") == "git"]
    
    def cleanup_git_repository(self, server_id: str) -> bool:
        """Remove git repository for a server."""
        config = self.server_manager.get_server(server_id)
        if not config or config.source.type != "git":
            return False
        
        clone_path = Path(config.source.clone_path) if config.source.clone_path else None
        if clone_path and clone_path.exists():
            clone_name = clone_path.name
            return self.git_manager.remove_repo(clone_name)
        
        return True
    
    # Removed complex runtime preparation - using simple file extension approach