from tavily import TavilyClient
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import List
import os

load_dotenv()

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

client = TavilyClient(TAVILY_API_KEY)

mcp = FastMCP('web search')

# operatios

@mcp.tool()
def get_weather(request:str) -> str:
    
    print(request)
    try:
        response = client.search(
            query=request
        )
        response_str = str(response)
        
        response_str = response_str.replace('\u2014', '-')
        
        print("response")
        return response_str
    except Exception as e:
        return f"Unable to process weather data for {request} due to encoding issues. Please try another location."

@mcp.tool()
def get_football_news(request:str) -> str:
    
    print(request)
    try:
        response = client.search(
            query=request
        )
        response_str = str(response)
        
        response_str = response_str.replace('\u2014', '-')
        
        print("response")
        return response_str
    except Exception as e:
        return f"Unable to process foot ball news: {request} due to encoding issues. Please try another location."

@mcp.tool()
def get_forex_updates(request:str) -> str:
    
    print(request)
    try:
        response = client.search(
            query=request
        )
        response_str = str(response)
        
        response_str = response_str.replace('\u2014', '-')
        
        print("response")
        return response_str
    except Exception as e:
        return f"Unable to process forex exchange for: {request} due to encoding issues. Please try another location."

if __name__ == '__main__':
    mcp.run()