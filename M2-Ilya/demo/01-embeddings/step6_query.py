"""Step 6. Query the collection: dense / bm25 / hybrid (prefetch + RRF) through /points/query.

DEMO_EXPLAIN=1 adds a "how to read this" note after every table, with the RRF scores worked out.
"""
from rich.syntax import Syntax
from rich.table import Table

from lib import (COLLECTION, QUERIES, TRAP_QUERY, cache_note, check_collection, console, embed, explain, header,
                 is_answer, qdrant, short_json)

# What each question shows; printed only with DEMO_EXPLAIN=1, under its table.
NOTES = {
    "Error code": [
        "bm25 finds the answer, dense ranks it lower: embeddings blur exact codes (step 3).",
        "Hybrid is not always the best of both: here two chunks that are first in one list and 5th in the other "
        "outscore the answer, which is 4th in dense and 2nd in bm25. RRF rewards being high in both lists.",
        "Qdrant's BM25 differs from our step 1-3 BM25: its tokenizer also reduces words to their root (stemming), "
        "so 'mean' now matches 'means', and it has its own stop words. That is why its scores and order differ "
        "from step 3.",
    ],
    "Paraphrase": [
        "dense puts the GDPR 'data export' chunk first (same word, other meaning); bm25 finds the answer first "
        "through the rare word 'viewer'.",
        "Hybrid puts the answer first: it is high in both lists, the GDPR chunk only in one.",
    ],
    "Russian question": [
        "bm25 is empty: no Russian word occurs in the English corpus.",
        "Hybrid still answers: when one branch returns nothing, the other branch alone decides the order. "
        "The scores are 1/2, 1/3, 1/4... because each chunk gets points from one list only.",
    ],
    "Trap": [
        "Salesforce occurs nowhere in the corpus, yet every column returns 5 chunks: a search engine always returns "
        "the closest it has, it never says 'nothing relevant'.",
        "The closest are about connecting other things (a store, integrations, Slack): similar words and meaning, "
        "wrong answer. Passing them to the model invites a made-up answer.",
    ],
}

header("Step 6. Querying Qdrant: dense, bm25 and hybrid",
       f"Everything through one endpoint POST /collections/{COLLECTION}/points/query (/search is deprecated: dropped from the API spec in 1.19).")
check_collection()

questions = QUERIES + [("Trap", TRAP_QUERY, None, None)]
qvecs = embed([q[1] for q in questions])        # precomputed and cached by `make warm`


def bodies(text: str, vec) -> dict[str, dict]:
    sparse = {"text": text, "model": "Qdrant/bm25"}   # Qdrant turns the text into a BM25 sparse vector itself
    return {
        "dense": {"query": vec, "limit": 5, "with_payload": True},
        "bm25": {"query": sparse, "using": "bm25", "limit": 5, "with_payload": True},
        "hybrid": {
            "prefetch": [
                {"query": vec, "limit": 20},
                {"query": sparse, "using": "bm25", "limit": 20},
            ],
            "query": {"fusion": "rrf"},
            "limit": 5,
            "with_payload": True,
        },
    }


def label(p: dict) -> str:
    content = p["payload"]["content"]
    first = content.split("\n", 1)[0]                     # "Title > Heading"
    return f"{p['payload']['metadata']['source'].removesuffix('.md')} > {first.split(' > ', 1)[-1]}"


example = bodies(QUERIES[0][1], qvecs[0].tolist())["hybrid"]
console.print("[bold]The whole hybrid query[/bold] (vector truncated): two branches in prefetch with 20 candidates each, "
              "then RRF fusion and top-5")
