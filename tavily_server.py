from mcp.server.fastmcp import FastMCP
import os
from tavily import TavilyClient
from typing import List, Optional, Dict, Any

# Set up Tavily client
# You'll need to set TAVILY_API_KEY as an environment variable or provide it directly here
api_key = os.environ.get("TAVILY_API_KEY", "your_tavily_api_key_here")
tavily_client = TavilyClient(api_key=api_key)

# MCP server instance name "TavilySearch"
mcp = FastMCP("TavilySearch")

@mcp.tool()
def search(query: str, search_depth: str = "basic", max_results: int = 5, include_domains: Optional[List[str]] = None, 
           exclude_domains: Optional[List[str]] = None, include_answer: bool = True, include_raw_content: bool = False) -> Dict[Any, Any]:
    """
    Perform a web search using Tavily.
    
    Args:
        query: The search query string
        search_depth: The depth of search - "basic" (faster) or "comprehensive" (more thorough)
        max_results: Maximum number of results to return (1-10)
        include_domains: Optional list of domains to specifically include in the search
        exclude_domains: Optional list of domains to exclude from the search
        include_answer: Whether to include Tavily's generated answer
        include_raw_content: Whether to include the raw content of search results
    
    Returns:
        Dict containing search results
    """
    # Validate parameters
    if max_results < 1 or max_results > 10:
        raise ValueError("max_results must be between 1 and 10")
    
    if search_depth not in ["basic", "comprehensive"]:
        raise ValueError("search_depth must be either 'basic' or 'comprehensive'")
    
    # Perform the search
    response = tavily_client.search(
        query=query,
        search_depth=search_depth,
        max_results=max_results,
        include_domains=include_domains or [],
        exclude_domains=exclude_domains or [],
        include_answer=include_answer,
        include_raw_content=include_raw_content
    )
    
    return response

@mcp.tool()
def search_images(query: str, max_results: int = 5) -> Dict[Any, Any]:
    """
    Search for images using Tavily.
    
    Args:
        query: The image search query string
        max_results: Maximum number of image results to return
    
    Returns:
        Dict containing image search results
    """
    # Validate parameters
    if max_results < 1 or max_results > 10:
        raise ValueError("max_results must be between 1 and 10")
    
    # Perform the image search
    response = tavily_client.images(
        query=query,
        max_results=max_results
    )
    
    return response

@mcp.tool()
def search_topic(topic: str) -> Dict[Any, Any]:
    """
    Get information about a specific topic using Tavily's topic search.
    
    Args:
        topic: The topic to search for
    
    Returns:
        Dict containing topic information
    """
    # Perform the topic search
    response = tavily_client.qna(question=topic)
    
    return response

@mcp.tool()
def get_weather(city: str, units: str = "metric") -> Dict[Any, Any]:
    """
    Get current weather information for a specific city using Tavily search.
    
    Args:
        city: Name of the city to get weather for
        units: Units of measurement ('metric' for Celsius, 'imperial' for Fahrenheit)
    
    Returns:
        Dict containing weather information from search results
    """
    query = f"current weather in {city} {units} units"
    
    # Use the standard search function to get weather information
    response = tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=3,
        include_answer=True
    )
    
    return {
        "city": city,
        "query": query,
        "answer": response.get("answer", ""),
        "results": response.get("results", []),
        "units": units
    }

@mcp.tool()
def get_news(query: str = None, category: str = None, country: str = "us") -> Dict[Any, Any]:
    """
    Get news articles based on criteria using Tavily search.
    
    Args:
        query: Keywords or phrases to search for in news articles
        category: Category of news (business, entertainment, health, etc.)
        country: Country to focus news on (e.g., 'us', 'uk', 'india')
    
    Returns:
        Dict containing news articles from search results
    """
    # Build the search query
    search_query = ""
    if query:
        search_query += query + " "
    if category:
        search_query += category + " news "
    if country:
        search_query += "in " + country
        
    # Default if nothing is provided
    if not search_query.strip():
        search_query = "latest news"
    
    # Use the standard search function with news domains
    response = tavily_client.search(
        query=search_query,
        search_depth="basic",
        max_results=8,
        include_answer=True,
        include_domains=["news.google.com", "cnn.com", "bbc.com", "reuters.com", 
                        "apnews.com", "nytimes.com", "wsj.com", "theguardian.com"]
    )
    
    return {
        "query": search_query,
        "answer": response.get("answer", ""),
        "articles": response.get("results", [])
    }

# Run the MCP server
if __name__ == '__main__':
    print("calling tool")
    mcp.run()