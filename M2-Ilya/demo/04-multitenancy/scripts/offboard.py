"""Offboard one tenant: delete its data from Qdrant (by filter) and Postgres (through RLS),
then verify counts. Usage: offboard.py <tenant>"""
import sys

from app import corpus, pg, qdrant, settings

tenant = sys.argv[1] if len(sys.argv) > 1 else "initech"
tenants = list(corpus.load_tenants())


def pg_counts():
    with pg.admin_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT tenant_id, count(*) FROM chunks GROUP BY 1 ORDER BY 1")
        return {t: n for t, n in cur.fetchall()}


def collections():
    names = [c["name"] for c in qdrant.call("GET", "/collections")["collections"]]
    return [c for c in (settings.COLLECTION, settings.TIERED_COLLECTION) if c in names]


print(f"== offboarding tenant '{tenant}' ==\n")
print("BEFORE")
for c in collections():
    print(f"  qdrant {c:10}: {qdrant.counts_by_tenant(tenants, name=c)}")
print(f"  postgres chunks : {pg_counts()}")

flt = qdrant.tenant_filter(tenant)
print(f"\nqdrant: POST /collections/<c>/points/delete {{'filter': {flt}}}")
for c in collections():
    if c == settings.TIERED_COLLECTION:
        # Custom sharding: a write must name a shard key; the tenant lives in its own shard
        # or in the fallback one. A promoted tenant would instead drop its whole shard key.
        qdrant.delete_by_filter(flt, name=c, shard_key={"target": tenant, "fallback": "default"})
    else:
        qdrant.delete_by_filter(flt, name=c)

print("postgres: as app_user, SET LOCAL app.tenant, then DELETE FROM chunks  (no WHERE: RLS scopes it)")
with pg.app_conn() as conn, conn.cursor() as cur:
    pg.set_tenant(cur, tenant, ["all"])
    cur.execute("DELETE FROM chunks")
    print(f"  rows deleted: {cur.rowcount}")
    conn.commit()

print("\nAFTER")
for c in collections():
    print(f"  qdrant {c:10}: {qdrant.counts_by_tenant(tenants, name=c)}")
print(f"  postgres chunks : {pg_counts()}")

print("""
NOT covered by this script (offboarding checklist):
  - embedding cache (data/cache) is keyed by text hash, not by tenant
  - Qdrant snapshots / Cloud backups and Postgres backups still contain the tenant
  - API logs, traces (prompts, retrieved chunks), eval datasets, LLM provider logs
  - deleted Qdrant points are only marked deleted until the vacuum optimizer runs
Restore the demo data with: make seed""")
