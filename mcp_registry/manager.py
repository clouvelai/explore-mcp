"""
Unified Server Manager

Clean, unified management of both local and remote MCP servers
with consistent discovery, generation, and tracking capabilities.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .models import ServerConfig, ServerRegistry, ServerSource, DiscoveryConfig, GenerationConfig, ServerMetadata
from ai_generation.discovery import DiscoveryEngine, DiscoveryResult


class ServerManager:
    """Unified manager for all MCP servers (local and remote)."""
    
    def __init__(self, base_dir: str = "mcp_registry"):
        """
        Initialize the server manager.
        
        Args:
            base_dir: Base directory for server registry
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Ensure servers directory exists
        self.servers_dir = self.base_dir / "servers"
        self.servers_dir.mkdir(exist_ok=True)
        
        # Initialize discovery engine
        self.discovery_engine = DiscoveryEngine()
        
        # Load registry
        self.registry_file = self.base_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> ServerRegistry:
        """Load the server registry."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                return ServerRegistry(**data)
            except Exception as e:
                print(f"Warning: Failed to load registry: {e}")
        
        # Create new registry
        return ServerRegistry()
    
    def _save_registry(self):
        """Save the server registry."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry.model_dump(), f, indent=2, default=str)
    
    def add_server(
        self,
        server_id: str,
        name: str,
        source: Union[str, ServerSource],
        description: Optional[str] = None,
        category: str = "General",
        provider: Optional[str] = None,
        auth_required: bool = False,
        auth_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Add a new server to the registry.
        
        Args:
            server_id: Unique server identifier
            name: Human-readable server name
            source: Server source (path/url string or ServerSource object)
            description: Server description
            category: Server category
            provider: Server provider
            auth_required: Whether server requires authentication
            auth_type: Type of authentication required
            **kwargs: Additional configuration options
            
        Returns:
            Server ID
        """
        # Create server source
        if isinstance(source, str):
            if source.startswith(("http://", "https://")):
                server_source = ServerSource(type="remote", url=source, transport="http")
            else:
                server_source = ServerSource(type="local", path=source, transport="stdio")
        else:
            server_source = source
        
        # Create server configuration
        server_config = ServerConfig(
            id=server_id,
            name=name,
            source=server_source,
            metadata=ServerMetadata(
                description=description,
                category=category,
                provider=provider,
                auth_required=auth_required,
                auth_type=auth_type
            ),
            **kwargs
        )
        
        # Create server directory
        server_dir = self.servers_dir / server_id
        server_dir.mkdir(exist_ok=True)
        (server_dir / server_config.generation.output_dir).mkdir(exist_ok=True)
        
        # Save server configuration
        with open(server_config.config_path, 'w') as f:
            json.dump(server_config.model_dump(), f, indent=2, default=str)
        
        # Update registry
        self.registry.add_server(server_id, category)
        self._save_registry()
        
        print(f"✅ Added server: {name} ({server_id})")
        print(f"   Type: {server_source.type}")
        print(f"   Source: {server_source.url or server_source.path}")
        print(f"   Generated path: {server_config.generated_path}")
        
        return server_id
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get server configuration by ID."""
        config_file = self.servers_dir / server_id / "config.json"
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            return ServerConfig(**data)
        except Exception as e:
            print(f"Error loading server {server_id}: {e}")
            return None
    
    def list_servers(
        self,
        category: Optional[str] = None,
        server_type: Optional[str] = None,
        auth_required: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        List all servers with optional filtering.
        
        Args:
            category: Filter by category
            server_type: Filter by type (local/remote)
            auth_required: Filter by authentication requirement
            
        Returns:
            List of server information
        """
        servers = []
        
        for server_id in self.registry.servers:
            config = self.get_server(server_id)
            if not config:
                continue
            
            # Apply filters
            if category and config.metadata.category != category:
                continue
            if server_type and config.source.type != server_type:
                continue
            if auth_required is not None and config.metadata.auth_required != auth_required:
                continue
            
            servers.append({
                "id": server_id,
                "name": config.name,
                "type": config.source.type,
                "status": "active",
                "auth_required": config.metadata.auth_required,
                "category": config.metadata.category,
                "provider": config.metadata.provider,
                "last_discovered": config.discovery.last_discovered,
                "last_generated": config.generation.last_generated,
                "generated_path": str(config.generated_path)
            })
        
        return servers
    
    def discover_server(self, server_id: str) -> Optional[DiscoveryResult]:
        """
        Discover tools/resources for a specific server.
        
        Args:
            server_id: Server ID to discover
            
        Returns:
            Discovery result or None if failed
        """
        config = self.get_server(server_id)
        if not config:
            print(f"❌ Server not found: {server_id}")
            return None
        
        if not config.discovery.enabled:
            print(f"⚠️  Discovery disabled for server: {server_id}")
            return None
        
        print(f"🔍 Discovering server: {config.name}")
        
        try:
            # Determine source path/URL
            if config.source.type == "local":
                source_path = config.source.path
            else:
                source_path = config.source.url
            
            # Perform discovery
            result = self.discovery_engine.discover(
                source_path,
                transport=config.source.transport,
                use_cache=True
            )
            
            # Save discovery results
            with open(config.discovery_path, 'w') as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
            
            # Update server configuration
            config.discovery.last_discovered = datetime.now()
            config.metadata.updated_at = datetime.now()
            
            with open(config.config_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
            
            print(f"✅ Discovery completed: {len(result.tools)} tools, {len(result.resources)} resources")
            print(f"   Discovery saved to: {config.discovery_path}")
            
            return result
            
        except Exception as e:
            print(f"❌ Discovery failed for {server_id}: {e}")
            return None
    
    def discover_all(
        self,
        server_type: Optional[str] = None,
        auth_required: Optional[bool] = None
    ) -> List[DiscoveryResult]:
        """
        Discover all servers matching criteria.
        
        Args:
            server_type: Only discover servers of this type
            auth_required: Only discover servers with this auth requirement
            
        Returns:
            List of discovery results
        """
        servers = self.list_servers(server_type=server_type, auth_required=auth_required)
        results = []
        
        print(f"🔍 Discovering {len(servers)} servers")
        
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
        config = self.get_server(server_id)
        if not config:
            print(f"❌ Server not found: {server_id}")
            return None
        
        if not config.generation.enabled:
            print(f"⚠️  Generation disabled for server: {server_id}")
            return None
        
        # Check if discovery results exist
        if not config.discovery_path.exists():
            print(f"❌ No discovery results found for {server_id}. Run discovery first.")
            return None
        
        print(f"🏗️  Generating mock server: {config.name}")
        
        try:
            # Load discovery results
            with open(config.discovery_path, 'r') as f:
                discovery_data = json.load(f)
            
            # Import generation modules
            from ai_generation.server_generator import generate_ai_mock_server
            
            # Generate mock server
            generate_ai_mock_server(discovery_data, config.generated_path)
            
            # Update server configuration
            config.generation.last_generated = datetime.now()
            config.metadata.updated_at = datetime.now()
            
            with open(config.config_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
            
            print(f"✅ Mock server generated")
            print(f"   Generated path: {config.generated_path}")
            print(f"   Files: server.py, tools.py")
            
            return str(config.generated_path)
            
        except Exception as e:
            print(f"❌ Generation failed for {server_id}: {e}")
            return None
    
    def generate_template(self, template_type: str = "config") -> str:
        """
        Generate template content for server configuration.
        
        Args:
            template_type: Type of template ("config" or "discovery")
            
        Returns:
            Template content as JSON string
        """
        if template_type == "config":
            return ServerConfig.generate_template()
        elif template_type == "discovery":
            # For discovery template, we can use the existing discovery result structure
            from ai_generation.discovery_models import DiscoveryResult
            return DiscoveryResult.generate_template()
        else:
            raise ValueError(f"Unknown template type: {template_type}")
    
    def save_template(self, template_type: str = "config", output_path: Optional[Path] = None):
        """
        Save template to file.
        
        Args:
            template_type: Type of template to save
            output_path: Where to save the template (defaults to templates directory)
        """
        if output_path is None:
            output_path = self.base_dir / "servers" / "templates" / f"{template_type}.json.template"
        
        template_content = self.generate_template(template_type)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        print(f"✅ Template saved: {output_path}")
    
    def update_templates(self):
        """Update all templates from current data models."""
        print("🔄 Updating templates from data models...")
        
        # Update config template
        self.save_template("config")
        
        # Update discovery template (if we implement it)
        # self.save_template("discovery")
        
        print("✅ All templates updated")
    
    def generate_all(
        self,
        server_type: Optional[str] = None,
        auth_required: Optional[bool] = None
    ) -> List[str]:
        """
        Generate mocks for all discovered servers.
        
        Args:
            server_type: Only generate for servers of this type
            auth_required: Only generate for servers with this auth requirement
            
        Returns:
            List of generated mock server paths
        """
        servers = self.list_servers(server_type=server_type, auth_required=auth_required)
        results = []
        
        print(f"🏗️  Generating mocks for {len(servers)} servers")
        
        for server_info in servers:
            server_id = server_info["id"]
            result = self.generate_mock(server_id)
            if result:
                results.append(result)
        
        print(f"✅ Generation completed: {len(results)}/{len(servers)} servers successful")
        return results
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server from the registry.
        
        Args:
            server_id: Server ID to remove
            
        Returns:
            True if successful
        """
        server_dir = self.servers_dir / server_id
        if not server_dir.exists():
            print(f"❌ Server not found: {server_id}")
            return False
        
        # Remove directory
        shutil.rmtree(server_dir)
        
        # Update registry
        self.registry.remove_server(server_id)
        self._save_registry()
        
        print(f"✅ Removed server: {server_id}")
        return True
    
    def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status for a server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Status information
        """
        config = self.get_server(server_id)
        if not config:
            return {"error": "Server not found"}
        
        return {
            "id": server_id,
            "name": config.name,
            "type": config.source.type,
            "source": config.source.url or config.source.path,
            "transport": config.source.transport,
            "auth_required": config.metadata.auth_required,
            "auth_type": config.metadata.auth_type,
            "category": config.metadata.category,
            "provider": config.metadata.provider,
            "discovery": {
                "enabled": config.discovery.enabled,
                "last_discovered": config.discovery.last_discovered,
                "has_results": config.discovery_path.exists()
            },
            "generation": {
                "enabled": config.generation.enabled,
                "last_generated": config.generation.last_generated,
                "output_dir": str(config.generated_path),
                "has_files": config.generated_path.exists()
            },
            "metadata": {
                "created_at": config.metadata.created_at,
                "updated_at": config.metadata.updated_at,
                "version": config.metadata.version
            }
        }
