# Vector database lifecycle and code indexing

A Module 2 reference. Two topics that came up in the session but deserve a separate
text: **how to live with a vector database after the first load** (updates, deletion,
consistency) and **how code indexing differs from document indexing**
(the promised links to tools are in the second part).

The material was compiled anew from open sources; all links are public.

---

## Part 1 · Updates and deletion: the maturity ladder

A vector database does not keep track of anything by itself. It will accept identical chunks without objection,
will not notice that the source document has been deleted, and will not tell you that half the points were loaded with a different
embedding model. All of this is the job of your ingestion layer, and it is done at one
of six maturity levels. Each next one is more expensive but closes a class of problems
that the previous one leaves open.

### Level 0 - full rebuild of the collection

Tear down the collection, recreate it, load again. For a corpus of 15-30 documents this is a
**normal strategy**, not a sign of immaturity: a minute of work and cents on embeddings.
A practical rule: **if more than ~80% of the data has changed, rebuild everything**;
incrementality does not pay off at that volume of changes.

What to take into account: a head-on rebuild leaves a window when the database is empty or half full.
The production variant is to build a new collection alongside and atomically switch an alias to it
(in Qdrant this is a built-in mechanism):
https://qdrant.tech/documentation/concepts/collections/#collection-aliases

### Level 1 - deterministic IDs: overwrite without duplicates

The point identifier is computed from the content or address of the chunk (`uuid5(namespace,
source::chunk_index)`, a hash of `source::section::n`, and so on). Re-loading the same
document overwrites the same points instead of breeding copies.

**The trap this level is silent about: orphaned chunks.** Deterministic IDs
overwrite but do not delete. A document was cut into 12 chunks, after an edit it
is cut into 9 - points 10-12 keep living in the database: they are found by search, they are stale,
and they are not visible in the point counter. The same happens when the chunking rule changes across the whole corpus.

### Level 2 - delete-then-upsert by source

Before loading a document, delete all its points with a filter on `metadata.source`, then load
the fresh ones. This closes orphans within a document. In Qdrant it is a single call
`POST /collections/{name}/points/delete` with a filter:
https://qdrant.tech/documentation/concepts/points/#delete-points

**What this level still does not see: documents deleted from the corpus.** Cleanup is tied
to loading a file; a file that has disappeared from the corpus is not loaded by anyone - so nobody
cleans it up either. A periodic reconciliation of the list of sources in the database against the list in the corpus is needed.

### Level 3 - hashes: do not re-embed the unchanged

Store a hash of its content next to the chunk and compare before loading. The advanced
variant is **two hashes, separately**: a hash of the text being vectorized and a hash of the metadata. Then there are
three outcomes instead of two:

- content changed → re-embedding + upsert (the expensive branch);
- only metadata changed (status, permissions, date) → update the payload without recomputing
  the vector (the cheap branch);
- nothing changed → skip.

On a corpus where edits are pinpoint, this cuts embedding costs several times over: you pay
only for what actually changed.

### Level 4 - record manager: an external state registry

A separate table (SQLite/Postgres) that remembers which documents and chunks are already in the database,
with which hashes and when they were loaded. This is the only level that closes the full
lifecycle: new documents are added, changed ones are updated, **ones deleted from the
source are deleted from the vector database**, duplicates do not get through.

Ready-made implementations are in the next section. The DIY variant is an ordinary relational
table plus three rules: hash matched → skip; hash changed → update; a document
arrived without a chunk that was there before → delete.

### Level 5 - statuses, versions, triggers

What distinguishes a training pipeline from an operated one:

- **embedding model version** in the collection metadata, checked before every run
  (a mismatch between the ingestion and search models breaks results silently - there is no error, and no meaning either);
- **chunk statuses** (`active` / `stale` / `failed`) instead of immediate deletion -
  stale content is marked first and physically cleaned up in a separate pass;
- **update triggers**: a webhook from the source (real time), a scheduler (once a day),
  a periodic full reconciliation for deletions. The choice of trigger is a decision about data,
  not about code: how quickly does staleness become a lie?

---

## Part 1a · Ready-made solutions: what you get out of the box and where their limits are

### LangChain Indexing API (RecordManager)

The canonical implementation of level 4. `index()` takes documents, a record manager
and a vector store; it hashes the content, skips the unchanged, and cleans up the stale.
Documentation: https://python.langchain.com/docs/how_to/indexing/

Four cleanup modes: `None` (delete nothing), `incremental` (continuously clean old versions
of changed documents as loading proceeds), `full` (delete everything absent from the current
load - catches deleted documents but requires feeding in the whole corpus at once),
`scoped_full` (like full, but within the bounds of the source ids seen).

**Known pitfalls:** in `incremental` mode all chunks of one document must land
in one batch, otherwise the API does extra work - it deletes and reloads the unchanged
(the final state is correct, but tokens for embeddings were wasted). With the default
`batch_size=100` this bit many people:
https://github.com/langchain-ai/langchain/issues/22135
`full` mode with a loader that does not return the whole corpus **will delete what it should not** -
this is stated directly in the API warning.

### Flowise Record Manager

