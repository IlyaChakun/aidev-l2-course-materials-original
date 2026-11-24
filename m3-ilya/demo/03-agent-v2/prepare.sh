#!/usr/bin/env bash
# Demo 3 preparation, run once before the lecture (about a minute, a few cents of model calls).
# Creates a fresh workspace outside the Smart-Technical-Support checkout, seeds 56 tickets,
# runs turns 1-2 on thread a1 and brings thread b1 to its pause, then writes demo3.env
# for present.py. Nothing in the Smart-Technical-Support working copy changes.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STS="${STS:-$(cd "$HERE/../../../.." && pwd)/Smart-Technical-Support}"
cd "$STS"
PY=agent_v2/.venv/bin/python
A=agent_v2/agent.py

export M3_DEMO_DIR="$(mktemp -d)"
export M3_DB_PATH="$M3_DEMO_DIR/tickets.sqlite"
export M3_CHECKPOINT_PATH="$M3_DEMO_DIR/checkpoints.sqlite"
export KB_BACKEND=stub
cat > "$HERE/demo3.env" <<EOF
STS=$STS
M3_DEMO_DIR=$M3_DEMO_DIR
M3_DB_PATH=$M3_DB_PATH
M3_CHECKPOINT_PATH=$M3_CHECKPOINT_PATH
KB_BACKEND=stub
EOF

$PY agent_v2/seed.py "$M3_DB_PATH"
$PY agent_v2/scripts/check_env.py
echo "--- a1, turn 1"
$PY $A start a1 "Look at ticket 2 and tell me what it is about." | grep -E "^(START|FINAL|SUMMARY)"
echo "--- a1, turn 2"
$PY $A start a1 "Search the knowledge base for how long the invitation link stays valid." | grep -E "^(START|FINAL|SUMMARY)"
echo "--- b1, brought to its pause"
if $PY $A start b1 "Store your decision for ticket 3 now. /submit" | grep -q "^PAUSE:"; then
  echo "b1 is paused: ready for 'resume b1 reject' on stage"
else
  echo "WARNING: b1 did not reach PAUSE. Run this script again, or start b1 live on stage."
fi
echo "Ready. On stage: python3 $(dirname "$HERE")/present.py $HERE/steps.txt"
