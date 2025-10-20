#!/usr/bin/env python3
"""
MCP Test Generator - Generates comprehensive test cases for MCP tools.

Uses AI to create intelligent test cases including edge cases and domain-specific scenarios.
"""

import json
from typing import Dict, Any, List
from ai_service import AIService


# Prompt template for generating test cases
TEST_CASES_PROMPT_TEMPLATE = """
I need you to generate comprehensive test cases for MCP tools. Here are the tools:

{tools_json}

For each tool, generate test cases that include:
1. Valid parameter tests with realistic values
2. Missing required parameter tests  
3. Invalid type tests
4. Domain-specific edge cases (e.g., for math tools: division by zero, negative numbers, very large numbers)
5. Boundary condition tests relevant to each tool

Return ONLY a JSON array of test case objects. Each test case should have:
- "tool": tool name
- "description": description of what the tool does
- "test_cases": array of test case objects with:
  - "id": unique test case ID
  - "type": test type (valid_params, missing_required, invalid_type, edge_case)
  - "description": what this test checks
  - "params": parameters to pass to the tool
  - "expected_result": "success", "error", or "any"
  - "expected_contains": array of strings that should appear in the response

Example format:
[
  {{
    "tool": "add",
    "description": "Add two numbers together",
    "test_cases": [
      {{
        "id": "add_valid_positive",
        "type": "valid_params",
        "description": "Add two positive numbers",
        "params": {{"a": 5.0, "b": 3.0}},
        "expected_result": "success",
        "expected_contains": ["8"]
      }}
    ]
  }}
]
"""


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
    
    # Format the prompt
    prompt = TEST_CASES_PROMPT_TEMPLATE.format(
        tools_json=json.dumps(tools_info, indent=2)
    )
    
    try:
        # Use AIService to generate response
        service = AIService()
        test_cases = service.generate_json(prompt)
        
        # Validate that we got a list
        if not isinstance(test_cases, list):
            print(f"⚠️  Expected list but got {type(test_cases)}")
            return []
        
        total_cases = sum(len(tool_tests.get("test_cases", [])) for tool_tests in test_cases)
        print(f"✅ Generated {total_cases} AI test cases across {len(test_cases)} tools")
        return test_cases
    
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse Claude response as JSON: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Error generating AI test cases: {e}")
        return []


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