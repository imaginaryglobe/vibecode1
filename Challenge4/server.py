# Team Members: [Your Name], [Partner Name]
from fastmcp import FastMCP
import random

# Initialize the MCP server
mcp = FastMCP("VibeUtility")

@mcp.tool()
def echo_message(message: str) -> str:
    """Repeats the message back to the user to confirm connection."""
    return f"Server received: {message}"

@mcp.tool()
def roll_dice(sides: int = 6) -> str:
    """Rolls a virtual dice with a specified number of sides."""
    result = random.randint(1, sides)
    return f"You rolled a {result} on a {sides}-sided dice!"

if __name__ == "__main__":
    mcp.run()