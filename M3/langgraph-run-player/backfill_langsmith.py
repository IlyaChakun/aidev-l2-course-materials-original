"""Backfill visualizer logs from LangSmith traces — for runs made before the recorder existed.

    python3 backfill_langsmith.py <run_id> [<run_id> ...]        # run_id = id of the root run in LangSmith

Takes the run tree (`Client.list_runs(trace_id=...)`), converts it into events of the same shape that
`runlog.RunRecorder` writes, and builds the log with the shared `assemble_log` function. Old runs
have no checkpoints (the graph was compiled without a checkpointer then) — the list is empty, with a note in `meta`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from runlog import assemble_log, write_log  # noqa: E402


def _dt(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc) if "+" in str(value) or "Z" in str(value) \
        else datetime.fromisoformat(str(value)).replace(tzinfo=timezone.utc)


def _lc_message(msg: dict) -> dict:
    """A message in LangChain serialization (`{"lc":1,"type":"constructor","id":[...],"kwargs":{...}}`) → {role, content}."""
    kw = msg.get("kwargs") or {}
    role = kw.get("type") or (msg.get("id") or ["?"])[-1].replace("Message", "").lower()
    out = {"role": role, "content": kw.get("content")}
    if kw.get("tool_calls"):
        out["tool_calls"] = kw["tool_calls"]
    return out


def convert_runs(runs: list[dict]) -> tuple[list[dict], datetime]:
    """List of LangSmith run objects (as dicts) → log events + the root start time."""
    runs = sorted(runs, key=lambda r: str(r.get("dotted_order") or r["start_time"]))
    root = next(r for r in runs if not r.get("parent_run_id"))
    t0 = _dt(root["start_time"])
    ms = lambda v: int((_dt(v) - t0).total_seconds() * 1000) if v else None  # noqa: E731

    events: list[dict] = []
    for r in runs:
        md = (r.get("extra") or {}).get("metadata") or {}
        tags = r.get("tags") or []
        name = r["name"]; rtype = r.get("run_type")
        base = {
            "id": str(r["id"]), "parent": str(r["parent_run_id"]) if r.get("parent_run_id") else None,
            "name": name, "node": md.get("langgraph_node"), "step": md.get("langgraph_step"),
            "checkpoint_ns": md.get("langgraph_checkpoint_ns"),
            "tags": [t for t in tags if not t.startswith("seq:")],
            "start_ms": ms(r["start_time"]), "end_ms": ms(r.get("end_time")),
            "status": "error" if r.get("error") else "ok", "error": r.get("error"),
        }
        if rtype == "llm":
            gen = ((r.get("outputs") or {}).get("generations") or [[{}]])[0][0]
            mkw = (gen.get("message") or {}).get("kwargs") or {}
            usage = mkw.get("usage_metadata") or {}
            resp_md = mkw.get("response_metadata") or {}
            params = (r.get("extra") or {}).get("invocation_params") or {}
            msgs = ((r.get("inputs") or {}).get("messages") or [[]])[0]
            events.append({**base, "kind": "llm",
                           "model": resp_md.get("model_name") or md.get("ls_model_name") or params.get("model"),
                           "provider": md.get("ls_provider"),
                           "params": {k: v for k, v in {"temperature": md.get("ls_temperature", params.get("temperature")),
                                                        "max_tokens": md.get("ls_max_tokens", params.get("max_tokens"))}.items() if v is not None},
                           "tools": [t.get("function", {}).get("name") for t in (params.get("tools") or []) if isinstance(t, dict)],
                           "messages": [_lc_message(m) for m in msgs],
                           "response": {"role": "ai", "content": mkw.get("content"), "tool_calls": mkw.get("tool_calls") or []},
                           "usage": {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                                     "total_tokens": usage.get("total_tokens"),
                                     "cache_read": (usage.get("input_token_details") or {}).get("cache_read"),
                                     "cache_creation": (usage.get("input_token_details") or {}).get("cache_creation"),
                                     "reasoning": (usage.get("output_token_details") or {}).get("reasoning")},
                           "cost_usd": (resp_md.get("token_usage") or {}).get("cost"),
                           "generation_id": resp_md.get("id"), "finish_reason": resp_md.get("finish_reason")})
        elif rtype == "tool":
            events.append({**base, "kind": "tool", "input": r.get("inputs"), "output": r.get("outputs")})
        elif not r.get("parent_run_id"):
            events.append({**base, "kind": "graph", "input": r.get("inputs"), "output": r.get("outputs")})
        elif md.get("langgraph_node") == name and any(t.startswith("graph:step:") for t in tags):
            events.append({**base, "kind": "node", "input": r.get("inputs"), "output": r.get("outputs")})
        else:
            ev = {**base, "kind": "internal"}
            out = (r.get("outputs") or {}).get("output")
            if isinstance(out, str):
                ev["output"] = out  # conditional-edge router
            events.append(ev)
    return events, t0


def backfill(run_id: str, project: str, log_dir: Path, graph_json: dict | None, extra_meta: dict | None = None) -> Path:
    from langsmith import Client

    runs = [dict(id=r.id, name=r.name, run_type=r.run_type, parent_run_id=r.parent_run_id, start_time=r.start_time,
                 end_time=r.end_time, inputs=r.inputs, outputs=r.outputs, extra=r.extra, tags=r.tags, error=r.error,
                 dotted_order=r.dotted_order)
            for r in Client().list_runs(project_name=project, trace_id=run_id, limit=100)]
    if not runs:
        raise LookupError(f"trace {run_id} not found in project {project}")
    events, t0 = convert_runs(runs)
    root_meta = next((r for r in runs if not r["parent_run_id"]), {})
    meta = {**((root_meta.get("extra") or {}).get("metadata") or {}), "source": "langsmith-backfill",
            "note": "no checkpoints: the run was made before the checkpointer was enabled", **(extra_meta or {})}
    # LangSmith service keys (ls_*, LANGSMITH_*, revision_id) are not carried into the run context
    meta = {k: v for k, v in meta.items() if not str(k).startswith(("ls_", "LANGSMITH_")) and k != "revision_id"}
    log = assemble_log(run_id=run_id, name=root_meta.get("name", "graph"), started_at=t0, events=events,
                       graph_json=graph_json, checkpoints=[], thread_id=None, meta=meta)
    return write_log(log, log_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_ids", nargs="*", help="id of the root run (trace) in LangSmith")
    parser.add_argument("--log-dir", type=Path, default=ROOT / "runs" / "log")
    args = parser.parse_args(argv)

    import os
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    project = os.environ.get("LANGSMITH_PROJECT") or ""
    if not project:
        raise SystemExit("LANGSMITH_PROJECT is empty in .env")

    # There is no graph diagram in the LangSmith trace; the player builds one from node events if graph_json=None is passed.
    # If you want the diagram — build your graph here and pass graph_to_json(graph) (imported from runlog).
    graph_json = None
    targets = [(rid, {}) for rid in args.run_ids]
    if not targets:
        parser.error("run_id values are required")
    for rid, extra in targets:
        path = backfill(rid, project, args.log_dir, graph_json, extra)
        print(f"{rid} → {path.name} ({path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
