"""
Git repository management for MCP servers.

Handles cloning, updating, and detecting MCP servers in git repositories.
"""

import json
import subprocess
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .exceptions import handle_error, handle_warning


@dataclass
class GitServerInfo:
    """Information about an MCP server found in a git repository."""
    name: str
    entry_point: str  # Relative path to server file from repo root
    server_type: str  # "python", "typescript", "nodejs", "other"
    description: Optional[str] = None
    category: str = "General"
    transport: str = "stdio"
    auth_required: bool = False


class GitManager:
    """Manages git-based MCP servers."""
    
    def __init__(self, base_clone_dir: str = "mcp_registry/git_repos"):
        """Initialize git manager with base directory for clones."""
        self.base_clone_dir = Path(base_clone_dir)
        self.base_clone_dir.mkdir(parents=True, exist_ok=True)
    
    def clone_or_update_repo(self, git_url: str, name: str, branch: str = "main") -> Tuple[bool, Path]:
        """
        Clone a git repository or update if it already exists.
        
        Args:
            git_url: Git repository URL
            name: Name for the local clone directory
            branch: Git branch to checkout
            
        Returns:
            (success: bool, clone_path: Path)
        """
        clone_path = self.base_clone_dir / name
        
        try:
            if clone_path.exists():
                # Update existing repo
                print(f"📦 Updating existing repo: {name}")
                result = subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=clone_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    handle_warning(f"Failed to fetch updates: {result.stderr}")
                    return False, clone_path
                
                # Checkout the desired branch
                result = subprocess.run(
                    ["git", "checkout", f"origin/{branch}"],
                    cwd=clone_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    handle_warning(f"Failed to checkout branch {branch}: {result.stderr}")
                    return False, clone_path
                
                print(f"✅ Repository updated: {name}")
                
            else:
                # Clone new repo
                print(f"📥 Cloning repository: {git_url}")
                result = subprocess.run(
                    ["git", "clone", "--branch", branch, git_url, str(clone_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    handle_error(f"Failed to clone repository: {result.stderr}")
                    return False, clone_path
                
                print(f"✅ Repository cloned: {name}")
            
            return True, clone_path
            
        except subprocess.TimeoutExpired:
            handle_error("Git operation timed out")
            return False, clone_path
        except Exception as e:
            handle_error(f"Git operation failed: {e}")
            return False, clone_path
    
    def get_current_commit(self, repo_path: Path) -> Optional[str]:
        """Get the current commit hash for a repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except Exception:
            return None
    
    def detect_mcp_servers(self, repo_path: Path) -> List[GitServerInfo]:
        """
        Detect MCP servers in a git repository.
        
        Args:
            repo_path: Path to the cloned repository
            
        Returns:
            List of detected servers
        """
        servers = []
        
        # Common patterns for MCP servers
        patterns = [
            # Python servers
            ("**/server.py", "python"),
            ("**/mcp_server.py", "python"),
            ("**/*_server.py", "python"),
            ("**/main.py", "python"),
            
            # TypeScript servers (prioritize over JS)
            ("**/server.ts", "typescript"),
            ("**/index.ts", "typescript"), 
            ("**/src/index.ts", "typescript"),
            ("**/src/server.ts", "typescript"),
            ("**/mcp_server.ts", "typescript"),
            
            # Node.js servers  
            ("**/server.js", "nodejs"),
            ("**/index.js", "nodejs"),
            ("**/dist/index.js", "nodejs"),
            ("**/mcp_server.js", "nodejs"),
        ]
        
        for pattern, server_type in patterns:
            for entry_point in repo_path.glob(pattern):
                if self._is_mcp_server_file(entry_point):
                    relative_path = entry_point.relative_to(repo_path)
                    server_info = self._create_server_info(entry_point, relative_path, server_type)
                    if server_info:
                        servers.append(server_info)
        
        # Remove duplicates based on entry_point
        unique_servers = {}
        for server in servers:
            if server.entry_point not in unique_servers:
                unique_servers[server.entry_point] = server
        
        return list(unique_servers.values())
    
    def _is_mcp_server_file(self, file_path: Path) -> bool:
        """Check if a file appears to be an MCP server."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Look for MCP-related imports and patterns
            mcp_indicators = [
                'from mcp import',
                'import mcp',
                '@mcp.tool',
                'mcp.Server',
                'FastMCP',
                'from fastmcp import',
                'import fastmcp',
                '"mcp"',
                "'mcp'",
                'ModelContextProtocol',
                'ToolResponse',
                'ListToolsRequest'
            ]
            
            content_lower = content.lower()
            for indicator in mcp_indicators:
                if indicator.lower() in content_lower:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _create_server_info(self, file_path: Path, relative_path: Path, server_type: str) -> Optional[GitServerInfo]:
        """Create server info from a detected file - simplified approach."""
        try:
            # Generate name from path
            if file_path.parent.name in ['src', 'dist', 'build']:
                name = file_path.parent.parent.name
            else:
                name = file_path.parent.name
            
            if name in ['.', 'root']:
                name = file_path.stem
            
            # Clean up name
            name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
            if not name:
                name = file_path.stem
            
            # Try to extract description from file
            description = self._extract_description(file_path)
            
            # Determine category based on path/content
            category = self._determine_category(file_path, description)
            
            # Simple server info - clean and minimal
            return GitServerInfo(
                name=name,
                entry_point=str(relative_path),
                server_type=server_type,
                description=description,
                category=category
            )
            
        except Exception as e:
            handle_warning(f"Failed to create server info for {file_path}: {e}")
            return None
    
    def _extract_description(self, file_path: Path) -> Optional[str]:
        """Extract description from file docstring or comments."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')[:2000]  # First 2KB
            
            # Python docstring
            docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
            if docstring_match:
                desc = docstring_match.group(1).strip()
                # Take first line only
                return desc.split('\n')[0][:100]
            
            # Comment description
            comment_match = re.search(r'#\s*(.+)', content)
            if comment_match:
                return comment_match.group(1).strip()[:100]
            
            return None
            
        except Exception:
            return None
    
    def _determine_category(self, file_path: Path, description: Optional[str]) -> str:
        """Determine server category based on path and description."""
        path_str = str(file_path).lower()
        desc_str = (description or "").lower()
        
        # Category keywords
        categories = {
            "Communication": ["gmail", "email", "slack", "discord", "chat", "message"],
            "Storage": ["drive", "storage", "file", "s3", "blob", "database", "db"],
            "Utilities": ["calculator", "math", "utility", "tool", "helper"],
            "Documentation": ["docs", "documentation", "wiki", "readme"],
            "Development": ["git", "github", "gitlab", "code", "repo", "development"],
            "API": ["api", "rest", "graphql", "endpoint"],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in path_str or keyword in desc_str:
                    return category
        
        return "General"
    
    # Removed complex runtime detection - using simple file extension approach
    
    def get_package_info(self, repo_path: Path) -> Dict:
        """Extract package information from repository."""
        info = {
            "language": "unknown",
            "dependencies": [],
            "entry_points": [],
            "description": None
        }
        
        # Check for Python
        if (repo_path / "pyproject.toml").exists():
            info["language"] = "python"
            # TODO: Parse pyproject.toml for dependencies
        elif (repo_path / "requirements.txt").exists():
            info["language"] = "python"
            try:
                deps = (repo_path / "requirements.txt").read_text().splitlines()
                info["dependencies"] = [dep.strip() for dep in deps if dep.strip()]
            except:
                pass
        
        # Check for Node.js
        package_json = repo_path / "package.json"
        if package_json.exists():
            info["language"] = "nodejs"
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    info["description"] = data.get("description")
                    info["dependencies"] = list(data.get("dependencies", {}).keys())
                    if "main" in data:
                        info["entry_points"].append(data["main"])
            except:
                pass
        
        # Check for README
        for readme_name in ["README.md", "README.txt", "readme.md"]:
            readme_path = repo_path / readme_name
            if readme_path.exists() and not info["description"]:
                try:
                    content = readme_path.read_text(encoding='utf-8')[:500]
                    # Extract first meaningful line
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#') and len(line) > 10:
                            info["description"] = line[:200]
                            break
                except:
                    pass
        
        return info
    
    def remove_repo(self, name: str) -> bool:
        """Remove a cloned repository."""
        clone_path = self.base_clone_dir / name
        if clone_path.exists():
            try:
                shutil.rmtree(clone_path)
                print(f"✅ Removed repository: {name}")
                return True
            except Exception as e:
                handle_error(f"Failed to remove repository {name}: {e}")
                return False
        return True