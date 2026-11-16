# RUNBOOK · Demo 02 "What happens inside a vector DB"

Vectors chapter of the M2 lecture (deck of 12.11.2026): step 2 is an optional live demo on slide 34, cut first; the numbers of steps 3–7 are on slides 33 and 35 and in appendix slides 82–85 and 101. The output below is a real run of 2026-11-01 on a MacBook (10 cores, Docker VM 8 GB, Qdrant limited to `cpus: 4`, `mem_limit: 3g`), 50,000 points, 50 queries via OpenAI. The milliseconds on your run will differ, the ratios will be the same.

## Preparation before the lecture (30 minutes ahead, the work itself ~15–20 minutes)

```bash
cd M2-Ilya/demo/02-vector-db-internals
cp .env.example .env     # fill in OPENAI_API_KEY; or export OPENAI_API_KEY=... in the current shell
make prep                # up + build + data + embed + load
make all                 # rehearsal run, ~2-3 min
```

| `make prep` stage | Time on the run | What happens |
|---|---|---|
| `up`, `build` | ~30 s | Qdrant v1.19.2 on 6351/6352, image `m2-demo-vector-db-runner:1` |
| `data` | 1–2 min | 2 parquet shards (~640 MB) → `data/vectors_f32.npy` (307 MB) + `data/payload.jsonl`; the parquet is deleted |
| `embed` | ~3 s | 50 queries → `cache/query_embeddings.json` (one OpenAI call); on repeat - from the cache |
| `load` | 5–12 min | 6 collections; HNSW: m=16 - 102 s, m=4 - 34 s, int8 - 19 s, binary - 8 s, with a payload index - up to 6 min under load |

Readiness check: `make status` - 6 `demo_*` collections; in the dashboard `http://localhost:6351/dashboard` all of them have status green. Before going to the screen: close heavy applications, terminal at least 120 columns wide, large font.

If the demo machine has no internet: `data/` and `cache/` survive `make down`, only `make up load` is needed (no network, ~10 min).

## Step 1 · Small collection: HNSW is not built

**Command:** `make step1`

**Expected output (abridged):**
```
Collection info (GET /collections/{name})
│ collection │ points │ vectors KB │ indexing_threshold KB │ indexed_vectors_count │ segments │ status │
│ demo_small │  1,000 │      6,000 │                10,000 │                     0 │        2 │  green │
│ demo_main  │ 50,000 │    300,000 │                10,000 │                50,000 │        2 │  green │
Segments (GET /telemetry)
│ demo_small │ 06392eed │   plain │    512 │      0 │
│ demo_small │ 48dbe9a5 │   plain │    488 │      0 │
│ demo_main  │ 8f1c1f5a │ indexed │ 50,000 │ 50,000 │
The indexing_threshold is counted per segment: 10,000 KB / (1536 x 4 bytes) ~ 1,666 vectors per segment.
For comparison: the homework - 190 chunks x 1024 dimensions x 4 bytes ~ 760 KB, 13 times below the threshold.
│ exact=true (brute force) │   1.14 │   1.25 │ 1.000 │
│ default                  │   1.13 │   1.32 │ 1.000 │
```

**What to say:** "While there are fewer vectors than the threshold, Qdrant does not even build HNSW: `indexed_vectors_count = 0`, the segments are plain, any search is an honest brute-force scan. Your homework with 190 chunks is 13 times below the threshold, so index tuning is not needed in the homework."

**Watch for:** the 10,000 KB threshold comes from the `config.yaml` of the 1.19.2 image; the OpenAPI says "default 20,000" (the value in the code), but the image sets 10,000 - look at `config.optimizer_config.indexing_threshold` in the output.

**What it proves:** approximate search kicks in only at scale; on small data it does not take part.

**Fallback:** show this block from the RUNBOOK or dashboard → `demo_small` → Info.

## Step 2 · Brute force vs HNSW on 50,000 points

**Command:** `make step2`

