"""Ticket model and change validation (plan_update). Pure logic, no DB or network."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from . import errors as e
from .status_graph import allowed_from, can_transition, is_known_status, STATUSES

CATEGORIES: tuple[str, ...] = ("billing", "technical", "account", "how_to", "complaint", "other")
PRIORITIES: tuple[str, ...] = ("low", "normal", "high", "urgent")
AGENT_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
MAX_TEXT = 4000


@dataclass(frozen=True)
class Ticket:
    id: int
    subject: str
    body: str
    customer_ref: str
    status: str
    category: str | None
    priority: str | None
    score: int | None
    answer: str | None
    escalation_reason: str | None
    created_at: str
    last_modified: str

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "id": self.id,
            "subject": self.subject,
            "body": self.body,
            "customer_ref": self.customer_ref,
            "status": self.status,
            "category": self.category,
            "priority": self.priority,
            "score": self.score,
            "answer": self.answer,
            "escalation_reason": self.escalation_reason,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
        }


@dataclass(frozen=True)
class UpdateRequest:
    ticket_id: int
    new_status: str
    agent: str
    category: str | None = None
    priority: str | None = None
    score: int | None = None
    answer: str | None = None
    escalation_reason: str | None = None


def validate_agent(agent: Any) -> str:
    if not isinstance(agent, str) or not AGENT_RE.match(agent):
        raise e.DomainError(
            code=e.INVALID_VALUE,
            message=f"agent {agent!r} is not a valid agent name",
            hint="Pass `agent` as lowercase letters, digits, '_' or '-', starting with a letter, up to 64 chars "
            "(for example 'operator' or 'classifier').",
            details={"field": "agent"},
        )
    return agent


def _blank(value: str | None) -> bool:
    return value is None or not value.strip()


def plan_update(ticket: Ticket, req: UpdateRequest) -> dict[str, Any]:
    """Checks the request against the current ticket and returns the fields to write.

    Check order: status is known -> transition is allowed -> required fields -> values.
    Raises DomainError with a fixable hint. Writes nothing.
    """
    current = ticket.status
    allowed = list(allowed_from(current))

    if not is_known_status(req.new_status):
        raise e.DomainError(
            code=e.UNKNOWN_STATUS,
            message=f"unknown status {req.new_status!r}",
            hint=f"Use one of {list(STATUSES)}. For this ticket only {allowed} is allowed right now."
            if allowed
            else f"Use one of {list(STATUSES)}. This ticket is in a terminal status and cannot change.",
            current_status=current,
            allowed_transitions=allowed,
        )

    if not can_transition(current, req.new_status):
        if not allowed:
            hint = (
                f"Ticket {ticket.id} is in terminal status '{current}' and can no longer change. "
                "Do not retry. Report that the ticket is already handled."
            )
        else:
            hint = (
                f"Ticket {ticket.id} is '{current}'. Retry update_ticket with new_status "
                f"in {allowed}, or stop if none fits."
            )
        raise e.DomainError(
            code=e.INVALID_STATUS_TRANSITION,
            message=f"cannot move ticket {ticket.id} from '{current}' to '{req.new_status}'",
            hint=hint,
            current_status=current,
            allowed_transitions=allowed,
        )

    if req.new_status == "answered":
        if _blank(req.answer):
            raise e.DomainError(
                code=e.MISSING_REQUIRED_FIELD,
                message="new_status 'answered' requires a non-empty `answer`",
                hint="Call update_ticket again with the same new_status and a non-empty `answer`.",
                current_status=current,
                allowed_transitions=allowed,
                details={"field": "answer"},
            )
        if not _blank(req.escalation_reason):
            raise e.DomainError(
                code=e.INVALID_VALUE,
                message="`escalation_reason` must be empty when new_status is 'answered'",
                hint="Remove `escalation_reason`, or use new_status 'escalated' if the ticket must be escalated.",
                current_status=current,
                allowed_transitions=allowed,
                details={"field": "escalation_reason"},
            )
    if req.new_status == "escalated" and _blank(req.escalation_reason):
        raise e.DomainError(
            code=e.MISSING_REQUIRED_FIELD,
            message="new_status 'escalated' requires a non-empty `escalation_reason`",
            hint="Call update_ticket again with the same new_status and a short `escalation_reason`.",
            current_status=current,
            allowed_transitions=allowed,
            details={"field": "escalation_reason"},
        )

    _check_enum("category", req.category, CATEGORIES, current, allowed)
    _check_enum("priority", req.priority, PRIORITIES, current, allowed)
    if req.score is not None and (isinstance(req.score, bool) or not isinstance(req.score, int) or not 0 <= req.score <= 100):
        raise e.DomainError(
            code=e.INVALID_VALUE,
            message=f"score {req.score!r} is outside 0..100",
            hint="Pass `score` as an integer from 0 to 100 (round(confidence * 100)), or omit it.",
            current_status=current,
            allowed_transitions=allowed,
            details={"field": "score"},
        )
    for name in ("answer", "escalation_reason"):
        value = getattr(req, name)
        if value is not None and len(value) > MAX_TEXT:
            raise e.DomainError(
                code=e.INVALID_VALUE,
                message=f"`{name}` is longer than {MAX_TEXT} characters",
                hint=f"Shorten `{name}` to at most {MAX_TEXT} characters and retry.",
                current_status=current,
                allowed_transitions=allowed,
                details={"field": name},
            )

    patch: dict[str, Any] = {"status": req.new_status}
    for name in ("category", "priority", "score"):
        value = getattr(req, name)
        if value is not None:
            patch[name] = value
    if req.new_status == "answered":
        patch["answer"] = req.answer.strip()  # type: ignore[union-attr]
    else:
        patch["escalation_reason"] = req.escalation_reason.strip()  # type: ignore[union-attr]
        if not _blank(req.answer):
            patch["answer"] = req.answer.strip()  # type: ignore[union-attr]
    return patch


def _check_enum(name: str, value: str | None, allowed_values: tuple[str, ...], current: str, allowed: list[str]) -> None:
    if value is not None and value not in allowed_values:
        raise e.DomainError(
            code=e.INVALID_VALUE,
            message=f"{name} {value!r} is not allowed",
            hint=f"Use one of {list(allowed_values)} for `{name}`, or omit it.",
            current_status=current,
            allowed_transitions=allowed,
            details={"field": name, "allowed_values": list(allowed_values)},
        )
