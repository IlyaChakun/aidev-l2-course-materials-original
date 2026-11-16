"""Lecture demo M2: PostgreSQL + pgvector vs Qdrant on the same chunks and embeddings.

Usage: python demo.py {load,step1,step2,step3,step4,step5,step6,all}
"""

from __future__ import annotations

import json
import re
import sys
import time
import uuid

import numpy as np
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table

from common import (
    COLL, COLL_BIG, DIM, EMBED_MODEL, FILTER_TENANTS, N_TENANTS, ROOT, UUID_NS,
    Qdrant, console, embed, embed_one, golden, load_corpus, ntokens, pg, read_doc,
    short, CORPUS_DIR,
)

OUT = ROOT / "data" / "out"
K = 5

# Which plans may see which document; internal support docs get no rows at all.
INTERNAL = {"reply-style-guide.md", "complaints-handling-procedure.md", "escalation-and-routing-policy.md"}
ACCESS_OVERRIDE = {
    "enterprise-contracts-and-discounts.md": ["business"],
    "security-and-compliance.md": ["business"],
    "integrations-and-api.md": ["team", "business"],
}


def header(title: str, subtitle: str = "") -> None:
    console.print()
    console.print(Rule(f"[bold]{title}[/]"))
    if subtitle:
        console.print(f"[dim]{subtitle}[/]")


def show_sql(sql: str) -> None:
    console.print(Syntax(sql.strip(), "sql", theme="ansi_dark", word_wrap=True))


def clean_plan(rows) -> str:
    """EXPLAIN inlines the 1536-number query vector; hide it."""
    return "\n".join(re.sub(r"'\[[^\]]{40,}\]'(::vector)?", "'[1536 numbers]'", r[0]) for r in rows)


def qdrant_bm25(text: str) -> dict:
    # Server-side inference: Qdrant turns text into a sparse BM25 vector itself.
    return {"text": text, "model": "Qdrant/bm25"}


# ------------------------------------------------------------------ load ----

PRICE_QUESTION = "How much does the Team plan cost per month?"
API_QUESTION = "How do I create an API key and what are the API rate limits?"


def updated_pricing_chunks():
    """Step 3: the pricing doc with the Team price changed from $59 to $69."""
    src = "plans-and-pricing.md"
    _, body = read_doc(CORPUS_DIR / src)
    new_chunks, _ = load_corpus(override={src: body.replace("$59", "$69")})
    return [c for c in new_chunks if c.source == src]


def prewarm_queries() -> None:
    """Embed every fixed query of steps 2-5 now, so the lecture runs from the cache without a key."""
    texts = [g["question"] for g in golden()] + [PRICE_QUESTION, API_QUESTION]
    texts += [c.embed_text for c in updated_pricing_chunks()]
    embed(texts)

