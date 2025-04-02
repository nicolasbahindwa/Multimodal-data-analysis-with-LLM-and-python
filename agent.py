
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from langchain_mcp_adapters.client import MultiServerMCPClient

# LangGraph agent
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Add pprint for better debugging
from pprint import pprint
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# MODEL
def call_model():
    return ChatAnthropic(model="claude-3-5-sonnet-latest", anthropic_api_key=ANTHROPIC_API_KEY)

model = call_model()

 
async def single_server():
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


def extract_ai_messages(messages):
    ai_messages = []
    for m in messages:
        if isinstance(m, AIMessage):
            ai_content = []
            if isinstance(m.content, list):
                for item in m.content:
                    if isinstance(item, dict) and 'text' in item:
                        ai_content.append(item['text'])
            elif isinstance(m.content, str):
                ai_content.append(m.content)
            ai_messages.append({'AI Message': ai_content})
    return ai_messages

def extract_tool_messages(messages):
    tool_messages = []
    tools_used = []
    
    for m in messages:
        if isinstance(m, AIMessage):
            if hasattr(m, 'tool_calls') and m.tool_calls:
                for tool_call in m.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tools_used.append({
                        'Tool Name': tool_name,
                        'Tool Args': tool_args
                    })
        elif isinstance(m, ToolMessage):
            tool_content = {}
            if hasattr(m, 'content'):
                if isinstance(m.content, str):
                    tool_content['Tool Content'] = m.content
                elif isinstance(m.content, dict):
                    tool_content.update(m.content)
                elif isinstance(m.content, list):
                    tool_content['Tool Content'] = m.content
            tool_messages.append(tool_content)
    
    return tools_used, tool_messages

async def server():
    async with MultiServerMCPClient() as client:
        await client.connect_to_server('math server', command='python', args=['./MCP-SERVER/math_server.py'])
        await client.connect_to_server('web search', command='python', args=['./MCP-SERVER/tavily_server.py'])
        
        agent = create_react_agent(model, client.get_tools())
        
        print("type exit to quit")
        while True:
            user_query = input("\n enter your question: ")
            if user_query.lower() in ['exit', 'quit', 'bye']:
                print('Exiting the MCP server')
                break
            
            print("\n" + "="*50)
            print(f"PROCESSING QUERY: {user_query}")
            print("\n" + "="*50)
            
            response = await agent.ainvoke({'messages': user_query})
            messages = response['messages']
            
            print("---------------------- TOOL CALLS ----------------------")
            tools_used, tool_messages = extract_tool_messages(messages)
            for tool in tools_used:
                pprint(tool)
                
            print("\n---------------------- TOOL MESSAGES ----------------------")
            for tool_message in tool_messages:
                pprint(tool_message)

            print("\n---------------------- AI MESSAGES ----------------------")
            ai_messages = extract_ai_messages(messages)
            for ai_message in ai_messages:
                pprint(ai_message)




if __name__ == "__main__":
    import asyncio
    asyncio.run(server())
