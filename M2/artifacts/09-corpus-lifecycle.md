# Corpus lifecycle: updates, deletion, versions, migrations

> Module 2 artifact. Checked on **10.08.2026**. This is the most boring layer of RAG and the most
> common reason a working pilot falls apart a quarter later.

## What this is and how to use it

Building an index is easy. What comes next is what tutorials do not cover: a document is edited at
the source, another is deleted, a third is re-chunked, the embedder is swapped, and the system
learns nothing about any of it and keeps answering confidently from text that no longer exists.

What makes this layer special is that **an error here does not drop a metric and does not raise an
exception**. A stale vector does not throw an error, it just keeps being found. Vector similarity
has no time dimension: an orphaned fragment matches exactly as well as it did on the day it was
written.

Connect this file to your agent, describe your corpus (where the documents come from, who edits
them and how often, whether deletion exists, whether there are retention deadlines) and go through
the "Brainstorm questions" section. The output should be four things written down in the project
repository: **a chunk identifier scheme, a way to detect changes and deletions, a set of lifecycle
fields in the metadata, and a freshness class for each document type.**

The first of these is irreversible. An identifier cannot be overwritten in any database, because it
is the key, so changing it after the fact is a full migration.

---

## Map of the set: this file is one of twelve

The module's artifacts take the pipeline apart layer by layer, and the decisions in them are
coupled: the upper bound of a chunk runs into the embedder's window, the metadata schema determines
what you can filter by at search time at all, and cost is the sum of decisions from every layer at
once. That is why the files live in one folder and are meant to be used together: this one is read
in full, the others are opened as needed.

> **Instruction to the agent.** You are reading one file of twelve; the others lie next to it, in
> the same folder. As soon as the conversation goes beyond the boundary of this layer, open the
> relevant file and read the corresponding section before advising. Do not retell the neighboring
> layer from memory: the artifacts contain thresholds, figures with measurement conditions and
> failure modes that general knowledge does not. Read on demand, not everything at once: this file
> first, then whatever the conversation needs. If the file you need is not there, say plainly which
> one is needed and ask for it instead of guessing. When a decision in one layer breaks a decision
> in a neighboring one, say so right away, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at ingestion |
| [`02-metadata.md`](02-metadata.md) | Metadata | you are deciding which fields go next to a chunk: source, freshness, permissions, version, and what to filter by afterwards |
| [`03-chunking.md`](03-chunking.md) | Chunking | you are choosing size, boundaries and overlap; questions about tables, code and structural splitting |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | you are choosing a model for the language and domain, dimensionality, local or via API; the cost of switching models |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, fusing the branches, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanism, source citation, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletion, record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reduction |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End to end | checking what has been built: errors where the pipeline runs and the metrics are green but the system lies; a checklist of 24 checks |

**Closest connections of this layer.** Everything rests on the chunk identifier, and it is designed
together with the splitting ([`03-chunking.md`](03-chunking.md)); statuses, versions and hashes are
stored in fields ([`02-metadata.md`](02-metadata.md)). Update triggers come from the sources
([`01-data-preparation.md`](01-data-preparation.md)), migration on a model change comes from
[`04-embeddings.md`](04-embeddings.md), deletion on request and its deadlines come from
[`10-security.md`](10-security.md), and the economics of incremental versus full run comes from
[`11-economics.md`](11-economics.md). A practical walkthrough of orphans and three questions for ID
design are in §3, the two-hash mechanism is in §4.2 of
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

**Reference for the same layer.** The same territory from another side is covered by
["Vector database lifecycle and code indexing"](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M2/reference/vector-db-lifecycle-and-code-indexing.md)
— it lives in the module repository, in the `M2/reference/` folder, and is read together with this
file. Here are the mechanics and decisions of the layer; there are three things that are not here:

- **a six-level update maturity ladder** (full rebuild → deterministic identifiers → deletion by
  source → hashes → record manager → statuses and versions), with a practical rule for the volume
  of changes at which incremental stops paying off;
- **ready-made record managers** - LangChain Indexing API, Flowise, LlamaIndex: what each does out
  of the box, where its boundary lies and what none of them does automatically; plus a checklist of
  seven questions for your own solution;
- **code indexing** as a separate discipline: how it differs from indexing documents and which
  tools it is done with.

To the agent: if the conversation moves to choosing a ready-made update tool or to indexing a code
repository, open this reference, these sections are not here.

---

## Map of the layer's decisions

