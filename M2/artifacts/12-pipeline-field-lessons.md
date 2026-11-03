# Layer 12 (end to end). Field lessons: typical RAG pipeline errors and checks before trusting the metrics

> Module 2 artifact "Context management: RAG and CAG". Unlike layers 1–11, this
> document is end to end: it is assembled from reviews of real pipelines and covers the whole path
> from corpus to metrics. All cases are anonymized; the figures are from real runs.

Every error here has one property in common: **the pipeline works with it, throws no
errors, the metrics may be green** — and the system quietly lies. That is why the
document is built not around "how to do it" but around "how to check that what was done is true".

---

## How to use this document

1. Attach the file to your coding agent (Claude Code, Cursor, Codex — any one that
   reads files from the project): put it next to your project.
2. When **designing** a pipeline, give it a frame: *"Read `12-pipeline-field-lessons.md`
   in full. We are designing ingestion and search for a vector database. For every design decision
   check against this document: which pitfalls from it apply to our variant, which
   checks need to be built in from the start"*.
3. When **reviewing** a finished pipeline, give it a frame: *"Read `12-pipeline-field-lessons.md`.
   Go through the summary checklist at the end and check every item against our code and data.
   For every item answer: confirmed by code / confirmed by a run / not checked —
   and what to add so that it gets checked"*.
4. Answers like "that is how it is in our config" are not accepted — almost all the lessons below are precisely about the difference
   between the config and the fact.

---

## Map of the set: twelve artifacts of the module

This file is the twelfth, the end-to-end one: it says what to check in an already assembled pipeline.
How to make the decisions themselves is written in the eleven layer artifacts — they lie in the same
folder and are meant to work together with this file.

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

