"""
Local MCP Server Scanner

Simple service for finding and analyzing local MCP server files.
Handles the pre-discovery phase - finding servers and extracting metadata
without any MCP protocol communication.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import DirectoryNotFoundError, FileOperationError, handle_warning


@dataclass
class LocalServerInfo:
    """Information about a discovered local MCP server."""
    id: str
    name: str
    path: str
    transport: str
    auth_required: bool
    category: str
    description: Optional[str] = None
    provider: Optional[str] = None


class LocalServerScanner:
    """Scans local directories for MCP servers and extracts metadata."""
    
    def discover_servers(self, servers_dir: str = "mcp_servers") -> List[LocalServerInfo]:
        """
        Discover all local MCP servers in a directory.
        
        Args:
            servers_dir: Path to the directory containing MCP servers
            
        Returns:
            List of discovered server information
            
        Raises:
            DirectoryNotFoundError: If the servers directory doesn't exist
        """
        servers_path = Path(servers_dir)
        if not servers_path.exists():
            raise DirectoryNotFoundError(str(servers_path))
        
        discovered_servers = []
        
        print(f"🔍 Scanning {servers_dir} for MCP servers...")
        
        # Look for server.py files in subdirectories
        for server_dir in servers_path.iterdir():
            if not server_dir.is_dir():
                continue
            
            server_file = server_dir / "server.py"
            if not server_file.exists():
                continue
            
            try:
                server_info = self._analyze_server_file(server_file, server_dir.name)
                discovered_servers.append(server_info)
                print(f"   ✅ Found: {server_info.name} ({server_info.id})")
            except Exception as e:
                handle_warning(f"Failed to analyze {server_file}: {e}", f"server_id={server_dir.name}")
                continue
        
        print(f"🎯 Discovered {len(discovered_servers)} local servers")
        return discovered_servers
    
    def _analyze_server_file(self, server_file: Path, server_id: str) -> LocalServerInfo:
        """
        Analyze a single server.py file to extract metadata.
        
        Args:
            server_file: Path to the server.py file
            server_id: Proposed server ID (directory name)
            
        Returns:
            LocalServerInfo with extracted metadata
        """
        try:
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            raise FileOperationError(str(server_file), "read", str(e))
        
        # Extract metadata using existing logic
        name = self._extract_name(content, server_id)
        description = self._extract_description(content)
        provider = self._extract_provider(content)
        transport = self._detect_transport_type(content)
        auth_required = self._detect_auth_requirement(content)
        category = self._categorize_server(name, content)
        
        return LocalServerInfo(
            id=server_id,
            name=name,
            path=str(server_file),
            transport=transport,
            auth_required=auth_required,
            category=category,
            description=description,
            provider=provider
        )
    
    def _extract_name(self, content: str, fallback_id: str) -> str:
        """Extract server name from FastMCP constructor."""
        name_match = re.search(r'FastMCP\("([^"]+)"\)', content)
        if name_match:
            return name_match.group(1)
        
        # Fallback to directory name
        return fallback_id.replace('_', ' ').title()
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from docstring."""
        desc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if desc_match:
            desc_text = desc_match.group(1).strip()
            # Take first line as description
            return desc_text.split('\n')[0].strip()
        return None
    
    def _extract_provider(self, content: str) -> Optional[str]:
        """Extract provider from imports or comments."""
        content_lower = content.lower()
        
        if "gmail" in content_lower or "google" in content_lower:
            return "Google"
        elif "microsoft" in content_lower:
            return "Microsoft"
        
        return None
    
    def _detect_transport_type(self, content: str) -> str:
        """Detect the transport type used by the server."""
        # Check for SSE/HTTP transport
        if 'transport="sse"' in content or 'mcp.run(transport="sse"' in content:
            return "sse"
        elif 'transport="http"' in content or 'mcp.run(transport="http"' in content:
            return "http"
        
        # Default to stdio
        return "stdio"
    
    def _detect_auth_requirement(self, content: str) -> bool:
        """Detect if the server requires authentication."""
        # Look for authentication-related keywords
        auth_keywords = [
            "oauth", "authentication", "auth", "credentials", 
            "api_key", "token", "login", "environment variables"
        ]
        
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in auth_keywords)
    
    def _categorize_server(self, server_name: str, content: str) -> str:
        """Categorize the server based on name and content."""
        name_lower = server_name.lower()
        content_lower = content.lower()
        
        # Check name first, then content - order matters for specificity
        text_to_check = f"{name_lower} {content_lower}"
        
        # Check most specific categories first
        if any(word in text_to_check for word in ["calculator", "math", "compute", "arithmetic"]):
            return "Utilities"
        elif any(word in text_to_check for word in ["gmail", "email", "mail"]):
            return "Communication"
        elif any(word in text_to_check for word in ["air", "fryer", "cooking", "recipe"]):
            return "Lifestyle"
        elif any(word in text_to_check for word in ["drive", "storage", "file"]):
            return "Storage"
        elif any(word in text_to_check for word in ["git", "github", "repository"]):
            return "Development"
        elif any(word in text_to_check for word in ["docs", "documentation", "learn"]):
            return "Documentation"
        else:
            return "General"