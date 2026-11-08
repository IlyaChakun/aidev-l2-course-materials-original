"""MCP server assembly. The transport is chosen by the MCP_TRANSPORT environment variable."""
from __future__ import annotations

import logging
import sys

from mcp.server import MCPServer

from ..config import Settings
from ..repository import SqliteTicketRepository
from ..service import TicketService
from .resources import register_resources
from .tools import register_tools

SERVER_NAME = "smart-support"
INSTRUCTIONS = (
    "Support ticket server. Tickets move new -> answered -> escalated (escalated is final). "
    "Read the support://status-graph resource, call get_ticket before update_ticket, "
    "and fix rejected calls using the `allowed_transitions` and `hint` in the error."
)


def build_server(service: TicketService, *, log_level: str = "INFO") -> MCPServer:
    server = MCPServer(SERVER_NAME, instructions=INSTRUCTIONS, log_level=log_level)  # type: ignore[arg-type]
    register_tools(server, service)
    register_resources(server, service)
    return server


def configure_logging(level: str) -> None:
    """Logs go to stderr only: in stdio mode stdout belongs to the protocol."""
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    service = TicketService(SqliteTicketRepository(settings.db_path))
    server = build_server(service, log_level=settings.log_level)
    logging.getLogger(SERVER_NAME).info(
        "starting transport=%s db=%s", settings.transport, settings.db_path.name
    )
    if settings.transport == "stdio":
        server.run("stdio")
    else:
        server.run("streamable-http", host=settings.http_host, port=settings.http_port)