If you built RAG in Flowise: its Record Manager is the same LangChain mechanism,
exposed in the UI. SQLite / MySQL / PostgreSQL nodes; every chunk is hashed on upsert,
an existing hash means a skip; the cleanup modes are the same Incremental / Full.
Documentation: https://docs.flowiseai.com/integrations/langchain/record-managers
Document Store combines loader + splitter + upsert + record manager in one place:
https://docs.flowiseai.com/using-flowise/document-stores

**Limits:** the SQLite variant slows down at large volumes and frequent updates - for
such a profile people take the Postgres node. And this is document management, not the full lifecycle:
update triggers (on a schedule, by webhook) are still assembled outside it.

### LlamaIndex IngestionPipeline + docstore

The same pattern in the LlamaIndex ecosystem: a pipeline with an attached docstore deduplicates
by document hash and supports the `upserts` / `duplicates_only` strategies.
https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/

### n8n

There is **no** built-in record manager in n8n nodes - this is a known limitation. The working
scheme shown in the session: file hash (Crypto node) → check against a registry
(a table in Postgres/Supabase) → new / changed / unchanged → for a changed one,
delete the points by `file_id` and load again.

### Mature ready-made solutions

Checked against the repositories on 21.08.2026 (stars rounded). The order is from "a data layer under your
database" to "a platform with its own stack": the further right on this scale, the less the solution resembles
"plugged into your own Qdrant collection" and the more it resembles "moved into someone else's product".

| Solution | Stars | What it gives for the lifecycle | Where the limit is |
|---|---|---|---|
| **Airbyte** — https://github.com/airbytehq/airbyte | ~22k | An ELT platform with vector destinations (Qdrant, Pinecone, Weaviate, Milvus, Chroma): hundreds of sources, sync modes up to Incremental Append + Deduped, chunking and embedding built into the destination connector. Official Qdrant guide: https://qdrant.tech/documentation/data-management/airbyte/ | Chunking and the choice of embedder are limited to what the connector can do; the Overwrite mode recreates the whole collection |
| **dlt** — https://github.com/dlt-hub/dlt | ~6k | An ELT library in Python (not a platform): incremental loading, merge deduplication, Qdrant / Weaviate / LanceDB destinations. Closest in spirit to your ingestion scripts from the homework | It is code, not a UI; vector destinations are less battle-tested than tabular ones |
| **Pathway** — https://github.com/pathwaycom/pathway + templates https://github.com/pathwaycom/llm-app | ~62k + ~59k | A streaming engine with incremental computation: live sync of additions, edits **and deletions** from a folder, Google Drive, SharePoint, S3, Kafka - a file change reaches the index in seconds, without a separate ETL. The recent `serviette` (https://github.com/pathwaycom/serviette) does the same on top of 8 external vector databases, including Qdrant and pgvector: editing and deleting a file become real upsert/delete in your database | The core engine is under BSL 1.1 (free for most uses, but read the license); the default templates keep the index in their own memory, an external database goes through serviette |
| **Onyx** (ex-Danswer) — https://github.com/onyx-dot-app/onyx | ~32k | Ready-made enterprise search: 50+ connectors, continuous background sync of changes, synchronization of access permissions from sources, a hybrid index | It is a product with its own storage and its own search, not a layer over your collection |
| **RAGFlow** — https://github.com/infiniflow/ragflow | ~89k | A full RAG platform with knowledge base management in the UI: upload, parsing, document statuses, reprocessing | The same: its own whole stack, it does not need your Qdrant |
| **Dify** — https://github.com/langgenius/dify | ~153k | An LLM application platform; the knowledge base can sync from external sources (for example, Notion) with reindexing | The same, plus it is already an application builder, not an ingestion layer |
| **airweave** — https://github.com/airweave-ai/airweave | ~7k | An OSS data integration layer for agents (an open alternative to Glean): connectors to SaaS sources, sync into a search layer | Younger than the others in the list, check how battle-tested it is on your own case |

Alongside, but about a different layer: https://github.com/Unstructured-IO/unstructured (~15k) - parsing
formats into clean text before chunking; this is "before" the lifecycle, not the cycle itself.

How to choose: if the task is "my collection in my Qdrant must be kept up to date" - look at
the library layer (LangChain Indexing API, LlamaIndex, dlt, Pathway/serviette) and at your own
record manager from the part above. If the task is "I need ready-made search over corporate sources
with permissions" - Onyx and its class. Platforms like RAGFlow/Dify solve the task as a whole, but together
with it they take your stack too.

Very small 2025-2026 projects (docprep, chunks-sync, steadlith - a few stars each)
are too early to take as dependencies, but the patterns in them are clean: separate content/metadata hashes,
content-defined chunk boundaries, tombstone deletions. And a common limitation of the whole list:
**nobody handles an embedding model change automatically** - it is always a full
reindex; the best technique: a new collection alongside plus an alias switch.

### A checklist for making your own decision

Seven questions for your ingestion layer. "No" is not a verdict, but make it a conscious "no":

