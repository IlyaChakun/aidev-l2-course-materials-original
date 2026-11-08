"""MCP tools: a thin layer over TicketService. The descriptions are written for the model, not for a human."""
from __future__ import annotations

from typing import Annotated

from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations
from pydantic import Field

from ..domain import DomainError
from ..repository import RepositoryUnavailable
from ..service import DEFAULT_LIMIT, MAX_LIMIT, TicketService
from .results import fail, ok, unavailable

GET_TICKET_DESCRIPTION = """\
Read ONE support ticket by id and return all of its fields: subject, body, customer_ref, status, category, \
priority, score, answer, escalation_reason, created_at, last_modified.

When to call: as the FIRST step of any work on a ticket (you MUST know its current `status` before changing it), \
and again after update_ticket if you need to confirm the stored result. Read-only, safe to repeat.
When NOT to call: to browse or look for tickets without an id (use list_tickets). To change a ticket \
(use update_ticket).

Input: ticket_id, integer >= 1.
Output: {"ok": true, "ticket": {...}} where ticket has schema_version "1.0". The `body` can be empty or very long; \
that is normal. If the id does not exist you get error code TICKET_NOT_FOUND with a hint: call list_tickets and \
pick an existing id.

Example: get_ticket(ticket_id=1) -> {"ok": true, "ticket": {"id": 1, "status": "new", ...}}
"""

LIST_TICKETS_DESCRIPTION = f"""\
List tickets as short summaries (id, subject, status, category, priority, score, last_modified), ordered by id. \
Bodies are NOT included.

When to call: to find which tickets exist or to find tickets in a given status (for example the ones still \
waiting: status='new').
When NOT to call: when you already know the id and need the full text (use get_ticket). To change a ticket \
(use update_ticket).

Input: status (optional): one of 'new', 'answered', 'escalated'; limit (optional): integer 1..{MAX_LIMIT}, \
default {DEFAULT_LIMIT}.
Output: {{"ok": true, "count": N, "tickets": [...]}}. An unknown status returns error code UNKNOWN_STATUS with \
the list of valid statuses.

Example: list_tickets(status='new', limit=5) -> {{"ok": true, "count": 5, "tickets": [{{"id": 1, ...}}]}}
"""

UPDATE_TICKET_DESCRIPTION = """\
Move a ticket to a new status and store the result of your work: classification, answer or escalation reason. \
This is the ONLY way to change a ticket. Every call, accepted or rejected, is written to the agent trace.

Allowed status transitions (the server enforces them, you cannot bypass them):
  new -> answered, new -> escalated, answered -> escalated. 'escalated' is final: nothing can change it.

When to call: once you have a decision for a ticket. You MUST call get_ticket first and read the current `status`; \
you MUST pass a `new_status` that is allowed from it. You MUST pass `agent` (your role name, for example \
'operator' or 'classifier').
- new_status='answered' requires a non-empty `answer` (the text for the customer).
- new_status='escalated' requires a non-empty `escalation_reason` (short, factual, one sentence).
When NOT to call: to read data (use get_ticket or list_tickets); to "check" whether a transition is possible \
(the allowed transitions are listed in the support://status-graph resource); when the ticket is already \
'escalated' (nothing can change it, report that and stop).

Optional fields (stored together with the status change): category in billing|technical|account|how_to|complaint|other; \
priority in low|normal|high|urgent; score integer 0..100 (use round(confidence * 100)).

Output on success: {"ok": true, "ticket": {...}, "transition": {"from": "new", "to": "answered"}}.
Output on rejection (is_error=true): {"ok": false, "error": {"code", "message", "hint", "current_status", \
"allowed_transitions"}}. If code is INVALID_STATUS_TRANSITION you MUST NOT repeat the same arguments: read \
`allowed_transitions`, choose one of them if it fits the situation, otherwise stop. If `allowed_transitions` is \
empty the ticket is final: stop and report it. If code is MISSING_REQUIRED_FIELD, repeat the call with the missing \
field filled. A rejected call changes nothing in the ticket.

Example: update_ticket(ticket_id=1, new_status='answered', agent='operator', category='account', \
priority='low', score=92, answer='Open Settings > Security > Change password.')
"""


def register_tools(server: MCPServer, service: TicketService) -> None:
    def guarded(fn):
        try:
            return ok(fn())
        except DomainError as err:
            return fail(err)
        except RepositoryUnavailable as err:
            return unavailable(err)

    @server.tool(
        name="get_ticket",
        description=GET_TICKET_DESCRIPTION,
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False),
    )
    def get_ticket(
        ticket_id: Annotated[int, Field(description="Ticket id, integer >= 1")],
    ) -> CallToolResult:
        return guarded(lambda: {"ticket": service.get_ticket(ticket_id)})

    @server.tool(
        name="list_tickets",
        description=LIST_TICKETS_DESCRIPTION,
        annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False),
    )
    def list_tickets(
        status: Annotated[str | None, Field(description="Filter: 'new', 'answered' or 'escalated'. Omit for all.")] = None,
        limit: Annotated[int, Field(description=f"Max items, 1..{MAX_LIMIT}")] = DEFAULT_LIMIT,
    ) -> CallToolResult:
        return guarded(lambda: service.list_tickets(status, limit))

    @server.tool(
        name="update_ticket",
        description=UPDATE_TICKET_DESCRIPTION,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
    )
    def update_ticket(
        ticket_id: Annotated[int, Field(description="Ticket id, integer >= 1")],
        new_status: Annotated[str, Field(description="Target status: 'answered' or 'escalated' (must be allowed from the current status)")],
        agent: Annotated[str, Field(description="Your role name for the trace, e.g. 'operator'")],
        category: Annotated[str | None, Field(description="billing|technical|account|how_to|complaint|other")] = None,
        priority: Annotated[str | None, Field(description="low|normal|high|urgent")] = None,
        score: Annotated[int | None, Field(description="Integer 0..100, round(confidence * 100)")] = None,
        answer: Annotated[str | None, Field(description="Customer-facing answer; required for 'answered'")] = None,
        escalation_reason: Annotated[str | None, Field(description="Short reason; required for 'escalated'")] = None,
    ) -> CallToolResult:
        return guarded(
            lambda: service.update_ticket(
                ticket_id=ticket_id,
                new_status=new_status,
                agent=agent,
                category=category,
                priority=priority,
                score=score,
                answer=answer,
                escalation_reason=escalation_reason,
            )
        )