**Expected output** (run of 15.11.2026, abridged; every table is followed by a "How to read" block):
```
50,000 Wikipedia articles (DBpedia), one OpenAI vector of 1,536 numbers each. The same 50 questions run twice: ...
│ mode                                     │ server p50 ms │ server p95 ms │ round-trip p50 ms │ recall@10 │
│ exact=true (brute force over all points) │          93.6 │         106.1 │              95.9 │     1.000 │
│ HNSW (m=16, default ef)                  │          4.10 │          4.83 │              5.82 │     0.998 │
HNSW is about 23x faster than brute force on 50,000 points. Brute force grows linearly: on 1M points ~1,872 ms, ...
How to read the first table: speed against exactness
  · exact=true is brute force ... the reference, but its time grows with the collection ...
  · HNSW walks a graph of near neighbours ... 23 times faster (4.10 ms), and it returned 99.8% of the exact top 10.
  · p50 is the median query, p95 the slow tail ...
  · recall@10 here = how many of the exact top 10 HNSW also returned. It is not the homework's recall@5 ...
Queries where HNSW missed something: 1 of 50
│ television series about a chemistry teacher making drugs │ 0.9 │ 1 │
How to read the second table: where the index lost something
  · "television series about a chemistry teacher making drugs": 9 of 10 found; it missed the article brute force
    put at position 1, the best answer itself.
Example: "physicist who developed the theory of relativity" (top-5)
│ 1 │ Paul Ehrenfest │ 0.471 │ Paul Ehrenfest │ 0.471 │
...
How to read the example
  · Both columns are the same five articles in the same order ...
  · The article you would expect, "Albert Einstein", is not among the 50,000: the collection is a random sample ...
  · A document missing from the collection is a corpus problem, not an index problem ...
```

**What to say:** "Brute force is the reference: exact, but the time grows linearly with the number of points. HNSW is 20 times faster and found 499 of 500 correct answers. That is what 'approximate' means: sometimes it loses even the first result - here is a query where position 1 was missed."

**Watch for:** the timings are sensitive to the laptop: under parallel load (other containers, indexing) HNSW showed 10–12 ms and once, on 15.11.2026, even 44–58 ms (2–3x instead of 20–24x); the next runs were back to 4 ms. If HNSW shows tens of ms, run the step again; recall@10 does not change. The corpus is 50,000 random DBpedia articles, Einstein is not in it, so the top for physics is Ehrenfest; that is normal, and someone may ask about it.

**What it proves:** exact search does not scale; HNSW trades a tiny share of recall for an order of magnitude of speed.

**Fallback:** show the table from here; if the question is "what is recall" - it is the share of the exact top-10 that HNSW found.

## Step 3 · HNSW knobs: hnsw_ef and m

**Command:** `make step3`

**Expected output:**
```
│ hnsw_ef  │ recall@10 │ server p50 ms │ server p95 ms │
│ not set  │     0.998 │          4.00 │          4.71 │
│ 8        │     0.896 │          0.94 │          1.39 │
│ 16       │     0.964 │          1.17 │          1.43 │
│ 32       │     0.986 │          1.84 │          3.64 │
│ 64       │     0.996 │          2.98 │          3.39 │
│ 100      │     0.998 │          4.22 │          4.97 │
│ 128      │     1.000 │          5.67 │          6.74 │
│ 256      │     1.000 │          8.46 │          9.85 │
│ 512      │     1.000 │          14.8 │          19.0 │
Without hnsw_ef the results matched hnsw_ef=100 (= ef_construct) in 50 of 50 queries.
m=4 vs m=16
│ collection │  m │ build s │ graph* │ recall ef=16 │ recall ef=64 │ recall ef=128 │ p50 ms ef=64 │
│ demo_m4    │  4 │    34.1 │   2 MB │        0.650 │        0.912 │         0.940 │         1.12 │
│ demo_main  │ 16 │   102.3 │   7 MB │        0.964 │        0.996 │         1.000 │         2.79 │
```

**What to say:** "`hnsw_ef` is the search width, turned on every query: from 0.90 to 1.00 recall while the time grows 15 times. By default ef = ef_construct = 100. `m` is set at build time: a graph with 4 links builds three times faster, but even with a large ef it does not reach 0.95 - what was lost at build time cannot be recovered by search."

**Watch for:** `build s` is taken from `cache/build_stats.json` (measured during `make load`) and depends on the laptop's load; with parallel containers m=16 took as long as 197 s to build. The first queries to a "cold" collection are slower - the script does a warm-up pass.

**What it proves:** the three HNSW knobs (m, ef_construct, hnsw_ef) trade speed and memory for recall.

**Fallback:** the table from here; verbally: "ef 8 → 512: recall 0.90 → 1.00, time 1 → 15 ms".

## Step 4 · Quantization

**Command:** `make step4`