1. Does re-loading the same corpus create duplicates? (level 1)
2. A document got shorter / the chunking rule changed - do the old chunks die? (level 2)
3. A document was deleted from the corpus - are its points deleted from the database? (level 4)
4. Is an unchanged document re-embedded for nothing? (level 3)
5. Does editing only metadata trigger re-embedding? (two hashes)
6. Is the embedding model name recorded in the collection and checked before a run? (level 5)
7. Between deleting old chunks and loading new ones, is there a window when search will return a mess?
   (atomicity: a transaction or an alias switch)

---

## Part 2 · Code indexing: why it is a separate discipline

The links to tools promised in the session are here, but with a caveat: the topic turned out to be
deeper than "two tools", so below is the whole map.

Code breaks the habits of document RAG for three reasons: it is full of **exact
identifiers** (a symbol name either matched or it did not - an "approximately similar" result
is harmful), it has a **syntactic structure** (a function is a natural unit of meaning,
cutting it in half is pointless), and it **changes an order of magnitude more often** than documents -
so the tax of keeping the index fresh is highest precisely here.

### Code chunking - by AST, not by lines

The industry standard is to parse code into a syntax tree via
https://tree-sitter.github.io/ and cut along node boundaries: function, class, method; small
neighboring nodes are glued together up to a token limit. Research confirmation is the
cAST method (EMNLP 2025): structural chunking gives +4.3 points of Recall@5 on RepoEval over
line-based chunking: https://aclanthology.org/2025.findings-emnlp.430/

### Three architectures of code search

**1. Embedding index** (Cursor, Windsurf, Copilot codebase index). Chunks → vectors →
semantic search. Strength: questions like "where do we handle authorization",
when the words of the query are not in the code. The price is part 1 of this document, taken
to the extreme: Cursor keeps a **Merkle tree** of hashes of all files, every few minutes
compares the roots of the client and server trees and reindexes only the diverged
branches, and caches embeddings by chunk hash. A breakdown of their engineering:
https://cursor.com/blog/secure-codebase-indexing - this is the best public example of
how much it costs to keep the index of a changing corpus fresh.

**2. Agentic search without an index** (Claude Code, Codex CLI). No index at all: the agent
walks the repository with grep/glob/read, like a human. The Claude Code team started with RAG
and a local vector database and abandoned it: accuracy on identifiers, freshness
(there is no index - nothing to go stale), simplicity and privacy. It is telling that
Sourcegraph also removed embeddings from Cody in favor of its own lexical search. A breakdown of the
debate from both sides:
https://dreaming.press/posts/code-retrieval-for-ai-coding-agents.html

A recent benchmark (May 2026, the paper "Is Grep All You Need? How Agent Harnesses Reshape
Agentic Search" - search for it by title, breakdown:
https://latenteval.ai/research/is-grep-all-you-need) added a nuance: with results delivered
inline, grep beat vector search in all ten configurations, but changing how results
are delivered to the agent changed accuracy more than changing the retriever. The moral for your projects: **you must measure
your whole combination, not "grep versus embeddings" in the abstract**.

**3. Structural and symbol search** - a third path, often skipped:

- https://github.com/ast-grep/ast-grep - grep over syntactic patterns instead of text
  (~15k stars, Rust, tree-sitter). There is an MCP server that exposes the tool to an agent:
  https://github.com/ast-grep/ast-grep-mcp
- A wave of local code indexes for agents (2025-2026): they parse the repository into a graph of
  symbols (SQLite + FTS, sometimes + vectors) and give the agent tools over MCP such as
  `find_symbol` / `get_callers` / `get_callees`. Examples to study - all young,
  choose by your own stack: https://github.com/Regsorm/code-index-mcp (Rust, a static
  binary, federation of several repos), https://github.com/freewind/codeix (the index
  is committed to git together with the code), https://github.com/achreftlili/code-index (hybrid
  vector+FTS with RRF - a scheme familiar to you), https://github.com/philtrem/codeagent-indexing-engine
  (a symbol graph with compiler-based call resolution).
- Aider builds a repo-map - a lightweight structural map of symbols instead of embeddings:
  https://aider.chat/docs/repomap.html

### If you do vectorize code: models for code

General-text embedders are noticeably weaker on code than specialized ones. Reference points:

- **voyage-code-3** and the recent **voyage-code-4** (August 2026, tuned for agentic
  queries like "find where we handle empty arrays incorrectly"):
  https://blog.voyageai.com/2026/08/13/voyage-code-4/
- Open weights: **nomic-embed-code** (7B, Apache-2.0,
  https://huggingface.co/nomic-ai/nomic-embed-code) and the compact **CodeRankEmbed**
  (137M, MIT, https://huggingface.co/nomic-ai/CodeRankEmbed - on CoIR it beats models
  several times larger than itself).
- A benchmark to compare them on: CoIR - https://archersama.github.io/coir/

### A practical takeaway for the course project

For a repository the size of a course project you do not need an index: an agent with grep copes, and this is the
default to start from. Indexing pays off at a different scale - a large
corpus, "cold" questions without knowing the names, many repeated queries to the same
code. And if you are going there, you are back in part 1 of this document: the main cost of an index
is not building it but keeping it fresh.
