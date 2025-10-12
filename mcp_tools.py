"""
Shared MCP tool definitions.

This module contains all the MCP tools that can be used by both
stdio and HTTP servers, avoiding code duplication.
"""

from fastmcp import FastMCP


def register_tools(mcp: FastMCP):
    """Register all tools with the given FastMCP instance."""
    
    @mcp.tool()
    def add(a: float, b: float) -> str:
        """Add two numbers together.
        
        Args:
            a: The first number
            b: The second number
            
        Returns:
            A message with the sum of the two numbers
        """
        result = a + b
        return f"The sum of {a} and {b} is {result}"
    
    # Keep 'sum' as an alias for backwards compatibility
    @mcp.tool(name="sum")
    def sum_tool(a: float, b: float) -> str:
        """Add two numbers together.
        
        Args:
            a: The first number
            b: The second number
            
        Returns:
            A message with the sum of the two numbers
        """
        result = a + b
        return f"The sum of {a} and {b} is {result}"
    
    @mcp.tool()
    def sum_many(numbers: list[float]) -> str:
        """Add multiple numbers together.
        
        Args:
            numbers: A list of numbers to add together
            
        Returns:
            A message with the sum of all numbers
        """
        if not numbers:
            return "Error: No numbers provided"
        
        if len(numbers) == 1:
            return f"The sum is {numbers[0]}"
        
        # Now we can safely use the built-in sum function
        result = sum(numbers)
        numbers_str = " + ".join(str(n) for n in numbers)
        return f"The sum of {numbers_str} is {result}"
    
    @mcp.tool()
    def multiply(a: float, b: float) -> str:
        """Multiply two numbers together.
        
        Args:
            a: The first number
            b: The second number
            
        Returns:
            A message with the product of the two numbers
        """
        result = a * b
        return f"The product of {a} and {b} is {result}"
    
    @mcp.tool()
    def divide(a: float, b: float) -> str:
        """Divide one number by another.
        
        Args:
            a: The dividend (number to be divided)
            b: The divisor (number to divide by)
            
        Returns:
            A message with the quotient, or an error if dividing by zero
        """
        if b == 0:
            return "Error: Cannot divide by zero"
        result = a / b
        return f"{a} divided by {b} is {result}"


def register_prompts(mcp: FastMCP):
    """Register all prompts with the given FastMCP instance."""
    
    @mcp.prompt()
    def explain_calculation(calculation: str) -> str:
        """Get help explaining a mathematical calculation step by step.
        
        This prompt helps you understand how to break down and explain
        a calculation in a clear, educational way.
        
        Args:
            calculation: The calculation to explain (e.g., "25 + 17" or "15 * 3 + 8")
        """
        return f"""Please explain the following calculation step by step, as if teaching it to a student:

Calculation: {calculation}

Break it down into clear steps:
1. Identify the operations involved
2. Explain the order of operations (if applicable)
3. Show the work step by step
4. Provide the final answer
5. Optionally, give a real-world example to make it relatable

Keep the explanation clear and educational."""