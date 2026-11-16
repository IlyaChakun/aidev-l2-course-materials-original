"""Step 5. Payload filters: narrow (1%) and broad (50%), with and without a payload index; ACORN."""

import statistics

from common import (C_FILTER, C_MAIN, api, collection_exists, collection_info, console, get_queries,
                    ground_truth, mean_recall, ms, new_table, note, query, run_batch, summarize)


def match(field, value):
    return {"key": field, "match": {"value": value}}


FILTERS = [
    ("narrow: category = hr", {"must": [match("category", "hr")]}),
    ("broad: category = sales", {"must": [match("category", "sales")]}),
    ("two conditions: category in (support, marketing) and year >= 2021",
     {"must": [{"key": "category", "match": {"any": ["support", "marketing"]}},
               {"key": "year", "range": {"gte": 2021}}]}),
]


def count(name: str, flt: dict) -> int:
    return api("POST", f"/collections/{name}/points/count", {"filter": flt, "exact": True})["result"]["count"]


def main() -> None:
    labels, qv, source = get_queries()
    n = collection_info(C_MAIN)["points_count"]
    console.rule("Step 5 · Payload filters")
    has_filter_coll = collection_exists(C_FILTER)
    if has_filter_coll:
        schema = collection_info(C_FILTER)["payload_schema"]
        note(f"{C_FILTER}: payload indexes " + ", ".join(f"{k} ({v['data_type']}, {v.get('points', '?')} points)"
                                                        for k, v in schema.items()) +
             f" created before loading; {C_MAIN} has no payload indexes.")

    t = new_table(f"{len(qv)} queries ({source}), limit=10, ground truth - exact with the same filter",
                  "filter", "share of points", "mode", "found (of 10)", "recall@10", "p50 ms")
    t.columns[2].justify = "left"
    for label, flt in FILTERS:
        sel = count(C_MAIN, flt) / n
        truth = ground_truth(C_MAIN, qv, flt)
        first = True

        def row(mode: str, found_avg: float, recall: float | None, p50: float | None) -> None:
            nonlocal first
            t.add_row(label if first else "", f"{sel:.1%}" if first else "", mode, f"{found_avg:.1f}",
                      "-" if recall is None else f"{recall:.3f}", "-" if p50 is None else ms(p50))
            first = False

        # Naive post-filtering on the client: take top-10 without filter, then drop non-matching.
        # Same filter evaluated by Qdrant via count over the returned ids.
        kept = []
        for v in qv:
            pts, _, _ = query(C_MAIN, v, 10)
            ids = [p["id"] for p in pts]
            kept.append(count(C_MAIN, {"must": [*flt["must"], {"has_id": ids}]}))
        row("post-filter after top-10", statistics.fmean(kept), None, None)

        for name, mode, params in ((C_MAIN, "no payload index", None),
                                   (C_FILTER, "with payload index", None),
                                   (C_FILTER, "with index + acorn", {"acorn": {"enable": True}})):
            if name == C_FILTER and not has_filter_coll:
                continue
            ids, srv, _ = run_batch(name, qv, params, flt)
            row(mode, statistics.fmean(len(x) for x in ids), mean_recall(ids, truth), summarize(srv)["p50"])
        t.add_section()
    console.print(t)
    note(f"no payload index = {C_MAIN}; with index = {C_FILTER}. Time is server-side. Post-filter: how many of the "
         "unfiltered top-10 pass the filter - this is how results get lost when filtering after the search.")
    note("Without an index Qdrant cannot cheaply estimate how many points will pass the filter, and checks the condition against the payload "
         "on disk - a narrow filter costs tens of ms, and a compound one returns incomplete results.")
    note("The Qdrant planner uses the payload index to estimate how many points will pass the filter. Few (below "
         "full_scan_threshold, 10,000 KB ~ 1,666 vectors of 1536) - it takes the points from the index and scans them by brute force. "
         "Many - it walks the HNSW graph and checks the filter on the fly (filterable HNSW).")
    note("A payload index created before the HNSW build gives the graph extra links within each field value - "
         "that is why indexes are created right after the collection, before loading. Links are built per field, "
         "not per combination - for compound filters there is ACORN (Qdrant 1.16+): during traversal it also looks at the neighbors "
         "of neighbors. Enabled in the query with acorn.enable, works when the share of points is below max_selectivity (0.4).")


if __name__ == "__main__":
    main()