```
1. THREE EVENTS               appeared · changed · disappeared
      ↓ only the first one is caught by itself
2. STABLE CHUNK ID            warning: irreversible, set today
      ↓
3. CHANGE DETECTION           content hash · events · transaction log
      ↓
4. DELETION DETECTION         marker in the source · list reconciliation
      ↓ a timestamp never catches deletions
5. CHUNK STATUS               current · superseded · deleted · failed · quarantined
      ↓ the status filter lives in the search query itself
6. PHYSICS OF DELETION        invisible · not in the index · not in the bytes
      ↓
7. INDEX VERSION              six independent parts, a tag on every query
      ↓
8. MIGRATIONS                 dual write · history backfill · atomic switch
      ↓
9. FRESHNESS AS AN SLA        three tiers, the class is assigned at ingestion
      ↓
10. DERIVED INVALIDATION      summaries · graph · answer cache · traces
```

**Half of the synchronization works by itself, and that is the worst thing that could have
happened.** All databases overwrite a record when inserting under an existing identifier, so
updating looks like it works from day one. That is exactly what makes the second half invisible.

---

## Brainstorm questions with the agent

**1. What does your chunk identifier look like, and is it reproducible from the source?**
If the answer is "a random UUID at insert", stop here and fix it. Everything else stands on this.

**2. What happens to the identifiers if you change the chunk size?**
If the identifier has no version of the splitting strategy, you will get collisions: two different
sets of parameters under one label.

**3. Who learns that a document changed at the source, and how?**
Check separately: a "file updated" event is not the same as "the text changed". Someone rewrote the
metadata in the cloud drive, and the trigger honestly fired.

**4. Who learns that a document was deleted, and how?**
The most common honest answer: nobody. Then you need a scheduled list reconciliation, and it has to
be set up now, not after the first incident.

**5. What happens when a document is re-chunked and there are fewer chunks?**
If there is no answer, orphaned fragments accumulate: there were ten, now there are six, four
identifiers stayed in the index.

**6. Where does the source text live, separately from the vectors?**
If there is nothing to re-embed from, a migration turns into re-parsing the whole corpus.

**7. Which lifecycle fields are in the metadata right now?**
Adding them later means going through the whole corpus. The minimum set is in the section on
statuses.

**8. Is the status filter in the search query itself, or in code on top of it?**
If on top, a soft delete does not work as a deletion: a single code path that forgot to filter is
enough.

**9. What freshness class does each of your document types have?**
Not "we need it fresh", but per type: prices a minute, regulations a day, architecture decisions a
quarter.

**10. How much does one full run of your ingestion pipeline cost, and how much an incremental one?**
The difference is usually two orders of magnitude. If you do not know both figures, you do not know
when the pipeline becomes unprofitable.

**11. What will you do when it is time to change the embedder?**
The right answer contains the words "dual write" and "parity gate", not "we will reload it
overnight".

**12. How will you know the index has diverged from the source?**
The reconciliation job must not end with a line saying "success": its output is numbers, examples
and failed probe queries.

**13. What derived artifacts do you make from the documents?**
Summaries, graph nodes, answer cache, pre-joined representations. Each keeps looking healthy when
it has gone stale.

**14. By what key is your answer cache invalidated?**
The cache key is the query, and what changed is the source. There is no link between them until you
build one.

**15. Does your test set contain deliberately deleted and deliberately outdated cases?**
The "the deleted is no longer found" test is production behavior, not housekeeping.

**16. What is recorded on every query: the index version and the model version?**
Costs nothing, pays off on the first "why did it get worse after the rollout" investigation.

**17. If a requirement arrives tomorrow to delete a specific person's data, how long will it take
and how will you prove it?**
Details are in the security artifact; what matters here is that the granularity of deletion equals
the granularity of a chunk, and that is set at design time.

---

## Foundation: a stable identifier and three operations

**Every chunk carries a deterministic identifier reproducible from the source.** Not a UUID at
insert, but `doc-4711:chunk-3` or a hash of `source:primary_key:chunk_number`. With a stable
identifier an update is an overwrite under the same key, and a deletion is a deletion by key.
**Without it a new vector is indistinguishable from an updated one, and there is nothing to find the
needed vector by.**

All synchronization is described by three operations: **upsert, delete, skip**.

Two live bugs that repeat everywhere:

- In a worker, points were written with a random UUID on every run, and the document record in the
  main database was written in a separate call. A failure on the second step sent the document to a
  retry, the retry generated new identifiers, and the collection accumulated a set of points
  **that the application no longer holds a single reference to**. The fix: a deterministic UUID
  version 5 from `${docId}-chunk-${i}` under a fixed namespace, so that a retry becomes safe.
- In another product the identifier from the request was accepted and echoed back in the response,
  but a fresh random one was stored anyway. Re-uploading the same document produced duplicates,
  **and there was no path at all from the logical identifier to the chunks it generated**.

Warning: **A subtlety about the key itself.** An identifier made only of position (`doc:chunk-3`)
breaks on an edit at the start of the document: the boundaries shift, and every following chunk
changes. An identifier made only of a content hash loses order, and you cannot tell whether a chunk
is new or is a re-split version of an old one.