**Where to go for details on each section.** This file says *what to check*; how to make
the decision itself is written in the layer artifacts. §1 (data, corpus language, embedder choice) →
[`01-data-preparation.md`](01-data-preparation.md) and [`04-embeddings.md`](04-embeddings.md);
§2 (chunking) → [`03-chunking.md`](03-chunking.md); §3 (identifiers and ingestion) →
[`02-metadata.md`](02-metadata.md) and [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md);
§4 (updates and deletion) → [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md);
§5 (hybrid search) → [`06-search-and-fusion.md`](06-search-and-fusion.md),
[`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) and
[`07-reranking-and-context.md`](07-reranking-and-context.md); §6 (metrics, refusal, traps) →
[`08-generation.md`](08-generation.md). Two layers touch all sections at once and are read
separately: [`10-security.md`](10-security.md) and [`11-economics.md`](11-economics.md).

---

## 1. Data and corpus preparation

### 1.1. The origin of the corpus is a decision with a price, and it is written into the report first

There are four ways to get a corpus, and each has its own price. The answer to "where does the data come from and what are we
allowed to do with it" must appear in the project before the answer to "how did we chunk".

**Real own data** is the most honest for measurement: search is checked on what it
will work on. The price is two questions at once:

- **Selection.** A field case: the source data pool is 1,528 documents at 1.75M tokens, ~197K
  were selected into the corpus. The right practice from this case: the reason for selecting each document
  is written into a manifest — a month later it is clear why the corpus is what it is.
- **Privacy.** A question that needs a written answer: *who is allowed to see your
  corpus? Can it even lie in git?* In one of the cases the data is private — the corpus did not get into the
  repository at all, instead of files there is a description of the source. This is a legitimate decision
  if it was made deliberately.

**Real third-party (public) data** — for example, vendor documentation. Two questions:

- **Conversion.** HTML → Markdown by a script — and what did the conversion lose? Tables? Anchors?
  Check with your eyes on a sample before loading.
- **Licenses.** A working pattern from practice: sources are split by license — permissive ones
  lie in git, closed ones do not get into git and are regenerated by a script; in each point's payload
  a status `current` / `quarantined`; attribution is collected in a separate file. The outcome: the corpus can be
  handed out without handing out someone else's.

**Data written for the project.** The most valuable type of corpus — knowledge that did not
exist in written form before you — and the most expensive in time. A field case: the methodology
of domain assessment used to live partly in the prompt, and partly the agent made it up on the fly
and gave different answers on the same input. The corpus was born as a crystallization of errors:
the agent made a mistake on a specific example (took "teammates across 20+ countries" for a sign of
remote work) → a section "the company's geography is not the position format" appeared in the methodology.
Every disputed section of the corpus grew out of a real error — that is why the corpus hits exactly
the weak spots of the system.

**LLM synthetic data** is the fastest way and the most dangerous for measurement: **if the corpus
is generated by a model and the golden set is generated the same way, the green metric confirms the
generator, not the search.** Minimal hygiene: a "generated" mark in the report and looking at the
texts with your eyes before the first measurement — not after.

Separately about format: markdown and plain text are greenhouse mode. PDF, OCR, tables,
screenshots on a working corpus will start from day one — build this into the plan, even if the
prototype lives on markdown.

### 1.2. Looking at chunks with your own eyes on a sample is a mandatory step before the first measurement

A field case: a sample check of chunks caught **~3,500 tokens of service junk in one
chunk** — technical garbage got inside an html tag of a snapshot, and chunking honestly packed it
as "text". It was found with eyes, not with a metric.

Why such a chunk is harmful if search "works": its vector is "about everything and nothing", it
surfaces on unrelated queries; landing in the top-5, it brings the agent 3,500 tokens of junk
into the context, and you pay for them.

The rule: **before the first measurement open a dozen random chunks with your own eyes** — not the corpus,
specifically the chunks, what actually landed in the database. Noisy sources — run through LLM cleanup
before loading.

### 1.3. Corpus language and the choice of embedder

A common situation: the corpus is in Russian, the embedder is an English-centric default
(`text-embedding-3-small`). On the multilingual benchmark MIRACL, small gets ~44 against ~67.8
for BGE-M3: **small on a Russian corpus is mediocre, and this is a known property, not a discovery.**
`text-embedding-3-large` is higher than small, but on Russian it is still lower than BGE-M3 — and 6.5 times
more expensive than small. Working multilingual alternatives: BGE-M3 locally (for example, via Ollama,
dimensionality 1024) or the cloud Cohere embed-multilingual-v3.0 (1024).

Why this is not visible on a small corpus: on 15–22 documents recall@5 is high with almost any
model — the gap shows up as the corpus grows and on hard queries. Hence two rules:

- **measure recall by language** (a per-language breakdown of the golden set) before the corpus has grown;
- remember the price of switching models: it is always a full reindexing — a new collection alongside +
  an alias switch.

And a check that is made before choosing a model, not in the middle of the work: **what can this model
physically be called with from your stack.** A field case: the plan required BGE-M3 through a specific
library — during implementation it turned out that the library does not support this model for
dense embeddings in any release (the issue has hung for years in an unmerged PR). The right
behavior is not to build a workaround but to deliberately replace the component and write down the price of the
replacement (in that case: a secret in `.env` and a network call on every query instead of a local
model). A benchmark is not the only criterion for choosing an embedder; "what to call it with" is the second.

---

## 2. Chunking

Reasonable reference points (for a typical text corpus): cut by structure (headings),
a target size of 300–500 tokens, an overlap of 10–15%, do not break code blocks and tables.
Why this range: a chunk that is too small is a vector without context (a scrap that the
embedding turns into "about nothing"); one that is too large has several topics in one vector,
and it matches each of them equally weakly.

### 2.1. A parameter in the config is an intention; the result is checked separately

The main case of the section. The config has the right target, but in fact **all chunks of the production
collection came out from 110 to 292 tokens — that is, every single one below the lower bound of 300**,
the average is 244. Why: the packer assembles a chunk from blocks and before each next block
checks "if I add it, will I exceed the target?" If yes — it does not add. The target was meant
as "aim here", but it worked as "under no circumstances higher": not a single chunk
reaches it.

A detail that makes the case more instructive: the line with the actual size distribution
**was printed by the ingestion run itself** — nobody simply looked at it. And a second
detail: next to it there was an experimental collection that fell within the range — but the agent
was connected not to it but to the base one.

Why chunks half the target size are bad if recall is green: the document is smeared
across a larger number of points, top-k gets clogged with fragments of one document, the agent receives
scraps without context — **the metric stays green (the document is found, after all), while the quality
of answers quietly sags.**

The rule: **after chunking print and look at min / avg / max of chunk lengths — one line
of code.** If you cannot name these three numbers for your database right now — that is the
signal.

### 2.2. Both edges of the range are a deliberate decision

A mirror case: the config sets only the lower threshold (min 200), the upper one is inherited
from the library default — and the default turned out to equal the embedder's window limit (8,191 tokens).
Formally the pipeline works, but a chunk the size of a whole document passes legitimately,
and the question "what is the largest chunk lying in the database right now?" cannot be answered — the upper
bound was never chosen.

The rule: **both edges of the range are chosen explicitly and written into the report** — otherwise a
month later nobody will say how the database was chunked.

### 2.3. Small chunking decisions worth making deliberately

- **Overlap in tokens or in percent.** With a variable chunk size the percentage "breathes",
  tokens give a predictable overlap. Count the actual share: 75 tokens at a ceiling of
  300 is ~25%, more than the typical reference point. What we pay for a large overlap: duplication of
  the same text in the database and in top-k — two neighboring chunks bring the same thing.
- **Your own tokenizer.** The tokenizer for chunking does not have to match the tokenizer of the embedding
  model — what matters is that the measure is single across the whole pipeline (ingestion and search count
  the same way). But "300 tokens" by your measure and "300 tokens" by the model's measure are different numbers,
  and you just have to know this.
- **Integrity check.** How did you check that code blocks and tables are not torn?
  "Not at all" is an honest but bad answer; the eyes-on sample from 1.2 covers this too.

---

## 3. Ingestion and identifiers

### 3.1. A chunk ID is the answer to the question "what happens on a repeated load"

A random ID → every load breeds duplicates. A deterministic one → the same point
is overwritten. That is why ID design is the foundation of the whole update mechanics.

Technical details:

- Qdrant accepts as a point ID **only a UUID or a number** — so hashes are converted:
  `sha1 → uuid` and `uuid5(namespace, key)` are one family (uuid5 is SHA-1
  of namespace + key); FNV-1a is a different hash, the same role.
- **The main decision is not which hash but what goes into the key:**
  - **A positional key** (`source :: chunk number`): overwriting works, but inserting a paragraph
    at the start of a document shifts the numbers of all chunks below — and they are re-embedded, although
    their text did not change. The variant `source :: section :: n` limits the shift to the boundaries
    of a section — already cheaper.
  - **A content key** (a hash of the chunk's content): unchanged chunks are stable under any
    shifts, but a changed chunk gets a **new** id — the old point remains an orphan
    if it is not deleted explicitly. **A content key without delete mechanics is worse than a positional one.**

The test for ID design — three questions, answer in writing: *what will happen to your IDs on
(a) editing one paragraph, (b) inserting a section in the middle of a document, (c) renaming
a file?* Item (c) is a trap for almost any formula: a new name = a new `source` = **the whole
old branch of the document is orphaned**; this is caught only by deletion by filter or
periodic cross-checking of lists.

### 3.2. Deterministic ids overwrite, but do not delete (orphans)

The mechanics in plain terms: yesterday a document was chunked into 12 chunks with ids `doc::1` … `doc::12`.
Today the chunking rule changed — the same document is cut into 9. We reload: points
1–9 are overwritten with fresh ones, and **points 10–12 nobody touched — they stayed alive**. These are
orphans: search finds them, they hold stale text, and in the point counter they are not visible
(the count is "about the same"). The database starts quietly lying, and there is no error anywhere.

A wording from the production code of one of the pipelines, good as a comment in your code:
*"Deterministic ids overwrite, but they do not delete… survives as an orphan —
retrievable, stale, and invisible in a point count"*.

The cure is three lines: before loading a document, delete all its points by filter
on `source`, then load the fresh ones (**delete-then-upsert**).

### 3.3. The embedding model name goes into the collection metadata, and is checked before the first query

If the corpus was loaded with one model and you search with another — **there will be no error at all**. The query
will honestly turn into a vector, search will honestly find the "nearest" points — it is just that vectors
from different models live in different coordinate systems, and "nearest" is meaningless.
An analogy: one wall was measured in inches, another in centimeters, the numbers were compared — the arithmetic
worked, the result is garbage.

A question for self-checking: *how will you find out in half a year that someone reloaded half
the corpus with a different model?* The usual answer "no way" is the problem.

A working pattern: the model name is written into the collection metadata at creation, and both
scripts — ingestion and search — **check it before the first query and fail on a
mismatch**. It breaks loudly at startup, not quietly in the results. Writing the name into the metadata is
half the job; the check is one check at the start of the script.

---

## 4. Updates and deletion

### 4.1. The maturity ladder

Levels: 0 — full rebuild → 1 — deterministic ids → 2 — delete-by-source →
3 — content hashes → 4 — record manager / periodic cross-check → 5 — statuses and versions.

Important: **a full rebuild is an honest strategy for a small corpus**, it is not a "level zero of
shame". It is worth climbing the ladder when the corpus becomes live.
The step is almost always cheap: from level 1 to 2 it is those same three lines of delete-by-source.

A detailed walkthrough of the ladder, ready-made record managers (LangChain Indexing API, Flowise,
LlamaIndex) with their boundaries, a checklist of seven questions for your own solution and a separate part
on indexing code are in the reference
["Vector database lifecycle and code indexing"](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M2/reference/vector-db-lifecycle-and-code-indexing.md)
(`M2/reference/` in the module repository). The mechanics of the layer itself are in the artifact
[`09-corpus-lifecycle.md`](09-corpus-lifecycle.md).

### 4.2. Two hashes: pay only for what changed

The most mature incremental update mechanism encountered in field pipelines.
Each chunk stores **two fingerprints**: one of the text that is vectorized,
the other of the metadata (status, date, permissions). On a repeated load, comparing the fingerprints
gives three outcomes instead of one:

- the text changed → re-embedding + overwrite (the expensive branch — we pay for the embedding);
- only the metadata changed → update the payload, do not touch the vector (a penny branch:
  the document's status changed — why recompute the meaning of the text, it is the same);
- nothing changed → skip (free).

On a corpus with point edits this cuts costs by an order of magnitude versus "reload everything".
Estimate it on your corpus: how many times is an incremental update cheaper than a full
reload at your edit frequency? On 15 documents the difference is pennies, on a working
corpus with daily edits it is already a budget.

Two questions that must be asked of this mechanism too:

- **"A document disappeared from the corpus"** — is it caught? Cleanup tied to loading a file
  will not see a document removed from the corpus entirely: its file is no longer loaded.
  A periodic cross-check of lists is needed (level 4).
- **Atomicity:** is there a window between delete and insert in which search sees the database
  without the document?

### 4.3. What automation does not solve

- **A change of the embedding model is not handled automatically by any mechanism or any
  ready-made tool** — it is always a rebuild. The best approach: a new collection alongside +
  an alias switch (plus the model name check from 3.3).
- **Update triggers.** On a prototype the update is launched by hand, and that is fine.
  Questions for a working corpus: what will be the trigger — a webhook from the source, a scheduler,
  a manual run? And **who is the data owner — who will even tell you that a document is stale?**
- **A status model** (a point is not deleted but marked `active` / stale) — an option
  for corpora where history matters: the stale is first marked, physically cleaned
  by a separate process.

---

## 5. Hybrid search

### 5.1. How many search paths there are in your project (the right answer is usually "two")

A typical prototype architecture contains **two different searches**, although people think of it as
one:

- **Path A — the measurement script.** The query goes to the database in two branches: by meaning (dense)
  and by words (sparse), the results are fused into one list. On this path all the metrics were
  computed: recall, NDCG, experiments with fusion weights.
- **Path B — the prototype.** The agent (for example, in n8n) searches with a ready-made Vector Store node, and the node
  physically can only do dense: it has neither a second branch nor fusion. On this path
  works what answers the user.

An analogy: **fuel consumption was measured on a test bench with one engine, and the car is sold
with another.** The figure is honest — but it is about the bench.

Where it backfires: the experiment's conclusion "in production we take fusion weights 1:1" — but on the path where
the prototype runs there is no fusion at all, there is nothing there to have weights. The figure moved to a path
it does not apply to.

The rule: **every figure in the report is signed with the path on which it was obtained.** And an explicit
answer to the question: on which path did you measure and on which does the agent answer?

### 5.2. BM25 in plain terms — and why "bm25" in two pipelines can be different things

Two ways to search: **by meaning** (embeddings: for the query "machine" a chunk about
"automobile" will be found) and **by words** (exact match: an article number, a function name, a
product name). BM25 is the standard algorithm for searching by words. It has three ideas:

1. **The more often a query word occurs in a chunk, the more relevant the chunk.** But with saturation: a word
   repeated 10 times is not 10 times better than one — the gain fades quickly. Otherwise
   any text where the word was simply repeated would win.
2. **The chunk length must be taken into account.** A long chunk will catch any word more often simply because
   it is long. Without length normalization the long ones are always on top.
3. **Rare words weigh more (IDF).** The word "error" is in half the corpus — it
   says nothing. The word "PayPal" is in three documents — almost certainly those are what is being
   searched for. Rarity can be computed only by looking at the whole collection.

An example: the query *"payment error PayPal"*. The word branch will raise chunks with "PayPal"
(a rare word, large weight), the meaning branch will find "transaction failure through a payment
gateway", where there is not a single word from the query. Each branch catches what the other
misses — hence the hybrid.

A configuration subtlety: a server-side setting like `"bm25": {"modifier": "idf"}` does
**only item 3** — because only the server sees the whole collection. Items 1–2 (saturation
and length normalization) must be done by whoever creates the sparse vector: either a server-side
model (for example, `Qdrant/bm25` — the full formula from the library), or your own
code on the client. The name is the same — "bm25" — but the places where the formula lives differ; check
who in your pipeline does items 1–2.

A check question: *what happens if you put bare word counts into the sparse vector, without
saturation and normalization?* — long chunks and texts with repetitions start winning; items
1–2 protect against exactly this.

### 5.3. Measurement noise versus the effect of a change (a detective story about a trembling top-5)

The story step by step — from a real review:

1. **The symptom.** The same query, the same database, nothing changed — and the top-5 differs from run
   to run. The metric trembles on its own.
2. **The first diagnosis is wrong.** "It's HNSW being noisy" (HNSW is an index structure that
   for speed searches for neighbors approximately; the documentation honestly says approximate).
   The check: turn on `exact: true` — exact brute force without an index. **The noise did not go away.**
   The diagnosis is wrong — and it is recorded that way in the report.
3. **The real cause is ties.** When fusing two branches, two chunks can score exactly
   the same final score. Which of them is fifth and which is sixth — the formula does not say,
   and the server returns them in random order. If the tie fell on the top-5 boundary, the composition
   of the results changes from run to run — that is the whole "mystery".
4. **The cure.** Fusion was moved into your own code, and a deterministic tie-break
   (source + section + length) was added to equal scores. The same input now
   always gives the same output.

Two conclusions that outlive the specific case:

- **Before fixing, prove that it is an effect and not noise.** A scale that wobbles by itself
  by ±200 grams will not show minus 100 grams from a diet. While the measurement trembles,
  any "improvement after a change" may be noise. First stabilize the scale:
  run the metrics twice in a row and compare to the last digit.
- **A recorded wrong diagnosis is half the value of a review.** The next person who stumbles
  on a trembling top-5 will read the report and will not spend an evening on the same false theory.

---

## 6. Metrics, eval and traps

### 6.1. An example in the prompt must not be taken from the eval set (contamination)

Context: in the golden set, besides ordinary questions there are **trap questions** — those whose
answer is not in the corpus. The right behavior of the system on them is a refusal ("this is not in the database"),
not an invention. Traps test the system's ability to stay silent when there is nothing to say.

The case: one of the two trap questions turned out to be **in the agent's system prompt verbatim** —
together with the ready correct answer, as an example "refuse like this". The agent gets this
question during the check and refuses. What was verified? Nothing: it may not have "understood that there is no answer"
but simply **recognized the question from its own instruction and reproduced the example**.
These two cases cannot be told apart in principle.

An analogy: hand students the exam tickets together with the answers and be glad that the exam is passed.
Passed it is — but what did the exam measure?

An honest detail of the same case: the second trap question did not get into the prompt, and the refusal on it
is clean — that is, the refusal rule itself works. What is broken is not the refusal but the **measurement**: out of two checking
questions, one remained.

The rule: **examples for the prompt are not taken from the eval set.** If you need an example of a refusal — compose
a new question that is neither in the corpus nor in the set. A short formula: the judge does not live
in the defendant's hands. In the module on evals the same phenomenon is called contamination.

### 6.2. A refusal must not be hung on a score threshold

A temptation that occurs to everyone: *"if the top-1 score is below the threshold, we answer
'I don't know'"*. Cheap, no LLM, one line of code.

The case that buries this: a trap question (the answer is not in the corpus!) got a top-1 score of
**1.0000 — the maximum possible**. And real questions whose answer is in the corpus
got from 0.8333 to 1.0000. Where to put the threshold? Any threshold either cuts real
questions or lets the trap through. Such a number does not exist.

Why: **the score measures similarity to the nearest chunk, not the presence of an answer.**
The trap question turned out to be thematically close to some chunk — the similarity is off the charts,
there is no answer. An analogy: "the person in the crowd most similar to the photo" will always be found, even
if the person from the photo is not in the crowd. Maximum similarity ≠ "that's him".

The conclusion: a refusal is the job of the prompt (the rule "answer only from what was found, if there is no answer — say
so directly") and the verification layer, not of a threshold on a number.

### 6.3. "Similar" and "the same" are different questions

A case from an archive pipeline, where the task is not to answer questions but to decide **whether there is already
such material in the database** (deduplication). Inside are two steps: find similar candidates
(retrieval) and decide whether it is a duplicate (classification). Retrieval worked perfectly — the needed
candidate is always in the results (1.00). But the decision "duplicate / not duplicate" was made by a threshold
on the same score — and was wrong in 4 cases out of 10.

The cause is proven, not assumed: **two queries with the same score of 0.839 —
and opposite correct answers** (one is a duplicate, the other is not). The same number
has to mean "yes" and "no" at the same time — which means no threshold will help, wherever
it is set. The point is not in picking the number but in the number not being enough.

The lesson: similarity is a signal for **searching** for candidates. The **decision** ("the same or not",
"is there an answer or not") is made by a separate step: LLM comparison, field matching, rules.
One scalar does not answer two different questions.

The link with 6.2 — the root is common: **people try to load the score with a meaning it does not have.**
In 6.2 the threshold was appointed as a detector of "there is no answer", here as a detector of "this is a duplicate".
They break the same way.

### 6.4. A zero delta of an experiment is a result

The situation: you changed one knob (fusion weights, chunk size) — the metrics did not move or
went down. The temptation is known to everyone: twist the parameters to a pretty number or quietly
not show it. The right behavior is to record it as is **and name the reason why there is no
difference**. An example of a named reason from practice: a breakdown down to the level of branches showed that each
branch finds exactly one document out of the two needed, and the fusion weights will not raise a document from the tail of the
only branch — the delta physically has nowhere to come from.

A nuance of scale: on a corpus of 15–22 documents recall is at the ceiling anyway — there is almost no room for
improvement, a zero delta is a property of the scale, not a failure of the experiment.
**The value of an experiment is the named reason, not the sign of the delta.**

A separate technique is **a methodology control**: before twisting weights in your own fusion
code, check that the 1:1 configuration gives exactly the same numbers as the server baseline.
If 1:1 ≠ baseline — your fusion code differs from the server's, and all the further "delta
from weights" measures the difference between your code and the server, not the effect of the weights. The same logic as
the control group in a drug trial: first prove that the bench in a neutral
position reproduces the initial state, then turn the knob.

Two hygienes of the same craft (the link with 5.3): there the measurement was stabilized (noise removed),
here the bench is checked (systematic error removed). First trust your measurement —
then trust your delta.

---

## 7. Summary checklist

Checks when designing or reviewing a pipeline. The format of the answer to every item:
confirmed by code / confirmed by a run / not checked — and what to add.

**Corpus:**

1. The origin of the corpus and the rights to it are written into the report (who may see it, whether it may
   lie in git, what about the licenses of third-party data).
2. If the corpus is synthetic: the golden set is built independently of the corpus generator.
3. A dozen random chunks were looked at with eyes before the first measurement.
4. The corpus language is checked against the embedder; recall is measured by language.
5. The way to physically call the model from the stack is checked before the choice is fixed.

**Chunking:**

6. The actual min / avg / max of chunk lengths are known (not from the config — from a run).
7. Both edges of the size range are chosen explicitly and written down.
8. It is checked that code blocks and tables are not torn.
9. The actual overlap share is computed and understood.

**Identifiers and ingestion:**

10. A written answer is given: what happens to IDs on editing a paragraph / inserting a section / renaming
    a file.
11. A repeated load does not breed duplicates (deterministic ids).
12. Before loading a document its old points are deleted by filter (delete-then-upsert) —
    or a full rebuild is deliberately accepted.
13. The embedding model name is in the collection metadata, and ingestion + search check it
    before the first query.

**Updates:**

14. Your own level on the 0–5 ladder and the next step are known.
15. The case "a document disappeared from the corpus entirely" is caught (cross-check of lists), or deliberately
    postponed.
16. There is no window between delete and insert in which search sees an incomplete database — or the window
    is understood.
17. It is clear what will be the update trigger on a working corpus and who the data owner is.

**Search:**

18. The number of search paths is counted; every metric is signed with the path on which it was obtained.
19. It is known who in the pipeline does saturation and length normalization for the sparse branch
    (server / client / nobody).
20. The metrics were run twice in a row and matched to the last digit; on ties there is a
    deterministic tie-break.

**Eval:**

21. Not a single question of the eval set appears in the system's prompts (including examples
    of refusal).
22. A "no answer" refusal is not implemented by a score threshold.
23. The decisions "duplicate / not duplicate", "there is an answer / no" are made by a separate step, not by a scalar
    of similarity.
24. Every experiment delta has a named reason; the methodology control (neutral
    configuration = baseline) is passed.
