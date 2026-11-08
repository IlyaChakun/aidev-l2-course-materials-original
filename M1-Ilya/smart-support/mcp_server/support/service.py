"""Service layer: scenarios over domain + repository. No knowledge of MCP.

This is where the "read -> check -> write -> leave a trace" transaction lives.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .domain import DomainError, UpdateRequest, plan_update, validate_agent, graph_as_dict
from .domain import errors as e
from .domain.status_graph import STATUSES, is_known_status
from .repository import TicketRepository

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _not_found(ticket_id: int) -> DomainError:
    return DomainError(
        code=e.TICKET_NOT_FOUND,
        message=f"ticket {ticket_id} does not exist",
        hint="Call list_tickets (optionally with status='new') to find an existing ticket id, then retry.",
        details={"ticket_id": ticket_id},
    )


class TicketService:
    def __init__(self, repo: TicketRepository) -> None:
        self._repo = repo

    def get_ticket(self, ticket_id: int) -> dict:
        ticket = self._repo.get(ticket_id)
        if ticket is None:
            raise _not_found(ticket_id)
        return ticket.to_dict()

    def list_tickets(self, status: str | None = None, limit: int = DEFAULT_LIMIT) -> dict:
        if status is not None and not is_known_status(status):
            raise DomainError(
                code=e.UNKNOWN_STATUS,
                message=f"unknown status filter {status!r}",
                hint=f"Use one of {list(STATUSES)} or omit `status` to list all tickets.",
            )
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
            raise DomainError(
                code=e.INVALID_VALUE,
                message=f"limit {limit!r} is outside 1..{MAX_LIMIT}",
                hint=f"Pass `limit` as an integer from 1 to {MAX_LIMIT} (default {DEFAULT_LIMIT}).",
                details={"field": "limit"},
            )
        tickets = self._repo.list(status, limit)
        items = [
            {
                "id": t.id,
                "subject": t.subject,
                "status": t.status,
                "category": t.category,
                "priority": t.priority,
                "score": t.score,
                "last_modified": t.last_modified,
            }
            for t in tickets
        ]
        return {"count": len(items), "status_filter": status, "limit": limit, "tickets": items}

    def update_ticket(
        self,
        ticket_id: int,
        new_status: str,
        agent: str,
        category: str | None = None,
        priority: str | None = None,
        score: int | None = None,
        answer: str | None = None,
        escalation_reason: str | None = None,
    ) -> dict:
        validate_agent(agent)
        req = UpdateRequest(
            ticket_id=ticket_id,
            new_status=new_status,
            agent=agent,
            category=category,
            priority=priority,
            score=score,
            answer=answer,
            escalation_reason=escalation_reason,
        )
        rejected: DomainError | None = None
        result: dict | None = None
        with self._repo.transaction() as tx:
            ticket = tx.get(ticket_id)
            if ticket is None:
                raise _not_found(ticket_id)
            try:
                patch = plan_update(ticket, req)
            except DomainError as err:
                rejected = err
                tx.add_trace(
                    ticket_id=ticket_id,
                    agent=agent,
                    input_json=_dump(asdict(req)),
                    output_json=_dump(err.to_dict()),
                    status_from=ticket.status,
                    status_to=None,
                    outcome="rejected",
                    error_code=err.code,
                )
            else:
                tx.apply_patch(ticket_id, patch)
                tx.add_trace(
                    ticket_id=ticket_id,
                    agent=agent,
                    input_json=_dump(asdict(req)),
                    output_json=_dump(patch),
                    status_from=ticket.status,
                    status_to=new_status,
                    outcome="ok",
                    error_code=None,
                )
                updated = tx.get(ticket_id)
                assert updated is not None
                result = {
                    "ticket": updated.to_dict(),
                    "transition": {"from": ticket.status, "to": new_status},
                }
        if rejected is not None:
            raise rejected
        assert result is not None
        return result

    # --- data for resources ---
    def status_graph(self) -> dict:
        return graph_as_dict()

    def db_schema(self) -> str:
        return self._repo.schema_ddl()

    def summary(self) -> dict:
        counts = self._repo.counts_by_status()
        return {"counts_by_status": {s: counts.get(s, 0) for s in STATUSES}, "total": sum(counts.values())}
