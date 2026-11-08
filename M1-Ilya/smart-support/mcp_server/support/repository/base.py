"""Data access interface. SQLite now, Postgres later: only one implementation file gets replaced.

The domain knows nothing about the DB; the service layer works only with this interface.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol

from ..domain import Ticket


class TicketTx(Protocol):
    """Operations inside one transaction."""

    def get(self, ticket_id: int) -> Ticket | None: ...

    def apply_patch(self, ticket_id: int, patch: dict[str, Any]) -> None:
        """Writes the fields and updates last_modified."""

    def add_trace(
        self,
        *,
        ticket_id: int,
        agent: str,
        input_json: str | None,
        output_json: str | None,
        status_from: str | None,
        status_to: str | None,
        outcome: str,
        error_code: str | None,
    ) -> int: ...


class TicketRepository(Protocol):
    def get(self, ticket_id: int) -> Ticket | None: ...

    def list(self, status: str | None, limit: int) -> list[Ticket]: ...

    def counts_by_status(self) -> dict[str, int]: ...

    def schema_ddl(self) -> str:
        """DB schema text for the support://db-schema resource."""

    def get_trace(self, ticket_id: int) -> list[dict[str, Any]]: ...

    def transaction(self) -> AbstractContextManager[TicketTx]:
        """Commit on normal exit, rollback on exception."""


class RepositoryUnavailable(Exception):
    """DB unavailable (no file, schema not applied)."""
