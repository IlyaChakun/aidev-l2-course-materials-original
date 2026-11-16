"""Step 9. Block A of the homework: one change at a time, the metrics before and after on the same golden set.

Two experiments: RRF branch weights on the step 5 collection, and three other chunkings loaded into a temporary
collection (deleted at the end). DEMO_EXPLAIN=1 adds a "how to read this" note after every table.
"""
from rich.table import Table

from lib import (COLLECTION, cache_note, check_collection, chunk_corpus, collection_body, console, embed, explain,
                 header, load_corpus, load_golden, ndcg_at, qdrant, recall_at, search, sources_of, to_points)

EXP = f"{COLLECTION}_exp"     # temporary collection for the chunking variants

header("Step 9. Block A: one change, metrics before and after",
       "The same golden set and the same metric code as step 8. Each row changes one thing; "
       "the deliverable is the difference between rows, not the absolute number.")
check_collection()

golden = load_golden()
core = [q for q in golden if q["kind"] == "core"]
multi = [q for q in golden if q["kind"] == "multi"]
asked = core + multi
qvecs = [v.tolist() for v in embed([q["question"] for q in asked])]


def measure(collection: str, fusion: dict | None = None) -> dict[str, float]:
    """Hybrid search for every question, then the step 8 metrics."""
    runs = {q["id"]: sources_of(search("hybrid", q["question"], v, collection=collection, fusion=fusion))
            for q, v in zip(asked, qvecs)}

    def avg(fn, qs, k):
        return sum(fn(runs[q["id"]], q["answer_docs"], k) for q in qs) / len(qs)
    return {"core r@5": avg(recall_at, core, 5), "core NDCG@5": avg(ndcg_at, core, 5),
            "multi r@5": avg(recall_at, multi, 5), "multi r@10": avg(recall_at, multi, 10),
            "multi NDCG@5": avg(ndcg_at, multi, 5)}


COLS = ["core r@5", "core NDCG@5", "multi r@5", "multi r@10", "multi NDCG@5"]


def metric_table(title: str, rows: list[tuple[str, str, dict]], first_col: str) -> None:
    t = Table(title=title)
    t.add_column(first_col)
    t.add_column("what changes")
    for c in COLS:
        t.add_column(c, justify="right")
    base = rows[0][2]
    for i, (name, note, m) in enumerate(rows):
        cells = []
        for c in COLS:
            d = m[c] - base[c]
            delta = "" if i == 0 or abs(d) < 0.0005 else f" [{'green' if d > 0 else 'red'}]({d:+.3f})[/]"
            cells.append(f"{m[c]:.3f}{delta}")
        t.add_row(name, note, *cells, style="bold" if i == 0 else "")
    console.print(t)


# ---- 9.1 RRF branch weights: same collection, only the fusion changes ------------------------------------------
console.print("[bold]9.1 RRF branch weights[/bold] (dense : bm25), collection "
              f"\"{COLLECTION}\" from step 5, query {{\"rrf\": {{\"weights\": \\[dense, bm25]}}}}\n")
weights = [("1:1 (before)", "default {\"fusion\": \"rrf\"}", None),
           ("3:1", "trust dense more", {"rrf": {"weights": [3.0, 1.0]}}),
           ("1:3", "trust bm25 more", {"rrf": {"weights": [1.0, 3.0]}})]
weight_rows = [(name, note, measure(COLLECTION, fusion)) for name, note, fusion in weights]
metric_table("RRF weights: hybrid metrics on the golden set (in brackets: the change against 1:1)", weight_rows, "weights")
console.print("Only the fusion part of the query changes; the collection and the questions stay the same.\n", style="dim")
explain([
    "Only the 'query' part of the hybrid request changes; the collection, the questions and the code are the same, "
    "so any difference in a row comes from the weights.",
    "The weights follow the order of the prefetch branches: here dense first, bm25 second. A bigger weight gives "
    "that branch's places more points in the RRF sum (step 6).",
    "r@5 = recall@5, r@10 = recall@10. core = the 10 one-document questions, multi = the 5 two-document ones.",
    "On 10 questions one question is 0.1 of recall: a change smaller than that is noise or one question moving. "
    "Read NDCG for small effects: it moves when the right document goes up or down by one place.",
])

# ---- 9.2 Chunk size and overlap: each variant is loaded into a temporary collection --------------------------
console.print("[bold]9.2 Chunking[/bold]: the same corpus cut three other ways, each loaded into the temporary "
              f"collection \"{EXP}\" and measured with the default hybrid (RRF, weights 1:1)\n")
