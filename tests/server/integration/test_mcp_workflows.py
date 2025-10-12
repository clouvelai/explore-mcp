"""
End-to-end tests for complete MCP server workflows.

These tests simulate real-world usage scenarios, testing the entire
flow from client connection through complex multi-step operations.
"""

import pytest


@pytest.mark.e2e
class TestCompleteCalculatorWorkflow:
    """Test complete calculator workflows end-to-end."""
    
    @pytest.mark.asyncio
    async def test_basic_arithmetic_workflow(self, mcp_client):
        """Test a complete arithmetic workflow with multiple operations."""
        # Step 1: Perform initial calculation
        result1 = await mcp_client.call_tool('sum', {'a': 10, 'b': 20})
        assert "is 30" in str(result1.content)
        
        # Step 2: Use result in multiplication
        result2 = await mcp_client.call_tool('multiply', {'a': 30, 'b': 2})
        assert "is 60" in str(result2.content)
        
        # Step 3: Divide the result
        result3 = await mcp_client.call_tool('divide', {'a': 60, 'b': 3})
        assert "is 20" in str(result3.content)
        
        # Step 4: Sum multiple numbers including our result
        result4 = await mcp_client.call_tool('sum_many', {'numbers': [20, 10, 5, 15]})
        assert "is 50" in str(result4.content)
    
    @pytest.mark.asyncio
    async def test_complex_calculation_chain(self, mcp_client):
        """Test a complex chain of calculations."""
        # Calculate: ((5 + 3) * 4) / 2 + sum([1,2,3,4,5])
        
        # (5 + 3) = 8
        step1 = await mcp_client.call_tool('sum', {'a': 5, 'b': 3})
        assert "is 8" in str(step1.content)
        
        # 8 * 4 = 32
        step2 = await mcp_client.call_tool('multiply', {'a': 8, 'b': 4})
        assert "is 32" in str(step2.content)
        
        # 32 / 2 = 16
        step3 = await mcp_client.call_tool('divide', {'a': 32, 'b': 2})
        assert "is 16" in str(step3.content)
        
        # sum([1,2,3,4,5]) = 15
        step4 = await mcp_client.call_tool('sum_many', {'numbers': [1, 2, 3, 4, 5]})
        assert "is 15" in str(step4.content)
        
        # 16 + 15 = 31
        final = await mcp_client.call_tool('sum', {'a': 16, 'b': 15})
        assert "is 31" in str(final.content)
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mcp_client):
        """Test workflow with error handling and recovery."""
        # Start with valid operation
        result1 = await mcp_client.call_tool('multiply', {'a': 100, 'b': 2})
        assert "is 200" in str(result1.content)
        
        # Attempt division by zero (should handle gracefully)
        error_result = await mcp_client.call_tool('divide', {'a': 200, 'b': 0})
        assert "Error: Cannot divide by zero" in str(error_result.content)
        
        # Recover and continue with valid operations
        result2 = await mcp_client.call_tool('divide', {'a': 200, 'b': 4})
        assert "is 50" in str(result2.content)
        
        # Continue with more operations
        result3 = await mcp_client.call_tool('sum_many', {'numbers': [50, 25, 25]})
        assert "is 100" in str(result3.content)
    
    @pytest.mark.asyncio
    async def test_financial_calculation_scenario(self, mcp_client):
        """Test a realistic financial calculation scenario."""
        # Scenario: Calculate total cost with tax and discount
        # Base price: $100
        # Tax rate: 8.5% (multiply by 1.085)
        # Discount: $15
        
        # Calculate price with tax: 100 * 1.085
        with_tax = await mcp_client.call_tool('multiply', {'a': 100, 'b': 1.085})
        assert "is 108.5" in str(with_tax.content)
        
        # Apply discount: 108.5 - 15
        final_price = await mcp_client.call_tool('sum', {'a': 108.5, 'b': -15})
        assert "is 93.5" in str(final_price.content)
        
        # Calculate savings percentage: 15 / 108.5 * 100
        savings_ratio = await mcp_client.call_tool('divide', {'a': 15, 'b': 108.5})
        assert "0.138" in str(savings_ratio.content)  # ~13.8% savings


