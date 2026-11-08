"""Domain logic tests. They import neither the MCP SDK, nor sqlite, nor the network."""
import ast
import itertools
import unittest
from pathlib import Path

from support.domain import (
    ALLOWED_TRANSITIONS,
    STATUSES,
    DomainError,
    Ticket,
    UpdateRequest,
    allowed_from,
    can_transition,
    plan_update,
    validate_agent,
)
from support.domain import errors as e


def ticket(status="new", **kw):
    base = dict(
        id=1, subject="s", body="b", customer_ref="cust-001", status=status, category=None, priority=None,
        score=None, answer=None, escalation_reason=None, created_at="2026-01-01T00:00:00Z",
        last_modified="2026-01-01T00:00:00Z",
    )
    base.update(kw)
    return Ticket(**base)


def req(new_status, **kw):
    return UpdateRequest(ticket_id=1, new_status=new_status, agent="operator", **kw)


class StatusGraphTest(unittest.TestCase):
    def test_exactly_three_allowed_transitions(self):
        allowed = {(a, b) for a in STATUSES for b in STATUSES if can_transition(a, b)}
        self.assertEqual(allowed, {("new", "answered"), ("new", "escalated"), ("answered", "escalated")})

    def test_all_other_pairs_forbidden(self):
        for a, b in itertools.product(STATUSES, STATUSES):
            if (a, b) not in {("new", "answered"), ("new", "escalated"), ("answered", "escalated")}:
                self.assertFalse(can_transition(a, b), (a, b))

    def test_escalated_is_terminal(self):
        self.assertEqual(allowed_from("escalated"), ())

    def test_unknown_status_has_no_transitions(self):
        self.assertEqual(allowed_from("closed"), ())


class PlanUpdateTest(unittest.TestCase):
    def test_new_to_answered_ok(self):
        patch = plan_update(ticket(), req("answered", answer=" Ответ ", category="account", priority="low", score=90))
        self.assertEqual(patch["status"], "answered")
        self.assertEqual(patch["answer"], "Ответ")
        self.assertEqual((patch["category"], patch["priority"], patch["score"]), ("account", "low", 90))

    def test_new_to_escalated_ok(self):
        patch = plan_update(ticket(), req("escalated", escalation_reason="payment"))
        self.assertEqual(patch["status"], "escalated")
        self.assertEqual(patch["escalation_reason"], "payment")
        self.assertNotIn("answer", patch)

    def test_answered_to_escalated_keeps_old_answer(self):
        patch = plan_update(ticket("answered", answer="old"), req("escalated", escalation_reason="needs engineer"))
        self.assertNotIn("answer", patch)

    def assertRejected(self, current, request, code):
        with self.assertRaises(DomainError) as cm:
            plan_update(ticket(current), request)
        self.assertEqual(cm.exception.code, code)
        return cm.exception

    def test_escalated_cannot_change_and_error_is_fixable(self):
        err = self.assertRejected("escalated", req("answered", answer="x"), e.INVALID_STATUS_TRANSITION)
        self.assertEqual(err.current_status, "escalated")
        self.assertEqual(err.allowed_transitions, [])
        self.assertIn("terminal", err.hint)

    def test_answered_to_new_rejected_with_allowed_list(self):
        err = self.assertRejected("answered", req("new"), e.INVALID_STATUS_TRANSITION)
        self.assertEqual(err.allowed_transitions, ["escalated"])
        self.assertIn("escalated", err.hint)

    def test_same_status_rejected(self):
        self.assertRejected("new", req("new"), e.INVALID_STATUS_TRANSITION)
        self.assertRejected("answered", req("answered", answer="x"), e.INVALID_STATUS_TRANSITION)

    def test_unknown_status(self):
        err = self.assertRejected("new", req("closed"), e.UNKNOWN_STATUS)
        self.assertEqual(err.allowed_transitions, ["answered", "escalated"])

    def test_answered_requires_answer(self):
        for bad in (None, "", "   "):
            err = self.assertRejected("new", req("answered", answer=bad), e.MISSING_REQUIRED_FIELD)
            self.assertEqual(err.details["field"], "answer")

    def test_escalated_requires_reason(self):
        for bad in (None, "", "  "):
            err = self.assertRejected("new", req("escalated", escalation_reason=bad), e.MISSING_REQUIRED_FIELD)
            self.assertEqual(err.details["field"], "escalation_reason")

    def test_answered_rejects_reason(self):
        self.assertRejected("new", req("answered", answer="x", escalation_reason="y"), e.INVALID_VALUE)

    def test_bad_enums_and_score(self):
        self.assertRejected("new", req("answered", answer="x", category="weather"), e.INVALID_VALUE)
        self.assertRejected("new", req("answered", answer="x", priority="asap"), e.INVALID_VALUE)
        for bad in (-1, 101, True):
            self.assertRejected("new", req("answered", answer="x", score=bad), e.INVALID_VALUE)

    def test_score_bounds_ok(self):
        for good in (0, 100):
            self.assertEqual(plan_update(ticket(), req("answered", answer="x", score=good))["score"], good)

    def test_error_dict_has_agent_facing_fields(self):
        with self.assertRaises(DomainError) as cm:
            plan_update(ticket("answered"), req("new"))
        d = cm.exception.to_dict()
        for key in ("code", "message", "hint", "current_status", "allowed_transitions"):
            self.assertIn(key, d)

    def test_validate_agent(self):
        self.assertEqual(validate_agent("operator"), "operator")
        for bad in ("", "Operator", "1op", "a b", None, "x" * 65):
            with self.assertRaises(DomainError):
                validate_agent(bad)


class DomainPurityTest(unittest.TestCase):
    """Domain must not import the SDK, the DB or the network (component independence rule)."""

    FORBIDDEN = {"mcp", "sqlite3", "socket", "http", "urllib", "requests", "httpx", "pydantic", "support.repository"}

    def test_no_forbidden_imports(self):
        for path in (Path(__file__).resolve().parents[1] / "support" / "domain").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module]
                for name in names:
                    root = name.split(".")[0]
                    self.assertNotIn(root, self.FORBIDDEN, f"{path.name} imports {name}")
                    self.assertNotIn(name, self.FORBIDDEN, f"{path.name} imports {name}")


if __name__ == "__main__":
    unittest.main()
