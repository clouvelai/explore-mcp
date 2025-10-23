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
from .doc_discovery import DocumentationDiscovery
from .git_cli import GitCLI
from .git_manager import GitManager
from .git_server_manager import GitServerManager
from .local_scanner import LocalServerInfo, LocalServerScanner
from .manager import ServerManager
from .models import (
    DiscoveryConfig,
    DocumentationDiscoveryConfig,
    GenerationConfig,
    ServerConfig,
    ServerRegistry,
    ServerSource,
    get_server_base_path,
    set_server_base_path,
)

__all__ = [
    'ServerManager', 'ServerConfig', 'ServerSource', 'ServerRegistry', 
    'DiscoveryConfig', 'DocumentationDiscoveryConfig', 'GenerationConfig', 'set_server_base_path', 'get_server_base_path',
    'DocumentationDiscovery', 'GitCLI', 'GitManager', 'GitServerManager', 'LocalServerScanner', 'LocalServerInfo',
    'MCPRegistryError', 'ServerNotFoundError', 'ServerConfigurationError',
    'RegistryLoadError', 'DiscoveryError', 'GenerationError', 'DirectoryNotFoundError',
    'FileOperationError', 'ValidationError', 'handle_error', 'handle_warning'
]