**Expected output:**
```
│ variant                          │ vectors in RAM │ compression │ recall@10 │ server p50 ms │ server p95 ms │
│ float32, no quantization         │         293 MB │          x1 │     0.998 │          4.14 │          4.64 │
│ int8, no rescore                 │          73 MB │          x4 │     0.976 │          0.80 │          0.89 │
│ int8, rescore                    │          73 MB │          x4 │     0.976 │          0.79 │          1.07 │
│ int8, rescore + oversampling 2   │          73 MB │          x4 │     0.996 │          0.77 │          0.96 │
│ binary, no rescore               │           9 MB │         x32 │     0.696 │          0.28 │          0.34 │
│ binary, rescore                  │           9 MB │         x32 │     0.696 │          0.33 │          0.38 │
│ binary, rescore + oversampling 3 │           9 MB │         x32 │     0.958 │          0.37 │          0.45 │
```

**What to say:** "int8 - 4 times less memory and almost no loss; binary - 32 times, but on its own it loses a third of the answers. Accuracy is brought back not by rescore alone but by oversampling: we fetch three times more candidates by the compressed vectors and re-score them against the originals, which live on disk."

**Watch for:** the "no rescore" rows and the "rescore" rows with oversampling 1 give the same recall - this is not a bug: rescore reorders the same 10 candidates, the set does not change. The quantized variants are also faster than float32 because HNSW walks over the compressed vectors. Binary works well specifically with `text-embedding-3-large`; on other models it may be worse - say "check on your own model".

**What it proves:** quantization is memory vs accuracy; rescoring with oversampling brings accuracy back, and the originals on disk are needed precisely for it.

**Fallback:** the table from here.

## Step 5 · Payload filters

**Command:** `make step5`

**Expected output:**
```
demo_filter: payload indexes category (keyword), year (integer) created before loading; demo_main has no payload indexes.
│ filter                       │ share of points │ mode                     │ found (of 10) │ recall@10 │ p50 ms │
│ narrow: category = hr        │            0.9% │ post-filter after top-10 │           0.1 │         - │      - │
│                              │                 │ no payload index         │          10.0 │     1.000 │   72.6 │
│                              │                 │ with payload index       │          10.0 │     1.000 │   1.08 │
│                              │                 │ with index + acorn       │          10.0 │     1.000 │   1.11 │
│ broad: category = sales      │           49.6% │ post-filter after top-10 │           4.7 │         - │      - │
│                              │                 │ no payload index         │          10.0 │     0.978 │   7.63 │
│                              │                 │ with payload index       │          10.0 │     0.990 │   5.30 │
│                              │                 │ with index + acorn       │          10.0 │     0.990 │   5.33 │
│ two conditions: category in  │            9.2% │ post-filter after top-10 │           0.9 │         - │      - │
│ (support, marketing) and     │                 │ no payload index         │           6.2 │     0.226 │   7.25 │
│ year >= 2021                 │                 │ with payload index       │          10.0 │     0.946 │   2.69 │
│                              │                 │ with index + acorn       │          10.0 │     1.000 │   13.9 │
```

**What to say:** "Filter after the search: we asked for 10 documents of the hr department - we got 0.1 on average. That is why the filter is part of the search. Without a payload index a narrow filter is 70 times slower, and a compound one returns only 6 of 10, and the wrong ones. With an index the planner chooses by itself: for a narrow filter - fetch the points via the index and scan them by brute force, for a broad one - walk the graph and check the filter on the fly. For compound filters there is ACORN: it brings recall to 1.0 at the cost of time."

**Watch for:** `category` is a synthetic field, assigned randomly (not the article topic); say so if asked. ACORN is switched on by the query parameter `params.acorn.enable` (available since Qdrant 1.16, verified on 1.19.2); on the narrow and broad filters it changes nothing - this is expected. Access rights are the same filter: a bridge to the tenant slides in the Production chapter.

**What it proves:** post-filtering loses results; the payload index must exist before loading (otherwise there are no extra links in the graph); the planner chooses the strategy from the estimated share of points.

**Fallback:** the table from here.

## Step 6 · When a write is visible, a delete is a mark

**Command:** `make step6` (~20 s, the `demo_consistency` collection is created and deleted by the step itself)

