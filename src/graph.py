# src/graph.py
from langgraph.graph import StateGraph, END
from src.state import SynapseState

# Placeholder functions (we will implement these in Step 5)
def planner_node(state: SynapseState):
    print("[Planner] Breaking down query...")
    state.current_node = "planner"
    state.plan = ["1. Search for context", "2. Analyze findings", "3. Draft answer"]
    return state

def steelman_node(state: SynapseState):
    print("[Steelman] Building the strongest possible argument for the draft...")
    state.current_node = "steelman"
    state.steelman_argument = "The draft is correct because..."
    return state

def skeptic_node(state: SynapseState):
    print("[Skeptic] Finding flaws, edge cases, and missing citations...")
    state.current_node = "skeptic"
    state.skeptic_argument = "However, it fails to consider..."
    return state

def judge_node(state: SynapseState):
    print("[Judge] Evaluating the debate...")
    state.current_node = "judge"
    # Simple mock logic for now: allow 1 revision max
    if state.revision_count < 1:
        state.needs_revision = True
        state.revision_count += 1
        state.judge_verdict = "REVISE: Skeptic raised valid points about missing sources."
    else:
        state.needs_revision = False
        state.judge_verdict = "APPROVED: Arguments are balanced and verified."
    return state

def synthesizer_node(state: SynapseState):
    print("[Synthesizer] Generating final verified answer...")
    state.current_node = "synthesizer"
    state.final_answer = "Based on the verified debate, here is the answer..."
    return state

def should_revise(state: SynapseState) -> str:
    if state.needs_revision:
        return "revise"
    return "synthesize"

# Build the Graph
builder = StateGraph(SynapseState)

# Add nodes
builder.add_node("planner", planner_node)
builder.add_node("steelman", steelman_node)
builder.add_node("skeptic", skeptic_node)
builder.add_node("judge", judge_node)
builder.add_node("synthesizer", synthesizer_node)

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