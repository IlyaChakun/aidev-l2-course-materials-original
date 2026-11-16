"""Thin REST client for Qdrant. Plain JSON on purpose: the request bodies printed
in the lecture are the same ones the code sends."""
import httpx

from app import settings

_client = httpx.Client(base_url=settings.QDRANT_URL, timeout=60)


def call(method, path, json=None, params=None, ok404=False):
    r = _client.request(method, path, json=json, params=params)
    if ok404 and r.status_code == 404:
        return None
    if r.status_code >= 400:
        raise RuntimeError(f"Qdrant {method} {path} -> {r.status_code}: {r.text[:500]}")
    return r.json().get("result")


def create_shared_collection(name=settings.COLLECTION):
    call("DELETE", f"/collections/{name}", ok404=True)
    call("PUT", f"/collections/{name}", json={
        "vectors": {"dense": {"size": settings.EMBED_DIM, "distance": "Cosine"}},
        "sparse_vectors": {"bm25": {"modifier": "idf"}},
        # No global HNSW graph (m=0); build per-tenant graphs instead (payload_m=16).
        "hnsw_config": {"payload_m": 16, "m": 0},
    })
    # Tenant index: keyword + is_tenant co-locates each tenant's points on disk.
    call("PUT", f"/collections/{name}/index", params={"wait": "true"}, json={
        "field_name": "tenant_id",
        "field_schema": {"type": "keyword", "is_tenant": True},
    })
    for field in ("groups", "doc_id"):
        call("PUT", f"/collections/{name}/index", params={"wait": "true"},
             json={"field_name": field, "field_schema": "keyword"})


def upsert(points, name=settings.COLLECTION, shard_key=None, batch=64):
    for i in range(0, len(points), batch):
        body = {"points": points[i:i + batch]}
        if shard_key is not None:
            body["shard_key"] = shard_key
        call("PUT", f"/collections/{name}/points", params={"wait": "true"}, json=body)


def count(flt=None, name=settings.COLLECTION, shard_key=None):
    body = {"exact": True}
    if flt:
        body["filter"] = flt
    if shard_key is not None:
        body["shard_key"] = shard_key
    return call("POST", f"/collections/{name}/points/count", json=body)["count"]


def query(body, name=settings.COLLECTION):
    return call("POST", f"/collections/{name}/points/query", json=body)["points"]


def delete_by_filter(flt, name=settings.COLLECTION, shard_key=None):
    body = {"filter": flt}
    if shard_key is not None:
        body["shard_key"] = shard_key
    return call("POST", f"/collections/{name}/points/delete", params={"wait": "true"}, json=body)


def tenant_filter(tenant):
    return {"must": [{"key": "tenant_id", "match": {"value": tenant}}]}


def counts_by_tenant(tenants, name=settings.COLLECTION):
    return {t: count(tenant_filter(t), name=name) for t in tenants}
