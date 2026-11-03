# Module 2 artifacts: the RAG pipeline by layer

Twelve helper documents. The first eleven cover one pipeline layer each: what is decided at it,
what the options are, what signs to choose by, what breaks and how to see it. The twelfth runs
across the layers — field lessons and checks along the whole path at once.

The files are written not to be read straight through but to be handed to a coding agent as
context and used to work through your own project. They are designed for joint work: inside each
there is a map of the set and cross-references, so an agent that has received one file knows about
the other eleven and opens them itself when the conversation moves to a neighboring layer.

## Twelve files

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at intake |
| [`02-metadata.md`](02-metadata.md) | Metadata | you are deciding which fields go next to the chunk: source, freshness, permissions, version — and what to filter by later |
| [`03-chunking.md`](03-chunking.md) | Chunking | you are choosing size, boundaries and overlap; questions about tables, code and structural chunking |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | you are choosing a model for the language and domain, the dimension, local or via API; the price of switching models |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, fusing branches, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | the candidates are found but the order is bad; assembling what will actually go to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanics, citing the source, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updating and deletion, the record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, the "before X this way, after X that way" thresholds, the levers for reducing it |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | Cross-cutting | checking what has been done: mistakes where the pipeline works and the metrics are green but the system lies; a checklist of 24 checks |

## How to connect them to the agent

Download the whole folder and put it next to your project (or specify the path to it in the
agent's rules file). Then copy the prompt below — it explains to the agent that in front of it is a
set, not a single file, and how to handle it.

```text
Next to the project there is an artifacts/ folder — twelve documents by RAG pipeline layer:
01 data, 02 metadata, 03 chunking, 04 embeddings, 05 database and indexes, 06 search and fusion,
07 reranking and context, 08 generation, 09 corpus lifecycle, 10 security, 11 economics,
12 cross-cutting field lessons and a checklist of checks.

Rules for working with this set:

1. Read artifacts/README.md and the file of the layer we are starting with. Read the others
   on demand — when the conversation has reached their topic, not in advance.
2. Do not retell a neighboring layer from memory. The artifacts contain thresholds, numbers with
   measurement conditions and failure modes that are not in general knowledge: open the file
   first, advise afterwards.
3. The layers' decisions are coupled. If my decision at one layer breaks a decision at another —
   the chunk size does not fit into the embedder's window, a filter relies on a field that is not
   in the schema, the chosen dimension does not fit into memory — say so right away, without
   waiting to be asked.
4. Lead me through the "Questions for brainstorming with the agent" section of the open file: one
   question at a time, pressing if I answer in generalities. Ask for specifics — the corpus type,
   the volume, the language, the average document length, the update frequency, the model's window.
5. After each block record the decision made in one line and keep a common list of decisions by
   layer. At the end assemble a short decisions document from it.
6. Before I believe the first metrics, take me through the checklist from
   12-pipeline-field-lessons.md and tell me which items we are not checking.
7. If the file you need is not nearby — say exactly which one is needed and ask for it. Do not
   make things up.

We start with: <layer name or a question about the project>.
```

## Where to start in three typical situations

**Designing from scratch.** The order along the pipeline: `01` → `02` → `03` → `04` → `05` → `06`.
Layers `07`–`08` come in when search already returns something. `09` is worth reading in advance,
before the first load: the chunk identifier and the update mechanics are designed together with
chunking, not afterwards. `11` — before choosing the model and the dimension, because it has the
"before X this way, after X that way" thresholds. `12` — before the first measurement.

**Search returns garbage.** Start with `12` §5–6: it analyzes which path your metric belongs to,
who in your pipeline is responsible for the sparse branch and why a score cannot be loaded with
the meaning "there is no answer". Then by suspects: `06` (fusion and filters), `03` (chunking),
`04` (a model for the corpus language), `07` (candidate order).

**Reviewing a finished pipeline.** `12` in full, then the summary checklist of 24 checks at the end
of the file: for each item the agent answers "confirmed by code / confirmed by a run / not checked"
and adds the missing checks.

## What is nearby

On top of the layers there are six reference documents in [`../reference/`](../reference/): the
design checklist, the catalog of failure modes, twelve principles, the tool landscape, adjustments
for the Russian language and the vector database lifecycle with code indexing.

Closest to the artifacts stands the last one —
["Vector database lifecycle and code indexing"](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M2/reference/vector-db-lifecycle-and-code-indexing.md):
a six-level update maturity ladder, ready-made record managers with their limits, a checklist of
seven questions and a separate part on code indexing. It is read as a pair with
[`09-corpus-lifecycle.md`](09-corpus-lifecycle.md).
The worked-out n8n builds are in [`../examples/`](../examples/), primary sources with links are in
[`../reading-list.md`](../reading-list.md).
