#!/usr/bin/env python3
"""
Sanitizer for AI-agent work logs.

Why: the built-in redaction of export tools cuts secrets of known formats,
but does not touch personal data and "human" passwords. Checked on 05.08.2026
with SpecStory 2.6.0: real key formats were cut, while email, phone numbers, surnames,
addresses, connection strings and a low-entropy password passed straight through.

This script finishes the job on any text export with one and the same set of rules: markdown
from SpecStory, HTML from claude-replay, json from dkod. Deterministic, works offline,
sends nothing anywhere.

For SpecStory exports the file NAME is also scrubbed: the slug after the timestamp is built
from the first prompt before redaction, and secrets from the prompt go straight into the name. The file
is renamed to a clean timestamp ("2026-08-05_19-01-00Z.md").

The third thing the script does: it BUILDS context-report.md, a summary of context
window management. It reads the raw Claude Code and Codex session files of the CURRENT project
(so it must be run from the project root) and writes a table next to the export: how many
turns in the session, the peak and final window fill in tokens, how many compactions there were and of what kind
(manual or automatic, how many tokens before and after). The report has only
numbers, not a line of code or conversation, so it can be submitted under any NDA.
Disabled with the --no-context-report flag.

Usage:
    python3 sanitize-log.py <file-or-folder> [more files...]
    python3 sanitize-log.py session.md --names "Acme Ltd" "Smith" --dry-run

By default it rewrites the file in place and puts <name>.orig next to it before the first run.
With --dry-run it writes nothing and only shows what it found.
"""

import argparse
import pathlib
import re
import sys

