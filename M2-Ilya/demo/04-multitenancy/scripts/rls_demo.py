"""pgvector + Row Level Security: the database, not the app code, enforces the tenant."""
import psycopg

from app import pg
from app.embeddings import embed_query

Q = "What are the support hours?"
vec = pg.vec_literal(embed_query(Q))
SEARCH = "SELECT tenant_id, doc_id, section FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s"


def step(title):
    print(f"\n-- {title}")


step("1. superuser (postgres): RLS does not apply to superusers / BYPASSRLS roles")
with pg.admin_conn() as conn, conn.cursor() as cur:
    cur.execute("SELECT tenant_id, count(*) FROM chunks GROUP BY 1 ORDER BY 1")
    print(f"   SELECT tenant_id, count(*) ... -> {cur.fetchall()}")
    cur.execute("SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname IN ('postgres','app_user') ORDER BY 1")
    print(f"   roles: {cur.fetchall()}")

step("2. app_user, app.tenant NOT set: fail closed")
with pg.app_conn() as conn, conn.cursor() as cur:
    cur.execute("SELECT count(*) FROM chunks")
    print(f"   SELECT count(*) FROM chunks -> {cur.fetchone()[0]}")

step("3. app_user, SET LOCAL app.tenant='acme', app.groups='all'")
with pg.app_conn() as conn, conn.cursor() as cur:
    pg.set_tenant(cur, "acme", ["all"])
    cur.execute("SELECT tenant_id, count(*) FROM chunks GROUP BY 1")
    print(f"   SELECT tenant_id, count(*) FROM chunks GROUP BY 1      -> {cur.fetchall()}  (no WHERE)")
    cur.execute("SELECT count(*) FROM chunks WHERE tenant_id = 'globex'")
    print(f"   SELECT count(*) FROM chunks WHERE tenant_id = 'globex' -> {cur.fetchone()[0]}")
    cur.execute("SELECT count(*) FROM chunks WHERE 'finance' = ANY(groups)")
    print(f"   finance-only rows visible to a support user             -> {cur.fetchone()[0]}")
    cur.execute(SEARCH, (vec, 5))
    print(f"   vector search '{Q}' LIMIT 5, no WHERE:")
    for r in cur.fetchall():
        print(f"     {r[0]}/{r[1]} / {r[2]}")

step("4. app_user as acme tries to INSERT a row for globex")
with pg.app_conn() as conn, conn.cursor() as cur:
    pg.set_tenant(cur, "acme", ["all"])
    try:
        cur.execute("INSERT INTO chunks SELECT gen_random_uuid(), 'globex', groups, doc_id, title, section, text, embedding "
                    "FROM chunks LIMIT 1")
        print("   inserted (unexpected)")
    except psycopg.Error as e:
        print(f"   {type(e).__name__}: {str(e).strip().splitlines()[0]}")

def plan(cur, k):
    cur.execute("EXPLAIN (COSTS OFF) " + SEARCH, (vec, k))
    lines = [r[0].strip().lstrip("-> ").strip() for r in cur.fetchall()]
    keep = [l.split(" on chunks")[0] for l in lines
            if l.startswith(("Index Scan", "Bitmap", "Sort", "Seq Scan", "Limit")) and not l.startswith("Sort Key")]
    return " -> ".join(keep)


step("5. RLS + HNSW: the policy is a filter applied AFTER the index scan -> fewer than k rows")
with pg.app_conn() as conn, conn.cursor() as cur:
    pg.set_tenant(cur, "acme", ["all"])
    print(f"   default plan: {plan(cur, 10)}")
    print("   (small table: the planner picks the tenant btree index + exact sort, no HNSW)")
    # Make the planner behave like on a big table: ORDER BY via the HNSW index.
    cur.execute("SET LOCAL enable_seqscan = off")
    cur.execute("SET LOCAL enable_bitmapscan = off")
    cur.execute("SET LOCAL enable_sort = off")
    cur.execute("SET LOCAL hnsw.ef_search = 10")  # default 40; small value makes the effect visible on 212 rows
    print(f"   forced plan : {plan(cur, 10)}")
    cur.execute(SEARCH, (vec, 10))
    print(f"   hnsw.ef_search=10, iterative_scan=off          LIMIT 10 -> {len(cur.fetchall())} rows")
    cur.execute("SET LOCAL hnsw.iterative_scan = strict_order")
    cur.execute(SEARCH, (vec, 10))
    print(f"   hnsw.ef_search=10, iterative_scan=strict_order LIMIT 10 -> {len(cur.fetchall())} rows")
