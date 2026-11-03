# LangGraph Run Player — a player for graph runs

A single HTML file that shows a LangGraph run like a video recording: play / pause / speed /
seek. Below the player is a timeline like the browser devtools (which node ran when, how long each
model call took and cost, which tool was called), a graph diagram with the active node highlighted,
the state at any point in time with changed keys highlighted, checkpoints, and a right-hand panel
with cost, tokens and cache. At the top you can switch between all runs.

It works **without LangSmith or Langfuse**: its own callback handler writes the log to a local JSON file.
It fits any LangGraph graph, not only the one it was built on: nodes are recognized from the metadata
that LangGraph sets itself; subgraphs, `create_agent` and tools get into the log the same way.
It was built while migrating a real documentation agency from Flowise to LangGraph (one of my
consulting cases); here it is a demo on a synthetic graph.

## Quick start (3 minutes, no keys needed)

```bash
pip install -r requirements.txt      # langchain-core, langgraph
python3 demo_run.py                  # run the demo graph on fake models → runs/log/
python3 -m http.server 8080          # any static server from this folder
open http://localhost:8080/viewer/   # the player
```

The folder already contains one demo log, so the player shows a run even before you run `demo_run.py`.
Each new run adds an entry to the selector; the "refresh" button re-reads the list without
reloading the page.

Keys: `space` — play/pause, `←`/`→` — ±2 s, `,`/`.` — previous/next event,
`Home`/`End`. Click on the timeline to seek, on a bar to select an event, on a diamond in the State lane for a
state snapshot, on a circle in the Checkpoints lane for a checkpoint.

## What you see in the player

| Area | What it shows | Where it comes from |
|---|---|---|
| Player | the current event: node (what it updated in state), model call (last message → response), tool (input → output), error | `events` |
| Timeline | lanes Nodes / LLM / Tools / State / Checkpoints; playhead; tooltips | `events`, `state_snapshots`, `checkpoints` |
| Graph diagram | nodes and edges (conditional ones dashed), active node, the edge just traversed, run counter | `graph` from `graph.get_graph()` |
| State | the full state at a point in time, changed keys highlighted, values expandable | `state_snapshots` |
| Checkpoints | step, id, parent, `next` (what runs on resume), changed keys | `graph.get_state_history()` |
| Events | a table of all events with tokens and cost; click to seek | `events` |
| Right panel | cost, tokens in/out, cache read/write, reasoning, per-node breakdown, details of the current call (model, parameters, all messages, response, tool calls) | `totals`, `events` |

## Connect it to your own graph

You need two files: `runlog.py` (depends only on `langchain-core`) and `viewer/index.html`.

```python
from pathlib import Path
from runlog import RunRecorder, write_log

run_id = "…"                                   # any unique run id
rec = RunRecorder(run_id, name="my-graph", meta={"agent_version": "0.3", "user": "…"})
config = {
    "callbacks": [rec],                        # the recorder is a regular LangChain callback
    "run_name": "my-graph",
    "configurable": {"thread_id": run_id},     # needed by the checkpointer; without it there will be no checkpoints
}
final = graph.invoke(state0, config=config)
log = rec.build(graph=graph, thread_config={"configurable": {"thread_id": run_id}})
write_log(log, Path("runs/log"))               # writes <run_id>.json and rebuilds index.json
```

The player looks for logs at `../runs/log/` relative to `viewer/`. Put `viewer/` and `runs/log/`
side by side (as in this folder) and open the player through any static server — `file://` will not work,
the browser will not allow `fetch` from disk.

Things to keep in mind:

- **Checkpoints** appear only if the graph is compiled with a checkpointer
  (`compile(checkpointer=InMemorySaver())`, `SqliteSaver`, Postgres) and a `thread_id` is passed.
  These are the very state snapshots after each step from which a run can be resumed.
- **Cost** is taken from the provider's response. With OpenRouter you have to ask for it:
  `ChatOpenAI(..., extra_body={"usage": {"include": True}})` — then `token_usage.cost` carries the
  price of each call. Anthropic/OpenAI directly do not return cost in the response — you only get tokens
  (including `cache_read` / `cache_creation`).
- **Call names**: `llm.invoke(messages, config={"run_name": "writer-llm"})` gives a readable name
  on the timeline; without it you get the class name (`ChatOpenAI`). The node is still identified from the metadata.
- **Structured output** via `with_structured_output(..., include_raw=True)` preserves the call's tokens and
  cost; without `include_raw` the raw message is lost.
- **Errors** are recorded too: a failed node/call is marked red, and the log is saved if
  you call `build()` in `finally`.
- **Tools and agents**: a `tool.invoke(...)` call or a `ToolNode`, as well as `create_agent` inside
  a node, produce `tool` events and nested nodes — the player shows the Tools lane and the nesting in the events
  table.
