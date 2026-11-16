"""Shared helpers: config, Qdrant REST/gRPC access, query vectors, recall, rich output."""

from __future__ import annotations

import hashlib
import json
import os
import random
import statistics
import time
from pathlib import Path

import httpx
import numpy as np
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / "cache"
DATA.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_HTTP_PORT = int(os.environ.get("QDRANT_HTTP_PORT", "6351"))
QDRANT_GRPC_PORT = int(os.environ.get("QDRANT_GRPC_PORT", "6352"))
BASE_URL = f"http://{QDRANT_HOST}:{QDRANT_HTTP_PORT}"
N_POINTS = int(os.environ.get("N_POINTS", "50000"))
DIM = 1536
EMBED_MODEL = "text-embedding-3-large"
TOP_K = 10

# Collection names used across the steps.
C_SMALL = "demo_small"          # step 1: below indexing threshold
C_MAIN = "demo_main"            # float32, m=16, no payload index
C_M4 = "demo_m4"                # float32, m=4
C_SQ = "demo_sq"                # scalar int8 quantization, originals on disk
C_BQ = "demo_bq"                # binary quantization, originals on disk
C_FILTER = "demo_filter"        # like demo_main + payload index created BEFORE upload
C_CONSIST = "demo_consistency"  # step 6 scratch collection

VECTORS_FILE = DATA / "vectors_f32.npy"
PAYLOAD_FILE = DATA / "payload.jsonl"
HOLDOUT_VEC_FILE = DATA / "holdout_f32.npy"
HOLDOUT_META_FILE = DATA / "holdout.json"
QUERY_CACHE = CACHE / "query_embeddings.json"
BUILD_STATS = CACHE / "build_stats.json"
QUERIES_FILE = Path(__file__).resolve().parent / "queries.txt"

console = Console(width=int(os.environ.get("COLUMNS", "120")))
http = httpx.Client(base_url=BASE_URL, timeout=120.0)


# ---------------------------------------------------------------- Qdrant REST

def api(method: str, path: str, body: dict | None = None, params: dict | None = None) -> dict:
    """Call the Qdrant REST API and return the parsed JSON (raises on HTTP errors)."""
    r = http.request(method, path, json=body, params=params)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:500]}")
    return r.json()


def collection_info(name: str) -> dict:
    return api("GET", f"/collections/{name}")["result"]


def collection_exists(name: str) -> bool:
    return api("GET", f"/collections/{name}/exists")["result"]["exists"]


def query(name: str, vector, limit: int = TOP_K, params: dict | None = None,
          flt: dict | None = None, with_payload=False) -> tuple[list, float, float]:
    """Run /points/query. Returns (points, server_ms, round_trip_ms).

    server_ms is the `time` Qdrant reports for the request (engine time),
    round_trip_ms includes HTTP and JSON on the client side.
    """
    body: dict = {"query": [float(x) for x in vector], "limit": limit, "with_payload": with_payload}
    if params:
        body["params"] = params
    if flt:
        body["filter"] = flt
    t0 = time.perf_counter()
    r = api("POST", f"/collections/{name}/points/query", body)
    rtt = (time.perf_counter() - t0) * 1000
    return r["result"]["points"], r["time"] * 1000, rtt


def ids_of(points: list) -> list:
    return [p["id"] for p in points]


def wait_green(name: str, expect_indexed: int | None = None, timeout: float = 1800, poll: float = 1.0) -> float:
    """Wait until the collection is green (optimizers idle). Returns seconds waited."""
    t0 = time.time()
    while True:
        info = collection_info(name)
        ok = info["status"] == "green" and info.get("update_queue", {}).get("length", 0) == 0
        if expect_indexed is not None:
            ok = ok and (info.get("indexed_vectors_count") or 0) >= expect_indexed
        if ok:
            return time.time() - t0
        if time.time() - t0 > timeout:
            raise TimeoutError(f"{name} not green after {timeout}s: {info['status']}")
        time.sleep(poll)


# ---------------------------------------------------------------- data

def load_vectors() -> np.ndarray:
    if not VECTORS_FILE.exists():
        raise SystemExit("No data/vectors_f32.npy. Run `make data` first.")
    return np.load(VECTORS_FILE, mmap_mode="r")


def load_payloads() -> list[dict]:
    with PAYLOAD_FILE.open() as f:
        return [json.loads(line) for line in f]


# ---------------------------------------------------------------- query vectors

def _cache_key(text: str) -> str:
    return hashlib.sha256(f"{EMBED_MODEL}|{DIM}|{text}".encode()).hexdigest()[:24]


def _read_cache() -> dict:
    if QUERY_CACHE.exists():
        return json.loads(QUERY_CACHE.read_text())
    return {}