@pytest.mark.e2e
class TestServerCapabilities:
    """Test overall server capabilities and features."""
    
    @pytest.mark.asyncio
    async def test_server_info_and_tools(self, mcp_client):
        """Test server information and tool availability."""
        # Get list of tools
        tools = await mcp_client.list_tools()
        
        # Verify minimum expected capabilities
        assert len(tools) >= 4
        
        # Verify each tool can be called
        for tool in tools:
            if tool.name == 'sum':
                result = await mcp_client.call_tool('sum', {'a': 1, 'b': 1})
                assert result is not None
            elif tool.name == 'multiply':
                result = await mcp_client.call_tool('multiply', {'a': 2, 'b': 2})
                assert result is not None
            elif tool.name == 'divide':
                result = await mcp_client.call_tool('divide', {'a': 4, 'b': 2})
                assert result is not None
            elif tool.name == 'sum_many':
                result = await mcp_client.call_tool('sum_many', {'numbers': [1, 2]})
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_prompt_integration(self, mcp_client):
        """Test integration between prompts and tools."""
        # Get the calculation explanation prompt
        prompt_result = await mcp_client.get_prompt(
            'explain_calculation',
            {'calculation': '25 + 17'}
        )
        
        assert prompt_result is not None
        assert len(prompt_result.messages) > 0
        
        # Verify we can still call tools after using prompts
        tool_result = await mcp_client.call_tool('sum', {'a': 25, 'b': 17})
        assert "is 42" in str(tool_result.content)


@pytest.mark.e2e
class TestStressAndPerformance:
    """Test server under stress and performance conditions."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rapid_sequential_calls(self, mcp_client):
        """Test rapid sequential tool calls."""
        results = []
        
        # Perform 50 rapid sequential calculations
        for i in range(50):
            result = await mcp_client.call_tool('sum', {'a': i, 'b': i + 1})
            results.append(result)
        
        # Verify all results are correct
        assert len(results) == 50
        for i, result in enumerate(results):
            expected_sum = i + (i + 1)
            content_text = result.content[0].text if result.content else ""
            assert f"is {expected_sum}" in content_text
    
    @pytest.mark.asyncio
    async def test_large_number_operations(self, mcp_client):
        """Test operations with very large numbers."""
        large_numbers = [10**6, 10**7, 10**8, 10**9]
        
        # Test sum_many with large numbers
        result = await mcp_client.call_tool('sum_many', {'numbers': large_numbers})
        content_text = result.content[0].text if result.content else ""
        assert "1111000000" in content_text  # Corrected sum: 1000000 + 10000000 + 100000000 + 1000000000
        
        # Test multiplication with large numbers
        result = await mcp_client.call_tool('multiply', {'a': 10**6, 'b': 10**3})
        content_text = result.content[0].text if result.content else ""
        assert "1000000000" in content_text
    
    @pytest.mark.asyncio
    async def test_precision_handling(self, mcp_client):
        """Test precision in floating-point operations."""
        # Test operations that might have precision issues
        result1 = await mcp_client.call_tool('sum', {'a': 0.1, 'b': 0.2})
        # Note: 0.1 + 0.2 in floating point is 0.30000000000000004
        assert result1 is not None
        
        result2 = await mcp_client.call_tool('divide', {'a': 1, 'b': 3})
        # Should get 0.3333333...
        content_text = result2.content[0].text if result2.content else ""
        assert "0.333" in content_text
        
        result3 = await mcp_client.call_tool('multiply', {'a': 0.1, 'b': 0.1})
        content_text = result3.content[0].text if result3.content else ""
        assert "0.01" in content_text