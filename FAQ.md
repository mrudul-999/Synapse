# Synapse / LangGraph FAQ

This document captures frequently asked questions and conceptual explanations regarding the architecture of Synapse, particularly concerning LangGraph, state management, and multi-agent workflows.

---

### Q1: In Pydantic, why use `Field(default_factory=list)` instead of `[]` for a plan? Doesn't an agent only have one plan per session?
**A:** If you define `plan: List[str] = []`, Python creates a single list object shared across all instances of the class (the "mutable default argument" problem). By using `default_factory=list`, Pydantic calls `list()` to create a brand new, empty list for every new instance of `SynapseState`. This ensures that if you have multiple user sessions or parallel agent runs, they don't accidentally overwrite each other's plans. The plan is a `List[str]` because it typically consists of multiple actionable steps.

### Q2: How will Synapse have multiple states running at once?
**A:** `SynapseState` is the blueprint for a single workflow. You will have multiple instances of this state in several scenarios:
1. **Multiple Users (API):** Concurrent requests from different users need separate state objects.
2. **LangGraph Checkpointing:** LangGraph uses `thread_id`s to pause and resume specific runs, requiring separate states for each thread.
3. **Parallel Sub-tasks:** A main agent might spawn multiple sub-agents to research different topics simultaneously.

### Q3: At any given instant, does the graph have a state where every node is doing something simultaneously?
**A:** Usually, no. Nodes generally run **sequentially** (one at a time), not simultaneously. The state acts like a baton in a relay race. A node reads the state, executes its code (e.g., calling an LLM), and returns a dictionary of the fields it wants to update. LangGraph merges these updates into the central state and passes it to the next node.

