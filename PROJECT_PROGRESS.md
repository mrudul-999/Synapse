# Synapse Project Progress Tracker

This document tracks the current state of the project, including completed steps, ongoing tasks, and future milestones. It will be updated continuously as we progress.

## ✅ Completed Steps

- **Step 1: Repo Structure**
  - Initialized base directory structure (`src/`, `agents/`, `api/`, `tools/`).
  - Added `.gitignore` and `docker-compose.yml`.

- **Step 2: Dependencies**
  - Created `pyproject.toml` with necessary dependencies (LangGraph, LangChain, Pydantic, etc.).

- **Step 3: Define the Brain (`src/state.py`)**
  - Defined a robust, Pydantic V2 state (`SynapseState`) that supports the multi-agent debate loop and eventual streaming.
  - Set up necessary tracking fields like `plan`, `messages`, `steelman_argument`, `skeptic_argument`, and `judge_verdict`.

- **Step 4: The Core Graph Skeleton (`src/graph.py`)**
  - Wired up the multi-agent debate loop skeleton.
  - Set up the "manager" rules and conditional edges: if the Judge says "needs revision", it loops back to the planner/agents. If it passes, it goes to the synthesizer.

- **Step 5: Quick Local Test (`test_run.py`)**
  - Created a temporary script in the root to verify the LangGraph engine runs and routes state properly before building the FastAPI wrapper or MCP tools.
  - Implemented actual LLM calls using local Ollama (`ChatOllama`) in `src/agents/llm_agents.py` to drive the debate loop with real generated content.

## 🚧 Current / Next Steps

- **Step 6: Add one MCP server and one tool call**
  - Build a trivial MCP server first (e.g. web search via Tavily).
  - Test it standalone with the MCP inspector or a tiny script.
  - Wire it into the tool-executor node via `langchain-mcp-adapters`.
  - *Note: Don't build all three MCP servers (web search, code exec, vector DB) at once to keep debugging isolated and simpler.*
