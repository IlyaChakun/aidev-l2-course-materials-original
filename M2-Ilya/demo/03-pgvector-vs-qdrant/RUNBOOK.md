# RUNBOOK. Demo 03: PostgreSQL + pgvector vs Qdrant

All outputs below are real, from the run of 2026-11-01 (macOS, Docker Desktop), abridged. Terminal width for readable tables - from 110 columns (`export COLUMNS=110` or wider; on a projector it is better to reduce the font than the width).

Time in the lecture: 10-12 minutes for all steps, each step takes 5-9 seconds.

## Preparation before the lecture (15 minutes, the day before or in the morning)

| Time | Action | Check |
|---|---|---|
| 0:00 | `cd M2-Ilya/demo/03-pgvector-vs-qdrant` | — |
| 0:01 | Key: `cp .env.example .env` and fill in `OPENAI_API_KEY` (or `export OPENAI_API_KEY=...` in the shell) | do not print the key on screen |
| 0:02 | `make up` | `Container ... Healthy` for postgres and qdrant; the first time the images are downloaded and the CLI is built (~1-2 min) |
| 0:04 | `make load` | `Done in ~46 s`, lines `chunks = 349`, `chunks_big = 20940`, `lumen_big = 20940` |
| 0:05 | Run `make step1` … `make step6` once | no `Traceback`; step 4: the average of "HNSW ef_search=40" is about 2.4 |
| 0:10 | The key can be removed: `unset OPENAI_API_KEY`, delete `.env` | all steps work from `data/cache/` |
| 0:11 | Open the Qdrant Dashboard `http://localhost:6361/dashboard` in a browser tab | the collections `lumen`, `lumen_big` are visible |

Stand ports: Postgres `5441`, Qdrant `6361` (REST) and `6362` (gRPC). Neighboring demos and third-party services (5432, 6333, 6341, 6351, 6371, 6381 and others) are not touched.

If you need a reset between the rehearsal and the lecture: `make clean && make up && make load` (about 1 minute; the embedding cache is kept, no key needed).

---

## Step 1. The same data in two places

**Command:** `make step1`

**Expected output (abridged):**

```
How much is stored and how
│ real chunks              │ chunks: 349                         │ lumen: 349                                   │
│ synthetic data for step 4│ chunks_big: 20940                   │ lumen_big: 20940                             │
│ dense                    │ embedding vector(1536), HNSW        │ unnamed vector 1536, Cosine                  │
│                          │ vector_cosine_ops                   │                                              │
│ lexical                  │ tsv tsvector (generated) + GIN      │ named sparse bm25, modifier idf,             │
│                          │                                     │ Qdrant/bm25 on the server                    │
│ metadata                 │ columns + tables docs, docs_access  │ payload: content, metadata.{source,section,…}│
│ business tables          │ docs: 22, docs_access: 52           │ none, payload only                           │
load_stats.json: {"chunks": 349, "chunks_big": 20940, "pg_hnsw_big_build_s": 6.4, ...}
```

Above it are the table of `chunks` columns (`embedding vector(1536)`, `tsv tsvector generated`) and the indexes: `chunks_big_embedding_hnsw` 164 MB, `chunks_tsv_gin` 168 kB.

**What to say:** "These are the same 349 chunks and the same vectors as in Qdrant. In Postgres a vector is just a column, and the lexical index is a generated `tsvector` column with GIN. The HNSW index on 21 thousand vectors takes 164 megabytes - vectors are heavy in any database."

**Watch for:** if `chunks: 0`, `make load` did not complete.

**What it proves:** a vector DB = storage + index + filters; in Postgres this fits into one table.

**Fallback move:** `make psql`, then `\d chunks` and `\di+`.

---

## Step 2. The same dense query

**Command:** `make step2` (question q03 from the golden set). Your own question: `docker compose run --rm demo python demo.py step2 "..."` - a key is needed if the question is not in the cache.

**Expected output (abridged):**

