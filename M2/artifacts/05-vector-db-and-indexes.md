# Vector database and indexes: what to choose and which knobs to turn

> Module 2 artifact. All versions and figures were checked on **10.08.2026**; the date matters: this layer
> changes with releases, not with years.

## What this is and how to use it

This is a helper document for one layer of your system: **where the vectors physically live, which index
searches them, and what you will be able to change later without re-loading the corpus.**

The workflow is as follows. Connect the file to your agent (Claude or another one you work with),
describe your course project to it in three paragraphs (what the corpus is, how many documents, who the users are,
what latency is acceptable) and go through the "Brainstorm questions" section with it. The agent should not
lecture you about HNSW; it should **bring you to a written decision**: which database, which dimensionality,
which tenant isolation, which knob values, and what you will measure.

The output should be a short text in the project repository, literally one page:
the chosen database and version, the collection schema, the values of `m`, `ef_construct`, `ef`, the quantization mode,
the isolation model, the list of payload indexes, and the threshold at which you revisit this decision.
This text will be useful in module 3: the collection and ingestion are reused there as is.

Terms are explained at first use. If you come across an unfamiliar one, ask the agent to explain
it on your corpus, not in general terms.

---

## Set map: this file is one of twelve

The module's artifacts walk through the pipeline layer by layer, and the decisions in them are interlinked: the upper
bound of a chunk runs into the embedder's window, the metadata schema determines what you can filter by
at search time at all, and cost is the sum of the decisions of all layers at once. That is why the files
sit in one folder and are designed to be used together: read this one in full, open the others
as needed.

> **Instruction to the agent.** You are reading one file out of twelve; the others are next to it, in the same
> folder. As soon as the conversation goes beyond the boundary of this layer, open the relevant file and read the
> relevant section before giving advice. Do not retell the neighboring layer from memory:
> the artifacts contain thresholds, figures with measurement conditions, and failure modes that are not in
> general knowledge. Read on demand, not everything at once: this file first, then whatever is needed
> as the conversation goes. If the file you need is not next to this one, say plainly which one is needed and ask for it,
> instead of making it up. When a decision in one layer breaks a decision in a neighboring layer, say
> so right away, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at ingestion |
| [`02-metadata.md`](02-metadata.md) | Metadata | you are deciding which fields go next to a chunk: source, freshness, permissions, version, and what to filter by later |
| [`03-chunking.md`](03-chunking.md) | Chunking | you are choosing size, boundaries and overlap; questions about tables, code and structural chunking |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | you are choosing a model for the language and domain, dimensionality, local or via API; the price of changing the model |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, branch fusion, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanics, source citation, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletion, record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reduction |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End-to-end | checking what was built: errors where the pipeline works and the metrics are green, but the system lies; a checklist of 24 checks |

**This layer's closest links.** Dimensionality and vector type come from
[`04-embeddings.md`](04-embeddings.md), the number of points comes from chunking
([`03-chunking.md`](03-chunking.md)), and the fields for filters and payload indexes come from
[`02-metadata.md`](02-metadata.md). Tenant isolation at the database level is half of the conversation
about access rights ([`10-security.md`](10-security.md)); memory and disk are the main cost item
([`11-economics.md`](11-economics.md)). For how index settings relate to the sparse branch
and to fusion, see [`06-search-and-fusion.md`](06-search-and-fusion.md); for why HNSW's approximate nature
often turns out to be a false diagnosis when metrics jitter, see §5.3 in
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

---

## Layer decision map

Decisions go from top to bottom. The upper ones cost the most to redo; the lower ones change in production.

```
1. WHERE THE INDEX LIVES       in memory · on disk · in object storage
      ↓ sets the price, latency and volume ceiling
2. WHICH DATABASE              chosen by stack and operations, not by benchmarks
      ↓
3. COLLECTION SCHEMA           dimensionality · metric · named vectors
      ↓ warning: irreversible: changed only by re-creation
4. INDEX TYPE                  HNSW · IVF · DiskANN
      ↓
5. KNOBS                       m and ef_construct at build · ef on every query
      ↓
6. QUANTIZATION AND RESCORE    how much one vector costs in memory
      ↓
7. TENANT ISOLATION            filter · own shard · own collection
      ↓
8. PAYLOAD INDEXES             warning: created BEFORE loading the data
      ↓
9. OPERATIONS                  update queue · strict mode · backups · upgrades
      ↓
10. OBSERVABILITY              search recall drops on its own, without a single deploy
```

