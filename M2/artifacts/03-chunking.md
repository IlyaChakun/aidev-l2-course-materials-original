# Layer 3. Chunking: how the unit of retrieval is produced

> Module 2 artifact "Context management: RAG and CAG".
> Library versions and release dates were checked on **10.08.2026**. Figures from studies are given
> together with the conditions of measurement: in this field a number without a denominator means nothing.

A **chunk** is a piece of text that becomes one unit of retrieval: one chunk yields one vector,
and the whole chunk is what lands in the model's context when retrieval finds it. This layer looks
technical ("split the text into pieces"), but in fact it is where the decision that is most
expensive to roll back gets made: **changing the chunk size means reindexing the entire corpus**.
A bad prompt is fixed in seconds; bad chunking costs a recompute of everything.

Terms used below without explanation: **embedder** — a model that turns text into a vector;
**recall** — the share of the needed documents that retrieval found; **retrieval** — the stage
where the system pulls out candidates; **pp** — percentage points; **AST** — the abstract syntax
tree of a program, what a compiler turns source code into before doing anything else with it.

---

## How to use this document

1. Attach the file to your agent (Claude Code, Cursor, Codex — any one that reads files
   from the project): put it next to your course project and say "read `03-chunking.md`
   in full".
2. Give it a frame: *"You are helping me design chunking for my project. Walk me through the
   questions in the section "Questions for brainstorming", one at a time. If I answer in general
   terms, ask for specifics: corpus type, average document length, the window of my embedder.
   After each block, record the decision in one line"*.
3. Go through the questions. The output should be: which corpus types you have, which chunking
   for each, what size and why exactly that one, whether there is overlap, and what you will
   measure it with.
4. Run the result through the checklist at the end.

Separately, ask the agent to calculate one thing: how many vectors your corpus will produce with
the chosen chunking. That number will then determine both the price of the database and the
reindexing time.

---

## An analogy that works: a chunk is a commit

Not "a shelf in a store". Take something you use every day.

**A chunk that is too big is a giant pull request.** Four hundred files, "migrated the project
to the new library version". Formally it contains everything needed. In practice nobody can
say what exactly was done there: the reviewer sees everything at once and sees nothing. A
five-thousand-token chunk behaves the same way: it will be found for almost any query, because it
mentions everything, and it will answer none of them, because the needed fact drowned among nine
unneeded ones.

**A chunk that is too small is a micro-commit with no message.** "Fixed indentation". It is clear what
changed and absolutely unclear why. This is exactly what happens with a 43-token fragment: a table
row without a header, a sentence without a subject, "It is taken off pause manually" with no
indication of who "it" is.

**A good commit is one complete change plus a message that explains the context.** A good
chunk is built the same way: one complete thought plus the path to it glued on — the section
heading, the document title, the date.

And the most useful corollary. To make a reviewer understand a commit, you do not copy a piece of
the previous commit into it — you write a link to the ticket. **Overlap in chunking is precisely
copying a piece of the previous commit**: expensive, noisy, and it treats the wrong disease. The
equivalent of a link to the ticket here is a prefix with the heading path and storing sequence
numbers, so that you can pull in the neighboring chunk when needed.

---

## Map of the set: this file is one of twelve

The module's artifacts walk through the pipeline layer by layer, and the decisions in them are
coupled: the upper bound of a chunk runs into the embedder's window, the metadata schema determines
what you can filter by at search time at all, and cost is made up of the decisions of all layers at
once. That is why the files sit in one folder and are meant to work together: this one is read in
full, the others are opened as needed.

