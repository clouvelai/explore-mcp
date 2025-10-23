"""
Pydantic models for unified MCP server registry.

Clean, type-safe models following best practices for server configuration,
discovery, and generation tracking.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator, validator

# Global configuration for server base path
_SERVER_BASE_PATH = "mcp_registry/servers"

def set_server_base_path(path: str):
    """Set the base path for server configurations."""
    global _SERVER_BASE_PATH
    _SERVER_BASE_PATH = path

def get_server_base_path() -> str:
    """Get the current server base path."""
    return _SERVER_BASE_PATH


class ServerSource(BaseModel):
    """Source configuration for a server (local file, remote URL, or git repo)."""
    type: Literal["local", "remote", "git"]
    path: Optional[str] = None  # For local servers or git clone path
    url: Optional[str] = None   # For remote servers or git repo URL
    transport: str = "stdio"    # stdio, http, sse
    
    # Git-specific fields
    git_url: Optional[str] = None      # Git repository URL
    git_branch: Optional[str] = "main" # Git branch to use
    git_commit: Optional[str] = None   # Specific commit hash (optional)
    git_subpath: Optional[str] = None  # Path within git repo to server
    clone_path: Optional[str] = None   # Local path where repo is cloned
    
    @model_validator(mode='after')
    def validate_source(self):
        """Ensure proper fields are provided based on type."""
        if self.type == 'local' and not self.path:
            raise ValueError('path is required for local servers')
        elif self.type == 'remote' and not self.url:
            raise ValueError('url is required for remote servers')
        elif self.type == 'git' and not self.git_url:
            raise ValueError('git_url is required for git servers')
        return self


class DiscoveryConfig(BaseModel):
    """Configuration for server discovery."""
    enabled: bool = True
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")
    timeout: int = Field(default=30, ge=1, description="Discovery timeout in seconds")
    retry_attempts: int = Field(default=3, ge=0, description="Number of retry attempts")
    auth_headers: Optional[Dict[str, str]] = None
    last_discovered: Optional[datetime] = None


class DocumentationDiscoveryConfig(BaseModel):
    """Configuration for documentation-based discovery from git repositories."""
    enabled: bool = True
    last_doc_discovered: Optional[datetime] = None
    parse_readme: bool = True
    parse_code_comments: bool = True
    parse_config_files: bool = True


class GenerationConfig(BaseModel):
    """Configuration for mock server generation."""
    enabled: bool = True
    output_dir: str = "generated"
    include_resources: bool = True
    include_prompts: bool = True
    mock_data_enabled: bool = True
    last_generated: Optional[datetime] = None


class ServerMetadata(BaseModel):
    """Metadata for a server."""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    description: Optional[str] = None
    category: str = "General"
    provider: Optional[str] = None
    auth_required: bool = False
    auth_type: Optional[str] = None


class ServerConfig(BaseModel):
    """Complete configuration for an MCP server."""
    id: str = Field(..., min_length=1, description="Unique server identifier")
    name: str = Field(..., min_length=1, description="Human-readable server name")
    source: ServerSource
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    doc_discovery: DocumentationDiscoveryConfig = Field(default_factory=DocumentationDiscoveryConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    metadata: ServerMetadata = Field(default_factory=ServerMetadata)
    
    @validator('id')
    def validate_id(cls, v):
        """Ensure ID is filesystem-safe."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('ID must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @property
    def generated_path(self) -> Path:
        """Get the path to generated files."""
        return Path(get_server_base_path()) / self.id / self.generation.output_dir
    
    @property
    def config_path(self) -> Path:
        """Get the path to server config file."""
        return Path(get_server_base_path()) / self.id / "config.json"
    
    @property
    def discovery_path(self) -> Path:
        """Get the path to discovery results."""
        return Path(get_server_base_path()) / self.id / "discovery.json"
    
    @property
    def doc_discovery_path(self) -> Path:
        """Get the path to documentation discovery results."""
        return Path(get_server_base_path()) / self.id / "doc_discovery.json"
    
    @classmethod
    def generate_template(cls) -> str:
        """Generate a template JSON string for server configuration."""
        # Create a template dict that bypasses Pydantic validation
        template_dict = {
            "id": "{{SERVER_ID}}",
            "name": "{{SERVER_NAME}}",
            "source": {
                "type": "{{SERVER_TYPE}}",
                "path": "{{SERVER_PATH}}",
                "url": "{{SERVER_URL}}",
                "transport": "{{TRANSPORT}}"
            },
            "discovery": {
                "enabled": True,
                "cache_ttl": 3600,
                "timeout": 30,
                "retry_attempts": 3,
                "auth_headers": None,
                "last_discovered": None
            },
            "generation": {
                "enabled": True,
                "output_dir": "generated",
                "include_resources": True,
                "include_prompts": True,
                "mock_data_enabled": True,
                "last_generated": None
            },
            "metadata": {
                "created_at": "{{CREATED_AT}}",
                "updated_at": "{{CREATED_AT}}",
                "version": "1.0.0",
                "description": "{{DESCRIPTION}}",
                "category": "{{CATEGORY}}",
                "provider": "{{PROVIDER}}",
                "auth_required": False,
                "auth_type": "{{AUTH_TYPE}}"
            }
        }
        
        import json
        return json.dumps(template_dict, indent=2)


class ServerRegistry(BaseModel):
    """Master registry of all MCP servers."""
    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.now)
    servers: List[str] = Field(default_factory=list, description="List of server IDs")
    categories: Dict[str, List[str]] = Field(default_factory=dict, description="Servers grouped by category")
    
    def add_server(self, server_id: str, category: str = "General"):
        """Add a server to the registry."""
        if server_id not in self.servers:
            self.servers.append(server_id)
        
        if category not in self.categories:
            self.categories[category] = []
        if server_id not in self.categories[category]:
            self.categories[category].append(server_id)
        
        self.last_updated = datetime.now()
    
    def remove_server(self, server_id: str):
        """Remove a server from the registry."""
        if server_id in self.servers:
            self.servers.remove(server_id)
        
        # Remove from all categories
        for category, servers in self.categories.items():
            if server_id in servers:
                servers.remove(server_id)
        
        self.last_updated = datetime.now()
    
    def get_servers_by_category(self, category: str) -> List[str]:
        """Get all server IDs in a category."""
        return self.categories.get(category, [])
    
    def get_servers_by_type(self, server_type: str) -> List[str]:
        """Get all server IDs of a specific type (local/remote)."""
        # This would need to be implemented in the manager
        # since we don't store type info in the registry
        return []