def cmd_load() -> None:
    header("load: corpus → chunks → embeddings → Postgres and Qdrant")
    t0 = time.time()
    chunks, titles = load_corpus()
    toks = [ntokens(c.content) for c in chunks]
    console.print(
        f"Corpus: {len(titles)} documents → {len(chunks)} chunks by headings "
        f"(at most 400 tokens, {sum(toks) / len(toks):.0f} on average, maximum {max(toks)})"
    )
    vecs = embed([c.embed_text for c in chunks])
    prewarm_queries()
    console.print(f"Embeddings: {vecs.shape[0]} × {vecs.shape[1]}, model {EMBED_MODEL}, cache data/cache/embeddings.json")
    stats = {"chunks": len(chunks)}

    # ---- Postgres
    conn = pg()
    conn.execute((ROOT / "sql" / "schema.sql").read_text())
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO docs (source, title) VALUES (%s, %s)", list(titles.items()))
        access = []
        for src in titles:
            if src in INTERNAL:
                continue
            for plan in ACCESS_OVERRIDE.get(src, ["starter", "team", "business"]):
                access.append((src, plan))
        cur.executemany("INSERT INTO docs_access (source, plan) VALUES (%s, %s)", access)
        with cur.copy("COPY chunks (id, source, section, content, embedding) FROM STDIN WITH (FORMAT BINARY)") as cp:
            cp.set_types(["uuid", "text", "text", "text", "vector"])
            for c, v in zip(chunks, vecs):
                cp.write_row([uuid.UUID(c.id), c.source, c.section, c.content, v])

        # Synthetic rows: every chunk copied for N_TENANTS tenants. Each copy is blended with a random
        # other chunk (weight 0.3-0.6) plus small noise: copies stay close to the original but are not
        # near-duplicates (60 identical vectors per chunk would make a degenerate HNSW graph).
        rng = np.random.default_rng(42)
        big_ids, big_meta, big_vecs = [], [], []
        with cur.copy("COPY chunks_big (id, source, section, content, tenant, embedding) FROM STDIN WITH (FORMAT BINARY)") as cp:
            cp.set_types(["uuid", "text", "text", "text", "text", "vector"])
            for t in range(N_TENANTS):
                tenant = f"tenant-{t:03d}"
                other = vecs[rng.integers(0, len(vecs), size=len(vecs))]
                w = rng.uniform(0.3, 0.6, size=(len(vecs), 1)).astype(np.float32)
                noise = rng.normal(0, 0.008, size=vecs.shape).astype(np.float32)
                nv = vecs + w * other + noise
                nv /= np.linalg.norm(nv, axis=1, keepdims=True)
                for c, v in zip(chunks, nv):
                    bid = uuid.uuid5(UUID_NS, f"{tenant}/{c.id}")
                    cp.write_row([bid, c.source, c.section, c.content, tenant, v])
                    big_ids.append(str(bid))
                    big_meta.append((c.source, c.section, tenant))
                    big_vecs.append(v)
        stats["chunks_big"] = len(big_ids)
    console.print(f"Postgres: chunks = {len(chunks)} rows, chunks_big = {stats['chunks_big']} rows "
                  f"({N_TENANTS} synthetic tenants × {len(chunks)} chunks, copies blended with a random chunk and noise)")

    t1 = time.time()
    conn.execute("SET maintenance_work_mem = '512MB'")
    for stmt in (ROOT / "sql" / "indexes.sql").read_text().split(";"):
        body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
        if body:
            ts = time.time()
            conn.execute(body)
            if "chunks_big_embedding_hnsw" in body:
                stats["pg_hnsw_big_build_s"] = round(time.time() - ts, 1)
    stats["pg_index_total_s"] = round(time.time() - t1, 1)
    console.print(f"Postgres: HNSW + GIN built in {stats['pg_index_total_s']} s "
                  f"(HNSW on chunks_big: {stats['pg_hnsw_big_build_s']} s)")

    # ---- Qdrant
    q = Qdrant()
    for coll in (COLL, COLL_BIG):
        q.http.delete(f"/collections/{coll}")
    q.req("PUT", f"/collections/{COLL}", {
        "vectors": {"size": DIM, "distance": "Cosine"},
        "sparse_vectors": {"bm25": {"modifier": "idf"}},
        "metadata": {"embedding_model": EMBED_MODEL},
    })
    q.req("PUT", f"/collections/{COLL}/index", {"field_name": "metadata.source", "field_schema": "keyword"})
    points = [{
        "id": c.id,
        "vector": {"": v.tolist(), "bm25": qdrant_bm25(c.content)},
        "payload": {"content": c.content, "metadata": {"source": c.source, "section": c.section, "tenant": "lumen"}},
    } for c, v in zip(chunks, vecs)]
    for i in range(0, len(points), 128):
        q.req("PUT", f"/collections/{COLL}/points?wait=true", {"points": points[i : i + 128]})

    # full_scan_threshold is lowered on purpose: with the default (10000 KB) a 5 percent filter
    # (~1K points, ~6 MB) is answered by exact scan over the payload index, and we want to see
    # the filterable HNSW graph itself.
    q.req("PUT", f"/collections/{COLL_BIG}", {
        "vectors": {"size": DIM, "distance": "Cosine"},
        "hnsw_config": {"full_scan_threshold": 10},
    })
    # Payload index BEFORE the upload, so HNSW is built filter-aware.
    q.req("PUT", f"/collections/{COLL_BIG}/index", {
        "field_name": "metadata.tenant", "field_schema": {"type": "keyword", "is_tenant": True}})
    ts = time.time()
    batch = 256
    for i in range(0, len(big_ids), batch):
        pts = [{
            "id": big_ids[j],
            "vector": [round(float(x), 6) for x in big_vecs[j]],
            "payload": {"metadata": {"source": big_meta[j][0], "section": big_meta[j][1], "tenant": big_meta[j][2]}},
        } for j in range(i, min(i + batch, len(big_ids)))]
        q.req("PUT", f"/collections/{COLL_BIG}/points?wait=true", {"points": pts})
    info = q.wait_green(COLL_BIG)
    stats["qdrant_big_upload_and_index_s"] = round(time.time() - ts, 1)
    q.wait_green(COLL)
    console.print(f"Qdrant: {COLL} = {len(points)} points (dense + bm25), {COLL_BIG} = {info['points_count']} points, "
                  f"upload and indexing {stats['qdrant_big_upload_and_index_s']} s")

    OUT.mkdir(parents=True, exist_ok=True)
    stats["total_s"] = round(time.time() - t0, 1)
    (OUT / "load_stats.json").write_text(json.dumps(stats, indent=2))
    console.print(f"[green]Done in {stats['total_s']} s[/]")