```
SELECT source, section, 1 - (embedding <=> %(q)s) AS cosine FROM chunks ORDER BY embedding <=> %(q)s LIMIT 5;
{"query": "[1536 numbers]", "limit": 5, "with_payload": true}

│ 1 │ payment-errors-reference.md / E-4012 Payment method rejected │ 0.6990 │ ... E-4012 Payment method rejected │ 0.6990 │
│ 2 │ payment-errors-reference.md / Quick decision table           │ 0.6306 │ ... Quick decision table           │ 0.6306 │
│ 5 │ payment-errors-reference.md / E-4020 Card declined by issuer │ 0.6121 │ ... E-4020 Card declined by issuer │ 0.6121 │
Chunks matching in the top-5: 5 of 5.

EXPLAIN on chunks (349 rows)
Limit (actual rows=5.00 loops=1)
  ->  Sort (actual rows=5.00 loops=1)
        Sort Method: top-N heapsort  Memory: 25kB
        ->  Seq Scan on chunks (actual rows=349.00 loops=1)
Execution Time: 1.523 ms

EXPLAIN on chunks_big (20940 rows)
Limit (actual rows=5.00 loops=1)
  ->  Index Scan using chunks_big_embedding_hnsw on chunks_big (actual rows=5.00 loops=1)
        Order By: (embedding <=> '[1536 numbers]')
Execution Time: 5.918 ms
```

**What to say:** "The same top-5, the cosine matches to the fourth decimal: `<=>` is the cosine distance, Qdrant returns the cosine. Look at the EXPLAIN: on 349 rows Postgres does not use the index - it is cheaper to scan everything. On 21 thousand rows it switches to HNSW by itself."

**Watch for:** on a small table Seq Scan is normal, not a bug; do not force the index.

**What it proves:** for basic dense search the systems are equivalent; Postgres chooses the plan by itself.

**Fallback move:** if Qdrant is unavailable - show only the Postgres part in `make psql`; the table from this RUNBOOK.

---

## Step 3. Transaction and JOIN with business tables

**Command:** `make step3`

**Expected output (abridged):**

```
3a. The document changed: the Team price $59 → $69. Metadata and chunks change in one transaction.
Before:             docs.version = 1, chunks = 12, Team price in the text = $59
Failure after DELETE: failure in the middle of the update (simulated) → ROLLBACK
After the failure:  docs.version = 1, chunks = 12, Team price in the text = $59  (nothing was lost)
After COMMIT:       docs.version = 2, chunks = 12, Team price in the text = $69
Search "How much does the Team plan cost per month?" immediately sees the new version, a line from the top-3:
| Team workspace with 15 people | $69 plan, no extra seats | $69 |

3b. Access rights are a plain JOIN with the docs_access table, before LIMIT, in the same query.
Question: How do I create an API key and what are the API rate limits?
plan = 'starter'
│ plans-and-pricing.md    │ API access, SSO and audit log    │ 2 │ 0.3808 │
│ plans-and-pricing.md    │ Plan comparison table            │ 2 │ 0.3592 │
plan = 'business'
│ integrations-and-api.md │ Creating a key                   │ 1 │ 0.5608 │
│ integrations-and-api.md │ Rate limits and HTTP 429         │ 1 │ 0.4920 │
Restored the original version so the demo can be re-run: docs.version = 1, chunks = 12, Team price in the text = $59
```

**What to say:** "The document was updated: delete the old chunks, insert the new ones, bump the version - one transaction. It failed in the middle - rolled back, search never saw a document without chunks. In Qdrant these are two calls without a shared transaction. Second: access rights are a JOIN with the plans table, a filter before LIMIT. Starter does not get the API article at all, instead of getting it and hiding it in the prompt."

**Watch for:** the step restores the original version at the end by itself; if you interrupt it in the middle, a rerun is still correct (transactions), and the version in `docs` may stay 2 - this does not affect the meaning.

**What it proves:** "the data is already in Postgres - pgvector": transactions, versions and access rights come for free; in a vector DB they have to be duplicated in the payload.

**Fallback move:** show the SQL from the output and the table above.

---

## Step 4. Filter + HNSW: asked for 5, got fewer

**Command:** `make step4`

**Expected output (abridged):**

