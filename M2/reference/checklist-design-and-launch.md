# RAG design and launch checklist · Module 2 handout · date 10.08.2026

An end-to-end checklist in six stages, from deciding "do we need search over our own data at all" to
security and compliance. Compiled from recurring practitioner recommendations and research.

**How to use it.** The order of items is not arbitrary: the upper ones are cheaper and prevent rework of
the lower ones. Go through it top to bottom, not selectively. Items marked with a bold word are the places
where people most often save time and then redo everything from scratch.

---

## Stage 0. Before the first line of code

- [ ] The user's task is formulated, not a technical solution. Check: if the answer is
      "we need search over documents", that is not yet a task.
- [ ] Interviews with future users are done, and real phrasings of queries are collected.
- [ ] A set of 20+ "question → correct answer → documents where it lives" triples is built.
- [ ] It is decided how quality will be measured, **before** development starts.
- [ ] The cost of an error is estimated: the price of one wrong answer in this domain.
- [ ] A source questionnaire is done: which channels exist, which are needed, which permissions, how
      sensitive the data is.
- [ ] It is checked whether RAG is needed at all: whether the task can be solved by an SQL query, full-text search,
      a long context, or an agent with tools.
- [ ] A knowledge base owner is assigned: who is responsible for a document being out of date.

## Stage 1. Data

- [ ] Format inventory: what documents, how many, how often they change, who edits them.
- [ ] A parser is chosen for the document class and tested on **your own** sample, not on the vendor's demo.
- [ ] Table extraction is checked separately: it is the main source of silent errors.
- [ ] Noise cleaning is set up: headers and footers, page numbers, repeating headings.
- [ ] The metadata schema is designed **before** the first bulk load: tenant, permissions, source,
      date, version, language, type, tombstone.
- [ ] A record manager is in place: the "document → chunks" link, otherwise deletion is impossible.
- [ ] Deduplication by content hash is set up.

## Stage 2. Index and search

- [ ] The baseline is built on full-text search: it gives a lower bound that you must not
      fall below.
- [ ] At least three chunking strategies are tested, with the **same context budget** in the prompt.
- [ ] The embedder is chosen by measurement on your own golden set, not by a leaderboard. Shortlist from the leaderboard,
      final choice on your data.
- [ ] Model prefixes (`query:` / `passage:`) are checked, if the model requires them.
- [ ] Hybrid search is on: lexical plus vector, fused with RRF.
- [ ] A reranker is connected and its contribution is measured separately from the rest.
- [ ] Metadata filtering happens **before** the ANN traversal, not after.
- [ ] Payload indexes are created on all fields used for filtering.
- [ ] In the hybrid, the same filter is applied to both branches.
- [ ] The embedder version is baked into the index name.

## Stage 3. Generation

- [ ] The number of chunks in the context is configurable and tuned experimentally.
- [ ] Retrieved content is marked as untrusted data.
- [ ] The answer contains source references, and they are clickable down to the specific place.
- [ ] An explicit refusal to answer when there is no context is implemented, and it is tested separately.
- [ ] The output format is checked for stability (models like to slip into tables and lists).
- [ ] Caching is set up: prompt caching and, where appropriate, a semantic answer cache.

## Stage 4. Operations

- [ ] Incremental update works and covers deletions, not just additions.
- [ ] There is a "deleted document is no longer found" test, and it runs automatically.
- [ ] There is a reindexing plan with no downtime (dual-write plus parity check).
- [ ] Index freshness is measured as an SLO, with an alert when the lag is exceeded.
- [ ] Tracing is set up for the whole path: query, rewriting, candidates, final context, answer.
- [ ] The golden set runs in CI on every deploy, with thresholds and an alert on degradation.
- [ ] Logs are reviewed daily for new failure modes, and what is found feeds back into the golden set.
- [ ] The share of out-of-domain queries is tracked separately.

## Stage 5. Security and compliance

- [ ] Permissions are inherited from the source system and applied in retrieval.
- [ ] A cross-tenant isolation test is run: synthetic queries must not return other tenants' data.
- [ ] Fail-closed behavior is verified at all stages.
- [ ] Personal data is redacted before indexing.
- [ ] There is a procedure for complete deletion of a data subject's data, including vectors.
- [ ] Vectors are inside the same protection perimeter as the source documents.
- [ ] The pipeline configuration is documented for audit: model, version, chunking, top-k, prompt.
- [ ] Residency of **all** nodes is checked: embedder, storage, reranker, cache, traces.