# ---------------------------------------------------------------- step 1 ----

def cmd_step1() -> None:
    header("Step 1. The same data in two places",
           "The same chunks and the same text-embedding-3-small vectors: the only difference is the storage")
    conn = pg()
    show_sql(r"\d chunks  -- simplified")
    cols = conn.execute("""
        SELECT a.attname, format_type(a.atttypid, a.atttypmod),
               CASE WHEN a.attgenerated = 's' THEN 'generated' ELSE '' END
        FROM pg_attribute a WHERE a.attrelid = 'chunks'::regclass AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum""").fetchall()
    t = Table("column", "type", "how it is filled", title="Postgres: chunks table")
    for c in cols:
        t.add_row(*c)
    console.print(t)
    idx = conn.execute("""
        SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass)), indexdef
        FROM pg_indexes WHERE tablename IN ('chunks', 'chunks_big') ORDER BY indexname""").fetchall()
    t = Table("index", "size", "definition", title="Postgres: indexes")
    for name, size, d in idx:
        t.add_row(name, size, d.split(" USING ", 1)[-1])
    console.print(t)
    counts = conn.execute("SELECT (SELECT count(*) FROM chunks), (SELECT count(*) FROM chunks_big), "
                          "(SELECT count(*) FROM docs), (SELECT count(*) FROM docs_access)").fetchone()

    q = Qdrant()
    info = q.req("GET", f"/collections/{COLL}")["result"]
    info_big = q.req("GET", f"/collections/{COLL_BIG}")["result"]
    t = Table("what", "Postgres", "Qdrant", title="How much is stored and how")
    t.add_row("real chunks", f"chunks: {counts[0]}", f"{COLL}: {info['points_count']}")
    t.add_row("synthetic data for step 4", f"chunks_big: {counts[1]}", f"{COLL_BIG}: {info_big['points_count']}")
    t.add_row("dense", "embedding vector(1536), HNSW vector_cosine_ops", "unnamed vector 1536, Cosine")
    t.add_row("lexical", "tsv tsvector (generated) + GIN", "named sparse bm25, modifier idf, Qdrant/bm25 on the server")
    t.add_row("metadata", "columns + tables docs, docs_access", "payload: content, metadata.{source,section,tenant}")
    t.add_row("business tables", f"docs: {counts[2]}, docs_access: {counts[3]}", "none, payload only")
    console.print(t)
    stats = OUT / "load_stats.json"
    if stats.exists():
        console.print(f"[dim]load_stats.json: {stats.read_text().strip()}[/]")


# ---------------------------------------------------------------- step 2 ----

DENSE_SQL = """
SELECT source, section, 1 - (embedding <=> %(q)s) AS cosine
FROM chunks
ORDER BY embedding <=> %(q)s
LIMIT 5;"""


