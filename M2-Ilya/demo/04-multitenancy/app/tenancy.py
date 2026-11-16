"""Auth and tenant scoping.

Rule: the tenant and the groups come ONLY from the authenticated token.
Nothing from the request (query string, body, headers other than Authorization)
can change them. Every read, write and delete goes through TenantScope, which
injects the filter, so a handler cannot forget it.
"""
import json
from dataclasses import dataclass

from app import qdrant, settings


@dataclass(frozen=True)
class Principal:
    user: str
    tenant: str
    groups: tuple


def load_tokens():
    return json.loads((settings.CONFIG_DIR / "tokens.json").read_text())["tokens"]


_TOKENS = None


def principal_from_bearer(authorization: str | None):
    global _TOKENS
    if _TOKENS is None:
        _TOKENS = load_tokens()
    if not authorization or not authorization.startswith("Bearer "):
        return None
    entry = _TOKENS.get(authorization.removeprefix("Bearer ").strip())
    if not entry:
        return None
    return Principal(entry["user"], entry["tenant"], tuple(entry["groups"]))


class TenantScope:
    """All vector DB access for one principal. The only way the API talks to Qdrant."""

    def __init__(self, p: Principal, collection=settings.COLLECTION):
        self.p = p
        self.collection = collection

    def filter(self, *extra):
        must = [
            {"key": "tenant_id", "match": {"value": self.p.tenant}},
            {"key": "groups", "match": {"any": list(self.p.groups)}},
        ]
        must.extend(extra)
        return {"must": must}

    def search(self, vector, k=5):
        body = {
            "query": vector,
            "using": "dense",
            "filter": self.filter(),
            "limit": k,
            "with_payload": True,
        }
        return qdrant.query(body, name=self.collection), body

    def upsert(self, points):
        for pt in points:
            # Overwrite whatever the caller put there.
            pt["payload"]["tenant_id"] = self.p.tenant
        qdrant.upsert(points, name=self.collection)

    def delete_doc(self, doc_id):
        # Tenant is part of the delete filter: doc_id alone is NOT unique across tenants.
        flt = {"must": [
            {"key": "tenant_id", "match": {"value": self.p.tenant}},
            {"key": "doc_id", "match": {"value": doc_id}},
        ]}
        before = qdrant.count(flt, name=self.collection)
        qdrant.delete_by_filter(flt, name=self.collection)
        return before, flt


def unsafe_search(vector, k=5):
    """The bug: a 'helper' that searches the whole collection. Used by the debug endpoint."""
    body = {"query": vector, "using": "dense", "limit": k, "with_payload": True}
    return qdrant.query(body), body
