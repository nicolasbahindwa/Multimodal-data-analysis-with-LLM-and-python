
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

# async def server():
#     async with MultiServerMCPClient() as client:
#         await client.connect_to_server('math server', command='python', args=['./MCP-SERVER/math_server.py'])
#         await client.connect_to_server('web search', command='python', args=['./MCP-SERVER/tavily_server.py'])
        
#         agent = create_react_agent(model, client.get_tools())
        
#         print("type exit to quit")
#         while True:
#             user_query = input("\n enter your question: ")
#             if user_query.lower() in ['exit', 'quit', 'bye']:
#                 print('Exiting the MCP server')
#                 break
            
#             print("\n" + "="*50)
#             print(f"PROCESSING QUERY: {user_query}")
#             print("\n" + "="*50)
            
#             response = await agent.ainvoke({'messages': user_query})
#             messages = response['messages']
            
#             print("---------------------- TOOL CALLS ----------------------")
#             tools_used, tool_messages = extract_tool_messages(messages)
#             for tool in tools_used:
#                 pprint(tool)
                
#             print("\n---------------------- TOOL MESSAGES ----------------------")
#             for tool_message in tool_messages:
#                 pprint(tool_message)

#             print("\n---------------------- AI MESSAGES ----------------------")
#             ai_messages = extract_ai_messages(messages)
#             for ai_message in ai_messages:
#                 pprint(ai_message)


async def finalize_answer(model, messages, user_query):
    """
    Process the agent's raw output and generate a well-structured final answer.
    
    Args:
        model: The LLM model to use for refinement
        messages: The list of messages from the agent's response
        user_query: The original user question
        
    Returns:
        A refined, well-structured answer
    """
    # Extract relevant tool messages and outputs
    tools_used, tool_messages = extract_tool_messages(messages)
    
    # Construct a prompt for the LLM to refine the answer
    refinement_prompt = f"""
    You are an expert assistant that provides clear, concise, and well-structured answers.
    
    ORIGINAL QUESTION: {user_query}
    
    TOOLS USED:
    {tools_used}
    
    TOOL OUTPUTS: 
    {tool_messages}
    
    Please provide a final, refined answer to the original question based on the tool outputs. 
    Your answer should:
    1. Be direct and address the question completely
    2. Include relevant calculations or data from the tool outputs
    3. Be well-structured and easy to understand
    4. Provide any necessary context or explanation
    5. Be conversational in tone while remaining informative
    
    FINAL ANSWER:
    """
    
    # Call the model to generate the refined answer
    refined_response = await model.ainvoke([HumanMessage(content=refinement_prompt)])
    
    # Extract the content from the model's response
    if isinstance(refined_response.content, list):
        refined_answer = " ".join([item.get('text', '') for item in refined_response.content if isinstance(item, dict) and 'text' in item])
    else:
        refined_answer = refined_response.content
        
    return refined_answer


# Updated server function that incorporates the finalize_answer function
async def server_with_refinement():
    async with MultiServerMCPClient() as client:
        await client.connect_to_server('math server', command='python', args=['./MCP-SERVER/math_server.py'])
        await client.connect_to_server('web search', command='python', args=['./MCP-SERVER/tavily_server.py'])
        
        llm = call_model()
        agent = create_react_agent(llm, client.get_tools())
        
        print("type exit to quit")
        while True:
            user_query = input("\n enter your question: ")
            if user_query.lower() in ['exit', 'quit', 'bye']:
                print('Exiting the MCP server')
                break
            
            print("\n" + "="*50)
            print(f"PROCESSING QUERY: {user_query}")
            print("\n" + "="*50)
            
            # Get the raw agent response
            response = await agent.ainvoke({'messages': user_query})
            messages = response['messages']
            
            # print("---------------------- TOOL CALLS ----------------------")
            # tools_used, tool_messages = extract_tool_messages(messages)
            # for tool in tools_used:
            #     pprint(tool)
                
            # print("\n---------------------- TOOL MESSAGES ----------------------")
            # for tool_message in tool_messages:
            #     pprint(tool_message)

            # print("\n---------------------- AI MESSAGES ----------------------")
            # ai_messages = extract_ai_messages(messages)
            # for ai_message in ai_messages:
            #     pprint(ai_message)
            
            # Generate the refined final answer
            print("\n---------------------- REFINED FINAL ANSWER ----------------------")
            final_answer = await finalize_answer(llm, messages, user_query)
            print(final_answer)


if __name__ == "__main__":
    import asyncio
    asyncio.run(server_with_refinement())



# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(server())
