#!/usr/bin/env python3
"""
Test direct server communication without MCP Inspector.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_server_direct(server_path: Path, working_dir: Path = None) -> dict:
    """Test MCP server with direct JSON-RPC communication."""
    
    # Determine command based on file extension
    if server_path.suffix == '.ts':
        cmd = ["npx", "tsx", str(server_path)]
    elif server_path.suffix == '.js':
        cmd = ["node", str(server_path)]
    elif server_path.suffix == '.py':
        cmd = ["python", str(server_path)]
    else:
        return {"error": f"Unsupported file type: {server_path.suffix}"}
    
    print(f"Testing: {' '.join(cmd)}")
    print(f"Working dir: {working_dir}")
    
    # Prepare JSON-RPC messages
    initialize_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"experimental": {}},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    tools_msg = {
        "jsonrpc": "2.0", 
        "id": 2, 
        "method": "tools/list",
        "params": {}
    }
    
    try:
        # Start server process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir
        )
        
        # Send messages
        input_data = json.dumps(initialize_msg) + "\n" + json.dumps(tools_msg) + "\n"
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        
        print(f"Exit code: {process.returncode}")
        print(f"STDERR: {stderr}")
        print(f"STDOUT lines: {len(stdout.splitlines())}")
        
        # Parse responses
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        responses = []
        tools = []
        
        for line in lines:
            if line.startswith('{"result"') or line.startswith('{"error"'):
                try:
                    response = json.loads(line)
                    responses.append(response)
                    
                    # Extract tools from tools/list response
                    if "result" in response and "tools" in response.get("result", {}):
                        tools = response["result"]["tools"]
                        
                except json.JSONDecodeError:
                    continue
        
        return {
            "success": True,
            "tools": tools,
            "responses": responses,
            "tool_count": len(tools)
        }
        
    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": "Server timeout"}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Test both servers."""
    base_dir = Path("/Users/samuelclark/Desktop/explore-mcp")
    
    # Test Gleanwork (TypeScript source)
    print("=" * 60)
    print("TESTING GLEANWORK MCP SERVER")
    print("=" * 60)
    
    gleanwork_path = base_dir / "mcp_registry/git_repos/gleanwork/packages/local-mcp-server/src/server.ts"
    if gleanwork_path.exists():
        result = test_server_direct(
            gleanwork_path, 
            working_dir=gleanwork_path.parent
        )
        print(f"Result: {result}")
    else:
        print("Gleanwork not found - need to add it first")
    
    print("\n")
    
    # Test Magic-MCP (built JavaScript)
    print("=" * 60)  
    print("TESTING MAGIC-MCP SERVER")
    print("=" * 60)
    
    magic_path = base_dir / "mcp_registry/git_repos/magic-mcp/dist/index.js"
    if magic_path.exists():
        result = test_server_direct(
            magic_path,
            working_dir=magic_path.parent.parent  # Go to repo root
        )
        print(f"Result: {result}")
    else:
        print("Magic-MCP not found - need to add it first")

if __name__ == "__main__":
    main()