console.print(Syntax(short_json(example, max_floats=4), "json", theme="ansi_dark", word_wrap=True))
console.print()
explain([
    f"All three searches go to one endpoint, POST /collections/{COLLECTION}/points/query; only the JSON body differs.",
    "dense: 'query' is the question's embedding (1536 numbers); Qdrant compares it with the unnamed dense vectors "
    "by cosine, as numpy did in step 3.",
    "bm25: 'query' is the question as text + model 'Qdrant/bm25', and 'using': 'bm25' picks the named sparse vector. "
    "Qdrant turns the text into a sparse vector itself and scores by BM25.",
    "hybrid (the JSON above): 'prefetch' runs both searches first, 20 candidates each; then 'query': "
    "{'fusion': 'rrf'} merges the two lists into one (Reciprocal Rank Fusion, worked out at the end) and 'limit' "
    "keeps the top 5.",
    "Why 20 and not 5 per branch: the answer may be 8th in one list and 3rd in the other; with more candidates "
    "the merge has a chance to lift it.",
])

explain([
    "Each table below is one question; the three columns are the three searches, the number under a chunk is its "
    "score. Bold green '<- answer' marks the chunk that holds the answer.",
    "The scores live on different scales and must not be compared across columns: cosine is at most 1, "
    "BM25 has no upper limit, and the RRF score depends only on ranks (positions), not on meaning.",
])

summary = []
for q, vec in zip(questions, qvecs):
    kind, text, src, pattern = q
    results = {name: qdrant("POST", f"/collections/{COLLECTION}/points/query", body)["result"]["points"]
               for name, body in bodies(text, vec.tolist()).items()}

    caption = f"\"<- answer\": the chunk with the answer from {src}" if src else "there is no answer in the corpus: Salesforce is not mentioned anywhere"
    t = Table(title=f"{kind}: \"{text}\"", caption=caption, show_lines=True)
    t.add_column("#", justify="right")
    for name, hint in [("dense", "cosine"), ("bm25", "BM25 from Qdrant"), ("hybrid", "RRF")]:
        t.add_column(f"{name} ({hint})")
    ranks = {}
    for r in range(5):
        row = [str(r + 1)]
        for name in ("dense", "bm25", "hybrid"):
            pts = results[name]
            if r >= len(pts):
                row.append("[dim]— empty —[/dim]")
                continue
            p = pts[r]
            hit = src and is_answer(p["payload"]["content"], p["payload"]["metadata"]["source"], src, pattern)
            if hit and name not in ranks:
                ranks[name] = r + 1
            style = "bold green" if hit else ""
            mark = "  <- answer" if hit else ""
            row.append(f"[{style}]{label(p)}{mark}[/{style}]\n[dim]{p['score']:.4f}[/dim]" if style
                       else f"{label(p)}\n[dim]{p['score']:.4f}[/dim]")
        t.add_row(*row)
    console.print(t)
    console.print()
    explain(NOTES.get(kind, []), title="What this question shows")
    summary.append((kind, ranks, {n: (results[n][0]["score"] if results[n] else None) for n in results}))

t = Table(title="Summary: rank of the chunk with the answer (top-5) and the score of the first result")
t.add_column("question")
for name in ("dense", "bm25", "hybrid"):
    t.add_column(f"{name}: rank", justify="right")
t.add_column("dense top-1 score", justify="right")
t.add_column("hybrid top-1 score", justify="right")
for kind, ranks, top in summary:
    is_trap = kind == "Trap"
    cells = ["—" if is_trap else str(ranks.get(n, "none")) for n in ("dense", "bm25", "hybrid")]
    t.add_row(kind, *cells, f"{top['dense']:.4f}", f"{top['hybrid']:.4f}" if top["hybrid"] is not None else "—")
console.print(t)
trap_dense = summary[-1][2]["dense"]
real_max = max(s[2]["dense"] for s in summary[:-1])
console.print(f"Trap: the database still returned 5 chunks. The dense top-1 of the trap is {trap_dense:.4f} — "
              f"{'higher than' if trap_dense > real_max else 'of the same order as'} that of the three questions above (maximum {real_max:.4f}). "
              "The RRF score depends only on ranks, not on meaning. A score threshold is not a refusal: "
              "the agent must refuse via its prompt, or a separate check must.\n")
