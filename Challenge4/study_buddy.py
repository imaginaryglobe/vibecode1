# Team Members: [Jason Lyu] & [Jaden Fang]
# Final Challenge: Vibe Coding Study Buddy MCP Server

from fastmcp import FastMCP
import textwrap

# Initialize the MCP server
mcp = FastMCP("StudyBuddy")

@mcp.tool()
def summarize_notes(content: str, detail_level: str = "brief") -> str:
    """
    Summarizes long study notes into bullet points.
    detail_level can be 'brief' (3 points) or 'detailed' (6 points).
    """
    points = 3 if detail_level == "brief" else 6
    # In a real tool, this could call another API, 
    # but for this MCP, we'll let the AI Client handle the logic 
    # once we return the formatted instruction.
    return f"Please provide a {detail_level} summary of the following text in exactly {points} bullet points: {content}"

@mcp.tool()
def generate_quiz(topic: str, difficulty: str = "easy") -> str:
    """
    Generates a 3-question multiple choice quiz on any given topic.
    """
    return f"Generate a {difficulty} 3-question MCQ quiz about {topic}. Include the correct answers at the very bottom."

if __name__ == "__main__":
    mcp.run()