**A working compromise:** the version of the splitting strategy inside the identifier namespace,
for example `v2_recursive_512_50_<doc>_<hash12>`, and the same version as a separate metadata field,
so that you can ask for "all chunks of version v1". **A strategy version number is never reused**,
even for a minor edit.

**How to fix it after the fact.** There is no direct identifier overwrite in any database. So this
is the same migration as an embedder change: a second collection with new keys, dual write, a
background backfill **from the source of truth, not from the old index**, an atomic switch of reads.
The only difference is that re-embedding is not required: if the model is the same, the vectors are
carried over, you pay for writing and building the index, but not for the model's work. In one
public write-up such a repair required an operation log of thousands of rows with a cross-check
before every write.

---

## Detecting changes and deletions

**A content hash per chunk is the main cost lever in the whole pipeline.** An edit to a document
usually touches one or two chunks out of dozens.

| Signal source | What it catches | What it does not catch |
|---|---|---|
| Polling by modification time | new and changed | Warning: **never catches deletions**: a hard-deleted row cannot be queried |
| Webhooks and connectors | what the source reports on its own | everything the source is silent about, including permission changes |
| Transaction log (CDC) | inserts, changes **and deletions**, without load on writes | the price: event ordering, repeats, a queue for parsing failures |

When the source does not report deletion, and that is the norm, there are two answers, and they are
not interchangeable. **A deletion marker in the source**: the source sets `deleted_at` instead of
physically deleting, ingestion sees the flag and removes the vectors by identifier. Requires
authority over the source's schema. **List reconciliation**: all identifiers in the source and in
the index are periodically enumerated, and everything in the index without a pair is deleted. Works
always, costs a full enumeration, and catches what slipped past the other mechanisms.

A third case that gets forgotten: **orphaned chunks after re-splitting**. The rule is simple: after
writing a document, always compare the current set of its `chunk_id` values with the previous one
and finish off the difference.

### What triggers a corpus update

The table is compiled from an analysis of live builds on low-code orchestrators. Read it with one
thought in mind: the first two rows cover appearance and edits, and nine pilots out of ten stop
there.

| Trigger | What it covers | What we pay |
|---|---|---|
| File trigger "created" | a new document appeared | this is polling, not an instant notification: a delay of up to the interval |
| File trigger "modified" | a document was rewritten | **an edit event is not the same as a text change**, you need a content hash right after the trigger |
| Schedule, minutes | **deletion**, which the file trigger does not catch | idle runs |
| Schedule, nightly | list reconciliation and orphan cleanup | divergence is visible once a day |
| Webhook | a change on the external system's side | needs access and setup on the source's side |
| Manual launch | initial load, rebuild | a human has to remember |

Warning: in an inventory of 26 analyzed ready-made builds, **not a single file trigger reports a deletion**.
Wherever deletion is handled at all, a separate branch with a scheduled reconciliation has been set up for it.

---

## Record manager: how it detects, what it cleans with, when to take it

A record manager (a ledger of what has been loaded) answers exactly four questions: **what counts as
a document's identity · how to tell a text edit from a metadata edit · how to learn that a document
has vanished from the source · what the accounting granularity is, chunk or document.**

The data below was obtained by reading the source code of three public implementations and running
behavior matrices on two documents, 07-10.08.2026. The fourth column is not a product but a scheme
that people write themselves when metadata lives a life separate from the text.

| | Own accounting on two hashes | Flowise | LangChain | LlamaIndex |
|---|---|---|---|---|
| Ledger | state table plus a status per store | table of load records | table of load records | document store, hash per document |
| Addressing | **stable identifier from the corpus** | key equals hash | key equals hash | key equals document identifier |
| New detection | no record for the identifier | key not in the namespace | key not in the namespace | no hash for the document |
| Text edit detection | content hash diverged | new key | new key | hash diverged |
| **Metadata edit detection** | **metadata hash diverged, its own branch** | indistinguishable from text | indistinguishable from text | indistinguishable from text |
| Deletion detection | difference between active identifiers and the export | only `Full` mode | only `full` mode | only the mode with deletion |
| Cleanup modes | a flag that disables deletion detection | None / Incremental / Full | none / incremental / full / **scoped_full** | upserts / duplicates_only / upserts_and_delete |
| Granularity | chunk | chunk | chunk | **source document** |
| **A single tag edit costs** | **column updates, the vector is intact** | re-embedding | re-embedding | re-embedding |
| When to take it | the corpus is produced by your own pipeline, metadata is often normalized | low-code setup, you need a visible chunk and a button | you are already on it, you need per-chunk accounting and the `scoped_full` mode | you are already on it, per-document accounting is acceptable |

