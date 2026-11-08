"""The smallest MCP server for the demo: one tool, one resource, one prompt. Only stdlib and mcp==2.3.0.

In the Inspector stand: /opt/mcp/venv/bin/python /home/node/own-server/faq_server.py
The folder is mounted from the host: edit the file, press Reconnect in Inspector, and the changes show up at once.
"""
from __future__ import annotations

import json

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

FAQ = {
    "password": "Open Settings > Security > Change password. The reset link in the email is valid for 24 hours.",
    "refund": "Refunds go back to the original card within 5 business days after approval.",
    "export": "Settings > Data > Export builds a CSV and emails a download link.",
}

server = MCPServer(
    "faq",
    instructions="Support FAQ. Call search_faq before you write an answer to a customer.",
)


@server.tool(
    description="Find FAQ answers whose topic or text contains the query. Returns a list of {topic, answer}; "
    "an empty list means the FAQ has nothing on it, so escalate instead of guessing.",
    annotations=ToolAnnotations(readOnlyHint=True),
)
def search_faq(query: str) -> list[dict[str, str]]:
    q = query.lower()
    return [{"topic": t, "answer": a} for t, a in FAQ.items() if q in t or q in a.lower()]


@server.resource(
    "faq://topics",
    name="topics",
    title="FAQ topics",
    description="All topics the FAQ covers.",
    mime_type="application/json",
)
def topics() -> str:
    return json.dumps(sorted(FAQ))


@server.prompt(description="Draft a two-sentence reply to a customer ticket using the FAQ.")
def answer_ticket(ticket_text: str) -> str:
    return f"Call search_faq for the main topic of this ticket, then reply in two sentences:\n\n{ticket_text}"


if __name__ == "__main__":
    server.run("stdio")
