"""
Calculator MCP tool definitions.

This module contains all the calculator MCP tools that can be used by
the calculator server.
"""

from fastmcp import FastMCP


def register_tools(mcp: FastMCP):
    """Register all calculator tools with the given FastMCP instance."""
    
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


def register_resources(mcp: FastMCP):
    """Register all calculator resources with the given FastMCP instance.
    
    Note: Template resources (with parameters like {category}) are correctly implemented
    and functional, but may not be discovered by MCP Inspector discovery tools yet.
    This is a known limitation of the current discovery process.
    """
    
    @mcp.resource("calculator://constants")
    def get_mathematical_constants() -> str:
        """Provides common mathematical constants used in calculations.
        
        Returns a formatted list of important mathematical constants
        with their values and descriptions.
        """
        constants = {
            "π (pi)": "3.14159265359",
            "e (Euler's number)": "2.71828182846", 
            "φ (Golden ratio)": "1.61803398875",
            "√2 (Square root of 2)": "1.41421356237",
            "√3 (Square root of 3)": "1.73205080757",
            "ln(2) (Natural log of 2)": "0.69314718056",
            "ln(10) (Natural log of 10)": "2.30258509299"
        }
        
        result = "# Mathematical Constants\n\n"
        for name, value in constants.items():
            result += f"**{name}**: {value}\n"
        
        return result
    
    @mcp.resource("calculator://formulas/{category}")
    def get_formulas(category: str) -> str:
        """Provides mathematical formulas for different categories.
        
        Args:
            category: The category of formulas (geometry, algebra, trigonometry)
            
        Note: This is a template resource that should work correctly at runtime,
        but may not appear in discovery tools due to MCP Inspector limitations.
        """
        formulas = {
            "geometry": {
                "Circle Area": "A = π × r²",
                "Circle Circumference": "C = 2 × π × r",
                "Rectangle Area": "A = length × width",
                "Triangle Area": "A = (base × height) / 2",
                "Sphere Volume": "V = (4/3) × π × r³",
                "Cylinder Volume": "V = π × r² × height"
            },
            "algebra": {
                "Quadratic Formula": "x = (-b ± √(b² - 4ac)) / (2a)",
                "Distance Formula": "d = √((x₂-x₁)² + (y₂-y₁)²)",
                "Slope Formula": "m = (y₂-y₁) / (x₂-x₁)",
                "Compound Interest": "A = P(1 + r/n)^(nt)"
            },
            "trigonometry": {
                "Sine": "sin(θ) = opposite / hypotenuse",
                "Cosine": "cos(θ) = adjacent / hypotenuse", 
                "Tangent": "tan(θ) = opposite / adjacent",
                "Pythagorean Identity": "sin²(θ) + cos²(θ) = 1",
                "Law of Cosines": "c² = a² + b² - 2ab×cos(C)"
            }
        }
        
        if category.lower() not in formulas:
            available = ", ".join(formulas.keys())
            return f"Category '{category}' not found. Available categories: {available}"
        
        category_formulas = formulas[category.lower()]
        result = f"# {category.title()} Formulas\n\n"
        for name, formula in category_formulas.items():
            result += f"**{name}**: {formula}\n"
        
        return result


def register_prompts(mcp: FastMCP):
    """Register all calculator prompts with the given FastMCP instance."""
    
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