**Expected output:**
```
A. Default settings: 5000 points, 5 requests of 1000
│ wait=false │ acknowledged │ 764 │ 4,256 │ no  │
│ wait=true  │    completed │ 729 │ 5,000 │ yes │
B. prevent_unoptimized=true, wait=false: response "acknowledged" in 479 ms, then we poll count
│ ms after the response │ count (exact) │ not yet visible to search │
│ 0                     │         3,494 │                     1,506 │
│ 202                   │         4,334 │                       666 │
│ 4,894                 │         4,334 │                       666 │
│ 5,097                 │         5,000 │                         0 │
The same experiment with wait=true: the response "completed" comes only after 5,794 ms, count right after = 5,000.
C. Deleting 2,000 points out of 5,000
│ before delete                    │ 5,000 │ 1000 + 4000 │ 0 + 0    │ green  │
│ right after delete (wait=true)   │ 3,000 │ 1000 + 2000 │ 0 + 2000 │ yellow │
│ after the optimizer ran          │ 3,000 │ 1000 + 2000 │ 0 + 0    │ green  │
Completed optimizations: vacuum, indexing
```

**What to say:** "`wait=false` - the server answered 'accepted', but search does not see these points yet. In the homework ingestion script you compute recall right after loading - set `wait=true`, otherwise you are measuring a half-empty database. A delete instantly removes points from the results, but physically it is a mark, and the vacuum optimizer frees the space."

**Watch for:** in part A the gap depends on load: on an idle machine `count` right after `wait=false` may already show 5,000 - then rely on part B, where the gap is stably seconds. `prevent_unoptimized` is a Qdrant 1.19 optimizer option (new points are hidden until their segment is indexed), not a default.

**What it proves:** a write being "accepted" and being "searchable" are different moments; a delete is a tombstone until vacuum.

**Fallback:** the table from here.

## Step 7 · How much memory is needed

**Command:** `make step7` (no Qdrant, instant)

**Expected output:**
```
GiB for the whole cluster (x2 replicas), without payload
│ points │ dims │ float32 │ int8 │ binary │ HNSW │ RAM: all float32 │ RAM: int8 + HNSW │ RAM: binary + HNSW │ disk: originals │
│ 1M     │ 1024 │     7.6 │  1.9 │    0.2 │  0.3 │              9.5 │              2.6 │                0.6 │             7.6 │
│ 1M     │ 1536 │    11.4 │  2.9 │    0.4 │  0.3 │             14.1 │              3.8 │                0.8 │            11.4 │
│ 10M    │ 1024 │    76.3 │ 19.1 │    2.4 │  2.9 │             95.0 │             26.3 │                6.3 │            76.3 │
│ 10M    │ 1536 │   114.4 │ 28.6 │    3.6 │  2.9 │            140.8 │             37.8 │                7.7 │           114.4 │
```

**What to say:** "10 million chunks at 1536 dimensions with two replicas - 140 GiB of RAM if everything is kept in float32. With int8 - 38, with binary - 8, and the originals go to disk. That is why quantization is not an optimization but a budget question."

**Watch for:** the formulas come from the Qdrant capacity planning page; payload, the ID tracker and WAL are not counted. Parameters are changed via the environment: `REPLICATION_FACTOR=3 HNSW_M=32 make step7`.

**What it proves:** sizing is calculated in advance and determines the choice of quantization and hardware.

**Fallback:** the table from here.

## After the lecture

```bash
make down      # stop the containers, remove the Qdrant volume (data/ and cache/ stay for next time)
make clean     # plus remove data/ (~330 MB) and cache/
```

## Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| `make data` silently fails or exit 137 | The container ran out of memory | The conversion is already streaming (batches of 2,000 rows); check the demo `mem_limit` (2g) and the free memory of Docker |
| A step hangs on `wait_green`, in `/collections/<name>/optimizations` the status is `wait_cpu_permit` | The optimizer is waiting for CPU: HNSW of another collection is being built | Wait for `make load` to finish; do not run steps in parallel with loading |
| `OPENAI_API_KEY is not set ...; using held-out dataset vectors` | No key and no `cache/query_embeddings.json` | The demo works anyway: the queries are 50 dataset vectors not loaded into the collections. For natural-language queries - `make embed` with a key |
| 429 from OpenAI | Shared rate limit | The script waits with an exponential backoff (up to 8 attempts); after the first success everything comes from the cache |
| Latency figures are noticeably higher than in the RUNBOOK | Parallel load (other containers, indexing) | The ratios hold; close what is not needed, `docker stats` |
| Port 6351/6352 is taken | Another demo stand | Change the ports in `docker-compose.yml` and `QDRANT_HTTP_PORT`/`QDRANT_GRPC_PORT` for host mode |
| Need it without the demo container | — | `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python scripts/step2_exact_vs_hnsw.py` - the scripts go to `localhost:6351/6352` by default (verified on Python 3.13) |
| Want 100,000 points | — | `N_POINTS=100000 make data load` (downloads the third shard; HNSW takes about twice as long to build; not run in this build) |
