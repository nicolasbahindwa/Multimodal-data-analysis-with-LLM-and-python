from mcp.server.fastmcp import FastMCP
import math
from typing import List

# MCP server instance name "Math"
mcp = FastMCP("Math")

# Register available math operations
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide a by b, returning a float result."""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b

@mcp.tool()
def power(a: int, b: int) -> int:
    """Raise a to the power of b."""
    return a ** b

@mcp.tool()
def modulo(a: int, b: int) -> int:
    """Find the remainder when a is divided by b."""
    if b == 0:
        raise ValueError("Modulo by zero is not allowed.")
    return a % b

@mcp.tool()
def square_root(a: int) -> float:
    """Find the square root of a."""
    if a < 0:
        raise ValueError("Square root of negative numbers is not allowed.")
    return math.sqrt(a)

@mcp.tool()
def mean(numbers: List[float]) -> float:
    """Calculate the mean (average) of a list of numbers."""
    if not numbers:
        raise ValueError("List cannot be empty.")
    return sum(numbers) / len(numbers)

@mcp.tool()
def max_value(numbers: List[float]) -> float:
    """Find the maximum value in a list of numbers."""
    if not numbers:
        raise ValueError("List cannot be empty.")
    return max(numbers)

# Run the MCP server
if __name__ == '__main__':
    mcp.run()