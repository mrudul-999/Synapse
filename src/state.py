# src/state.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from langgraph.graph import add_messages
from typing_extensions import Annotated

class AgentMessage(BaseModel):
    role: str
    content: str
    agent_name: str

class SynapseState(BaseModel):
    # The original user query
    query: str
    
    # The hierarchical plan (starts simple, can be upgraded to a tree later)
    plan: List[str] = Field(default_factory=list)
    current_step_index: int = 0
    
    # Messages history (using LangGraph's add_messages reducer for thread safety)
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    
    # Debate tracking
    steelman_argument: Optional[str] = None
    skeptic_argument: Optional[str] = None
    judge_verdict: Optional[str] = None
    needs_revision: bool = True
    revision_count: int = 0
    
    # Final output
    final_answer: Optional[str] = None
    
    # Telemetry / Streaming metadata
    current_node: str = "init"
    token_budget_remaining: int = 50000