def cmd_step2(question: str | None = None) -> None:
    question = question or golden("core")[2]["question"]
    header("Step 2. The same dense query in both systems", f"Question: {question}")
    qv = embed_one(question)
    conn = pg()
    show_sql(DENSE_SQL)
    pg_rows = conn.execute(DENSE_SQL, {"q": qv}).fetchall()
    console.print(Syntax(json.dumps({"query": "[1536 numbers]", "limit": 5, "with_payload": True}, ensure_ascii=False),
                         "json", theme="ansi_dark"))
    qd = Qdrant().query(COLL, {"query": qv.tolist(), "limit": K, "with_payload": True})

    t = Table("#", "Postgres: source / section", "cosine", "Qdrant: source / section", "score",
              title="Top-5 in both systems")
    for i in range(K):
        p, d = pg_rows[i], qd[i]
        same = (p[0], p[1]) == (d["payload"]["metadata"]["source"], d["payload"]["metadata"]["section"])
        style = "" if same else "yellow"
        t.add_row(str(i + 1), f"{p[0]} / {short(p[1], 32)}", f"{p[2]:.4f}",
                  f"{d['payload']['metadata']['source']} / {short(d['payload']['metadata']['section'], 32)}",
                  f"{d['score']:.4f}", style=style)
    console.print(t)
    overlap = len({(r[0], r[1]) for r in pg_rows} & {(d["payload"]["metadata"]["source"], d["payload"]["metadata"]["section"]) for d in qd})
    console.print(f"Chunks matching in the top-5: [bold]{overlap} of 5[/]. "
                  "Cosine in Postgres = 1 - the `<=>` distance; the Qdrant score with Cosine is the same cosine.")

    for table in ("chunks", "chunks_big"):
        plan_sql = f"EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, BUFFERS OFF, SUMMARY ON)\nSELECT id FROM {table} ORDER BY embedding <=> %(q)s LIMIT 5"
        plan = clean_plan(conn.execute(plan_sql, {"q": qv}).fetchall())
        n = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        console.print(Panel(plan, title=f"EXPLAIN on {table} ({n} rows)", expand=False))
    console.print("[dim]If a small table shows Seq Scan + Sort: it is cheaper for the planner to scan everything. "
                  "The index kicks in by itself once there are many rows (chunks_big).[/]")


# ---------------------------------------------------------------- step 3 ----

JOIN_SQL = """
SELECT c.source, c.section, d.version, 1 - (c.embedding <=> %(q)s) AS cosine
FROM chunks c
JOIN docs d        ON d.source = c.source
JOIN docs_access a ON a.source = c.source AND a.plan = %(plan)s
ORDER BY c.embedding <=> %(q)s
LIMIT 5;"""

UPDATE_TX = """
BEGIN;
  UPDATE docs SET version = version + 1, updated_at = now() WHERE source = 'plans-and-pricing.md';
  DELETE FROM chunks WHERE source = 'plans-and-pricing.md';
  INSERT INTO chunks (...) VALUES (...);   -- new chunks and new vectors
COMMIT;   -- or ROLLBACK: then nothing changes"""


def _replace_doc(conn, new_chunks, new_vecs, fail: bool) -> None:
    src = "plans-and-pricing.md"
    with conn.transaction():
        conn.execute("UPDATE docs SET version = version + 1, updated_at = now() WHERE source = %s", (src,))
        conn.execute("DELETE FROM chunks WHERE source = %s", (src,))
        if fail:
            raise RuntimeError("failure in the middle of the update (simulated)")
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (id, source, section, content, embedding) VALUES (%s, %s, %s, %s, %s)",
                [(c.id, c.source, c.section, c.content, v) for c, v in zip(new_chunks, new_vecs)])


def _doc_state(conn) -> str:
    v, n, has69 = conn.execute("""
        SELECT d.version, count(c.id), bool_or(c.content LIKE '%$69%')
        FROM docs d LEFT JOIN chunks c ON c.source = d.source
        WHERE d.source = 'plans-and-pricing.md' GROUP BY d.version""").fetchone()
    return f"docs.version = {v}, chunks = {n}, Team price in the text = {'$69' if has69 else '$59'}"


