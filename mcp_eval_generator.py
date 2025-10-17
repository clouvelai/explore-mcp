#!/usr/bin/env python3
"""
MCP Evaluation Generator

Connects to an MCP server, discovers its tools, and generates:
1. A mock MCP server with identical tool signatures
2. An evaluation suite with test cases derived from tool schemas
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
from mcp_mock_generator import generate_ai_mock_responses
from mcp_test_generator import generate_ai_test_cases
from ai_service import test_claude_cli


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


def get_python_type(json_type: str, is_array: bool = False) -> str:
    """Convert JSON schema type to Python type annotation."""
    type_map = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "array": "list",
        "object": "dict"
    }
    python_type = type_map.get(json_type, "Any")
    if is_array:
        return f"List[{python_type}]"
    return python_type


def get_mock_value(param_type: str, param_name: str) -> Any:
    """Generate a mock value based on parameter type."""
    mock_values = {
        "string": f"test_{param_name}",
        "number": 42.0,
        "integer": 42,
        "boolean": True,
        "array": [1, 2, 3],
        "object": {"key": "value"}
    }
    return mock_values.get(param_type, f"mock_{param_name}")


def generate_mock_server(discovery_data: Dict[str, Any], output_path: str, use_ai: bool = False):
    """Generate a mock MCP server with discovered tool signatures."""
    print(f"🔨 Generating mock server: {output_path}")
    
    tools = discovery_data["tools"]
    
    # Generate AI responses if requested
    ai_responses = {}
    if use_ai:
        try:
            ai_responses = generate_ai_mock_responses(tools)
        except Exception as e:
            print(f"⚠️  AI generation failed, falling back to hardcoded responses: {e}")
            use_ai = False
    
    mock_code = '''#!/usr/bin/env python3
"""
Auto-generated Mock MCP Server
Generated from: {server_path}
Generated at: {timestamp}
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Suppress all output to stdout/stderr to avoid MCP protocol issues
logging.basicConfig(level=logging.CRITICAL, stream=sys.stderr)
logging.getLogger().setLevel(logging.CRITICAL)

# Create mock server instance
mcp = FastMCP("mock-server")

# Request log for verification
request_log = []

def log_request(tool_name: str, params: Dict[str, Any]):
    """Log tool requests for verification."""
    request_log.append({{
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "params": params
    }})
    # Don't print to stdout as it interferes with MCP stdio protocol

'''.format(
        server_path=discovery_data["server_path"],
        timestamp=discovery_data["discovered_at"]
    )
    
    # Generate tool functions
    for tool in tools:
        tool_name = tool["name"]
        description = tool["description"]
        schema = tool.get("inputSchema", {})
        
        # Parse parameters from schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Build parameter list
        params = []
        param_types = {}
        for param_name, param_schema in properties.items():
            param_type = param_schema.get("type", "string")
            
            # Handle arrays
            if param_type == "array":
                items_type = param_schema.get("items", {}).get("type", "Any")
                python_type = get_python_type(items_type, is_array=True)
            else:
                python_type = get_python_type(param_type)
            
            param_types[param_name] = param_type
            
            # Add optional annotation if not required
            if param_name not in required:
                python_type = f"Optional[{python_type}]"
                params.append(f"{param_name}: {python_type} = None")
            else:
                params.append(f"{param_name}: {python_type}")
        
        # Generate tool function
        params_str = ", ".join(params) if params else ""
        
        mock_code += f'''
@mcp.tool()
def {tool_name}({params_str}) -> str:
    """
    {description}
    """
    # Log the request
    log_request("{tool_name}", locals())
    
