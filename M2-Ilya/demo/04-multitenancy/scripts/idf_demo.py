"""BM25 (sparse, modifier=idf) for an acme user: global IDF vs per-tenant IDF.

IDF is computed by Qdrant over the whole collection by default, so a word that is
everywhere in a NEIGHBOUR's documents looks "common" and loses weight for you.
Qdrant 1.19 adds params.idf.corpus: a filter that defines whose statistics to use.
"""
import argparse
import math

from app import corpus, qdrant, sparse

ap = argparse.ArgumentParser()
ap.add_argument("--tenant", default="acme")
ap.add_argument("--q", default="warehouse pallet")
a = ap.parse_args()

tflt = qdrant.tenant_filter(a.tenant)
terms = sorted(set(sparse.tokenize(a.q)))

# Document frequencies computed locally from the same chunks (BM25 idf formula),
# to show what IDF Qdrant sees with and without the tenant scope.
chunks = corpus.all_chunks()
def df_local(term, tenant=None):
    return sum(1 for c in chunks if (tenant is None or c["tenant_id"] == tenant)
               and term in sparse.tokenize(c["text"]))

N_all = len(chunks)
N_t = sum(1 for c in chunks if c["tenant_id"] == a.tenant)
print(f"query: '{a.q}'  tenant: {a.tenant}  points: all={N_all}, {a.tenant}={N_t}\n")
print(f"{'term':10} {'df all':>6} {'idf all':>8} {'df '+a.tenant:>8} {'idf '+a.tenant:>9}")
for t in terms:
    d_all, d_t = df_local(t), df_local(t, a.tenant)
    idf = lambda n, d: math.log((n - d + 0.5) / (d + 0.5) + 1)
    print(f"{t:10} {d_all:6} {idf(N_all, d_all):8.2f} {d_t:8} {idf(N_t, d_t):9.2f}")

base = {"query": sparse.query_vector(a.q), "using": "bm25", "filter": tflt, "limit": 3,
        "with_payload": ["tenant_id", "doc_id", "section"]}
runs = [
    ("global IDF (default)", dict(base)),
    ("per-tenant IDF: params.idf.corpus = tenant filter", dict(base, params={"idf": {"corpus": tflt}})),
]
for title, body in runs:
    print(f"\n-- {title}")
    if "params" in body:
        print(f"   params: {body['params']}")
    for i, h in enumerate(qdrant.query(body), 1):
        p = h["payload"]
        print(f"   {i}. {p['tenant_id']}/{p['doc_id']} / {p['section']}  score={h['score']:.3f}")
