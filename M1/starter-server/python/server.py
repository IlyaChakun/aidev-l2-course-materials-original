"""Starter MCP server skeleton: one tool, one resource.

Purpose of the file: check that the environment is set up and the server is visible in MCP Inspector
and in the IDE. There is intentionally no business logic here. Replace the contents with your own.

SDK: the `mcp` package (the official Python SDK), line 2.x.
Protocol: revision 2026-07-28.
"""

import json
import platform
import sys
from datetime import datetime, timezone

# IMPORTANT: the class is called MCPServer. In line 1.x it was called FastMCP.
# If the import `from mcp.server import FastMCP` fails, you have SDK 2.x installed,
# and this is the correct import for it.
from mcp.server import MCPServer

server = MCPServer(name="starter-server", version="0.1.0")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL. Your tool goes here.
#
# What you substitute in your own project:
#   - function name -> the tool name the agent will see (get_article, move_ticket...)
#   - docstring     -> the tool description; the agent picks the tool by it,
#                      so write it as a contract, not as a note to yourself
#   - arguments     -> the SDK builds the JSON Schema from the type annotations itself
#   - return        -> dict/list are serialized to JSON automatically
#
# For now there is exactly one tool and it does nothing with data. This is deliberate:
# the skeleton checks the environment, it does not solve the homework.
# ─────────────────────────────────────────────────────────────────────────────
@server.tool()
def ping(message: str) -> dict:
    """Return the passed message together with server diagnostics.

    Args:
        message: any string, to make sure the arguments reach the server.
    """
    return {
        "echo": message,
        "server_time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python_version": platform.python_version(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESOURCE. Your resource goes here.
#
# The assignment requires at least one resource: the DB schema or a state summary.
# Change the URI and the function body: for example, `db://schema` returns the DDL of your tables,
# and `db://summary` returns the number of entities per status.
#
# A URI with a parameter (`db://entity/{id}`) is registered as a resource template -
# that is the advanced level. The syntax is shown in the README next to this file.
# ─────────────────────────────────────────────────────────────────────────────
@server.resource("starter://info", mime_type="application/json")
def info() -> str:
    """Static summary of what is currently running."""
    payload = {
        "server": "starter-server",
        "tools": ["ping"],
        "resources": ["starter://info"],
        "note": "A skeleton for checking the environment. Replace it with your own contract.",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # stdio is the transport used by MCP Inspector and the IDE.
    #
    # Warning: in a stdio server, stdout is taken by the protocol. Any print() to stdout
    # breaks the connection. For debugging, write to stderr: print(..., file=sys.stderr).
    print("starter-server: starting on stdio", file=sys.stderr)
    server.run(transport="stdio")