# (rule name, regex, what to substitute for the match)
RULES = [
    # ── secrets ────────────────────────────────────────────────────────────────
    ("aws_key",       r"\b(?:AKIA|ASIA|AROA|ABIA|ACCA)[A-Z0-9]{16}\b", "[AWS_KEY]"),
    ("github_token",  r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b", "[GITHUB_TOKEN]"),
    ("github_pat",    r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", "[GITHUB_TOKEN]"),
    ("anthropic_key", r"\bsk-ant-[A-Za-z0-9_-]{10,}\b", "[API_KEY]"),
    ("openai_key",    r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b", "[API_KEY]"),
    ("stripe_key",    r"\bsk_(?:live|test)_[A-Za-z0-9]{10,}\b", "[API_KEY]"),
    ("slack_token",   r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "[SLACK_TOKEN]"),
    ("google_key",    r"\bAIza[A-Za-z0-9_-]{35}\b", "[API_KEY]"),
    ("jwt",           r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b", "[JWT]"),
    ("private_key",   r"-----BEGIN[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END[A-Z ]*PRIVATE KEY-----",
                      "[PRIVATE_KEY]"),
    # A password in the form of source code or config, in quotes:
    #   DB_PASSWORD = "hunter2", api_key: 'abc', self.token="xyz"
    # The prefix before the keyword must be allowed: without it \b does not match
    # inside DB_PASSWORD, and the rule silently misses the most common case.
    ("code_secret",   r"""(?i)[A-Za-z0-9_.\-]*"""
                      r"""(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|"""
                      r"""private[_-]?key|credential|conn[_-]?str)"""
                      r"""[A-Za-z0-9_]*\s*[:=]\s*\\*["'][^"'\n\\]{4,}\\*["']""",
                      "[SECRET_ASSIGNMENT]"),
    # The same without quotes: DB_PASSWORD=hunter2, export API_TOKEN=abc
    ("env_secret",    r"""(?i)[A-Za-z0-9_.\-]*"""
                      r"""(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|"""
                      r"""private[_-]?key|credential)"""
                      r"""[A-Za-z0-9_]*\s*=\s*[^\s"'\n,;)]{4,}""",
                      "[SECRET_ASSIGNMENT]"),
    # connection string with a password: postgres://user:pass@host
    ("conn_string",   r"(?i)\b[a-z][a-z0-9+.\-]*://[^\s:@/]+:[^\s:@/]+@[^\s/\"']+", "[CONNECTION_STRING]"),

    # ── personal data ────────────────────────────────────────────────────
    ("email",         r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
    # The trailing lookahead lets through a sentence-ending period ("call +375 ... 67."),
    # but still rejects decimal continuations like "1.2" and words stuck together.
    ("phone",         r"(?<![\w.])(?:\+?\d{1,3}[ \-]?)?\(?\d{2,4}\)?[ \-]?\d{3}[ \-]?\d{2}[ \-]?\d{2}(?!\w|\.\d)",
                      "[PHONE]"),
    ("passport_by_ru", r"\b\d{4}[ \-]?\d{6}\b", "[DOC_ID]"),
    ("card",          r"\b(?:\d{4}[ \-]?){3}\d{4}\b", "[CARD]"),
    ("iban",          r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", "[IBAN]"),

    # ── OS username in paths ────────────────────────────────────────────
    # Found by a run on 05.08 on live logs: /Users/<login> appeared in the body 24 thousand times.
    # People's logins often match their surname, so this is PII, not cosmetics.
    ("home_path",     r"(?P<pfx>/(?:Users|home)/)[A-Za-z0-9_.\-]+", r"\g<pfx>[USER]"),
    ("home_path_win", r"(?i)(?P<pfx>[A-Z]:\\Users\\)[A-Za-z0-9_.\-]+", r"\g<pfx>[USER]"),
    # The same leak in the "munged" form of Claude Code paths (-Users-login-...)
    ("home_path_munged", r"(?P<pfx>-Users-)[A-Za-z0-9_.]+(?=-)", r"\g<pfx>[USER]"),

    # ── internal infrastructure ──────────────────────────────────────────────
    ("internal_host", r"(?i)\bhttps?://[a-z0-9.\-]+\.(?:internal|local|corp|intranet|lan)\b[^\s\"'<>]*",
                      "[INTERNAL_URL]"),
    ("private_ip",    r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
                      "[PRIVATE_IP]"),
]

# Do not touch what looks like a secret but is not one: placeholders in documentation
# and service values like TOKEN_TYPE = "bearer".
ALLOWLIST = re.compile(
    r"(?i)\b(?:example|test|fake|dummy|sample|placeholder|your[_-]?key|changeme|xxx+"
    r"|bearer|basic|digest|none|null|true|false|string|number|boolean|required|optional"
    r"|env|process\.env|os\.environ|secret_name|redacted)\b"
    r"|<[^>]{1,40}>|\$\{[^}]{1,40}\}|\{\{[^}]{1,40}\}\}"
)


def sanitize(text, extra_names=()):
    """Returns (sanitized text, {rule: number of times it fired})."""
    hits = {}

    for name in extra_names:
        if not name.strip():
            continue
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        text, n = pattern.subn("[NAME]", text)
        if n:
            hits["custom:" + name] = hits.get("custom:" + name, 0) + n

    for rule, pattern, repl in RULES:
        def _sub(m):
            if ALLOWLIST.search(m.group(0)):
                return m.group(0)
            hits[rule] = hits.get(rule, 0) + 1
            return m.expand(repl) if "\\" in repl else repl
        text = re.sub(pattern, _sub, text)

    return text, hits


# SpecStory names an export "<timestamp>-<slug of the first prompt>.md", and the slug is built
# BEFORE redaction: a token or email from the first message goes straight into the file name (checked
# on 2.6.0). The content is fixed by the rules above, and the name only by renaming.
SPECSTORY_SLUG = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}Z?)[-_].+$")


def deslug_target(path):
    """For a SpecStory export returns the path with a clean timestamp name, otherwise None."""
    m = SPECSTORY_SLUG.match(path.stem)
    if not m:
        return None
    return path.with_name(m.group(1) + path.suffix)


# ── context-report: summary of context window fill ────────────────────────────
# The numbers are taken from the raw session files (not from the SpecStory export, which
# drops the metadata): Claude Code puts the API usage in every assistant record and records
# every compaction separately, Codex writes token_count events that account for reasoning.

def _munge(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def _fmt_k(n):
    return f"{round(n / 1000)}K" if n >= 10_000 else str(n)


def _parse_claude_session(fp):
    import json
    turns, compacts, models = [], [], set()
    first_ts = last_ts = None
    prompts = cache_read = prompt_total = 0
    for line in open(fp, encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        ts = o.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        if o.get("compactMetadata"):
            cm = o["compactMetadata"]
            compacts.append((ts or "", cm.get("trigger", "?"),
                             cm.get("preTokens", 0), cm.get("postTokens", 0)))
        if o.get("isSidechain"):
            continue
        m = o.get("message") or {}
        if o.get("type") == "assistant":
            u = m.get("usage") or {}
            ctx = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                   + u.get("cache_creation_input_tokens", 0))
            if ctx:
                turns.append(ctx)
                cache_read += u.get("cache_read_input_tokens", 0)
                prompt_total += ctx
            if m.get("model"):
                models.add(m["model"])
        elif o.get("type") == "user" and isinstance(m.get("content"), str) and m["content"].strip():
            prompts += 1
    if not turns:
        return None
    return {"start": (first_ts or "")[:16].replace("T", " "), "api_turns": len(turns),
            "prompts": prompts, "peak": max(turns), "final": turns[-1],
            "cache_pct": cache_read * 100 // prompt_total if prompt_total else 0,
            "compacts": compacts, "models": models}


def _codex_sessions(project_root):
    base = pathlib.Path.home() / ".codex" / "sessions"
    found = []
    if not base.is_dir():
        return found
    needle_a = f'"cwd": "{project_root}"'
    needle_b = f'"cwd":"{project_root}"'
    for fp in base.rglob("*.jsonl"):
        try:
            with open(fp, encoding="utf-8", errors="replace") as f:
                head = "".join(next(f, "") for _ in range(6))
        except OSError:
            continue
        if needle_a in head or needle_b in head:
            found.append(fp)
    return sorted(found)


def _parse_codex_session(fp):
    import json
    last_usage = None
    first_ts = None
    for line in open(fp, encoding="utf-8", errors="replace"):
        if first_ts is None and '"timestamp"' in line:
            mts = re.search(r'"timestamp":\s*"([^"]{16})', line)
            if mts:
                first_ts = mts.group(1).replace("T", " ")
        if '"token_count"' not in line:
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        info = ((o.get("payload") or {}).get("info") or {})
        if info.get("total_token_usage"):
            last_usage = info["total_token_usage"]
    if not last_usage:
        return None
    return {"start": first_ts or "", "usage": last_usage}


def build_context_report(project_root, out_path):
    """Returns a summary text for the console, or None if no sessions were found."""
    claude_dir = pathlib.Path.home() / ".claude" / "projects" / _munge(project_root)
    sessions = []
    for fp in sorted(claude_dir.glob("*.jsonl")) if claude_dir.is_dir() else []:
        s = _parse_claude_session(fp)
        if s:
            s["id"] = fp.stem[:8]
            sessions.append(s)
    sessions.sort(key=lambda s: s["start"])
    codex = []
    for fp in _codex_sessions(project_root):
        s = _parse_codex_session(fp)
        if s:
            codex.append(s)
    if not sessions and not codex:
        return None

    window = 200_000
    over = any(s["peak"] > window for s in sessions)
    if over:
        window = 1_000_000

    lines = [
        "# Context report — context window management",
        "",
        f"Project: `{pathlib.Path(project_root).name}`. Claude Code sessions: {len(sessions)}, "
        f"Codex sessions: {len(codex)}. The report was built by sanitize-log.py from the raw session files; "
        "it contains only numbers, no conversation content.",
        "",
        f"Window used for percentages: {_fmt_k(window)} tokens"
        + (" (the peak exceeded 200K, so the sessions ran in the extended window)." if over else "."),
        "",
    ]
    if sessions:
        lines += [
            "## Claude Code",
            "",
            "| Start | Session | API turns | Prompts | Window peak | Final | Cache hits | Compactions |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for s in sessions:
            comp = "none"
            if s["compacts"]:
                comp = "; ".join(
                    f"{trig}: {_fmt_k(pre)}→{_fmt_k(post)}"
                    for _, trig, pre, post in s["compacts"])
            lines.append(
                f"| {s['start']} | {s['id']} | {s['api_turns']} | {s['prompts']} "
                f"| {_fmt_k(s['peak'])} ({s['peak'] * 100 // window}%) "
                f"| {_fmt_k(s['final'])} ({s['final'] * 100 // window}%) "
                f"| {s['cache_pct']}% | {comp} |")
        n_comp = sum(len(s["compacts"]) for s in sessions)
        lines += ["", f"Total compactions: {n_comp} "
                      f"(manual: {sum(1 for s in sessions for c in s['compacts'] if c[1] == 'manual')}, "
                      f"automatic: {sum(1 for s in sessions for c in s['compacts'] if c[1] == 'auto')}).", ""]
    if codex:
        lines += [
            "## Codex",
            "",
            "| Start | Total tokens | Input | Cache | Output | Of which reasoning |",
            "|---|---|---|---|---|---|",
        ]
        for s in codex:
            u = s["usage"]
            lines.append(
                f"| {s['start']} | {_fmt_k(u.get('total_tokens', 0))} "
                f"| {_fmt_k(u.get('input_tokens', 0))} | {_fmt_k(u.get('cached_input_tokens', 0))} "
                f"| {_fmt_k(u.get('output_tokens', 0))} | {_fmt_k(u.get('reasoning_output_tokens', 0))} |")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return f"context-report: {len(sessions)} Claude Code sessions, {len(codex)} Codex → {out_path}"


def iter_files(targets):
    exts = {".md", ".html", ".htm", ".json", ".jsonl", ".txt"}
    for t in targets:
        p = pathlib.Path(t)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in exts and not f.name.endswith(".orig"):
                    yield f
        elif p.is_file():
            yield p
        else:
            print(f"  skipped, not found: {t}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Scrub secrets and personal data from a log export")
    ap.add_argument("targets", nargs="+", help="files or folders")
    ap.add_argument("--names", nargs="*", default=[],
                    help="your own names and surnames that a regex cannot catch")
    ap.add_argument("--dry-run", action="store_true", help="write nothing, only show")
    ap.add_argument("--no-context-report", action="store_true",
                    help="do not build context-report.md from the project's raw sessions")
    args = ap.parse_args()

    total = {}
    changed = 0
    files = list(iter_files(args.targets))
    if not files:
        print("No files found.")
        return 1

    for f in files:
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  read error {f}: {e}", file=sys.stderr)
            continue

        clean, hits = sanitize(raw, args.names)
        target = deslug_target(f)
        if not hits and target is None:
            print(f"  clean    {f}")
            continue

        changed += 1
        lines = []
        if hits:
            lines.append(", ".join(f"{k}×{v}" for k, v in sorted(hits.items())))
        if target is not None:
            lines.append(f"file name → {target.name} (slug from the prompt, it may contain secrets)")
        print(f"  SCRUBBED {f}\n           " + "\n           ".join(lines))
        for k, v in hits.items():
            total[k] = total.get(k, 0) + v

        if not args.dry_run:
            out = target if target is not None else f
            backup = out.with_suffix(out.suffix + ".orig")
            if not backup.exists():
                backup.write_text(raw, encoding="utf-8")
            out.write_text(clean, encoding="utf-8")
            if target is not None and f != out and f.exists():
                f.unlink()  # do not leave the leaking slug name behind, even empty

    print(f"\nFiles scanned: {len(files)}, changed: {changed}")
    if total:
        print("Total hits: " + ", ".join(f"{k}×{v}" for k, v in sorted(total.items())))
    if args.dry_run:
        print("--dry-run mode: files untouched, context-report not built.")
    else:
        print("Originals saved next to the files with the .orig suffix — do NOT commit them, add to .gitignore.")
        if not args.no_context_report:
            report_dir = next((pathlib.Path(t) for t in args.targets if pathlib.Path(t).is_dir()),
                              files[0].parent)
            summary = build_context_report(pathlib.Path.cwd(), report_dir / "context-report.md")
            if summary:
                print(summary)
            else:
                print("context-report: no raw Claude Code/Codex sessions found for this folder — "
                      "run the script from the root of the project the agent worked in.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
