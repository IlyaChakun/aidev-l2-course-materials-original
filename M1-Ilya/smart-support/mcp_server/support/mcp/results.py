"""MCP response format: success and fixable error."""
from __future__ import annotations

import json
from typing import Any

from mcp.types import CallToolResult, TextContent

from ..domain import DomainError
from ..repository import RepositoryUnavailable


def _text(payload: dict[str, Any]) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


def ok(data: dict[str, Any]) -> CallToolResult:
    payload = {"ok": True, **data}
    return CallToolResult(content=_text(payload), structured_content=payload, is_error=False)


def fail(err: DomainError) -> CallToolResult:
    """Fixable error: code, message, current status, allowed transitions, hint."""
    payload = {"ok": False, "error": err.to_dict()}
    return CallToolResult(content=_text(payload), structured_content=payload, is_error=True)


def unavailable(err: RepositoryUnavailable) -> CallToolResult:
    payload = {
        "ok": False,
        "error": {
            "code": "STORAGE_UNAVAILABLE",
            "message": str(err),
            "hint": "This is not fixable by changing arguments. Stop and report that the ticket storage is unavailable.",
        },
    }
    return CallToolResult(content=_text(payload), structured_content=payload, is_error=True)
