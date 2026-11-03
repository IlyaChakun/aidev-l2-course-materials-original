"""Build a self-contained player HTML with the logs embedded (for sharing/publishing, no fetch needed).

    python3 build_embedded.py [--out runs/viewer-embedded.html] [--limit 6]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_embedded(index_html: str, log_dir: Path, limit: int | None = None) -> str:
    """Insert a data block before the first <script>: index.json + logs (newest first)."""
    marker = "<script>"
    if marker not in index_html:
        raise ValueError("index.html has no <script>")
    index = json.loads((log_dir / "index.json").read_text())
    runs = index["runs"][:limit] if limit else index["runs"]
    data = {"index.json": {**index, "runs": runs}}
    for run in runs:
        data[run["file"]] = json.loads((log_dir / run["file"]).read_text())
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")  # so that </script> inside the data does not close the tag
    return index_html.replace(marker, f"<script>window.EMBEDDED_RUNS = {payload};</script>\n{marker}", 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "viewer-embedded.html")
    parser.add_argument("--limit", type=int, default=6, help="how many of the latest runs to embed")
    args = parser.parse_args(argv)
    html = build_embedded((ROOT / "viewer" / "index.html").read_text(), ROOT / "runs" / "log", args.limit)
    args.out.write_text(html)
    print(f"{args.out} · {args.out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