Two things that are useful to understand before everything else.

**The index decides how many vectors to compare against. Quantization decides how much each one costs.**
These are two independent choices, not alternatives to each other. A binary-compressed HNSW is a normal,
recommended configuration, not a compromise for the poor.

**An index is not chosen for speed.** Below ten million vectors almost all common
indexes respond in single-digit milliseconds. They are chosen by memory, by recall (the share of needed
documents that the search actually found) and by mutability, that is, by how much a corpus that is
constantly being edited costs. No public benchmark measures mutability.

---

## Brainstorm questions with the agent

Go in order. For each question the agent should extract from you a number or an explicit "don't know yet,
I'll check with such-and-such".

**1. How many vectors will you have in a year, not today?**
Counted as "documents × average number of chunks". Everything else depends on the order of magnitude:
up to ten million almost anything works, above that engineering begins.

**2. How much memory will this take, and do you have it?**
The formula is below in the section with thresholds. If the answer is "twice as much as we have", this is not a reason
to save on hardware, it is a reason to choose a different storage architecture.

**3. Should your index be in memory, or can it live on disk?**
Ask yourself what latency is acceptable to the user. The difference between "in memory" and "in object
storage" is the difference between single-digit milliseconds and hundreds on a cold query, and an order of
magnitude in storage price.

**4. What is the vector dimensionality, and why exactly that?**
Dimensionality is a recurring charge: it is multiplied by the number of vectors and lasts the whole life of the project.
Ask the agent to calculate what 3072 versus 1024 will cost you at your volume over a year.

**5. Do you have one tenant or many?**
If the corpus is split by customers, departments or projects, then the permissions filter is the narrowest filter
in the system, and it breaks an ordinary index. There are three isolation options, and they cost different amounts.

**6. What share of the corpus remains after your typical filters?**
This is the layer's key number. If a typical query sees less than one percent of the data, search without special
index preparation will return garbage, while answering fast.

**7. Which fields will you filter on, and are they all already in the data?**
A field that is absent at load time cannot be used in a filter without reindexing. The list of
fields is part of the schema, not a detail.

**8. How often does the corpus change?**
An index that is rewritten every hour and an index that is built once a quarter are different
configurations of the same database.

**9. What is your latency budget, broken down by stage?**
Not "it should be fast", but "search so many milliseconds, context assembly so many, generation so many".
Without the breakdown there is nothing to discuss.

**10. Do you already know which database version you will run, and have you read its changelog?**
This is not a formality: the latest release removed from REST three endpoints that 2024 tutorials are full of.

**11. What will you do when search recall drops?**
The right answer contains the words "weekly cross-check" and "raise `ef`", not "we'll notice from
complaints".

**12. How will you restore the database if it disappears tonight?**
The answer "there's a snapshot" is incomplete: snapshots have restrictions on version and cluster shape, and some
managed solutions have no automatic backups at all.

**13. Which of the listed decisions will you not be able to redo without re-loading the corpus?**
Have the agent write them out as a separate list. Usually these are dimensionality, metric, the set of named
vectors, the identifier scheme, and the presence of payload indexes at build time.

**14. What queries will you measure quality on?**
Public benchmarks run uniformly random queries. Your traffic does not behave that way, and this
changes the conclusions.

**15. What will you hand over to a managed service, and what will you keep, and why?**
What matters here is not the pricing plan but the question "can we move out". One notable vendor has no path to
self-hosting at all: the index format is closed, and leaving means a full
reindex.

**16. Who on the team will operate this?**
If the answer is "nobody in particular", choose a managed solution, even if it is more expensive on paper.

---

## How HNSW works and what follows from it

HNSW (Hierarchical Navigable Small World) is a multilayer proximity graph. The upper layers are sparse and
hold long links; the bottom one contains all vectors and short links. Search enters from the top, greedily moves
toward the query and drops to the layer below when there is nothing left to improve.

