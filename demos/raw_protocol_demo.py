"""
Show the actual raw JSON-RPC messages sent between client and server.
"""

import asyncio
import json
import subprocess
import sys


async def show_raw_protocol():
    """Show the actual JSON messages."""
    print("🔍 Raw MCP Protocol Messages")
    print("=" * 50)
    
    # Start the MCP server process
    process = subprocess.Popen(
        ["python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0  # Unbuffered
    )
    
    try:
        print("\n📡 Step 1: Initialize Request")
        print("-" * 30)
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "protocol-demo",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Client sends:")
        print(json.dumps(init_request, indent=2))
        
        # Send to server
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        init_response = json.loads(response_line.strip())
        
        print("\nServer responds:")
        print(json.dumps(init_response, indent=2))
        
        print("\n📋 Step 2: List Tools Request")
        print("-" * 30)
        
        # Send tools/list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("Client sends:")
        print(json.dumps(tools_request, indent=2))
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        tools_response = json.loads(response_line.strip())
        
        print("\nServer responds:")
        print(json.dumps(tools_response, indent=2))
        
        print("\n🔧 Step 3: Call Tool Request")
        print("-" * 30)
        
        # Send tool call request
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {
                    "a": 5,
                    "b": 3
                }
            }
        }
        
        print("Client sends:")
        print(json.dumps(call_request, indent=2))
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        call_response = json.loads(response_line.strip())
        
        print("\nServer responds:")
        print(json.dumps(call_response, indent=2))
        
        print("\n✅ Protocol Demo Complete!")
        
    finally:
        process.terminate()
        process.wait()


if __name__ == "__main__":
    asyncio.run(show_raw_protocol())
