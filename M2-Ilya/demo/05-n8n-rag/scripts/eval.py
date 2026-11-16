#!/usr/bin/env python3
"""Runs the golden set (../_shared/golden.json) through the n8n chat webhook and prints a table.

For every question: which files the Qdrant tool retrieved (top-k), which files the agent cited
in its `Sources:` line, whether it refused, and a verdict:
  core / multi: PASS if at least one expected file is cited and the agent did not refuse
                (multi also shows how many of the expected files were cited);
  trap:         PASS if the agent refused (the fixed refusal phrase is present).
Stdlib only. Usage:
  python3 scripts/eval.py                 # all 17 questions
  python3 scripts/eval.py --only q02,t01  # a subset
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
GOLDEN = HERE.parent / "_shared" / "golden.json"
PORT = os.environ.get("DEMO05_N8N_PORT", "5681")
WEBHOOK_ID = "d05c4a70-0000-4000-8000-000000000005"
URL = f"http://127.0.0.1:{PORT}/webhook/{WEBHOOK_ID}/chat"
REFUSAL = "could not find this in the lumen knowledge base"
FILE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\.md")


def ask(question: str, tries: int = 4) -> dict:
    body = json.dumps({"action": "sendMessage", "sessionId": f"eval-{uuid.uuid4().hex[:8]}",
                       "chatInput": question}).encode()
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(URL, data=body, method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as err:
            # 404 right after a restart (webhook not registered yet), 5xx on upstream 429 / timeouts.
            detail = err.read()[:200].decode(errors="replace")
            if attempt == tries:
                raise RuntimeError(f"HTTP {err.code}: {detail}")
            time.sleep(5 * attempt)
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt == tries:
                raise RuntimeError(str(err))
            time.sleep(5 * attempt)
    raise RuntimeError("unreachable")


def retrieved_files(resp: dict) -> list:
    """Files returned by the Qdrant tool, in order, deduplicated (from intermediateSteps)."""
    seen = []
    for step in resp.get("intermediateSteps") or []:
        obs = step.get("observation")
        text = obs if isinstance(obs, str) else json.dumps(obs)
        for m in re.finditer(r'source\\*"\s*:\s*\\*"([^"\\]+\.md)', text):
            if m.group(1) not in seen:
                seen.append(m.group(1))
    return seen


def cited_files(output: str) -> list:
    lines = [ln for ln in output.splitlines() if ln.strip().lower().startswith(("sources:", "**sources"))]
    found = []
    for ln in lines:
        for f in FILE_RE.findall(ln):
            if f not in found:
                found.append(f)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated question ids, e.g. q02,t01")
    ap.add_argument("--out", default=str(HERE / "runs"), help="folder for the Markdown report")
    args = ap.parse_args()

    questions = json.loads(GOLDEN.read_text(encoding="utf-8"))["questions"]
    if args.only:
        wanted = set(args.only.split(","))
        questions = [q for q in questions if q["id"] in wanted]

    rows, answers, passed = [], [], 0
    for q in questions:
        t0 = time.time()
        try:
            resp = ask(q["question"])
            output = str(resp.get("output", ""))
        except RuntimeError as err:
            resp, output = {}, f"ERROR {err}"
        dt = time.time() - t0
        retrieved = retrieved_files(resp)
        cited = cited_files(output)
        refused = REFUSAL in output.lower()
        expected = q["answer_docs"]
        hit = [f for f in expected if f in cited]
        if output.startswith("ERROR"):
            verdict = "ERROR"
        elif q["kind"] == "trap":
            verdict = "PASS" if refused else "FAIL"
        else:
            verdict = "PASS" if hit and not refused else "FAIL"
        passed += verdict == "PASS"
        cover = f"{len(hit)}/{len(expected)}" if expected else "-"
        rows.append(f"| {q['id']} | {q['kind']} | {', '.join(expected) or '-'} | {', '.join(retrieved) or '-'} | "
                    f"{', '.join(cited) or '-'} | {cover} | {'yes' if refused else 'no'} | {verdict} | {dt:.0f} s |")
        answers.append(f"**{q['id']}** {q['question']}\n\n> " + output.strip().replace("\n", "\n> ") + "\n")
        print(f"{q['id']:4} {verdict:5} cited={cited} refused={refused} ({dt:.0f} s)", file=sys.stderr)

    header = ("| id | kind | expected | retrieved by tool (top-k) | cited in answer | expected cited | refused | verdict | time |\n"
              "|---|---|---|---|---|---|---|---|---|")
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    report = (f"# Eval run {stamp}\n\nWebhook: `{URL}` · questions: {len(questions)} · PASS: {passed}/{len(questions)}\n\n"
              + header + "\n" + "\n".join(rows) + "\n\n## Answers\n\n" + "\n".join(answers))
    print(header + "\n" + "\n".join(rows))
    print(f"\nPASS {passed}/{len(questions)}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"eval-{stamp}.md"
    path.write_text(report, encoding="utf-8")
    print(f"report: {path.relative_to(HERE) if path.is_relative_to(HERE) else path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
