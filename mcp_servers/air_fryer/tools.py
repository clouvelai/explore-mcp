"""
Air Fryer MCP tool definitions.

This module contains all the air fryer MCP tools that can be used by
the air fryer server via HTTP transport.
"""

import time

from fastmcp import FastMCP


def register_tools(mcp: FastMCP):
    """Register all air fryer tools with the given FastMCP instance."""
    
    @mcp.tool()
    def cook(time_seconds: int) -> str:
        """Cook food in the air fryer for a specified time.
        
        Args:
            time_seconds: The cooking time in seconds
            
        Returns:
            A message describing the cooking process and result
        """
        if time_seconds <= 0:
            return "Error: Cooking time must be greater than 0 seconds"
        
        if time_seconds > 3600:  # 1 hour max
            return "Error: Maximum cooking time is 3600 seconds (1 hour)"
        
        # Convert to minutes and seconds for display
        minutes = time_seconds // 60
        seconds = time_seconds % 60
        
        if minutes > 0 and seconds > 0:
            time_display = f"{minutes} minute(s) and {seconds} second(s)"
        elif minutes > 0:
            time_display = f"{minutes} minute(s)"
        else:
            time_display = f"{seconds} second(s)"
        
        # Determine cooking temperature based on time
        if time_seconds < 120:  # Less than 2 minutes
            temp = 400
            intensity = "quick crisp"
        elif time_seconds < 600:  # Less than 10 minutes
            temp = 375
            intensity = "medium cook"
        else:  # 10+ minutes
            temp = 350
            intensity = "slow roast"
        
        return f"🍟 Air fryer cooking for {time_display} at {temp}°F ({intensity}). Your food will be crispy and delicious!"


def register_resources(mcp: FastMCP):
    """Register all air fryer resources with the given FastMCP instance."""
    
    @mcp.resource("airfryer://recipes")
    def get_recipes() -> str:
        """Provides a collection of popular air fryer recipes with cooking times and temperatures.
        
        Returns a formatted list of air fryer recipes with instructions.
        """
        recipes = {
            "French Fries": {
                "time": "15 minutes (900 seconds)",
                "temp": "400°F",
                "instructions": "Cut potatoes into strips, toss with oil and salt, cook until golden"
            },
            "Chicken Wings": {
                "time": "25 minutes (1500 seconds)", 
                "temp": "380°F",
                "instructions": "Season wings, cook flipping halfway through until crispy"
            },
            "Mozzarella Sticks": {
                "time": "6 minutes (360 seconds)",
                "temp": "390°F", 
                "instructions": "Freeze first, then cook until golden and cheese is melted"
            },
            "Bacon": {
                "time": "10 minutes (600 seconds)",
                "temp": "400°F",
                "instructions": "Place strips in basket, flip halfway through cooking"
            },
            "Vegetables": {
                "time": "12 minutes (720 seconds)",
                "temp": "375°F",
                "instructions": "Toss with oil and seasonings, shake basket halfway through"
            },
            "Salmon": {
                "time": "10 minutes (600 seconds)",
                "temp": "400°F",
                "instructions": "Season fillet, cook skin-side down until flaky"
            },
            "Donuts": {
                "time": "5 minutes (300 seconds)",
                "temp": "350°F",
                "instructions": "Use canned biscuit dough, make holes, cook until golden"
            }
        }
        
        result = "# 🍟 Air Fryer Recipe Collection\n\n"
        result += "Popular recipes with cooking times and temperatures:\n\n"
        
        for name, details in recipes.items():
            result += f"## {name}\n"
            result += f"**Time**: {details['time']}\n"
            result += f"**Temperature**: {details['temp']}\n"
            result += f"**Instructions**: {details['instructions']}\n\n"
        
        result += "💡 **Tips**:\n"
        result += "- Preheat for 2-3 minutes for best results\n"
        result += "- Don't overcrowd the basket\n"
        result += "- Shake or flip food halfway through cooking\n"
        result += "- Use oil spray for extra crispiness\n"
        
        return result