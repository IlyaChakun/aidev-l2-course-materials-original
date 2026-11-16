"""Step 8. Measure search on the golden set: recall@5, recall@10 and NDCG@5 for dense, bm25 and hybrid.

DEMO_EXPLAIN=1 adds a "how to read this" note after every table, with one NDCG worked out by hand.
"""
import math

from rich.syntax import Syntax
from rich.table import Table

from lib import (COLLECTION, SEARCH_MODES, cache_note, check_collection, console, doc_ranks, embed, explain, header,
                 load_golden, ndcg_at, recall_at, search, search_body, short_json, sources_of)

header("Step 8. Measuring search: golden set, recall@5, recall@10, NDCG@5",
       "The homework's numbers, computed with our own code: each golden question goes through dense, bm25 and hybrid, "
       "the first 10 results are kept, then it is arithmetic over the saved sources.")
check_collection()

golden = load_golden()
core = [q for q in golden if q["kind"] == "core"]
multi = [q for q in golden if q["kind"] == "multi"]
traps = [q for q in golden if q["kind"] == "trap"]
asked = core + multi
vecs = embed([q["question"] for q in asked])

t = Table(title="The golden set (../_shared/golden.json, shared with Lab 03 and Lab 05)")
t.add_column("kind")
t.add_column("questions", justify="right")
t.add_column("what is marked")
t.add_column("counts in")
t.add_row("core", str(len(core)), "one document with the answer", "recall@5 (homework threshold 0.8), recall@10, NDCG@5")
t.add_row("multi", str(len(multi)), "two documents, the answer needs both", "the same metrics, block A")
t.add_row("trap", str(len(traps)), "nothing: the corpus has no answer", "no metric here; the agent must refuse (Lab 05)")
console.print(t)
console.print(f"Example: {core[0]['id']} \"{core[0]['question']}\" → {', '.join(core[0]['answer_docs'])}\n", style="dim")
explain([
    "A golden set is a fixed list of questions with the right documents marked by a person in advance, before any "
    "search is tuned. It turns 'search seems fine' into a number that can be compared between two versions.",
    "The documents are marked, not the chunks: the homework counts a hit when the right document shows up, whatever "
    "chunk of it was returned.",
    "Traps have no right document, so recall cannot be computed for them. Their job is to test the agent's refusal "
    "in part 3 of the homework; step 6 already showed that the database itself always returns something.",
    "All 17 questions were drafted by a model and still wait for a human review (see 'origin' in the file); "
    "the homework asks to mark such questions.",
])

# One run: the first 10 results of each search for each question; everything below is arithmetic over them.
console.print(f"[bold]8.1 One run[/bold]: {len(asked)} questions × {len(SEARCH_MODES)} searches, the first 10 results "
              f"kept. The hybrid request for {asked[0]['id']}  [cyan]POST /collections/{COLLECTION}/points/query[/cyan]")
console.print(Syntax(short_json(search_body("hybrid", asked[0]["question"], vecs[0].tolist()), max_floats=4), "json",
                     theme="ansi_dark", word_wrap=True))
console.print()
runs: dict[str, dict[str, list[str]]] = {}
hybrid_points: dict[str, list[dict]] = {}
for q, vec in zip(asked, vecs):
    runs[q["id"]] = {}
    for mode in SEARCH_MODES:
        pts = search(mode, q["question"], vec.tolist())
        runs[q["id"]][mode] = sources_of(pts)
        if mode == "hybrid":
            hybrid_points[q["id"]] = pts


def short_doc(source: str) -> str:
    return source.removesuffix(".md")


def cell(ranks: list[int | None]) -> str:
    text = ", ".join("—" if r is None else str(r) for r in ranks)
    if all(r is not None and r <= 5 for r in ranks):
        return f"[green]{text}[/green]"
    return f"[red]{text}[/red]" if any(r is None for r in ranks) else f"[yellow]{text}[/yellow]"


t = Table(title="Where the answer document is: position in the first 10 results (from 1)",
          caption="green: in the top 5 · yellow: 6-10 · red '—': not in the top 10; two numbers = two documents")
t.add_column("id")
t.add_column("question", max_width=58)
t.add_column("answer document(s)", max_width=40)
for mode in SEARCH_MODES:
    t.add_column(mode, justify="right")
for q in asked:
    ranks = {m: doc_ranks(runs[q["id"]][m], q["answer_docs"]) for m in SEARCH_MODES}
    t.add_row(q["id"], q["question"], "\n".join(short_doc(d) for d in q["answer_docs"]),
              *(cell(ranks[m]) for m in SEARCH_MODES))
