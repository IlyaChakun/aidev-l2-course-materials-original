"""Selfcheck: starts the server as a separate stdio process on a TEMPORARY copy of the DB and runs all tools and resources.

Prints "OK / FAIL" for each item; exit code 0 only if everything is OK. Does not touch the working DB.
Run: make selfcheck  (or  .venv/bin/python selfcheck.py)
"""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

from mcp import Client, StdioServerParameters

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"{'OK  ' if cond else 'FAIL'} {name}" + (f"  [{detail}]" if detail and not cond else ""), flush=True)


def make_temp_db(dir_: str) -> Path:
    path = Path(dir_) / "selfcheck.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript((ROOT / "db" / "schema.sqlite.sql").read_text(encoding="utf-8"))
    conn.executescript((ROOT / "db" / "seed.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    return path


async def run(db: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "support"],
        cwd=str(HERE),
        env={**os.environ, "SUPPORT_DB_PATH": str(db), "MCP_TRANSPORT": "stdio"},
    )
    async with Client(params) as c:
        check("server starts over stdio and initializes", True)

        tools = {t.name: t for t in (await c.list_tools()).tools}
        check("3 tools are visible: get_ticket, list_tickets, update_ticket",
              set(tools) == {"get_ticket", "list_tickets", "update_ticket"}, str(sorted(tools)))
        check("tool descriptions contain 'When to call' and 'When NOT to call'",
              all("When to call" in t.description and "When NOT to call" in t.description for t in tools.values()))

        resources = {str(r.uri) for r in (await c.list_resources()).resources}
        check("resource support://status-graph is listed", "support://status-graph" in resources, str(resources))
        graph = json.loads((await c.read_resource("support://status-graph")).contents[0].text)
        check("status-graph resource lists the 3 allowed transitions",
              graph["allowed_transitions"] == {"new": ["answered", "escalated"], "answered": ["escalated"], "escalated": []})
        schema = (await c.read_resource("support://db-schema")).contents[0].text
        check("db-schema resource contains tickets and agent_trace", "tickets" in schema and "agent_trace" in schema)
        summary = json.loads((await c.read_resource("support://summary")).contents[0].text)
        check("summary resource counts 20 tickets", summary["total"] == 20, str(summary))

        r = await c.call_tool("get_ticket", {"ticket_id": 1})
        check("get_ticket(1) returns a ticket in status new",
              not r.is_error and r.structured_content["ticket"]["status"] == "new")
        r = await c.call_tool("get_ticket", {"ticket_id": 3})
        check("get_ticket(3) handles an empty body", not r.is_error and r.structured_content["ticket"]["body"] == "")
        r = await c.call_tool("get_ticket", {"ticket_id": 9999})
        check("get_ticket(9999) returns fixable TICKET_NOT_FOUND",
              r.is_error and r.structured_content["error"]["code"] == "TICKET_NOT_FOUND"
              and "list_tickets" in r.structured_content["error"]["hint"])

        r = await c.call_tool("list_tickets", {"status": "new", "limit": 5})
        check("list_tickets(status=new, limit=5) returns 5 summaries without body",
              not r.is_error and r.structured_content["count"] == 5 and "body" not in r.structured_content["tickets"][0])
        r = await c.call_tool("list_tickets", {"status": "closed"})
        check("list_tickets(status=closed) returns UNKNOWN_STATUS",
              r.is_error and r.structured_content["error"]["code"] == "UNKNOWN_STATUS")

        r = await c.call_tool("update_ticket", {"ticket_id": 1, "new_status": "answered", "agent": "selfcheck",
                                                 "category": "account", "priority": "low", "score": 92,
                                                 "answer": "Open Settings > Security."})
        check("update_ticket new -> answered succeeds",
              not r.is_error and r.structured_content["transition"] == {"from": "new", "to": "answered"})
        r = await c.call_tool("update_ticket", {"ticket_id": 1, "new_status": "new", "agent": "selfcheck"})
        err = r.structured_content["error"] if r.is_error else {}
        check("update_ticket answered -> new is rejected with allowed_transitions and hint",
              r.is_error and err.get("code") == "INVALID_STATUS_TRANSITION"
              and err.get("allowed_transitions") == ["escalated"] and err.get("hint"), str(err))
        r = await c.call_tool("update_ticket", {"ticket_id": 1, "new_status": "escalated", "agent": "selfcheck",
                                                 "escalation_reason": "needs specialist"})
        check("update_ticket answered -> escalated succeeds (agent fixes itself by the hint)", not r.is_error)
        r = await c.call_tool("update_ticket", {"ticket_id": 1, "new_status": "answered", "agent": "selfcheck", "answer": "x"})
        check("update_ticket escalated -> anything is rejected, allowed_transitions is empty",
              r.is_error and r.structured_content["error"]["allowed_transitions"] == [])
        r = await c.call_tool("update_ticket", {"ticket_id": 2, "new_status": "answered", "agent": "selfcheck"})
        check("update_ticket answered without answer returns MISSING_REQUIRED_FIELD",
              r.is_error and r.structured_content["error"]["code"] == "MISSING_REQUIRED_FIELD")

    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT outcome, status_from, status_to FROM agent_trace WHERE ticket_id = 1 ORDER BY id").fetchall()
    status2 = conn.execute("SELECT status FROM tickets WHERE id = 2").fetchone()[0]
    conn.close()
    check("agent_trace recorded 2 ok and 2 rejected attempts for ticket 1",
          [r[0] for r in rows] == ["ok", "rejected", "ok", "rejected"], str(rows))
    check("rejected call did not change ticket 2", status2 == "new")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db = make_temp_db(tmp)
        try:
            asyncio.run(run(db))
        except Exception as exc:  # noqa: BLE001
            check("selfcheck finished without exceptions", False, f"{type(exc).__name__}: {exc}")
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} OK" + (f", FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
