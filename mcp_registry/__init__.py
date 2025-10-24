"""
Unified MCP Server Registry

Clean, modular system for managing MCP servers with focused components
and dependency injection for testability and maintainability.

Architecture:
- ServerRegistryManager: CRUD operations and data persistence
- ServerDiscoveryManager: Discovery operations and intelligent caching  
- ServerGeneratorManager: Mock server and evaluation generation
- ServerTesterManager: Test execution and validation
- ServerManager: Clean facade with dependency injection
"""

from .discovery import ServerDiscoveryManager
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
from .generator import ServerGeneratorManager
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
from .registry import ServerRegistryManager
from .tester import ServerTesterManager

__all__ = [
    # Main API
    'ServerManager',
    # Core Components (for advanced usage and testing)
    'ServerRegistryManager', 'ServerDiscoveryManager', 
    'ServerGeneratorManager', 'ServerTesterManager',
    # Models
    'ServerConfig', 'ServerSource', 'ServerRegistry', 
    'DiscoveryConfig', 'GenerationConfig', 
    'set_server_base_path', 'get_server_base_path',
    # Local scanning
    'LocalServerScanner', 'LocalServerInfo',
    # Exceptions
    'MCPRegistryError', 'ServerNotFoundError', 'ServerConfigurationError',
    'RegistryLoadError', 'DiscoveryError', 'GenerationError', 'DirectoryNotFoundError',
    'FileOperationError', 'ValidationError', 'handle_error', 'handle_warning'
]
