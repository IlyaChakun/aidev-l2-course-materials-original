"""Step 3. Same questions on the whole corpus: BM25 top-5 vs dense top-5 (numpy brute force).

DEMO_EXPLAIN=1 adds a "how to read this" note after every table and a per-word BM25 breakdown.
"""
import numpy as np
from rich.table import Table

from lib import (BM25, EXPLAIN, QUERIES, cache_note, chunk_corpus, console, embed, explain, header, is_answer,
                 load_corpus, tokenize)

# What each question shows; printed only with DEMO_EXPLAIN=1, under the per-word breakdown.
NOTES = {
    "Error code": [
        "BM25: the code e-4031 is a rare word, but it occurs in several chunks, and 'mean' is rare too. A short chunk "
        "that only contains 'mean' can outscore the answer: the breakdown shows which word brought the points.",
        "Dense: every chunk about error codes looks alike to the embedding, so neighbours about other codes "
        "(E-4012, E-1105) come before the answer. Embeddings blur exact identifiers.",
    ],
    "Paraphrase": [
        "BM25 does well here: the question happens to share rare words with the answer ('viewer', 'export'). "
        "'workspace' occurs in many chunks, so its IDF and its points are small.",
        "Dense puts 'Requesting a data export' (GDPR) first: same word 'export', different meaning. "
        "The answer is still in the top-5.",
    ],
    "Russian question": [
        "BM25: the Russian words occur nowhere in the English corpus, every score is 0, nothing is returned.",
        "Dense: the multilingual model maps the Russian question next to the English 'Forgot password' chunk: "
        "first place, with no shared words.",
    ],
}

header("Step 3. BM25 vs embeddings on the Lumen corpus",
       "22 documents are cut into chunks (we show how in step 4). Dense is brute force in numpy: "
       "chunk matrix @ query vector. There is no database yet.")

chunks = chunk_corpus(load_corpus())
bm = BM25([tokenize(c.text) for c in chunks])
matrix = embed([c.text for c in chunks])              # (n_chunks, 1536), from cache after first run
qvecs = embed([q[1] for q in QUERIES])
console.print(f"Chunks: {len(chunks)}, embedding matrix {matrix.shape}. {cache_note()}\n", style="dim")
explain([
    f"Same idea as steps 1 and 2, now on the real corpus: {len(chunks)} chunks (pieces of the 22 documents) "
    "and three questions. Each question is answered twice, by BM25 and by embeddings, side by side.",
    f"BM25: the same class as in step 1, built over the {len(chunks)} chunks. The average chunk length is now "
    f"{bm.avgdl:.0f} words after the step 1 tokenizer (step 4 counts model tokens, a different unit, so its numbers "
    "are higher). Chunk lengths vary a lot, so the length penalty matters more than with three tiny documents.",
    f"Dense: the embedding matrix is {matrix.shape[0]} rows × {matrix.shape[1]} numbers, one row per chunk. "
    f"'matrix @ query vector' multiplies every row by the question's vector in one go: {matrix.shape[0]} cosines "
    "(the vectors have length 1, so dot = cosine). Sort them, take the top 5.",
    "This is exact search by brute force: every chunk is compared with the question. A vector database does the "
    "same faster on millions of vectors (step 5 onwards); there is no database here yet.",
])


def cell(i: int, score: float, q) -> str:
    c = chunks[i]
    _, _, src, pattern = q
    if is_answer(c.text, c.source, src, pattern):
        return f"[bold green]{c.label}  <- answer[/bold green]\n[dim]{score:.3f}[/dim]"
    if c.source == src:
        return f"[green]{c.label}[/green]\n[dim]{score:.3f}[/dim]"
    return f"{c.label}\n[dim]{score:.3f}[/dim]"


def answer_rank(order, q) -> int | None:
    _, _, src, pattern = q
    return next((r + 1 for r, i in enumerate(order) if is_answer(chunks[i].text, chunks[i].source, src, pattern)), None)