```
chunks_big (60 tenants × 349 chunks) and lumen_big; filter on 3 tenants = 5% of rows; k = 5

EXPLAIN first: what the planner chose by itself
  ->  Seq Scan on chunks_big (actual rows=1047.00 loops=1)
        Filter: (tenant = ANY ('{tenant-007,tenant-023,tenant-041}'::text[]))
        Rows Removed by Filter: 19893

How many rows came back out of the 5 requested
│ question │ planner's own │ HNSW         │ HNSW          │ HNSW + iterative │ relaxed ∩ │ Qdrant          │ Qdrant ∩ │
│          │ (Seq Scan)    │ ef_search=40 │ ef_search=200 │ relaxed_order    │ exact     │ + payload index │ exact    │
│ q01      │ 5             │ 3            │ 5             │ 5                │ 5         │ 5               │ 5        │
│ q02      │ 5             │ 1            │ 5             │ 5                │ 5         │ 5               │ 5        │
│ q04      │ 5             │ 2            │ 5             │ 5                │ 4         │ 5               │ 5        │
│ q08      │ 5             │ 1            │ 5             │ 5                │ 5         │ 5               │ 5        │
│ average  │ 5.0           │ 2.4          │ 5.0           │ 5.0              │ 4.9       │ 5.0             │ 5.0      │

EXPLAIN (q01), HNSW, iterative_scan = off
Limit (actual rows=3.00 loops=1)
  ->  Index Scan using chunks_big_embedding_hnsw on chunks_big (actual rows=3.00 loops=1)
        Filter: (tenant = ANY (...))
        Rows Removed by Filter: 37

EXPLAIN (q01), HNSW, iterative_scan = relaxed_order
Limit (actual rows=5.00 loops=1)
  ->  Index Scan using chunks_big_embedding_hnsw on chunks_big (actual rows=5.00 loops=1)
        Rows Removed by Filter: 68
```

**What to say:** "First, honestly: on 21 thousand rows Postgres chooses the scan by itself, and the answer is exact. On millions of rows it will go into HNSW - we switch the scan off and see what happens then. The index returned the 40 nearest, the filter threw out 37, 3 of 5 remained. On average 2.4 of 5 - and no error, just less context for the model. pgvector 0.8 has `iterative_scan`: the traversal continues until 5 are collected. Qdrant filters during graph traversal."

**Watch for:**
- the "HNSW ef_search=40" column must be less than 5; if it is 5 everywhere, check that `chunks_big` = 20940 rows (`make step1`);
- `relaxed ∩ exact` = 4.9 of 5: relaxed_order is approximate, this is normal;
- in Qdrant `lumen_big` intentionally has `full_scan_threshold = 10` KB, otherwise on ~1K points Qdrant would have answered with an exact scan over the payload index (you can mention this: "Qdrant has a planner too").

**What it proves:** a filter after the index loses results ("asked for 5, got 2"); the filter must be part of the search - `iterative_scan` in pgvector or filterable HNSW in Qdrant. The synthetic data is documented in the README ("Synthetic data for step 4").

**Fallback move:** in `make psql`:

```sql
SET enable_seqscan = off;
SELECT count(*) FROM (SELECT id FROM chunks_big WHERE tenant IN ('tenant-007','tenant-023','tenant-041')
  ORDER BY embedding <=> (SELECT embedding FROM chunks LIMIT 1) LIMIT 5) s;   -- usually fewer than 5
SET hnsw.iterative_scan = relaxed_order;   -- repeat the query: 5
```

---

## Step 5. Hybrid: FTS + vector in SQL vs prefetch + rrf

**Command:** `make step5`

**Expected output (abridged):**

```
WITH dense AS (... ORDER BY embedding <=> %(q)s LIMIT 20),
     lexical AS (... ts_rank_cd(tsv, query) ... LIMIT 20),
     fused AS (SELECT id, sum(1.0 / (60 + rnk)) AS rrf ... GROUP BY id)
SELECT c.source FROM fused JOIN chunks c USING (id) ORDER BY rrf DESC LIMIT 5
{"prefetch": [{"query": "<dense>", "limit": 20}, {"query": {"text": "<question>", "model": "Qdrant/bm25"},
 "using": "bm25", "limit": 20}], "query": {"fusion": "rrf"}, "limit": 5, "with_payload": true}

recall@5 on the golden set (core and multi; traps are not counted)
│ method                    │ core (n=10) │ multi (n=5) │
│ PG dense                  │ 1.00        │ 0.90        │
│ PG lexical AND            │ 0.10        │ 0.00        │
│ PG lexical OR             │ 1.00        │ 0.80        │
│ PG hybrid RRF k=60        │ 1.00        │ 0.90        │
│ QD dense                  │ 1.00        │ 0.90        │
│ QD bm25                   │ 1.00        │ 0.90        │
│ QD hybrid rrf (default)   │ 1.00        │ 0.90        │
│ QD hybrid rrf k=60        │ 1.00        │ 0.90        │
Qdrant RRF, maximum score on core (the document is first in both branches): default k → 1.0000, k=60 → 0.0333.
```

**What to say:** "Hybrid in Postgres is one SQL: two lists of 20, fusion by ranks. In Qdrant - `prefetch` and `fusion`. On 22 documents both systems find the right document for all 10 core questions, the difference is not in quality but in convenience. One trap: `websearch_to_tsquery` requires all the words of the question - recall 0.1. For real questions the words have to be joined with OR."

