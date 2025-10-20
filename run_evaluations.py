#!/usr/bin/env python3
"""
MCP Evaluation Runner

Executes test cases from evaluations.json against a mock MCP server
and generates a results report.

TODO: Next iteration improvements needed:
- The AI-generated test cases often expect actual computation results (e.g., "8" for add(5,3))
  but mock servers return static responses (e.g., "The sum of 15 and 27 is 42")
- Consider adding a "mock_mode" flag to evaluations that adjusts expectations for mock vs real servers
- Or have separate evaluation sets: one for testing mock server structure/errors, 
  another for testing real server computation accuracy
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def get_mock_server_params(server_path: str = "generated/mock_server.py") -> StdioServerParameters:
    """Get parameters for connecting to the mock MCP server."""
    env = dict(os.environ)
    # Suppress Python logging to avoid stdio conflicts
    env["PYTHONUNBUFFERED"] = "1"
    
    return StdioServerParameters(
        command="uv",
        args=["run", "python", server_path],
        env=env
    )


def load_evaluations(eval_path: str = "generated/evaluations.json") -> Dict[str, Any]:
    """Load evaluation test cases from JSON file."""
    with open(eval_path, "r") as f:
        return json.load(f)


async def run_test_case(session: ClientSession, test_case: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """Execute a single test case against the mock server."""
    test_id = test_case["id"]
    params = test_case["params"]
    
    print(f"  Running: {test_id}")
    
    result = {
        "test_id": test_id,
        "type": test_case["type"],
        "description": test_case.get("description", ""),
        "params": params,
        "expected_result": test_case["expected_result"],
        "expected_contains": test_case.get("expected_contains", [])
    }
    
    try:
        # Call the tool
        response = await session.call_tool(tool_name, params)
        
        # Extract response text
        response_text = ""
        if response.content:
            for content in response.content:
                if hasattr(content, 'text'):
                    response_text += content.text
        
        result["response"] = response_text
        result["call_success"] = True
        
        # Check expectations
        if test_case["expected_result"] == "success":
            # Should not contain error indicators
            if "error" in response_text.lower():
                result["passed"] = False
                result["reason"] = "Expected success but got error response"
            else:
                result["passed"] = True
        elif test_case["expected_result"] == "error":
            # Should contain error indicators
            if "error" in response_text.lower():
                result["passed"] = True
            else:
                result["passed"] = False
                result["reason"] = "Expected error but got success response"
        else:  # "any"
            result["passed"] = True
        
        # Check for expected content
        if result["passed"] and test_case.get("expected_contains"):
            for expected in test_case["expected_contains"]:
                if expected.lower() not in response_text.lower():
                    result["passed"] = False
                    result["reason"] = f"Response missing expected content: {expected}"
                    break
        
    except Exception as e:
        result["call_success"] = False
        result["response"] = str(e)
        
        # If we expected an error, this might be okay
        if test_case["expected_result"] == "error":
            result["passed"] = True
            result["reason"] = "Got expected error during call"
        else:
            result["passed"] = False
            result["reason"] = f"Unexpected exception: {e}"
    
    # Print result
    status = "✅" if result["passed"] else "❌"
    print(f"    {status} {test_id}: {result.get('reason', 'Passed')}")
    
    return result


async def run_evaluations(eval_path: str, server_path: str) -> Dict[str, Any]:
    """Run all evaluations against the mock server."""
    print(f"\n🧪 Running evaluations from: {eval_path}")
    print(f"🎯 Against mock server: {server_path}\n")
    
    # Load evaluations
    evaluations = load_evaluations(eval_path)
    
    # Get server parameters
    print("🔌 Connecting to mock server...")
    server_params = get_mock_server_params(server_path)
    
    all_results = {
        "run_info": {
            "timestamp": datetime.now().isoformat(),
            "eval_file": eval_path,
            "mock_server": server_path,
            "server_source": evaluations["server_info"]["source"]
        },
        "tool_results": [],
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0
        }
    }
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            print("✅ Connected to mock server\n")
            
            # Verify tools are available
            tools_response = await session.list_tools()
            available_tools = [tool.name for tool in tools_response.tools]
            print(f"📋 Available tools: {', '.join(available_tools)}\n")
            
            # Run tests for each tool
            for tool_eval in evaluations["evaluations"]:
                tool_name = tool_eval["tool"]
                test_cases = tool_eval["test_cases"]
                
                print(f"🔧 Testing tool: {tool_name}")
                
                tool_results = {
                    "tool": tool_name,
                    "description": tool_eval["description"],
                    "test_results": []
                }
                
                # Check if tool is available
                if tool_name not in available_tools:
                    print(f"  ⚠️  Tool '{tool_name}' not found in mock server, skipping...")
                    continue
                
                # Run each test case
                for test_case in test_cases:
                    result = await run_test_case(session, test_case, tool_name)
                    tool_results["test_results"].append(result)
                    
                    # Update summary
                    all_results["summary"]["total_tests"] += 1
                    if result["passed"]:
                        all_results["summary"]["passed"] += 1
                    else:
                        all_results["summary"]["failed"] += 1
                
                all_results["tool_results"].append(tool_results)
                print()  # Blank line between tools
    
    return all_results


def generate_report(results: Dict[str, Any], output_path: str):
    """Generate a markdown report of evaluation results."""
    print(f"\n📄 Generating report: {output_path}")
    
    summary = results["summary"]
    pass_rate = (summary["passed"] / summary["total_tests"] * 100) if summary["total_tests"] > 0 else 0
    
    report = f"""# MCP Evaluation Report