def bm25_breakdown(query: str, rows: list[tuple[str, int]]) -> None:
    """Per-word points for the given chunks: where a BM25 score comes from."""
    words = tokenize(query)
    t = Table(title="BM25 breakdown: points each query word brings (tf = occurrences in the chunk)")
    t.add_column("chunk")
    t.add_column("length", justify="right")
    for w in words:
        idf = f"IDF {bm.idf(w):.2f}, in {len(bm.index[w])} chunks" if w in bm.index else "in no chunk"
        t.add_column(f"{w}\n[dim]{idf}[/dim]", justify="right")
    t.add_column("total", justify="right")
    for role, i in rows:
        cells = []
        for w in words:
            tf = bm.index.get(w, {}).get(i)
            cells.append(f"tf={tf} → {bm.term_score(tf, len(bm.docs[i]), bm.idf(w)):.2f}" if tf else "-")
        t.add_row(f"{role}: {chunks[i].label}", str(len(bm.docs[i])), *cells, f"{bm.scores(query)[i]:.3f}")
    console.print(t)


explain([
    "Each table below is one question. Left column: BM25 top-5, right column: dense top-5. "
    "The small number under each chunk is its score.",
    "Green = a chunk from the right document; bold green with '<- answer' = the chunk that actually holds the answer.",
    "Do not compare the numbers across the columns: BM25 has no upper limit (a sum of word points), "
    "cosine is at most 1. Compare the ranks: where did the answer end up?",
    "With DEMO_EXPLAIN=1 each question also gets a BM25 breakdown: the points each word brought to the BM25 winner "
    "and to the answer chunk.",
])

summary = []
for qi, q in enumerate(QUERIES):
    kind, query, src, _ = q
    bm_scores = bm.scores(query)
    dense_scores = matrix @ qvecs[qi]
    bm_order = [i for i in np.argsort(-bm_scores, kind="stable") if bm_scores[i] > 0]
    dn_order = list(np.argsort(-dense_scores))

    t = Table(title=f"{kind}: \"{query}\"", caption=f"green: document {src}, \"<- answer\": the chunk that holds the answer",
              show_lines=True)
    t.add_column("#", justify="right")
    t.add_column("BM25 (word match)")
    t.add_column("Dense (cosine, meaning)")
    for r in range(5):
        left = cell(bm_order[r], bm_scores[bm_order[r]], q) if r < len(bm_order) else "[dim]— no matching words —[/dim]"
        t.add_row(str(r + 1), left, cell(dn_order[r], dense_scores[dn_order[r]], q))
    console.print(t)
    console.print(f"query tokens for BM25: {' '.join(tokenize(query))}\n", style="dim")
    summary.append((kind, answer_rank(bm_order, q), answer_rank(dn_order, q)))
    if EXPLAIN:
        rows = [("BM25 #1", bm_order[0])] if bm_order else []
        ans = answer_rank(bm_order, q)
        if ans and ans > 1:
            rows.append((f"answer, BM25 #{ans}", bm_order[ans - 1]))
        if rows:
            bm25_breakdown(query, rows)
        explain(NOTES.get(kind, []), title="What this question shows")

t = Table(title="Summary: rank of the first chunk with the answer (out of all corpus chunks)")
t.add_column("question")
t.add_column("BM25", justify="right")
t.add_column("Dense", justify="right")
for kind, b, d in summary:
    t.add_row(kind, str(b) if b else "not found", str(d) if d else "not found")
console.print(t)
explain([
    f"rank = the position of the first chunk that holds the answer, counting all {len(chunks)} chunks; "
    "1 is the best. 'not found' = the method did not return it at all (BM25 returns only chunks with a shared word).",
    "Neither method wins every row. BM25 is ahead on the code and, on this corpus, on the paraphrase too (the question "
    "shares the rare word 'viewer' with the answer); dense is the only one that finds the Russian question. "
    "Step 6 merges both lists (hybrid search) to get the strengths of each.",
])
console.print("Takeaway: each method has its own blind spots. That is why the homework uses a hybrid: dense + BM25, the result lists are merged (step 6).")
