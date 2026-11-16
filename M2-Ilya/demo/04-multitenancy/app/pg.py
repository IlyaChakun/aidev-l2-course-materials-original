"""pgvector + RLS access. The app connects as app_user and sets the tenant per transaction."""
import psycopg

from app import settings


def vec_literal(v):
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"


def app_conn():
    return psycopg.connect(settings.PG_APP_DSN, autocommit=False)


def admin_conn():
    return psycopg.connect(settings.PG_ADMIN_DSN, autocommit=False)


def set_tenant(cur, tenant, groups):
    # is_local=true -> SET LOCAL: the value dies with the transaction,
    # so a pooled connection cannot carry tenant A's setting into tenant B's request.
    cur.execute("SELECT set_config('app.tenant', %s, true), set_config('app.groups', %s, true)",
                (tenant, ",".join(groups)))


def search(tenant, groups, vector, k=5):
    with app_conn() as conn, conn.cursor() as cur:
        set_tenant(cur, tenant, groups)
        # Note: no WHERE tenant_id = ... here. RLS adds it.
        cur.execute(
            "SELECT tenant_id, doc_id, section, groups, text, 1 - (embedding <=> %s::vector) AS score "
            "FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s",
            (vec_literal(vector), vec_literal(vector), k),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
