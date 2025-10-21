#!/usr/bin/env python3
"""
MCP Server Generator - Generates mock MCP servers with AI-powered responses.

Creates a server.py and tools.py matching the structure of real MCP servers.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from .ai_service import AIService
from .prompts import format_prompt




def generate_ai_mock_responses(tools: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Generate mock responses for tools using Claude.
    
    Args:
        tools: List of tool definitions with name, description, and schema
        
    Returns:
        Dictionary mapping tool names to mock response strings
    """
    print("🤖 Generating AI-powered mock responses...")
    
    # Prepare tool information for Claude
    tools_info = []
    for tool in tools:
        tool_info = {
            "name": tool["name"],
            "description": tool["description"],
            "schema": tool.get("inputSchema", {})
        }
        tools_info.append(tool_info)
    
    # Format the prompt
    prompt = format_prompt(
        "mock_responses",
        tools_json=json.dumps(tools_info, indent=2)
    )
    
    try:
        # Use AIService to generate response
        service = AIService()
        mock_responses = service.generate_json(prompt)
        
        print(f"✅ Generated {len(mock_responses)} AI mock responses")
        return mock_responses
    
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse Claude response as JSON: {e}")
        return {}
    except Exception as e:
        print(f"⚠️  Error generating AI mock responses: {e}")
        return {}


