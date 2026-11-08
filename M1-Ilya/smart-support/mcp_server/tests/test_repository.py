"""Repository and service on a temporary DB (schema and seed from db/)."""
import json
import sqlite3
import unittest

from support.domain import DomainError
from support.domain import errors as e
from support.domain.status_graph import ALLOWED_TRANSITIONS, STATUSES
from support.repository import RepositoryUnavailable, SqliteTicketRepository
from support.service import TicketService

from .helpers import fixed_clock, make_db


class RepoTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp, self.path = make_db()
        self.addCleanup(self.tmp.cleanup)
        self.repo = SqliteTicketRepository(self.path, clock=fixed_clock())
        self.svc = TicketService(self.repo)

    def raw(self, sql, *params):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()


class RepositoryTest(RepoTestBase):
    def test_seed_loaded(self):
        self.assertEqual(self.repo.counts_by_status(), {"new": 10, "answered": 5, "escalated": 5})

    def test_get_and_missing(self):
        self.assertEqual(self.repo.get(1).status, "new")
        self.assertIsNone(self.repo.get(999))

    def test_list_filter_and_limit(self):
        self.assertEqual(len(self.repo.list("new", 100)), 10)
        self.assertEqual([t.id for t in self.repo.list(None, 3)], [1, 2, 3])

    def test_missing_db_file(self):
        repo = SqliteTicketRepository(self.path.with_name("nope.sqlite"))
        with self.assertRaises(RepositoryUnavailable):
            repo.get(1)

    def test_missing_db_is_not_created(self):
        missing = self.path.with_name("nope.sqlite")
        with self.assertRaises(RepositoryUnavailable):
            SqliteTicketRepository(missing).list(None, 1)
        self.assertFalse(missing.exists())

    def test_schema_ddl_contains_tables_and_trigger(self):
        ddl = self.repo.schema_ddl()
        for needle in ("CREATE TABLE tickets", "CREATE TABLE agent_trace", "trg_tickets_status_transition"):
            self.assertIn(needle, ddl)


class ServiceUpdateTest(RepoTestBase):
    def test_happy_path_updates_and_traces(self):
        res = self.svc.update_ticket(1, "answered", "operator", category="account", priority="low", score=92, answer="Готово")
        self.assertEqual(res["transition"], {"from": "new", "to": "answered"})
        t = self.repo.get(1)
        self.assertEqual((t.status, t.category, t.priority, t.score, t.answer), ("answered", "account", "low", 92, "Готово"))
        self.assertEqual(t.last_modified, "2030-01-01T00:00:00Z")
        self.assertEqual(t.created_at, "2026-09-01T08:15:00Z")
        trace = self.repo.get_trace(1)
        self.assertEqual(len(trace), 1)
        self.assertEqual((trace[0]["agent"], trace[0]["outcome"], trace[0]["status_from"], trace[0]["status_to"]),
                         ("operator", "ok", "new", "answered"))
        self.assertEqual(json.loads(trace[0]["input_json"])["ticket_id"], 1)

    def test_full_lifecycle_new_answered_escalated(self):
        self.svc.update_ticket(2, "answered", "operator", answer="Ответ")
        self.svc.update_ticket(2, "escalated", "operator", escalation_reason="нужен платёжный специалист")
        self.assertEqual(self.repo.get(2).status, "escalated")
        self.assertEqual(len(self.repo.get_trace(2)), 2)

    def test_rejected_transition_changes_nothing_but_leaves_trace(self):
        before = self.repo.get(16)
        with self.assertRaises(DomainError) as cm:
            self.svc.update_ticket(16, "answered", "operator", answer="x")
        self.assertEqual(cm.exception.code, e.INVALID_STATUS_TRANSITION)
        self.assertEqual(self.repo.get(16), before)
        trace = self.repo.get_trace(16)
        rejected = [r for r in trace if r["outcome"] == "rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["error_code"], e.INVALID_STATUS_TRANSITION)
        self.assertEqual(rejected[0]["status_from"], "escalated")
        self.assertIsNone(rejected[0]["status_to"])

    def test_missing_field_rejected_with_trace(self):
        with self.assertRaises(DomainError):
            self.svc.update_ticket(1, "answered", "operator")
        self.assertEqual(self.repo.get(1).status, "new")
        self.assertEqual(self.repo.get_trace(1)[-1]["outcome"], "rejected")

    def test_unknown_ticket_not_found(self):
        with self.assertRaises(DomainError) as cm:
            self.svc.update_ticket(999, "answered", "operator", answer="x")
        self.assertEqual(cm.exception.code, e.TICKET_NOT_FOUND)
        self.assertEqual(self.raw("SELECT COUNT(*) FROM agent_trace WHERE ticket_id = 999")[0][0], 0)

    def test_invalid_agent_leaves_no_trace_and_no_change(self):
        with self.assertRaises(DomainError):
            self.svc.update_ticket(1, "answered", "Bad Agent", answer="x")
        self.assertEqual(self.repo.get(1).status, "new")
        self.assertEqual(self.repo.get_trace(1), [])

    def test_transaction_rolls_back_on_failure(self):
        class Boom(Exception):
            pass

        with self.assertRaises(Boom):
            with self.repo.transaction() as tx:
                tx.apply_patch(1, {"status": "answered", "answer": "x"})
                raise Boom()
        self.assertEqual(self.repo.get(1).status, "new")

    def test_list_summaries_have_no_body(self):
        out = self.svc.list_tickets("new", 3)
        self.assertEqual(out["count"], 3)
        self.assertNotIn("body", out["tickets"][0])

    def test_list_validation(self):
        with self.assertRaises(DomainError):
            self.svc.list_tickets("closed")
        for bad in (0, 101, True):
            with self.assertRaises(DomainError):
                self.svc.list_tickets(None, bad)

    def test_summary(self):
        self.assertEqual(self.svc.summary(), {"counts_by_status": {"new": 10, "answered": 5, "escalated": 5}, "total": 20})


class DomainMatchesDbTriggerTest(RepoTestBase):
    """The graph in domain and the trigger in the DB must match (D-011)."""

    def test_every_pair_agrees(self):
        # For each (from, to) pair, prepare a ticket in status "from" and try a direct UPDATE at the DB level.
        fixtures = {
            "new": {"status": "new"},
            "answered": {"status": "answered", "answer": "a"},
            "escalated": {"status": "escalated", "escalation_reason": "r"},
        }
        for src in STATUSES:
            for dst in STATUSES:
                if src == dst:
                    continue
                conn = sqlite3.connect(self.path)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("DELETE FROM agent_trace")
                conn.execute("DELETE FROM tickets")
                f = fixtures[src]
                conn.execute(
                    "INSERT INTO tickets (id, subject, body, customer_ref, status, answer, escalation_reason) "
                    "VALUES (1, 's', '', 'cust-001', ?, ?, ?)",
                    (f["status"], f.get("answer"), f.get("escalation_reason")),
                )
                extra = {"answered": ("answer = 'a'",), "escalated": ("escalation_reason = 'r'",), "new": ()}[dst]
                set_clause = ", ".join([f"status = '{dst}'", *extra])
                if dst == "new":
                    set_clause += ", answer = NULL, escalation_reason = NULL"
                db_allows = True
                try:
                    conn.execute(f"UPDATE tickets SET {set_clause} WHERE id = 1")
                except sqlite3.DatabaseError:
                    db_allows = False
                finally:
                    conn.close()
                self.assertEqual(db_allows, dst in ALLOWED_TRANSITIONS[src], f"{src}->{dst}")


if __name__ == "__main__":
    unittest.main()
