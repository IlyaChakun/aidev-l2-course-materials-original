"""Demo 2: a checkpoint continues the graph, it does not undo the outside world.

A two-node graph draft -> send with a file SqliteSaver and no model. `start` kills the process
right after `send` has written to outbox.txt, before the node returns. `resume` continues the
thread from the last snapshot, so `send` runs again from its first line.
"""
import hashlib, os, sys
from pathlib import Path
from typing import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

HERE = Path(__file__).parent
OUTBOX, DB = HERE / "outbox.txt", HERE / "checkpoints.sqlite"
IDEMPOTENT = "--idempotent" in sys.argv
CRASH = False


class State(TypedDict):
    ticket_id: int
    draft: str


def draft(state: State) -> dict:
    return {"draft": "The invitation link is valid for 7 days. Please re-send it."}


def send(state: State) -> dict:
    key = f"{state['ticket_id']}-{hashlib.sha256(state['draft'].encode()).hexdigest()[:8]}"
    sent = OUTBOX.read_text() if OUTBOX.exists() else ""
    if IDEMPOTENT and f"key={key}" in sent:
        print(f"send: key {key} already in the outbox, skipping")
        return {}
    with OUTBOX.open("a") as f:                                  # the effect on the outside world
        f.write(f"reply to ticket {state['ticket_id']}" + (f"  key={key}" if IDEMPOTENT else "") + "\n")
    print(f"send: wrote the reply to ticket {state['ticket_id']}", flush=True)
    if CRASH:
        print("send: the process dies before the node returns", flush=True)
        os._exit(1)
    return {}


builder = StateGraph(State)
builder.add_node("draft", draft)
builder.add_node("send", send)
builder.add_edge(START, "draft")
builder.add_edge("draft", "send")
builder.add_edge("send", END)

if __name__ == "__main__":
    mode, thread = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    if mode == "reset":
        for p in (OUTBOX, DB, Path(f"{DB}-wal"), Path(f"{DB}-shm")):
            p.unlink(missing_ok=True)
        print("reset: outbox and checkpoints removed")
        sys.exit(0)
    cfg = {"configurable": {"thread_id": thread}}
    with SqliteSaver.from_conn_string(str(DB)) as saver:
        graph = builder.compile(checkpointer=saver)
        if mode == "start":
            CRASH = True
            graph.invoke({"ticket_id": 2, "draft": ""}, cfg, durability="sync")
        elif mode == "resume":
            graph.invoke(None, cfg, durability="sync")           # continue from the last snapshot
            print("resume: the graph finished")
        snap = graph.get_state(cfg)
        print(f"state {thread}: next={snap.next}  draft={snap.values.get('draft', '')[:40]!r}")
