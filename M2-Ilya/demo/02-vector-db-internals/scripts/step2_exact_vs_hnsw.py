"""Step 2. Big collection: exact brute force vs HNSW - latency and recall@10."""

from common import (C_MAIN, api, collection_info, console, explain, get_queries, mean_recall, ms, new_table, note,
                    query, recall_at_k, run_batch, summarize)

# The article a reader expects for the example query, to check whether the 50,000-article sample has it.
EXPECTED_TITLE = {"physicist who developed the theory of relativity": "Albert Einstein"}


def title_in_collection(title: str) -> bool:
    body = {"filter": {"must": [{"key": "title", "match": {"value": title}}]}, "limit": 1, "with_payload": False}
    return bool(api("POST", f"/collections/{C_MAIN}/points/scroll", body)["result"]["points"])


def main() -> None:
    labels, qv, source = get_queries()
    info = collection_info(C_MAIN)
    n = info["points_count"]
    console.rule(f"Step 2 · {C_MAIN}: {n:,} points, exact search vs HNSW")
    note(f"{n:,} Wikipedia articles (DBpedia), one OpenAI vector of 1,536 numbers each. "
         f"The same {len(qv)} questions run twice: brute force over every point, then through the HNSW index.")

    exact_ids, exact_srv, exact_rtt = run_batch(C_MAIN, qv, {"exact": True})
    hnsw_ids, hnsw_srv, hnsw_rtt = run_batch(C_MAIN, qv)

    t = new_table(f"{len(qv)} queries ({source}), top-10", "mode", "server p50 ms", "server p95 ms",
                  "round-trip p50 ms", "recall@10")
    e, h = summarize(exact_srv), summarize(hnsw_srv)
    recall = mean_recall(hnsw_ids, exact_ids)
    t.add_row("exact=true (brute force over all points)", ms(e["p50"]), ms(e["p95"]), ms(summarize(exact_rtt)["p50"]), "1.000")
    t.add_row("HNSW (m=16, default ef)", ms(h["p50"]), ms(h["p95"]), ms(summarize(hnsw_rtt)["p50"]), f"{recall:.3f}")
    console.print(t)
    speedup = e["p50"] / h["p50"] if h["p50"] else float("nan")
    note(f"HNSW is about {speedup:.0f}x faster than brute force on {n:,} points. Brute force grows linearly: "
         f"on 1M points ~{e['p50'] * 1_000_000 / n:,.0f} ms, on 100M ~{e['p50'] * 100_000_000 / n / 1000:,.0f} s "
         "per query (a rough linear estimate on this hardware).")
    explain("How to read the first table: speed against exactness", [
        f"exact=true is brute force: Qdrant compares the question with every one of the {n:,} vectors. "
        f"It is exact by definition (recall@10 = 1.000) and serves as the reference, but its time grows with the "
        f"collection: {ms(e['p50'])} ms here, about {e['p50'] * 100_000_000 / n / 1000:,.0f} s per query at 100 million.",
        f"HNSW walks a graph of near neighbours and checks only a small part of the points: {speedup:.0f} times "
        f"faster ({ms(h['p50'])} ms), and it returned {recall:.1%} of the exact top 10. That small loss is the price.",
        "p50 is the median query, p95 the slow tail (95% of queries were faster). Server time is measured inside "
        "Qdrant; round-trip adds the network and Python.",
        "recall@10 here = how many of the exact top 10 HNSW also returned. It is not the homework's recall@5, "
        "which checks whether the right document came back for a golden question.",
        "Milliseconds and the ratio depend on the laptop and its load; the shape of the result does not.",
    ])

    imperfect = [i for i in sorted(range(len(qv)), key=lambda i: recall_at_k(hnsw_ids[i], exact_ids[i]))
                 if recall_at_k(hnsw_ids[i], exact_ids[i]) < 1]
    worst = imperfect[:5]
    t2 = new_table(f"Queries where HNSW missed something: {len(imperfect)} of {len(qv)} (up to 5 shown)",
                   "query", "recall@10", "what was missed (positions in exact)")
    lines = [f"HNSW returned the whole exact top 10 for {len(qv) - len(imperfect)} of {len(qv)} questions; "
             "this table lists the rest."]
    for i in worst:
        missed = [pos + 1 for pos, pid in enumerate(exact_ids[i]) if pid not in set(hnsw_ids[i])]
        r = recall_at_k(hnsw_ids[i], exact_ids[i])
        t2.add_row(labels[i][:60], f"{r:.1f}", ", ".join(map(str, missed)) or "-")
        where = ", ".join(map(str, missed))
        lines.append(f"\"{labels[i]}\": {round(r * 10)} of 10 found; it missed the article brute force put at "
                     f"position {where}" + (", the best answer itself." if 1 in missed else "."))
    console.print(t2)
    if imperfect:
        lines.append("The greedy walk stopped at a near point that was good but not the best: that is what "
                     "\"approximate\" means. A wider search, hnsw_ef in step 3, closes the gap at the cost of speed.")
    else:
        lines.append("HNSW matched brute force on every question in this run.")
    explain("How to read the second table: where the index lost something", lines)

    i = 0
    ex, _, _ = query(C_MAIN, qv[i], 5, {"exact": True}, with_payload=["title"])
    hn, _, _ = query(C_MAIN, qv[i], 5, with_payload=["title"])
    t3 = new_table(f"Example: \"{labels[i]}\" (top-5)", "#", "exact", "score", "HNSW", "score", justify_right_from=9)
    for k in range(5):
        t3.add_row(str(k + 1), ex[k]["payload"]["title"], f"{ex[k]['score']:.3f}",
                   hn[k]["payload"]["title"], f"{hn[k]['score']:.3f}")
    console.print(t3)
    note("recall@10 = the share of the exact top-10 that HNSW found. Ground truth is the same Qdrant with params.exact=true.")
    same = [p["id"] for p in ex] == [p["id"] for p in hn]
    lines = ["Both columns are the same five articles in the same order: for most questions HNSW loses nothing."
             if same else "The two columns differ: HNSW changed the top 5 for this question."]
    expected = EXPECTED_TITLE.get(labels[i])
    if expected and not title_in_collection(expected):
        lines.append(f"The article you would expect, \"{expected}\", is not among the {n:,}: the collection is a "
                     "random sample of DBpedia. Any search, exact or HNSW, can only return the nearest articles "
                     "that exist, so the results are articles close in meaning.")
    lines.append("A document missing from the collection is a corpus problem, not an index problem: no search "
                 "setting brings it back. In RAG the same holds for your knowledge base.")
    explain("How to read the example", lines)


if __name__ == "__main__":
    main()
