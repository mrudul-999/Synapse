# test_run.py
import asyncio
from src.graph import synapse_graph
from src.state import SynapseState

async def main():
    initial_state = SynapseState(query="What are the actual performance benchmarks of Llama 3 vs Claude 3.5 Sonnet?")
    
    print("🧠 Starting Synapse Multi-Agent Debate...\n")
    
    async for event in synapse_graph.astream(initial_state, stream_mode="updates"):
        for node_name, node_state in event.items():
            print(f"✅ Completed: {node_name.upper()}")
            if hasattr(node_state, 'judge_verdict') and node_state.judge_verdict:
                print(f"   → Verdict: {node_state.judge_verdict}")
                
    print("\n🎯 Final Answer:")
    print(synapse_graph.get_state({"query": initial_state.query}).values.final_answer)

if __name__ == "__main__":
    asyncio.run(main())