## Summary

- **Date**: {results['run_info']['timestamp']}
- **Source Server**: `{results['run_info']['server_source']}`
- **Mock Server**: `{results['run_info']['mock_server']}`
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed']} ({pass_rate:.1f}%)
- **Failed**: {summary['failed']}

## Results by Tool

"""
    
    for tool_result in results["tool_results"]:
        tool_name = tool_result["tool"]
        description = tool_result["description"]
        
        # Count pass/fail for this tool
        tool_passed = sum(1 for r in tool_result["test_results"] if r["passed"])
        tool_total = len(tool_result["test_results"])
        
        report += f"### {tool_name}\n\n"
        report += f"*{description}*\n\n"
        report += f"Results: {tool_passed}/{tool_total} tests passed\n\n"
        
        # Show failed tests in detail
        failed_tests = [r for r in tool_result["test_results"] if not r["passed"]]
        if failed_tests:
            report += "#### Failed Tests\n\n"
            for test in failed_tests:
                report += f"- **{test['test_id']}**: {test.get('reason', 'Unknown failure')}\n"
                report += f"  - Type: {test['type']}\n"
                report += f"  - Params: `{json.dumps(test['params'])}`\n"
                report += f"  - Response: `{test.get('response', 'No response')[:200]}`\n\n"
        
        # Show summary of passed tests
        passed_tests = [r for r in tool_result["test_results"] if r["passed"]]
        if passed_tests:
            report += "#### Passed Tests\n\n"
            for test in passed_tests:
                report += f"- ✅ {test['test_id']} ({test['type']})\n"
            report += "\n"
    
    # Add recommendations
    report += """## Recommendations

"""
    
    if pass_rate == 100:
        report += "🎉 All tests passed! The mock server correctly implements all tool signatures.\n"
    elif pass_rate >= 80:
        report += "✅ Most tests passed. Review failed tests for potential improvements.\n"
    else:
        report += "⚠️ Significant number of tests failed. Review mock server implementation and test expectations.\n"
    
    # Write report
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)
    
    print(f"✅ Report generated")


async def main():
    parser = argparse.ArgumentParser(description="Run MCP evaluations against mock server")
    parser.add_argument("--evaluations", default="generated/evaluations.json", help="Path to evaluations JSON")
    parser.add_argument("--mock-server", default="generated/mock_server.py", help="Path to mock server")
    parser.add_argument("--output", default="generated/eval_results.md", help="Output report path")
    
    args = parser.parse_args()
    
    # Check files exist
    if not os.path.exists(args.evaluations):
        print(f"❌ Evaluations file not found: {args.evaluations}")
        print(f"   Run 'python mcp_eval_generator.py --server <server_path>' first")
        sys.exit(1)
    
    if not os.path.exists(args.mock_server):
        print(f"❌ Mock server not found: {args.mock_server}")
        print(f"   Run 'python mcp_eval_generator.py --server <server_path>' first")
        sys.exit(1)
    
    try:
        # Run evaluations
        results = await run_evaluations(args.evaluations, args.mock_server)
        
        # Generate report
        generate_report(results, args.output)
        
        # Print summary
        summary = results["summary"]
        pass_rate = (summary["passed"] / summary["total_tests"] * 100) if summary["total_tests"] > 0 else 0
        
        print(f"\n" + "="*50)
        print(f"📊 EVALUATION COMPLETE")
        print(f"   Total: {summary['total_tests']} tests")
        print(f"   Passed: {summary['passed']} ({pass_rate:.1f}%)")
        print(f"   Failed: {summary['failed']}")
        print(f"   Report: {args.output}")
        print("="*50)
        
        # Exit code based on results
        sys.exit(0 if summary["failed"] == 0 else 1)
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())