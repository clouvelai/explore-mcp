#!/usr/bin/env python3
"""
MCP Mock Generator - Generates realistic mock responses for MCP tools.

Uses AI to create domain-appropriate responses based on tool schemas.
"""

import json
from typing import Dict, Any, List
from ai_service import AIService


# Prompt template for generating mock responses
MOCK_RESPONSES_PROMPT_TEMPLATE = """
I need you to generate realistic mock responses for MCP tools. Here are the tools:

{tools_json}

For each tool, generate a realistic mock response string that:
1. Reflects what the tool would actually return
2. Is appropriate for the tool's purpose based on its name and description
3. Includes realistic data (not just "mock_value")
4. Handles mathematical operations with actual calculations when possible

Return ONLY a JSON object mapping tool names to mock response strings. No other text.

Example format:
{{
  "tool_name": "realistic response string",
  "another_tool": "another realistic response"
}}
"""


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
    prompt = MOCK_RESPONSES_PROMPT_TEMPLATE.format(
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


if __name__ == "__main__":
    # Test with sample tools
    import sys
    from ai_service import test_claude_cli
    
    if not test_claude_cli():
        print("❌ Claude CLI not found or not working")
        sys.exit(1)
    
    # Sample tools for testing
    sample_tools = [
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
    
    print("Testing mock response generation...")
    responses = generate_ai_mock_responses(sample_tools)
    
    if responses:
        print("\nGenerated mock responses:")
        for tool_name, response in responses.items():
            print(f"  {tool_name}: {response}")
    else:
        print("Failed to generate mock responses")