def embed_queries(texts: list[str]) -> np.ndarray:
    """Embed texts with OpenAI (cached on disk; retries on 429/5xx with backoff)."""
    cache = _read_cache()
    missing = [t for t in texts if _cache_key(t) not in cache]
    if missing:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set and some queries are not cached")
        from openai import OpenAI, APIStatusError, RateLimitError, APIConnectionError

        client = OpenAI()
        for i in range(0, len(missing), 64):
            batch = missing[i:i + 64]
            for attempt in range(8):
                try:
                    resp = client.embeddings.create(model=EMBED_MODEL, input=batch, dimensions=DIM)
                    break
                except (RateLimitError, APIConnectionError) as e:
                    delay = min(60, 2 ** attempt) + random.random()
                    console.print(f"[yellow]OpenAI {type(e).__name__}, retry in {delay:.1f}s[/]")
                    time.sleep(delay)
                except APIStatusError as e:
                    if e.status_code >= 500:
                        time.sleep(min(60, 2 ** attempt) + random.random())
                        continue
                    raise
            else:
                raise RuntimeError("OpenAI embeddings: too many retries")
            for t, d in zip(batch, resp.data):
                cache[_cache_key(t)] = d.embedding
            QUERY_CACHE.write_text(json.dumps(cache))
    return np.array([cache[_cache_key(t)] for t in texts], dtype=np.float32)


def get_queries() -> tuple[list[str], np.ndarray, str]:
    """Return (labels, vectors, source).

    QUERY_SOURCE=auto (default): natural-language queries embedded with OpenAI
    (from cache if present); falls back to held-out dataset vectors when there is
    no key and no cache. QUERY_SOURCE=holdout forces the offline fallback.
    """
    source = os.environ.get("QUERY_SOURCE", "auto")
    texts = [line.strip() for line in QUERIES_FILE.read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    if source in ("auto", "openai"):
        try:
            return texts, embed_queries(texts), "openai"
        except RuntimeError as e:
            if source == "openai":
                raise
            console.print(f"[yellow]{e}; using held-out dataset vectors as queries[/]")
    vecs = np.load(HOLDOUT_VEC_FILE)
    labels = [m["title"] for m in json.loads(HOLDOUT_META_FILE.read_text())]
    return labels, vecs, "holdout"


# ---------------------------------------------------------------- metrics and output

def recall_at_k(found: list, truth: list, k: int = TOP_K) -> float:
    truth_k = set(truth[:k])
    if not truth_k:
        return 1.0
    return len(truth_k & set(found[:k])) / len(truth_k)


def pct(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    v = sorted(values)
    idx = min(len(v) - 1, max(0, int(round(p / 100 * (len(v) - 1)))))
    return v[idx]


def summarize(lat: list[float]) -> dict:
    return {"p50": pct(lat, 50), "p95": pct(lat, 95), "mean": statistics.fmean(lat) if lat else float("nan")}


def run_batch(name: str, vectors, params: dict | None = None, flt: dict | None = None,
              limit: int = TOP_K, warmup: bool = True) -> tuple[list[list], list[float], list[float]]:
    """Run all query vectors once (after an optional warm-up pass).

    Returns (id lists, server ms list, round-trip ms list)."""
    if warmup:
        # Warm the page cache: a full pass for ANN, a few queries for brute force (slow anyway).
        exact = bool(params and params.get("exact"))
        for v in (vectors[:5] if exact else vectors):
            query(name, v, limit, params, flt)
    all_ids, srv, rtt = [], [], []
    for v in vectors:
        pts, s, r = query(name, v, limit, params, flt)
        all_ids.append(ids_of(pts))
        srv.append(s)
        rtt.append(r)
    return all_ids, srv, rtt


def ground_truth(name: str, vectors, flt: dict | None = None, limit: int = TOP_K) -> list[list]:
    """Exact (brute force) top-k from Qdrant itself: params.exact=true."""
    ids, _, _ = run_batch(name, vectors, {"exact": True}, flt, limit, warmup=False)
    return ids


def mean_recall(found: list[list], truth: list[list], k: int = TOP_K) -> float:
    return statistics.fmean(recall_at_k(f, t, k) for f, t in zip(found, truth))


def new_table(title: str, *cols: str, justify_right_from: int = 1) -> Table:
    t = Table(title=title, title_justify="left", header_style="bold")
    for i, c in enumerate(cols):
        t.add_column(c, justify="right" if i >= justify_right_from else "left")
    return t


def ms(x: float) -> str:
    return f"{x:.1f}" if x >= 10 else f"{x:.2f}"


def mb(n_bytes: float) -> str:
    return f"{n_bytes / 1024 / 1024:,.0f} MB"


def note(text: str) -> None:
    console.print(f"[dim]{text}[/]")


def explain(title: str, lines: list[str]) -> None:
    """A short "how to read this" block printed under a table."""
    console.print(f"[bold cyan]{title}[/]")
    grid = Table.grid(padding=(0, 1))
    grid.add_column(width=3, justify="right")
    grid.add_column()
    for line in lines:
        grid.add_row("[cyan]·[/]", line)
    console.print(grid)
    console.print()


def load_build_stats() -> dict:
    return json.loads(BUILD_STATS.read_text()) if BUILD_STATS.exists() else {}


def save_build_stats(update: dict) -> None:
    stats = load_build_stats()
    stats.update(update)
    BUILD_STATS.write_text(json.dumps(stats, indent=2))


def segments(name: str) -> list[dict]:
    """Per-segment info from /telemetry (type plain/indexed, points, deleted vectors)."""
    tel = api("GET", "/telemetry", params={"details_level": 4})["result"]
    for c in tel["collections"]["collections"]:
        if c["id"] == name:
            out = []
            for shard in c["shards"]:
                for s in (shard.get("local") or {}).get("segments", []):
                    out.append(s["info"])
            return out
    return []
