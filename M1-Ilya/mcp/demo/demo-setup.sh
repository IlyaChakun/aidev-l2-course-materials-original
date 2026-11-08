#!/usr/bin/env bash
# Setup for the three demos of the M1 MCP lecture (see README.md next to this script).
#
#   bash demo-setup.sh setup   # once: server copies, demo 1 patches, venv, DBs, client folders
#   bash demo-setup.sh reset   # before each run: fresh DBs in all three copies
#   bash demo-setup.sh remove  # when done: remove the copies and client folders
#
# Variables (optional):
#   STS_SRC  — the smart-support project (default ../../smart-support next to this folder)
#   DEMO_DIR — where to put the copies and client folders (default ~/sts-demo)
#
# The project itself is not changed: each demo gets its own copy, and the demo 1 patches go into the copies.
# Requires: uv, Python 3.13 (uv installs it), sqlite3, make.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
STS_SRC="${STS_SRC:-$(cd "$HERE/../../smart-support" && pwd)}"
DEMO_DIR="${DEMO_DIR:-$HOME/sts-demo}"

# copy -> which demo 1 patches are applied to it
#   m1 — demos 2 and 3, the server as is
#   a  — demo 1, version A: no hints + bad error
#   b  — demo 1, version B: no hints, the regular error
COPIES=(m1 a b)
patches_for() {
  case "$1" in
    m1) ;;
    a) echo "$HERE/demo1-no-hints.patch $HERE/demo1-bad-error.patch" ;;
    b) echo "$HERE/demo1-no-hints.patch" ;;
  esac
}

write_client() {
  # The client folder is outside the project copy: the agent sees only the MCP server, not the source.
  local name="$1" wt="$DEMO_DIR/sts-$1"
  mkdir -p "$DEMO_DIR/client-$name"
  cat > "$DEMO_DIR/client-$name/.mcp.json" <<JSON
{
  "mcpServers": {
    "support-tickets": {
      "type": "stdio",
      "command": "$wt/scripts/server-stdio.sh",
      "args": [],
      "env": { "SUPPORT_DB_PATH": "$wt/data/ide-scenario.sqlite" }
    }
  }
}
JSON
}

setup() {
  mkdir -p "$DEMO_DIR"
  for c in "${COPIES[@]}"; do
    local wt="$DEMO_DIR/sts-$c"
    if [ -d "$wt" ]; then
      echo "· $wt already exists, skipping creation"
    else
      mkdir -p "$wt"
      (cd "$STS_SRC" && tar --exclude .venv --exclude data --exclude .env -cf - .) | (cd "$wt" && tar -xf -)
      local n=0
      for p in $(patches_for "$c"); do patch -s -p1 -d "$wt" < "$p"; n=$((n + 1)); done
      echo "· $wt created ($n patch(es) applied)"
    fi
    (cd "$wt" && make setup >/dev/null 2>&1 && make ide-db 2>&1 | tail -1)
    write_client "$c"
  done
  (cd "$DEMO_DIR/sts-m1" && make test-server 2>&1 | tail -1 && make selfcheck 2>&1 | tail -1)
  cat <<MSG

Done. Start Claude Code for the demos (from the client folder, demo server only, no file access):
  cd $DEMO_DIR/client-<a|b|m1> && claude --strict-mcp-config --mcp-config .mcp.json \\
    --tools "ListMcpResourcesTool,ReadMcpResourceTool" --allowedTools "mcp__support-tickets"

Inspector for demo 2 (without the Docker stand):
  cd $DEMO_DIR/sts-m1 && CLIENT_PORT=6390 MCP_SANDBOX_PORT=6391 npx -y @modelcontextprotocol/inspector@2.13.0 \\
    "\$PWD/scripts/server-stdio.sh" -e SUPPORT_DB_PATH=./data/ide-scenario.sqlite --protocol-era auto
MSG
}

reset() {
  for c in "${COPIES[@]}"; do
    (cd "$DEMO_DIR/sts-$c" && make ide-db 2>&1 | tail -1 | sed "s/^/sts-$c: /")
  done
}

remove() {
  for c in "${COPIES[@]}"; do
    rm -rf "$DEMO_DIR/sts-$c" "$DEMO_DIR/client-$c"
  done
  rmdir "$DEMO_DIR" 2>/dev/null || true
  echo "Copies and client folders removed."
}

case "${1:-}" in
  setup) setup ;;
  reset) reset ;;
  remove) remove ;;
  *) echo "usage: bash demo-setup.sh setup|reset|remove" >&2; exit 2 ;;
esac