def cmd_step3() -> None:
    header("Step 3. Where Postgres is stronger: a transaction and a JOIN with business tables")
    conn = pg()
    src = "plans-and-pricing.md"

    console.print("[bold]3a. The document changed: the Team price $59 → $69. Metadata and chunks change in one transaction.[/]")
    show_sql(UPDATE_TX)
    new_chunks = updated_pricing_chunks()
    new_vecs = embed([c.embed_text for c in new_chunks])
    console.print(f"Before:             {_doc_state(conn)}")
    try:
        _replace_doc(conn, new_chunks, new_vecs, fail=True)
    except RuntimeError as e:
        console.print(f"[yellow]Failure after DELETE: {e} → ROLLBACK[/]")
    console.print(f"After the failure:  {_doc_state(conn)}  [dim](nothing was lost)[/]")
    _replace_doc(conn, new_chunks, new_vecs, fail=False)
    console.print(f"After COMMIT:      {_doc_state(conn)}")
    qv = embed_one(PRICE_QUESTION)
    rows = conn.execute("SELECT section, content FROM chunks ORDER BY embedding <=> %s LIMIT 3", (qv,)).fetchall()
    price_lines = [l.strip() for _, content in rows for l in content.splitlines() if "Team" in l and "$" in l]
    console.print(f"Search \"{PRICE_QUESTION}\" immediately sees the new version, a line from the top-3: "
                  f"[bold]{price_lines[0] if price_lines else short(rows[0][1], 100)}[/]")
    console.print("[dim]In Qdrant the same thing is two separate calls (delete by filter + upsert) without a shared transaction: "
                  "in between, search sees the document without chunks or with a mix of versions.[/]")

    console.print()
    console.print("[bold]3b. Access rights are a plain JOIN with the docs_access table, before LIMIT, in the same query.[/]")
    show_sql(JOIN_SQL)
    question = API_QUESTION
    qv = embed_one(question)
    console.print(f"Question: {question}")
    for plan in ("starter", "business"):
        rows = conn.execute(JOIN_SQL, {"q": qv, "plan": plan}).fetchall()
        t = Table("source", "section", "version", "cosine", title=f"plan = '{plan}'")
        for r in rows:
            t.add_row(r[0], short(r[1], 40), str(r[2]), f"{r[3]:.4f}")
        console.print(t)
    console.print("[dim]Starter does not see integrations-and-api.md (team and business only), and nobody sees the internal support "
                  "procedures. In Qdrant the rights would have to be copied into the payload of every point "
                  "and re-synchronized on every plan change.[/]")

    # Put the original version back so the demo can be re-run.
    orig_chunks, _ = load_corpus()
    orig_chunks = [c for c in orig_chunks if c.source == src]
    _replace_doc(conn, orig_chunks, embed([c.embed_text for c in orig_chunks]), fail=False)
    conn.execute("UPDATE docs SET version = 1 WHERE source = %s", (src,))
    console.print(f"[dim]Restored the original version so the demo can be re-run: {_doc_state(conn)}[/]")


# ---------------------------------------------------------------- step 4 ----

FILTER_SQL = """
SELECT id, source, section, tenant
FROM chunks_big
WHERE tenant = ANY(%(tenants)s)          -- 3 tenants out of 60 = 5 percent of rows
ORDER BY embedding <=> %(q)s
LIMIT 5;"""

RELAXED_SQL = """
SET hnsw.iterative_scan = relaxed_order;   -- pgvector >= 0.8
-- relaxed_order may slightly break the order: re-sort outside
WITH hits AS MATERIALIZED (
  SELECT id, source, section, tenant, embedding <=> %(q)s AS dist
  FROM chunks_big WHERE tenant = ANY(%(tenants)s)
  ORDER BY dist LIMIT 5)
SELECT * FROM hits ORDER BY dist;"""

RELAXED_RUN = """
WITH hits AS MATERIALIZED (
  SELECT id, source, section, tenant, embedding <=> %(q)s AS dist
  FROM chunks_big WHERE tenant = ANY(%(tenants)s)
  ORDER BY dist LIMIT 5)
SELECT id, source, section, tenant FROM hits ORDER BY dist"""


def _pg_filtered(conn, qv, settings: dict[str, str], sql: str = FILTER_SQL) -> list:
    with conn.transaction():
        for k, v in settings.items():
            conn.execute(f"SET LOCAL {k} = {v}")
        return conn.execute(sql, {"q": qv, "tenants": FILTER_TENANTS}).fetchall()


# The planner of pgvector 0.8 picks Seq Scan for a 5 percent filter on 21K rows (cheap: ~12 ms).
# On millions of rows it picks the HNSW index; to show that behaviour here we switch Seq Scan off.
FORCE_INDEX = {"enable_seqscan": "off"}


def _explain(conn, qv, settings: dict[str, str]) -> str:
    with conn.transaction():
        for k, v in settings.items():
            conn.execute(f"SET LOCAL {k} = {v}")
        return clean_plan(conn.execute(
            "EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, BUFFERS OFF, SUMMARY ON) " + FILTER_SQL.split(";")[0],
            {"q": qv, "tenants": FILTER_TENANTS}).fetchall())


