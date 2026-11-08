"""Domain errors. Each one carries everything an agent needs to correct itself without a human."""
from __future__ import annotations

from dataclasses import dataclass, field

TICKET_NOT_FOUND = "TICKET_NOT_FOUND"
INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
UNKNOWN_STATUS = "UNKNOWN_STATUS"
MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
INVALID_VALUE = "INVALID_VALUE"


@dataclass
class DomainError(Exception):
    code: str
    message: str
    hint: str
    current_status: str | None = None
    allowed_transitions: list[str] | None = None
    details: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        Exception.__init__(self, f"{self.code}: {self.message}")

    def to_dict(self) -> dict:
        out: dict = {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
        }
        if self.current_status is not None:
            out["current_status"] = self.current_status
        if self.allowed_transitions is not None:
            out["allowed_transitions"] = list(self.allowed_transitions)
        if self.details:
            out["details"] = self.details
        return out
