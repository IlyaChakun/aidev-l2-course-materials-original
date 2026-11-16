"""Step 1. On homework-size data ANN does not kick in: no HNSW, search is a full scan."""

from common import (C_MAIN, C_SMALL, DIM, collection_exists, collection_info, console, get_queries,
                    mean_recall, ms, new_table, note, run_batch, segments, summarize)


def main() -> None:
    labels, qv, source = get_queries()
    console.rule("Step 1 · Small collection: HNSW is not built")

    t = new_table("Collection info (GET /collections/{name})",
                  "collection", "points", "vectors KB", "indexing_threshold KB", "indexed_vectors_count",
                  "segments", "status")
    for name in (C_SMALL, C_MAIN):
        if not collection_exists(name):
            continue
        info = collection_info(name)
        n = info["points_count"]
        kb = n * DIM * 4 / 1024
        thr = info["config"]["optimizer_config"]["indexing_threshold"]
        t.add_row(name, f"{n:,}", f"{kb:,.0f}", f"{thr:,}", f"{info['indexed_vectors_count']:,}",
                  str(info["segments_count"]), info["status"])
    console.print(t)
    t_seg = new_table("Segments (GET /telemetry): each has its own index", "collection", "segment",
                      "type", "points", "indexed vectors")
    for name in (C_SMALL, C_MAIN):
        for seg in segments(name):
            t_seg.add_row(name, seg["uuid"][:8], seg["segment_type"], f"{seg['num_points']:,}",
                          f"{seg['num_indexed_vectors']:,}")
    console.print(t_seg)
    per_segment = 10_000 * 1024 // (DIM * 4)
    note(f"The indexing_threshold is counted per segment: 10,000 KB / ({DIM} x 4 bytes) ~ {per_segment:,} vectors "
         "per segment. Below the threshold the segment stays plain - search is a brute-force scan.")
    note("For comparison: the homework - 190 chunks x 1024 dimensions x 4 bytes ~ 760 KB, 13 times below the threshold.")

    exact_ids, exact_srv, _ = run_batch(C_SMALL, qv, {"exact": True})
    def_ids, def_srv, _ = run_batch(C_SMALL, qv)
    t2 = new_table(f"{C_SMALL}: {len(qv)} queries ({source}), top-10",
                   "mode", "p50 ms", "p95 ms", "recall@10 vs exact")
    for label, ids, srv in (("exact=true (brute force)", exact_ids, exact_srv), ("default", def_ids, def_srv)):
        s = summarize(srv)
        t2.add_row(label, ms(s["p50"]), ms(s["p95"]), f"{mean_recall(ids, exact_ids):.3f}")
    console.print(t2)
    note("Time is server-side (the time field in the Qdrant response). The results match: on a small collection "
         "\"default\" is the exact brute-force scan, there is no approximation.")


if __name__ == "__main__":
    main()