**The main conclusion of the comparison.** Three public implementations out of three compute the
content hash and the metadata hash separately, **and then glue them into a single key**. The
meaning: an edit to one tag is indistinguishable from an edit to the text, so it costs a new
embedding and a new insert. The scheme with two independent hashes turns a tag edit into an ordinary
column update with the vector untouched.

The cost of the decision is computed on a napkin: the share of documents in which only metadata
changed over a year, multiplied by the cost of embedding the corpus. If you have a tag dictionary
that is constantly being normalized, that share is large.

**How cleanup works inside.** All of it rests on a single line: for every document of the batch,
**including those skipped as unchanged**, the last-touched time is updated. So "not updated in this
run" is identical to "stale", and the mode boils down to deleting everything older than the run's
start time. Hence the main danger of the `full` mode: if the loader returned an incomplete export,
the mode will honestly throw out of the index everything that was not in the export.

**Five selection rules.** Metadata changes separately from text and often → you need a split hash,
no ready-made implementation provides one. The loader may return an incomplete export → **never
`full`**. You need to delete individual chunks, not the whole document → per-chunk accounting. The
pipeline is already written as code → take what detects a change in the transformation code itself.
The database cannot delete by metadata filter → the per-document accounting option is out.

Warning: **A ready illustration of silent degradation.** The "duplicates only" mode on three runs
gives 3, then 5, then 7 live vectors on the same two documents. It protects only against re-uploading
a byte-for-byte identical input. Any edit is a new hash, which means new chunks on top of old ones
that nobody removes. The index quietly fills with mutually contradictory versions of one document.
And separately: in one of the implementations, when there is no vector database, the "upsert" mode
**silently becomes the "duplicates only" mode**, while the object's property afterwards still reads
as the original. The conclusion: **check the effective mode by running two documents, not by reading
the config.**

---

## Chunk status: what each value means

The status is moved out into an explicit metadata field. The ingestion pipeline moves it, and the
search query filters on it **by default**. The point is for the state to live in the retrieval path,
not in a background job's log.

| Status | What it means | When it is set | Visible to search |
|---|---|---|---|
| `current` | the active version of the chunk, the only one in its place | after a successful embedding and write to the index | yes, this is the default filter |
| `superseded` | the text is replaced by a newer version, the chunk itself still lies there | at the moment the new version of the same logical chunk is written | no. Kept for audit and rollback, cleaned on a schedule |
| `deleted` | the document is deleted at the source, the chunk is due for physical deletion | on a deletion event or as a result of list reconciliation | no. Time passes between this status and the actual deletion from the index, and that is normal |
| `failed` | processing failed: the parser crashed, the embedder returned an error, the schema did not match | at the moment of failure, together with the reason and the number of attempts | no. **What matters is that a record exists**: a silently lost document is worse than a visible error |
| `quarantined` | the document is accepted but not trusted: it came from a semi-open channel, failed the integrity check, is marked as suspicious | at ingestion, before embedding or right after | no, until a human decides. Handled by a separate queue |

Next to it in the schema, and this is the minimum set of lifecycle fields: the source identifier
and the source system itself · the modification time at the source and the ingestion time · the
chunk identifier · the chunk's sequence number · the chunk hash · the parser version · the embedding
model version · the tenant and access permissions.

**Adding these fields later means going through the whole corpus.** Set them up on day one, even if
half of them are not filled in yet.

### Index drift: six reconciliation questions

Drift is the divergence of the index from the source of truth. Reconciliation runs along five axes:
records, chunk hashes, deletion markers, embedder version, search results. The reconciliation job
answers six questions with numbers and examples:

1. Does every active chunk point to an active source?
2. Does every active source have its expected current chunks?
3. Did the text change at the source without a change of the chunk hash?
4. Did a chunk's text change without a new embedding?
5. Are deleted and superseded chunks still being found?
6. Have chunks computed by the old model been mixed into the current path?

On top of that, probe queries: ask about a document that is deleted and must not be cited · a
question where the old and the new version coexist, and require that the current one wins · a point
query by identifier after deletion, and require emptiness.

---

## Physics of deletion: three meanings of one word

| Meaning | What achieves it | When it happens |
|---|---|---|
| Invisible to queries | the delete call itself | immediately |
| Absent from the index, not traversed by the graph | vacuum, compaction, marker cleanup | on a threshold, in the background |
| Absent from the bytes on disk | rewriting pages, expiry of backups, logs and replicas | on a schedule, **which you set** |

**A system can be fully correct in the first sense and fully non-compliant in the third, and no
query will show this difference.**

What the delete call does in different databases and when the space is freed:

