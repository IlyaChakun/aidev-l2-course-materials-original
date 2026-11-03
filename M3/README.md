# Module 3 · Agents and context: state and memory on LangGraph

Materials for the third module. The session: one agent - its loop, limits and budgets, state,
state persistence, memory, autonomy and a pause for a human, moving from n8n to code.

| What | Where | What for |
|---|---|---|
| Homework | [`homework.md`](homework.md) | Moving one agent of the course project to code: a LangGraph loop, a checkpointer, a pause. Submit by link in the field at the bottom of the assignment in the LMS |
| Guide: LangGraph for a coding agent | [`guides/langgraph-agent-guardrails.md`](guides/langgraph-agent-guardrails.md) | **The main homework material.** Handed to the coding agent together with the task: rules and pitfalls of state, the checkpointer, interrupt, navigation |
| Guide: LangChain Code node | [`guides/langchain-code-node-guardrails.md`](guides/langchain-code-node-guardrails.md) | The dialect of the n8n code node - for repeating the session demo. Not related to the homework |
| Guide: observability | [`guides/observability-langsmith-langfuse-n8n.md`](guides/observability-langsmith-langfuse-n8n.md) | Connecting LangSmith and Langfuse to self-hosted n8n |
| Session demo | [`examples/`](examples/) | JSON exports of two workflows (import them yourself, substitute your own credentials) + the code of three LangChain Code examples with comments |
| LangGraph run player | [`langgraph-run-player/`](langgraph-run-player/) | A visualizer for a run of your own graph: a timeline of nodes and model calls, the graph diagram, state step by step, checkpoints, cost. Without LangSmith/Langfuse; a demo without keys in 3 minutes, instructions for connecting to your own graph |
| Module slides | [`slides/m3-slides.html`](slides/m3-slides.html) | Download and open with a double click; clicking an item expands the details |

Related from the first module: [`../M1/guides/tool-design.md`](../M1/guides/tool-design.md) -
tool descriptions and the error contract, which also work for the agent tools of this module.
