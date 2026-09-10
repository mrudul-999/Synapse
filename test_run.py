# test_run.py
import asyncio
from dotenv import load_dotenv
load_dotenv()

from src.graph import synapse_graph
from src.state import SynapseState

async def main():
    initial_state = {
    "query": "Who do you think is hotter conventionally? Sydney Sweeney or Ana De Armas",
    "plan": [],
    "current_step_index": 0,
    "messages": [],
    "current_node": "init",
    "steelman_argument": None,
    "skeptic_argument": None,
    "judge_verdict": None,
    "needs_revision": True,
    "revision_count": 0,
    "final_answer": None,
    "token_budget_remaining": 50000
    }
    
    print("Hey I am starting Synapse Multi-Agent Debate...\n")
    
    final_state = {}
    # LangGraph yields the state as a dictionary during streaming
    async for state_update in synapse_graph.astream(initial_state, stream_mode="values"):
        final_state = state_update
        node_name = final_state.get('current_node','unknown')
        print(f"✅ Node executed: {node_name.upper()}")
        
        # Print verdict only when the judge node finishes
        if final_state.get('judge_verdict') and node_name == "judge":
            verdict = final_state.get('judge_verdict')
            if "VERDICT:" in verdict:
                verdict_line = [line for line in verdict.split('\n') if 'VERDICT:' in line][0]
                print(f"   → {verdict_line}")
                
    print("\n🎯 Final Answer:")
    print(final_state.get('final_answer',"No answer generated"))

if __name__ == "__main__":
    asyncio.run(main())