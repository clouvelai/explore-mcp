"""
Server Registry - Pure CRUD operations for server configurations.

Handles storage, retrieval, and basic validation of server configurations
without any business logic for discovery, generation, or testing.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import (
    FileOperationError,
    ServerConfigurationError,
    handle_warning,
    validate_server_id,
)
from .models import ServerConfig, ServerRegistry


class ServerRegistryManager:
    """Manages server configuration storage and retrieval."""
    
    def __init__(self, base_dir: Path):
        """Initialize registry manager."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        self.servers_dir = self.base_dir / "servers"
        self.servers_dir.mkdir(exist_ok=True)
        
        self.registry_file = self.base_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> ServerRegistry:
        """Load the server registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                return ServerRegistry(**data)
            except json.JSONDecodeError as e:
                handle_warning(f"Registry file contains invalid JSON: {e}", str(self.registry_file))
            except (IOError, OSError) as e:
                handle_warning(f"Cannot read registry file: {e}", str(self.registry_file))
            except Exception as e:
                handle_warning(f"Failed to load registry: {e}", str(self.registry_file))
        
        return ServerRegistry()
    
    def _save_registry(self) -> None:
        """Save the server registry to disk."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry.model_dump(), f, indent=2, default=str)
        except (IOError, OSError) as e:
            raise FileOperationError(str(self.registry_file), "write", str(e))
    
    def add_server(self, server_id: str, config: ServerConfig) -> None:
        """Add a new server configuration."""
        validate_server_id(server_id)
        
        # Setup server directory
        server_dir = self.servers_dir / server_id
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Create generated directory for future use
        generated_dir = server_dir / "generated"
        generated_dir.mkdir(exist_ok=True)
        
        # Save config to file
        self._persist_server_config(server_id, config)
        
        # Update registry
        category = config.metadata.category
        self.registry.add_server(server_id, category)
        self._save_registry()
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server configuration."""
        if server_id not in self.registry.servers:
            return False
        
        # Remove from registry
        self.registry.remove_server(server_id)
        self._save_registry()
        
        # Remove server directory
        server_dir = self.servers_dir / server_id
        if server_dir.exists():
            shutil.rmtree(server_dir)
        
        return True
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get a server configuration."""
        if server_id not in self.registry.servers:
            return None
        
        config_file = self.servers_dir / server_id / "config.json"
        if not config_file.exists():
            handle_warning(f"Config file missing for registered server", server_id)
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            return ServerConfig(**data)
        except json.JSONDecodeError as e:
            raise ServerConfigurationError(server_id, f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ServerConfigurationError(server_id, f"Invalid configuration data: {e}")
    
    def list_servers(self, category: Optional[str] = None) -> List[ServerConfig]:
        """List all server configurations."""
        servers = []
        for server_id, server_category in self.registry.servers.items():
            if category and server_category != category:
                continue
            
            config = self.get_server(server_id)
            if config:
                servers.append(config)
        
        return servers
    
    def update_server(self, server_id: str, config: ServerConfig) -> None:
        """Update an existing server configuration."""
        if server_id not in self.registry.servers:
            raise ServerConfigurationError(server_id, "Server not found")
        
        # Update config
        self._persist_server_config(server_id, config)
        
        # Update category in registry if changed
        old_category = self.registry.servers[server_id]
        new_category = config.metadata.category
        if old_category != new_category:
            self.registry.servers[server_id] = new_category
            # Update categories mapping
            if old_category in self.registry.categories:
                if server_id in self.registry.categories[old_category]:
                    self.registry.categories[old_category].remove(server_id)
                if not self.registry.categories[old_category]:
                    del self.registry.categories[old_category]
            
            if new_category not in self.registry.categories:
                self.registry.categories[new_category] = []
            if server_id not in self.registry.categories[new_category]:
                self.registry.categories[new_category].append(server_id)
            
            self._save_registry()
    
    def get_server_directory(self, server_id: str) -> Path:
        """Get the directory path for a server."""
        return self.servers_dir / server_id
    
    def server_exists(self, server_id: str) -> bool:
        """Check if a server exists in the registry."""
        return server_id in self.registry.servers
    
    def get_all_server_ids(self) -> List[str]:
        """Get all registered server IDs."""
        return list(self.registry.servers.keys())
    
    def get_categories(self) -> List[str]:
        """Get all unique server categories."""
        return list(set(self.registry.servers.values()))
    
    def _persist_server_config(self, server_id: str, config: ServerConfig) -> None:
        """Save server configuration to file."""
        config_file = self.servers_dir / server_id / "config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
        except Exception as e:
            raise FileOperationError(str(config_file), "write", str(e))