Two consequences from which all of operations grows.

**Every traversal step is a random memory access.** While the graph is in RAM, a step costs
nanoseconds. As soon as the graph does not fit, a step turns into a disk read, and the worst percentiles
of queries collapse. The appetite for memory comes from here, not from the algorithm's greed.

**A node cannot be cleanly cut out.** Deleting an upper sparse node breaks connectivity and leaves
part of the graph unreachable. That is why all engines mark records as deleted and clean them up in the background.
Practical conclusion: with a frequently changing corpus the limit becomes not query speed
but the cost of rebuilding. The deletion mechanics are covered in the corpus lifecycle artifact.

### Three knobs, and one of them is the main one

| Knob | When it is fixed | What it does | What grows |
|---|---|---|---|
| `m` | at index build | maximum links per node, graph density | recall, memory, build time |
| `ef_construct` | at index build | width of the candidate list at insertion | graph quality and build time. **Does not affect query latency at all** |
| `ef` / `hnsw.ef_search` | on every query | width of the candidate list at search | recall, latency |

The conclusion that changes the order of work: `ef_construct` is raised to 200 simply because it costs
only build time, and builds are rare. `m` is chosen once for the dimensionality and memory.
And `ef` is turned in production and differently for different query paths: a cheap search for suggestions and an expensive one
for the legal path live on the same index.

The factory defaults, which for some reason nobody departs from: pgvector `m=16`, `ef_construction=64`,
`hnsw.ef_search=40`; Qdrant `m=16`, `ef_construct=100`, and `ef` at search time defaults to
`ef_construct`.

**Measured `ef_search` sweep** (50 thousand random vectors at 128 dimensions, pgvector,
top-10 recall against exact brute force, public measurement from 17.02.2026):

| `ef_search` | recall@10 | query time |
|---|---|---|
| 10 | 30% | 0.38 ms |
| 40 (default) | 50% | 1.36 ms |
| 100 | 80% | 1.56 ms |
| 200 | 100% | 2.29 ms |
| 400 | 100% | 3.91 ms |

Read with a caveat: these are random vectors, that is, the worst case. On real embeddings recall
is higher at the same `ef`, and the knee of the curve usually lies between 80 and 200. The value of the table is not in
the absolute numbers but in the shape: **doubling `ef` roughly doubles the time and barely moves recall
past the knee.**

The sweep over `m` on the same corpus: `m=4` gives a 33 MB index and 10% recall, `m=16` gives 40 MB and
50%, `m=32` gives 49 MB and 80%, while build time grows from 1.4 to 26.6 seconds. That is, **`m` gets more expensive
in build time faster than in size.**

### The "knob → what it affects" table

| Knob | Changeable without a rebuild | Recall grows | Query latency grows | Memory grows | Build time grows |
|---|---|---|---|---|---|
| `ef` / `ef_search` | **yes** | yes | yes | no | no |
| `ef_construct` | no | yes | **no** | no | yes |
| `m` | no | yes | slightly | yes | yes, faster than linear |
| `payload_m` | no | yes on a filter | no | yes | yes |
| quantization level | no | drops | drops (faster) | **down sharply** | slightly |
| oversampling at rescore | **yes** | yes | yes | no | no |
| `full_scan_threshold` | yes | exact answer on a narrow filter | depends | no | no |

**In production you can change only the rows with "yes" in the first column. The rest is a work plan.**

---

## Memory: where the gigabytes come from

```
memory ≈ number_of_vectors × dimensionality × 4 bytes × 1.5
```

The one and a half is metadata, point versions and the optimizer's temporary segments. Reference points for a cross-check:
a million vectors at 1536 dimensions is about 6-7 GB, ten million about 60-70 GB, a hundred million
at 768 dimensions with `m=16` about 340 GB. Hence the generally accepted boundary: **an in-memory index is
the right answer up to roughly 10-50 million vectors and the wrong one at a billion.**

A vendor rule of thumb nearby: **if you hold half as many vectors in memory, latency roughly
doubles.**