### Q4: Can I think of LangGraph as a round table with 10 people (nodes), where a "Planner" makes a plan on a page (state) and passes it to the next person, continuing until the last person changes the state?
**A:** Yes, that is a perfect analogy! 
- **The Page** is the `SynapseState`.
- **The Schema (Pydantic)** is the form structure—people can only write in specific labeled boxes (like `query`, `plan`, `steelman_argument`).
- **The Graph Edges** represent the rules determining who passes the page to whom next (it doesn't have to go in a circle; it can loop back for revisions).

### Q5: Does `state.py` decide who to send the state to next? What is the role of the `messages` field?
**A:** **No, `state.py` only defines *WHAT* information is passed around**, not *WHO* goes next. The routing rules (who goes next) are defined by the "manager" in `graph.py` using edges. 

The `messages` field is like a running chat log on the back of the page. Because everyone shares the same state, every agent can read the `messages` log to see exactly what previous agents discovered before doing their own work. Eventually, a final node (like a Synthesizer) reads everything and fills out the `final_answer` field.

### Q6: So `graph.py` dictates the order in which the "page" is passed around?
**A:** Exactly. In `graph.py`, you add nodes (`builder.add_node()`) and define the paths between them using edges (`builder.add_edge()`). The most powerful feature is **Conditional Edges**, where a manager node (like a Judge) can decide on the fly whether to pass the page backward for revisions or forward to finish the task.

### Q7: Why do we use `await` when calling the LLM inside an agent? Doesn't LangGraph already make the other agents wait their turn?
**A:** Yes, LangGraph already ensures the *other agents* wait their turn. The `await` keyword has nothing to do with the other agents! 

Instead, `await` is an instruction to the **Python CPU** (your computer's processor). Calling an LLM API means sending data over the internet and waiting for Google/Anthropic to send a response back. This is called "Network I/O" and it is very slow in computer time (it can take seconds). 

By saying `await llm.ainvoke(...)`, you are telling Python: *"Hey, I'm waiting for a slow internet response. Please pause this specific function, put it to the side, and go do other useful things (like serving other users on the website) until the internet response arrives."* It prevents your entire application from freezing while waiting for the LLM.

### Q8: What are the exact roles of the agents in the Synapse debate loop?
**A:** You have it perfectly mapped out:
1. **Planner**: The first one to act. It looks at the query and creates a step-by-step plan.
2. **Steelman**: Acts on the plan. It checks if any Skeptic argument was made previously (if this is a loop) and makes the absolute best, most charitable possible argument to answer the query.
3. **Skeptic**: Checks the Steelman argument and acts as a critical fact-checker. It looks for logical flaws, edge cases, or scenarios where the Steelman argument might fail.
4. **Judge**: Takes both the Steelman and Skeptic's arguments and acts as the evaluator. It decides if the answer is ready to be sent (passes) or if the agents still need to revise it (loops back).
5. **Synthesizer**: The final agent. Once the Judge approves the debate, the Synthesizer takes all the findings and generates the final, verified answer!

### Q9: Why did I get a `TypeError: 'SynapseState' object is not subscriptable` or `KeyError: 'query'` when testing?
**A:** This happens when there is a mismatch between how your state is defined and how your agents try to read it.
- If your graph is built using `builder = StateGraph(dict)`, LangGraph passes a standard Python dictionary to your agents. You read it using **bracket notation** (e.g., `state['query']`). But if you don't define reducers for that dict, LangGraph's default behavior is to completely overwrite the entire state with whatever the node returns, which wipes out the original `query` (causing a `KeyError` on the next step)!
- To prevent this, we built a structured Pydantic model (`SynapseState`). If your graph uses `builder = StateGraph(SynapseState)`, LangGraph passes that actual Pydantic object to the agents. You must read it using **dot notation** (e.g., `state.query`). If your code still tries to do `state['query']`, it will crash with a `TypeError` because an object is not a dictionary!

### Q10: Why do we use an `async for` loop when looping through the graph's output (e.g., `async for state_update in graph.astream(...)`)?
**A:** When we call `graph.astream(...)`, LangGraph runs our graph asynchronously. This means the graph will pause (await) whenever it hits a slow operation inside an agent (like waiting for the LLM to reply). 

Because the graph is running asynchronously and yielding results one node at a time, it returns an **Asynchronous Generator**. Standard Python `for` loops don't know how to "wait" for the next item to be ready. 

By using `async for`, we tell Python: *"Start looping through the graph's updates. Every time you ask for the next update, it might take a few seconds (while the agent thinks). Go do other things in the background, and pause this loop until the next state update is actually ready."* This is essential for streaming real-time progress to a user interface without freezing the server!

### Q11: What is the difference between synchronous and asynchronous? If 10 people use 10 different logins on a synchronous server, will it still freeze?
**A:** Yes, the freezing problem would still persist on a purely synchronous, single-threaded server, regardless of how many different logins are used!

Here is a simple analogy:

**Synchronous (Sequential / Blocking)**
Imagine a chef in a restaurant cooking a burger.
1. The chef puts the meat on the grill.
2. The chef **stands there and stares at the meat for 5 minutes** until it's cooked.
3. Then, the chef toasts the buns and serves the burger.

If 10 customers walk in, Customer #2 cannot even get their order started until Customer #1 is completely finished. The server is "frozen" waiting for the grill.

**Asynchronous (Concurrent / Non-Blocking)**
Now imagine a better chef.
1. The chef puts the meat on the grill.
2. Instead of staring at the meat, the chef **sets a timer** and immediately starts taking orders and prepping ingredients for Customers #2 through #10.
3. When the timer goes off, the chef goes back to flip the burger.

**Why this matters for your application:**
When you ask an LLM to generate text, the computer has to send a request over the internet and wait. This is "Network I/O". 
- In a **synchronous** Python server, if User 1 asks a question, the server stops completely to wait for the LLM. Users 2 through 10 will just see a loading spinner. The server won't even acknowledge them until User 1 is done. *(Note: Traditional synchronous servers solve this by spinning up completely separate CPU processes or threads for every user, but this consumes a massive amount of RAM and CPU).*
- In an **asynchronous** Python server (like FastAPI), Python sets a "timer" using the `await` keyword. It sends User 1's request to the LLM, immediately parks that task, and is instantly free to accept the requests from Users 2 through 10. A single process can handle thousands of users concurrently this way!