def cmd_step4() -> None:
    header("Step 4. Filter + HNSW: asked for 5, got fewer",
           f"chunks_big ({N_TENANTS} tenants × 349 chunks) and {COLL_BIG}; filter on {len(FILTER_TENANTS)} "
           "tenants = 5% of rows; k = 5")
    conn = pg()
    q = Qdrant()
    show_sql(FILTER_SQL)
    qs = golden("core")
    console.print(Panel(_explain(conn, embed_one(qs[0]["question"]), {"hnsw.iterative_scan": "off"}),
                        title="EXPLAIN first: what the planner chose by itself", expand=False))
    console.print("[dim]On 21K rows scanning 5% is cheaper than going into the index, and the result is exact. On millions of rows "
                  "the planner will pick HNSW. To see what happens then, we switch Seq Scan off from here on "
                  "(SET enable_seqscan = off).[/]")

    t = Table("question", "planner's own\n(Seq Scan)", "HNSW\nef_search=40", "HNSW\nef_search=200",
              "HNSW + iterative\nrelaxed_order", "relaxed ∩\nexact", "Qdrant\n+ payload index", "Qdrant ∩\nexact",
              title="How many rows came back out of the 5 requested")
    totals = np.zeros(7)
    example = None
    for g in qs:
        qv = embed_one(g["question"])
        exact = _pg_filtered(conn, qv, {"enable_indexscan": "off", "enable_bitmapscan": "off"})
        a = _pg_filtered(conn, qv, {**FORCE_INDEX, "hnsw.iterative_scan": "off"})
        b = _pg_filtered(conn, qv, {**FORCE_INDEX, "hnsw.iterative_scan": "off", "hnsw.ef_search": "200"})
        c = _pg_filtered(conn, qv, {**FORCE_INDEX, "hnsw.iterative_scan": "relaxed_order"}, RELAXED_RUN)
        qd = q.query(COLL_BIG, {
            "query": qv.tolist(), "limit": K, "with_payload": False,
            "filter": {"must": [{"key": "metadata.tenant", "match": {"any": FILTER_TENANTS}}]},
        })
        exact_ids = {str(r[0]) for r in exact}
        row = [len(exact), len(a), len(b), len(c), len(exact_ids & {str(r[0]) for r in c}),
               len(qd), len(exact_ids & {p["id"] for p in qd})]
        totals += row
        t.add_row(g["id"], *[str(x) for x in row], style="" if len(a) == K else "yellow")
        if example is None and 0 < len(a) < K:
            example = (g["id"], qv)
    n = len(qs)
    t.add_row("[bold]average[/]", *[f"[bold]{x / n:.1f}[/]" for x in totals])
    console.print(t)

    qid, qv = example or (qs[0]["id"], embed_one(qs[0]["question"]))
    for title, settings in (("HNSW, iterative_scan = off", {**FORCE_INDEX, "hnsw.iterative_scan": "off"}),
                            ("HNSW, iterative_scan = relaxed_order", {**FORCE_INDEX, "hnsw.iterative_scan": "relaxed_order"})):
        console.print(Panel(_explain(conn, qv, settings), title=f"EXPLAIN ({qid}), {title}", expand=False))
    console.print("How it is fixed in Postgres:")
    show_sql(RELAXED_SQL)
    console.print("[dim]HNSW in pgvector returns ef_search candidates (40), WHERE is applied afterwards: of the 40 nearest, "
                  "only a few belong to the right tenants. ef_search=200 also helps here, but it is more expensive on every query "
                  "and will not help with a 1% filter. "
                  "iterative_scan keeps walking the graph until it collects LIMIT rows (capped by hnsw.max_scan_tuples). "
                  "Qdrant filters during graph traversal (filterable HNSW, payload index with is_tenant).[/]")


# ---------------------------------------------------------------- step 5 ----

PG_DENSE = "SELECT source FROM chunks ORDER BY embedding <=> %(q)s LIMIT %(k)s"
PG_LEX_AND = """
SELECT source FROM chunks, websearch_to_tsquery('english', %(text)s) query
WHERE tsv @@ query ORDER BY ts_rank_cd(tsv, query) DESC LIMIT %(k)s"""
# websearch_to_tsquery ANDs every word; for a natural-language question we OR the lexemes.
OR_QUERY = "to_tsquery('english', replace(websearch_to_tsquery('english', %(text)s)::text, ' & ', ' | '))"
PG_LEX_OR = f"""
SELECT source FROM chunks, {OR_QUERY} query
WHERE tsv @@ query ORDER BY ts_rank_cd(tsv, query) DESC LIMIT %(k)s"""
PG_HYBRID = f"""
WITH dense AS (
  SELECT id, row_number() OVER (ORDER BY embedding <=> %(q)s) AS rnk
  FROM chunks ORDER BY embedding <=> %(q)s LIMIT 20
), lexical AS (
  SELECT id, row_number() OVER (ORDER BY ts_rank_cd(tsv, query) DESC) AS rnk
  FROM chunks, {OR_QUERY} query
  WHERE tsv @@ query ORDER BY ts_rank_cd(tsv, query) DESC LIMIT 20
), fused AS (
  SELECT id, sum(1.0 / (60 + rnk)) AS rrf     -- RRF, k = 60
  FROM (SELECT * FROM dense UNION ALL SELECT * FROM lexical) u
  GROUP BY id
)
SELECT c.source FROM fused JOIN chunks c USING (id)
ORDER BY rrf DESC LIMIT %(k)s"""


