"""Isolation tests: tenant A never sees tenant B.

Run against the safe endpoint (default):          pytest -q tests          -> must pass
Run against the buggy endpoint:  SEARCH_PATH=/debug/search_unsafe pytest -k search_isolation -> must fail
"""
import json
import os
import re
from pathlib import Path

import httpx
import pytest

API = os.getenv("API_URL", "http://localhost:8471")
SEARCH_PATH = os.getenv("SEARCH_PATH", "/search")
CFG = json.loads((Path(__file__).resolve().parent.parent / "config" / "demo_queries.json").read_text())
QUERIES = CFG["queries"]
PROBE = CFG["probe_doc"]

USERS = {  # token -> (tenant, groups); mirrors config/tokens.json
    "tok-acme-support": ("acme", {"all"}),
    "tok-acme-finance": ("acme", {"all", "finance"}),
    "tok-globex-support": ("globex", {"all"}),
    "tok-globex-finance": ("globex", {"all", "finance"}),
    "tok-initech-support": ("initech", {"all"}),
}
SECRET = {"acme": "ACME-FIN-7731", "globex": "GLOBEX-VIP-2026", "initech": "INITECH-TPS-0042"}


def get(path, token, **params):
    r = httpx.get(f"{API}{path}", params=params, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    r.raise_for_status()
    return r.json()


def hits(token, q, k=8):
    return get(SEARCH_PATH, token, q=q, k=k)["hits"]


# ---- the core property, parametrized over every user and every demo query ----

@pytest.mark.parametrize("q", QUERIES)
@pytest.mark.parametrize("token", USERS)
def test_search_isolation_tenant(token, q):
    tenant, _ = USERS[token]
    foreign = [(h["tenant_id"], h["doc_id"]) for h in hits(token, q) if h["tenant_id"] != tenant]
    assert not foreign, f"{tenant} received chunks of other tenants: {foreign}"


@pytest.mark.parametrize("q", QUERIES)
@pytest.mark.parametrize("token", USERS)
def test_search_isolation_acl(token, q):
    _, groups = USERS[token]
    denied = [(h["tenant_id"], h["doc_id"], h["groups"]) for h in hits(token, q) if not set(h["groups"]) & groups]
    assert not denied, f"user with groups {sorted(groups)} received restricted chunks: {denied}"


@pytest.mark.parametrize("token", USERS)
def test_search_isolation_no_foreign_secret(token):
    tenant, groups = USERS[token]
    forbidden = {c for t, c in SECRET.items() if t != tenant or "finance" not in groups}
    for q in QUERIES:
        text = " ".join(h["text"] for h in hits(token, q))
        found = forbidden & set(re.findall(r"[A-Z]+-[A-Z]+-\d{4}", text))
        assert not found, f"{token} saw secret codes {found} for query {q!r}"


# ---- positive control: the filter is not simply "return nothing" ----

def test_finance_sees_own_secret():
    text = " ".join(h["text"] for h in get("/search", "tok-acme-finance", q=QUERIES[1], k=5)["hits"])
    assert SECRET["acme"] in text


# ---- the tenant can only come from the token ----

def test_unauthenticated_is_rejected():
    assert httpx.get(f"{API}/search", params={"q": QUERIES[0]}, timeout=30).status_code == 401
    r = httpx.get(f"{API}/search", params={"q": QUERIES[0]},
                  headers={"Authorization": "Bearer tok-made-up"}, timeout=30)
    assert r.status_code == 401


def test_spoofed_tenant_param_and_header_are_ignored():
    r = httpx.get(f"{API}/search", params={"q": QUERIES[0], "tenant_id": "globex", "tenant": "globex"},
                  headers={"Authorization": "Bearer tok-acme-support", "X-Tenant-Id": "globex"}, timeout=60)
    r.raise_for_status()
    assert {h["tenant_id"] for h in r.json()["hits"]} == {"acme"}


def test_delete_is_tenant_scoped():
    # acme tries to delete a globex document by its id: nothing happens.
    r = httpx.delete(f"{API}/docs/globex-internal-pricing",
                     headers={"Authorization": "Bearer tok-acme-support"}, timeout=60)
    r.raise_for_status()
    assert r.json()["deleted_points"] == 0
    text = " ".join(h["text"] for h in get("/search", "tok-globex-finance", q=QUERIES[0], k=8)["hits"])
    assert SECRET["globex"] in text


def test_upsert_takes_tenant_from_token_not_body():
    auth = {"Authorization": "Bearer tok-acme-support"}
    body = dict(PROBE, tenant_id="globex")  # attempt to write into another tenant
    r = httpx.post(f"{API}/docs", json=body, headers=auth, timeout=60)
    r.raise_for_status()
    assert r.json()["tenant_id"] == "acme"
    try:
        acme = get("/search", "tok-acme-support", q=PROBE["text"], k=3)["hits"]
        globex = get("/search", "tok-globex-support", q=PROBE["text"], k=3)["hits"]
        assert any(h["doc_id"] == PROBE["doc_id"] for h in acme)
        assert not any(h["doc_id"] == PROBE["doc_id"] for h in globex)
    finally:
        d = httpx.delete(f"{API}/docs/{PROBE['doc_id']}", headers=auth, timeout=60).json()
        assert d["deleted_points"] == 1


def test_cannot_write_for_a_group_you_are_not_in():
    r = httpx.post(f"{API}/docs", json=dict(PROBE, groups=["finance"]),
                   headers={"Authorization": "Bearer tok-acme-support"}, timeout=60)
    assert r.status_code == 403
