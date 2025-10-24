"""
Server Tester - Handles evaluation and testing of MCP servers.

Manages the execution of evaluation suites against mock servers
to validate their functionality and generate test reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import handle_warning
from .models import ServerConfig
from .registry import ServerRegistryManager


class ServerTesterManager:
    """Manages server testing and evaluation."""
    
    def __init__(self, registry: ServerRegistryManager):
        """Initialize tester manager with dependency injection."""
        self.registry = registry
    
    def test_server(self, server_id: str) -> bool:
        """Run evaluation tests for a specific server."""
        config = self.registry.get_server(server_id)
        if not config:
            print(f"❌ Server not found: {server_id}")
            return False
        
        # Check if generated server and evaluations exist
        server_dir = self.registry.get_server_directory(server_id)
        generated_dir = server_dir / "generated"
        mock_server_path = generated_dir / "server.py"
        evaluations_path = generated_dir / "evaluations.json"
        
        if not mock_server_path.exists():
            print(f"❌ No generated mock server found for {server_id}")
            print(f"   Run 'mcp generate {server_id}' first")
            return False
        
        if not evaluations_path.exists():
            print(f"❌ No evaluations found for {server_id}")
            print(f"   Run 'mcp generate {server_id}' to create evaluations")
            return False
        
        print(f"🧪 Running tests for: {config.name}")
        
        # Run the evaluation
        return self._run_evaluations(mock_server_path, evaluations_path, config.name)
    
    def test_all(self, server_ids: Optional[List[str]] = None) -> Dict[str, bool]:
        """Test multiple servers."""
        if not server_ids:
            server_ids = self.registry.get_all_server_ids()
        
        results = {}
        passed = 0
        failed = 0
        
        print(f"🧪 Testing {len(server_ids)} servers...")
        print("=" * 50)
        
        for server_id in server_ids:
            result = self.test_server(server_id)
            results[server_id] = result
            
            if result:
                passed += 1
            else:
                failed += 1
        
        # Summary
        print("=" * 50)
        print(f"📊 Test Summary:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success Rate: {passed}/{len(server_ids)} ({passed*100//len(server_ids) if server_ids else 0}%)")
        
        return results
    
    def get_test_status(self, server_id: str) -> Dict[str, any]:
        """Get the current test status for a server."""
        config = self.registry.get_server(server_id)
        if not config:
            return {"status": "not_found", "server_id": server_id}
        
        server_dir = self.registry.get_server_directory(server_id)
        generated_dir = server_dir / "generated"
        mock_server_path = generated_dir / "server.py"
        evaluations_path = generated_dir / "evaluations.json"
        results_path = generated_dir / "test_results.json"
        
        status = {
            "server_id": server_id,
            "name": config.name,
            "has_mock": mock_server_path.exists(),
            "has_evaluations": evaluations_path.exists(),
            "has_results": results_path.exists(),
            "last_test": None,
            "last_result": None
        }
        
        # Load last test results if available
        if results_path.exists():
            try:
                with open(results_path, 'r') as f:
                    results = json.load(f)
                    status["last_test"] = results.get("timestamp")
                    status["last_result"] = results.get("passed", False)
            except Exception:
                pass
        
        return status
    
    def validate_server_health(self, server_id: str) -> Dict[str, any]:
        """Perform a comprehensive health check on a server."""
        health = {
            "server_id": server_id,
            "healthy": True,
            "issues": [],
            "warnings": []
        }
        
        # Check if server exists
        config = self.registry.get_server(server_id)
        if not config:
            health["healthy"] = False
            health["issues"].append("Server not found in registry")
            return health
        
        server_dir = self.registry.get_server_directory(server_id)
        
        # Check for discovery
        discovery_path = server_dir / "discovery.json"
        if not discovery_path.exists():
            health["healthy"] = False
            health["issues"].append("No discovery data - run 'mcp discover'")
        elif config.source.type == "local":
            # Check if source file exists
            server_path = Path(config.source.path)
            if not server_path.exists():
                health["healthy"] = False
                health["issues"].append(f"Source file not found: {config.source.path}")
        
        # Check for generation
        generated_dir = server_dir / "generated"
        if not (generated_dir / "server.py").exists():
            health["warnings"].append("No mock server generated - run 'mcp generate'")
        
        if not (generated_dir / "evaluations.json").exists():
            health["warnings"].append("No evaluations generated - run 'mcp generate'")
        
        # Check test results
        results_path = generated_dir / "test_results.json"
        if results_path.exists():
            try:
                with open(results_path, 'r') as f:
                    results = json.load(f)
                    if not results.get("passed", False):
                        health["warnings"].append("Last test run failed")
            except Exception:
                health["warnings"].append("Could not read test results")
        else:
            health["warnings"].append("No test results available - run 'mcp test'")
        
        return health
    
    def batch_test_by_category(self, category: str) -> Dict[str, bool]:
        """Test all servers in a specific category."""
        servers = self.registry.list_servers(category=category)
        server_ids = [s.id for s in servers]
        
        if not server_ids:
            print(f"No servers found in category: {category}")
            return {}
        
        print(f"🧪 Testing servers in category: {category}")
        return self.test_all(server_ids)
    
    def _run_evaluations(self, mock_server_path: Path, evaluations_path: Path, 
                        server_name: str) -> bool:
        """Run the actual evaluation process."""
        try:
            # Import evaluation runner
            from ai_generation.evaluation_runner import run_evaluations
            
            # Run evaluations
            result = run_evaluations(
                evaluations_file=str(evaluations_path),
                mock_server_file=str(mock_server_path)
            )
            
            # Save test results
            results_path = mock_server_path.parent / "test_results.json"
            with open(results_path, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "passed": result,
                    "server_name": server_name
                }, f, indent=2)
            
            if result:
                print(f"   ✅ All tests passed")
                return True
            else:
                print(f"   ❌ Some tests failed")
                return False
                
        except ImportError:
            print(f"   ❌ Evaluation runner not available")
            print(f"      Install required dependencies: pip install ai_generation")
            return False
        except Exception as e:
            print(f"   ❌ Test execution failed: {e}")
            return False