docs = load_corpus()
variants = [("400 (before)", "the step 4 chunking", 400, 0.0),
            ("300", "smaller chunks", 300, 0.0),
            ("300 + overlap 12%", "smaller chunks, repeated tail", 300, 0.12),
            ("500", "bigger chunks", 500, 0.0)]
rows, stats = [], []
for name, note, target, share in variants:
    chunks = chunk_corpus(docs, target=target, overlap_share=share)
    overlapped = [c for c in chunks if c.overlap]
    stats.append((name, len(chunks), sum(c.tokens for c in chunks) / len(chunks), max(c.tokens for c in chunks),
                  len(overlapped), sum(c.overlap for c in overlapped) / max(1, sum(c.tokens for c in overlapped))))
    if target == 400 and not share:
        rows.append((name, note, measure(COLLECTION)))      # the step 5 collection is exactly this chunking
        continue
    vecs = embed([c.text for c in chunks])
    qdrant("DELETE", f"/collections/{EXP}")
    qdrant("PUT", f"/collections/{EXP}", collection_body(f"h2-{target}tok" + (f"-overlap{share:.0%}" if share else "")))
    points = to_points(chunks, vecs)
    for i in range(0, len(points), 64):
        qdrant("PUT", f"/collections/{EXP}/points?wait=true", {"points": points[i:i + 64]})
    rows.append((name, note, measure(EXP)))
qdrant("DELETE", f"/collections/{EXP}")

t = Table(title="The chunkings compared")
t.add_column("chunking")
t.add_column("chunks", justify="right")
t.add_column("avg tokens", justify="right")
t.add_column("max tokens", justify="right")
t.add_column("chunks with overlap", justify="right")
t.add_column("overlap share in them", justify="right")
for name, n, avg, mx, n_ov, share in stats:
    t.add_row(name, str(n), f"{avg:.0f}", str(mx), str(n_ov), f"{share:.0%}" if n_ov else "—")
console.print(t)
console.print("Smaller target → more chunks and more splits, so the overlap fires more often.\n", style="dim")
metric_table("Chunking: hybrid metrics on the golden set (in brackets: the change against 400)", rows, "chunking")
console.print(f"The temporary collection \"{EXP}\" is deleted; \"{COLLECTION}\" was not changed.\n", style="dim")
explain([
    "Each variant keeps the step 4 rules (cut by H2, never inside a table or code block) and changes one number: "
    "the target size (range = target × 0.75 ... × 1.25) or the overlap.",
    "Smaller chunks split more sections, so overlap fires more often; '300 + overlap 12%' repeats the last sentences "
    "of a piece (up to 36 tokens) at the start of the next one. This is the 10-15% overlap of the homework.",
    "Every variant goes into its own fresh collection with the same schema as step 5; changing the chunking means "
    "re-embedding and reloading everything, which is why the collection is rebuilt by a script.",
    "Both experiments are in-sample: the variants are judged on the same 15 questions that would be used to pick one. "
    "A winner here is a hypothesis to confirm on other questions, not a production decision.",
])

# For the report: a change counts as an improvement only if no metric got worse.
candidates = [(f"{exp} {before[0]} → {r[0]}", before[2], r[2]) for exp, rs in (("weights", weight_rows), ("chunking", rows))
              for before, r in [(rs[0], r) for r in rs[1:]]
              if all(r[2][c] >= rs[0][2][c] - 0.0005 for c in COLS) and any(r[2][c] > rs[0][2][c] + 0.0005 for c in COLS)]
if candidates:
    title, before, after = max(candidates, key=lambda x: sum(x[2][c] - x[1][c] for c in COLS))
    report = ["| Metric | Before | After |", "|---|---|---|"] + [f"| {c} | {before[c]:.3f} | {after[c]:.3f} |" for c in COLS]
    console.print(f"[bold]The shape of the homework's before/after table[/bold] ({title}: some metrics up, none down)")
    console.print("\n".join(report), markup=False)
else:
    console.print("[bold]Before/after:[/bold] no variant improved a metric without making another one worse.")
console.print()
explain([
    "The homework wants one such table per experiment plus two or three sentences: what changed, why you think so, "
    "what you would take to production.",
    "Only a change with no metric going down is offered as the 'after'. A variant that wins one column and loses "
    "another is a trade-off, not an improvement; write it up as such.",
    "An honest conclusion on this corpus can be 'no measurable change': with 10 + 5 questions the set is too small "
    "to separate close variants, and the core questions are easy for every chunking.",
])
console.print("Takeaway: change one thing, measure on the same set, report the difference and how big the set is.")
console.print(cache_note(), style="dim")
