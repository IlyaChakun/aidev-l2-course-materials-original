"""Tiered multitenancy (Qdrant >= 1.16): small tenants share a fallback shard,
a big tenant is promoted to its own dedicated shard without downtime.

Requires distributed mode (here: a one-peer cluster, see docker-compose.yml).
Points are copied from kb_shared, so no new embeddings are needed.
"""
import json
import time

from app import embeddings, qdrant, settings

C = settings.TIERED_COLLECTION
BIG = "globex"


def show(title, body=None):
    print(f"\n-- {title}")
    if body is not None:
        print("   " + json.dumps(body))


def shards():
    info = qdrant.call("GET", f"/collections/{C}/cluster")
    for s in info["local_shards"]:
        print(f"   shard_key={s['shard_key']!s:8} points={s['points_count']:4} state={s['state']}")


def scroll_all():
    pts, offset = [], None
    while True:
        body = {"limit": 256, "with_payload": True, "with_vector": ["dense"]}
        if offset is not None:
            body["offset"] = offset
        res = qdrant.call("POST", f"/collections/{settings.COLLECTION}/points/scroll", json=body)
        pts.extend(res["points"])
        offset = res.get("next_page_offset")
        if offset is None:
            return pts


qdrant.call("DELETE", f"/collections/{C}", ok404=True)

body = {"vectors": {"dense": {"size": settings.EMBED_DIM, "distance": "Cosine"}},
        "shard_number": 1, "sharding_method": "custom"}
show(f"1. PUT /collections/{C}", body)
qdrant.call("PUT", f"/collections/{C}", json=body)
qdrant.call("PUT", f"/collections/{C}/index", params={"wait": "true"},
            json={"field_name": "tenant_id", "field_schema": {"type": "keyword", "is_tenant": True}})

body = {"shard_key": "default", "shards_number": 1}
show(f"2. PUT /collections/{C}/shards  (fallback shard for all small tenants)", body)
qdrant.call("PUT", f"/collections/{C}/shards", json=body)

show("3. upsert every tenant with shard_key {target: <tenant>, fallback: default}")
by_tenant = {}
for p in scroll_all():
    by_tenant.setdefault(p["payload"]["tenant_id"], []).append(
        {"id": p["id"], "payload": p["payload"], "vector": p["vector"]})
for tenant, pts in sorted(by_tenant.items()):
    qdrant.upsert(pts, name=C, shard_key={"target": tenant, "fallback": "default"})
    print(f"   {tenant}: {len(pts)} points -> no shard '{tenant}' yet, so they go to 'default'")
shards()

body = {"shard_key": BIG, "shards_number": 1, "replication_factor": 1, "initial_state": "Partial"}
show(f"4. promote '{BIG}': PUT /collections/{C}/shards", body)
qdrant.call("PUT", f"/collections/{C}/shards", json=body)
shards()

body = {"replicate_points": {"filter": {"must": {"key": "tenant_id", "match": {"value": BIG}}},
                             "from_shard_key": "default", "to_shard_key": BIG}}
show(f"5. POST /collections/{C}/cluster", body)
qdrant.call("POST", f"/collections/{C}/cluster", json=body)
for _ in range(60):
    info = qdrant.call("GET", f"/collections/{C}/cluster")
    if all(s["state"] == "Active" for s in info["local_shards"]) and not info["shard_transfers"]:
        break
    time.sleep(0.5)
shards()
print(f"   total exact count (no shard_key): {qdrant.count(name=C)}  <- '{BIG}' is now in BOTH shards")

body = {"filter": qdrant.tenant_filter(BIG), "shard_key": "default"}
show(f"6. clean up the copy in the fallback: POST /collections/{C}/points/delete", body)
qdrant.delete_by_filter(qdrant.tenant_filter(BIG), name=C, shard_key="default")
shards()
print(f"   total exact count: {qdrant.count(name=C)}")

show("7. the same query code for every tenant: shard_key {target: tenant, fallback: default} + tenant filter")
vec = embeddings.embed_query("What are the support hours?")
for tenant in ("acme", BIG):
    body = {"query": vec, "using": "dense", "limit": 3, "with_payload": ["tenant_id", "doc_id"],
            "filter": qdrant.tenant_filter(tenant),
            "shard_key": {"target": tenant, "fallback": "default"}}
    hits = qdrant.query(body, name=C)
    print(f"   {tenant:7} -> " + ", ".join(f"{h['payload']['tenant_id']}/{h['payload']['doc_id']} (shard {h.get('shard_key')})" for h in hits))
