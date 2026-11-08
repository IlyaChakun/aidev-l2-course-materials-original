#!/usr/bin/env python3
"""Checks the DB state after a run against the expectation in m1/expected/<run>.json.

Usage: python3 scripts/check_expected.py <run> <path to sqlite>, where <run> is a file name in m1/expected/ without .json (ide-scenario)
Reads the DB only. Prints OK / FAIL for each item, exit code 1 on any FAIL.
Only the DB part (db_after) is checked. Agent outputs are checked by hand against the run logs.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failed = 0


def check(name, cond, detail=""):
    global failed
    print(f"{'OK  ' if cond else 'FAIL'} {name}" + ("" if cond else f"  [{detail}]"))
    if not cond:
        failed += 1


def check_ide(db: str) -> int:
    """DB state after the IDE scenario (tickets 5 and 6); all other tickets equal the clean seed."""
    exp = json.loads((ROOT / "m1" / "expected" / "ide-scenario.json").read_text(encoding="utf-8"))["db_after"]
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    def outcomes(tid):
        return [r["outcome"] for r in conn.execute("SELECT outcome FROM agent_trace WHERE ticket_id = ? ORDER BY id", (tid,))]

    for tid, key in ((5, "ticket_5"), (6, "ticket_6")):
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (tid,)).fetchone()
        check(f"ticket {tid} status == {exp[key]['status']}", row is not None and row["status"] == exp[key]["status"], str(row and row["status"]))
        check(f"ticket {tid} agent_trace outcomes == {exp[key]['agent_trace']}", outcomes(tid) == exp[key]["agent_trace"], str(outcomes(tid)))

    ref = sqlite3.connect(":memory:")
    ref.row_factory = sqlite3.Row
    ref.executescript((ROOT / "db" / "schema.sqlite.sql").read_text(encoding="utf-8"))
    ref.executescript((ROOT / "db" / "seed.sql").read_text(encoding="utf-8"))
    q = "SELECT * FROM tickets WHERE id NOT IN (5, 6) ORDER BY id"
    check("other 18 tickets equal clean seed", [tuple(r) for r in conn.execute(q)] == [tuple(r) for r in ref.execute(q)])
    q = "SELECT COUNT(*) FROM agent_trace WHERE ticket_id NOT IN (5, 6)"
    check("trace rows of other tickets unchanged", conn.execute(q).fetchone()[0] == ref.execute(q).fetchone()[0])
    return 1 if failed else 0


def main(run: str, db: str) -> int:
    if run == "ide-scenario":
        return check_ide(db)
    exp = json.loads((ROOT / "m1" / "expected" / f"{run}.json").read_text(encoding="utf-8"))["db_after"]
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    t = conn.execute("SELECT * FROM tickets WHERE id = ?", (exp["ticket_id"],)).fetchone()
    check(f"ticket {exp['ticket_id']} exists", t is not None)
    if t is None:
        return 1
    trace = [dict(r) for r in conn.execute(
        "SELECT agent, outcome, status_from, status_to FROM agent_trace WHERE ticket_id = ? ORDER BY id", (exp["ticket_id"],))]

    if exp.get("unchanged"):
        check("status unchanged", t["status"] == exp["status"], t["status"])
        check("no new trace rows", len(trace) == exp["agent_trace_rows"], f"{len(trace)} rows")
        return 1 if failed else 0

    check(f"status == {exp['status']}", t["status"] == exp["status"], t["status"])
    if "category" in exp:
        check(f"category == {exp['category']}", t["category"] == exp["category"], str(t["category"]))
    if "priority" in exp:
        check(f"priority == {exp['priority']}", t["priority"] == exp["priority"], str(t["priority"]))
    if "priority_one_of" in exp:
        check(f"priority in {exp['priority_one_of']}", t["priority"] in exp["priority_one_of"], str(t["priority"]))
    if "score_min" in exp:
        check(f"score in [{exp['score_min']}, {exp['score_max']}]",
              t["score"] is not None and exp["score_min"] <= t["score"] <= exp["score_max"], str(t["score"]))
    if exp.get("answer_not_empty"):
        check("answer not empty", bool(t["answer"] and t["answer"].strip()))
    if "answer" in exp and exp["answer"] is None:
        check("answer is NULL", t["answer"] is None, str(t["answer"]))
    if "escalation_reason" in exp and exp["escalation_reason"] is None:
        check("escalation_reason is NULL", t["escalation_reason"] is None, str(t["escalation_reason"]))
    if exp.get("escalation_reason_not_empty"):
        check("escalation_reason not empty", bool(t["escalation_reason"] and t["escalation_reason"].strip()))
    if "agent_trace" in exp:
        check(f"agent_trace == {exp['agent_trace']}", trace == exp["agent_trace"], str(trace))
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
