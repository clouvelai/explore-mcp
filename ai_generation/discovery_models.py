#!/usr/bin/env python3
"""
Pydantic models for MCP discovery data structures.

These models provide type safety, validation, and better developer experience
for working with discovery results from MCP servers.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolSchema(BaseModel):
    """Schema for an MCP tool parameter or property."""
    type: str
    description: Optional[str] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types
    required: Optional[List[str]] = None
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class MCPTool(BaseModel):
    """Represents a discovered MCP tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="JSON Schema for tool input")
    outputSchema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for tool output")
    meta: Optional[Dict[str, Any]] = Field(None, description="Tool metadata (e.g., FastMCP tags)", alias="_meta")

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields from Inspector
        populate_by_name=True  # Allow both 'meta' and '_meta'
    )


class MCPResource(BaseModel):
    """Represents a discovered MCP resource."""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mimeType: Optional[str] = Field(None, description="MIME type of resource content")
    meta: Optional[Dict[str, Any]] = Field(None, description="Resource metadata", alias="_meta")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True
    )


class PromptArgument(BaseModel):
    """Represents a prompt argument."""
    name: str = Field(..., description="Argument name")
    description: Optional[str] = Field(None, description="Argument description")
    required: bool = Field(True, description="Whether argument is required")


class MCPPrompt(BaseModel):
    """Represents a discovered MCP prompt."""
    name: str = Field(..., description="Prompt name")
    description: str = Field(..., description="Prompt description")
    arguments: List[PromptArgument] = Field(default_factory=list, description="Prompt arguments")
    meta: Optional[Dict[str, Any]] = Field(None, description="Prompt metadata", alias="_meta")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True
    )


class ServerInfo(BaseModel):
    """Represents MCP server metadata."""
    name: Optional[str] = Field(None, description="Server name")
    version: Optional[str] = Field(None, description="Server version")
    description: Optional[str] = Field(None, description="Server description")
    author: Optional[str] = Field(None, description="Server author")
    license: Optional[str] = Field(None, description="Server license")

    model_config = ConfigDict(
        extra="allow"  # Allow additional server metadata
    )