An important caveat about compression: **the real gain is smaller than the theoretical one, because the graph and metadata
are not compressed.** A hundred thousand vectors at 1536 dimensions is about 900 MB uncompressed and about 128 MB with
binary quantization. The gain is sevenfold, not the thirty-twofold that follows from the arithmetic
of "one bit instead of thirty-two".

**Calculate peak memory in advance, it takes a minute.** A public postmortem from 30.04.2026: an index build
on 165 million rows was killed after 23 hours 41 minutes at 44% completion. The working set was computed
with the same formula and came to 472 GB against 125 GB of RAM, an overshoot of 4.7 times. Replacing it with
eight partial indexes by shard took about 6 hours.

---

## Quantization: the ladder and one fresh fork

| Method | Compression | What happens to quality | Caveat |
|---|---|---|---|
| `halfvec` (16 bit) | 2x | practically lossless on text | first move, minimal risk |
| Scalar int8 | 4x | about 99.3% of search quality | friendly to CPU instructions, error under 1% per vendor measurements |
| 4 bits per dimension | 8x | comparable to scalar | the query is computed at full precision, the scheme is asymmetric |
| 2 bits | 16x | cures the main weakness of binary: values near zero | |
| Binary, 1 bit | 32x | about 92.5% alone, **about 96% with rescore** | **reliable only above 1000 dimensions** |
| Product (PQ) | up to 64x | lower than the others | needs codebooks trained on your own data |

**The trick that makes aggressive compression workable: search over the compressed, rank by the full.**
Pull a hundred candidates from the compressed vectors in memory, read the hundred original values from disk,
re-sort, return ten. One extra read per query, quality rises from roughly
92.5% to roughly 96% while keeping the thirty-twofold saving. **Skipping the rescore is the most
common quantization mistake.**

How many candidates to take beyond what is needed (oversampling, from vendor documentation): a 1536-dimension
model gives recall 0.98 in the top hundred at fourfold oversampling, a 4096-dimension model
gives the same in the top fifty at twofold. **The higher the dimensionality, the less headroom is
needed.**

Warning: **A fork from 05.08.2026.** Qdrant 1.19 introduced a storage type that keeps **only** the
four-bit representation, with no full-precision copy on disk. Storage savings of up to nine times versus the
combination of "full precision plus a four-bit copy", fewer reads, higher throughput. The price:
**there is nothing to rescore with**, because the original values simply do not exist. This is a direct contradiction of the rule from the
previous paragraph, and the choice should be made not by "what is newer" but by what matters more in your task. The caveat
is mandatory: the type came out five days before the session, the vendor named only the storage savings, **nobody has
measurements of the recall drop**, the vendor included.

---

## When not HNSW

**IVF.** Splits the space into cells with k-means and at query time looks at a few nearest ones.
Builds fast, uses 30-50% less memory, shards naturally, accelerates well on
GPUs. Pays in recall at the same time. Two pitfalls: the index cannot be built on an
empty table, it needs data for clustering, and **cell centers go stale as the data drifts**,
that is, recall drops until retraining. The tuning canon: number of cells about the square root of the number of vectors,
probe from one thirty-second to one eighth of the cells. The default "probe one cell"
is almost always wrong in production.

**DiskANN.** The graph and full vectors on a fast disk, only compressed ones in memory for traversal. A public
result from 2019: a billion 128-dimension vectors on a single machine with 64 GB of memory give more than 5000
queries per second at recall above 95%. The same corpus in HNSW would have needed more than 640 GB
of memory. Available to Postgres users through an extension on top of pgvector.

**Index in object storage.** Lives in S3, the local disk is a cache. The first query to an unused
namespace is about 874 ms on a million documents, subsequent ones about 14 ms. A fundamentally different
cost curve: about $70 per terabyte per month versus about $600 for a triple-replicated disk
and about $1600 for solutions with an in-memory cache (market overview, 05.2026, the composition of the calculation is partly disclosed).

---

## Choosing a database: three architectures instead of eight names

A frame more useful than a list of vendors: **the question is not "which database is best" but "where does the index live".**

