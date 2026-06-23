# 🧠 Project Memory: Comparing Agent Frameworks

This file tracks the design decisions, resolutions, and benchmark findings for the agent comparison workspace.

---

## 🎯 Project Context & Goal
The objective of this project is to implement, test, and benchmark the same multi-agent workflow (Researcher with Web Search + Technical Writer) across three orchestration styles using **Google Gemini**:
1. **Native SDK**: Imperative, direct scripting.
2. **LangGraph**: Stateful, cyclic graph control.
3. **CrewAI**: Declarative, role-based orchestration.

---

## ⚙️ Current Implementation State

### 📂 Directory Structure Map
* [`.env`](file:///Users/sureshthomas/source/comparing-agent-frameworks/.env) - Holds API credentials (`GEMINI_API_KEY`) and active model name.
* [`requirements.txt`](file:///Users/sureshthomas/source/comparing-agent-frameworks/requirements.txt) - Holds dependencies.
* [`shared/tools.py`](file:///Users/sureshthomas/source/comparing-agent-frameworks/shared/tools.py) - DuckDuckGo Search with a local mock database fallback.
* [`native_agent/agent.py`](file:///Users/sureshthomas/source/comparing-agent-frameworks/native_agent/agent.py) - Procedural execution logic.
* [`langgraph_agent/agent.py`](file:///Users/sureshthomas/source/comparing-agent-frameworks/langgraph_agent/agent.py) - Cyclic graphs with `safe_extract_text` logic.
* [`crewai_agent/agent.py`](file:///Users/sureshthomas/source/comparing-agent-frameworks/crewai_agent/agent.py) - Crew, task callbacks, and LiteLLM/LLM wrapper execution.
* [`run.py`](file:///Users/sureshthomas/source/comparing-agent-frameworks/run.py) - Main comparison runner script.
* [`README.md`](file:///Users/sureshthomas/source/comparing-agent-frameworks/README.md) - Setup and execution documentation.
* [`langgraph_vs_n8n.md`](file:///Users/sureshthomas/source/comparing-agent-frameworks/langgraph_vs_n8n.md) - Conceptual guide comparing LangGraph and n8n platform orchestration.

---

## 📊 Benchmark Telemetry Results
*Model: `gemini-flash-lite-latest` (Gemini 1.5 Flash 8B)*

| Framework | Status | Time (s) | Notes Length | Report Length |
| :--- | :--- | :--- | :--- | :--- |
| **NATIVE** | Success | **24.43s** | 4,105 chars | 5,276 chars |
| **LANGGRAPH** | Success | **34.17s** | 2,754 chars | 4,721 chars |
| **CREWAI** | Success | **36.67s** | 2,655 chars | 4,993 chars |

---

## 🛠️ Key Decisions & Bug Resolutions

### 1. API Quota Limits (429 Resource Exhausted)
* **Problem**: Newer/free accounts on Gemini API have a very strict daily quota of **20 requests per day** on `gemini-2.5-flash`, which is easily exhausted during agent loops.
* **Resolution**: Configured the model in `.env` to `gemini-flash-lite-latest` (Gemini 1.5 Flash 8B). This stable model features higher daily quotas (1,500 RPD) and is less prone to temporary load spikes (503 Service Unavailable).
* **Spacing**: Added `time.sleep(15)` between the research phase and writing phase in all frameworks to avoid rapid-fire API request rate limits.
* **Prompt Constraint**: Instructed the research agents to limit themselves to exactly **one** broad search tool call.

### 2. LangGraph API Turn Order Validation (400 Invalid Argument)
* **Problem**: Gemini API requires strict turn alternation: `user` -> `model` -> `tool` (function response) -> `model`. LangChain's system message mapping caused formatting issues that violated this pattern, resulting in a 400 validation error in subsequent loop turns. Additionally, local variables in nodes led to the initial message being lost.
* **Resolution**:
  1. Simplified the LangGraph message state by passing instructions directly within the initial `HumanMessage` inside `initial_state`, completely avoiding `SystemMessage` structural issues.
  2. Simplified `researcher_node` to use the state directly, preserving the initial user message.

### 3. LangGraph Content Output Structure (TypeError)
* **Problem**: LangChain's Gemini model wrapper sometimes returns message content as a `list` of parts rather than a plain string, which throws `TypeError: write() argument must be str, not list` when writing to output files.
* **Resolution**: Implemented the `safe_extract_text` utility in `langgraph_agent/agent.py` to recursively parse and join list elements back into clean strings before outputs are written.
