"""Build tenant corpora, embed (cached), load Qdrant (shared collection) and Postgres."""
import json
from collections import Counter

from app import corpus, pg, qdrant, settings, sparse
from app.embeddings import embed_texts


def main():
    corpus.build()
    chunks = corpus.all_chunks()
    print(f"chunks: {len(chunks)} {dict(Counter(c['tenant_id'] for c in chunks))}")

    vecs = embed_texts([c["text"] for c in chunks])
    demo = json.loads((settings.CONFIG_DIR / "demo_queries.json").read_text())
    probe = demo["probe_doc"]
    # Warm the cache so the lecture and the tests run offline (same strings the API embeds).
    embed_texts(demo["queries"] + [f"{probe['title']}\n\n{probe['text']}", probe["text"]])
    print(f"embeddings ready (cache: {settings.CACHE_DIR.relative_to(settings.ROOT)})")

    qdrant.create_shared_collection()
    points = []
    for c, v in zip(chunks, vecs):
        payload = {k: c[k] for k in ("tenant_id", "groups", "doc_id", "title", "section", "chunk", "text")}
        points.append({"id": c["id"], "payload": payload,
                       "vector": {"dense": v, "bm25": sparse.doc_vector(c["text"])}})
    # Ingestion is a trusted pipeline: tenant_id comes from the source folder, not from a user.
    qdrant.upsert(points)
    print(f"qdrant {settings.COLLECTION}: {qdrant.counts_by_tenant(corpus.load_tenants())}")

    with pg.admin_conn() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE chunks")
        with cur.copy("COPY chunks (id, tenant_id, groups, doc_id, title, section, text, embedding) FROM STDIN") as cp:
            for c, v in zip(chunks, vecs):
                cp.write_row((c["id"], c["tenant_id"], c["groups"], c["doc_id"], c["title"],
                              c["section"], c["text"], pg.vec_literal(v)))
        conn.commit()
        cur.execute("SELECT tenant_id, count(*) FROM chunks GROUP BY 1 ORDER BY 1")
        print(f"postgres chunks (as superuser): {dict(cur.fetchall())}")


if __name__ == "__main__":
    main()
