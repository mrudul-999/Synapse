# src/graph.py
from langgraph.graph import StateGraph, END
from src.state import SynapseState

from src.agents.llm_agents import (
    planner_agent,
    steelman_agent,
    skeptic_agent,
    judge_agent,
    synthesizer_agent
)

# Placeholder functions (we will implement these in Step 5)


def should_revise(state: SynapseState) -> str:
    """Determine if we should revise or synthesize based on judge verdict"""
    # Hard limit to prevent infinite debate loops!
    if state.revision_count >= 2:
        return "synthesize"
        
    if state.needs_revision == True:
        return "revise"
    return "synthesize"

# Build the Graph
builder = StateGraph(SynapseState)

# Add nodes
builder.add_node("planner", planner_agent)
builder.add_node("steelman", steelman_agent)
builder.add_node("skeptic", skeptic_agent)
builder.add_node("judge", judge_agent)
builder.add_node("synthesizer", synthesizer_agent)

# Define the flow
builder.set_entry_point("planner")
builder.add_edge("planner", "steelman")
builder.add_edge("steelman", "skeptic")
builder.add_edge("skeptic", "judge")

# Conditional edge based on Judge's verdict
builder.add_conditional_edges(
    "judge",
    should_revise,
    {
        "revise": "planner", # Loop back to re-plan/research
        "synthesize": "synthesizer"
    }
)

builder.add_edge("synthesizer", END)

# Compile the graph
synapse_graph = builder.compile()