| Where the index lives | What you buy | What you pay with | Examples |
|---|---|---|---|
| In memory | latency in single-digit milliseconds | RAM, which is expensive | Qdrant, Weaviate |
| On disk | scale at the same money | latency and operational complexity | Milvus with DiskANN, pgvector with an extension |
| In object storage | a price an order of magnitude lower | cold start of the first query | turbopuffer, LanceDB |

A cut by engine as of 10.08.2026:

| Engine | Version | Niche | What it pays with |
|---|---|---|---|
| pgvector | 0.8.6 (29.07.2026) | Postgres is already in the stack: vectors in the same transactions, backups and permissions | manual tuning, single-machine ceiling, a 2000-dimension limit on the `vector` type |
| Qdrant | **1.19.0 (05.08.2026)** | heavy filters, many tenants, quantization, self-hosting | fewer ready-made integrations, the standard cloud plan has no uptime commitment |
| Weaviate | 1.27+ | hybrid search and reranking out of the box | requires 2-3 times more memory, modules add latency |
| Milvus | 2.6.x | hundreds of millions and billions, GPUs, tiering to disk and to object storage | distributed mode brings along a queue, a coordinator and object storage |
| Chroma | 1.5.x | the fastest start, a notebook and a prototype | the path to production is shorter than for dedicated engines |
| LanceDB | 0.20+ | vectors on top of a data lake, zero infrastructure | cold read latency, feature maturity |
| turbopuffer | managed | large rarely read corpora, isolation by namespaces | cold start, cloud lock-in, **no self-hosting** |
| Pinecone | managed | minimum operations | **the only one with no path to self-hosting**: the index format is closed, leaving equals a full reindex |

**About the pgvector ceiling.** The common figure "hits the wall at 2-5 million vectors" is understated by an order of magnitude,
do not use it. The current picture: **up to about a million without questions, up to 10 million with
tuning, 10-50 million is the real ceiling of a single installation**, beyond that an extension with an on-disk
index or a dedicated database.

---

## Many tenants: three models and the price of isolation

The position of the Qdrant vendor is unambiguous: **a separate collection per user is a typical cause
of the "too many shards" problem**. Collections are created sparingly and only where strict isolation
or different embedders and metrics are needed.

| Model | When | Ceiling |
|---|---|---|
| Filter by field in a shared collection | many small similar tenants | almost no overhead, but the filter must be narrow and indexed |
| Own shard for a large tenant | a few large ones, there is a noisy-neighbor problem | **no more than 1000 dedicated shards per cluster** |
| Tiered scheme | small ones in a shared shard, large ones move to their own transparently to the application | the move threshold recommended by the vendor is about **20,000 points** |
| Own collection | strict isolation, a regulatory requirement | **1000 collections per cluster**, and the vendor calls this an antipattern |

**The only public measurement that answers the question with numbers** (Curator, arXiv 2401.07119,
YFCC100M corpus, 2024): **a separate index per tenant is on average 37.2 times faster than a filter on
metadata and requires 10.1 times more memory.** The overhead comes not from indexes but from duplication:
a vector accessible to five tenants lies in five copies and carries five sets of links.

Why a filter over a shared index is slow: the permission check happens at traversal time on every visited
node, and the structure of the shared graph is not fitted to the vector distribution of a specific tenant.
In the same corpus most tenants see less than 5% of the vectors, that is, traversal spends most
of its steps on other people's data. A claim from a managed-database vendor from the other side (04.2026): the spread in response time
between tenants on a shared graph reaches three times.

Three parameters that turn a shared collection into many small graphs (Qdrant):

- `is_tenant: true` on the payload index: a tenant's data is physically placed together, and reading
  becomes sequential instead of a scatter of random accesses;
- `payload_m: 16` together with `m: 0`: **the global graph is not built at all**, search goes over the tenant's
  subgraph. The price: cross-tenant search without a filter becomes impossible. If you need admin search across everyone,
  keep `m` small and hold both graphs;
- a payload index on the filter field is mandatory: without it the filter works but scans the data of every
  point. A breakdown on 100 thousand points gives a difference of "about 2 ms versus about 200 ms".

