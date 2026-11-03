# Module 2 homework: RAG for the course project on Qdrant

The second module's homework gives your agent from the first module search over the course
project's knowledge base. The M1 prototype answers only with what fit into its prompt and knows
nothing about your project's documents. Putting the whole corpus into the prompt is expensive, and
at larger volumes the corpus does not fit into the context at all, so the knowledge is moved out
into a separate store with search. In this assignment you bring up Qdrant, load the project's
knowledge base into it, connect search to your n8n prototype and show with numbers that it works.

The base program is the same for everyone. The advanced level is optional blocks on top of it:
extended retrieval metrics and a comparison of the module's two architectures, RAG versus CAG, on
the same set of questions: by answers, by cost and by speed. You can take one block or both.

## What to submit — the short version first

The work consists of three base parts; advanced adds optional blocks to them. Everything is
submitted together, in one repository.

| Part | What you do | What artifacts remain |
|---|---|---|
| 1. Corpus and golden set | A corpus of documents for the project's role and a reference set of questions for it | the corpus (or a script to obtain it), the golden set file |
| 2. Qdrant and ingestion | A collection, an ingestion script (chunking, embeddings, dense + sparse, payload), a hybrid query and recall@5 computed with your own code | the collection creation script, the ingestion script, the query and metrics script, the metrics table in `report.md`, a screenshot of the collection in the Web UI |
| 3. Search in the n8n prototype | The Qdrant Vector Store node as an agent tool, a run of the golden set through the agent | the workflow export (JSON), the run table and the analysis of the worst question in `report.md`, a screenshot of the agent dialog showing the source |
| Block A (advanced, optional) | Deeper metrics: recall@10, NDCG@5, two-document questions, one before/after experiment | the extended golden set, the updated metrics script, the tables in `report.md` |
| Block B (advanced, optional) | CAG instead of RAG on a copy of the same workflow: the corpus in the context, a cache, the same set of questions, a comparison | the workflow copy, the measurement script, the comparison table in `report.md` |

