"""Download the DBpedia dataset with precomputed OpenAI embeddings and convert it.

Source: https://huggingface.co/datasets/Qdrant/dbpedia-entities-openai3-text-embedding-3-large-1536-100K
100K rows in 3 parquet shards (~318 MB each), columns: _id, title, text,
text-embedding-3-large-1536-embedding (float64 list).

Output (data/):
  vectors_f32.npy   N x 1536 float32 (points to load)
  payload.jsonl     one JSON per point: id, doc_id, title, text, category, year
  holdout_f32.npy   50 vectors that are NOT loaded (offline query fallback)
  holdout.json      their titles
The raw parquet shards are deleted afterwards unless --keep-raw is given.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import urllib.request

import numpy as np
import pyarrow.parquet as pq

from common import DATA, DIM, HOLDOUT_META_FILE, HOLDOUT_VEC_FILE, N_POINTS, PAYLOAD_FILE, VECTORS_FILE, console

REPO = "Qdrant/dbpedia-entities-openai3-text-embedding-3-large-1536-100K"
SHARDS = [f"data/train-0000{i}-of-00003.parquet" for i in range(3)]
ROWS_PER_SHARD = 33_333
HOLDOUT = 50
EMB_COL = "text-embedding-3-large-1536-embedding"

# Synthetic, skewed categorical field to demo filters (assigned at random,
# it does NOT reflect the entity's real topic). Think "department that owns the document".
CATEGORIES = {
    "sales": 0.50, "support": 0.20, "marketing": 0.12, "engineering": 0.08,
    "legal": 0.05, "finance": 0.03, "hr": 0.01, "security": 0.01,
}


def download(shard: str) -> None:
    dst = DATA / "raw" / shard.split("/")[-1]
    if dst.exists() and dst.stat().st_size > 100_000_000:
        console.print(f"cached  {dst.name} ({dst.stat().st_size / 1e6:.0f} MB)")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{shard}"
    console.print(f"download {url}")
    tmp = dst.with_suffix(".part")
    with urllib.request.urlopen(url) as r, tmp.open("wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)
    tmp.rename(dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-raw", action="store_true", help="keep parquet shards in data/raw")
    args = ap.parse_args()

    if VECTORS_FILE.exists():
        n = np.load(VECTORS_FILE, mmap_mode="r").shape[0]
        if n >= N_POINTS:
            console.print(f"data/vectors_f32.npy already has {n} points, nothing to do")
            return

    need_rows = min(N_POINTS + HOLDOUT, 100_000)
    shards = SHARDS[: math.ceil(need_rows / ROWS_PER_SHARD)]
    for s in shards:
        download(s)

    # Stream record batches into a preallocated float32 array: reading whole
    # float64 list columns at once needs several GB of RAM.
    files = [pq.ParquetFile(DATA / "raw" / s.split("/")[-1]) for s in shards]
    total = sum(f.metadata.num_rows for f in files)
    vectors = np.empty((total, DIM), dtype=np.float32)
    titles, texts, ids = [], [], []
    pos = 0
    for pf in files:
        for batch in pf.iter_batches(batch_size=2000, columns=["_id", "title", "text", EMB_COL]):
            emb = batch.column(EMB_COL)
            flat = emb.values.to_numpy(zero_copy_only=False)
            vectors[pos:pos + len(batch)] = flat.reshape(-1, DIM)
            pos += len(batch)
            ids += batch.column("_id").to_pylist()
            titles += batch.column("title").to_pylist()
            texts += batch.column("text").to_pylist()
    total = vectors.shape[0]
    n = min(N_POINTS, total - HOLDOUT)
    console.print(f"rows read: {total}, points to load: {n}, held-out queries: {HOLDOUT}")

    norms = np.linalg.norm(vectors[:1000], axis=1)
    console.print(f"vector norms (first 1000): min {norms.min():.4f}, max {norms.max():.4f}")

    rng = np.random.default_rng(42)
    cats = rng.choice(list(CATEGORIES), size=n, p=list(CATEGORIES.values()))
    years = np.arange(2000, 2026)
    w = np.linspace(1, 4, len(years))  # more recent years are more frequent
    yrs = rng.choice(years, size=n, p=w / w.sum())

    np.save(VECTORS_FILE, vectors[:n])
    with PAYLOAD_FILE.open("w") as f:
        for i in range(n):
            f.write(json.dumps({"id": i, "doc_id": ids[i], "title": titles[i], "text": texts[i],
                                "category": str(cats[i]), "year": int(yrs[i])}, ensure_ascii=False) + "\n")
    np.save(HOLDOUT_VEC_FILE, vectors[total - HOLDOUT:])
    HOLDOUT_META_FILE.write_text(json.dumps(
        [{"doc_id": ids[j], "title": titles[j]} for j in range(total - HOLDOUT, total)], ensure_ascii=False))

    counts = {c: int((cats == c).sum()) for c in CATEGORIES}
    console.print("category distribution: " + ", ".join(f"{c}={v} ({v / n:.1%})" for c, v in counts.items()))
    console.print(f"saved {VECTORS_FILE.name} ({VECTORS_FILE.stat().st_size / 1e6:.0f} MB), {PAYLOAD_FILE.name}")

    if not args.keep_raw:
        shutil.rmtree(DATA / "raw", ignore_errors=True)
        console.print("removed data/raw (parquet shards); use --keep-raw to keep them")


if __name__ == "__main__":
    main()
