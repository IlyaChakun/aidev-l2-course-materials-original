# mcp_server: the "Smart Support" MCP server

A server on top of an SQLite ticket DB: 3 tools and 3 resources. Ticket statuses are `new → answered → escalated`; invalid transitions are rejected with a recoverable error. Every change attempt (successful or rejected) is written to the `agent_trace` table.

## Stack (exact versions)

| What | Version | Note |
|---|---|---|
| Python | 3.10+ (tested on 3.13.0) | |
| **SDK: `mcp`** | **2.3.0** (PyPI, 2 October 2026) | the official Python SDK, class `mcp.server.MCPServer`. The `fastmcp` package is not used (it is a different package). Do not confuse it with the v1 line (`mcp==1.30.0`, `FastMCP` from `mcp.server.fastmcp`) |
| Storage | SQLite (stdlib `sqlite3`) | replacing it with Postgres: see "How to replace the repository" |
| MCP Inspector | 2.13.0 (`npx`, Node >= 22.19) | started with `make inspector` |
| Tests | `unittest` (stdlib) | no third-party test dependencies |

Dependencies are pinned: [requirements.txt](requirements.txt) (direct) and [requirements.lock.txt](requirements.lock.txt) (full `pip freeze`).

## Architecture

```
contracts  ←  support/domain  ←  support/repository  ←  support/service  ←  support/mcp
(JSON Schema)  status graph,      interface + SQLite     transaction:         tools, resources,
               field checks       (knows nothing         read→validate→       error format
               no SDK/DB/network  about MCP)             write→trace
```

- `support/domain/`: pure logic (`status_graph.py`, `ticket.py`, `errors.py`). It does not import the SDK, sqlite or the network (checked by a test).
- `support/repository/`: the `TicketRepository` interface (`base.py`) and the `SqliteTicketRepository` implementation (`sqlite.py`).
- `support/service.py`: the scenarios; one `BEGIN IMMEDIATE` transaction for "read → check → write → leave a trace".
- `support/mcp/`: a thin layer: `tools.py` (descriptions for the model), `resources.py`, `results.py` (response format), `server.py` (assembly and transport). The folder name `mcp` belongs to the `support.mcp` package and does not clash with the `mcp` SDK (imports are absolute); run it as `python -m support`, not by running files from `support/mcp/` directly.
- Agents do not access the DB directly: only through the tools.

## Contract

| Tool | Purpose | Mode |
|---|---|---|
| `get_ticket(ticket_id)` | the full ticket | read-only |
| `list_tickets(status?, limit?)` | short cards without the body | read-only |
| `update_ticket(ticket_id, new_status, agent, category?, priority?, score?, answer?, escalation_reason?)` | status change + the result of the agent's work | write |

| Resource | What |
|---|---|
| `support://status-graph` | statuses, allowed transitions, field rules |
| `support://db-schema` | DB DDL |
| `support://summary` | ticket counts by status |

A resource template (`db://entity/{id}`) is advanced and is not implemented in M1.

### Response format
Success: `{"ok": true, ...}` (both in `content` as JSON text and in `structuredContent`).
Recoverable error (`isError: true`):

```json
{"ok": false, "error": {
  "code": "INVALID_STATUS_TRANSITION",
  "message": "cannot move ticket 1 from 'answered' to 'new'",
  "hint": "Ticket 1 is 'answered'. Retry update_ticket with new_status in ['escalated'], or stop if none fits.",
  "current_status": "answered",
  "allowed_transitions": ["escalated"]
}}
```

Codes: `TICKET_NOT_FOUND`, `INVALID_STATUS_TRANSITION`, `UNKNOWN_STATUS`, `MISSING_REQUIRED_FIELD`, `INVALID_VALUE`, `STORAGE_UNAVAILABLE` (cannot be fixed by changing the arguments). Argument type errors are produced by the SDK itself (pydantic).

> Important for the v2 SDK: an exception thrown from a tool turns into a faceless "Error executing tool …", and the model does not see the reason. That is why domain errors are returned explicitly as `CallToolResult(is_error=True)`.

## Running

From the repository root:

```
make setup              # venv and dependencies (uv)
make db-reset db-seed   # DB from db/schema.sqlite.sql and db/seed.sql (the DB file does not go into git)
make server-stdio       # server over stdio (stdout is used by the protocol, logs go to stderr)
make server-http        # Streamable HTTP on MCP_HTTP_HOST:MCP_HTTP_PORT (default 127.0.0.1:8000, /mcp)
make inspector          # MCP Inspector web UI
```

Configuration comes only from environment variables (see [../.env.example](../.env.example)): `SUPPORT_DB_PATH` (a relative path is resolved from the repository root), `MCP_TRANSPORT` (`stdio` | `streamable-http`), `MCP_HTTP_HOST`, `MCP_HTTP_PORT`, `MCP_LOG_LEVEL`.

Connecting a client (IDE): command `scripts/server-stdio.sh` (absolute path), environment `SUPPORT_DB_PATH`.

## How to test

```
make test                # unittest: domain, repository, MCP layer, stdout, domain graph = DB trigger
make selfcheck           # a separate stdio process on a temporary DB: all tools and resources, OK/FAIL per item
make inspector-check     # the same through MCP Inspector (CLI), on a temporary DB
make runlog M=1 NAME=tests CMD="make test"   # log into m1/runs/ with secrets masked
```

What the tests check: the transition graph without the SDK; no SDK/DB/network imports in `domain`; the repository and the service on a temporary DB (including transaction rollback and the trace of rejected attempts); that the graph in `domain` and the DB trigger match for every pair of statuses; the MCP layer (3 tools, descriptions with "When to call" / "When NOT to call", resources, no resource template); no `print()` in the code, and that every stdout line in stdio mode is JSON-RPC.

## How to replace the repository

1. Implement `TicketRepository` and `TicketTx` from [`support/repository/base.py`](support/repository/base.py) (for example, `postgres.py`): `get`, `list`, `counts_by_status`, `schema_ddl`, `get_trace`, `transaction()` with `get`, `apply_patch`, `add_trace`.
2. The transaction must be atomic: the read, the write and the trace all in one.
3. Replace where the repository is created in `support/mcp/server.py` (`main()`). `domain`, `service` and `mcp` do not change.
4. Run `tests/test_repository.py` against the new implementation (the trigger consistency test is needed only if you keep the DB trigger).

## M1 limitations
- State is only in the SQLite file; there is no authorization and no multi-tenancy (the architecture allows for them; they are added in M7).
- The HTTP transport is enabled for testing, with no bearer check (advanced).