def generate_ai_mock_resource_content(resources: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Generate mock content for resources using Claude.
    
    Args:
        resources: List of resource definitions with uri, name, description
        
    Returns:
        Dictionary mapping resource names to mock content strings
    """
    if not resources:
        return {}
        
    print("🤖 Generating AI-powered mock resource content...")
    
    # Prepare resource information for Claude
    resources_info = []
    for resource in resources:
        resource_info = {
            "uri": resource["uri"],
            "name": resource["name"],
            "description": resource["description"],
            "mimeType": resource.get("mimeType", "text/plain")
        }
        resources_info.append(resource_info)
    
    # Format the prompt (we'll create a resource-specific prompt)
    prompt = format_prompt(
        "mock_resource_content",
        resources_json=json.dumps(resources_info, indent=2)
    )
    
    try:
        # Use AIService to generate response
        service = AIService()
        mock_content = service.generate_json(prompt)
        
        print(f"✅ Generated {len(mock_content)} AI mock resource content")
        return mock_content
    
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse Claude response as JSON: {e}")
        return {}
    except Exception as e:
        print(f"⚠️  Error generating AI mock resource content: {e}")
        return {}


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


def generate_tools_py(discovery_data: Dict[str, Any], output_dir: Path):
    """Generate tools.py with AI-powered mock implementations."""
    print("🔨 Generating tools.py...")
    
    tools = discovery_data["tools"]
    resources = discovery_data.get("resources", [])
    
    # Generate AI responses for tools
    ai_responses = generate_ai_mock_responses(tools)
    
    # Generate AI content for resources
    ai_resource_content = generate_ai_mock_resource_content(resources)
    
    # Start building tools.py content
    tools_code = '''"""
Auto-generated MCP Tools
Generated from: {server_path}
Generated at: {timestamp}
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Request log for verification
request_log = []


def log_request(tool_name: str, params: Dict[str, Any]):
    """Log tool requests for verification."""
    request_log.append({{
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "params": params
    }})


def register_tools(mcp: FastMCP):
    """Register all tools with the MCP server."""
    
'''.format(
        server_path=discovery_data["server_path"],
        timestamp=discovery_data["metadata"]["discovered_at"]
    )
    
    # Generate each tool function
    for tool in tools:
        tool_name = tool["name"]
        description = tool["description"]
        schema = tool.get("inputSchema", {})
        
        # Parse parameters from schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Build parameter list
        params = []
        for param_name, param_schema in properties.items():
            param_type = param_schema.get("type", "string")
            
            # Handle arrays
            if param_type == "array":
                items_type = param_schema.get("items", {}).get("type", "Any")
                python_type = get_python_type(items_type, is_array=True)
            else:
                python_type = get_python_type(param_type)
            
            # Add optional annotation if not required
            if param_name not in required:
                python_type = f"Optional[{python_type}]"
                params.append(f"{param_name}: {python_type} = None")
            else:
                params.append(f"{param_name}: {python_type}")
        
        # Generate tool function
        params_str = ", ".join(params) if params else ""
        
        tools_code += f'''    @mcp.tool()
    def {tool_name}({params_str}) -> str:
        """
        {description}
        """
        # Log the request
        log_request("{tool_name}", locals())
        
'''
        
        # Add validation for required parameters
        if required:
            tools_code += "        # Validate required parameters\n"
            for req_param in required:
                tools_code += f"        if {req_param} is None:\n"
                tools_code += f'            return "Error: Missing required parameter: {req_param}"\n'
            tools_code += "\n"
        
        # Add AI-generated mock response
        tools_code += "        # Return mock response\n"
        if tool_name in ai_responses:
            # Properly escape the response string
            ai_response = ai_responses[tool_name].replace('\\', '\\\\').replace('"', '\\"')
            tools_code += f'        return "{ai_response}"\n\n'
        else:
            # Fallback if AI didn't generate a response for this tool
            tools_code += f'        return "Mock response for {tool_name}"\n\n'
    
    # Add resource generation if any resources were discovered
    if resources:
        tools_code += '''

def register_resources(mcp: FastMCP):
    """Register all resources with the MCP server."""
    
'''
        
        # Generate each resource function (static resources only)
        for resource in resources:
            resource_name = resource["name"]
            description = resource["description"]
            uri = resource["uri"]
            
            # Generate static resource
            tools_code += f'''    @mcp.resource("{uri}")
    def {resource_name}() -> str:
        """
        {description}
        """
'''
            
            # Add AI-generated mock content
            tools_code += "        # Return mock content\n"
            if resource_name in ai_resource_content:
                # Properly escape the content string
                ai_content = ai_resource_content[resource_name].replace('\\', '\\\\').replace('"', '\\"')
                tools_code += f'        return "{ai_content}"\n\n'
            else:
                # Fallback if AI didn't generate content for this resource
                tools_code += f'        return "Mock content for {resource_name}"\n\n'

    # Add request log tool
    tools_code += '''    @mcp.tool()
    def get_request_log() -> str:
        """Get the log of all requests made to this mock server."""
        return json.dumps(request_log, indent=2)
'''
    
    # Write tools.py
    tools_path = output_dir / "tools.py"
    with open(tools_path, "w") as f:
        f.write(tools_code)
    
    resource_count = len(resources)
    print(f"✅ Generated tools.py with {len(tools)} tools" + (f" and {resource_count} resources" if resource_count > 0 else ""))


def generate_server_py(discovery_data: Dict[str, Any], output_dir: Path):
    """Generate server.py that imports and runs the tools."""
    print("🔨 Generating server.py...")
    
    resources = discovery_data.get("resources", [])
    has_resources = len(resources) > 0
    
    imports = "from tools import register_tools"
    if has_resources:
        imports += ", register_resources"
    
    registration = "# Register all tools\nregister_tools(mcp)"
    if has_resources:
        registration += "\n\n# Register all resources\nregister_resources(mcp)"
    
    server_code = f'''#!/usr/bin/env python3
"""
Auto-generated Mock MCP Server
"""

import logging
import sys

# Suppress output to avoid MCP protocol issues
logging.basicConfig(level=logging.CRITICAL, stream=sys.stderr)
logging.getLogger().setLevel(logging.CRITICAL)

from fastmcp import FastMCP
{imports}

# Create mock server instance
mcp = FastMCP("mock-server")

{registration}

if __name__ == "__main__":
    # Run the server
    mcp.run(show_banner=False)
'''
    
    # Write server.py
    server_path = output_dir / "server.py"
    with open(server_path, "w") as f:
        f.write(server_code)
    
    print("✅ Generated server.py")


def generate_ai_mock_server(discovery_data: Dict[str, Any], output_dir: Path):
    """
    Generate a complete mock MCP server with server.py and tools.py structure.
    
    Args:
        discovery_data: Server discovery information including tools and resources
        output_dir: Directory to write the generated files
    """
    print(f"📦 Generating mock server in: {output_dir}")
    
    # Generate tools.py with AI-powered responses
    generate_tools_py(discovery_data, output_dir)
    
    # Generate server.py
    generate_server_py(discovery_data, output_dir)
    
    tools_count = len(discovery_data['tools'])
    resources_count = len(discovery_data.get('resources', []))
    
    message = f"✅ Mock server generated with {tools_count} tools"
    if resources_count > 0:
        message += f" and {resources_count} resources"
    print(message)


if __name__ == "__main__":
    # Test with sample tools
    import sys
    from .ai_service import test_claude_cli
    
    if not test_claude_cli():
        print("❌ Claude CLI not found or not working")
        sys.exit(1)
    
    # Sample discovery data for testing
    sample_discovery = {
        "server_path": "test_server.py",
        "discovered_at": "2024-01-01T00:00:00",
        "tools": [
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "list_files",
                "description": "List files in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    }
                }
            }
        ]
    }
    
    print("Testing mock server generation...")
    output_dir = Path("test_generated")
    output_dir.mkdir(exist_ok=True)
    
    generate_ai_mock_server(sample_discovery, output_dir)
    
    print(f"\nGenerated files in {output_dir}:")
    print(f"  - server.py")
    print(f"  - tools.py")