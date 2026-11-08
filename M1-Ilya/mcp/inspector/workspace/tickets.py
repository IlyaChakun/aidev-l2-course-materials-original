"""In-memory tickets for the demo."""

from dataclasses import dataclass

from status_graph import check_transition


@dataclass
class Ticket:
    id: int
    subject: str
    status: str = "new"
    answer: str | None = None


def answer(ticket: Ticket, text: str) -> Ticket:
    check_transition(ticket.status, "answered")
    ticket.status = "answered"
    ticket.answer = text
    return ticket


def escalate(ticket: Ticket) -> Ticket:
    check_transition(ticket.status, "escalated")
    ticket.status = "escalated"
    return ticket
