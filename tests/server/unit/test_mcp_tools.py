"""
Unit tests for calculator tool functions.

These tests verify the core logic of each calculator operation
by calling the tools through the MCP client interface.
"""

import pytest


class TestCalculatorOperations:
    """Test suite for basic calculator operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_positive_numbers(self, mcp_client):
        """Test addition of two positive numbers."""
        result = await mcp_client.call_tool('sum', {'a': 5.0, 'b': 3.0})
        assert "The sum of 5.0 and 3.0 is 8.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_negative_numbers(self, mcp_client):
        """Test addition of two negative numbers."""
        result = await mcp_client.call_tool('sum', {'a': -5.0, 'b': -3.0})
        assert "The sum of -5.0 and -3.0 is -8.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_mixed_sign(self, mcp_client):
        """Test addition of positive and negative numbers."""
        result = await mcp_client.call_tool('sum', {'a': 10.0, 'b': -3.0})
        assert "The sum of 10.0 and -3.0 is 7.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_with_zero(self, mcp_client):
        """Test addition with zero."""
        result = await mcp_client.call_tool('sum', {'a': 5.0, 'b': 0.0})
        assert "The sum of 5.0 and 0.0 is 5.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("a,b,expected", [
        (1.0, 2.0, 3.0),
        (0.5, 0.5, 1.0),
        (-1.0, 1.0, 0.0),
        (100.0, 200.0, 300.0),
        (0.1, 0.2, 0.30000000000000004),  # Float precision
    ])
    async def test_sum_parametrized(self, mcp_client, a, b, expected):
        """Parametrized test for various sum operations."""
        result = await mcp_client.call_tool('sum', {'a': a, 'b': b})
        assert f"is {expected}" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_many_empty_list(self, mcp_client):
        """Test sum_many with empty list."""
        result = await mcp_client.call_tool('sum_many', {'numbers': []})
        assert "Error: No numbers provided" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_many_single_number(self, mcp_client):
        """Test sum_many with a single number."""
        result = await mcp_client.call_tool('sum_many', {'numbers': [42.0]})
        assert "The sum is 42.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_many_multiple_numbers(self, mcp_client):
        """Test sum_many with multiple numbers."""
        result = await mcp_client.call_tool('sum_many', {'numbers': [1.0, 2.0, 3.0, 4.0]})
        assert "The sum of 1.0 + 2.0 + 3.0 + 4.0 is 10.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_many_negative_numbers(self, mcp_client):
        """Test sum_many with negative numbers."""
        result = await mcp_client.call_tool('sum_many', {'numbers': [-1.0, -2.0, -3.0]})
        assert "The sum of -1.0 + -2.0 + -3.0 is -6.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiply_positive_numbers(self, mcp_client):
        """Test multiplication of two positive numbers."""
        result = await mcp_client.call_tool('multiply', {'a': 4.0, 'b': 5.0})
        assert "The product of 4.0 and 5.0 is 20.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiply_negative_numbers(self, mcp_client):
        """Test multiplication with negative numbers."""
        result = await mcp_client.call_tool('multiply', {'a': -3.0, 'b': -4.0})
        assert "The product of -3.0 and -4.0 is 12.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiply_by_zero(self, mcp_client):
        """Test multiplication by zero."""
        result = await mcp_client.call_tool('multiply', {'a': 100.0, 'b': 0.0})
        assert "The product of 100.0 and 0.0 is 0.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("a,b,expected", [
        (2.0, 3.0, 6.0),
        (0.5, 2.0, 1.0),
        (-2.0, 3.0, -6.0),
        (0.0, 999.0, 0.0),
        (1.0, 1.0, 1.0),
    ])
    async def test_multiply_parametrized(self, mcp_client, a, b, expected):
        """Parametrized test for various multiplication operations."""
        result = await mcp_client.call_tool('multiply', {'a': a, 'b': b})
        assert f"is {expected}" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_divide_normal(self, mcp_client):
        """Test normal division."""
        result = await mcp_client.call_tool('divide', {'a': 10.0, 'b': 2.0})
        assert "10.0 divided by 2.0 is 5.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_divide_by_zero(self, mcp_client):
        """Test division by zero error handling."""
        result = await mcp_client.call_tool('divide', {'a': 10.0, 'b': 0.0})
        assert "Error: Cannot divide by zero" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_divide_negative_numbers(self, mcp_client):
        """Test division with negative numbers."""
        result = await mcp_client.call_tool('divide', {'a': -15.0, 'b': 3.0})
        assert "-15.0 divided by 3.0 is -5.0" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_divide_decimal_result(self, mcp_client):
        """Test division resulting in decimal."""
        result = await mcp_client.call_tool('divide', {'a': 7.0, 'b': 2.0})
        assert "7.0 divided by 2.0 is 3.5" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("a,b,expected", [
        (10.0, 2.0, 5.0),
        (9.0, 3.0, 3.0),
        (1.0, 2.0, 0.5),
        (0.0, 5.0, 0.0),
        (-10.0, -2.0, 5.0),
    ])
    async def test_divide_parametrized(self, mcp_client, a, b, expected):
        """Parametrized test for various division operations."""
        result = await mcp_client.call_tool('divide', {'a': a, 'b': b})
        assert f"is {expected}" in str(result.content)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_very_large_numbers(self, mcp_client):
        """Test operations with very large numbers."""
        large_num = 1e10
        result = await mcp_client.call_tool('sum', {'a': large_num, 'b': large_num})
        assert f"is {2 * large_num}" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_very_small_decimals(self, mcp_client):
        """Test operations with very small decimal numbers."""
        small_num = 1e-10
        result = await mcp_client.call_tool('multiply', {'a': small_num, 'b': 1000000.0})
        assert "0.0001" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_many_large_list(self, mcp_client):
        """Test sum_many with a large list of numbers."""
        numbers = list(range(1, 101))  # 1 to 100
        result = await mcp_client.call_tool('sum_many', {'numbers': numbers})
        assert "is 5050" in str(result.content)  # Sum of 1 to 100


class TestInputValidation:
    """Test input validation and type handling."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_integer_inputs(self, mcp_client):
        """Test that integer inputs work correctly."""
        result = await mcp_client.call_tool('sum', {'a': 5, 'b': 3})
        assert "is 8" in str(result.content)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mixed_integer_float(self, mcp_client):
        """Test mixed integer and float inputs."""
        result = await mcp_client.call_tool('multiply', {'a': 5, 'b': 2.5})
        assert "is 12.5" in str(result.content)