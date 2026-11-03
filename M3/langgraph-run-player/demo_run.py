"""Keyless demo: a small graph on fake models writes a log for the player.

    python3 demo_run.py            # → runs/log/<run_id>.json + index.json
    python3 -m http.server 8080    # → http://localhost:8080/viewer/

Graph: planner → worker ⇄ reviewer → END. The reviewer sends the document back the first time and approves
it the second time; the worker calls a tool along the way. This shows everything in the player at once: three nodes, a loop, model calls
with tokens and cost, a tool, state snapshots and checkpoints. The models are `GenericFakeChatModel`
from langchain-core: no network or API keys needed, the responses are predefined.
"""
from __future__ import annotations

import operator
import time
import uuid
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from runlog import RunRecorder, write_log

LOG_DIR = Path(__file__).resolve().parent / "runs" / "log"


# --- graph state ---------------------------------------------------------
class State(TypedDict, total=False):
    task: str                                  # what we are doing (input)
    plan: str                                  # plan from planner
    draft: str                                 # draft from worker
    needs_revision: bool                       # reviewer verdict
    feedback: str                              # reviewer remarks
    revisions: int                             # how many times it was sent back to the worker
    max_revisions: int                         # ceiling
    history: Annotated[list[str], operator.add]  # step log (reducer: append, do not overwrite)


# --- "models": predefined responses with tokens and cost, like a real provider ---
def fake_model(name: str, replies: list[tuple[str, int, int, float]]) -> GenericFakeChatModel:
    """replies: (text, input_tokens, output_tokens, cost_usd) for each call in turn."""
    messages = [AIMessage(content=text, usage_metadata={"input_tokens": i, "output_tokens": o, "total_tokens": i + o,
                                                      "input_token_details": {"cache_read": i // 4 if k else 0, "cache_creation": 0}},
                          response_metadata={"model_name": name, "token_usage": {"cost": cost}, "finish_reason": "stop",
                                             "id": f"gen-demo-{name}-{k}"})
                for k, (text, i, o, cost) in enumerate(replies)]
    return GenericFakeChatModel(messages=iter(messages))


planner_llm = fake_model("demo/planner-small", [("1. Collect facts. 2. Write sections A, B, C. 3. Add examples.", 420, 38, 0.0006)])
worker_llm = fake_model("demo/writer-large", [
    ("# Feature X\n\n## A\nFirst draft of section A.\n\n## B\nSection B.\n", 1850, 240, 0.012),
    ("# Feature X\n\n## A\nFirst draft of section A.\n\n## B\nSection B, now with the example the reviewer asked for.\n\n## C\nSection C.\n", 2300, 310, 0.016),
])
reviewer_llm = fake_model("demo/reviewer-large", [
    ("NEEDS_REVISION: section C is missing; add an example to section B.", 2100, 22, 0.011),
    ("APPROVED", 2400, 3, 0.012),
])


@tool
def lookup_facts(topic: str) -> str:
    """Look up facts on a topic (demo tool, returns a stub)."""
    time.sleep(0.4)
    return f"3 facts about {topic}: fact-1, fact-2, fact-3"


# --- nodes: state → partial update -----------------------------------
def planner(state: State) -> dict:
    time.sleep(0.3)
    reply = planner_llm.invoke([SystemMessage(content="You are a planner."), HumanMessage(content=state["task"])],
                               config={"run_name": "planner-llm"})
    return {"plan": reply.content, "history": ["planner: plan ready"]}


def worker(state: State) -> dict:
    facts = lookup_facts.invoke({"topic": state["task"]}, config={"run_name": "lookup_facts"})
    time.sleep(0.6)
    prompt = f"Plan:\n{state['plan']}\nFacts:\n{facts}\n" + (f"Previous draft:\n{state.get('draft', '')}\nFeedback:\n{state.get('feedback', '')}" if state.get("feedback") else "")
    reply = worker_llm.invoke([SystemMessage(content="You are a technical writer."), HumanMessage(content=prompt)],
                              config={"run_name": "worker-llm"})
    return {"draft": reply.content, "history": [f"worker: draft v{state.get('revisions', 0) + 1}"]}


def reviewer(state: State) -> dict:
    time.sleep(0.5)
    reply = reviewer_llm.invoke([SystemMessage(content="You are a strict reviewer."), HumanMessage(content=state["draft"])],
                                config={"run_name": "reviewer-llm"})
    needs = reply.content.startswith("NEEDS_REVISION")
    revisions = state.get("revisions", 0) + (1 if needs else 0)
    return {"needs_revision": needs, "feedback": reply.content if needs else "", "revisions": revisions,
            "history": [f"reviewer: {'sent back' if needs else 'approved'}"]}


def route(state: State) -> Literal["worker", "__end__"]:
    """Conditional edge: back to the worker while the reviewer is unhappy and the ceiling is not reached."""
    if state.get("needs_revision") and state.get("revisions", 0) <= state.get("max_revisions", 1):
        return "worker"
    return "__end__"


def build_graph():
    g = StateGraph(State)
    g.add_node("planner", planner); g.add_node("worker", worker); g.add_node("reviewer", reviewer)
    g.add_edge(START, "planner"); g.add_edge("planner", "worker"); g.add_edge("worker", "reviewer")
    g.add_conditional_edges("reviewer", route, {"worker": "worker", "__end__": END})
    return g.compile(checkpointer=InMemorySaver())   # checkpointer → state snapshots after each step


def main() -> None:
    graph = build_graph()
    run_id = str(uuid.uuid4())
    recorder = RunRecorder(run_id, name="demo-doc-agent", meta={"agent_version": "demo-0.1", "task": "Feature X"})
    config = {"callbacks": [recorder], "run_name": "demo-doc-agent",
              "configurable": {"thread_id": run_id}}          # one run = one checkpointer thread
    final = graph.invoke({"task": "Feature X", "revisions": 0, "max_revisions": 1, "history": []}, config=config)
    log = recorder.build(graph=graph, thread_config={"configurable": {"thread_id": run_id}})
    path = write_log(log, LOG_DIR)
    t = log["totals"]
    print(f"log: {path}")
    print(f"nodes {t['node_runs']}, model calls {t['llm_calls']}, tools {t['tool_calls']}, "
          f"checkpoints {len(log['checkpoints'])}, ${t['cost_usd']}, {t['duration_ms']} ms; revisions {final['revisions']}")
    print("open the player: python3 -m http.server 8080 → http://localhost:8080/viewer/")


if __name__ == "__main__":
    main()
