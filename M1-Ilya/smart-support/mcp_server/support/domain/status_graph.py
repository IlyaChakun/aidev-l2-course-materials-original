"""Ticket status graph. The single source of truth about allowed transitions.

Pure logic: no DB, network or MCP SDK. Reused by the tests and the future LangGraph (M3).
"""
from __future__ import annotations

STATUSES: tuple[str, ...] = ("new", "answered", "escalated")

ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "new": ("answered", "escalated"),
    "answered": ("escalated",),
    "escalated": (),
}

TERMINAL_STATUSES: tuple[str, ...] = tuple(s for s, nxt in ALLOWED_TRANSITIONS.items() if not nxt)


def is_known_status(status: str) -> bool:
    return status in ALLOWED_TRANSITIONS


def allowed_from(status: str) -> tuple[str, ...]:
    return ALLOWED_TRANSITIONS.get(status, ())


def can_transition(current: str, target: str) -> bool:
    return target in allowed_from(current)


def graph_as_dict() -> dict:
    """Graph description for the support://status-graph resource."""
    return {
        "statuses": list(STATUSES),
        "initial_status": "new",
        "terminal_statuses": list(TERMINAL_STATUSES),
        "allowed_transitions": {s: list(nxt) for s, nxt in ALLOWED_TRANSITIONS.items()},
        "field_rules": {
            "answered": "requires non-empty `answer`",
            "escalated": "requires non-empty `escalation_reason`",
        },
    }