def _recall(sources: list[str], answer_docs: list[str]) -> float:
    return len(set(sources) & set(answer_docs)) / len(answer_docs)


def cmd_step5() -> None:
    header("Step 5. Hybrid: Postgres FTS + vector via RRF in SQL vs Qdrant prefetch + rrf",
           "recall@5 = the share of the needed documents among the sources of the top-5 chunks")
    conn = pg()
    q = Qdrant()
    console.print("Postgres, hybrid in a single SQL query:")
    show_sql(PG_HYBRID)
    body = {"prefetch": [{"query": "<dense>", "limit": 20},
                         {"query": {"text": "<question>", "model": "Qdrant/bm25"}, "using": "bm25", "limit": 20}],
            "query": {"fusion": "rrf"}, "limit": 5, "with_payload": True}
    console.print("Qdrant, hybrid in a single /points/query request:")
    console.print(Syntax(json.dumps(body, ensure_ascii=False), "json", theme="ansi_dark", word_wrap=True))

    def qd_sources(b: dict) -> list[str]:
        return [p["payload"]["metadata"]["source"] for p in q.query(COLL, {**b, "limit": K, "with_payload": True})]

    methods = ["PG dense", "PG lexical AND", "PG lexical OR", "PG hybrid RRF k=60",
               "QD dense", "QD bm25", "QD hybrid rrf (default)", "QD hybrid rrf k=60"]
    results: dict[str, dict[str, list[float]]] = {}
    top_scores, top_scores_60 = [], []
    for kind in ("core", "multi"):
        res = {m: [] for m in methods}
        for g in golden(kind):
            text, qv = g["question"], embed_one(g["question"])
            p = {"q": qv, "text": text, "k": K}
            dense_pf = {"query": qv.tolist(), "limit": 20}
            bm25_pf = {"query": qdrant_bm25(text), "using": "bm25", "limit": 20}
            runs = {
                "PG dense": [r[0] for r in conn.execute(PG_DENSE, p)],
                "PG lexical AND": [r[0] for r in conn.execute(PG_LEX_AND, p)],
                "PG lexical OR": [r[0] for r in conn.execute(PG_LEX_OR, p)],
                "PG hybrid RRF k=60": [r[0] for r in conn.execute(PG_HYBRID, p)],
                "QD dense": qd_sources({"query": qv.tolist()}),
                "QD bm25": qd_sources({"query": qdrant_bm25(text), "using": "bm25"}),
                "QD hybrid rrf (default)": qd_sources({"prefetch": [dense_pf, bm25_pf], "query": {"fusion": "rrf"}}),
                "QD hybrid rrf k=60": qd_sources({"prefetch": [dense_pf, bm25_pf], "query": {"rrf": {"k": 60}}}),
            }
            for m, srcs in runs.items():
                res[m].append(_recall(srcs, g["answer_docs"]))
            if kind == "core":
                top = q.query(COLL, {"prefetch": [dense_pf, bm25_pf], "query": {"fusion": "rrf"}, "limit": 1})
                top_scores.append(top[0]["score"])
                top = q.query(COLL, {"prefetch": [dense_pf, bm25_pf], "query": {"rrf": {"k": 60}}, "limit": 1})
                top_scores_60.append(top[0]["score"])
        results[kind] = res

    t = Table("method", f"core (n={len(golden('core'))})", f"multi (n={len(golden('multi'))})",
              title="recall@5 on the golden set (core and multi; traps are not counted)")
    for m in methods:
        t.add_row(m, f"{np.mean(results['core'][m]):.2f}", f"{np.mean(results['multi'][m]):.2f}",
                  style="cyan" if m.startswith("QD") else "")
    console.print(t)
    console.print(f"Qdrant RRF, maximum score on core (the document is first in both branches): "
                  f"default k → [bold]{max(top_scores):.4f}[/], k=60 → [bold]{max(top_scores_60):.4f}[/]. "
                  "For comparison: 2/(k+1) at k=2 = 0.6667, at k=60 = 0.0328; 2/k at k=2 = 1.0, at k=60 = 0.0333.")
    console.print("[dim]PG lexical AND: websearch_to_tsquery requires all the words of the question - on real questions it is almost "
                  "always empty. That is why the lexemes are joined with OR in the hybrid. In Qdrant, BM25 is \"OR-like\" by default.[/]")


