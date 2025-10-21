#!/usr/bin/env python3
"""
MCP Test Generator - Generates comprehensive test cases for MCP tools.

Uses AI to create intelligent test cases including edge cases and domain-specific scenarios.
"""

import json
from typing import Dict, Any, List
from .ai_service import AIService
from .prompts import format_prompt




def generate_ai_test_cases(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate intelligent test cases using Claude.
    
    Args:
        tools: List of tool definitions with name, description, and schema
        
    Returns:
        List of test case definitions for each tool
    """
    print("🤖 Generating AI-powered test cases...")
    
    # Prepare tool information for Claude
    tools_info = []
    for tool in tools:
        tool_info = {
            "name": tool["name"],
            "description": tool["description"],
            "schema": tool.get("inputSchema", {})
        }
        tools_info.append(tool_info)
    
    # Try bulk generation first
    try:
        return _generate_bulk_test_cases(tools_info)
    except Exception as e:
        print(f"⚠️  Bulk generation failed: {e}")
        print("🔄 Falling back to per-tool generation...")
        return _generate_per_tool_test_cases(tools_info)


def _generate_bulk_test_cases(tools_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate test cases for all tools at once."""
    # Format the prompt
    prompt = format_prompt(
        "test_cases",
        tools_json=json.dumps(tools_info, indent=2)
    )
    
    # Use AIService to generate response
    service = AIService()
    test_cases = service.generate_json(prompt)
    
    # Validate that we got a list
    if not isinstance(test_cases, list):
        raise Exception(f"Expected list but got {type(test_cases)}")
    
    total_cases = sum(len(tool_tests.get("test_cases", [])) for tool_tests in test_cases)
    print(f"✅ Generated {total_cases} AI test cases across {len(test_cases)} tools")
    return test_cases


def _generate_per_tool_test_cases(tools_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate test cases one tool at a time as fallback."""
    all_test_cases = []
    service = AIService()
    
    for tool_info in tools_info:
        try:
            print(f"🔧 Generating test cases for {tool_info['name']}...")
            
            # Create prompt for single tool
            prompt = format_prompt(
                "test_cases",
                tools_json=json.dumps([tool_info], indent=2)
            )
            
            tool_test_cases = service.generate_json(prompt)
            
            if isinstance(tool_test_cases, list) and len(tool_test_cases) > 0:
                all_test_cases.extend(tool_test_cases)
                case_count = len(tool_test_cases[0].get("test_cases", []))
                print(f"✅ Generated {case_count} test cases for {tool_info['name']}")
            else:
                print(f"⚠️  No test cases generated for {tool_info['name']}")
                
        except Exception as e:
            print(f"⚠️  Failed to generate test cases for {tool_info['name']}: {e}")
            continue
    
    total_cases = sum(len(tool_tests.get("test_cases", [])) for tool_tests in all_test_cases)
    print(f"✅ Generated {total_cases} total AI test cases across {len(all_test_cases)} tools")
    return all_test_cases


if __name__ == "__main__":
    # Test with sample tools
    import sys
    from .ai_service import test_claude_cli
    
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
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        },
        {
            "name": "divide",
            "description": "Divide one number by another",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dividend": {"type": "number"},
                    "divisor": {"type": "number"}
                },
                "required": ["dividend", "divisor"]
            }
        }
    ]
    
    print("Testing test case generation...")
    test_cases = generate_ai_test_cases(sample_tools)
    
    if test_cases:
        print("\nGenerated test cases:")
        for tool_tests in test_cases:
            print(f"\nTool: {tool_tests['tool']}")
            for test in tool_tests.get('test_cases', []):
                print(f"  - {test['id']} ({test['type']}): {test['description']}")
    else:
        print("Failed to generate test cases")