**Watch for:**
- recall@5 core 1.00 almost everywhere is expected on a small corpus; do not present it as "hybrid is not needed": the difference appears on hundreds of documents and on exact terms (error codes);
- the `PG lexical AND` row is the main teaching moment of the step.

**What it proves:** hybrid = two searches + RRF; in Postgres it is assembled by hand in SQL, in Qdrant it is there out of the box (BM25 on the server). Along the way, the cross-check from the lecture plan ("Check before the slides", item 1): in Qdrant 1.19.2 the default RRF gives a score of 1.0 for a document that is first in both branches - this is `1/(k + rank)` with k=2 and a zero-based rank; `{"rrf": {"k": 60}}` is accepted and gives 0.0333 = 2/60.

**Fallback move:** the recall table from this RUNBOOK.

---

## Step 6. Operations

**Command:** `make step6`

**Expected output (abridged):**

```
│ dimensions in the index │ vector: up to 2000 in HNSW/IVFFlat; halfvec: up to 4000 │ dense up to 65536 │ vector(3072) + hnsw →
│                         │                                                          │                   │ "column cannot have more than 2000
│                         │                                                          │                   │ dimensions for hnsw index";
│                         │                                                          │                   │ halfvec(3072) + hnsw → index created
│ HNSW build              │ in maintenance_work_mem ...                              │ in the background, yellow → green │ maintenance_work_mem = 512MB,
│                         │                                                          │                   │ parallel workers = 2; HNSW on 20940 rows: 6.4 s, index 164 MB
│ Docker                  │ the parallel build uses /dev/shm → shm_size              │ volumes           │ shm_size: 1g in docker-compose.yml
│ backup                  │ pg_dump / PITR - together with the business data         │ a snapshot via the API │ Qdrant snapshot lumen-...snapshot (4.9 MB)
│ versions in the stand   │ PostgreSQL 18.6, pgvector 0.8.7                          │ Qdrant 1.19.2     │ whole database 361 MB
```

**What to say:** "`text-embedding-3-large` gives 3072 dimensions - they do not fit into a plain `vector` with an index, you need `halfvec`. HNSW is built in `maintenance_work_mem`, and in Docker it also runs into `/dev/shm` - we have `shm_size: 1g`. A Postgres backup is the familiar `pg_dump` together with the business data; in Qdrant it is a collection snapshot, separately."

**Watch for:** every run of the step creates a new Qdrant snapshot in the `qdrant_snapshots` volume - they are removed together with the volumes (`make clean`).

**What it proves:** in operation Postgres wins with a single backup and monitoring loop, and loses on dimension limits and on the fact that filters and index builds have to be tuned by hand.

**Fallback move:** `make backup` - makes `pg_dump -Fc` into `data/out/lumen.dump` (161 MB, almost all of it `chunks_big`) and a Qdrant snapshot via `curl`.

---

## Cleanup after the lecture

```bash
make clean          # docker compose down -v + rm -rf data/out; the data/cache/ cache stays
rm -f .env          # if the key was put into a file
```

Fully, with the cache: `make clean && rm -rf data/cache`.

## Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| `… texts are not in the data/cache/ cache and OPENAI_API_KEY is not set` | a question or chunk was not embedded | set the key and repeat `make load` (it also warms up all the questions of steps 2-5) |
| `Bind for 127.0.0.1:5441 failed: port is already allocated` | the port is taken by another stand | `docker ps --format '{{.Names}} {{.Ports}}' \| grep 5441`; stop your old stand with `make down` |
| `make load` hangs on Qdrant | indexing of `lumen_big` (yellow → green), usually up to 40 s | wait; `curl -s localhost:6361/collections/lumen_big` → `status` |
| Step 4: "HNSW ef_search=40" is 5 everywhere | no synthetic data or a different filter | `make step1`: `chunks_big: 20940`; otherwise `make load` |
| Step 4: "planner's own" is less than 5, matches HNSW | a cached prepared-statement plan survived `SET` | in `common.py` the connection has `prepare_threshold=None` - do not remove it |
| `OpenAI RateLimitError, retrying in …` | shared key limit | wait: up to 8 retries with exponential backoff; embeddings are saved after every batch |
| Tables wrap and break | narrow terminal | `export COLUMNS=120` before `make stepN` |
| `the input device is not a TTY` | run from a script without a terminal | `docker compose run --rm -T demo python demo.py stepN` |