console.print(t)
top5 = {m: sum(all(r is not None and r <= 5 for r in doc_ranks(runs[q["id"]][m], q["answer_docs"])) for q in asked)
        for m in SEARCH_MODES}
console.print("Questions with every answer document in the top 5: "
              + ", ".join(f"{m} {top5[m]} of {len(asked)}" for m in SEARCH_MODES) + "\n", style="dim")
explain([
    "One row per question, one column per search. The number is the position of the first chunk of the answer "
    "document among the 10 returned chunks. Several chunks of one document can come back; only the first counts.",
    "This table is the raw material: recall and NDCG below are computed only from these positions.",
    "Read the colours as the homework does: green = counts for recall@5, yellow = only for recall@10, red = not found.",
])


def metrics(questions: list[dict], mode: str) -> tuple[int, int, float]:
    r5 = sum(recall_at(runs[q["id"]][mode], q["answer_docs"], 5) for q in questions)
    r10 = sum(recall_at(runs[q["id"]][mode], q["answer_docs"], 10) for q in questions)
    ndcg = sum(ndcg_at(runs[q["id"]][mode], q["answer_docs"], 5) for q in questions) / len(questions)
    return r5, r10, ndcg


t = Table(title="Retrieval metrics (higher is better, 1.0 is the maximum)")
t.add_column("set")
t.add_column("search")
t.add_column("recall@5", justify="right")
t.add_column("recall@10", justify="right")
t.add_column("NDCG@5", justify="right")
results = {}
for name, qs in (("core", core), ("two-document", multi)):
    for mode in SEARCH_MODES:
        r5, r10, ndcg = metrics(qs, mode)
        results[(name, mode)] = (r5, r10, ndcg, len(qs))
        style = "bold" if mode == "hybrid" else ""
        t.add_row(f"{name} ({len(qs)})", mode, f"{r5 / len(qs):.2f} ({r5} of {len(qs)})",
                  f"{r10 / len(qs):.2f}", f"{ndcg:.3f}", style=style)
    t.add_section()
console.print(t)
console.print("recall@5 = share of questions found in the top 5; NDCG@5 also rewards the place.\n", style="dim")

# NDCG by hand on a real row: a core question whose answer is found but not first (hybrid first, then any search).
example, ex_mode = next(((q, m) for m in ("hybrid", "bm25", "dense") for q in core
                         if (doc_ranks(runs[q["id"]][m], q["answer_docs"])[0] or 99) in (2, 3, 4, 5)), (core[0], "hybrid"))
pos = doc_ranks(runs[example["id"]][ex_mode], example["answer_docs"])[0]
multi_ex = max(multi, key=lambda q: sum(r or 99 for r in doc_ranks(runs[q["id"]]["hybrid"], q["answer_docs"]))
               if all(doc_ranks(runs[q["id"]]["hybrid"], q["answer_docs"])) else 0)
mpos = doc_ranks(runs[multi_ex["id"]]["hybrid"], multi_ex["answer_docs"])
mdcg = sum(1 / math.log2(r + 1) for r in mpos if r and r <= 5)
same_core = len({results[("core", m)][:2] for m in SEARCH_MODES}) == 1
explain([
    "recall@5: for each question 1 if the answer document is among the first 5 results, else 0; then the average. "
    "It answers 'do we find it at all'. The homework threshold is recall@5 ≥ 0.8 on the 10 core questions, "
    "so one miss costs 0.1.",
    "recall@10: the same with a window of 10. If it is clearly higher than recall@5, the documents are found but "
    "ranked too low: fix the ranking (weights, fusion), not the corpus.",
    "NDCG@5 also rewards the place: first is better than fifth. Each position gives 1 / log2(position + 1) points if "
    "the answer document is there: position 1 → 1.000, 2 → 0.631, 3 → 0.500, 4 → 0.431, 5 → 0.387. "
    "This sum is DCG; it is divided by the best possible sum (IDCG), so the result is between 0 and 1.",
    f"By hand for {example['id']} ({ex_mode}): the answer document is at position {pos}, so "
    + (f"DCG = 1 / log2({pos} + 1) = {1 / math.log2(pos + 1):.3f}; IDCG = 1 (one document, best case at position 1); "
       f"NDCG@5 = {ndcg_at(runs[example['id']][ex_mode], example['answer_docs'], 5):.3f}. "
       if pos else "nothing is found: NDCG@5 = 0. ")
    + "Had it been first, NDCG@5 would be 1.000; recall@5 is 1 in both cases: this difference is what NDCG adds.",
    f"Two documents, {multi_ex['id']} (hybrid, positions {', '.join('—' if p is None else str(p) for p in mpos)}): "
    f"DCG = {' + '.join(f'1/log2({r}+1)' for r in mpos if r and r <= 5)} = {mdcg:.3f}; IDCG = 1 + 1/log2(3) = 1.631 "
    f"(both documents on top); NDCG@5 = {mdcg:.3f} / 1.631 = {mdcg / 1.631:.3f}. "
    "recall counts 1 only when both documents are in the window.",
    "Bold rows are the hybrid, the search the homework asks for. Compare the three searches on the same row "
    "of the set, not the absolute numbers with other corpora.",
] + ([
    "All three searches have the same recall on the core questions: this set is too easy to tell them apart. The questions "
    "share many words with the documents and were drafted by a model from the corpus. The differences show only on "
    "the two-document questions and in the worst question below; a harder, independently written set is M6 work.",
] if same_core else []))

