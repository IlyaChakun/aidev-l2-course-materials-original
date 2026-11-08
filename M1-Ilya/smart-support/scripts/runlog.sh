#!/usr/bin/env bash
# Runs a command and writes its log to mN/runs/ with a header and masked secrets.
# Usage: scripts/runlog.sh <M> <NAME> "<command>"
set -uo pipefail

M="${1:?usage: runlog.sh <M> <NAME> "<command>"}"
NAME="${2:?name required}"
CMD="${3:?command required}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNS="$ROOT/m$M/runs"
mkdir -p "$RUNS"

TS="$(date +%Y%m%d-%H%M)"
SAFE_NAME="$(printf '%s' "$NAME" | tr -c 'A-Za-z0-9._-' '-')"
OUT="$RUNS/$TS-$SAFE_NAME.log"

GIT_SHA="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo 'no-commits')"
GIT_BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
PY_VER="$(python3 --version 2>&1)"
SDK_VER="$( (cd "$ROOT/mcp_server" 2>/dev/null && [ -x .venv/bin/python ] && .venv/bin/python -c 'import importlib.metadata as m; print("mcp " + m.version("mcp"))' 2>/dev/null) || echo 'mcp: n/a')"

{
  echo "# runlog"
  echo "time:    $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "module:  m$M"
  echo "name:    $NAME"
  echo "git:     $GIT_BRANCH @ $GIT_SHA"
  echo "python:  $PY_VER"
  echo "sdk:     $SDK_VER"
  echo "command: $CMD"
  echo "-----"
} | python3 "$ROOT/scripts/mask_secrets.py" > "$OUT"

( cd "$ROOT" && bash -c "$CMD" ) 2>&1 | python3 -u "$ROOT/scripts/mask_secrets.py" | tee -a "$OUT"
RC="${PIPESTATUS[0]}"

echo "----- exit code: $RC" | tee -a "$OUT"
echo "log: ${OUT#$ROOT/}"
exit "$RC"