| Database | What the call does | When space is freed | Pitfall |
|---|---|---|---|
| pgvector | marks the row deleted, it is invisible immediately | `VACUUM` removes dead rows and asks the index to relink neighbors. The space goes back to the free space map, **not to the operating system** | autovacuum triggers at about 20% of the table changed, which for a large vector table is a great many dead records. Tune the thresholds on the table itself |
| Qdrant | soft delete through a bitmask, the point is unavailable immediately | the vacuum optimizer, thresholds are **per segment**: deleted fraction 0.2 and a minimum of 1000 vectors | Warning: the default number of segments equals the number of cores per shard, so **on a small volume cleanup never triggers** |
| Weaviate | a deletion marker on the object | marker cleanup at an interval plus storage compaction | default parallelism is half the cores, cleanup is **interrupted when memory runs short** |
| Milvus | logical deletion, a bitmask is built at query time | compaction rebuilds the segment and **re-indexes it**, then the garbage collector deletes the files | deleted fraction threshold 0.2, checked every 60 s. Warning: the threshold must not be set to zero: every deletion would start rebuilding a segment |
| Chroma | a mark in the index library | Warning: **not freed**: replacement of deleted entries is off by default | maintainer's measurement (02.08.2024): after 500 thousand add-and-delete cycles at 1536 dimensions **the index grows to about 3 GB with zero live records**. Cured only by a rebuild |
| Pinecone | deletion by identifier, by metadata, namespace wipe | Warning: **the compaction schedule is not documented** | deletions spend write units, that is **deletion is a paid operation**. The limits on deletion by metadata are hard |
| turbopuffer | a record in a log on object storage | compaction is periodic, in its own setup there are explicit trigger operations | Warning: a namespace branch is a copy-on-write clone: **deleted data may continue to live in the branch** |

Warning: check the thresholds and defaults against the documentation on the date of your work: some of the
values in the sources come without a measurement date. Separately, check on your own account whether
your plan supports deletion by metadata filter: on this question a claim circulates in blogs that the
official documentation does not confirm.

**What happens to quality while dead records lie in the graph.** Traversal spends steps on
candidates that are then discarded: at 20% deleted, a search parameter of 40 works as 32. This is
arithmetic from the share of dead candidates, not a measurement, but the direction is right and can
be verified on your own index.

**A check worth keeping in the tests:** take the vector of a deleted record as a query, set the search
parameter to a thousand, and require that it not be in the first hundred. **This is the hardest case
for an index to hide.**

**What a query cannot prove:** that the bytes are not in a backup, a log, on a replica, in a snapshot
or in an unoverwritten block. This is a statement about retention policy, and it has to be
formalized as a policy.

---

## Index versioning

**An index version is not a snapshot of vectors.** An index is a composite artifact made of **six
independently changing parts**: the document corpus · chunk boundaries · the embedding model · the
ANN index structure · metadata and filters · prompt templates. If you version the vectors and do not
version the splitting strategy, the same document will be split differently and answer differently,
**and the version history will lie**.

**Maturity levels, of different cost.** Level 0: tag every query with the index version and the
model version. Costs nothing, can be done today. Levels 1 and 2: a version manifest (a set of
document hashes, the document count, the last-modified time) and switching through an alias. Levels
3 and 4: a full audit trail with metrics tied to version transitions, when a regulator requires it.

**A cost antipattern:** snapshotting the whole index when it is enough to save the set of document
hashes, the model version and the config in order to rebuild on demand.

### What it looks like in code

A version manifest, a file next to the pipeline config:

```json
{
  "index_version": "kb-2026.08.10-1",
  "created_at": "2026-08-10T09:14:22Z",
  "components": {
    "corpus_snapshot": "sha256:9f2c...",
    "chunker": { "strategy": "recursive", "size": 512, "overlap": 64, "version": "v2" },
    "embedder": { "name": "text-embedding-3-small", "dim": 1536, "input_type": "passage" },
    "ann": { "type": "hnsw", "m": 16, "ef_construct": 200, "quantization": "int8" },
    "metadata_schema": "v4",
    "prompt_template": "answer-with-citations@v7"
  },
  "doc_count": 10432,
  "chunk_count": 71218
}
```

A version tag in the metadata of every point and in every query trace:

```json
{
  "id": "v2_recursive_512_64_doc-4711_a91c3e0b",
  "payload": {
    "doc_id": "doc-4711",
    "chunk_index": 3,
    "status": "current",
    "content_hash": "sha256:4b7d...",
    "meta_hash": "sha256:0ac1...",
    "index_version": "kb-2026.08.10-1",
    "embedder": "text-embedding-3-small",
    "source_updated_at": "2026-08-09T18:02:11Z",
    "ingested_at": "2026-08-10T09:20:03Z"
  }
}
```

In the response log:

```json
{ "response_id": "r-8823", "index_version": "kb-2026.08.10-1",
  "embedder": "text-embedding-3-small", "chunks": ["...:doc-4711_a91c3e0b"] }
```

