"""Step 3. HNSW knobs: hnsw_ef at query time, m at build time."""

from common import (C_M4, C_MAIN, collection_exists, collection_info, console, get_queries, ground_truth,
                    load_build_stats, mb, mean_recall, ms, new_table, note, run_batch, summarize)

EF_VALUES = [8, 16, 32, 64, 100, 128, 256, 512]


def main() -> None:
    labels, qv, source = get_queries()
    console.rule("Step 3 · HNSW knobs: hnsw_ef (at query time) and m (at build time)")
    truth = ground_truth(C_MAIN, qv)

    t = new_table(f"{C_MAIN} (m=16, ef_construct=100): {len(qv)} queries ({source}), top-10",
                  "hnsw_ef", "recall@10", "server p50 ms", "server p95 ms")
    default_ids, srv, _ = run_batch(C_MAIN, qv)
    s = summarize(srv)
    t.add_row("not set", f"{mean_recall(default_ids, truth):.3f}", ms(s["p50"]), ms(s["p95"]))
    by_ef = {}
    for ef in EF_VALUES:
        ids, srv, _ = run_batch(C_MAIN, qv, {"hnsw_ef": ef})
        by_ef[ef] = ids
        s = summarize(srv)
        t.add_row(str(ef), f"{mean_recall(ids, truth):.3f}", ms(s["p50"]), ms(s["p95"]))
    console.print(t)
    same = sum(a == b for a, b in zip(default_ids, by_ef[100]))
    note(f"Without hnsw_ef the results matched hnsw_ef=100 (= ef_construct) in {same} of {len(qv)} queries. "
         "An ef below limit=10 makes no sense: there must be at least as many candidates as we ask for.")

    if not collection_exists(C_M4):
        note(f"{C_M4} is not loaded - the m comparison is skipped (make load).")
        return
    stats = load_build_stats()
    truth_m4 = truth  # same points and vectors, so the exact answer is the same
    t2 = new_table("m=4 vs m=16 (the same 50,000 points)", "collection", "m", "build s",
                   "graph*", "recall ef=16", "recall ef=64", "recall ef=128", "p50 ms ef=64")
    for name in (C_M4, C_MAIN):
        info = collection_info(name)
        m = info["config"]["hnsw_config"]["m"]
        n = info["points_count"]
        recalls, p50 = [], 0.0
        for ef in (16, 64, 128):
            ids, srv, _ = run_batch(name, qv, {"hnsw_ef": ef})
            recalls.append(f"{mean_recall(ids, truth_m4):.3f}")
            if ef == 64:
                p50 = summarize(srv)["p50"]
        t2.add_row(name, str(m), str(stats.get(name, {}).get("build_s", "-")), mb(n * m * 2 * 4 * 1.2),
                   *recalls, ms(p50))
    console.print(t2)
    note("* graph ~ N x m x 2 x 4 bytes x 1.2 (capacity planning formula). build s - HNSW build time "
         "during make load, depends on the machine load.")
    note("m - the number of links per node: larger m - denser graph, higher recall, longer build and more memory. "
         "ef - search width: tuned on every query without rebuilding the index.")


if __name__ == "__main__":
    main()
