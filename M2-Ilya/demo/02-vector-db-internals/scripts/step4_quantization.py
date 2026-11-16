"""Step 4. Quantization: scalar int8 and binary; recall with/without rescoring, RAM estimate."""

from common import (C_BQ, C_MAIN, C_SQ, DIM, collection_exists, collection_info, console, get_queries,
                    ground_truth, mb, mean_recall, ms, new_table, note, run_batch, summarize)

CASES = [
    # collection, label, search params, bytes per vector of the in-RAM copy
    (C_MAIN, "float32, no quantization", None, DIM * 4),
    (C_SQ, "int8, no rescore", {"quantization": {"rescore": False}}, DIM),
    (C_SQ, "int8, rescore", {"quantization": {"rescore": True, "oversampling": 1.0}}, DIM),
    (C_SQ, "int8, rescore + oversampling 2", {"quantization": {"rescore": True, "oversampling": 2.0}}, DIM),
    (C_BQ, "binary, no rescore", {"quantization": {"rescore": False}}, DIM / 8),
    (C_BQ, "binary, rescore", {"quantization": {"rescore": True, "oversampling": 1.0}}, DIM / 8),
    (C_BQ, "binary, rescore + oversampling 3", {"quantization": {"rescore": True, "oversampling": 3.0}}, DIM / 8),
]


def main() -> None:
    labels, qv, source = get_queries()
    n = collection_info(C_MAIN)["points_count"]
    console.rule(f"Step 4 · Quantization on {n:,} points x {DIM} dimensions")
    truth = ground_truth(C_MAIN, qv)  # exact search over original float32 vectors

    t = new_table(f"{len(qv)} queries ({source}), top-10, ground truth - exact over float32",
                  "variant", "vectors in RAM", "compression", "recall@10", "server p50 ms", "server p95 ms")
    for name, label, params, bpv in CASES:
        if not collection_exists(name):
            t.add_row(label, "-", "-", "no collection", "-", "-")
            continue
        ids, srv, _ = run_batch(name, qv, params)
        s = summarize(srv)
        t.add_row(label, mb(n * bpv), f"x{DIM * 4 / bpv:.0f}", f"{mean_recall(ids, truth):.3f}",
                  ms(s["p50"]), ms(s["p95"]))
    console.print(t)
    note(f"RAM: float32 originals = N x d x 4 = {mb(n * DIM * 4)}; int8 = N x d = {mb(n * DIM)}; "
         f"binary = N x d / 8 = {mb(n * DIM / 8)}. The HNSW graph and payload are not included.")
    note(f"In {C_SQ} and {C_BQ} the originals live on disk (memory: cold), only the compressed copy is pinned in RAM "
         "(memory: pinned). Rescore re-reads the originals from disk only for the top candidates.")
    note("rescore without oversampling only re-scores and reorders the same 10 candidates - the set, and hence "
         "recall@10, does not change. Oversampling brings recall back: more candidates to re-score.")
    note("oversampling 3 = fetch 30 candidates by the compressed vectors, re-score them against the originals, return 10.")


if __name__ == "__main__":
    main()
