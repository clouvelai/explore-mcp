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
    """Source configuration for a server (local file or remote URL)."""
    type: Literal["local", "remote"]
    path: Optional[str] = None  # For local servers
    url: Optional[str] = None   # For remote servers
    transport: str = "stdio"    # stdio, http, sse
    
    @model_validator(mode='after')
    def validate_source(self):
        """Ensure either path or url is provided based on type."""
        if self.type == 'local' and not self.path:
            raise ValueError('path is required for local servers')
        elif self.type == 'remote' and not self.url:
            raise ValueError('url is required for remote servers')
        return self


class DiscoveryConfig(BaseModel):
    """Configuration for server discovery."""
    enabled: bool = True
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")
    timeout: int = Field(default=30, ge=1, description="Discovery timeout in seconds")
    retry_attempts: int = Field(default=3, ge=0, description="Number of retry attempts")
    auth_headers: Optional[Dict[str, str]] = None
    last_discovered: Optional[datetime] = None


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
