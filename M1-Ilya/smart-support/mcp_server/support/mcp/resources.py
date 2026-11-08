"""MCP resources: reference context without a tool call. Static URIs only (resource templates are advanced)."""
from __future__ import annotations

import json

from mcp.server import MCPServer

from ..service import TicketService


def register_resources(server: MCPServer, service: TicketService) -> None:
    @server.resource(
        "support://status-graph",
        name="status-graph",
        title="Ticket status graph",
        description="Statuses, allowed transitions and field rules for tickets. Read it before calling update_ticket.",
        mime_type="application/json",
    )
    def status_graph() -> str:
        return json.dumps(service.status_graph(), ensure_ascii=False, indent=2)

    @server.resource(
        "support://db-schema",
        name="db-schema",
        title="Database schema",
        description="DDL of the support database (tickets and agent_trace tables, constraints, trigger).",
        mime_type="text/plain",
    )
    def db_schema() -> str:
        return service.db_schema()

    @server.resource(
        "support://summary",
        name="summary",
        title="Ticket counts by status",
        description="Current number of tickets per status. Cheap overview before list_tickets.",
        mime_type="application/json",
    )
    def summary() -> str:
        return json.dumps(service.summary(), ensure_ascii=False, indent=2)
