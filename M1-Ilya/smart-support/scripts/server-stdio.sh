#!/usr/bin/env bash
# Runs the MCP server over stdio. One command for make, Inspector, supergateway and IDE clients.
# Configuration only from environment variables (SUPPORT_DB_PATH etc.), see .env.example.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/mcp_server"
export MCP_TRANSPORT="${MCP_TRANSPORT:-stdio}"
exec .venv/bin/python -m support
