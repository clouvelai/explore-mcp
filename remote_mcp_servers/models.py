"""
Data models for remote MCP server management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DiscoveryConfig(BaseModel):
    """Configuration for server discovery."""
    enabled: bool = True
    cache_ttl: int = 3600  # seconds
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    auth_headers: Optional[Dict[str, str]] = None


class GenerationConfig(BaseModel):
    """Configuration for mock server generation."""
    enabled: bool = True
    output_dir: str = "generated/"
    include_resources: bool = True
    include_prompts: bool = True
    mock_data_enabled: bool = True


class ServerMetadata(BaseModel):
    """Metadata for a remote server."""
    created_at: datetime
    last_discovered: Optional[datetime] = None
    last_generated: Optional[datetime] = None
    version: str = "1.0.0"


class RemoteServerConfig(BaseModel):
    """Configuration for a remote MCP server."""
    name: str
    id: str
    description: str
    url: str
    transport: str = "http"
    auth_required: bool = False
    auth_type: Optional[str] = None
    category: str
    provider: str
    status: str = "active"
    discovery_config: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)
    metadata: ServerMetadata = Field(default_factory=lambda: ServerMetadata(created_at=datetime.now()))


class RemoteServerRegistry(BaseModel):
    """Registry of all remote MCP servers."""
    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.now)
    servers: List[Dict[str, Any]] = Field(default_factory=list)
    categories: Dict[str, List[str]] = Field(default_factory=dict)