- The log stores full prompts and responses. If they contain secrets or personal data —
  do not commit `runs/log/` (in the demo the folder is in the repository only as an example).

## Runs made before the recorder was connected

If LangSmith tracing was enabled, old runs can be restored into the same format:

```bash
pip install langsmith
LANGSMITH_API_KEY=… LANGSMITH_PROJECT=… python3 backfill_langsmith.py <run_id> [<run_id> …]
```

`run_id` is the id of the root run (trace) in LangSmith. Such runs have no checkpoints, and no graph
diagram either (it is not in the trace); in the player they are marked "backfill from LangSmith".

## A self-contained file to send to colleagues

```bash
python3 build_embedded.py --limit 5     # → runs/viewer-embedded.html: the player + the last 5 logs inside
```

The file opens with a double click, no server needed. Size is about 300–500 KB per run.

## Log format `langgraph-runlog/1`

```jsonc
{
  "schema": "langgraph-runlog/1",
  "run_id": "…", "name": "my-graph", "thread_id": "…",
  "started_at": "2026-08-28T15:12:03.120+00:00", "duration_ms": 45641, "status": "ok",
  "meta": { "agent_version": "…", "source": "recorder | langsmith-backfill", "…": "any fields of your own" },
  "graph": { "nodes": [{"id": "__start__"}, {"id": "writer"}, …],
             "edges": [{"source": "reviewer", "target": "writer", "conditional": true}, …] },
  "events": [
    { "id": "…", "parent": null, "kind": "graph", "name": "my-graph", "start_ms": 0, "end_ms": 45641,
      "status": "ok", "input": {…state on input…}, "output": {…state on output…} },
    { "id": "…", "parent": "…", "kind": "node", "name": "writer", "node": "writer", "step": 1,
      "start_ms": 0, "end_ms": 28700, "output": {…state update…} },
    { "id": "…", "parent": "…", "kind": "llm", "name": "writer-llm", "node": "writer", "step": 1,
      "model": "anthropic/claude-opus-4.5", "provider": "openai",
      "params": {"temperature": 0.3, "max_tokens": 16384}, "tools": [],
      "messages": [{"role": "system", "content": "…"}, {"role": "human", "content": "…"}],
      "response": {"role": "ai", "content": "…", "tool_calls": []},
      "usage": {"input_tokens": 12100, "output_tokens": 1287, "total_tokens": 13387,
                "cache_read": 0, "cache_creation": 0, "reasoning": 0},
      "cost_usd": 0.0927, "generation_id": "gen-…", "finish_reason": "stop" },
    { "kind": "tool", "name": "lookup_facts", "input": {"topic": "…"}, "output": "…" },
    { "kind": "internal", "name": "route", "output": "worker" }        // conditional-edge router: the chosen branch
  ],
  "state_snapshots": [
    { "at_ms": 0, "label": "graph input", "full": true, "state": {…} },
    { "at_ms": 28700, "label": "before reviewer (step 2)", "full": false, "changed": {"draft": "…"} },
    { "at_ms": 45641, "label": "graph output", "full": false, "changed": {"final": "…"} }
  ],
  "checkpoints": [
    { "checkpoint_id": "…", "parent_checkpoint_id": "…", "step": 1, "source": "loop", "next": ["reviewer"],
      "created_at": "…", "changed_keys": ["draft"], "tasks": ["reviewer"] }
  ],
  "totals": { "llm_calls": 3, "tool_calls": 1, "node_runs": 4, "input_tokens": 32500, "output_tokens": 2359,
              "cache_read": 0, "cache_creation": 0, "reasoning": 0, "cost_usd": 0.1705, "duration_ms": 45641, "errors": 0 }
}
```

How the recorder tells what is what:

| What | Signature |
|---|---|
| graph root | a chain run without a parent |
| node | a chain run whose `metadata.langgraph_node == name` and which has the tag `graph:step:N` |
| model call | chat model events (`on_chat_model_start` / `on_llm_end`) |
| tool | tool events |
| router | an internal run with a string output — the branch name |
| state snapshot | the node's `inputs` at start is the whole state on input; the graph output is the final one |
| checkpoint | `graph.get_state_history(thread_config)` |

## Files

| File | What |
|---|---|
| `viewer/index.html` | the player, no build and no dependencies; dark theme follows the system setting |
| `runlog.py` | the log recorder (`RunRecorder`, `write_log`, `assemble_log`) |
| `demo_run.py` | a demo graph on fake models, writes a log without keys |
| `build_embedded.py` | builds a self-contained HTML with the logs inside |
| `backfill_langsmith.py` | restores the log of an old run from LangSmith |
| `runs/log/` | logs (`<run_id>.json` + `index.json`); the repository has one demo log |
