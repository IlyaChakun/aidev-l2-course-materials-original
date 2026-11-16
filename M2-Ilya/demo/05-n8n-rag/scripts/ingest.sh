#!/usr/bin/env bash
# Runs the ingestion workflow headless (`n8n execute`) and reports what landed in Qdrant.
# Same result as opening "Demo 05 · Lumen ingest" in the UI and pressing "Execute workflow".
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
C="m2-demo-n8n-rag-n8n"
Q="http://127.0.0.1:${DEMO05_QDRANT_PORT:-6381}"
LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT

echo "running workflow demo05LumenIngest inside $C ..."
start=$(date +%s)
# The running n8n already holds the task-broker port 5679; the CLI instance needs its own one.
docker exec -e N8N_RUNNERS_BROKER_PORT=5690 "$C" n8n execute --id=demo05LumenIngest >"$LOG" 2>&1
rc=$?
if [ $rc -ne 0 ] || ! grep -q "Execution was successful" "$LOG"; then
  echo "ERROR: ingestion failed (exit $rc). Last lines:"; grep -v -i migration "$LOG" | tail -15 | cut -c1-300; exit 1
fi
echo "ingestion ok in $(( $(date +%s) - start )) s"

curl -s "$Q/collections/lumen_kb" | python3 -c '
import json, sys
r = json.load(sys.stdin)["result"]
print("collection lumen_kb: points=%s vector=%s" % (r["points_count"], r["config"]["params"]["vectors"]))'
curl -s -X POST "$Q/collections/lumen_kb/points/scroll" -H 'Content-Type: application/json' \
  -d '{"limit":1000,"with_payload":true,"with_vector":false}' | python3 -c '
import collections, json, sys
pts = json.load(sys.stdin)["result"]["points"]
src = collections.Counter(p["payload"]["metadata"]["source"] for p in pts)
lens = [len(p["payload"]["content"]) for p in pts]
print(f"documents={len(src)} chunks={len(pts)} chunk chars min/avg/max={min(lens)}/{sum(lens)//len(lens)}/{max(lens)}")
print("payload keys:", sorted(pts[0]["payload"].keys()), "metadata keys:", sorted(pts[0]["payload"]["metadata"].keys()))'
