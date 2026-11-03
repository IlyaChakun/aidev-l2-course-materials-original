"""LangGraph run log — data for the player (`viewer/index.html`).

One run → one JSON `runs/log/<run_id>.json` (schema `langgraph-runlog/1`, described in
`README.md`). It is written by a generic LangChain callback handler, so it fits
any LangGraph graph, not only this one: nodes are recognized from the metadata that LangGraph
puts into every run (`langgraph_node`, `langgraph_step`), LLM calls — from chat model
events, tools — from tool events. Subgraphs and `create_agent` inside a node produce
nested events of the same shape.

What goes into the log:
* `events` — a flat list with `parent`: graph → node → llm/tool/internal (routers etc.);
  each has start/end in ms from the start of the run, input/output; for LLM calls — messages, response,
  call parameters, tokens (including cache), cost, generation id;
* `state_snapshots` — state at the graph input, at each node's input and at the graph output
  (the first in full, the rest only changed keys);
* `checkpoints` — the checkpointer history (if the graph is compiled with one): id, step, `next`,
  parent, time, changed keys;
* `graph` — nodes and edges from `graph.get_graph()`;
* `totals` — calls, tokens, cache, cost.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage

SCHEMA = "langgraph-runlog/1"
MAX_STR = 200_000  # protection against giant strings in the log


# ---------------------------------------------------------------------------
# Serialization: anything that can appear in state/messages → JSON
# ---------------------------------------------------------------------------

def jsonable(value: Any, depth: int = 0) -> Any:
    if depth > 12:
        return str(value)[:MAX_STR]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= MAX_STR else value[:MAX_STR] + f"…[truncated, {len(value)} chars in total]"
    if isinstance(value, BaseMessage):
        return message_to_dict(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v, depth + 1) for v in value]
    if hasattr(value, "model_dump"):
        try:
            return jsonable(value.model_dump(), depth + 1)
        except Exception:  # noqa: BLE001
            return str(value)[:MAX_STR]
    if isinstance(value, (datetime, UUID)):
        return str(value)
    return str(value)[:MAX_STR]


def message_to_dict(message: BaseMessage) -> dict:
    """LangChain message → {role, content, tool_calls?, name?}."""
    out: dict[str, Any] = {"role": message.type, "content": jsonable(message.content)}
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        out["tool_calls"] = jsonable(tool_calls)
    if getattr(message, "name", None):
        out["name"] = message.name
    if getattr(message, "tool_call_id", None):
        out["tool_call_id"] = message.tool_call_id
    return out


def state_diff(before: dict | None, after: dict | None) -> dict:
    """Keys that changed between two state snapshots, with their new values."""
    before = before or {}
    after = after or {}
    changed = {}
    for key, value in after.items():
        if key not in before or json.dumps(before[key], sort_keys=True, default=str) != json.dumps(value, sort_keys=True, default=str):
            changed[key] = value
    for key in before:
        if key not in after:
            changed[key] = None
    return changed


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

class RunRecorder(BaseCallbackHandler):
    """Collects the events of one run. Passed in `config["callbacks"]` on invoke."""

    def __init__(self, run_id: str, name: str, meta: dict | None = None) -> None:
        self.run_id = str(run_id)
        self.name = name
        self.meta = meta or {}
        self.t0 = time.time()
        self.events: dict[str, dict] = {}   # LangChain run_id → event
        self.order: list[str] = []          # start order

    # --- helpers ---
    def _ms(self) -> int:
        return int((time.time() - self.t0) * 1000)

    def _start(self, kind: str, name: str, run_id: UUID, parent_run_id: UUID | None, tags: list | None,
               metadata: dict | None, **fields: Any) -> dict:
        md = metadata or {}
        event = {
            "id": str(run_id),
            "parent": str(parent_run_id) if parent_run_id else None,
            "kind": kind,
            "name": name,
            "node": md.get("langgraph_node"),
            "step": md.get("langgraph_step"),
            "checkpoint_ns": md.get("langgraph_checkpoint_ns"),
            "tags": [t for t in (tags or []) if not t.startswith("seq:")],
            "start_ms": self._ms(),
            "end_ms": None,
            "status": "running",
            **fields,
        }
        self.events[str(run_id)] = event
        self.order.append(str(run_id))
        return event

    def _end(self, run_id: UUID, **fields: Any) -> None:
        event = self.events.get(str(run_id))
        if event is None:
            return
        event["end_ms"] = self._ms()
        event["status"] = fields.pop("status", "ok")
        event.update(fields)

    @staticmethod
    def _name(serialized: dict | None, kwargs: dict) -> str:
        if kwargs.get("name"):
            return kwargs["name"]
        if serialized:
            return serialized.get("name") or (serialized.get("id") or ["?"])[-1]
        return "?"

    # --- chains: graph, nodes, internal runnables ---
    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, tags=None, metadata=None, **kwargs):
        name = self._name(serialized, kwargs)
        md = metadata or {}
        if parent_run_id is None:
            kind = "graph"
        elif md.get("langgraph_node") == name and any(t.startswith("graph:step:") for t in (tags or [])):
            kind = "node"
        else:
            kind = "internal"
        fields: dict[str, Any] = {}
        if kind in ("graph", "node"):
            fields["input"] = jsonable(inputs)  # state on input
        self._start(kind, name, run_id, parent_run_id, tags, metadata, **fields)

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        event = self.events.get(str(run_id))
        if event is None:
            return
        fields: dict[str, Any] = {}
        if event["kind"] in ("graph", "node"):
            fields["output"] = jsonable(outputs)  # graph: the final state; node: its update
        elif event["kind"] == "internal":
            out = jsonable(outputs)
            # conditional-edge routers return the branch name — worth showing
            if isinstance(out, str) or (isinstance(out, list) and all(isinstance(x, str) for x in out)):
                fields["output"] = out
        self._end(run_id, **fields)

    def on_chain_error(self, error, *, run_id, **kwargs):
        self._end(run_id, status="error", error=f"{type(error).__name__}: {error}")

    # --- models ---
    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, tags=None, metadata=None, **kwargs):
        md = metadata or {}
        params = kwargs.get("invocation_params") or {}
        self._start(
            "llm", self._name(serialized, kwargs), run_id, parent_run_id, tags, metadata,
            model=md.get("ls_model_name") or params.get("model") or params.get("model_name"),
            provider=md.get("ls_provider"),
            params={k: params.get(k) for k in ("temperature", "max_tokens", "top_p", "tool_choice", "response_format") if params.get(k) is not None},
            tools=[t.get("function", {}).get("name") if isinstance(t, dict) else str(t) for t in (params.get("tools") or [])],
            messages=[message_to_dict(m) for m in (messages[0] if messages else [])],
        )

    def on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None, tags=None, metadata=None, **kwargs):
        md = metadata or {}
        params = kwargs.get("invocation_params") or {}
        self._start("llm", self._name(serialized, kwargs), run_id, parent_run_id, tags, metadata,
                    model=md.get("ls_model_name") or params.get("model"), provider=md.get("ls_provider"),
                    params={}, tools=[], messages=[{"role": "human", "content": p} for p in prompts])

    def on_llm_end(self, response, *, run_id, **kwargs):
        event = self.events.get(str(run_id))
        if event is None:
            return
        gen = None
        try:
            gen = response.generations[0][0]
        except (IndexError, AttributeError):
            pass
        message = getattr(gen, "message", None)
        usage = dict(getattr(message, "usage_metadata", None) or {}) if message is not None else {}
        resp_md = dict(getattr(message, "response_metadata", None) or {}) if message is not None else {}
        token_usage = resp_md.get("token_usage") or (response.llm_output or {}).get("token_usage") or {}
        details_in = usage.get("input_token_details") or {}
        details_out = usage.get("output_token_details") or {}
        self._end(
            run_id,
            response=message_to_dict(message) if message is not None else {"content": getattr(gen, "text", "")},
            usage={
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "cache_read": details_in.get("cache_read"),
                "cache_creation": details_in.get("cache_creation"),
                "reasoning": details_out.get("reasoning"),
            },
            cost_usd=token_usage.get("cost"),
            model=resp_md.get("model_name") or event.get("model"),
            generation_id=resp_md.get("id"),
            finish_reason=resp_md.get("finish_reason"),
        )

    def on_llm_error(self, error, *, run_id, **kwargs):
        self._end(run_id, status="error", error=f"{type(error).__name__}: {error}")

    # --- tools (for create_agent / tool nodes) ---
    def on_tool_start(self, serialized, input_str, *, run_id, parent_run_id=None, tags=None, metadata=None, inputs=None, **kwargs):
        self._start("tool", self._name(serialized, kwargs), run_id, parent_run_id, tags, metadata,
                    input=jsonable(inputs if inputs is not None else input_str))

    def on_tool_end(self, output, *, run_id, **kwargs):
        self._end(run_id, output=jsonable(output))

    def on_tool_error(self, error, *, run_id, **kwargs):
        self._end(run_id, status="error", error=f"{type(error).__name__}: {error}")

    # --- log assembly ---
    def build(self, graph=None, thread_config: dict | None = None, extra: dict | None = None) -> dict:
        """Build the final JSON. `graph` and `thread_config` are needed for the diagram and checkpoints."""
        events = [self.events[i] for i in self.order]
        checkpoints = collect_checkpoints(graph, thread_config) if graph is not None and thread_config else []
        graph_json = graph_to_json(graph) if graph is not None else None
        return assemble_log(
            run_id=self.run_id, name=self.name, started_at=datetime.fromtimestamp(self.t0, tz=timezone.utc),
            events=events, graph_json=graph_json, checkpoints=checkpoints,
            thread_id=(thread_config or {}).get("configurable", {}).get("thread_id"),
            meta={**self.meta, **(extra or {})},
        )


# ---------------------------------------------------------------------------
# Assembling the log from a list of events — shared by the recorder and the LangSmith backfill
# ---------------------------------------------------------------------------

def graph_to_json(graph) -> dict:
    gj = graph.get_graph().to_json()
    return {"nodes": [{"id": n["id"], "type": n.get("type")} for n in gj["nodes"]], "edges": gj["edges"]}


def collect_checkpoints(graph, thread_config: dict) -> list[dict]:
    """Checkpointer history of a thread: oldest to newest, with the changed state keys."""
    if not getattr(graph, "checkpointer", None):
        return []
    history = list(graph.get_state_history(thread_config))
    history.reverse()
    out: list[dict] = []
    prev_values: dict | None = None
    for s in history:
        values = jsonable(s.values)
        out.append({
            "checkpoint_id": s.config["configurable"].get("checkpoint_id"),
            "parent_checkpoint_id": ((s.parent_config or {}).get("configurable") or {}).get("checkpoint_id"),
            "step": (s.metadata or {}).get("step"),
            "source": (s.metadata or {}).get("source"),
            "next": list(s.next),
            "created_at": s.created_at,
            "changed_keys": sorted(state_diff(prev_values, values).keys()) if prev_values is not None else sorted(values.keys()),
            "tasks": [t.name for t in (s.tasks or [])],
        })
        prev_values = values
    return out


def assemble_log(*, run_id: str, name: str, started_at: datetime, events: list[dict], graph_json: dict | None,
                 checkpoints: list[dict], thread_id: str | None, meta: dict) -> dict:
    """Events (already with start_ms/end_ms) → log: state snapshots, totals, status."""
    root = next((e for e in events if e["kind"] == "graph"), None)
    end_ms = max((e["end_ms"] or e["start_ms"]) for e in events) if events else 0

    # state snapshots: graph input, each node's input (changes only), graph output
    snapshots: list[dict] = []
    prev: dict | None = None
    if root is not None and isinstance(root.get("input"), dict):
        snapshots.append({"at_ms": root["start_ms"], "event": root["id"], "label": "graph input", "full": True,
                          "state": root["input"]})
        prev = root["input"]
    for e in events:
        if e["kind"] == "node" and isinstance(e.get("input"), dict):
            snapshots.append({"at_ms": e["start_ms"], "event": e["id"], "label": f"before {e['name']} (step {e.get('step')})",
                              "full": False, "changed": state_diff(prev, e["input"])})
            prev = e["input"]
    if root is not None and isinstance(root.get("output"), dict):
        snapshots.append({"at_ms": root["end_ms"] or end_ms, "event": root["id"], "label": "graph output", "full": False,
                          "changed": state_diff(prev, root["output"])})
    for e in events:
        if e["kind"] == "node":
            e.pop("input", None)  # the full state is in the snapshots; the node keeps its update

    llm_events = [e for e in events if e["kind"] == "llm"]

    def _sum(key: str) -> int:
        return sum(v for v in ((e.get("usage") or {}).get(key) for e in llm_events) if isinstance(v, (int, float)))

    totals = {
        "llm_calls": len(llm_events),
        "tool_calls": sum(1 for e in events if e["kind"] == "tool"),
        "node_runs": sum(1 for e in events if e["kind"] == "node"),
        "input_tokens": _sum("input_tokens"), "output_tokens": _sum("output_tokens"),
        "cache_read": _sum("cache_read"), "cache_creation": _sum("cache_creation"), "reasoning": _sum("reasoning"),
        "cost_usd": round(sum(e.get("cost_usd") or 0 for e in llm_events), 6),
        "duration_ms": end_ms,
        "errors": sum(1 for e in events if e["status"] == "error"),
    }
    return {
        "schema": SCHEMA,
        "run_id": run_id,
        "name": name,
        "thread_id": thread_id,
        "started_at": started_at.isoformat(timespec="milliseconds"),
        "duration_ms": end_ms,
        "status": "error" if totals["errors"] else "ok",
        "meta": meta,
        "graph": graph_json,
        "events": events,
        "state_snapshots": snapshots,
        "checkpoints": checkpoints,
        "totals": totals,
    }


# ---------------------------------------------------------------------------
# Log storage and index
# ---------------------------------------------------------------------------

def index_entry(log: dict) -> dict:
    return {
        "run_id": log["run_id"], "name": log["name"], "started_at": log["started_at"], "duration_ms": log["duration_ms"],
        "status": log["status"], "meta": log.get("meta", {}), "totals": log.get("totals", {}), "file": f"{log['run_id']}.json",
        "source": log.get("meta", {}).get("source", "recorder"),
    }


def write_log(log: dict, log_dir: Path) -> Path:
    """Write the log and rebuild the folder index (`index.json`, newest first)."""
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{log['run_id']}.json"
    path.write_text(json.dumps(log, ensure_ascii=False, indent=1, default=str))
    rebuild_index(log_dir)
    return path


def rebuild_index(log_dir: Path) -> list[dict]:
    entries = []
    for f in log_dir.glob("*.json"):
        if f.name == "index.json":
            continue
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"corrupted log {f}: {exc}") from exc
        if data.get("schema") != SCHEMA:
            continue
        entries.append(index_entry(data))
    entries.sort(key=lambda e: e["started_at"], reverse=True)
    (log_dir / "index.json").write_text(json.dumps({"schema": SCHEMA, "runs": entries}, ensure_ascii=False, indent=1))
    return entries
