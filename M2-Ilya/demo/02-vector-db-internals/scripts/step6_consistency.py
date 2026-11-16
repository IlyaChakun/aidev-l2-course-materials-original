"""Step 6. Write visibility: wait=false vs wait=true; deletes are tombstones until vacuum.

A. default collection:   wait=false -> "acknowledged" (WAL written, applied later), wait=true -> "completed".
B. prevent_unoptimized:  new points stay hidden ("deferred") until their segment is indexed, so the
                         gap between "accepted" and "searchable" becomes seconds and is easy to see.
C. delete:               points vanish from results at once, but stay in segments as deleted marks
                         until the vacuum optimizer rewrites the segment.
"""

import time

from qdrant_client import QdrantClient, models

from common import (C_CONSIST, DIM, QDRANT_GRPC_PORT, QDRANT_HOST, api, collection_exists, collection_info,
                    console, load_payloads, load_vectors, new_table, note, segments)

N = 5000
BATCH = 1000


def recreate(optimizers: dict | None = None) -> None:
    if collection_exists(C_CONSIST):
        api("DELETE", f"/collections/{C_CONSIST}")
    body = {"vectors": {"size": DIM, "distance": "Cosine"}}
    if optimizers:
        body["optimizers_config"] = optimizers
    api("PUT", f"/collections/{C_CONSIST}", body)


def exact_count() -> int:
    return api("POST", f"/collections/{C_CONSIST}/points/count", {"exact": True})["result"]["count"]


def last_point_found(vec) -> bool:
    r = api("POST", f"/collections/{C_CONSIST}/points/query",
            {"query": [float(x) for x in vec], "limit": 1, "params": {"exact": True}})
    pts = r["result"]["points"]
    return bool(pts) and pts[0]["id"] == N - 1


def send(client: QdrantClient, batches, wait: bool) -> tuple[float, str]:
    t0 = time.perf_counter()
    status = ""
    for pts in batches:
        res = client.upsert(C_CONSIST, wait=wait, points=pts)
        status = getattr(res.status, "value", res.status)
    return (time.perf_counter() - t0) * 1000, str(status).lower().split(".")[-1]


def poll(limit_s: float = 60) -> list[tuple[float, int]]:
    t0 = time.perf_counter()
    rows = [(0.0, exact_count())]
    while rows[-1][1] < N and time.perf_counter() - t0 < limit_s:
        time.sleep(0.2)
        rows.append(((time.perf_counter() - t0) * 1000, exact_count()))
    return rows


def timeline_table(title: str, rows) -> None:
    t = new_table(title, "ms after the response", "count (exact)", "not yet visible to search")
    shown = rows if len(rows) <= 8 else rows[:4] + rows[-3:]
    for ms_after, cnt in shown:
        t.add_row(f"{ms_after:,.0f}", f"{cnt:,}", f"{N - cnt:,}")
    console.print(t)
    if len(rows) > 8:
        note(f"(showing the first 4 and the last 3 of {len(rows)} measurements)")


def wait_idle(limit_s: float = 120) -> None:
    t0 = time.time()
    while time.time() - t0 < limit_s:
        if collection_info(C_CONSIST)["status"] == "green":
            return
        time.sleep(0.5)


def main() -> None:
    console.rule("Step 6 · When a write becomes visible; a delete is a mark")
    vectors = load_vectors()
    payloads = load_payloads()
    batches = [models.Batch(ids=list(range(s, s + BATCH)), vectors=vectors[s:s + BATCH].tolist(),
                            payloads=payloads[s:s + BATCH]) for s in range(0, N, BATCH)]
    last_vec = vectors[N - 1]
    client = QdrantClient(host=QDRANT_HOST, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=True, timeout=120)

    # A. Default settings
    t = new_table(f"A. Default settings: {N} points, {N // BATCH} requests of {BATCH}",
                  "mode", "server response", "send ms", "count right after", "last point is found")
    for wait in (False, True):
        recreate()
        send_ms, status = send(client, batches, wait)
        cnt, found = exact_count(), last_point_found(last_vec)
        t.add_row(f"wait={str(wait).lower()}", status, f"{send_ms:,.0f}", f"{cnt:,}", "yes" if found else "no")
    console.print(t)
    note("acknowledged = the write is accepted into the WAL and will be applied later; completed = applied. On an idle server "
         "the gap is milliseconds, under load (update queue, indexing) it is noticeably larger.")

    # B. prevent_unoptimized: new points are hidden until their segment is optimized
    recreate({"prevent_unoptimized": True})
    send_ms, status = send(client, batches, wait=False)
    timeline_table(f"B. prevent_unoptimized=true, wait=false: response \"{status}\" in {send_ms:,.0f} ms, "
                   "then we poll count", poll())
    recreate({"prevent_unoptimized": True})
    send_ms, status = send(client, batches, wait=True)
    note(f"The same experiment with wait=true: the response \"{status}\" comes only after {send_ms:,.0f} ms, count right after = "
         f"{exact_count():,}. The client waits until the points become visible.")
    note("Points in segments above indexing_threshold wait for indexing (deferred points) and are not visible "
         "to search until then. This makes \"accepted\" and \"searchable\" visibly different moments.")

    # C. Deletes are tombstones
    recreate()
    send(client, batches, wait=True)
    wait_idle()

    def seg_row(tt, label: str) -> None:
        info = collection_info(C_CONSIST)
        segs = [s for s in segments(C_CONSIST) if s["num_points"] or s["num_deleted_vectors"]]
        tt.add_row(label, f"{info['points_count']:,}", " + ".join(str(s["num_points"]) for s in segs),
                   " + ".join(str(s["num_deleted_vectors"]) for s in segs), info["status"])

    tt = new_table("C. Deleting 2,000 points out of 5,000", "moment", "points_count", "segments: live points",
                   "segments: deleted vectors (marks)", "status")
    seg_row(tt, "before delete")
    api("POST", f"/collections/{C_CONSIST}/points/delete", {"points": list(range(2000))}, params={"wait": "true"})
    seg_row(tt, "right after delete (wait=true)")
    time.sleep(1)
    wait_idle()
    time.sleep(1)
    seg_row(tt, "after the optimizer ran")
    console.print(tt)
    done = api("GET", f"/collections/{C_CONSIST}/optimizations",
               params={"with": "completed", "completed_limit": 10})["result"].get("completed", [])
    if done:
        note("Completed optimizations: " + ", ".join(d.get("optimizer", "?") for d in done))
    note("Deleted points vanish from results at once, but the space is freed by the vacuum optimizer when the share "
         "of deleted points in a segment > deleted_threshold (0.2) and the segment has >= vacuum_min_vector_number (1000).")
    api("DELETE", f"/collections/{C_CONSIST}")


if __name__ == "__main__":
    main()
