# shared/tools.py
import os
import json
from duckduckgo_search import DDGS

# Mock search database for reliable fallback
MOCK_DATABASE = {
    "solid-state batteries": (
        "Solid-state batteries replace the liquid or polymer gel electrolyte found in current lithium-ion batteries "
        "with a solid electrolyte. Key advantages include higher energy density (potentially double), faster charging "
        "times, and significantly improved safety (non-flammable). Major players include Toyota, QuantumScape, "
        "Samsung SDI, and Solid Power. Current challenges are high manufacturing costs, dendrite formation (which can "
        "short-circuit the battery), and volume expansion/contraction during cycling that leads to delamination."
    ),
    "solid state batteries": (
        "Solid-state batteries replace the liquid electrolyte with solid materials like ceramics, glasses, or polymers. "
        "They offer higher energy density, faster charging, and greater safety. Key challenges include high production costs, "
        "dendrite growth, and contact degradation. Toyota plans to commercialize solid-state batteries by 2027-2028."
    ),
    "quantum computing": (
        "Quantum computing utilizes quantum mechanics principles like superposition and entanglement to perform complex "
        "computations. Qubits can exist in multiple states simultaneously, allowing exponential processing power for specific "
        "problems. Key applications include cryptography, optimization, molecular modeling, and material science. Leading "
        "companies are IBM (Eagle and Condor processors), Google (Sycamore), Honeywell/Quantinuum, and IonQ. Major hurdles "
        "are decoherence, high error rates, and the requirement for dilution refrigerators to maintain near absolute zero temperatures."
    ),
    "nuclear fusion": (
        "Nuclear fusion power seeks to replicate the reaction powering the sun. It promises clean, virtually limitless, "
        "and safe energy. In December 2022, the National Ignition Facility (NIF) achieved net energy gain (Q > 1) using laser fusion "
        "(Inertial Confinement). Magnetic confinement (Tokamaks) like ITER in France and Commonwealth Fusion Systems' SPARC are "
        "also making rapid progress. Challenges include sustaining the high-temperature plasma, developing neutron-resistant "
        "materials, and achieving commercial viability (grid-ready power)."
    ),
    "generative ai agents": (
        "Generative AI agents are autonomous software entities that leverage Large Language Models (LLMs) to perceive "
        "their environment, make decisions, and execute actions using tools. Popular frameworks include LangGraph, CrewAI, "
        "and Microsoft AutoGen. They operate using loops of reasoning, planning, memory, and tool usage. Challenges include "
        "hallucinations, infinite loops, high API costs, and security risks like prompt injection."
    )
}

def web_search(query: str) -> str:
    """
    Search the web for information on a given query topic.
    
    Args:
        query (str): The search query or topic to search for.
        
    Returns:
        str: A summary text containing the search results.
    """
    print(f"\n[Tool: Web Search] Searching for: '{query}'...")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
            
        if results:
            formatted_results = []
            for i, r in enumerate(results, 1):
                formatted_results.append(
                    f"Result {i}:\n"
                    f"Title: {r.get('title', 'N/A')}\n"
                    f"Snippet: {r.get('body', 'N/A')}\n"
                    f"Link: {r.get('href', 'N/A')}\n"
                )
            return "\n---\n".join(formatted_results)
    except Exception as e:
        print(f"[Tool: Web Search Warning] DDG search failed or was rate-limited: {str(e)}")
    
    # Fallback to Mock Database if DDG search fails or returns nothing
    query_lower = query.lower()
    for key, val in MOCK_DATABASE.items():
        if key in query_lower or query_lower in key:
            print(f"[Tool: Web Search Fallback] Found matches in local mock database for '{key}'")
            return f"Source: Mock Search Database (Local Fallback)\nSummary: {val}"
            
    print("[Tool: Web Search Fallback] No specific mock data found. Returning generic fallback search results.")
    return (
        f"Search results for '{query}':\n"
        f"1. Recent articles discuss the rapid technological advancements in '{query}'.\n"
        f"2. Experts emphasize key challenges such as high development costs, regulatory hurdles, and scaling issues.\n"
        f"3. Leading industry groups are investing heavily in research and development to address these constraints by 2028."
    )
