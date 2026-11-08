"""TicketRepository implementation on SQLite (standard library)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

from ..domain import Ticket
from .base import RepositoryUnavailable

_COLUMNS = (
    "id, subject, body, customer_ref, status, category, priority, score, "
    "answer, escalation_reason, created_at, last_modified"
)
_PATCHABLE = {"status", "category", "priority", "score", "answer", "escalation_reason"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_ticket(row: sqlite3.Row) -> Ticket:
    return Ticket(**{k: row[k] for k in row.keys()})


class _Tx:
    def __init__(self, conn: sqlite3.Connection, clock: Callable[[], str]) -> None:
        self._conn = conn
        self._clock = clock

    def get(self, ticket_id: int) -> Ticket | None:
        row = self._conn.execute(f"SELECT {_COLUMNS} FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return _row_to_ticket(row) if row else None

    def apply_patch(self, ticket_id: int, patch: dict[str, Any]) -> None:
        unknown = set(patch) - _PATCHABLE
        if unknown:
            raise ValueError(f"unpatchable fields: {sorted(unknown)}")
        sets = [f"{name} = ?" for name in patch] + ["last_modified = ?"]
        params = [*patch.values(), self._clock(), ticket_id]
        self._conn.execute(f"UPDATE tickets SET {', '.join(sets)} WHERE id = ?", params)

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
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO agent_trace (ticket_id, agent, input_json, output_json, status_from, status_to, "
            "outcome, error_code, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, agent, input_json, output_json, status_from, status_to, outcome, error_code, self._clock()),
        )
        return int(cur.lastrowid)


class SqliteTicketRepository:
    def __init__(self, db_path: str | Path, clock: Callable[[], str] = utc_now) -> None:
        self._path = Path(db_path)
        self._clock = clock

    def _connect(self) -> sqlite3.Connection:
        if not self._path.exists():
            raise RepositoryUnavailable(
                f"database file not found: {self._path}. Create it with `make db-reset db-seed`."
            )
        conn = sqlite3.connect(f"file:{self._path}?mode=rw", uri=True, isolation_level=None, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute("SELECT 1 FROM tickets LIMIT 1")
        except sqlite3.OperationalError as exc:
            conn.close()
            raise RepositoryUnavailable(
                f"database {self._path} has no `tickets` table. Run `make db-reset db-seed`."
            ) from exc
        return conn

    @contextmanager
    def _read(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def get(self, ticket_id: int) -> Ticket | None:
        with self._read() as conn:
            return _Tx(conn, self._clock).get(ticket_id)

    def list(self, status: str | None, limit: int) -> list[Ticket]:
        sql = f"SELECT {_COLUMNS} FROM tickets"
        params: list[Any] = []
        if status is not None:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY id ASC LIMIT ?"
        params.append(limit)
        with self._read() as conn:
            return [_row_to_ticket(r) for r in conn.execute(sql, params).fetchall()]

    def counts_by_status(self) -> dict[str, int]:
        with self._read() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS n FROM tickets GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}

    def schema_ddl(self) -> str:
        with self._read() as conn:
            rows = conn.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
                "ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 ELSE 2 END, name"
            ).fetchall()
        return ";\n\n".join(r["sql"] for r in rows) + ";\n"

    def get_trace(self, ticket_id: int) -> list[dict[str, Any]]:
        with self._read() as conn:
            rows = conn.execute(
                "SELECT id, ticket_id, agent, input_json, output_json, status_from, status_to, outcome, "
                "error_code, created_at FROM agent_trace WHERE ticket_id = ? ORDER BY id ASC",
                (ticket_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    @contextmanager
    def transaction(self) -> Iterator[_Tx]:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield _Tx(conn, self._clock)
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            else:
                conn.execute("COMMIT")
        finally:
            conn.close()
