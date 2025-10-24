"""
Server Generator - Handles mock server and evaluation generation.

Manages the generation of mock MCP servers and evaluation suites
using AI-powered generation services with intelligent caching.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ai_generation.discovery import DiscoveryResult

from .exceptions import FileOperationError, handle_warning
from .models import ServerConfig
from .registry import ServerRegistryManager


class ServerGeneratorManager:
    """Manages mock server and evaluation generation."""
    
    def __init__(self, registry: ServerRegistryManager):
        """Initialize generator manager with dependency injection."""
        self.registry = registry
    
    def generate_mock(self, server_id: str, discovery_result: Optional[DiscoveryResult] = None,
                     force: bool = False) -> Optional[str]:
        """Generate a mock server implementation."""
        config = self.registry.get_server(server_id)
        if not config:
            handle_warning(f"Server not found", server_id)
            return None
        
        # Check if generation is needed
        generated_dir = self.registry.get_server_directory(server_id) / "generated"
        mock_server_path = generated_dir / "server.py"
        
        if mock_server_path.exists() and not force:
            if self._is_generation_current(server_id, config):
                print(f"✅ Mock server already up-to-date for {config.name}")
                return str(mock_server_path)
        
        print(f"🤖 Generating mock server for: {config.name}")
        
        # Load discovery result if not provided
        if not discovery_result:
            discovery_result = self._load_discovery_result(server_id)
            if not discovery_result:
                handle_warning(f"Discovery not found - run discovery first", server_id)
                return None
        
        # Generate mock server and evaluations
        try:
            self._run_generation(server_id, config, discovery_result)
            
            # Update config with generation info
            config.generation.last_generated = datetime.now()
            self.registry.update_server(server_id, config)
            
            print(f"✅ Generation complete for {config.name}")
            return str(mock_server_path)
            
        except Exception as e:
            handle_warning(f"Generation failed: {e}", server_id)
            return None
    
    def generate_all(self, discovered_servers: Dict[str, DiscoveryResult], 
                    force: bool = False) -> Dict[str, str]:
        """Generate mocks for multiple servers."""
        generated = {}
        
        print(f"🤖 Generating mocks for {len(discovered_servers)} servers...")
        
        for server_id, discovery_result in discovered_servers.items():
            mock_path = self.generate_mock(server_id, discovery_result, force=force)
            if mock_path:
                generated[server_id] = mock_path
        
        print(f"✅ Generation complete: {len(generated)}/{len(discovered_servers)} succeeded")
        return generated
    
    def generate_template(self, template_type: str = "config") -> str:
        """Generate a template file."""
        templates = {
            "config": self._generate_config_template(),
            "server": self._generate_server_template(),
            "evaluation": self._generate_evaluation_template()
        }
        
        return templates.get(template_type, self._generate_config_template())
    
    def save_template(self, template_type: str = "config", 
                     output_path: Optional[Path] = None) -> Path:
        """Save a template to file."""
        content = self.generate_template(template_type)
        
        if not output_path:
            output_path = self.registry.base_dir / f"template_{template_type}.json"
        
        output_path.write_text(content)
        print(f"✅ Template saved to: {output_path}")
        
        return output_path
    
    def _load_discovery_result(self, server_id: str) -> Optional[DiscoveryResult]:
        """Load discovery result from file."""
        discovery_file = self.registry.get_server_directory(server_id) / "discovery.json"
        if not discovery_file.exists():
            return None
        
        try:
            with open(discovery_file, 'r') as f:
                data = json.load(f)
            return DiscoveryResult(**data)
        except Exception as e:
            handle_warning(f"Failed to load discovery: {e}", server_id)
            return None
    
    def _is_generation_current(self, server_id: str, config: ServerConfig) -> bool:
        """Check if existing generation is current."""
        if not config.generation.last_generated:
            return False
        
        # Check if discovery is newer than generation
        discovery_file = self.registry.get_server_directory(server_id) / "discovery.json"
        if discovery_file.exists():
            discovery_mtime = discovery_file.stat().st_mtime
            generation_timestamp = config.generation.last_generated.timestamp()
            if discovery_mtime > generation_timestamp:
                return False
        
        return True
    
    def _run_generation(self, server_id: str, config: ServerConfig, 
                       discovery_result: DiscoveryResult) -> None:
        """Run the actual generation process."""
        generated_dir = self.registry.get_server_directory(server_id) / "generated"
        generated_dir.mkdir(exist_ok=True)
        
        # Save discovery for generator to use
        discovery_file = generated_dir / "discovery_input.json"
        with open(discovery_file, 'w') as f:
            json.dump(discovery_result.model_dump(), f, indent=2, default=str)
        
        # Run server generator
        try:
            from ai_generation.server_generator import generate_mock_server
            
            mock_code = generate_mock_server(
                discovery_file=str(discovery_file),
                server_name=config.name
            )
            
            # Save mock server
            mock_server_path = generated_dir / "server.py"
            mock_server_path.write_text(mock_code)
            
            # Also create tools.py for compatibility
            tools_path = generated_dir / "tools.py"
            tools_code = self._extract_tools_module(mock_code)
            tools_path.write_text(tools_code)
            
        except ImportError:
            raise FileOperationError(str(generated_dir), "generate", "AI generation service not available")
        except Exception as e:
            raise FileOperationError(str(generated_dir), "generate", str(e))
        
        # Run evaluations generator
        try:
            from ai_generation.evals_generator import generate_evaluations
            
            evaluations = generate_evaluations(
                discovery_file=str(discovery_file),
                server_name=config.name
            )
            
            # Save evaluations
            evaluations_path = generated_dir / "evaluations.json"
            evaluations_path.write_text(evaluations)
            
        except ImportError:
            handle_warning("Evaluations generator not available", server_id)
        except Exception as e:
            handle_warning(f"Failed to generate evaluations: {e}", server_id)
    
    def _extract_tools_module(self, mock_code: str) -> str:
        """Extract tools into a separate module for compatibility."""
        return '''"""
Generated tools module for compatibility.
"""

from .server import mcp

# Tools are defined in server.py
'''
    
    def _generate_config_template(self) -> str:
        """Generate a server config template."""
        template = {
            "id": "example-server",
            "name": "Example Server",
            "source": {
                "type": "local",
                "path": "path/to/server.py"
            },
            "metadata": {
                "description": "An example MCP server",
                "category": "General",
                "provider": "Local"
            }
        }
        
        return json.dumps(template, indent=2)
    
    def _generate_server_template(self) -> str:
        """Generate a basic MCP server template."""
        return '''#!/usr/bin/env python3
"""
Example MCP Server
"""

from fastmcp import FastMCP

mcp = FastMCP("example-server")

@mcp.tool()
def example_tool(input: str) -> str:
    """An example tool."""
    return f"Processed: {input}"

if __name__ == "__main__":
    mcp.run()
'''
    
    def _generate_evaluation_template(self) -> str:
        """Generate an evaluation template."""
        template = {
            "evaluations": [
                {
                    "name": "test_example_tool",
                    "tool": "example_tool",
                    "inputs": {"input": "test"},
                    "expected_output": "Processed: test"
                }
            ]
        }
        
        return json.dumps(template, indent=2)