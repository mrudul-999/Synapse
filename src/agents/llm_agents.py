# src/agents/llm_agents.py
import os
from typing import Dict, Any
from langchain_ollama import ChatOllama
from src.state import SynapseState

def extract_text(response) -> str:
    if isinstance(response.content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content)
    return str(response.content)

# Initialize the LLM (using local Ollama)
llm = ChatOllama(
    model="llama3.2",
    temperature=0.7,
)

async def planner_agent(state: SynapseStatze) -> Dict[str, Any]:
    """Breaks down the query into a step-by-step plan"""
    query = state.query
    revision_count = state.revision_count
    
    # If this is a revision, include the judge's feedback
    context = ""
    if revision_count > 0 and state.judge_verdict:
        context = f"\n\nIMPORTANT: This is revision #{revision_count}. The judge said: {state.judge_verdict}\nPlease adjust your plan to address these concerns."
    
    prompt = f"""You are a strategic planner for a multi-agent research system.

    Your task: Break down this query into a clear, actionable research plan.

    Query: {query}{context}

    Output a numbered list of 3-5 specific steps to research and answer this query.
    Each step should be concrete and actionable (e.g., "Search for recent benchmarks comparing X and Y", "Analyze performance metrics for Z").

    Be specific about what information you need to find."""

    response = await llm.ainvoke([
        ("system", "You create clear, actionable research plans."),
        ("human", prompt)
    ])
    
    plan_text = extract_text(response).strip()
    plan_steps = [step.strip() for step in plan_text.split('\n') if step.strip() and step.strip()[0].isdigit()]
    
    return {
        "plan": plan_steps,
        "current_step_index": 0,
        "current_node": "planner",
        "messages": state.messages + [{"role": "assistant", "content": f"Plan: {plan_text}", "agent_name": "planner"}]
    }

async def steelman_agent(state: SynapseState) -> Dict[str, Any]:
    """Builds the strongest possible argument for the current draft/understanding"""
    query = state.query
    plan = '\n'.join(state.plan)
    
    # Get previous debate context if this is a revision
    previous_skeptic = state.skeptic_argument
    context = ""
    if previous_skeptic:
        context = f"\n\nThe skeptic previously raised these concerns: {previous_skeptic}\nAddress these concerns in your steelman argument."
    
    prompt = f"""You are the "Steelman" agent in a multi-agent debate system.

    Your role: Build the STRONGEST possible argument for answering this query correctly.
    Assume the current understanding is correct and defend it vigorously.

    Query: {query}

    Research Plan:
    {plan}{context}

    Instructions:
    - Present the most compelling evidence and reasoning
    - Cite specific facts, data points, or logical arguments
    - Be charitable to the position - make it as strong as possible
    - If there are gaps in knowledge, note what information would strengthen the argument

    Write a detailed steelman argument (2-3 paragraphs)."""

    response = await llm.ainvoke([
        ("system", "You build strong, well-reasoned arguments. Be thorough and charitable."),
        ("human", prompt)
    ])
    
    steelman_arg = extract_text(response).strip()
    
    return {
        "steelman_argument": steelman_arg,
        "current_node": "steelman",
        "messages": state.messages + [{"role": "assistant", "content": f"Steelman: {steelman_arg}", "agent_name": "steelman"}]
    }

async def skeptic_agent(state: SynapseState) -> Dict[str, Any]:
    """Finds flaws, edge cases, and weaknesses in the steelman argument"""
    query = state.query
    steelman_arg = state.steelman_argument or ""
    
    prompt = f"""You are the "Skeptic" agent in a multi-agent debate system.

    Your role: Critically examine the steelman argument and find its weaknesses.
    You are a rigorous fact-checker and critical thinker.

    Query: {query}

    Steelman Argument to Critique:
    {steelman_arg}

    Instructions:
    - Identify logical fallacies, unsupported claims, or missing evidence
    - Point out edge cases or scenarios where the argument fails
    - Question assumptions and demand citations
    - Be constructive but rigorous - your goal is to strengthen the final answer by stress-testing it
    - If the argument is weak, say so clearly and explain why

    Write a detailed skeptic critique (2-3 paragraphs)."""

    response = await llm.ainvoke([
        ("system", "You are a rigorous skeptic. Find flaws and demand evidence. Be constructive but critical."),
        ("human", prompt)
    ])
    
    skeptic_arg = extract_text(response).strip()
    
    return {
        "skeptic_argument": skeptic_arg,
        "current_node": "skeptic",
        "messages": state.messages + [{"role": "assistant", "content": f"Skeptic: {skeptic_arg}", "agent_name": "skeptic"}]
    }