**Why this is needed in practice.** The phrase "hallucinations grew by 15% after the rollout" is a
diagnosable statement only when the version number lies in the trace. Otherwise it is a complaint:
search drift is indistinguishable from generation drift, and the investigation comes down to
guesses.

---

## Changing the embedder: one pattern, not two

Changing the embedder generation equals a **full re-embedding of the corpus**, and this is the most
underestimated expense item in production RAG. Doing it lazily, as reads happen, will not work:
search compares the query **against the whole space at once**, so a single old vector in the top ten
is not a small error but a comparison of apples with rulers. The space must be internally
consistent.

**The canonical form, four parts:**

1. **Build a new index alongside.** A separate collection or a separate named vector. The old one
   keeps serving every query.
2. **Turn on dual write.** Every new document is computed by both models and written to both
   indexes. **The step that gets skipped, and skipping it guarantees a broken migration:** while the
   history backfill runs, live traffic keeps changing the corpus, and the new index will be stale
   exactly at the moment the backfill finishes. Write both sides in one transaction, otherwise a
   partial failure will make the indexes diverge with no way to notice it.
3. **Backfill the history in the background.** The discipline: insert only, never overwrite a record
   that dual write has already populated. The "needs backfilling" criterion: the record is not in
   the new index **or the text hash has diverged**. The second condition is mandatory: in migration
   audits, from 4 to 12 percent of the corpus turned out to have been computed from an outdated
   version of the text, because the text was edited after embedding and the embedding was not rerun.
   Anchor the backfill to a position in the source's log, not to the clock: with creation time you
   lose rows inserted between reading the maximum and turning on dual write.
4. **Switch reads atomically.** With an alias, not by editing the application config.

**A gate stands between the third and the fourth.** Shadow queries go to both indexes, the
comparison is logged. What is measured is top-ten overlap and, if labels exist, recall and the
position of the first correct answer. Three independent sources give three different overlap
thresholds, so **what goes on the slide is not a number but a rule: take the threshold from your own
test bench, and the parity curve must rise monotonically.** A plateau below the threshold for an
hour means the problem is in the chunker or the embedder, and finishing the backfill will not cure
it.

**Rollback is a separate piece of work, not a footnote.** The old index is kept alive **and
writing** for at least a week, better two: dual write after the switch continues in the reverse
direction. Stopping it on the day of the switch is a typical mistake, after which a ninety-second
rollback turns into a multi-day re-embedding under a barrage of complaints.

**The real price of a mistake:** a recorded 14% drop in top-ten recall on a key segment when the
embedder was switched, with a forced rollback (an engineering write-up of three real corpora,
02.05.2026).

**An academic alternative that bypasses reindexing:** a trainable adapter layer that maps the new
model's query back into the old index's space. It gives 95-99% of the metrics of a full
re-embedding, under 10 microseconds per query, and is cheaper than a full rebuild by more than a
factor of a hundred (EMNLP 2025). The authors' caveat is honest: **this is postponing, not
cancelling.**

### Four forms of migration

| Form | What exactly breaks |
|---|---|
| Model change at the same dimensionality | The spaces are incompatible. The indexes may share a schema, but not a ranking. Default: dual write. Warning: identical dimensionality is **more dangerous** than a different one: a different vector length is a loud error on the first insert, while two different 1024-dimension models side by side will not give an error at all |
| Dimensionality change | The indexes cannot even share a column type. A separate table, a separate index, a separate build |
| Chunk granularity change | The ratio of document to chunks changes: a 30-page contract gives 60 chunks at 1000 characters and 150 at 400 characters. **Everything outside that is keyed on `chunk_id` loses its meaning.** Rule: do not expose `chunk_id` beyond the service boundary, hand out `(doc_id, range)` instead |
| Database change | A migration tool streams points and rebuilds the index, a snapshot carries over a ready index, a disk backup clones the volume. Each has its own limits, the disk headroom is double |

**The migration window and the incremental backfill are the same window.** While it is open, both
indexes live, dual write runs, the background backfill goes on and parity is measured. There is no
separate "incremental reindexing stage" after the switch: if you needed one, dual write was not
working.

---

## Incremental versus full run

**The trap looks the same for everyone:** the initial indexing script does not distinguish new,
changed and unchanged, it simply processes everything. On 10 thousand documents that is 20 minutes
and a few dollars. Half a year later, on 500 thousand where nightly changes touch 2 percent, the same
script runs for 8 hours, costs about 200 dollars a day and, if it fails midway, leaves the system on
stale data. Incremental on the same data is minutes and about 4 dollars, **a difference of roughly
50 times** (a vendor's calculation by tokens, 20.02.2026, the per-token price is not named: take the
order of magnitude, not the number).