> **Instruction to the agent.** You are reading one file out of twelve; the others are next to it, in the same
> folder. As soon as the conversation goes beyond the boundary of this layer, open the needed file and read
> the relevant section before giving advice. Do not retell a neighboring layer from memory:
> the artifacts contain thresholds, figures with measurement conditions and failure modes that are not in
> common knowledge. Read on demand, not everything at once: first this file, then whatever
> becomes necessary in the course of the conversation. If the needed file is not next to this one, say directly which one
> is needed and ask for it, instead of making things up. When the decision of one layer breaks the decision of a neighboring one, say
> so immediately, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication on intake |
| [`02-metadata.md`](02-metadata.md) | Metadata | deciding which fields go next to a chunk: source, freshness, permissions, version — and what to filter by later |
| [`03-chunking.md`](03-chunking.md) | Chunking | choosing size, boundaries and overlap; questions about tables, code and structural chunking |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | choosing a model for language and domain, dimensionality, local or via API; the price of switching models |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, fusing the branches, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanics, citing the source, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletion, the record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reducing it |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End to end | checking what has been done: errors where the pipeline works and the metrics are green, but the system lies; a checklist of 24 checks |

**The closest links of this layer.** The upper bound of a chunk runs into the embedder's window
([`04-embeddings.md`](04-embeddings.md)), and the quality of the input text runs into the preparation layer
([`01-data-preparation.md`](01-data-preparation.md)). The number of chunks translates directly into the number of
vectors, that is, into memory and money ([`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md),
[`11-economics.md`](11-economics.md)), and the chunk size into how much fits in the context
([`07-reranking-and-context.md`](07-reranking-and-context.md)). The chunk identifier is designed
here, but it is paid for at update time ([`09-corpus-lifecycle.md`](09-corpus-lifecycle.md)).
A mandatory check after chunking is the actual min / avg / max, not the numbers from the config: §2
in [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

---

## The decision map of the layer

Chunking is usually presented as a list of eight strategies. The list is useless: it does not say
what combines with what. There are two axes, and they are independent.

```
AXIS A — WHAT WE CUT WITH (from crude to clever)
characters/tokens → sentences → recursively by separators → by document structure
   → by meaning → by syntax tree (code) → by a model (a trained segmenter or an LLM)

AXIS B — WHEN WE EMBED
├─ after chunking           classic: cut first, then compute a vector for each piece
├─ before chunking          late chunking: run the whole document through the encoder,
│                           then assemble the vectors along the boundaries
└─ change the text before embedding   contextual retrieval, a prefix with the heading path

A FOURTH POSITION, OUTSIDE BOTH AXES
the unit of retrieval is PRODUCED, not cut: an extractor emits atomic
objects right away, one object = one vector. The argument about size and overlap goes away entirely
```

The frame removes a false opposition: late chunking is not a competitor to recursive chunking,
it is simply on a different axis, and they can be combined.

---

## Questions for brainstorming with the agent

**About the corpus**

1. How many different corpus types do I have? Documentation, reports with complex layout, tables,
   contracts, transcripts, correspondence, tickets, code — which of them do I have and in what shares?
2. Do my documents have a reliable heading tree? If so, why am I thinking about
   size at all rather than about structure?
3. What are the average and the maximum document length? How many chunks will the longest
   document produce, and will it take over the results entirely?
4. What questions will be asked of the system: a point fact, a comparison, a section overview, "what did we
   decide on this topic"? Different question types want different chunk sizes — which one
   dominates for me?

**About size and boundaries**

5. What is the context window of the embedder I chose? (This is a hard ceiling on chunk size,
   and for some Russian-language models it is only 512 tokens.)
6. What is my lower size threshold, and what happens to chunks that did not make it past it:
   do I discard them, merge them with a neighbor, keep them?
7. Do I need overlap at all? Can I name the specific failure mode it
   fixes for me — or am I setting 20% "like everyone else"?
8. Does my corpus contain tables, and is the header repeated in every chunk of a table?
9. Do I have documents that must not be cut at all (a ticket, a short policy,
   a one-page instruction)? How will I forbid cutting them technically, rather than by agreement?

**About strategies and code**

10. Which strategy do I take for each corpus type and why exactly that one — because of the corpus type
    or because of the name of the method?
11. If my corpus contains code: do I use an AST, and do I understand that the gain comes from **merging small
    nodes**, not from the tree itself? Have I measured the cross-file context budget, which has
    a stronger effect than chunking?
12. Can I not cut but **produce** retrieval units — that is, ask a model to extract
    ready atomic objects from the raw material? What will then be my stable key?

**About verification**

13. How will I measure that my chunking is good without running the whole pipeline through to an answer?
14. Do I have a golden set: 50 queries with **reference fragments** labeled, not
    reference answers?
15. When comparing strategies, do I equalize the context budget? (Without this, a strategy with large
    chunks wins simply because it received more text.)
16. What will happen to my system when in a month I want to change the chunk size? How much
    does it cost in money and in hours of downtime?

---

## 1. There is no right size, there are three constraints

Published optima for 2024–2026 are scattered **from 100 to 1100 tokens**, and each was obtained
on its own corpus, its own metric and its own retriever. Adding them together is meaningless.

| Recommendation | Measurement conditions |
|---|---|
| 200–400 tokens, no overlap | token-level recall and IoU, 5 corpora, 07.2024 |
| 400–512 with 10–20% overlap | mass practice, the common default |
| 512 recursive | scientific papers, end-to-end answer accuracy, 02.2026 |
| 150–300, sentence chunking | Natural Questions, ECIR 2026 |
| 1024 and above | analytical reports, peak answer groundedness |
| 1100, cut and merge back | highest average score on internal metrics, LREC 2026 |
| **no more than 512** | the hard window of some Russian-language embedders, overrides everything above |

Instead of a number — three constraints:

1. **The context ceiling of your embedder.** It is not your choice, it is in the model card. If it says 512,
   recommendations from English benchmarks for 1024 do not apply to you at all.
2. **Query type.** A factoid question likes small chunks, an analytical one likes large ones.
3. **Your own measurement.** The only thing that survives a change of models.

And one hard norm, the only one in this layer: **a floor of 200–400 tokens**. Never go below it,
however clever the method that suggests it to you.

---

## 2. Overlap: a default that stopped being a default

For many years the answer was "10–20%, don't think about it". Since January 2026 this is a contested position.

- **Against.** An independent academic study (ECIR 2026) systematically tested overlap
  and **found no measurable gain**. The mechanism is named directly: overlapping chunks are
  near-duplicates, and when both land in the results they eat up the context window without adding a single
  new piece of evidence. The authors' recommendation: 0% by default.
- **For.** In another report, on small chunks overlap gave roughly +5 points of recall.
- **Within one and the same report the direction differs:** for recursive chunking at 400 tokens
  the best recall was **without** overlap (89.5 versus 88.1 with an overlap of 200).

The dispute is not settled, and it is honest not to settle it. But the price can be named: **a 20% overlap
means 1.25 times more vectors in the index** (the arithmetic: 1 / (1 − share)). You pay a quarter
of the storage and search cost for a parameter whose benefit is not proven.

**The practical compromise of 2026:** zero by default; 10–15% on dirty sources (OCR,
scraping, contracts), where the boundaries are objectively unreliable; on clean structured documents
overlap only adds noise. And an alternative that is almost always better: **neighbors instead of
overlap** — store the chunk's sequence number and, when chunk N is hit, pull in N−1 and N+1
at the context assembly stage. You get the context, and there is no duplication in the index.

---

## 3. Chunking strategies: each in detail

**Fixed by tokens or characters.** We cut every N units without looking at the text.
When to use: homogeneous logs, streams without structure, ingestion speed as the priority. What breaks it:
it cuts mid-sentence, separates a pronoun from what it refers to, tears tables
and code apart.

**Recursive by separators.** We try to split on a double newline; if a piece
is still large — on a single newline; then on a period; at the very end by characters. This is the de facto
industry default, and it honestly remains one: it degrades gently. When to use: mixed
prose, no structure or structure that cannot be trusted. What breaks it: the separator hierarchy is designed
for the Latin alphabet and paragraphs; on poorly marked-up text it degenerates into fixed chunking.

**By sentences.** Cheap and predictable. In the ECIR 2026 study, sentence chunking
**statistically matched semantic chunking** on context up to roughly 5 thousand tokens, which is
quite sobering. What breaks it: on dirty punctuation (speech transcripts, OCR output)
it falls apart.

**By document structure.** A chunk is a section, a clause, a table row; the prefix holds the path of
headings like `Payments v3 Webhooks > Redeliveries`. It usually gives more than
semantic chunking, and it is the most underrated answer to the question "what size to take": the right
answer is often "do not think about size, cut by structure". What breaks it: the size of a node
is non-deterministic, a section may not fit in the embedder's window — you need a fallback path.

**Semantic.** We walk through the sentences, compute the similarity of neighbors, and put a boundary where
the similarity drops. It sounds smarter than recursive, and that is the trap. **It is not an upgrade of
recursive but a different tool with a narrow area of applicability:** transcripts, long prose without
markup, topics drifting unpredictably. A size floor is mandatory. Two real numbers
you will come across: in one measurement semantic chunking gives the best recall of 91.9%, in another end-to-end
answer accuracy of 54% versus 69% for recursive 512 — it loses outright. Both figures are honest,
the metrics differ. A plausible explanation of the second failure: the average fragment there came out at
**43 tokens**, and the similarity threshold was not tuned. This explains one failure and does not explain why
in the first measurement an LLM-based chunker led. And a separate uncomfortable position from practitioners:
on real corpora, splitting on line breaks often gives a better result —
**document topology matters more than the semantic proximity of paragraphs**. The price: semantic chunking
is roughly 14 times slower than recursive (4.82 versus 0.33 MB/s in a vendor speed measurement).

**Hierarchical (parent-child, small-to-big).** We build two levels: small chunks for retrieval,
large parent ones for the answer. We search over the small ones, and give the model the whole parent in the context
or several merged neighbors. The point: retrieval likes short and specific, while generation likes
complete. A measurement on a real corpus: accuracy rose from 60% to 70–75%. When to use: when you get
both point questions and "tell me about the section". What breaks it: on a document update a
cascade is invalidated (a child changed — the parent went stale), and without parent deduplication
the same text arrives in the context three times.

A separate line here is **HiChunk** (ACL 2026): a fine-tuned model marks up the document hierarchy,
and at retrieval time an algorithm for automatically merging neighboring fragments kicks in. Along the way the authors
explained **why benchmarks do not distinguish chunking methods at all**: it comes down to the sparsity of
evidence. If the answer lies in one or two sentences, any chunking will catch it, and the difference
between methods drowns. On datasets with dense evidence the gap appears immediately: evidence
recall is 74.06 for fixed chunking versus 81.03 for hierarchical.

**LLM-driven.** The language model itself places the boundaries: it is fed consecutive pieces
and asked where the topic changes. A published method of this class is **LumberChunker**;
in the Chonkie library it is implemented under the name `SlumberChunker`. When to use: an expensive
irregular corpus where chunk quality defines the product. What breaks it: it is non-deterministic,
hallucinates boundaries, drops pieces of text, breaks the response format. Run it only as an asynchronous
queue with validation of the result, never in synchronous ingestion.

**Neural.** A separate trained segmenter model (in Chonkie this is `NeuralChunker`). A middle ground
between semantic and LLM-driven: it looks at the text more meaningfully than a similarity threshold, but costs
less than a call to a large model and behaves more predictably. A reasonable candidate if semantic
chunking did not take off for you and LLM chunking is too expensive.

**Late chunking.** The order of operations is flipped: first the whole document
is run through the encoder, and only then are the token vectors assembled along the chunk boundaries.
The point: the vector of the last paragraph has already "seen" the heading at the start of the document, so a chunk
with the word "it" is found by a word that is physically absent from it. It works at no extra
compute compared to contextual retrieval and requires no fine-tuning. **But:** the method
requires a model with mean pooling and access to per-token vectors, while newer embedder lines
are moving to last-token pooling and losing support — in one SDK the late chunking parameter
for new models is **silently ignored**. The conclusion for design: do not build late
chunking in as an architecture layer that will survive a change of embedder. Contextual retrieval has no such
dependency, because it edits the **text**, and the gain carries over to lexical
search and to the reranker as well.

**Adaptive.** Not one strategy per corpus but a choice of strategy **per document** based on its
properties. The Adaptive Chunking study (LREC 2026) showed an average score of 91.07 versus 88.62
for standard recursive chunking on 33 documents from three domains. The five internal
metrics discussed below come from the same study.

**Tabular.** A table is cut by rows, the header is **forcibly repeated** at the start of every
chunk, and a row is serialized into a self-contained sentence. In some libraries this behavior
is the default. And a rule that goes along with it: send computation and aggregation questions to SQL,
not to vector search. A chunker that cut a table badly gives a plausible and wrong
answer, and this is one of the most frequent production failures.

---

## 4. Code: AST, and why the gain is not in the tree

Intuition says to cut code by functions. **Intuition is wrong.**

A controlled 2026 experiment on 864 configurations (4 strategies × 4 retrievers ×
5 generators × 9 parameters): chunking by functions is **the worst of all**, minus 3.57–5.64 points
with the maximum effect size. The reason is clear: a function is usually shorter than the chunk budget,
and modular code outside function bodies (imports, constants, configuration) is lost entirely.

The cAST method (EMNLP 2025) gives +4.3 points of Recall@5 and +2.67 points of Pass@1 on code: it walks the
syntax tree top-down, puts a large node in whole if it fits the budget,
and **greedily merges** small neighboring nodes. The key detail: without the merge step nDCG drops
from 71.1 to 53.5. **The gain comes from merging small nodes, not from the AST itself** — which is exactly why in another
experiment a simple sliding window turned out to be no worse than structural chunking.

Both sides of the dispute agree on one thing: **the main lever on code is not the chunking strategy but the budget
of cross-file context.** Expanding from 2048 to 8192 gives up to +4.2 points, whereas the choice of
retriever gives no more than 1.11.

Practical rules: do not cut by functions; measure size in **non-whitespace characters**,
not in lines; aim for 2000–2500 non-whitespace characters.

**Two tools worth looking at before writing your own tree walker.**

- **ast-grep** (`https://github.com/ast-grep/ast-grep`) — search, lint and rewrite of code
  by **structure**, not by text. The pattern is written in the language of the code itself: `console.log($ARG)`
  will find all such calls regardless of formatting and line breaks. Under the hood it is tree-sitter,
  and it works on many languages. For chunking it is useful as a deterministic way to cut out the needed
  nodes and find boundaries without involving a model.
- **Claude-ast-index-search** (`https://github.com/defendend/Claude-ast-index-search`) — a CLI
  that builds a local index in SQLite: symbols, references, imports, modules, dependencies,
  inheritance. After that the agent navigates the code with structural queries (`ast-index refs`,
  `usages`, `callers`, `hierarchy`) instead of reading whole files. The author claims savings
  of about 40–50% of agent tokens on large repositories. Here it is interesting as a working
  alternative to code chunking itself: if the agent can ask "who calls this function",
  it does not need someone to cut the repository into vectors in advance.

---

## 5. The fourth position: the unit of retrieval can be produced, not cut

The strongest point of this layer, and it is almost never spelled out.

The usual frame: there is a document, it has to be cut. The alternative: **let an extractor emit
atomic units right away**. A model reads the raw material (a transcript, correspondence, a ticket, a log) and returns
an array of typed objects: the unit type, a short summary, details, a verbatim quote,
a link, a date, tags. One object — one vector. In such a system there is **no chunking for retrieval at all**.

*Example: a pipeline with LLM preparation over transcripts and correspondence exports.* There chunking
does exist, but it solves a different task — it cuts the input stream to fit the extractor's window and the limit on
output tokens. Its objective function is the opposite: **never cut a unit of meaning**. The unit of chunking is not "1000 characters
with an overlap of 200" but a post together with its album, comments and photos; an oversized such set
gets a personal chunk and is never split. There is no overlap at all, and it is not needed: the boundaries run where the meaning
ends anyway.

**Hence an important distinction: in a working pipeline there can be two chunkings, and they solve
different tasks.** The first is for the extractor model's window. The second is for retrieval. Their parameters have no
relation to each other, and mixing them up costs you whatever the parameters of one drag along from
the parameters of the other.

**What you gain:** the argument about size and overlap goes away entirely; there is by construction
no reindexing, because there is nothing to recut; every unit is verifiable if it holds
a verbatim quote.

**What you pay:** you need a **stable meaningful key** for each produced unit.
If the key drifts, you get duplicates and orphans, and you will have to clean them up by hand. Plus everything
that comes with LLM preparation: non-determinism, the model and prompt version in the metadata,
idempotency by input hash.

**A ticket corpus gives you the same logic for free.** A ticket is not cut: median 184 tokens, 95th
percentile 612, it is already semantically whole. If your corpus consists of such objects,
half of this document you simply do not need.

---

## 6. How to measure chunks without running the whole pipeline

By habit the industry measures chunking through recall@k, that is, it mixes it with the retriever
and the embedder and moves very slowly. There is a cheaper way.

**Five internal metrics** (Adaptive Chunking, LREC 2026) are computed right on the document, without
reference answers and without running generation:

- **References Completeness** — the share of "entity and its pronoun" chains not torn apart
  by a chunk boundary. It catches exactly the case when "it" ended up in another chunk.
- **Intrachunk Cohesion** — how close the sentences inside a chunk are to each other.
- **Document Contextual Coherence** — how close a chunk is to the context surrounding it.
- **Block Integrity** — the share of structural blocks (paragraphs, tables, lists) that stayed whole.
- **Size Compliance** — the share of chunks within the target size range.

The value is in two things. First: they are cheap enough to run **inside the indexing
pipeline**, not in a lab. Second, and not obvious — the **amplification effect**: the difference between
methods on these metrics is only 0.4–2.4 points, but on retrieval recall it unfolds
into 8–10 points, and on answer correctness into 5–8 (33 documents, three domains, statistically
significant). That is, a small difference on a cheap metric predicts a large difference
on an expensive one.

**A procedure for your own measurement that you can take away and apply.**

1. Build a golden set: at least 50 queries with **reference fragments** labeled,
   not reference answers. Measure retrieval directly: an end-to-end metric mixes three layers
   and moves noticeably later.
2. Run 3–4 strategies with an **identical context budget**. The number of chunks is chosen
   adaptively: `k = target_tokens / average_chunk_size`. Without this the comparison is unfair.
3. Compute recall@k, the coverage of the reference fragment and, if possible, the internal
   metrics.
4. **Read 20 diffs and 50 random chunks with your own eyes.** Cheaper than any metric, and it catches
   what the metrics do not see.
5. Break the result down **by document types and by query types separately.** An aggregate hides
   a catastrophe in a single category.

Warning: vendor chunker benchmarks are no good as an argument for choosing: different vendors publish
mutually contradictory results, each under its own conditions, and in one of them the "smart" mode
runs on the same vendor's paid model. You have to measure on your own corpus.

---

## 7. Corpus type → chunking → tool

| Corpus type | Chunking | Tool | Key parameter |
|---|---|---|---|
| Technical documentation, Markdown | Structural by headings, section path in the prefix | `MarkdownHeaderTextSplitter`, `HybridChunker` (Docling) | The tokenizer must match the embedder's tokenizer |
| PDF reports with complex layout | Element-based, on top of the parser output | `HierarchicalChunker` (Docling), `chunk_by_title` (Unstructured) | `combine_text_under_n_chars` against false headings |
| Tables | Row by row with forced header repetition | `repeat_table_header`, `TableChunker` | Send computation questions to SQL |
| Contracts and regulation | By clauses plus context enrichment | Structural splitter plus contextual retrieval | Overlap is justified here: boundaries are sensitive |
| Mixed prose without markup | Recursive 400–512 | `RecursiveCharacterTextSplitter`, `RecursiveChunker` | A safe default, degrades gently |
| Transcripts and correspondence | By sentences or semantic | `SemanticChunker`, `semchunk`, `NeuralChunker` | **A floor of 200–400 tokens is mandatory** |
| Short chat messages | Late chunking with neighbors merged into the prefix | `LateChunker` | Only on a model with mean pooling |
| Code | Sliding window or AST with merging | `CodeChunker`, `astchunk`, ast-grep for boundaries | 2000–2500 non-whitespace characters; the cross-file context budget matters more |
| Tickets | Do not cut at all | — | Whole, if the system answers; typed, if it generates artifacts |
| Russian-language corpus | Any of the above | The same | The 512-token ceiling of some models overrides all recommendations |

---

## 8. Libraries: what is alive as of 10.08.2026

| Tool | Version and date | What it provides | Status |
|---|---|---|---|
| **Chonkie** | 1.7.0 · 07.07.2026 | 12 chunkers in one library: token, fast, sentence, recursive, semantic, late, code, neural, slumber (LLM), table and others. Plus refineries (overlap, embeddings) and ports to popular vector databases | The only complete set |
| **semchunk** | 4.1.1 · 13.06.2026 | A hierarchical recursive algorithm; since March 2026 a mode based on a segmentation model. Used inside Docling | Active |
| **Docling** | 2.118.1 · 07.08.2026 | `HierarchicalChunker` and `HybridChunker` (fitting to the embedder's tokenizer: splits ones that are too large, merges neighbors with the same header). Table header repetition is on by default | Very active |
| **Unstructured** | 0.25.2 · 03.08.2026 | `chunk_by_title`, `combine_text_under_n_chars`, `isolate_table` | Active |
| **langchain-text-splitters** | 1.1.2 · 16.04.2026 | The industry baseline `RecursiveCharacterTextSplitter`, splitters by Markdown and HTML headings | Alive, but no releases for a long time. Warning: **CVE-2026-41481**: `HTMLHeaderTextSplitter.split_text_from_url()` did not validate redirects (SSRF); the method is deprecated, fixed in 1.1.2 |
| **semantic-text-splitter** | 0.32.0 · 16.06.2026 | Rust, called from Python, faster than the alternatives | Active |
| **astchunk** | 0.1.0 · 19.06.2025 | A reference implementation of cAST on tree-sitter | Research code, not a product |
| **semantic-chunkers** | 0.1.1 · 10.06.2025 | Statistical / Consecutive / Cumulative chunkers | **14 months without a release, consider it frozen** |

Checking the date of the last release before choosing a library takes thirty seconds, and it is the
only cheap way not to land on an abandoned project.

---

## Common mistakes

| What not to do | What it leads to | What to do |
|---|---|---|
| Take a semantic chunker because it sounds smarter than recursive | 43-token scraps on transcripts, torn tables in reports | Choose by corpus type, not by the name of the method; always with a floor of 200–400 tokens |
| Set a 20% overlap "like everyone else" and not measure | An index 1.25 times larger, near-duplicates compete in the results and eat the window | Zero by default; enable it for proven sensitivity to boundaries; or neighbors instead of overlap |
| Split more aggressively "just in case" | The number of vectors grows 3–5 times, and the cost of storage and search follows | Count the number of vectors before loading; aim for 4–6 chunks in the context, at 10+ hallucinations grow |
| Cut code by functions | The worst result of all those tested: minus 3.57–5.64 points | A sliding window or an AST **with merging of small nodes**; first expand the cross-file context budget |
| Cut a ticket into chunks | You break an object that is already semantically whole | The ticket whole; typed — only if the system generates artifacts from it |
| Build late chunking into the architecture | A change of embedder breaks the layer: new models lose support, the parameter is silently ignored | Use it as a local optimization; for a stable gain — contextual retrieval, it edits the text |
| Ignore the embedder's window when choosing a size | The tail of a chunk is silently truncated on ingestion, and half of the document ends up in the index | Look at the model card **before** choosing a size; at 512 tokens the English recommendations do not apply |
| Cut a table without repeating the header | The chunk is left with numbers without units of measurement and without column names | Repeat the header in every chunk of the table; send computation to SQL |
| Compare strategies without equalizing the context budget | The one that simply received more text wins | Adaptive k: divide the target tokens by the average chunk size |
| Measure chunking only by end-to-end answer quality | The metric mixes three layers and moves latest of all; you do not understand what you are fixing | Internal chunk metrics plus recall on reference fragments |
| Trust a vendor chunker benchmark | Vendors publish mutually contradictory results under their own conditions | Your own corpus, 50 labeled queries, a breakdown by document types |
| Install a library without looking at the release date | You land on a frozen project or on a version with a known vulnerability | Check the date of the last release and open CVEs, thirty seconds |
| Assume there is one chunking in the system | The chunking parameters for the model window drag along the parameters of the retrieval unit, although the goals differ | Separate them explicitly: one cuts to the extractor's window, the other defines the retrieval unit |
| Change the chunk size "to try it" on a live system | A full reindexing of the corpus, and going back is just as expensive | Decide the size on a pilot; write the chunking parameters into the collection metadata |

---

## Layer readiness checklist

**Frame**
- [ ] It is determined whether I cut or produce retrieval units. If I produce — a stable key is named.
- [ ] The two chunkings are separated, if there are two: for the model window and for retrieval.
- [ ] Each corpus type has its own strategy chosen, not one for everything.

**Size and boundaries**
- [ ] The embedder's context window is known, and the chunk size fits under it with a margin.
- [ ] The floor of 200–400 tokens is in place; fragments below the floor are merged or discarded deliberately.
- [ ] The decision on overlap is made and justified (including the decision "zero is enough").
- [ ] Objects that must not be cut are protected technically, not by agreement.
- [ ] Tables have the header repeated in every chunk.
- [ ] There is a fallback path for a structural node that did not fit in the window.

**Verification**
- [ ] There is a golden set of 50+ queries with reference fragments labeled.
- [ ] Strategies were compared with an equalized context budget.
- [ ] 50 random chunks from the real corpus have been read with my own eyes.
- [ ] The result is broken down by document types and by query types separately.
- [ ] The number of vectors is counted and the storage cost estimated for the chosen chunking.

**Durability**
- [ ] The chunking parameters are written into the collection metadata, not in the head of whoever created it.
- [ ] It is understood and written down how much changing the chunk size costs (a full reindexing).
- [ ] For the chosen libraries, the date of the last release and open vulnerabilities have been checked.

---

## Links

**Studies** (read together with the measurement conditions, not from the abstract)
- Systematic check of overlap, ECIR 2026: arXiv **2601.14123**
- Adaptive Chunking, LREC 2026 — five internal metrics and the amplification effect, code is open
- HiChunk / HiCBench, ACL 2026 (`2026.acl-long.1372`) — why benchmarks do not distinguish chunking methods
- cAST, EMNLP 2025 Findings, and the controlled experiment arXiv **2605.04763** — read as a pair,
  the conclusions are opposite
- LumberChunker (segmentation of long documents by a language model): arXiv **2406.17526**

**Libraries**
- Chonkie: https://github.com/chonkie-inc/chonkie
- Docling: https://github.com/docling-project/docling
- semchunk: https://github.com/isaacus-dev/semchunk
- langchain-text-splitters: https://github.com/langchain-ai/langchain
- semantic-text-splitter (Rust): https://github.com/benbrandt/text-splitter

**Working with code**
- ast-grep — structural search and rewriting of code: https://github.com/ast-grep/ast-grep
- Claude-ast-index-search — a local AST index for agents: https://github.com/defendend/Claude-ast-index-search
- tree-sitter (what both are built on): https://tree-sitter.github.io/tree-sitter/

**Evaluation**
- `chunking_evaluation` — generating a dataset for evaluating chunking from your own corpus:
  https://github.com/brandonstarxel/chunking_evaluation