explain([
    "rank columns: where the answer chunk ended up in each search's top-5 ('none' = not in the top-5). "
    "The trap has no answer, so '—'.",
    "dense top-1 score: the cosine of the best chunk. Look at the trap row: its best match scores higher than "
    "the best match of any real question. So 'cosine above X means relevant' does not work as a filter.",
    "hybrid top-1 score: RRF gives the same 0.8333 to the trap and to a real answer, because RRF only adds up "
    "1 / (k + rank): first in one list and second in the other is 1/2 + 1/3 = 0.8333, whatever the meaning.",
    "Conclusion for the homework: the database cannot say 'no answer'. The agent's prompt must make it refuse when "
    "the chunks do not contain the answer, or a separate check must run before the model.",
])

# RRF by hand: recompute Qdrant's fused score from the two ranked lists.
kind, text, _, _ = QUERIES[0]
b = bodies(text, qvecs[0].tolist())
dense20 = [p["id"] for p in qdrant("POST", f"/collections/{COLLECTION}/points/query", {**b["dense"], "limit": 20, "with_payload": False})["result"]["points"]]
bm20 = [p["id"] for p in qdrant("POST", f"/collections/{COLLECTION}/points/query", {**b["bm25"], "limit": 20, "with_payload": False})["result"]["points"]]
hyb = qdrant("POST", f"/collections/{COLLECTION}/points/query", b["hybrid"])["result"]["points"]
K = 2  # Qdrant default for {"fusion": "rrf"}; ranks start at 0
t = Table(title=f"RRF by hand for \"{text}\": score = sum of 1/(k + rank), rank from 0, k = {K}")
t.add_column("chunk")
t.add_column("rank in dense", justify="right")
t.add_column("rank in bm25", justify="right")
t.add_column("our calculation", justify="right")
t.add_column("Qdrant", justify="right")
for p in hyb:
    rd = dense20.index(p["id"]) if p["id"] in dense20 else None
    rb = bm20.index(p["id"]) if p["id"] in bm20 else None
    mine = (1 / (K + rd) if rd is not None else 0) + (1 / (K + rb) if rb is not None else 0)
    t.add_row(label(p), "—" if rd is None else str(rd), "—" if rb is None else str(rb), f"{mine:.4f}", f"{p['score']:.4f}")
console.print(t)
first = hyb[0]
rd0 = dense20.index(first["id"]) if first["id"] in dense20 else None
rb0 = bm20.index(first["id"]) if first["id"] in bm20 else None
explain([
    "RRF (Reciprocal Rank Fusion) ignores the scores and looks only at positions: each list gives a chunk "
    "1 / (k + rank) points, the points from both lists are added up. Rank counts from 0 (first place = 0).",
    f"Worked out for the first row: rank {rd0 if rd0 is not None else '—'} in dense gives "
    f"{f'1 / ({K} + {rd0}) = {1 / (K + rd0):.4f}' if rd0 is not None else '0 (not in the list)'}, "
    f"rank {rb0 if rb0 is not None else '—'} in bm25 gives "
    f"{f'1 / ({K} + {rb0}) = {1 / (K + rb0):.4f}' if rb0 is not None else '0 (not in the list)'}; "
    f"sum {first['score']:.4f}, the same as Qdrant.",
    f"With k = {K} the maximum is 1/{K} + 1/{K} = {2 / K:.1f} (first in both lists). Being high in both lists beats "
    "being first in one: that is the whole idea of hybrid search.",
    "Why the scores ignore meaning: cosine (at most 1) and BM25 (no limit) cannot be added directly, positions can. "
    "The price: RRF scores say nothing about relevance, as the trap showed.",
    "k smooths the gap between places: with a big k (60 in the original paper) first and fifth place get almost the "
    "same points; Qdrant's default is 2. Ties are possible: ranks 4 and 0 give the same sum as ranks 0 and 4.",
])
console.print("Matches. In Qdrant 1.19 k can be set explicitly: \"query\": {\"rrf\": {\"k\": 60}} "
              "(then top-1 gives 1/60 instead of 1/2), branch weights: {\"rrf\": {\"weights\": [3.0, 1.0]}}.", style="dim")
console.print(cache_note(), style="dim")
