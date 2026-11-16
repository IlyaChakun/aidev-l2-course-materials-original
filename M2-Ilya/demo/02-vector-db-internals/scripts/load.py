"""Create the demo collections and load the dataset.

Bulk-upload pattern from the Qdrant docs: create the collection with
indexing_threshold=0 (no HNSW while uploading), upload over gRPC, then switch
indexing on and time how long the optimizer needs to build HNSW.

Usage: python scripts/load.py [--only demo_main,demo_m4] [--force]
"""

from __future__ import annotations

import argparse
import time

from qdrant_client import QdrantClient

from common import (C_BQ, C_FILTER, C_M4, C_MAIN, C_SMALL, C_SQ, DIM, QDRANT_GRPC_PORT, QDRANT_HOST,
                    api, collection_exists, collection_info, console, load_payloads, load_vectors,
                    new_table, save_build_stats, wait_green)

INDEXING_THRESHOLD_KB = 10_000  # value shipped in the qdrant/qdrant:v1.19.2 image config.yaml

BASE_VECTORS = {"size": DIM, "distance": "Cosine"}

# name -> (collection body, payload indexes created BEFORE upload, number of points or None for all)
SPECS: dict[str, tuple[dict, dict, int | None]] = {
    C_SMALL: ({"vectors": BASE_VECTORS}, {}, 1000),
    C_MAIN: ({"vectors": BASE_VECTORS, "hnsw_config": {"m": 16, "ef_construct": 100}}, {}, None),
    C_M4: ({"vectors": BASE_VECTORS, "hnsw_config": {"m": 4, "ef_construct": 100}}, {}, None),
    C_SQ: ({"vectors": {**BASE_VECTORS, "memory": "cold"},  # originals stay on disk
            "quantization_config": {"scalar": {"type": "int8", "quantile": 0.99, "memory": "pinned"}}},
           {}, None),
    C_BQ: ({"vectors": {**BASE_VECTORS, "memory": "cold"},
            "quantization_config": {"binary": {"memory": "pinned"}}},
           {}, None),
    C_FILTER: ({"vectors": BASE_VECTORS, "hnsw_config": {"m": 16, "ef_construct": 100}},
               {"category": "keyword", "year": "integer"}, None),
}


def create_and_load(name: str, client: QdrantClient, vectors, payloads, force: bool) -> None:
    body, indexes, limit = SPECS[name]
    n = limit or len(vectors)
    if collection_exists(name):
        info = collection_info(name)
        if not force and info["points_count"] == n and info["status"] == "green":
            console.print(f"{name}: already loaded ({n} points), skip")
            return
        api("DELETE", f"/collections/{name}")

    small = name == C_SMALL
    create = dict(body)
    if not small:
        create["optimizers_config"] = {"indexing_threshold": 0}  # no HNSW during upload
    api("PUT", f"/collections/{name}", create)
    for field, schema in indexes.items():
        api("PUT", f"/collections/{name}/index", {"field_name": field, "field_schema": schema}, params={"wait": "true"})

    t0 = time.time()
    client.upload_collection(
        collection_name=name,
        vectors=vectors[:n],
        payload=payloads[:n],
        ids=list(range(n)),
        batch_size=256,
        parallel=1,
        wait=True,
    )
    upload_s = time.time() - t0
    console.print(f"{name}: uploaded {n} points in {upload_s:.1f}s")

    build_s = 0.0
    if not small:
        api("PATCH", f"/collections/{name}", {"optimizers_config": {"indexing_threshold": INDEXING_THRESHOLD_KB}})
        time.sleep(1)
        build_s = wait_green(name, expect_indexed=n)
        console.print(f"{name}: HNSW built in {build_s:.1f}s")
    else:
        wait_green(name)
    info = collection_info(name)
    save_build_stats({name: {"points": n, "upload_s": round(upload_s, 1), "build_s": round(build_s, 1),
                             "segments": info["segments_count"],
                             "indexed_vectors_count": info["indexed_vectors_count"]}})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated collection names")
    ap.add_argument("--force", action="store_true", help="recreate even if already loaded")
    args = ap.parse_args()
    names = [n for n in SPECS if not args.only or n in args.only.split(",")]

    vectors = load_vectors()
    payloads = load_payloads()
    client = QdrantClient(host=QDRANT_HOST, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=True, timeout=300)
    for name in names:
        create_and_load(name, client, vectors, payloads, args.force)

    t = new_table("Demo collections", "collection", "points", "indexed", "segments", "status", "upload s", "build s")
    from common import load_build_stats
    stats = load_build_stats()
    for name in SPECS:
        if not collection_exists(name):
            continue
        info = collection_info(name)
        st = stats.get(name, {})
        t.add_row(name, str(info["points_count"]), str(info["indexed_vectors_count"]), str(info["segments_count"]),
                  info["status"], str(st.get("upload_s", "-")), str(st.get("build_s", "-")))
    console.print(t)


if __name__ == "__main__":
    main()