Plus `process-log.md`: how you worked with the agent while building. The full list is in the
section ["What to submit and acceptance criteria"](#what-to-submit-and-acceptance-criteria), which is the
source of truth for what the submission contains.

## Deadlines and submission format

**Deadlines:** the module theory: August 10. The submission deadline and the practice date will be
announced separately in the course chat and in the LMS. If you see that you will not make it, write
in advance, not on the submission day.

**Submission format:** the work continues in the private repository of your course project from M1;
read access for the teacher's account [`Serg1Kk`](https://github.com/Serg1Kk) has already been
granted. Paste the repository link into the field at the bottom of this assignment in the LMS and
send it with the button: feedback is written there too and attached to your submission. This
module's report does not overwrite the first module's report: put it in a separate file, for
example `report-m2.md` or `m2/report.md` (below it is called simply `report.md`). In the report,
state the submission level and, if you submit advanced, which blocks you did.

**Difficulty:** middle+. You need a working n8n prototype from M1 and Docker.

**Time:** the base program is 5–7 hours with ready infrastructure and a corpus you know; on an
unfamiliar corpus allow another two to three hours for reading. Each advanced block adds one and a
half to two hours. The estimate is honest: two steps cannot be sped up in principle. Labeling the
golden set requires actually reading the corpus, and the iterations up to the recall threshold are
unpredictable: on ten questions a single error costs ten percentage points at once.

## Order of work

The dependencies between the parts are hard, so the order is this:

| Step | What | Why now |
|---|---|---|
| 0 | Make sure the n8n prototype from M1 starts and runs the chain | The assignment stands on it. If the prototype did not come together, sort it out before the start, not along the way |
| 1 | Bring up Qdrant, create the collection with a script | Separates an environment problem from a data problem. Half an hour. Take the vector dimension for the model you plan to use in part 2: changing your mind is cheap, the collection is recreated by your own script |
| 2 | Part 1: assemble the corpus and label the golden set | The labeling is fixed before the pipeline, otherwise the questions get fitted to what was found |
| 3 | Part 2: the ingestion script | Chunking, embeddings, upsert with payload |
| 4 | The hybrid query by script, recall@5, iterations up to the threshold | The least predictable step in time: the reserve goes here |
| 5 | Part 3: search in n8n, a run of the agent over the golden set | Assembled from ready-made nodes |
| 6 | Finish `report.md` and `process-log.md`, attach screenshots | While the runs are fresh: the numbers and screenshots are collected in minutes, and a day later they have to be restored from scratch |
| 7 | The advanced blocks, if you do them | Block A is run with the same metrics script. Block B comes after part 3: the CAG version is compared with the already working RAG version |

## How normal and advanced differ

The base program is the same for everyone: parts 1–3 in full. Advanced is not a different
assignment but blocks on top of the base. Fully do at least one of the two, or both; mark which
ones you did in `report.md`.

| | normal | advanced |
|---|---|---|
| Parts 1–3 | in full | in full, unchanged |
| Block A: deeper metrics | not required | recall@10 and NDCG@5, plus 5 two-document questions, one before/after experiment |
| Block B: CAG versus RAG | not required | a second version of the workflow with the corpus in a cacheable context, a comparison by answers, cost and speed |

**Decoding the table rows.**

- **Block A, deeper metrics.** The base has one metric, recall@5: out of ten questions, for how
  many the needed document ended up in the top five of the results. Block A adds recall@10 (the
  same for the top ten) and NDCG@5 (takes into account exactly which place the needed document is
  at: first is better than fifth). The formulas, a worked example and what to compute with: part 2,
  the section ["How to compute recall and NDCG"](#how-to-compute-recall-and-ndcg). The block also adds
  to the golden set five questions whose answer is assembled from two different documents, and one
  experiment: one pipeline change and the metrics before and after on the same set. The main
  deliverable of the block: the delta, not the absolute number.
- **Two-document questions.** A question counts only when both labeled documents made it into the
  top of the results. Such questions check that search assembles context from several places
  rather than finding one lucky paragraph.
- **Block B, CAG versus RAG.** CAG (cache-augmented generation): the architecture from topic 2.1
  where the corpus is not searched but put into the context whole and cached at the provider. You
  build a CAG version of your own workflow and run through it the same golden set as through the
  RAG version. The result: a comparison table by answer quality, the cost of a thousand requests
  and response speed, plus a conclusion on where, on your project, the border between the
  architectures lies.

## Preparation

### Environment: check before you start

The assignment stands on the M1 prototype, and the first step is blocked if there is no prototype.
Before you begin, make sure that:

- the n8n prototype from M1 starts and runs the whole chain;
- Docker is installed and the machine has at least 2 GB free for the Qdrant volume;
- you have a key for an embeddings provider, or a local Ollama is up;
- **if your n8n is in Cloud:** a local Qdrant is not visible from the cloud, like any localhost
  (we covered the same limitation in M1). Working options: a tunnel, a free Qdrant Cloud cluster,
  a self-hosted n8n next to Qdrant;
- for block B: a provider key with access to direct API calls. The cost measurement is done with a
  script, because only in the API response are the `usage` fields fully visible.

### Module theory

The assignment draws on both sessions of the module; reread them before you start:

- topic 2.1: context caching, the `cache_control` mechanics, prompt structure for the cache,
  measuring the savings, CAG versus RAG;
- topic 2.2: the RAG pipeline, chunking, embeddings, Qdrant and hybrid search, retrieval metrics.

Primary sources with links and dates are collected in [`reading-list.md`](reading-list.md): the
first two sections are needed directly for this assignment.

### Artifacts: helpers for design

In [`artifacts/`](artifacts/) there are helper documents by layer of the RAG pipeline. They are
written to be handed to your agent as context during design and brainstorming, not to be read
straight through: put the file you need in front of it and work through your case with the agent
before writing code. Not all layers take part in this assignment: the database is chosen for you
(Qdrant), the corpus lifecycle and security come in later modules. The ones relevant for the
homework:

| When | Artifact |
|---|---|
| You are assembling the corpus, converting documents to text | [`01-data-preparation.md`](artifacts/01-data-preparation.md) |
| You are designing the payload schema and thinking about what filters will need | [`02-metadata.md`](artifacts/02-metadata.md) |
| You are choosing the chunk size and boundaries | [`03-chunking.md`](artifacts/03-chunking.md) |
| You are choosing the embedding model | [`04-embeddings.md`](artifacts/04-embeddings.md) |
| You are sorting out branch fusion and weights | [`06-search-and-fusion.md`](artifacts/06-search-and-fusion.md) |
| You are looking at what else can be squeezed out of ranking in block A | [`07-reranking-and-context.md`](artifacts/07-reranking-and-context.md) |
| You are teaching the agent to cite and to refuse | [`08-generation.md`](artifacts/08-generation.md) |
| You are computing the economics in block B | [`11-economics.md`](artifacts/11-economics.md) |

Working questions to the agent to start with: "here is my corpus, these formats and volumes, where
is the weakest spot by layer", "propose a metadata schema for my documents and explain which
filters it will give", "assemble ten questions for this corpus so that there are both exact and
rephrased ones among them".

### Where to start if you lack experience

**If you have never worked with a vector database.** Do not start with the full corpus. Bring up
Qdrant, open the Web UI, load two or three documents with a minimal script and run one query by
hand. When the chain "document → chunk → vector → results" works on three documents, the full
corpus becomes a matter of a loop, not of faith.

**If you have not built an ingestion pipeline.** Build it on one document with fixed-size
chunking and get an end-to-end result, then grow it: structural chunking, payload, batch loading.
In [`examples/`](examples/) there are worked-out n8n builds that show how loading and updating are
structured; they import into your instance, but the credentials have been scrubbed from them.

## Part 1: corpus and golden set

### A corpus for the project's role

Search works over your course project's documents. Assemble the corpus for the role that needs
search:

| Project | Who needs search | What is in the corpus |
|---|---|---|
| AI newsroom | Fact checker or Editor | reference materials, the style guide |
| Smart tech support | First-line operator | FAQ, regulations |
| Assistant for DevTools | Documenter | the repository's README and documentation |
| Knowledge curator | Evaluator | criteria and examples of evaluations |

If you run your own project, assemble the corpus for the role that needs search, by the same
logic.

Requirements for the corpus:

- a guideline of 15 documents; more is fine, fewer is not advisable: on a very small corpus the
  metrics show nothing;
- formats: Markdown or plain text, convert in advance;
- total volume: a guideline of 50–100 thousand tokens; more is fine if you already know the
  corpus;
- the metadata schema is fixed: `source` (the document name), `title`, `section`, `date`. They
  will become the payload (the fields Qdrant stores next to the vector) and the basis of filters.

### Golden set

The golden set: a reference set of questions by which you measure retrieval with numbers, not with
an impression.

- 10 real questions to the corpus; for each, the document that holds the answer is marked;
- 2 trap questions: there is no answer in the corpus, and the agent must refuse rather than make
  something up;
- block A: plus 5 questions whose answer is assembled from two different documents; for each, both
  documents are marked;
- if part of the questions was generated by a model, mark that and proofread them by eye: a
  question that nobody would ask your agent spoils the measurement.

The file format is free: a markdown table, CSV or JSON. What matters is that your metrics script
can read it. An example row (the format is indicative, adapt the fields to yourself):

```json
{ "id": 3, "question": "How is an order refund filed?", "answer_doc": "refund-policy.md", "trap": false }
```

Ten questions are a first measurement, not a regression gate: working sets start at roughly fifty
questions, and you will deal with that in the fifth module. For now the task is to learn to count.

## Part 2: Qdrant and the ingestion pipeline

### Deploy Qdrant locally

- Run `qdrant/qdrant` via `docker run`: port 6333, a volume for the data (the quickstart link is
  in [`reading-list.md`](reading-list.md)). Take an image no lower than 1.18.2: in 1.18.1 and
  1.18.2 an authorization bypass and an out-of-bounds buffer read were fixed.
- The fresh image is already 1.19, released on August 5, 2026. Its REST API has the legacy
  endpoints `/search`, `/recommend` and `/discover` removed: any snippet from a two-year-old
  article will return an error, and it will look like a problem with the data or the collection,
  although the matter is the request address. All calls in this assignment go through `/query`, so
  it is not the assignment text that breaks but copy-paste from the internet.
- Check the Web UI at `localhost:6333/dashboard`.
- Create the collection: an unnamed dense vector for the chosen embedding model plus a named
  sparse vector with the IDF modifier (inverse document frequency: the server half of the BM25
  formula) for keyword search:

```json
{
  "vectors": { "size": 1536, "distance": "Cosine" },
  "sparse_vectors": { "bm25": { "modifier": "idf" } }
}
```

  Set `size` for your model: 1536 for text-embedding-3-small, 768 for nomic-embed-text; the
  dimension is written on the model card.
- Vector naming here is a condition of working, not a matter of style. Sparse in Qdrant is always
  named, and dense under this schema stays the default vector. If you give a name to the dense
  vector too, the Qdrant Vector Store node in n8n stops working altogether, even on ordinary
  search: it sends an unnamed vector and gets `400 Wrong input: Collection requires specified
  vector name in the request`.
- Fix the collection configuration with a script in the repository: the collection must be
  recreated with a single command.

### Build the ingestion pipeline

A script: documents → chunks → vectors → Qdrant.

- **Chunking.** Cut by structure (headings), target size 300–500 tokens, overlap 10–15%; do not
  split code blocks and tables. One chunking variant, fixed in the report; the experiment with a
  second size lives in block A. On the assignment's corpus it usually comes out to a hundred
  chunks or more.
- **Embeddings** of your choice, but with one rule: **the same model in ingestion and in n8n**. A
  model mismatch breaks search invisibly: there is no error, the results simply stop making sense.
  Three working paths:
  - cloud: `text-embedding-3-small` ($0.02 per 1M tokens, the assignment's corpus will cost cents).
    In n8n you use the Embeddings OpenAI node, where this model is selected by default. If you go
    through your own OpenAI-compatible endpoint, note that the Embeddings OpenAI node with
    typeVersion 1.2 has no baseURL field in the node itself; your own address is set in the
    credentials;
  - local and free: Ollama. In ingestion you call it over HTTP, in n8n you use the Embeddings
    Ollama node;
  - FastEmbed (ONNX Runtime, no GPU): fine for the ingestion script, but n8n has no FastEmbed
    node, neither in the core nor among the community nodes. If you choose this path, build the
    search in n8n with an HTTP request to Qdrant rather than the Qdrant Vector Store node: how
    exactly is written in part 3. This submission variant is accepted, just mark it in
    `report.md`.

  The sparse vector in all three cases is computed by the `Qdrant/bm25` model on the server side.
- **Upsert.** Write the chunks with a batch upsert with payload (`source`, `title`, `section`,
  `date`). Put the chunk text under the `content` key and the metadata under `metadata`: with other
  names the Qdrant Vector Store node will return empty documents without any error (or else
  override `contentPayloadKey` and `metadataPayloadKey` in the node settings).
- **The embedding model name**: write it into the collection metadata and check it before every
  run.
- **The chunk identifier.** Think through a formula: by what will you find and replace the chunks
  of a specific document when it is updated. For example, a hash of `source` plus the chunk's
  sequence number. This is one of the decisions that live until the end of the course.

### Hybrid query

The hybrid query lives in your script, not in n8n. The schema of the Qdrant Vector Store node has
no vector name, no `prefetch` and no fusion: requests to support them have been open since 2024
and are not closed. So you write the hybrid with metrics computation in code, and in part 3 n8n
gets ordinary dense search. This is not a workaround of the assignment but the boundary of a
low-code tool and one of the reasons why in the third module search moves into code.

- A query through `/query`: `prefetch` with two branches (dense and sparse), RRF fusion
  (Reciprocal Rank Fusion: a document gets from each branch a score of 1/(k+rank), so the score
  scales of the branches do not need to be brought to one another; k here is an implementation
  constant, it is not configurable in Qdrant and there is no need to tweak it).
- Run the golden set and compute recall@5 with your own code (how exactly: the next section). The
  threshold: no lower than 8 out of 10.
- If recall is below the threshold, first look by hand at the chunks of the failed questions
  (usually the culprit is document parsing or the chunk size), then tune the parameters.

### How to compute recall and NDCG

First the meaning in plain words, then the formulas.

- **recall@5:** out of your questions, for how many the needed document ended up in the top five
  of the results. Answers the question "do we find it at all".
- **recall@10:** the same about the top ten. Comparing it with recall@5 shows whether search loses
  documents completely or just fails to pull them to the top.
- **NDCG@5:** takes into account not only "did the document make it into the five" but also the
  place it stands at: first is better than fifth. Answers the question "is what was found ranked
  well".

All the metrics are computed from the hybrid query's results, before generation: the agent and its
answers do not take part in this section. There is one run: for each question save the first 10
results with their `source`, then arithmetic over what was saved. The base program needs only
recall@5; recall@10 and NDCG@5 come with block A but are computed by the same script.

What to compute with: an ordinary script in your language, no libraries are needed, it is an
average and a logarithm. Input: the golden set file and the saved `/query` responses; output: the
metrics table. Setting the task for the agent for this script is the material for
`process-log.md`.

**recall@5.** For each question: 1 if the document with the answer made it into the first 5
results, otherwise 0. For block A's two-document questions: 1 only if both documents are in the
top five. The set's recall@5: the average over the questions. The "8 out of 10" threshold is
recall@5 = 0.8 over the ten main questions. The traps do not take part in recall: they have no
correct document, they test the agent in part 3.

**recall@10.** The same, with a window of 10 instead of 5. If recall@10 is noticeably higher than
recall@5, the documents are found but do not get pulled to the top of the results: what needs
treating is the ranking (branch weights, fusion), not the corpus.

**NDCG@5** (normalized discounted cumulative gain). Computed in three steps.

1. DCG@5 of a question: the sum over the result positions from the first to the fifth:
   rel / log2(position + 1), where rel = 1 if the document with the answer is at that position,
   otherwise 0.
2. IDCG@5 of a question: the DCG of the ideal results, where the needed documents stand from the
   first position. For a one-document question IDCG = 1. For a two-document one:
   1 + 1/log2(3) ≈ 1.63.
3. NDCG@5 of a question = DCG@5 / IDCG@5. The set's NDCG@5: the average over the questions.

An example. The document with the answer was found at the third position: DCG = 1/log2(4) = 0.5;
IDCG = 1; NDCG@5 = 0.5. Had it stood first, the result would be one. recall@5 is the same in both
cases: 1. This difference is exactly what NDCG adds to recall.

This is what the final metrics table in `report.md` looks like (the numbers are made up, this is a
format guideline, not a sample to copy):

```markdown
| Metric    | Value          |
|-----------|----------------|
| recall@5  | 0.8 (8 of 10)  |
| recall@10 | 0.9 (block A)  |
| NDCG@5    | 0.71 (block A) |
```

## Part 3: search in the n8n prototype

### Connect Qdrant to the agent

- In the n8n prototype from M1 add a Qdrant Vector Store node with the same collection and an
  Embeddings node of the same model as in ingestion.
- Connect it as a tool to the AI Agent: the **Retrieve Documents (As Tool for AI Agent)** mode,
  top-k 5. There are two modes with similar names, and the second one gives an `ai_vectorStore`
  output, which does not connect to the agent: choose exactly the As Tool variant.
- In the tool description, write when the agent should search the knowledge base and when to
  answer without searching.
- Extend the role's system prompt: answer questions about the base only from the retrieved
  fragments, at the end of the answer give the `source` of the chunks used, and when there is no
  answer in the base, say so explicitly.
- **If you took the FastEmbed path:** the Qdrant Vector Store node does not suit you, there is
  nothing to compute the question's dense vector with in n8n. Connect to the agent an HTTP Request
  Tool node with a POST to `/collections/<name>/points/query` and search with the sparse branch:
  the question text is passed directly in the request, bm25 is computed on the server:
  `{"query": {"text": "<question>", "model": "Qdrant/bm25"}, "using": "bm25", "limit": 5,
  "with_payload": true}`. In n8n the search is then keyword-only, and the hybrid stays in your
  script: an honest compromise of the path without cloud keys, mark it in `report.md`.
- If you need the hybrid specifically inside n8n: there is an official community node
  `n8n-nodes-qdrant` from qdrant-tech (resource `search`, operation `queryPoints`; it accepts
  `prefetch`, fusion, `using`, `filter`, `limit`; it is marked as an AI tool and attaches to the
  agent directly). Conditions: self-hosted with `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE=true`
  (since n8n 1.79.0) or Cloud 1.94+ with verified community nodes enabled; on Cloud without admin
  rights the path is unavailable. It is not required for the submission: dense search with the node
  is enough.

### Check the quality of the answers

A run of the golden set through the agent as a whole: now not only search but also generation with
citation.

- Run all 10 questions; record: the correctness of the answer, whether the real source is given,
  whether there is any fabrication.
- Run the 2 traps: the agent must refuse rather than make up an answer.
- Put the results together in a table in `report.md`. This is what it looks like (the rows are
  made up, this is a format guideline):

```markdown
| Question                      | Found   | Source cited | Comment                          |
|-------------------------------|---------|--------------|----------------------------------|
| How is an order refund filed? | yes     | yes          | the answer is complete           |
| What is the attachment limit? | no      | no           | the chunk with the limits table was split |
| Trap: competitor's pricing    | refused | ...          | refused correctly                |
```

- For the worst question, write 2–3 sentences of diagnosis: the chunk, the search or the prompt.
  One analyzed failure is worth more than a general percentage.

## Advanced blocks

Both blocks rest on a finished base program. Fully do at least one; you can do both.

### Block A: deeper metrics and one experiment

1. Extend the golden set with five questions whose answer is assembled from two different
   documents; for each, mark both documents.
2. Compute recall@10 and NDCG@5 with the same script as recall@5: the formulas, the example and
   the table are in part 2.
3. Run one before/after experiment, of your choice (you can do both, one is mandatory):
   - **tuning the fusion branch weights.** A weighted RRF is set as
     `{"rrf": {"weights": [3.0, 1.0]}}`, the number of weights must match the number of `prefetch`
     branches. The table: the metrics with equal weights and with tuned ones;
   - **comparing two chunk sizes.** The same corpus, two target sizes (for example 300 and 500
     tokens), two runs on one set. Load the second chunking into a separate collection or recreate
     the collection with the script: you already have it.
4. For each before/after table: two or three sentences of conclusion. What changed, why you think
   so, what you would take to prod. The delta on your own set is the main deliverable of the block.

This is what the experiment table looks like (the numbers are made up, a format guideline):

```markdown
| Metric    | Before (weights 1:1) | After (weights 3:1) |
|-----------|----------------------|---------------------|
| recall@5  | 0.8                  | 0.87                |
| recall@10 | 0.9                  | 0.93                |
| NDCG@5    | 0.71                 | 0.78                |
```

### Block B: CAG versus RAG on the same prototype

Topic 2.1 is entirely about caching and CAG, and it is the only place in the course where you can
compare both architectures of the module by hand on your own project. The idea: the same agent,
the same questions, but instead of searching Qdrant the corpus is put into the context whole and
cached at the provider. On a corpus of this assignment's size that is possible, and the question
"why RAG then" becomes concrete: everyone's answer is their own, and it is in numbers.

**The CAG version of the workflow.**

- Make a copy of your workflow from part 3. In the copy, disable the search tool and put the whole
  corpus into the system prompt after the role's instructions: the stable part (role, rules,
  corpus) first, the variable one (the question) at the end, no timestamps and IDs at the start.
- Check that the corpus fits into your model's window together with the prompt and the answer. If
  not, take a subset of the documents and compare on those golden set questions whose answers are
  in that subset: the same questions for both versions, otherwise the comparison is unfair.
- Mind the tool's boundary: in the n8n copy the cache really works only with OpenAI, where it is
  automatic. The Anthropic node in n8n does not set `cache_control`, so with Anthropic the CAG
  version's runs in n8n go with full input and no cache: this does not affect the quality of the
  answers, but do not run a long series in n8n, and compute the cache economics with the
  measurement script below.
- Run the same set through the CAG version: 10 questions and both traps. The table is the same as
  in part 3. Look at the traps separately: when the whole corpus is in front of its eyes, the model
  is more willing to make things up, and "there is no answer in the corpus" has to be checked, not
  assumed.

**The cache and the cost measurement.**

- Do the measurement with a script making direct API calls (10–20 requests in a row with an
  identical prefix): only that way are the `usage` fields fully visible.
- Anthropic: enable `cache_control` on the last stable block. OpenAI: the cache kicks in
  automatically with a prefix of 1024 tokens or more, with no code changes.
- The minimum length of a cacheable prefix depends on the model: 512 tokens for Opus 5, 1024 for
  Sonnet 5 and Opus 4.8, 2048 for Opus 4.7, 4096 for Opus 4.6 and Haiku 4.5, 1024 for OpenAI. A
  prefix shorter than the minimum is silently not cached: zero hits and not a single error. With
  the corpus in the prompt you are certainly above the minimum, but it is worth checking.
- Collect per series: `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`
  (Anthropic) or `cached_tokens` (OpenAI). With Anthropic `input_tokens` is only the tokens after
  the last breakpoint: the full input is the sum of three fields.
- The expected order: the first request writes the cache (with Anthropic that is 1.25x the input
  price), from the second a read at 0.1x; the hit rate on a series is above 50%. If both cache
  fields are zeros, the prefix was not cached: check the length and the variable fields at the
  start of the prompt.

This is what the series measurement table looks like (the numbers are made up, a format guideline;
with OpenAI there is one cache field instead of two, `cached_tokens`):

```markdown
| Request | input_tokens | cache_creation | cache_read |
|---------|--------------|----------------|------------|
| 1       | 1,210        | 48,000         | 0          |
| 2       | 1,180        | 0              | 48,000     |
| ...     | ...          | ...            | ...        |
| Total   | hit rate 19/20, input savings 62%          |
```

**Comparison with the RAG version.** The result of the block: a table in `report.md` where both
versions are compared on one set along three axes, and a conclusion.

- **Answers:** how many questions out of 10 each version closed correctly, what happened with the
  traps.
- **Cost:** the input price of one request and the price of 1000 requests for each version at your
  provider's rates. For the RAG version the input is the role prompt, the question and the top-k
  chunks. For the CAG version: a cache read of the whole corpus in every request plus a cache write
  once per TTL.
- **Speed:** the average response time per question over an identical series. Both versions are
  workflows in n8n, so look at the time in the executions list. The comparison is rough, n8n
  itself is in it too, but it shows the order and the difference between the architectures. Which
  is faster is not obvious in advance: RAG has a shorter input, CAG has no search stage. Your
  numbers are the answer.
- **Conclusion:** at what corpus size and what traffic on your project CAG is more profitable, and
  where it runs into the model's window or the price of cache reads. Three or four sentences, with
  your own numbers.

This is what the final comparison table looks like (the numbers are made up, a format guideline):

```markdown
| Axis                        | RAG version     | CAG version                    |
|-----------------------------|-----------------|--------------------------------|
| Correct answers out of 10   | 8               | 9                              |
| Traps (2)                   | both: refused   | one: made up an answer         |
| Input of one request        | ~2,500 tokens   | ~50,000 tokens, 96% of it cached |
| Price of 1000 requests (input) | $0.9         | $1.8 + $0.06 cache write       |
| Average response time       | 7 s             | 9 s                            |
```

## Where it usually breaks

A short collection of the rakes most people step on. Everything "works", there is no error
anywhere, and the result is garbage:

- **Different embedding models in loading and in search.** There is no error, the results simply
  stop making sense. Keep the model name in the collection metadata and check it before every run.
- **Payload keys are not `content` and not `metadata`.** The Qdrant Vector Store node will return
  empty documents and will not tell you that anything is wrong.
- **A name on the dense vector.** The n8n node stops working even on ordinary search: it sends an
  unnamed vector and gets a 400. Sparse is always named, and dense under this schema stays the
  default vector.
- **Copy-paste onto old endpoints.** The 1.19 image has no `/search`, `/recommend` and
  `/discover`; snippets from old articles return an error that looks like a data problem.
  Everything goes through `/query`.
- **n8n Cloud does not see localhost.** Neither your Qdrant nor a local Ollama. A tunnel, Qdrant
  Cloud or a self-hosted n8n next to it.
- **The wrong node mode.** Retrieve Documents comes in two variants; only As Tool for AI Agent
  connects to the agent.
- **Chunk overlap.** The assignment says 10–15%, the common heuristic is 20%, some sources say
  20–50%, and a systematic check at the start of 2026 found no measurable gain from overlap at all.
  Take the assignment's number: on fifteen documents the difference is unmeasurable, and what you
  submit is the delta between your own runs, not an absolute.
- **The cache is "set up" but there are zero hits.** A cache miss is silent: both cache fields are
  zeros. First check the prefix length against the model's minimum, second: variable fields at the
  start of the prompt.

The first question for an empty or meaningless result is always the same: are these exactly the
right keys, the right vector names and the right versions.

## What to submit and acceptance criteria

### What to attach

Everything in the course project's repository, the link in the answer field in the LMS or in the
course chat:

- the corpus or a script to obtain it; if the documents cannot be put in the repository, attach a
  script or a description of the source, and describe the corpus composition in `report.md`;
- the golden set: 10 questions + 2 traps; block A: plus 5 two-document ones;
- the collection creation script and the ingestion pipeline;
- the hybrid query and metrics computation script;
- the n8n workflow export (JSON) with the Qdrant Vector Store and AI Agent nodes; if you took the
  FastEmbed path, there will be an HTTP Request Tool instead of the node, mark this in `report.md`;
- `report.md` following the skeleton below;
- `process-log.md` following the skeleton below: how you set the task to the agent while building
  the ingestion script, what steps you split the work into, how you checked the result of each
  step. An export of the session from your IDE plus 10–15 lines in your own words is enough;
- screenshots: the collection in the Qdrant Web UI; the agent dialog with the answer and the
  source;
- block B, if you did it: the export of the CAG version of the workflow, the measurement script.

### What to write in report.md

The sections are copied as headings:

```markdown
# Module 2 homework report

## Submission level
normal or advanced; for advanced: which blocks you did.

## Corpus
The project's role, the corpus composition: how many documents, from where, total volume.

## Collection schema
The embedding model and its dimension, the chunk identifier formula, the payload schema.

## Golden set
The composition of the set, how it was labeled, what is in the traps. If part of the questions
was generated by a model: a note and a confirmation of proofreading.

## Retrieval metrics
The metrics table: recall@5; block A: plus recall@10 and NDCG@5, the before/after experiment
table, a conclusion.

## Agent run
A table: question → found or not → source cited → comment.
Separately: behavior on the two traps.

## Analysis of the worst question
2–3 sentences: what broke (chunk, search, prompt) and why you think so.

## Block B: CAG versus RAG (if done)
The cache measurement table, the comparison table on one set: answers, cost of
1000 requests, speed. A conclusion: what is more profitable on your project and up to what boundary.
```

### process-log.md skeleton

```markdown
# Process of working with the agent: module 2

## How I set the task
The wording you came to the agent with before building the ingestion script.

## What steps I split it into
A list of steps, one sentence per step.

## How I checked each step
Step → way of checking → result.

An export of the session from the IDE: a file alongside or a link.
```

### Acceptance criteria

- [ ] Qdrant comes up, the collection is recreated with one command by a script from the
      repository.
- [ ] The whole corpus is in the collection: dense + sparse vectors, payload with the fields
      `source`, `title`, `section`, `date`.
- [ ] One embedding model in ingestion and in search, the model name is recorded in the collection
      metadata.
- [ ] recall@5 on the golden set is no lower than 8 out of 10, computed with your own code.
- [ ] The agent answers from the base, gives the `source` and refuses on both trap questions.
- [ ] `report.md`: the metrics and agent run tables, the analysis of the worst question. Numbers,
      not impressions.
- [ ] `process-log.md` shows the process: the task setting, the breakdown into steps, the check of
      each step.
- [ ] The advanced level (if you submit it): at least one block is fully done. Block A: five
      two-document questions in the set, recall@10 and NDCG@5 computed, the before/after
      experiment table with a conclusion. Block B: the CAG version answers on the same set, the
      cost of both versions is computed from the `usage` fields rather than estimated, the
      comparison along three axes with a conclusion.

## The course project map: how results are reused later

This is stage 4 of the course project, the RAG part. Stages 1–3 (the MCP server, the agent roles,
the n8n prototype) were submitted in M1.

Three decisions from this assignment live until the end of the course, and redoing them later is
expensive: changing any of them means reloading the corpus from scratch.

1. The payload schema: which fields sit next to the chunk.
2. The chunk identifier formula: by what you will find and replace pieces of a document on update.
3. The embedding model name recorded in the collection metadata.

| Module | What happens to this assignment's artifacts |
|---|---|
| M3–M4 | Search moves from an n8n node into a LangGraph agent tool; the collection and the ingestion script are reused unchanged |
| M5 | The golden set becomes the core of the automatic evals of retrieval and generation |
| M6 | Knowledge base queries get into tracing together with the agent's other steps |
| M7 | The cost of a search request and the block B comparison (if you did it) go into the agent's unit economics |
| M7, security topics | The knowledge base and the payload filters go through an audit: data isolation and corpus poisoning |

The cleaner the ingestion and the metadata are now, the less rework in M3–M5.

## How to submit your work

At the bottom of this assignment in the LMS there is one input field. Paste into it the link to
your private repository and press the submit button. Nothing else needs to be added to this field:
the work itself lives in the repository.

Submit your work exactly this way, even if you already sent the link to the course chat. Feedback
is written in the LMS and attached to your submission: anything sent outside this field is left
without feedback and without a mark.