Warning: **Payload indexes are created BEFORE loading the data.** The filterable graph gets additional links
that take the filter into account only if the index on the field already existed at build time. An index created
after loading requires a graph rebuild to start working as intended. This is a one-line
order of operations that breaks an already built production.

### Example: collection configuration for many tenants

The comments here are for reading, they will not be in a real request.

```jsonc
PUT /collections/kb_prod
{
  "vectors": {
    "size": 1024,                   // embedder dimensionality; changing it = reindexing
    "distance": "Cosine",
    "memory": "cold"                // original vectors on disk: needed only for rescore
  },
  "quantization_config": {
    "turbo": { "always_ram": true } // 4 bits, 8x; search goes over them, so they are in memory
  },
  "hnsw_config": {
    "m": 0,                         // no global graph: cross-tenant search not needed
    "payload_m": 16,                // a per-tenant subgraph instead
    "ef_construct": 200,            // costlier build, higher recall; does not affect queries
    "memory": "pinned"              // the graph is always in memory: every step is a random access
  },
  "optimizers_config": { "indexing_threshold": 20000 },
  "strict_mode_config": { "enabled": true, "unindexed_filtering_retrieve": false }
}
```

A mandatory second step, **before loading the data**:

```http
PUT /collections/kb_prod/index
{ "field_name": "tenant_id", "field_schema": { "type": "keyword", "is_tenant": true } }
```

Three questions worth asking the agent about this config: why `m: 0` is a decision and not a saving;
what breaks if you swap the two requests; who will be hurt here by `"memory": "cold"`.

---

## Qdrant nuances that are rarely talked about

Checked against the documentation and changelog as of 10.08.2026. Check parameter names against the documentation
of your version: this layer changes fast.

**Upgrading to 1.19: code first, then the version.** In 1.19 the old `/search`, `/recommend`, `/discover`
endpoints are **removed** from REST. Not marked deprecated, removed. They were replaced by the single `/query`
back in version 1.10. In gRPC they are so far only marked deprecated, so gRPC clients have one
release of headroom, REST has none. The practical consequence: a fresh `docker pull` gives 1.19, and code from
a two-year-old article stops working, and it looks like a data problem. **The order:
migrate calls to `/query`, then upgrade.**

**Thresholds you learn about in an incident.** `indexing_threshold` defaults to 20,000 (in kilobytes,
where one kilobyte is roughly one vector of size 256): below it a full scan is cheaper than an index.
`full_scan_threshold` (10,000 by default, also in kilobytes): if fewer than the threshold remain after the filter,
the planner honestly falls back to a full scan instead of traversing the graph. This is not a bug, this is correct
behavior, but it explains why on a small collection the index "does not work".

**The update queue and what to do with it.** Under heavy writes the optimizer cannot keep up, and search
starts scanning the unindexed part. Two cures, both with a price. `indexed_only: true` makes it
search only the indexed part, with a side effect: **fresh points temporarily disappear from results**.
The `prevent_unoptimized` mode accepts and reliably stores points but does not show them until indexed.
A trap: this mode together with `wait=true` produces head-of-line blocking of the queue, the response is held until all
deferred points are indexed, and this stalls the whole update pipeline.

**Strict mode as a gate.** `unindexed_filtering_retrieve: false` rejects queries with a filter on an
unindexed field. On the cloud plan it is enabled by default. This is exactly what is needed in production:
a missing index becomes an error at the API boundary, not a slow query that nobody
notices for half a year.

**Memory tiers (1.19).** A single `memory` parameter with the values `pinned`, `cached`, `cold` replaced
the patchwork of earlier flags on all parts of the collection. The graph links can now be pinned in memory separately
from the vectors, and compressed vectors get their own tier independently of the originals. The old flags work,
but are marked deprecated.

**Keyword statistics per tenant (1.19).** In a shared collection the statistics for lexical
search were computed over the whole shard, that is, one tenant's vocabulary spoiled the ranking for another.
Now the corpus for the statistics is narrowed by a filter. A subtlety from the documentation: if the filter finds
no points at all, the statistics **do not fall back** to the global ones, all words get the same weight,
and the ranking degenerates.

