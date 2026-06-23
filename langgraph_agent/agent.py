# langgraph_agent/agent.py
import os
import time
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from shared.tools import web_search

# Define the LangChain tool wrapper
@tool
def search_tool(query: str) -> str:
    """
    Search the web for information on a given query topic.
    
    Args:
        query (str): The search term or topic.
        
    Returns:
        str: Search results text.
    """
    return web_search(query)

# Define the state shape for our LangGraph workflow
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    topic: str
    research_notes: str
    final_report: str

# Define the Researcher node
def researcher_node(state: AgentState):
    print("\n[LangGraph] 🔍 Activating Researcher Node...")
    messages = list(state.get("messages", []))
    
    model = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=os.environ.get("GEMINI_API_KEY"),
        temperature=0.2
    )
    
    # Bind the tool to the Gemini model
    model_with_tools = model.bind_tools([search_tool])
    
    # Debug message sequence
    print("\n--- [LangGraph Debug] Message History to model.invoke: ---")
    for i, m in enumerate(messages):
        print(f"  Msg #{i} | Type: {type(m).__name__} | Content Snippet: {repr(m.content[:100])}")
        if hasattr(m, 'tool_calls') and m.tool_calls:
            print(f"          | Tool Calls: {m.tool_calls}")
    print("-----------------------------------------------------------\n")
    
    # Generate the next step (either a tool call or the final notes)
    response = model_with_tools.invoke(messages)
    
    return {
        "messages": [response]
    }

# Tool execution node (uses LangGraph prebuilt ToolNode)
tool_node = ToolNode([search_tool])

# Conditional routing logic after the researcher node
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        tool_name = last_message.tool_calls[0]['name']
        print(f"[LangGraph] 🔀 Tool call detected: '{tool_name}'. Routing to 'tools' node.")
        return "tools"
    
    print("[LangGraph] 🔀 No tool calls requested. Routing to 'writer' node.")
    return "writer"

def safe_extract_text(content) -> str:
    """Helper to convert LangChain message content (which can be str or list of parts) to a clean string."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        return "".join(text_parts)
    return str(content)

# Define the Writer node
def writer_node(state: AgentState):
    print("\n[LangGraph] ✍️ Activating Writer Node...")
    topic = state["topic"]
    
    # Extract the final research notes from the latest non-tool-calling AIMessage
    research_notes_raw = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            research_notes_raw = msg.content
            break
            
    research_notes = safe_extract_text(research_notes_raw)
    if not research_notes:
        research_notes = "No research notes were gathered."
        
    # Rate Limit Spacer
    print("\n[LangGraph] ⏳ Sleeping for 15 seconds to respect Gemini API rate limits...")
    time.sleep(15)
        
    model = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=os.environ.get("GEMINI_API_KEY"),
        temperature=0.5
    )
    
    prompt = (
        f"You are a Technical Writer. Write a professional report on '{topic}' based on the following research notes:\n\n"
        f"{research_notes}\n\n"
        "Your report must be structured in professional Markdown and include:\n"
        "1. Title (H1)\n"
        "2. Executive Summary\n"
        "3. Detailed Analysis (Mechanism & Benefits)\n"
        "4. Industry Players & Progress\n"
        "5. Technical Challenges & Future Outlook\n"
        "Use a professional, objective tone."
    )
    
    response = model.invoke([
        HumanMessage(content=f"System Instructions: You are a professional technical writer who excels at creating structured reports.\n\nUser Request: {prompt}")
    ])
    
    final_report = safe_extract_text(response.content)
    
    return {
        "research_notes": research_notes,
        "final_report": final_report
    }

def run_langgraph_agent(topic: str) -> dict:
    """
    Compiles and runs the LangGraph workflow.
    
    Args:
        topic (str): The research topic.
        
    Returns:
        dict: A dictionary containing the research_notes and final_report.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    # Build the state graph
    workflow = StateGraph(AgentState)
    
    # Register our nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("writer", writer_node)
    
    # Set entry point
    workflow.add_edge(START, "researcher")
    
    # Set conditional edges
    workflow.add_conditional_edges(
        "researcher",
        should_continue,
        {
            "tools": "tools",
            "writer": "writer"
        }
    )
    
    # Loop back from tools to the researcher
    workflow.add_edge("tools", "researcher")
    
    # Connect writer to the end
    workflow.add_edge("writer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    # Execute the graph
    initial_state = {
        "topic": topic,
        "messages": [
            HumanMessage(content=(
                "System Instructions: You are an expert researcher. You must use the web_search tool to gather facts. "
                "You are strictly limited to calling the web_search tool ONCE. Do not perform multiple searches. "
                "Once you have gathered your search results, summarize your findings "
                "into structured research notes covering:\n"
                "1. Core concept and mechanism.\n"
                "2. Key advantages.\n"
                "3. Major players/companies.\n"
                "4. Critical technical/market challenges.\n"
                "Do NOT call tools if you have already done a search. Just provide the final summary.\n\n"
                f"User Request: Please research '{topic}'."
            ))
        ]
    }
    
    result_state = app.invoke(initial_state)
    
    return {
        "research_notes": result_state.get("research_notes", ""),
        "final_report": result_state.get("final_report", "")
    }
