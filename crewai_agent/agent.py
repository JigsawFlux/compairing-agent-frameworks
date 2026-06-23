# crewai_agent/agent.py
import os
import time
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from shared.tools import web_search

# Define the CrewAI tool wrapper
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

def run_crewai_agent(topic: str) -> dict:
    """
    Runs the CrewAI sequential workflow.
    
    Args:
        topic (str): The research topic.
        
    Returns:
        dict: A dictionary containing the research_notes and final_report.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    # LiteLLM/CrewAI uses the prefix "gemini/" for Gemini models
    crew_model = f"gemini/{model}" if not model.startswith("gemini/") else model
    
    # Initialize the LLM config for CrewAI
    llm = LLM(
        model=crew_model,
        api_key=api_key,
        temperature=0.2
    )
    
    # 1. Define the Researcher Agent
    researcher = Agent(
        role="Senior Technology Researcher",
        goal=f"Conduct deep research on '{topic}' and compile key insights using exactly ONE search query",
        backstory=(
            "You are a highly analytical research specialist. To stay within strict API rate limits, "
            "you must use the search_tool exactly ONCE to run a single, broad query. "
            "Do not perform multiple searches or repeat search queries. List precise, structured notes."
        ),
        tools=[search_tool],
        llm=llm,
        verbose=True
    )
    
    # 2. Define the Writer Agent
    writer = Agent(
        role="Expert Technical Writer",
        goal=f"Synthesize research notes into a highly professional technical report on '{topic}'",
        backstory=(
            "You are a veteran technical publisher who specializes in explaining complex technological advancements "
            "in clean, structured, and easy-to-read Markdown reports."
        ),
        llm=llm,
        verbose=True
    )
    
    # Callback to sleep between tasks to prevent hitting RPM limits
    def sleep_callback(task_output):
        print("\n[CrewAI] ⏳ Sleeping for 15 seconds to respect Gemini API rate limits...")
        time.sleep(15)

    # 3. Define the Research Task
    research_task = Task(
        description=(
            f"Research the topic '{topic}' using the web_search tool.\n"
            "You are strictly limited to exactly ONE call of the web_search tool. Choose your query carefully.\n"
            "Identify and detail:\n"
            "1. Core concept and mechanism.\n"
            "2. Three major benefits or advantages.\n"
            "3. Companies/institutions leading the work.\n"
            "4. Main technical or scaling barriers.\n"
            "Produce structured, objective research notes."
        ),
        expected_output="Detailed, structured notes listing research facts.",
        agent=researcher,
        callback=sleep_callback
    )
    
    # 4. Define the Writing Task
    write_task = Task(
        description=(
            "Review the research notes gathered. "
            f"Write a comprehensive technical report on '{topic}'.\n"
            "The report must include:\n"
            "1. Title (H1)\n"
            "2. Executive Summary\n"
            "3. Detailed Analysis (Mechanism & Benefits)\n"
            "4. Industry Players & Progress\n"
            "5. Technical Challenges & Future Outlook\n"
            "Format the report in clean Markdown."
        ),
        expected_output="A beautifully structured technical report in Markdown format.",
        agent=writer
    )
    
    # 5. Instantiate and execute the Crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Kickoff the process
    result = crew.kickoff()
    
    # Retrieve notes and final report safely
    research_notes = ""
    if research_task.output:
        research_notes = str(research_task.output.raw)
        
    final_report = str(result.raw) if hasattr(result, 'raw') else str(result)
    
    return {
        "research_notes": research_notes,
        "final_report": final_report
    }
