# Correct imports for MCP clients
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from langchain_mcp_adapters.client import MultiServerMCPClient

# LangGraph agent
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

# Add pprint for better debugging
from pprint import pprint

import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# MODEL
model = ChatAnthropic(model="claude-3-5-sonnet-latest", anthropic_api_key=ANTHROPIC_API_KEY)

# SERVER
# - Handles incoming connections (in this case, via stdio)
# - Handles tool discovery (when client asks "what tools do you have?")
# - Executes tools when requested and returns results

async def main():
    server_params = StdioServerParameters(
        command='python',
        args=['./math_server.py'],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connections
            await session.initialize()
            
            tools = await load_mcp_tools(session)
            
            # Create and run the agent (model, tools)
            agent = create_react_agent(model, tools)
            agent_response = await agent.ainvoke({'messages': "what is (3+5) x 12?"})
            
            # Iterate through all messages in the response and print them
            for i, m in enumerate(agent_response['messages']):
                print(f"\nMessage {i}:")
                pprint(m)

# Multi-server handling
async def server():
    print('starting.....')
    
    async with MultiServerMCPClient() as client:
        # Connect to multiple servers
        await client.connect_to_server(
            'math_server',
            command='python',
            args=['/math_server.py'],
        )
        await client.connect_to_server(
            'weather',
            command='python',
            args=['/tavily_server.py'],
        )
        
        # Create the agent using the connected client's tools
        agent = create_react_agent(model, client.get_tools())
        
        # Ask multiple questions from both servers
        math_response = await agent.ainvoke({'messages': 'what is (4x9):4'})
        # weather_response = await agent.ainvoke({'messages': 'what is the weather in tokyo'})
        
        # Print out the math server's response
        print("Math server response:")
        for m in math_response['messages']:
            pprint(m)
        
        # Print out the weather server's response
        # print("Weather server response:")
        # for m in weather_response['messages']:
        #     pprint(m)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