# ---------------------------------------------------------------- step 6 ----

def cmd_step6() -> None:
    header("Step 6. Operations: what people step on")
    conn = pg()
    checks = {}
    with conn.transaction(force_rollback=True):
        conn.execute("CREATE TEMP TABLE big_dims (e vector(3072), h halfvec(3072))")
        try:
            with conn.transaction():
                conn.execute("CREATE INDEX ON big_dims USING hnsw (e vector_cosine_ops)")
            checks["vector3072"] = "created (unexpected)"
        except Exception as e:  # noqa: BLE001 - we print the server message as is
            checks["vector3072"] = str(e).splitlines()[0]
        conn.execute("CREATE INDEX ON big_dims USING hnsw (h halfvec_cosine_ops)")
        checks["halfvec3072"] = "index created"
    mwm = conn.execute("SHOW maintenance_work_mem").fetchone()[0]
    pmw = conn.execute("SHOW max_parallel_maintenance_workers").fetchone()[0]
    ver = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()[0]
    pgver = conn.execute("SHOW server_version").fetchone()[0]
    idx = conn.execute("SELECT pg_size_pretty(pg_relation_size('chunks_big_embedding_hnsw')), "
                       "pg_size_pretty(pg_total_relation_size('chunks_big')), "
                       "pg_size_pretty(pg_database_size(current_database()))").fetchone()
    stats = json.loads((OUT / "load_stats.json").read_text()) if (OUT / "load_stats.json").exists() else {}

    q = Qdrant()
    snap = q.req("POST", f"/collections/{COLL}/snapshots?wait=true")["result"]
    qver = q.req("GET", "/")["version"]

    t = Table("topic", "Postgres + pgvector", "Qdrant", "verified in this stand", title="Operational notes",
              show_lines=True)
    t.add_row("dimensions in the index",
              "vector: up to 2000 dimensions in HNSW/IVFFlat; halfvec: up to 4000; up to 16000 can be stored",
              "dense up to 65536 dimensions",
              f"vector(3072) + hnsw → \"{checks['vector3072']}\"; halfvec(3072) + hnsw → {checks['halfvec3072']}")
    t.add_row("HNSW build",
              "in maintenance_work_mem; if it does not fit → slow build with a NOTICE; build after loading",
              "in the background by the optimizer, collection yellow → green",
              f"maintenance_work_mem = {mwm}, parallel workers = {pmw}; HNSW on {stats.get('chunks_big', '?')} "
              f"rows: {stats.get('pg_hnsw_big_build_s', '?')} s, index {idx[0]}")
    t.add_row("Docker",
              "the parallel HNSW build uses /dev/shm: the default 64MB is too little → shm_size",
              "a volume for /qdrant/storage, a separate one for snapshots",
              "shm_size: 1g in docker-compose.yml")
    t.add_row("filters",
              "WHERE after the index; hnsw.iterative_scan (0.8+) or a partial index/partitions",
              "filterable HNSW, payload index before loading, is_tenant",
              "step 4")
    t.add_row("backup",
              "pg_dump / physical backup and PITR - together with the business data",
              "a collection snapshot via the API, separate from the rest of the data",
              f"make backup: pg_dump -Fc; Qdrant snapshot {snap['name']} ({snap['size'] / 1e6:.1f} MB)")
    t.add_row("versions in the stand", f"PostgreSQL {pgver}, pgvector {ver}", f"Qdrant {qver}",
              f"whole database {idx[2]}, chunks_big with indexes {idx[1]}")
    console.print(t)


# ------------------------------------------------------------------ main ----

COMMANDS = {
    "load": cmd_load, "step1": cmd_step1, "step2": cmd_step2, "step3": cmd_step3,
    "step4": cmd_step4, "step5": cmd_step5, "step6": cmd_step6,
}


def main(argv: list[str]) -> None:
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in (*COMMANDS, "all"):
        console.print(__doc__)
        return
    if argv[0] == "all":
        for name in ("step1", "step2", "step3", "step4", "step5", "step6"):
            COMMANDS[name]()
        return
    if argv[0] == "step2" and len(argv) > 1:
        cmd_step2(" ".join(argv[1:]))
        return
    COMMANDS[argv[0]]()


if __name__ == "__main__":
    main(sys.argv[1:])