# The worst question: the lowest hybrid NDCG@5, then the lowest recall@10.
worst = min(asked, key=lambda q: (ndcg_at(runs[q["id"]]["hybrid"], q["answer_docs"], 5),
                                  recall_at(runs[q["id"]]["hybrid"], q["answer_docs"], 10)))
console.print(f"[bold]Worst question {worst['id']}[/bold] (lowest hybrid NDCG@5): \"{worst['question']}\"")
t = Table(caption=f"needs: {', '.join(worst['answer_docs'])}")
t.add_column("#", justify="right")
t.add_column("hybrid top 5: chunk")
t.add_column("RRF", justify="right")
for i, p in enumerate(hybrid_points[worst["id"]][:5], start=1):
    src = p["payload"]["metadata"]["source"]
    heading = p["payload"]["content"].split("\n", 1)[0].split(" > ", 1)[-1]
    text = f"{short_doc(src)} > {heading}"
    t.add_row(str(i), f"[green]{text}[/green]" if src in worst["answer_docs"] else text, f"{p['score']:.4f}")
console.print(t)
console.print("positions of the answer document(s): " + "; ".join(
    f"{m} {', '.join('—' if r is None else str(r) for r in doc_ranks(runs[worst['id']][m], worst['answer_docs']))}"
    for m in SEARCH_MODES) + "\n", style="dim")
explain([
    "The homework asks for 2-3 sentences of diagnosis for the worst question: is it the chunk, the search or the "
    "prompt. This table is where that starts: what the hybrid actually returned instead of the answer.",
    "Three usual causes. Chunk: the answer is split or buried in a long chunk about something else. Search: the "
    "question uses other words than the document (look at bm25) or mixes two intents (one part wins both branches). "
    "Corpus: the answer is not written down where it was marked.",
    "Two documents and only one found is the typical sign of two intents in one question: the louder part (here "
    "the outage words) wins both branches, the second part never competes. The fix is not chunking but splitting "
    "the question into two searches and merging the results (query decomposition), an agent-level step.",
    "Document-level recall can hide a chunk-level miss: the right document may be found through the wrong section. "
    "Before writing the diagnosis, open the returned chunk and check that the answer is in it.",
])

# The block the homework's report.md expects, ready to paste.
r5, r10, ndcg, n = results[("core", "hybrid")]
m5, m10, mndcg, mn = results[("two-document", "hybrid")]
report = "\n".join([
    "| Metric | Value |",
    "|---|---|",
    f"| recall@5 | {r5 / n:.2f} ({r5} of {n}) |",
    f"| recall@10 | {r10 / n:.2f} (block A) |",
    f"| NDCG@5 | {ndcg:.2f} (block A) |",
    f"| recall@5, two-document questions | {m5 / mn:.2f} ({m5} of {mn}, block A) |",
])
console.print("[bold]The shape of the metrics table the homework asks for in report.md[/bold] "
              "(filled with this demo's numbers; yours come from your corpus and your golden set)")
console.print(Syntax(report, "markdown", theme="ansi_dark"))
console.print()
explain([
    "This is the shape of the table the homework asks for. The numbers here describe the Lumen demo; a homework "
    "report needs numbers from its own corpus, golden set and script.",
    "Write next to it which search produced the numbers (here: hybrid, prefetch 20 + RRF, collection "
    f"\"{COLLECTION}\"), the embedding model and the date: a number without its setup cannot be compared later.",
])
verdict = "met" if r5 / n >= 0.8 else "NOT met"
console.print(f"Takeaway: hybrid recall@5 on the core questions is {r5 / n:.2f}, the homework threshold of 0.8 is "
              f"{verdict}. Ten questions are a first measurement: one question moves recall by 0.1.")
console.print(cache_note(), style="dim")
