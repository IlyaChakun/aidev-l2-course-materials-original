#!/usr/bin/env python3
"""Masks strings that look like secrets in the stdin -> stdout stream.

Standard library only. Used by scripts/runlog.sh.
"""
import re
import sys

MASK = "***MASKED***"

PATTERNS = [
    # Bearer tokens in headers and logs
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{6,}"), r"\1" + MASK),
    # sk-..., sk-lf-..., pk-lf-..., sk-ant-...
    (re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{6,}"), MASK),
    # GitHub / Slack tokens
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), MASK),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), MASK),
    # api_key=..., api-key: ..., token=..., secret=..., password=..., authorization: ...
    (
        re.compile(
            r"(?i)(\b[A-Za-z0-9_-]*(?:api[_-]?key|token|secret|passw(?:or)?d|authorization)[A-Za-z0-9_-]*"
            r"\"?\s*[=:]\s*\"?)(?!\*\*\*MASKED)[^\s\",;&]+"
        ),
        r"\1" + MASK,
    ),
]


def mask(line: str) -> str:
    for pattern, repl in PATTERNS:
        line = pattern.sub(repl, line)
    return line


def main() -> int:
    for line in sys.stdin:
        sys.stdout.write(mask(line))
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