**What else is worth opening in your version's documentation** (a list of things to look for, not a description of
behavior): prefix search for keyword fields, if you have paths, SKUs or URLs · deterministic
non-overlapping samples for batch processing · pinning a user's reads to a single replica ·
cluster-level quotas and reading effective memory limits in telemetry · an embedded build of the database
for local scenarios · computing embeddings on the managed database side, so as not to route text
through your own service · relevance feedback, when a query is refined with "similar" and
"not similar" examples · a memory-saving mode for small installations. Each item is worth ten minutes of reading
and sometimes removes an entire layer of hand-written glue code.

---

## Backups: three mechanisms, and they are not interchangeable

| | Migration tool | Snapshot | Disk backup |
|---|---|---|---|
| What it does | streams points to the target cluster | an archive of the collection together with the ready index | a snapshot of the disk volumes |
| Indexing on the receiver | full rebuild, slow | no, the index moves ready-made | no, a disk clone |
| Receiver restriction | any version, any shape | **the same minor version and the same number of shards** | the same provider, region, version, cluster shape |
| Disk headroom | double | double | no less than the source |

Practical notes: a snapshot restores only into a cluster of the same minor version, in a distributed
installation it is taken on each node separately, and collection aliases are not included in it and are carried over by hand.

To show that the backup model is a property of the engine, not a common practice: in Weaviate, snapshots
of the graph itself are needed for startup time, otherwise the whole log is replayed at launch; in Milvus a snapshot
prevents the garbage collector from deleting the files it references, and one snapshot in the limit doubles
the object storage bill; turbopuffer has **no automatic backups at all**, instead there are copies
of namespaces and branches, and a branch is a copy-on-write clone, that is, **deleted data
may keep living in a branch**, and this matters for deletion requests.

---

## Recall drops on its own, without a single deploy

**HNSW recall is a function of collection size, not a property of the config.** A fixed `ef`
explores a fixed number of candidates, and as the graph grows the true neighbors end up farther away in
hops. An index tuned to 98% at a hundred thousand vectors drops below 90% at ten million
with the same parameters. The numbers are illustrative (the source explains the mechanism correctly
but gives no measurement), the mechanism is exact. **No database has an alert for this.**

The practice that follows: a weekly cross-check of a hundred queries against exact brute force,
an alert when it falls below your own threshold, and raising `ef` before users notice.

A related silent failure specific to pgvector: with insufficient `maintenance_work_mem` the index build
does not fail but switches to a disk path that is 10-50 times slower, and the graph ends up
less connected. **Memory under-provided at build time shows up as sagging recall on
queries**, where nobody looks for it. The default `maintenance_work_mem` is 64 MB, set
at some point for completely different indexes.

And one more: `ef_search` and the number of probed cells in pgvector are session settings. Through a
connection pooler in transaction mode an ordinary `SET` is **silently lost**, the pool hands the next query
to a different server connection. There is no error, recall is at the default, the engineer is sure everything is configured.
The cure is `SET LOCAL` inside a transaction.

---

## Real traffic does not look like a benchmark

Public vector database tests run queries drawn uniformly from the corpus. Production traffic does not behave
that way: **a small share of queries hits the same data a hundred times more often than the rest. One segment
is overloaded, the others sit idle.**

Three sources of skew, and all three will show up in your project:

- **temporal**: today's incident, a fresh release, two hundred recurring support questions;
- **per tenant**: a few large customers produce a disproportionate share of traffic;
- **structural**: inside the graph there are hub nodes through which almost every traversal passes,
  and this is a property of the data, not of your load.

Why an ordinary cache does not cure it: **the graph is traversed in order of proximity, not in order of
access**, so to read-ahead mechanisms the access looks random, and hot vectors
do not settle in the cache on their own. Hence the practice of pinning the neighborhoods of entry points in memory and explicitly separating
hot and cold storage tiers.

A second story of the same nature: **filtered search breaks what a clean benchmark shows.**
A controlled filtered-search benchmark (VecBench, SIGMOD 2026) shows for one and the same
engine recall of 0.995 in one mode and 0.455 in another. This is not a ranking of engines, it is an illustration
that **recall on a filter is set by the mode, not by the engine**, and you have to measure your own configuration.

