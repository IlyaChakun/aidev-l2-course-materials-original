"""MCP layer: tools, resources, the format of fixable errors. In-memory SDK client, temporary DB."""
import json
import unittest

from mcp import Client

from support.mcp.server import build_server
from support.repository import SqliteTicketRepository
from support.service import TicketService

from .helpers import fixed_clock, make_db


class McpTestBase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp, self.path = make_db()
        self.addCleanup(self.tmp.cleanup)
        self.repo = SqliteTicketRepository(self.path, clock=fixed_clock())
        self.server = build_server(TicketService(self.repo))

    async def call(self, name, args):
        async with Client(self.server) as client:
            return await client.call_tool(name, args)


class ListingTest(McpTestBase):
    async def test_three_tools_visible_with_when_and_when_not(self):
        async with Client(self.server) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
        self.assertEqual(set(tools), {"get_ticket", "list_tickets", "update_ticket"})
        for t in tools.values():
            self.assertIn("When to call", t.description, t.name)
            self.assertIn("When NOT to call", t.description, t.name)
            self.assertIn("Example", t.description, t.name)
        self.assertIn("You MUST", tools["update_ticket"].description)
        self.assertIn("allowed_transitions", tools["update_ticket"].description)
        self.assertEqual(tools["update_ticket"].input_schema["required"], ["ticket_id", "new_status", "agent"])

    async def test_resources_listed_and_readable(self):
        async with Client(self.server) as client:
            uris = {str(r.uri) for r in (await client.list_resources()).resources}
            self.assertEqual(uris, {"support://status-graph", "support://db-schema", "support://summary"})
            graph = json.loads((await client.read_resource("support://status-graph")).contents[0].text)
            summary = json.loads((await client.read_resource("support://summary")).contents[0].text)
            schema = (await client.read_resource("support://db-schema")).contents[0].text
            templates = await client.list_resource_templates()
        self.assertEqual(graph["allowed_transitions"]["new"], ["answered", "escalated"])
        self.assertEqual(graph["allowed_transitions"]["escalated"], [])
        self.assertEqual(summary["total"], 20)
        self.assertIn("CREATE TABLE tickets", schema)
        self.assertEqual(templates.resource_templates, [], "resource template это advanced, в М1 его нет")


class ToolsTest(McpTestBase):
    async def test_get_ticket(self):
        r = await self.call("get_ticket", {"ticket_id": 1})
        self.assertFalse(r.is_error)
        self.assertEqual(r.structured_content["ticket"]["status"], "new")
        self.assertEqual(r.structured_content["ticket"]["schema_version"], "1.0")

    async def test_get_ticket_not_found_is_fixable(self):
        r = await self.call("get_ticket", {"ticket_id": 999})
        self.assertTrue(r.is_error)
        err = r.structured_content["error"]
        self.assertEqual(err["code"], "TICKET_NOT_FOUND")
        self.assertIn("list_tickets", err["hint"])

    async def test_list_tickets(self):
        r = await self.call("list_tickets", {"status": "answered", "limit": 2})
        self.assertFalse(r.is_error)
        self.assertEqual(r.structured_content["count"], 2)

    async def test_list_tickets_bad_status(self):
        r = await self.call("list_tickets", {"status": "closed"})
        self.assertTrue(r.is_error)
        self.assertEqual(r.structured_content["error"]["code"], "UNKNOWN_STATUS")

    async def test_text_content_is_same_json_as_structured(self):
        r = await self.call("get_ticket", {"ticket_id": 2})
        self.assertEqual(json.loads(r.content[0].text), r.structured_content)

    async def test_lifecycle_and_refusal_via_protocol(self):
        ok = await self.call("update_ticket", {"ticket_id": 1, "new_status": "answered", "agent": "operator",
                                                 "answer": "Откройте Настройки.", "category": "account", "score": 90})
        self.assertFalse(ok.is_error)
        self.assertEqual(ok.structured_content["transition"], {"from": "new", "to": "answered"})
        back = await self.call("update_ticket", {"ticket_id": 1, "new_status": "new", "agent": "operator"})
        self.assertTrue(back.is_error)
        err = back.structured_content["error"]
        self.assertEqual(err["code"], "INVALID_STATUS_TRANSITION")
        self.assertEqual(err["current_status"], "answered")
        self.assertEqual(err["allowed_transitions"], ["escalated"])
        self.assertTrue(err["hint"])
        # fix following the hint
        fixed = await self.call("update_ticket", {"ticket_id": 1, "new_status": "escalated", "agent": "operator",
                                                    "escalation_reason": "нужен специалист"})
        self.assertFalse(fixed.is_error)
        final = await self.call("update_ticket", {"ticket_id": 1, "new_status": "answered", "agent": "operator", "answer": "x"})
        self.assertTrue(final.is_error)
        self.assertEqual(final.structured_content["error"]["allowed_transitions"], [])

    async def test_wrong_argument_type_is_reported_not_crash(self):
        r = await self.call("get_ticket", {"ticket_id": "abc"})
        self.assertTrue(r.is_error)

    async def test_missing_required_argument_is_reported(self):
        r = await self.call("update_ticket", {"ticket_id": 1, "new_status": "answered"})
        self.assertTrue(r.is_error)


if __name__ == "__main__":
    unittest.main()