'''
        
        # Add basic validation for required parameters
        if required:
            mock_code += "    # Validate required parameters\n"
            for req_param in required:
                mock_code += f"    if {req_param} is None:\n"
                mock_code += f'        return "Error: Missing required parameter: {req_param}"\n'
            mock_code += "\n"
        
        # Add mock response based on AI generation or hardcoded patterns
        mock_code += "    # Return mock success response\n"
        
        # Use AI response if available, otherwise fall back to hardcoded patterns
        if use_ai and tool_name in ai_responses:
            ai_response = ai_responses[tool_name].replace('"', '\\"')  # Escape quotes
            mock_code += f'    return "{ai_response}"\n'
        else:
            # Generate realistic mock responses based on tool name patterns (hardcoded fallback)
            if "list" in tool_name.lower() and "file" in tool_name.lower():
                mock_code += '    return "Mock files: item1.txt, item2.pdf, item3.doc, item4.xlsx, item5.jpg"\n'
            elif "list" in tool_name.lower() and "folder" in tool_name.lower():
                mock_code += '    return "Mock folders: folder1/, folder2/, folder3/, folder4/, folder5/"\n'
            elif "list" in tool_name.lower() and ("message" in tool_name.lower() or "mail" in tool_name.lower() or "email" in tool_name.lower()):
                mock_code += '    return "Mock messages: [ID:001] Subject: First Message, [ID:002] Subject: Second Message, [ID:003] Subject: Third Message"\n'
            elif "list" in tool_name.lower() and "label" in tool_name.lower():
                mock_code += '    return "Mock labels: label1, label2, label3, label4, label5"\n'
            elif "list" in tool_name.lower():
                mock_code += '    return "Mock list: item1, item2, item3, item4, item5"\n'
            elif "search" in tool_name.lower():
                mock_code += '    return "Mock search results: Found 3 items matching query - result1, result2, result3"\n'
            elif "read" in tool_name.lower() and ("message" in tool_name.lower() or "mail" in tool_name.lower() or "email" in tool_name.lower()):
                mock_code += '    return "Mock message content: From: sender@example.com\\nTo: recipient@example.com\\nSubject: Mock Message\\nBody: This is mock message content."\n'
            elif "read" in tool_name.lower() and "file" in tool_name.lower():
                mock_code += '    return "Mock file content: This is the mock content of the file. Lorem ipsum dolor sit amet."\n'
            elif "read" in tool_name.lower() and "spreadsheet" in tool_name.lower():
                mock_code += '    return "Mock spreadsheet data: [[Header1, Header2, Header3], [Row1Col1, Row1Col2, Row1Col3], [Row2Col1, Row2Col2, Row2Col3]]"\n'
            elif "read" in tool_name.lower():
                mock_code += '    return "Mock content: This is mock content data."\n'
            elif "count" in tool_name.lower() or "get" in tool_name.lower() and "count" in tool_name.lower():
                mock_code += '    return "Mock count: 42"\n'
            elif "create" in tool_name.lower() or "add" in tool_name.lower():
                mock_code += '    return "Mock: Successfully created item with ID: mock_12345"\n'
            elif "send" in tool_name.lower():
                mock_code += '    return "Mock: Successfully sent with ID: mock_send_67890"\n'
            elif "update" in tool_name.lower() or "edit" in tool_name.lower() or "modify" in tool_name.lower():
                mock_code += '    return "Mock: Successfully updated item"\n'
            elif "mark" in tool_name.lower():
                mock_code += '    return "Mock: Successfully marked item"\n'
            elif "delete" in tool_name.lower() or "remove" in tool_name.lower():
                mock_code += '    return "Mock: Successfully deleted item"\n'
            elif "calculate" in tool_name.lower() or "compute" in tool_name.lower():
                mock_code += '    return "Mock calculation result: 42"\n'
            elif "sum" in tool_name.lower():
                mock_code += '    return "Mock sum result: 42"\n'
            elif "multiply" in tool_name.lower() or "product" in tool_name.lower():
                mock_code += '    return "Mock product result: 84"\n'
            elif "divide" in tool_name.lower() or "quotient" in tool_name.lower():
                mock_code += '    return "Mock division result: 21"\n'
            elif "subtract" in tool_name.lower() or "minus" in tool_name.lower():
                mock_code += '    return "Mock subtraction result: 8"\n'
            elif "info" in tool_name.lower() or "detail" in tool_name.lower() or "describe" in tool_name.lower():
                mock_code += '    return "Mock info: Name: Mock Item, Type: Mock Type, Size: 1.5MB, Modified: 2024-01-15"\n'
            elif "status" in tool_name.lower() or "state" in tool_name.lower():
                mock_code += '    return "Mock status: Active and operational"\n'
            else:
                mock_code += '    return "Mock: Operation completed successfully"\n'
    
    # Add server runner
    tool_names = [t["name"] for t in tools]
    mock_code += '''

