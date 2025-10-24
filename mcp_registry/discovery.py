"""
Server Discovery - Handles all MCP server discovery operations.

Manages server discovery through MCP Inspector, local scanning,
and caching with intelligent cache invalidation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ai_generation.discovery import DiscoveryEngine, DiscoveryResult

from .exceptions import DiscoveryError, DirectoryNotFoundError, FileOperationError, handle_warning
from .local_scanner import LocalServerScanner
from .models import ServerConfig
from .registry import ServerRegistryManager


class ServerDiscoveryManager:
    """Manages all server discovery operations."""
    
    def __init__(self, registry: ServerRegistryManager, 
                 discovery_engine: Optional[DiscoveryEngine] = None,
                 local_scanner: Optional[LocalServerScanner] = None):
        """Initialize discovery manager with dependency injection."""
        self.registry = registry
        self.discovery_engine = discovery_engine or DiscoveryEngine()
        self.local_scanner = local_scanner or LocalServerScanner()
    
    def discover_server(self, server_id: str, use_cache: bool = True) -> Optional[DiscoveryResult]:
        """Discover tools and resources for a specific server."""
        config = self.registry.get_server(server_id)
        if not config:
            handle_warning(f"Server not found", server_id)
            return None
        
        print(f"🔍 Discovering server: {config.name}")
        
        # Check for cached discovery
        if use_cache:
            cached_result = self._get_cached_discovery(server_id, config)
            if cached_result:
                print(f"✅ Using cached discovery for {config.name}")
                return cached_result
        
        # Perform new discovery
        try:
            result = self._perform_discovery(config)
            self._save_discovery_result(server_id, config, result)
            
            print(f"✅ Discovery complete for {config.name}")
            print(f"   Found {len(result.tools)} tools, {len(result.resources)} resources")
            
            return result
            
        except Exception as e:
            raise DiscoveryError(f"Discovery failed for {server_id}: {e}")
    
    def discover_all(self, force: bool = False, use_cache: bool = True) -> Dict[str, DiscoveryResult]:
        """Discover all registered servers."""
        results = {}
        server_ids = self.registry.get_all_server_ids()
        
        print(f"🔍 Discovering {len(server_ids)} servers...")
        
        for server_id in server_ids:
            try:
                # Force rediscovery if requested
                cache_enabled = use_cache and not force
                
                result = self.discover_server(server_id, use_cache=cache_enabled)
                if result:
                    results[server_id] = result
                    
            except DiscoveryError as e:
                handle_warning(f"Discovery failed: {e}", server_id)
            except Exception as e:
                handle_warning(f"Unexpected error during discovery: {e}", server_id)
        
        print(f"✅ Discovery complete: {len(results)}/{len(server_ids)} succeeded")
        return results
    
    def discover_local_servers(self, mcp_servers_dir: str = "mcp_servers") -> List[Dict[str, any]]:
        """Discover MCP servers in a local directory."""
        servers_path = Path(mcp_servers_dir)
        
        if not servers_path.exists():
            raise DirectoryNotFoundError(str(servers_path))
        
        try:
            discovered_servers = self.local_scanner.discover_servers(servers_path)
            
            print(f"🔍 Found {len(discovered_servers)} local servers in {mcp_servers_dir}")
            for server in discovered_servers:
                print(f"   - {server['name']}: {server['server_file']}")
            
            return discovered_servers
            
        except DirectoryNotFoundError:
            raise
        except Exception as e:
            handle_warning(f"Failed to discover local servers: {e}", mcp_servers_dir)
            return []
    
    def auto_discover_and_add(self, mcp_servers_dir: str = "mcp_servers", 
                             dry_run: bool = False) -> List[str]:
        """Auto-discover and add local servers to registry."""
        from .models import ServerSource, ServerMetadata, DiscoveryConfig, GenerationConfig
        
        discovered = self.discover_local_servers(mcp_servers_dir)
        added_servers = []
        
        for server_info in discovered:
            server_id = server_info['name']
            
            # Skip if already registered
            if self.registry.server_exists(server_id):
                print(f"   ⏭️  {server_id} already registered")
                continue
            
            if dry_run:
                print(f"   🔍 Would add: {server_id}")
                added_servers.append(server_id)
            else:
                # Create server config from discovered info
                config = ServerConfig(
                    id=server_id,
                    name=server_info['name'],
                    source=ServerSource(
                        type="local",
                        path=server_info['server_file']
                    ),
                    discovery=DiscoveryConfig(),
                    generation=GenerationConfig(),
                    metadata=ServerMetadata(
                        description=server_info.get('description', f"{server_id} MCP server"),
                        category="Auto-discovered"
                    )
                )
                
                self.registry.add_server(server_id, config)
                print(f"   ✅ Added: {server_id}")
                added_servers.append(server_id)
        
        return added_servers
    
    def _get_cached_discovery(self, server_id: str, config: ServerConfig) -> Optional[DiscoveryResult]:
        """Get cached discovery if it's still valid."""
        discovery_file = self.registry.get_server_directory(server_id) / "discovery.json"
        
        if not discovery_file.exists():
            return None
        
        if not self._is_discovery_current(config, discovery_file):
            return None
        
        try:
            with open(discovery_file, 'r') as f:
                data = json.load(f)
            return DiscoveryResult(**data)
        except Exception as e:
            handle_warning(f"Failed to load cached discovery: {e}", server_id)
            return None
    
    def _perform_discovery(self, config: ServerConfig) -> DiscoveryResult:
        """Perform actual discovery using the discovery engine."""
        # Determine source path/URL
        if config.source.type == "local":
            source = config.source.path
        elif config.source.type == "remote":
            source = config.source.url
        elif config.source.type == "npm":
            source = config.source.package
        else:
            raise DiscoveryError(f"Unknown source type: {config.source.type}")
        
        # Use discovery engine
        return self.discovery_engine.discover(
            source,
            transport=config.source.transport or "stdio",
            use_cache=False  # We handle caching at this level
        )
    
    def _save_discovery_result(self, server_id: str, config: ServerConfig, 
                               result: DiscoveryResult) -> None:
        """Save discovery result and update config."""
        discovery_file = self.registry.get_server_directory(server_id) / "discovery.json"
        
        # Save discovery result
        try:
            with open(discovery_file, 'w') as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
        except Exception as e:
            raise FileOperationError(str(discovery_file), "write", str(e))
        
        # Update config with discovery metadata
        config.discovery.last_discovered = datetime.now()
        config.discovery.tools_count = len(result.tools)
        config.discovery.resources_count = len(result.resources)
        config.discovery.prompts_count = len(result.prompts)
        
        # Save updated config
        self.registry.update_server(server_id, config)
    
    def _is_discovery_current(self, config: ServerConfig, discovery_file: Path) -> bool:
        """Check if cached discovery is still current."""
        # For local servers, check if file has changed
        if config.source.type == "local":
            server_path = Path(config.source.path)
            if server_path.exists():
                file_mtime = server_path.stat().st_mtime
                cache_mtime = discovery_file.stat().st_mtime
                if file_mtime > cache_mtime:
                    return False
        
        # For remote/npm servers, check if discovery is recent (within 1 hour)
        if config.source.type in ["remote", "npm"]:
            cache_age = datetime.now().timestamp() - discovery_file.stat().st_mtime
            if cache_age > 3600:  # 1 hour
                return False
        
        return True