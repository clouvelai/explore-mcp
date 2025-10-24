"""
Server Manager - Clean facade for MCP server management.

Provides a unified interface to all server operations while delegating
to specialized components. Uses dependency injection for testability
and maintains backward compatibility.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ai_generation.discovery import DiscoveryResult

from .discovery import ServerDiscoveryManager
from .exceptions import validate_server_id
from .generator import ServerGeneratorManager
from .models import DiscoveryConfig, GenerationConfig, ServerConfig, ServerMetadata, ServerSource
from .registry import ServerRegistryManager
from .tester import ServerTesterManager


class ServerManager:
    """
    Unified manager for all MCP servers.
    
    Clean facade that delegates to specialized components while maintaining
    the original API for backward compatibility.
    """
    
    def __init__(self, base_dir: str = "mcp_registry"):
        """Initialize with dependency injection."""
        self.base_dir = Path(base_dir)
        
        # Initialize core components with dependency injection
        self.registry = ServerRegistryManager(self.base_dir)
        self.discovery = ServerDiscoveryManager(self.registry)
        self.generator = ServerGeneratorManager(self.registry)
        self.tester = ServerTesterManager(self.registry)
        
        # Expose convenient references
        self.servers_dir = self.registry.servers_dir
    
    # ========== Registry Operations ==========
    
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
        source_type: Optional[str] = None
    ) -> str:
        """Add a new server to the registry."""
        validate_server_id(server_id)
        
        # Normalize source
        if isinstance(source, str):
            if source_type == "npm" or source.startswith("@"):
                server_source = ServerSource(type="npm", package=source)
            elif source.startswith("http"):
                server_source = ServerSource(type="remote", url=source)
            else:
                server_source = ServerSource(type="local", path=source)
        else:
            server_source = source
        
        # Create config using existing models
        config = ServerConfig(
            id=server_id,
            name=name,
            source=server_source,
            discovery=DiscoveryConfig(),
            generation=GenerationConfig(),
            metadata=ServerMetadata(
                description=description or f"{name} MCP server",
                category=category,
                provider=provider,
                auth_required=auth_required,
                auth_type=auth_type
            )
        )
        
        # Delegate to registry
        self.registry.add_server(server_id, config)
        
        print(f"✅ Server '{server_id}' added successfully")
        print(f"   Type: {server_source.type}")
        print(f"   Category: {category}")
        
        return server_id
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the registry."""
        success = self.registry.remove_server(server_id)
        if success:
            print(f"✅ Removed server '{server_id}' from registry")
        return success
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get a server configuration."""
        return self.registry.get_server(server_id)
    
    def list_servers(
        self,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        with_metadata: bool = False
    ) -> List[Union[ServerConfig, Dict[str, Any]]]:
        """List all servers in the registry."""
        servers = self.registry.list_servers(category)
        
        # Filter by source type if specified
        if source_type:
            servers = [s for s in servers if s.source.type == source_type]
        
        # Add metadata if requested (for CLI compatibility)
        if with_metadata:
            result = []
            for server in servers:
                server_dict = server.model_dump()
                server_dict["status"] = {
                    "discovered": server.discovery.last_discovered is not None,
                    "generated": server.generation.last_generated is not None
                }
                result.append(server_dict)
            return result
        
        return servers
    
    # ========== Discovery Operations ==========
    
    def discover_server(self, server_id: str) -> Optional[DiscoveryResult]:
        """Discover tools and resources for a specific server."""
        return self.discovery.discover_server(server_id)
    
    def discover_all(self, force: bool = False) -> Dict[str, DiscoveryResult]:
        """Discover all registered servers."""
        return self.discovery.discover_all(force=force, use_cache=not force)
    
    def discover_local_servers(self, mcp_servers_dir: str = "mcp_servers") -> List[Dict[str, Any]]:
        """Discover MCP servers in a local directory."""
        return self.discovery.discover_local_servers(mcp_servers_dir)
    
    def auto_discover_and_add_local_servers(
        self,
        mcp_servers_dir: str = "mcp_servers",
        dry_run: bool = False
    ) -> List[str]:
        """Auto-discover and add local servers."""
        return self.discovery.auto_discover_and_add(mcp_servers_dir, dry_run)
    
    # ========== Generation Operations ==========
    
    def generate_mock(self, server_id: str) -> Optional[str]:
        """Generate a mock server implementation."""
        return self.generator.generate_mock(server_id)
    
    def generate_all(self, force: bool = False) -> Dict[str, str]:
        """Generate mocks for all discovered servers."""
        # First discover all
        discoveries = self.discovery.discover_all(force=force)
        
        # Then generate
        return self.generator.generate_all(discoveries, force=force)
    
    def generate_template(self, template_type: str = "config") -> str:
        """Generate a template file."""
        return self.generator.generate_template(template_type)
    
    def save_template(self, template_type: str = "config", output_path: Optional[Path] = None):
        """Save a template to file."""
        return self.generator.save_template(template_type, output_path)
    
    def update_templates(self):
        """Update template files."""
        for template_type in ["config", "server"]:
            self.generator.save_template(template_type)
        print(f"✅ Updated template files")
    
    # ========== Testing Operations ==========
    
    def test_server(self, server_id: str) -> bool:
        """Run evaluation tests for a specific server."""
        return self.tester.test_server(server_id)
    
    def test_all(self, category: Optional[str] = None) -> Dict[str, bool]:
        """Test multiple servers."""
        if category:
            return self.tester.batch_test_by_category(category)
        else:
            return self.tester.test_all()
    
    # ========== Status and Utility Operations ==========
    
    def status(self) -> None:
        """Print comprehensive status of the registry."""
        servers = self.list_servers(with_metadata=True)
        
        discovered_count = sum(1 for s in servers if s.get("status", {}).get("discovered"))
        generated_count = sum(1 for s in servers if s.get("status", {}).get("generated"))
        
        print("📊 MCP Registry Status")
        print("=" * 50)
        print(f"Total Servers: {len(servers)}")
        print(f"Discovered: {discovered_count}")
        print(f"Generated: {generated_count}")
        
        # Group by category
        categories = {}
        for server in servers:
            category = server.get("metadata", {}).get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
        
        print(f"\n📁 Categories:")
        for category, count in categories.items():
            print(f"   {category}: {count}")
    
    def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """Get comprehensive status for a server."""
        config = self.get_server(server_id)
        if not config:
            return {"error": f"Server {server_id} not found"}
        
        return {
            "id": server_id,
            "name": config.name,
            "source": config.source.model_dump(),
            "category": config.metadata.category,
            "discovered": config.discovery.last_discovered is not None,
            "generated": config.generation.last_generated is not None,
            "discovery_info": {
                "last_discovered": config.discovery.last_discovered,
                "tools_count": config.discovery.tools_count,
                "resources_count": config.discovery.resources_count
            },
            "test_status": self.tester.get_test_status(server_id),
            "health": self.tester.validate_server_health(server_id)
        }
    
    def sync(self, force: bool = False) -> Dict[str, Any]:
        """Sync all servers: discover, generate, and test."""
        print("🔄 Starting full sync...")
        print("=" * 50)
        
        summary = {
            "started_at": datetime.now(),
            "discovered": 0,
            "generated": 0,
            "tested": 0,
            "failed": 0,
            "servers": {}
        }
        
        # Discover all servers
        print("📡 Phase 1: Discovery")
        discoveries = self.discovery.discover_all(force=force, use_cache=not force)
        summary["discovered"] = len(discoveries)
        
        # Generate mocks for discovered servers
        print("\n🤖 Phase 2: Generation")
        generated = self.generator.generate_all(discoveries, force=force)
        summary["generated"] = len(generated)
        
        # Test generated servers (optional)
        print("\n🧪 Phase 3: Testing")
        test_results = self.tester.test_all(list(generated.keys()))
        summary["tested"] = sum(1 for r in test_results.values() if r)
        
        # Track individual server status
        for server_id in self.registry.get_all_server_ids():
            status = {
                "discovered": server_id in discoveries,
                "generated": server_id in generated,
                "tested": test_results.get(server_id, False),
                "error": None
            }
            
            if not status["discovered"]:
                status["error"] = "Discovery failed"
                summary["failed"] += 1
            elif not status["generated"] and server_id in discoveries:
                status["error"] = "Generation failed"
                summary["failed"] += 1
            
            summary["servers"][server_id] = status
        
        summary["completed_at"] = datetime.now()
        summary["duration"] = (summary["completed_at"] - summary["started_at"]).total_seconds()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Sync Summary:")
        print(f"   ✅ Discovered: {summary['discovered']}")
        print(f"   🤖 Generated: {summary['generated']}")
        print(f"   🧪 Tested: {summary['tested']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⏱️  Duration: {summary['duration']:.1f}s")
        
        return summary