@mcp.tool()
def get_request_log() -> str:
    """Get the log of all requests made to this mock server."""
    return json.dumps(request_log, indent=2)


if __name__ == "__main__":
    # Don't print to stdout as it interferes with MCP stdio protocol
    mcp.run(show_banner=False)
'''.format(tool_names)
    
    # Write to file
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(mock_code)
    
    print(f"✅ Mock server generated with {len(tools)} tools")


def generate_evaluations(discovery_data: Dict[str, Any], output_path: str, use_ai: bool = False):
    """Generate evaluation test cases from tool schemas."""
    print(f"📝 Generating evaluations: {output_path}")
    
    tools = discovery_data["tools"]
    evaluations = {
        "server_info": {
            "source": discovery_data["server_path"],
            "generated_at": discovery_data["discovered_at"],
            "tools_count": len(tools)
        },
        "evaluations": []
    }
    
    # Try AI generation first if requested
    if use_ai:
        try:
            ai_test_cases = generate_ai_test_cases(tools)
            if ai_test_cases:
                evaluations["evaluations"] = ai_test_cases
                
                # Write to file
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(evaluations, f, indent=2)
                
                total_tests = sum(len(t.get("test_cases", [])) for t in evaluations["evaluations"])
                print(f"✅ Generated {total_tests} AI test cases for {len(tools)} tools")
                return
        except Exception as e:
            print(f"⚠️  AI test case generation failed, falling back to hardcoded approach: {e}")
    
    for tool in tools:
        tool_name = tool["name"]
        description = tool["description"]
        schema = tool.get("inputSchema", {})
        
        # Parse schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        tool_tests = {
            "tool": tool_name,
            "description": description,
            "test_cases": []
        }
        
        # Generate valid test case
        if properties:
            valid_params = {}
            for param_name, param_schema in properties.items():
                param_type = param_schema.get("type", "string")
                valid_params[param_name] = get_mock_value(param_type, param_name)
            
            # Determine what the mock response should contain
            expected_contains = ["Mock"]
            if "list" in tool_name.lower() or "search" in tool_name.lower():
                expected_contains.append("result")
            elif "count" in tool_name.lower():
                expected_contains.append("42")
            elif "read" in tool_name.lower():
                expected_contains.append("content")
            elif "create" in tool_name.lower() or "send" in tool_name.lower():
                expected_contains.append("Successfully")
            else:
                expected_contains.append("successfully")
            
            tool_tests["test_cases"].append({
                "id": f"{tool_name}_valid",
                "type": "valid_params",
                "description": f"Valid parameters for {tool_name}",
                "params": valid_params,
                "expected_result": "success",
                "expected_contains": expected_contains
            })
        else:
            # Tool with no parameters
            expected_contains = ["Mock"]
            if "list" in tool_name.lower() or "search" in tool_name.lower():
                expected_contains.append("result")
            elif "count" in tool_name.lower():
                expected_contains.append("42")
            else:
                expected_contains.append("successfully")
                
            tool_tests["test_cases"].append({
                "id": f"{tool_name}_no_params",
                "type": "valid_params",
                "description": f"Call {tool_name} with no parameters",
                "params": {},
                "expected_result": "success",
                "expected_contains": expected_contains
            })
        
        # Generate missing required parameter tests
        for req_param in required:
            test_params = {}
            for param_name, param_schema in properties.items():
                if param_name != req_param:
                    param_type = param_schema.get("type", "string")
                    test_params[param_name] = get_mock_value(param_type, param_name)
            
            tool_tests["test_cases"].append({
                "id": f"{tool_name}_missing_{req_param}",
                "type": "missing_required",
                "description": f"Missing required parameter: {req_param}",
                "params": test_params,
                "expected_result": "error",
                "expected_contains": ["Error", "Missing", req_param]
            })
        
        # Generate wrong type test (if has parameters)
        if properties:
            wrong_type_params = {}
            param_to_break = list(properties.keys())[0]
            for param_name, param_schema in properties.items():
                if param_name == param_to_break:
                    # Intentionally use wrong type
                    param_type = param_schema.get("type", "string")
                    if param_type == "string":
                        wrong_type_params[param_name] = 12345  # number instead of string
                    elif param_type in ["number", "integer"]:
                        wrong_type_params[param_name] = "not_a_number"  # string instead of number
                    elif param_type == "boolean":
                        wrong_type_params[param_name] = "not_a_bool"  # string instead of bool
                    elif param_type == "array":
                        wrong_type_params[param_name] = "not_an_array"  # string instead of array
                    else:
                        wrong_type_params[param_name] = None
                else:
                    param_type = param_schema.get("type", "string")
                    wrong_type_params[param_name] = get_mock_value(param_type, param_name)
            
            tool_tests["test_cases"].append({
                "id": f"{tool_name}_wrong_type",
                "type": "invalid_type",
                "description": f"Wrong type for parameter: {param_to_break}",
                "params": wrong_type_params,
                "expected_result": "error",
                "expected_contains": ["Error", "type"]
            })
        
        # Add edge case test for string parameters
        if any(p.get("type") == "string" for p in properties.values()):
            edge_params = {}
            for param_name, param_schema in properties.items():
                param_type = param_schema.get("type", "string")
                if param_type == "string":
                    edge_params[param_name] = ""  # empty string
                else:
                    edge_params[param_name] = get_mock_value(param_type, param_name)
            
            tool_tests["test_cases"].append({
                "id": f"{tool_name}_empty_string",
                "type": "edge_case",
                "description": "Empty string parameters",
                "params": edge_params,
                "expected_result": "any",  # Could be valid or error depending on tool
                "expected_contains": []
            })
        
        evaluations["evaluations"].append(tool_tests)
    
    # Write to file
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(evaluations, f, indent=2)
    
    # Count total test cases
    total_tests = sum(len(t["test_cases"]) for t in evaluations["evaluations"])
    print(f"✅ Generated {total_tests} test cases for {len(tools)} tools")


async def main():
    parser = argparse.ArgumentParser(description="Generate mock MCP server and evaluations")
    parser.add_argument("--server", required=True, help="Path to MCP server to analyze")
    parser.add_argument("--output-dir", default="generated", help="Base output directory for generated files")
    parser.add_argument("--name", help="Name for the server (defaults to server filename without extension)")
    parser.add_argument("--use-agent", action="store_true", help="Use Claude AI agent for intelligent generation (requires claude CLI)")
    
    args = parser.parse_args()
    
    # Check Claude CLI availability if AI generation requested
    if args.use_agent:
        if not test_claude_cli():
            print("❌ Claude CLI not found or not working. Please install and configure Claude CLI.")
            print("   Try: pip install claude-cli")
            sys.exit(1)
        print("✅ Claude CLI available - AI generation enabled")
    
    # Determine server name for namespacing
    if args.name:
        server_name = args.name
    else:
        # Extract name from server path (e.g., "gmail_mcp_server.py" -> "gmail")
        server_filename = Path(args.server).stem
        server_name = server_filename.replace("_mcp_server", "").replace("_server", "").replace("server", "")
        if not server_name:
            server_name = "mcp"
    
    # Create namespaced output directory
    output_dir = Path(args.output_dir) / server_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Discover MCP server tools
        discovery_data = await discover_mcp_server(args.server)
        
        # Generate mock server
        mock_path = output_dir / "mock_server.py"
        generate_mock_server(discovery_data, str(mock_path), use_ai=args.use_agent)
        
        # Generate evaluations
        eval_path = output_dir / "evaluations.json"
        generate_evaluations(discovery_data, str(eval_path), use_ai=args.use_agent)
        
        print(f"\n✨ Generation complete for '{server_name}'!")
        print(f"   Mock server: {mock_path}")
        print(f"   Evaluations: {eval_path}")
        print(f"\nNext steps:")
        print(f"   1. Start mock server: uv run python {mock_path}")
        print(f"   2. Run evaluations: uv run python run_evaluations.py --evaluations {eval_path} --mock-server {mock_path}")
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())