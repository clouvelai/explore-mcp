"""
Unified MCP Server Registry

A clean, unified system for managing both local and remote MCP servers
with consistent discovery, generation, and tracking capabilities.
"""

from .manager import ServerManager
from .models import ServerConfig, ServerSource, ServerRegistry, DiscoveryConfig, GenerationConfig
from .local_scanner import LocalServerScanner, LocalServerInfo
from .exceptions import (
    MCPRegistryError, ServerNotFoundError, ServerConfigurationError, 
    RegistryLoadError, DiscoveryError, GenerationError, DirectoryNotFoundError,
    FileOperationError, ValidationError, handle_error, handle_warning
)

__all__ = [
    'ServerManager', 'ServerConfig', 'ServerSource', 'ServerRegistry', 
    'DiscoveryConfig', 'GenerationConfig', 'LocalServerScanner', 'LocalServerInfo',
    'MCPRegistryError', 'ServerNotFoundError', 'ServerConfigurationError',
    'RegistryLoadError', 'DiscoveryError', 'GenerationError', 'DirectoryNotFoundError',
    'FileOperationError', 'ValidationError', 'handle_error', 'handle_warning'
]
