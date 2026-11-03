# Module 2. Context management: RAG and CAG

## About the module

The second module closes the knowledge layer of the course project: the agent gets search over
your document base, and you show with numbers that this search works.

The module's main question is not "how to connect a vector database" but **where quality is lost
in the pipeline**. The answer is almost never in the database: it is in how a document turned into
text, where the chunk boundary fell, what ended up in the metadata, what the embedding was computed
with and how the results of two different searches were fused. That is why the materials are laid
out by pipeline layer, not by tool.

The practical output of the module is working search in your project, a set of reference questions
for it and a computed metric. In the third module this search moves from a low-code node into code,
**and the collection and the loading script are reused unchanged**: what you decide here about the
data schema will be expensive to change.

## What is in this folder

| File or folder | Why |
|---|---|
| [`homework.md`](homework.md) | **The full text of the homework**: what to submit, the order of work, the levels with the advanced blocks, the parts of the assignment, the metrics with worked examples, the acceptance criteria |
| [`artifacts/`](artifacts/) | Twelve helper documents: eleven by pipeline layer plus a cross-cutting analysis of typical mistakes. The main content of the folder, details below |
| [`reference/`](reference/) | Six reference documents on top of the layers: a design checklist, a catalog of failure modes, twelve principles, the tool landscape, adjustments for the Russian language, the vector database lifecycle and code indexing |
| [`examples/`](examples/) | Five worked-out n8n builds: document loading, incremental update, an agent with four tools, a full cycle with deletion handling |
| [`reading-list.md`](reading-list.md) | Primary sources with links and a "why read it" line. The first two sections are needed directly for the homework |
| [`slides/`](slides/) | The module's slides as one self-contained HTML: download and open with a double click, no internet needed. A click on a list item expands the breakdown, a click on a picture expands it to full screen |

## Artifacts: eleven pipeline layers and a cross-cutting analysis

The first eleven files cover one layer each: what is decided at it, what the options are, what
signs to choose by, what breaks and how to see it. The twelfth runs across the layers: these are
field lessons: typical mistakes where the pipeline works and the metrics are green, but the system
quietly lies, and the checks that catch them.

| Artifact | What it is about |
|---|---|
| [`01-data-preparation.md`](artifacts/01-data-preparation.md) | How to turn what actually lies around in a company into text: formats, parsers, OCR, normalization, deduplication, intake from a wiki and a tracker. The layer that eats from a third to a half of the project |
| [`02-metadata.md`](artifacts/02-metadata.md) | What to write next to a chunk at intake so that there is something to filter by later: the field schema, freshness, access rights, provenance |
| [`03-chunking.md`](artifacts/03-chunking.md) | How the unit of search comes about: size, boundaries, overlap, structural chunking, what to do with tables and code |
| [`04-embeddings.md`](artifacts/04-embeddings.md) | Choosing a model: for your language and domain, dimension, price, local launch, what to do when changing the model |
| [`05-vector-db-and-indexes.md`](artifacts/05-vector-db-and-indexes.md) | Choosing a database and index settings: which knobs really matter, what costs memory, where the differences between databases begin |
| [`06-search-and-fusion.md`](artifacts/06-search-and-fusion.md) | Why the database **always** returns something: dense and keyword search, fusing results, filters, query processing |
| [`07-reranking-and-context.md`](artifacts/07-reranking-and-context.md) | The last mile: reranking the candidates and assembling what goes to the model |
| [`08-generation.md`](artifacts/08-generation.md) | The answer and its citation: how to make the system refuse when there is no answer and give the source |
| [`09-corpus-lifecycle.md`](artifacts/09-corpus-lifecycle.md) | The index as a living system: updating, deletion, versions, embedder migration, cross-checking against the source |
| [`10-security.md`](artifacts/10-security.md) | Search as an authorization decision: data isolation, corpus poisoning, leaks through embeddings and the cache |
| [`11-economics.md`](artifacts/11-economics.md) | What the cost is made of: indexing versus traffic, where the money actually is, how to compute it before launch |
| [`12-pipeline-field-lessons.md`](artifacts/12-pipeline-field-lessons.md) | **Cross-cutting.** Field lessons from the whole pipeline: config versus fact, orphans on reloading, two search paths, why a refusal cannot be hung on a score threshold, measurement noise versus the effect of a fix. Plus a checklist of 24 checks for reviewing your own pipeline |

## How to use this

**Step 1. Read the framing.** Start with `reference/principles.md`: five minutes, and then the rest
reads faster. If you are deciding whether you need RAG at all and in what order to work —
`reference/checklist-design-and-launch.md`.

**Step 2. Connect the artifacts to your agent.** The artifacts are written so that they can be
handed to an agent as context and used to discuss your project with it, not to be read straight
through cover to cover. A practical way: put the files you need next to the project (or specify the
path to this folder in the agent's rules with the condition "read when the topic is search over the
knowledge base") and work through your case with it layer by layer.

Questions worth starting a conversation with the agent from:

- "Here is my corpus: these formats, this volume, updated like so. Go through the layers and tell
  me where my weakest spot is".
- "Propose a metadata schema for my documents and explain which filters it will give me".
- "My search returns garbage on questions of this type. Go through the layers to find where it
  could have broken and suggest what to check first".
- "Assemble ten questions for me on this corpus so that among them there are multi-step ones and
  ones whose answer is not in the corpus".

The point is not for the agent to write the code for you but for the decisions by layer to be made
consciously and written down. Almost all expensive rework in RAG happens not because of bad code
but because of a decision made without looking at the second layer and discovered at the ninth.

**Step 3. Go through the examples.** In `examples/` there are n8n builds that show how this is
arranged in practice: how a collection appears, what an incremental update looks like instead of a
full rebuild, how an agent chooses a tool for the type of question. They import into your n8n, but
will not run right away: the credentials and addresses have been scrubbed from them, and
placeholders stand in their place.

**Step 4. Do the homework.** The full text, the order of work and the criteria: in
[`homework.md`](homework.md). Before starting, read the section "Where it usually breaks": it holds
exactly what eats the first evening for most people.

## How to read the numbers in the artifacts

The numbers are given with the measurement method: on what corpus, in what way, for what date. This
is not pedantry. In this field three loud numbers "about the same thing" usually measure three
different quantities, and without the method they contradict one another.

Separately about freshness: everything that costs money or lives in someone else's release cycle —
prices, versions, tool statuses — was checked on 10.08.2026 and goes stale within weeks. Before a
decision, cross-check with the primary source; the links are in `reading-list.md`.

Where there is no footing, it is said directly. The estimate "data preparation eats from a third to
a half of the project" is practitioners' experience, not a measurement, and it is marked that way in
the text.

---

*The second module of the course. The previous one: the first, your own MCP server. The next one:
the third — the agent moves from a low-code prototype into code, and the search from this module
becomes its tool.*