**Two modes of updating a changed document.** *Replace*: delete all chunks, re-split, upload again.
Simpler, guarantees no leftovers, but the identifiers change and external links break. *Per-chunk
update*: hashes at the chunk level, only the diverged ones are updated. More efficient, but requires
tracking the added, deleted and shifted ones.

**Recommendation: start with replace**, move to per-chunk update only if the documents are very
large and the edits are very local.

**The threshold for a full re-creation.** The only numeric formulation found: if more than 80% of the
data changes, it is simpler to re-create everything. The number comes from practice without
justification, so check it on your own corpus. A more reliable framing without a number: a full run
is reserved for a model change and a change of the splitting strategy.

---

## Freshness as an SLA, in plain words

**"The index reflects a change within 60 seconds" and "within 60 minutes" are not two settings but
two different architectures and two different budgets.** The first requires an event stream, a
queue, workers and lag monitoring. The second gets by with a schedule. That is why freshness is a
requirement that is formulated in the first week, not a virtue to strive for by default.

**Freshness is not one number but four independently measured quantities:**

| Quantity | What it means | How to measure |
|---|---|---|
| Content age | how much time has passed since the document's last edit or check | median and 95th percentile across the corpus |
| Embedding lag | how much time passed between the edit and the appearance of a new vector | a histogram by pipeline stage |
| Share of stale retrievals | in which queries content actually surfaced whose embedding is older than the source's edit | computed from traces, not from the corpus |
| Coverage drift | what made it into the corpus and what is missing from it | list reconciliation |

A document can have a small age and a large lag, and vice versa. **A low queue lag does not mean
fresh search**: the topic can be fine while the retrieval layer is stale, because embeddings, metadata
writes, the index update or cache invalidation are lagging.

**Three ingestion architectures and their windows** (the figures agree across several independent
authors): a nightly batch up to 24 hours · an hourly batch up to 60 minutes · a stream through the
transaction log a few seconds, **but only for sources that report changes**. The complexity of the
streaming setup is roughly three times that of the batch one.

**The second multiplier is corpus size.** On a thousand documents, hourly freshness is achieved by a
naive full rebuild. On a hundred thousand the same architecture gives a half-day floor. On a million,
a multi-day lag becomes the norm. **The architecture that worked in the pilot is exactly the one that
quietly rots in production.**

**A practical conclusion that changes the design: the freshness class is assigned at ingestion, not
at query time.**

| Tier | Tolerance | What goes here | Mechanism |
|---|---|---|---|
| Hot | minutes | prices, stock levels, flags, safety warnings | webhooks, transaction log |
| Warm | hours or a day | all incremental logic, tickets, correspondence | incremental batch |
| Cold | a month or a quarter | architecture documentation, regulations, historical materials | infrequent rebuild |

**Running everything on one schedule means simultaneously overpaying for the cold and being late on
the hot.**

Separately, about the recovery budget: how long the system takes to catch up after a failure, a
replay or a rebuild. This budget is what exposes fragile designs. A quiet pipeline holds its target
for weeks and misses exactly on a priority rebuild.

And an honest caveat: **freshness is not always needed.** For agentic scenarios over a codebase the
opposite production experience is found, where a ten-day-old index is entirely acceptable, because
the consumer is an agent tolerant of inaccuracy, and the price of an error is one extra text search.
This is a different class of tasks, and it legitimately lives in the cold tier.

---

## Invalidating derived artifacts

**Reindexing a changed document is not enough.** Derivatives have already been made from it:
embeddings, summaries, graph nodes and edges, a search result cache, an answer cache, pre-joined
representations. **Each keeps looking healthy: a stale summary reads well, a stale embedding returns
results, nobody throws an exception.**

**The directionality rule.** A derivative is built from the canonical, never the other way around.
Provenance points from the derivative to the canon, and points not just to a record but to its
version. **A check of the separation's cleanliness: delete the derived layer entirely and rebuild it
from the canon. If that does not work, there is no separation.**

**Three policies for a change of the canon**, chosen per artifact type, not globally: *rebuild*
(the default for projections and chunks) · *delete* (when the derivative has lost its meaning: the
representation of a deleted record must disappear, not be updated) · *flag* (for snapshots: the
summary stays but gets a stamp "made from version 3, now version 5").

**The answer cache is a separate and the most underestimated case**, because the cache key (the
query) has nothing to do with what changed (the source). Two working approaches: a key that includes
everything that changes the output (prompt version, corpus version, tool schema, model, query), or a
reverse index "document → answers", where each cached unit holds a list of cited sources with hashes
and versions. The first is simpler, but wipes the whole cache on any corpus change. The second gives
targeted invalidation and skips idle edits: if a file is rewritten byte for byte, nothing is
invalidated. A measurement of the reverse index on a trace of 2230 queries: **53.27% of model calls
skipped with zero stale results served.**