A budget reference point so you have something to check against: **20-80 ms at the 95th percentile for vector search
at k=10-50** and 500-3000 ms for the whole query path. This is a practitioners' summary, not a standard. If search
goes outside the range, the cause is usually not the database but that the index is not in memory or the filter fell back to a full
scan.

---

## Common mistakes

| How not to | What it leads to | How to |
|---|---|---|
| Create a payload index after loading the data | The filter works, but the graph does not know about the field: recall on a narrow filter drops severalfold, and it is fixed only by rebuilding the graph | The list of filter fields is fixed before the first load, indexes are created on an empty collection |
| Enable quantization and not enable rescore | Quality sags silently: rounding errors change the order in the top ten, noticeable only by measurement | Search over the compressed, rank by the full, measure recall on your own set before and after |
| Leave `ef` at the default | Half of the needed documents are not found, and the dashboard is green because latency is excellent | Sweep the curve on your own data, find the knee, set different `ef` profiles for different query paths |
| Upgrade to 1.19 without migrating calls to `/query` | The application returns errors that look like a data problem | First convert the code, then upgrade the database, go one minor version at a time |
| Create a collection per customer | Hundreds of collections, each with its own shards and structures: memory and startup time grow well before the formal ceiling | A tenant filter in a shared collection, a tiered scheme with large ones moving out, a separate collection only where isolation has to be proven to an auditor |
| Set `ef_search` through a connection pooler | The setting is lost without an error, recall stays at the default | `SET LOCAL` inside a transaction, verify the effective value with a query |
| Measure quality on uniform queries | In production exactly what the benchmark did not test breaks: narrow filters and hot segments | Capture a profile of real filters and query repetition, build a test set from it |
| Plan memory by eye | A day of build into the trash, as in the 165-million-row postmortem | The formula, multiplication by 1.5, comparison with available memory before launch |
| Treat a snapshot as a recovery plan | A snapshot does not restore into a cluster of a different minor version or shape, and this is learned at the moment of the outage | Recovery is verified by a drill, not by documentation. Separately check what gets into the backup: in some solutions inactive tenants are not included |
| Treat recall as a constant | Silent degradation over months that nobody connects with corpus growth | Regular cross-check against exact brute force and an alert at your own threshold |

---

## Layer readiness checklist

- [ ] It is written down where the index lives: in memory, on disk or in object storage, and why.
- [ ] Memory is calculated by the formula for the volume **in a year**, not for today's.
- [ ] Dimensionality and metric are fixed, and it is written down that changing them means reindexing.
- [ ] The values of `m` and `ef_construct` are chosen deliberately, not left at the defaults.
- [ ] The `ef` curve is swept on your own data, the knee is found, profiles for different paths are set.
- [ ] It is decided whether to enable quantization, and if so, with rescore or deliberately without it.
- [ ] A tenant isolation model is chosen, its memory cost is calculated.
- [ ] The list of filter fields is fixed, payload indexes are created **before** loading.
- [ ] Strict mode is on: a query with a filter on an unindexed field fails instead of being slow.
- [ ] The database version is pinned, the changelog is read, calls are on the current endpoint.
- [ ] There is a verified restore from backup, not just a configured backup.
- [ ] A weekly recall cross-check against exact brute force and an alert at your own threshold are in place.
- [ ] The threshold at which this decision is revisited is written down: number of vectors, volume or latency.

---

## Public links

- Qdrant documentation, the sections on search, quantization, multi-tenancy, the optimizer and snapshots:
  https://qdrant.tech/documentation/
- Qdrant changelog (check what your version does): https://github.com/qdrant/qdrant/releases
- pgvector, README with index parameters and release notes: https://github.com/pgvector/pgvector
- Curator, a measurement of the price of tenant isolation: https://arxiv.org/abs/2401.07119
- DiskANN, source code and paper: https://github.com/microsoft/DiskANN
- ANN-Benchmarks, a set of public measurements and a warning about their conditions:
  https://github.com/erikbern/ann-benchmarks
- Weaviate, documentation on backups and multi-tenancy: https://weaviate.io/developers/weaviate
- Milvus, documentation on compaction and garbage collection: https://milvus.io/docs
