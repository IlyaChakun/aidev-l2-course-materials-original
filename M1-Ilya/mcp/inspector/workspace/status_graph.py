"""Ticket statuses and the transitions the support desk allows."""

ALLOWED = {
    "new": {"answered", "escalated"},
    "answered": {"escalated"},
    "escalated": set(),
}


class InvalidTransition(Exception):
    def __init__(self, current: str, requested: str):
        self.current = current
        self.requested = requested
        self.allowed = sorted(ALLOWED.get(current, set()))
        super().__init__(f"{current} -> {requested} is not allowed; allowed: {self.allowed}")


def check_transition(current: str, requested: str) -> None:
    if requested not in ALLOWED.get(current, set()):
        raise InvalidTransition(current, requested)
