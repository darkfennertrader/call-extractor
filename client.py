"""
LangGraph Client for Call Extractor MCP Server

This client demonstrates how to use LangGraph to build an agent that
communicates with the webhook callback MCP server.
"""

import os
import uuid
import asyncio
from typing import Annotated, Dict, Any, List, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Load environment variables from .env file
load_dotenv()


# Define the state for our agent
class State(TypedDict):
    messages: Annotated[List, add_messages]


# Create a unique task ID and client ID for this session
TASK_ID = f"task_{uuid.uuid4().hex[:8]}"
CLIENT_ID = f"client_{uuid.uuid4().hex[:8]}"
CALLBACK_URL = f"http://localhost:9000/webhook/{CLIENT_ID}"

# Initialize the LLM with tools
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
    temperature=float(os.getenv("AGENT_TEMPERATURE", "0.01")),
)


# Use MultiServerMCPClient to manage MCP tools and server communication
mcp_client = MultiServerMCPClient(
    {
        "extract_data": {
            "transport": "streamable_http",
            "url": "http://localhost:8011/mcp/",
        }
    }
)


# Get all tools from the MCP client (async)
async def setup_tools_and_llm():
    tools = await mcp_client.get_tools()
    llm_with_tools = llm.bind_tools(tools)
    return tools, llm_with_tools


async def main():
    """Run the LangGraph agent."""
    print("🤖 Starting LangGraph Agent for Call Extractor MCP Server")
    print(f"📋 Task ID: {TASK_ID}")
    print(f"👤 Client ID: {CLIENT_ID}")
    print(f"🔄 Callback URL: {CALLBACK_URL}")
    print("----------------------------------------------")

    # Initial user prompt
    initial_prompt = (
        "I want to use the webhook callback server to process a task. \n"
        "First register a callback, then start the task, and finally check the status of the task.\n"
        "Show me the complete workflow step by step."
    )

    # Setup tools and LLM
    tools, llm_with_tools = await setup_tools_and_llm()

    # Create the ToolNode to handle tool executions
    tool_node = ToolNode(tools=tools)

    # Define the agent node that processes messages and determines actions
    def agent_node(state: State) -> Dict[str, Any]:
        """Process messages and determine next actions using the LLM."""
        messages = state["messages"]

        # Add context about the task and client IDs if not in the first message
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            if isinstance(messages[0].content, str):
                task_info = (
                    f"\nUse these identifiers for your API calls:\n- Task ID: {TASK_ID}\n"
                    f"- Client ID: {CLIENT_ID}\n- Callback URL: {CALLBACK_URL}"
                )
                messages[0].content = messages[0].content + task_info

        # Get response from the LLM
        response = llm_with_tools.invoke(messages)

        # Return the updated messages
        return {"messages": [response]}

    # Define the graph
    graph_builder = StateGraph(State)
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    # Add edges
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )
    graph_builder.add_edge("tools", "agent")

    # Compile the graph
    graph = graph_builder.compile()

    # Run the graph with the initial prompt
    print("🔵 User: " + initial_prompt)

    # Stream the graph execution (ASYNC)
    async for event in graph.astream(
        {"messages": [HumanMessage(content=initial_prompt)]}
    ):
        key, value = next(iter(event.items()))
        message = value["messages"][-1]

        if isinstance(message, AIMessage):
            print(f"🤖 Agent: {message.content}")
        elif isinstance(message, ToolMessage):
            print(f"🔧 Tool ({message.name}): {message.content}")

    print("----------------------------------------------")
    print("✅ Workflow completed!")


if __name__ == "__main__":
    asyncio.run(main())
