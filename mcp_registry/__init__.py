"""
Unified MCP Server Registry

A clean, unified system for managing both local and remote MCP servers
with consistent discovery, generation, and tracking capabilities.
"""

from .exceptions import (
    DirectoryNotFoundError,
    DiscoveryError,
    FileOperationError,
    GenerationError,
    MCPRegistryError,
    RegistryLoadError,
    ServerConfigurationError,
    ServerNotFoundError,
    ValidationError,
    handle_error,
    handle_warning,
)
from .local_scanner import LocalServerInfo, LocalServerScanner
from .manager import ServerManager
from .models import (
    DiscoveryConfig,
    GenerationConfig,
    ServerConfig,
    ServerRegistry,
    ServerSource,
    get_server_base_path,
    set_server_base_path,
)

__all__ = [
    'ServerManager', 'ServerConfig', 'ServerSource', 'ServerRegistry', 
    'DiscoveryConfig', 'GenerationConfig', 'set_server_base_path', 'get_server_base_path',
    'LocalServerScanner', 'LocalServerInfo',
    'MCPRegistryError', 'ServerNotFoundError', 'ServerConfigurationError',
    'RegistryLoadError', 'DiscoveryError', 'GenerationError', 'DirectoryNotFoundError',
    'FileOperationError', 'ValidationError', 'handle_error', 'handle_warning'
]
