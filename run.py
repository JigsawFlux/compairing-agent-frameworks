# run.py
import os
import time
import argparse
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from native_agent.agent import run_native_agent
from langgraph_agent.agent import run_langgraph_agent
from crewai_agent.agent import run_crewai_agent

def main():
    parser = argparse.ArgumentParser(description="Compare Agentic Frameworks using Gemini")
    parser.add_argument(
        "--framework",
        choices=["native", "langgraph", "crewai", "all"],
        default="native",
        help="Which agent framework to execute (default: native)"
    )
    parser.add_argument(
        "--topic",
        default="solid-state batteries",
        help="The topic to research and write a report on (default: solid-state batteries)"
    )
    
    args = parser.parse_args()
    
    # Check if API Key is configured
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY is not set.")
        print("Please create a .env file with your key (see .env.example) or run: export GEMINI_API_KEY='your_api_key'")
        return
        
    topic = args.topic
    framework = args.framework
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    print("=" * 65)
    print("🚀 GEMINI AGENT FRAMEWORK COMPARISON RUNNER")
    print(f"Target Topic: '{topic}'")
    print(f"Gemini Model: '{model_name}'")
    print("=" * 65)
    
    results = {}
    
    def run_one(name, func):
        print(f"\n\n{'='*20} RUNNING FRAMEWORK: {name.upper()} {'='*20}")
        start_time = time.time()
        try:
            res = func(topic)
            elapsed = time.time() - start_time
            print(f"\n✅ {name.upper()} execution succeeded in {elapsed:.2f} seconds!")
            
            # Save files
            report_file = f"report_{name}.md"
            notes_file = f"notes_{name}.md"
            
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(res["final_report"])
            with open(notes_file, "w", encoding="utf-8") as f:
                f.write(res["research_notes"])
                
            print(f"💾 Report saved to: [./{report_file}]")
            print(f"💾 Research notes saved to: [./{notes_file}]")
            
            results[name] = {
                "status": "Success",
                "time": elapsed,
                "report_length": len(res["final_report"]),
                "notes_length": len(res["research_notes"])
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ {name.upper()} execution failed after {elapsed:.2f} seconds.")
            print(f"Error Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            results[name] = {
                "status": f"Failed ({type(e).__name__})",
                "time": elapsed,
                "report_length": 0,
                "notes_length": 0
            }
            
    if framework == "all":
        run_one("native", run_native_agent)
        run_one("langgraph", run_langgraph_agent)
        run_one("crewai", run_crewai_agent)
        
        # Print comparative summary table
        print("\n\n" + "=" * 65)
        print("📊 COMPARATIVE SUMMARY TABLE")
        print("=" * 65)
        print(f"{'Framework':<12} | {'Status':<12} | {'Time (s)':<10} | {'Notes (chars)':<14} | {'Report (chars)':<14}")
        print("-" * 65)
        for name, data in results.items():
            print(
                f"{name.upper():<12} | "
                f"{data['status']:<12} | "
                f"{data['time']:<10.2f} | "
                f"{data['notes_length']:<14} | "
                f"{data['report_length']:<14}"
            )
        print("=" * 65)
    else:
        if framework == "native":
            run_one("native", run_native_agent)
        elif framework == "langgraph":
            run_one("langgraph", run_langgraph_agent)
        elif framework == "crewai":
            run_one("crewai", run_crewai_agent)

if __name__ == "__main__":
    main()
