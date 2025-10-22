"""
Remote MCP Server Manager

Manages remote MCP server definitions, discovery, and mock generation.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from .models import RemoteServerConfig, RemoteServerRegistry, DiscoveryConfig, GenerationConfig
from ai_generation.discovery import DiscoveryEngine, DiscoveryResult


class RemoteServerManager:
    """Manages remote MCP server definitions and operations."""
    
    def __init__(self, base_dir: str = "remote_mcp_servers"):
        """
        Initialize the remote server manager.
        
        Args:
            base_dir: Base directory for remote server definitions
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Initialize discovery engine
        self.discovery_engine = DiscoveryEngine()
        
        # Load registry
        self.registry_file = self.base_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> RemoteServerRegistry:
        """Load the server registry."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                return RemoteServerRegistry(**data)
            except Exception as e:
                print(f"Warning: Failed to load registry: {e}")
        
        # Create new registry
        return RemoteServerRegistry()
    
    def _save_registry(self):
        """Save the server registry."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry.model_dump(), f, indent=2, default=str)
    
    def add_server(self, server_config: RemoteServerConfig) -> str:
        """
        Add a new remote server definition.
        
        Args:
            server_config: Server configuration
            
        Returns:
            Server ID
        """
        server_dir = self.base_dir / server_config.id
        server_dir.mkdir(exist_ok=True)
        
        # Create generated subdirectory
        (server_dir / "generated").mkdir(exist_ok=True)
        
        # Save server configuration
        server_file = server_dir / "server.json"
        with open(server_file, 'w') as f:
            json.dump(server_config.model_dump(), f, indent=2, default=str)
        
        # Update registry
        server_entry = {
            "id": server_config.id,
            "name": server_config.name,
            "status": server_config.status,
            "auth_required": server_config.auth_required,
            "category": server_config.category,
            "last_discovered": None,
            "url": server_config.url
        }
        
        # Remove existing entry if present
        self.registry.servers = [s for s in self.registry.servers if s.get("id") != server_config.id]
        self.registry.servers.append(server_entry)
        
        # Update categories
        if server_config.category not in self.registry.categories:
            self.registry.categories[server_config.category] = []
        if server_config.id not in self.registry.categories[server_config.category]:
            self.registry.categories[server_config.category].append(server_config.id)
        
        self.registry.last_updated = datetime.now()
        self._save_registry()
        
        print(f"✅ Added server: {server_config.name} ({server_config.id})")
        return server_config.id
    
    def get_server(self, server_id: str) -> Optional[RemoteServerConfig]:
        """Get server configuration by ID."""
        server_file = self.base_dir / server_id / "server.json"
        if not server_file.exists():
            return None
        
        try:
            with open(server_file, 'r') as f:
                data = json.load(f)
            return RemoteServerConfig(**data)
        except Exception as e:
            print(f"Error loading server {server_id}: {e}")
            return None
    
    def list_servers(self, category: Optional[str] = None, auth_required: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        List all servers with optional filtering.
        
        Args:
            category: Filter by category
            auth_required: Filter by authentication requirement
            
        Returns:
            List of server information
        """
        servers = self.registry.servers.copy()
        
        if category:
            servers = [s for s in servers if s.get("category") == category]
        
        if auth_required is not None:
            servers = [s for s in servers if s.get("auth_required") == auth_required]
        
        return servers
    
    def discover_server(self, server_id: str) -> Optional[DiscoveryResult]:
        """
        Discover tools/resources for a specific server.
        
        Args:
            server_id: Server ID to discover
            
        Returns:
            Discovery result or None if failed
        """
        server_config = self.get_server(server_id)
        if not server_config:
            print(f"❌ Server not found: {server_id}")
            return None
        
        if not server_config.discovery_config.enabled:
            print(f"⚠️  Discovery disabled for server: {server_id}")
            return None
        
        print(f"🔍 Discovering server: {server_config.name}")
        
        try:
            # Perform discovery
            result = self.discovery_engine.discover(
                server_config.url,
                transport=server_config.transport,
                use_cache=True
            )
            
            # Save discovery results
            discovery_file = self.base_dir / server_id / "discovery.json"
            with open(discovery_file, 'w') as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
            
            # Update server metadata
            server_config.metadata.last_discovered = datetime.now()
            server_file = self.base_dir / server_id / "server.json"
            with open(server_file, 'w') as f:
                json.dump(server_config.model_dump(), f, indent=2, default=str)
            
            # Update registry
            for server in self.registry.servers:
                if server["id"] == server_id:
                    server["last_discovered"] = datetime.now().isoformat()
                    break
            
            self._save_registry()
            
            print(f"✅ Discovery completed: {len(result.tools)} tools, {len(result.resources)} resources")
            return result
            
        except Exception as e:
            print(f"❌ Discovery failed for {server_id}: {e}")
            return None
    
    def discover_all(self, auth_required: bool = False) -> List[DiscoveryResult]:
        """
        Discover all servers matching criteria.
        
        Args:
            auth_required: Only discover servers with this auth requirement
            
        Returns:
            List of discovery results
        """
        servers = self.list_servers(auth_required=auth_required)
        results = []
        
        print(f"🔍 Discovering {len(servers)} servers (auth_required={auth_required})")
        
        for server_info in servers:
            server_id = server_info["id"]
            result = self.discover_server(server_id)
            if result:
                results.append(result)
        
        print(f"✅ Discovery completed: {len(results)}/{len(servers)} servers successful")
        return results
    
    def generate_mock(self, server_id: str) -> Optional[str]:
        """
        Generate mock server for a specific server.
        
        Args:
            server_id: Server ID to generate mock for
            
        Returns:
            Path to generated mock server or None if failed
        """
        server_config = self.get_server(server_id)
        if not server_config:
            print(f"❌ Server not found: {server_id}")
            return None
        
        if not server_config.generation_config.enabled:
            print(f"⚠️  Generation disabled for server: {server_id}")
            return None
        
        # Check if discovery results exist
        discovery_file = self.base_dir / server_id / "discovery.json"
        if not discovery_file.exists():
            print(f"❌ No discovery results found for {server_id}. Run discovery first.")
            return None
        
        print(f"🏗️  Generating mock server: {server_config.name}")
        
        try:
            # Load discovery results
            with open(discovery_file, 'r') as f:
                discovery_data = json.load(f)
            
            # Import generation modules
            from ai_generation.server_generator import generate_ai_mock_server
            
            # Generate mock server
            generate_ai_mock_server(
                discovery_data,
                self.base_dir / server_id / "generated"
            )
            
            # Update server metadata
            server_config.metadata.last_generated = datetime.now()
            server_file = self.base_dir / server_id / "server.json"
            with open(server_file, 'w') as f:
                json.dump(server_config.model_dump(), f, indent=2, default=str)
            
            print(f"✅ Mock server generated")
            return str(self.base_dir / server_id / "generated")
            
        except Exception as e:
            print(f"❌ Generation failed for {server_id}: {e}")
            return None
    
    def generate_all(self, auth_required: bool = False) -> List[str]:
        """
        Generate mocks for all discovered servers.
        
        Args:
            auth_required: Only generate for servers with this auth requirement
            
        Returns:
            List of generated mock server paths
        """
        servers = self.list_servers(auth_required=auth_required)
        results = []
        
        print(f"🏗️  Generating mocks for {len(servers)} servers (auth_required={auth_required})")
        
        for server_info in servers:
            server_id = server_info["id"]
            result = self.generate_mock(server_id)
            if result:
                results.append(result)
        
        print(f"✅ Generation completed: {len(results)}/{len(servers)} servers successful")
        return results
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server definition.
        
        Args:
            server_id: Server ID to remove
            
        Returns:
            True if successful
        """
        server_dir = self.base_dir / server_id
        if not server_dir.exists():
            print(f"❌ Server not found: {server_id}")
            return False
        
        # Remove directory
        shutil.rmtree(server_dir)
        
        # Update registry
        self.registry.servers = [s for s in self.registry.servers if s.get("id") != server_id]
        
        # Update categories
        for category, servers in self.registry.categories.items():
            if server_id in servers:
                servers.remove(server_id)
        
        self._save_registry()
        
        print(f"✅ Removed server: {server_id}")
        return True