class DiscoveryMetadata(BaseModel):
    """Metadata about the discovery process."""
    discovered_at: datetime = Field(..., description="When discovery was performed")
    discovery_method: str = Field("mcp-inspector", description="Method used for discovery")
    discovery_time_ms: Optional[int] = Field(None, description="Discovery time in milliseconds")
    cache_hit: bool = Field(False, description="Whether result came from cache")
    cache_age_seconds: Optional[int] = Field(None, description="Age of cached data in seconds")
    inspector_version: Optional[str] = Field(None, description="MCP Inspector version used")

    @field_validator('discovered_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from ISO string if needed."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class DiscoveryResult(BaseModel):
    """Complete MCP server discovery result."""
    server_path: str = Field(..., description="Path to the MCP server file")
    transport: str = Field(..., description="Transport type (stdio, http, sse)")
    command: str = Field(..., description="Command used to launch the server")
    tools: List[MCPTool] = Field(default_factory=list, description="Discovered tools")
    resources: List[MCPResource] = Field(default_factory=list, description="Discovered resources")
    prompts: List[MCPPrompt] = Field(default_factory=list, description="Discovered prompts")
    server_info: ServerInfo = Field(default_factory=ServerInfo, description="Server metadata")
    metadata: DiscoveryMetadata = Field(..., description="Discovery process metadata")
    server_file_hash: Optional[str] = Field(None, description="MD5 hash of server file (local servers only)")
    discovery_content_hash: Optional[str] = Field(None, description="MD5 hash of discovery content (tools, resources, prompts)")

    @field_validator('transport')
    @classmethod
    def validate_transport(cls, v):
        """Validate transport type."""
        valid_transports = {'stdio', 'http', 'sse'}
        if v not in valid_transports:
            raise ValueError(f"Transport must be one of {valid_transports}, got {v}")
        return v

    @property
    def tool_count(self) -> int:
        """Number of discovered tools."""
        return len(self.tools)

    @property
    def resource_count(self) -> int:
        """Number of discovered resources."""
        return len(self.resources)

    @property
    def prompt_count(self) -> int:
        """Number of discovered prompts."""
        return len(self.prompts)

    @property
    def is_cached(self) -> bool:
        """Whether this result came from cache."""
        return self.metadata.cache_hit

    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return next((tool for tool in self.tools if tool.name == name), None)

    def get_tool_names(self) -> List[str]:
        """Get list of all tool names."""
        return [tool.name for tool in self.tools]

    def summary(self) -> str:
        """Get a human-readable summary of the discovery."""
        return (
            f"Discovery of {self.server_path}:\n"
            f"  Transport: {self.transport}\n"
            f"  Tools: {self.tool_count}\n"
            f"  Resources: {self.resource_count}\n"
            f"  Prompts: {self.prompt_count}\n"
            f"  Cached: {self.is_cached}\n"
            f"  Discovery time: {self.metadata.discovery_time_ms}ms\n"
            f"  Server file hash: {self.server_file_hash[:8] + '...' if self.server_file_hash else 'N/A'}\n"
            f"  Discovery hash: {self.discovery_content_hash[:8] + '...' if self.discovery_content_hash else 'N/A'}"
        )

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        Compute MD5 hash of a file.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            MD5 hash as hex string
            
        Example:
            hash = DiscoveryResult.compute_file_hash('server.py')
            print(f"File hash: {hash}")
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (OSError, IOError) as e:
            print(f"⚠️  Failed to compute hash for {file_path}: {e}")
            return ""

    @staticmethod
    def compute_discovery_hash(tools: List[MCPTool], resources: List[MCPResource], prompts: List[MCPPrompt]) -> str:
        """
        Compute MD5 hash of discovery content (tools, resources, prompts).
        
        This hash captures the API contract of the MCP server - all tool schemas,
        resource definitions, and prompt structures including descriptions.
        Changes to any tool parameters, descriptions, or new/removed capabilities
        will result in a different hash.
        
        Args:
            tools: List of discovered tools
            resources: List of discovered resources  
            prompts: List of discovered prompts
            
        Returns:
            MD5 hash as hex string
            
        Example:
            hash = DiscoveryResult.compute_discovery_hash(tools, resources, prompts)
            print(f"Discovery content hash: {hash}")
        """
        try:
            discovery_content = {
                "tools": [tool.model_dump() for tool in tools],
                "resources": [resource.model_dump() for resource in resources],
                "prompts": [prompt.model_dump() for prompt in prompts]
            }
            
            # Sort keys for consistent hashing
            content_json = json.dumps(discovery_content, sort_keys=True, separators=(',', ':'))
            return hashlib.md5(content_json.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"⚠️  Failed to compute discovery content hash: {e}")
            return ""

    def save(self, file_path: Union[str, Path]) -> Path:
        """
        Save discovery result to a JSON file.
        
        Args:
            file_path: Path where to save the discovery data
            
        Returns:
            Path: The path where the file was saved
            
        Example:
            result = engine.discover('server.py')
            saved_path = result.save('output/discovery.json')
            print(f"💾 Saved to {saved_path}")
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.model_dump(), f, indent=2, default=str)
        
        print(f"💾 Saved discovery data to: {path}")
        return path

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


# Conversion utilities for backward compatibility
def dict_to_discovery_result(data: Dict[str, Any]) -> DiscoveryResult:
    """
    Convert a dictionary (from legacy code) to a DiscoveryResult model.
    
    This function handles the transition from untyped dictionaries to
    Pydantic models while maintaining backward compatibility.
    """
    # Handle metadata conversion
    metadata_dict = data.get("metadata", {})
    if "discovered_at" in metadata_dict and isinstance(metadata_dict["discovered_at"], str):
        metadata_dict["discovered_at"] = datetime.fromisoformat(metadata_dict["discovered_at"])
    
    return DiscoveryResult(**data)


def discovery_result_to_dict(result: DiscoveryResult) -> Dict[str, Any]:
    """
    Convert a DiscoveryResult model to a dictionary for legacy compatibility.
    
    This ensures that existing code expecting dictionaries continues to work.
    """
    return result.model_dump()


# Example usage and validation
if __name__ == "__main__":
    # Example discovery result
    example_data = {
        "server_path": "mcp_servers/calculator/server.py",
        "transport": "stdio",
        "command": "uv run python mcp_servers/calculator/server.py",
        "tools": [
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            }
        ],
        "resources": [],
        "prompts": [],
        "server_info": {"name": "calculator", "version": "1.0.0"},
        "metadata": {
            "discovered_at": datetime.now(),
            "discovery_method": "mcp-inspector",
            "discovery_time_ms": 4500,
            "cache_hit": False
        },
        "server_file_hash": "ca05db014a452deb0af27b372af7f47a",
        "discovery_content_hash": "4ff2cad11d4bd129c763c57d7aa15057"
    }
    
    # Test model creation and validation
    result = DiscoveryResult(**example_data)
    print(result.summary())
    print(f"Tool names: {result.get_tool_names()}")
    
    # Test conversion utilities
    dict_result = discovery_result_to_dict(result)
    back_to_model = dict_to_discovery_result(dict_result)
    print(f"Round-trip successful: {result.server_path == back_to_model.server_path}")
    
    # Test model_dump
    print(f"\nJSON serialization test:")
    json_data = result.model_dump()
    print(f"Serialized keys: {list(json_data.keys())}")