#!/usr/bin/env python3
"""
MCP Generator - Main orchestrator for generating mock MCP servers and evaluations.

Connects to an MCP server, discovers its tools, and generates:
1. A mock MCP server with AI-generated responses (server.py + tools.py structure)
2. An evaluation suite with AI-generated test cases
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .server_generator import generate_ai_mock_server
from .evals_generator import generate_ai_test_cases
from .ai_service import test_claude_cli


async def discover_mcp_server(server_path: str) -> Dict[str, Any]:
    """Connect to an MCP server and discover its tools."""
    print(f"🔍 Discovering tools from: {server_path}")
    
    # Prepare server parameters
    server_params = StdioServerParameters(
        command="python",
        args=[server_path],
        env=dict(os.environ)  # Pass through environment for auth tokens
    )
    
    tools_data = []
    prompts_data = []
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                print("✅ Connected to MCP server")
                
                # Get tools
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    tools_data.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    })
                
                # Get prompts (if any)
                try:
                    prompts_response = await session.list_prompts()
                    for prompt in prompts_response.prompts:
                        prompts_data.append({
                            "name": prompt.name,
                            "description": prompt.description
                        })
                except:
                    pass  # Server may not have prompts
                
                print(f"📊 Discovered {len(tools_data)} tools and {len(prompts_data)} prompts")
                
    except Exception as e:
        print(f"❌ Error discovering server: {e}")
        raise
    
    return {
        "server_path": server_path,
        "tools": tools_data,
        "prompts": prompts_data,
        "discovered_at": datetime.now().isoformat()
    }


def extract_server_name(server_path: str) -> str:
    """Extract a clean server name from the server path."""
    path = Path(server_path)
    
    # Check if it's in the mcp_servers directory structure
    # e.g., mcp_servers/calculator/server.py -> calculator
    parts = path.parts
    if len(parts) >= 3 and parts[-3] == "mcp_servers" and parts[-1] == "server.py":
        return parts[-2]  # Return the directory name (e.g., "calculator")
    
    # Otherwise, extract from filename
    # Remove common suffixes and clean up
    filename = path.stem
    for suffix in ["_mcp_server", "_server", "server"]:
        filename = filename.replace(suffix, "")
    
    # If we end up with an empty string, use the parent directory name or "mcp"
    if not filename:
        if path.parent.name and path.parent.name != ".":
            return path.parent.name
        return "mcp"
    
    return filename


def generate_evaluations(discovery_data: Dict[str, Any], output_dir: Path):
    """Generate AI-powered evaluation test cases."""
    print(f"📝 Generating evaluations...")
    
    tools = discovery_data["tools"]
    
    # Generate AI test cases
    ai_test_cases = generate_ai_test_cases(tools)
    
    # Wrap in evaluation structure
    evaluations = {
        "server_info": {
            "source": discovery_data["server_path"],
            "generated_at": discovery_data["discovered_at"],
            "tools_count": len(tools)
        },
        "evaluations": ai_test_cases
    }
    
    # Write to file
    eval_path = output_dir / "evaluations.json"
    with open(eval_path, "w") as f:
        json.dump(evaluations, f, indent=2)
    
    total_tests = sum(len(t.get("test_cases", [])) for t in evaluations["evaluations"])
    print(f"✅ Generated {total_tests} AI test cases for {len(tools)} tools")
    return eval_path


async def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered mock MCP server and evaluations"
    )
    parser.add_argument(
        "--server", 
        required=True, 
        help="Path to MCP server to analyze"
    )
    parser.add_argument(
        "--output-dir", 
        default="generated", 
        help="Base output directory for generated files"
    )
    parser.add_argument(
        "--name", 
        help="Name for the server (auto-detected if not provided)"
    )
    
    args = parser.parse_args()
    
    # Check Claude CLI availability
    if not test_claude_cli():
        print("❌ Claude CLI not found or not working.")
        print("   Please install and configure Claude CLI:")
        print("   https://docs.anthropic.com/claude/docs/claude-cli")
        sys.exit(1)
    print("✅ Claude CLI available - AI generation ready")
    
    # Determine server name
    if args.name:
        server_name = args.name
    else:
        server_name = extract_server_name(args.server)
    
    print(f"📦 Server name: {server_name}")
    
    # Create output directory
    output_dir = Path(args.output_dir) / server_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Discover MCP server tools
        discovery_data = await discover_mcp_server(args.server)
        
        # Generate mock server with server.py + tools.py structure
        generate_ai_mock_server(discovery_data, output_dir)
        
        # Generate evaluations
        eval_path = generate_evaluations(discovery_data, output_dir)
        
        print(f"\n✨ Generation complete for '{server_name}'!")
        print(f"   Output directory: {output_dir}")
        print(f"   Mock server: {output_dir}/server.py")
        print(f"   Tools: {output_dir}/tools.py")
        print(f"   Evaluations: {eval_path}")
        print(f"\nNext steps:")
        print(f"   1. Start mock server: uv run python {output_dir}/server.py")
        print(f"   2. Run evaluations: uv run python run_evaluations.py --evaluations {eval_path} --mock-server {output_dir}/server.py")
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())