async def judge_agent(state: SynapseState) -> Dict[str, Any]:
    """Evaluates the debate and decides if the answer is ready or needs revision"""
    query = state.query
    steelman_arg = state.steelman_argument or ""
    skeptic_arg = state.skeptic_argument or ""
    revision_count = state.revision_count
    
    prompt = f"""You are the "Judge" agent in a multi-agent debate system.

    Your role: Evaluate the debate between the Steelman and Skeptic agents and decide if the answer is ready or needs revision.

    Query: {query}

    Steelman Argument:
    {steelman_arg}

    Skeptic Critique:
    {skeptic_arg}

    Current Revision Count: {revision_count}

    Instructions:
    1. Evaluate whether the steelman argument adequately addresses the query
    2. Evaluate whether the skeptic's concerns are valid and important
    3. Decide: Is the answer ready, or does it need revision?
    4. If revision is needed, provide specific guidance on what to improve

    Output Format (be exact):
    VERDICT: [APPROVE or REVISE]
    REASONING: [Your detailed reasoning here]
    GUIDANCE: [If REVISE, specific steps to improve. If APPROVE, write "Ready for synthesis."]

    Note: After {2} revisions, you should be more lenient and approve unless there are critical errors."""

    response = await llm.ainvoke([
        ("system", "You are a fair but rigorous judge. Evaluate arguments objectively and provide clear verdicts."),
        ("human", prompt)
    ])
    
    verdict_text = extract_text(response).strip()
    
    # Parse the verdict
    needs_revision = "REVISE" in verdict_text.upper() and "APPROVE" not in verdict_text.upper()
    
    # Extract reasoning (everything after "REASONING:")
    reasoning = verdict_text
    if "REASONING:" in verdict_text:
        reasoning = verdict_text.split("REASONING:")[1].strip()
    
    return {
        "judge_verdict": verdict_text,
        "needs_revision": needs_revision,
        "revision_count": revision_count + 1 if needs_revision else revision_count,
        "current_node": "judge",
        "messages": state.messages + [{"role": "assistant", "content": f"Judge: {verdict_text}", "agent_name": "judge"}]
    }

async def synthesizer_agent(state: SynapseState) -> Dict[str, Any]:
    """Generates the final, verified answer based on the debate"""
    query = state.query
    steelman_arg = state.steelman_argument or ""
    skeptic_arg = state.skeptic_argument or ""
    judge_verdict = state.judge_verdict or ""
    
    prompt = f"""You are the "Synthesizer" agent in a multi-agent debate system.

    Your role: Generate the final, verified answer to the query based on the debate between the Steelman and Skeptic agents, and the Judge's verdict.

    Query: {query}

    Steelman Argument:
    {steelman_arg}

    Skeptic Critique:
    {skeptic_arg}

    Judge's Verdict:
    {judge_verdict}

    Instructions:
    - Synthesize the strongest points from the steelman argument
    - Address valid concerns raised by the skeptic
    - Follow the judge's guidance if any revisions were suggested
    - Provide a clear, well-structured, and comprehensive answer
    - If information is uncertain or debated, acknowledge this explicitly
    - Cite specific evidence or reasoning where appropriate

    Write the final answer (3-5 paragraphs, well-structured)."""

    response = await llm.ainvoke([
        ("system", "You synthesize balanced, well-reasoned answers from debate transcripts. Be clear and comprehensive."),
        ("human", prompt)
    ])
    
    final_answer = extract_text(response).strip()
    
    return {
        "final_answer": final_answer,
        "current_node": "synthesizer",
        "messages": state.messages + [{"role": "assistant", "content": f"Final Answer: {final_answer}", "agent_name": "synthesizer"}]
    }