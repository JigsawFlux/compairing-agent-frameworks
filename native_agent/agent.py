# native_agent/agent.py
import os
import time
from google import genai
from google.genai import types
from shared.tools import web_search

def run_native_agent(topic: str) -> dict:
    """
    Runs the native Gemini multi-agent workflow using only the google-genai SDK.
    
    Args:
        topic (str): The research topic.
        
    Returns:
        dict: A dictionary containing the research_notes and final_report.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Initialize the official google-genai client
    client = genai.Client(api_key=api_key)
    
    # -------------------------------------------------------------
    # Phase 1: Research Agent (with tool access)
    # -------------------------------------------------------------
    print(f"\n[Native] 🔍 Activating Research Agent for topic: '{topic}'...")
    
    researcher_prompt = (
        f"You are a Senior Researcher. Your task is to research '{topic}'. "
        "Use the web_search tool to gather detailed, factual, and up-to-date information. "
        "You are strictly limited to exactly ONE tool call. Choose your query carefully to be comprehensive. "
        "Construct structured research notes covering:\n"
        "1. Core concept and mechanism. "
        "2. Key advantages. "
        "3. Major players/companies. "
        "4. Critical technical/market challenges. "
        "Be factual and reference facts. Avoid making up details."
    )
    
    # The SDK automatically handles the tool calling execution loop
    # when tools are provided as plain Python functions.
    research_response = client.models.generate_content(
        model=model,
        contents=researcher_prompt,
        config=types.GenerateContentConfig(
            tools=[web_search],
            system_instruction=(
                "You are an expert researcher. You must rely on the web_search tool to look up information. "
                "You are strictly limited to calling the web_search tool ONCE. Do not make multiple calls. "
                "Present detailed, well-structured notes."
            ),
            temperature=0.2,
        )
    )
    
    research_notes = research_response.text
    
    # -------------------------------------------------------------
    # Rate Limit Spacer
    # -------------------------------------------------------------
    print("\n[Native] ⏳ Sleeping for 15 seconds to respect Gemini API rate limits...")
    time.sleep(15)
    
    # -------------------------------------------------------------
    # Phase 2: Writer Agent
    # -------------------------------------------------------------
    print(f"\n[Native] ✍️ Activating Writer Agent to draft report...")
    
    writer_prompt = (
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
    
    writer_response = client.models.generate_content(
        model=model,
        contents=writer_prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a professional technical writer who excels at creating clear, comprehensive reports.",
            temperature=0.5,
        )
    )
    
    final_report = writer_response.text
    
    return {
        "research_notes": research_notes,
        "final_report": final_report
    }