Warning: **A semantic cache amplifies hallucinations.** One wrong generation is served to all
semantically close queries, and the error accumulates instead of fading.

Warning: **The "hit worse than a miss" trap.** A summary was cached instead of raw chunks to save
tokens, then a query arrived about a special case that the summary discarded. The cache "hit"
because the topic matched, whereas ordinary search would have fetched the raw chunk with the
exception. The metric to watch: the share of hits that had to fall back to the raw.

Warning: **The graph is the worst case of invalidation.** In the best-known implementation,
incremental update is **append-only**: changing an existing document requires a full recompute,
deletion is officially unsupported, and the maintainers do not announce plans to invest in it. The
pattern that survived: at ingestion, resolve entities, update nodes and edges, find the affected
communities and **mark their summaries invalid without rebuilding**, and regenerate on demand.

---

## Common mistakes

| What not to do | What it leads to | What to do |
|---|---|---|
| A random identifier at insert | A retry after a failure breeds points that have no references and there is nothing to delete them by | A deterministic identifier from the source, with the splitting strategy version inside |
| Assuming synchronization is set up because reindexing passes without errors | The system answers from a paragraph that was deleted half a year ago. The log is clean, the metrics are green | The deletion path is designed at the same time as the insert path |
| Catching changes by polling the modification time | Deletions are never caught: a deleted row cannot be queried | A deletion marker in the source or scheduled list reconciliation, preferably both |
| Leaving the record cleanup mode at its default | The default deletes nothing, old versions stay in the database and keep being found | Choose the mode deliberately, knowing whether the loader can return an incomplete export |
| Treating a `200 OK` from a deletion as confirmation of the deletion | Space is not freed, recall drops on dead records, the obligation to the customer is not met | Find out your database's compaction thresholds and assign an explicit cleanup on a schedule. **A promise about deletion is a promise about the compaction schedule** |
| Filtering the status in code on top of search | One code path forgot the filter, and the soft-deleted came back into the results | The status filter inside the search query itself |
| Changing the embedder without dual write | The new index goes stale exactly by the end of the backfill, and this is discovered only after the switch | Four steps and a parity gate, the old index alive and writing for another week |
| Keeping one update schedule for the whole corpus | Simultaneous overpaying for cold documents and being late on hot ones | A freshness class per document, assigned at ingestion |
| Not versioning the index | Search drift is indistinguishable from generation drift, the investigation comes down to guesses | An index version and model version tag on every query. Costs nothing |
| Forgetting about derived artifacts | The document is updated, while the summary, the graph and the answer cache keep answering with the old one, and nobody throws an exception | A policy for each type of derivative and the "delete and rebuild from the canon" check |

---

## Layer readiness checklist

The first three items are irreversible: after the fact they cost a full migration.

- [ ] The chunk identifier scheme is fixed, the splitting strategy version is part of it.
- [ ] The source text and metadata are stored **separately from the vectors**.
- [ ] Lifecycle fields are set up in the metadata from day one, even if unfilled.
- [ ] The status filter is in the search query itself.
- [ ] Change detection is built on a content hash, not on file time.
- [ ] Deletion detection is set up explicitly: a marker in the source or list reconciliation.
- [ ] The record cleanup mode is chosen deliberately and checked by running two documents.
- [ ] The compaction schedule of your own database is found out and written down.
- [ ] A freshness class is assigned to each document type, the update tier for it is chosen.
- [ ] An index version and model version tag is written on every query.
- [ ] The test set has deliberately deleted and deliberately outdated cases.
- [ ] A policy is written down for each derived artifact: rebuild, delete or flag.
- [ ] An embedder migration plan is written, including the rollback window.
- [ ] It is decided whether personal data enters the corpus, and if so, isolation at ingestion is designed.

---

## Public links

- Qdrant, optimizer and vacuum, snapshots, named vectors: https://qdrant.tech/documentation/
- Embedder migration without downtime: the database tutorials section of the Qdrant documentation.
  Warning: the tutorial itself says the recipe covers only insertion: deletions and partial updates
  are paused for the duration of the migration
- pgvector and vacuum in Postgres: https://github.com/pgvector/pgvector and
  https://www.postgresql.org/docs/current/routine-vacuuming.html
- Milvus, compaction and garbage collection: https://milvus.io/docs
- Weaviate, deletion marker cleanup: https://weaviate.io/developers/weaviate
- LangChain, indexing and cleanup modes: https://python.langchain.com/docs/how_to/indexing/
- LlamaIndex, document store strategies: https://docs.llamaindex.ai/
- An adapter instead of reindexing: an EMNLP 2025 paper on mapping the new model's space into the
  old index's space (search by the keywords "embedding space alignment",
  "backward-compatible embeddings")
- A cache with a reverse dependency index: https://arxiv.org/abs/2607.26076
