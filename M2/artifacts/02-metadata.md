# Artifact 2. Metadata: what to record at intake so there is something to filter by later

## What this is and how to use it

This is a helper document for one layer of a RAG system: **metadata**. That is, all the fields
that travel next to the chunk text: who the owner is, which document it was taken from, when it was written, who it may
be shown to, where to point in the answer.

How to use it: connect this file to your agent (Claude, Cursor, any other) and work through
the metadata layer with it **for your course project**. Do not read the document like an article: open
the "Questions for brainstorming" section, hand the questions to the agent together with a description of your project and answer
one by one. The output should be a field schema and intake rules written into the repository,
not a feeling of "I understood the topic". A starting prompt, which can be copied verbatim:

```
Read the attached document on metadata in RAG. My project: <description in 5-10 lines:
what the data is, where it comes from, who the users are, whether there is access separation>.
Walk me through the questions from the "Questions for brainstorming" section one at a time, ask
clarifying questions, do not give general advice. At the end assemble: (1) the chunk field schema
as JSON, (2) the intake rules (what we reject, what we put in quarantine), (3) a list of
the decisions I deferred, with reasons.
```

**What is not in the document.** There is no analysis of parsing and cleaning sources (that is the neighboring artifact
on data preparation), no chunking or choice of embedding model, no analysis of search itself.
Metadata is treated here as a separate layer with its own decisions.

**How to read the numbers.** Next to each number there is a source and a date. If the measurement
methodology is not disclosed, there is an "estimate" mark. Thresholds and coefficients from other people's systems
do not transfer to your corpus: they must be remeasured on your own. All the quality thresholds in this document were taken
on English-language corpora; for Russian nobody has published public thresholds.

---

## Map of the set: this file is one of twelve

The module's artifacts walk through the pipeline layer by layer, and the decisions in them are coupled: the upper
bound of a chunk rests on the embedder's window, the metadata schema determines what you can
filter by at search time at all, and cost is made up of the decisions of all layers at once. That is why the files
live in one folder and are meant to be used together: this one is read in full, the others
are opened as needed.

> **Instruction to the agent.** You are reading one file of twelve; the others are next to it, in the same
> folder. As soon as the conversation goes beyond this layer, open the right file and read
> the relevant section before advising. Do not retell the neighboring layer from memory:
> the artifacts contain thresholds, figures with measurement conditions and failure modes that are not in general
> knowledge. Read on demand, not everything at once: first this file, then whatever is needed
> as the conversation goes. If the needed file is not next to you, say plainly which one is needed and ask for it
> instead of making things up. When a decision in one layer breaks a decision in a neighboring one, say
> so right away, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at intake |
| [`02-metadata.md`](02-metadata.md) | Metadata | you are deciding which fields go next to a chunk: source, freshness, permissions, version — and what to filter by later |
| [`03-chunking.md`](03-chunking.md) | Chunking | choosing size, boundaries and overlap; questions about tables, code and structural splitting |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | choosing a model for language and domain, dimensionality, local or via API; the price of switching models |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, merging the branches, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanics, source citation, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletions, record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | how much it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reduction |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End to end | checking what you built: errors where the pipeline works and the metrics are green but the system lies; a checklist of 24 checks |

**Closest links of this layer.** Fields are taken from what parsers actually return
([`01-data-preparation.md`](01-data-preparation.md)), and they work in search filters
([`06-search-and-fusion.md`](06-search-and-fusion.md)) and in citation in the answer
([`08-generation.md`](08-generation.md)). Permissions in fields are not yet security: how they are
applied and go stale is covered in [`10-security.md`](10-security.md). Statuses, versions
and chunk hashes live in [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md). The embedding model name
is also metadata — why it is checked before the first query, see §3.3 in
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md); there too, in §4.2, is the two-hash
mechanism that lets you pay only for what changed.

---

## Layer decision map

The main thing to understand before all the details: **one field, recorded at intake, works
in four places at once.**

```
        METADATA SCHEMA (decided once, BEFORE the first bulk load)
                            │
   ┌───────────┬────────────┴───────┬──────────────────┐
   ▼           ▼                    ▼                  ▼
PREPARATION  FILTERS at search   ACCESS PERMISSIONS   CITATIONS AND LIFECYCLE
source_id   tenant_id            acl_groups      doc_id, revision
section     labels, date         acl_version     content_hash
```

From the same place come three different mechanisms that are often confused, although they are designed differently:

| Mechanism | What it does | Example field |
|---|---|---|
| **Filter** | hard selection of candidates: if it does not fit, it does not take part in search at all | `tenant_id`, `is_deleted`, date range |
| **Ranking** | a soft shift of order: the document stays in the results but moves up or down | freshness, source authority, element type |
| **Provenance** | an address by which you can go back to the primary source and show a quote | `doc_id`, version number, offsets in the text |

**Order of decisions** (work through the layer with the agent in this order):

1. Which fields are mandatory, that is, without them the document is not accepted at all.
2. Which fields are cheap now and unrecoverable later.
3. What goes into the text under embedding and what stays a metadata field.
4. Whether expensive fields are needed: those you pay for with a model call on every chunk.
5. How permissions are structured and at what moment they are checked.
6. How time is structured: dates, lifetime, replacement of one version by another.
7. What the link to the source in the answer is built from.

The rule everything boils down to: **first the metadata schema and the intake contract, then the first
bulk load.** The reverse order costs a reindexing of the whole corpus.

---

## Questions for brainstorming with the agent

Go through them in order. The answer "don't know yet" is also an answer; it must be written into the list
of deferred decisions.

**Field composition**

1. List the data I will have in the corpus. For each source type answer: which fields
   does it give on its own, for free, at the moment of export? What of this will I lose if I do not record it right away?
2. Does my system have access separation between people or organizations? If so, which field
   carries that boundary and where does its value come from?
3. Which fields in my data **change without changing the text**? Status, assignee, priority, labels.
   What happens if they end up inside the embedding?
4. Which fields do I need in order to build a link to the primary source in the answer? Of these,
   what can I actually get: page number, section anchor, timecode, row identifier?
5. Which of the useful fields **can I not** restore after the fact, because the source
   does not store them, while at intake they are visible?

**Format and intake**

6. Which fields will be categorical (type, status, department, product)? What does the controlled
   vocabulary of values look like for each, and who decides what to do with a new value?
7. What does my pipeline do if a mandatory field arrives empty: reject the document, put it
   in quarantine or substitute a default value? Go through each field separately.
8. How are dates written in my sources, and is there a risk of confusing day with month? What do I do
   with a date that could not be parsed unambiguously?
9. If two sources give different values of one field, who wins? Describe the priority rule
   explicitly, not through "whoever wrote last".

**Enrichment**

10. What will the cheapest enrichment step give me: gluing the parent heading and document type
    to every chunk before embedding? What will it look like on my data, show an example.
11. Should I pay for expensive enrichment (a model call on every chunk)? Calculate my corpus:
    how many chunks, how much it will cost once at load.
12. Are there tables in my corpus? What do I embed instead of the table and what do I show the user?

**Filters and permissions**

13. Give 10 real questions users will ask my system. For each
    answer: what filter must be applied before search and is there a field in the schema for it?
14. How narrow are my filters: what percentage of the corpus remains after a typical filter? If
    it is less than a few percent, what does that mean for the chosen database?
15. Where does my service get the user's permissions at query time: from a verified session token or
    from the request body? What happens if the backend calls search with one shared service credential?

**Time and versions**

16. Are there documents in my corpus that go stale? How will the system know that a document is no longer
    in force: by date, by an explicit expiry, by a link to a replacing document?
17. Do my documents have versions? How do I keep the first and third versions of one instruction
    from reaching the model at the same time?
18. What will I do when I need a filter on a field that is not in the schema? Go through three different
    cases: the value is derivable from the text, the value exists in the source system, the value was visible
    only at the moment of intake.

---

## Selection criteria, thresholds, tables

### 1. Three baskets of fields

Memorizing a list of fields is useless. What matters is the division by **what to do when one is missing**.

| Basket | What goes in | What to do if the field is missing |
|---|---|---|
| **Mandatory** | owner or organization (`tenant_id`), permissions (`acl_groups`), source identifier plus chunk number, deletion flag | **Intake rejection or quarantine.** An empty value is unacceptable: without permissions you can neither search nor delete safely |
| **Useful** | two different dates (creation and entry into the corpus), version and relevance flag, type, department, language, structural anchor (file, page, section, breadcrumbs), a short summary of the document | We accept but note: **these fields usually cannot be restored after the fact** |
| **Expensive** | document context for the chunk, synthetic questions for the chunk, tags, model-extracted | Computed separately: the price is linear in the number of chunks |

The decision at the intake boundary is always one of three: **reject, put in quarantine or bring
to the required form.** The last is acceptable only when the transformation provably does not lose meaning.

A separate set is needed if documents go stale: creation date, start and end of validity, document
type, kind (permanent, versioned, event-based), link to the document being replaced, revision
number. Without a "what it replaces" link a chain of versions cannot be built in principle.

### 2. What we embed, what we put in metadata

The watershed in one phrase: **you can glue to the text what distinguishes documents, and you cannot glue what
unites them.**

| Source type | Into the embedding | Into metadata | Citation locator | What breaks it by default |
|---|---|---|---|---|
| Tracker ticket | key and title, description, comments in chronological order | project, type, status, priority, labels, components, version, assignee role, dates, links | link to the ticket plus revision number | status inside the text pulls vectors; comments in the API response are truncated to 20 |
| Wiki page | breadcrumbs in the prefix, then the section text | space, ancestors, labels, type, version and version date, archive flag, review due date, access groups | link to the section anchor plus version | the answer lies in a child page, while the parent is a table of contents and wins on headings |
| Call transcript | utterances with speaker labels | meeting type, participants, "has a decision" and "has a task" flags, meeting series, time binding | timecode | without speaker labels the model cannot tell who said what |
| Correspondence, chats | the whole thread as one unit | venue, channel, date, roles, tags from a controlled vocabulary | link to the specific message | replies like "+1" and "agree" get a junk vector and are not found at all |
| Document or PDF | normalized text plus descriptions of images and tables | file name, page, section title, type, author, language, content hash | page plus region on the page | the bibliography lands in the top because of keyword density |
| Tabular data | a summary of the table in words | the table itself as a stored value, schema separately | row identifier | aggregates are not solved by vector search in principle, it is a computation |
| Code | a description, not the code itself | path, language, symbol, dependencies | file plus line range | the meaning lies in a different directory than the fragment itself |

**Why status cannot be glued into the text.** The word "Closed" occurs in roughly six tickets
out of ten. If it is glued to the description before embedding, it pulls the vectors toward a generalized
"completed work" instead of the specific content. A team that did this rolled back the
concatenation after a measurable drop in search quality. A reverse example from the same practice:
the parent page title glued to the start of the chunk raised nDCG@5 from 0.61 to 0.73
(one team's internal set, not published, take it as a direction, not a norm).

### 3. A ready example: a tracker ticket, three fragments side by side

The data is synthetic. Look at one question: **what changes here without the text changing.**

**(a) What the API returns** (abridged):

```json
{ "key": "PAY-1187",
  "fields": {
    "summary": "Payment hangs in pending on acquirer timeout",
    "issuetype": {"name":"Bug"}, "priority": {"name":"High"},
    "status": {"name":"Done","statusCategory":{"key":"done"}},
    "labels": ["acquiring","timeout"], "components": [{"name":"payment-gateway"}],
    "created": "2026-06-14T09:12:03.000+0300", "updated": "2026-07-02T16:41:55.000+0300",
    "description": {"type":"doc","version":1,"content":["...tree of nodes, not text..."]},
    "comment": {"total":7,"maxResults":20,"comments":["...truncated to 20..."]} } }
```

Three things are visible right away: the description is a **JSON tree, not text**; the comments in the response are
**truncated to twenty** (while all the value of a ticket is often in the long discussion); the total number of
results is not returned by ticket search at all.

**(b) What goes into the embedding** (there are deliberately no state fields here):

```markdown
# PAY-1187: Payment hangs in pending on acquirer timeout
On acquirer timeout the transaction stays in `pending` and does not move to failed.
## Cause
Retries are not idempotent, the idempotency key is not passed.
## Resolution
The limit was raised, Retry-After was added to the response, the import is split into pages.
## From the discussion
2026-06-18: reproduced on the test stand, the gateway returns 504, the worker does not write the final status.
```

**(c) What goes into metadata:**

```json
{
  "doc_uri": "tracker://PAY-1187",
  "url": "https://example.atlassian.net/browse/PAY-1187",
  "tenant_id": "acme-core",
  "project_key": "PAY", "issue_type": "Bug",
  "status": "Done", "status_category": "done", "priority": "High",
  "labels": ["acquiring", "timeout", "postmortem"],
  "components": ["payment-gateway"], "fix_version": "2026.7.2",
  "assignee_role": "backend-engineer",
  "created_at": "2026-06-14T06:12:03Z", "updated_at": "2026-07-02T13:41:55Z",
  "links": [{ "type": "causes", "key": "PAY-1203" }],
  "content_hash": "sha256:9f2c…",
  "acl_groups": ["grp-payments", "grp-eng-all"], "acl_version": 47
}
```

What is load-bearing here. `content_hash` is needed so that "opened and saved without changes" does not lead
to re-embedding: we compared the hash, nothing changed, no model call. `assignee_role`
instead of a person's name: filters are needed by role anyway, while a name in the index is personal data
and an extra risk. `acl_version` makes it possible to mark a chunk stale when permissions change, **without recomputing
the text embedding**.

For a wiki page the set is the same in meaning, with the addition of `parent_chain` (the chain of parents),
`breadcrumb` (a ready breadcrumb string), `version` and `review_due` (until what date the document
is considered verified). An overdue review is a corpus health metric, not somebody's ticket.

### 4. Enrichment: three steps by price

**The first lever is enriching the document, not changing the database and not changing the model.**

| Step | What we do | Price | What it gives |
|---|---|---|---|
| Deterministic header | glue type, date, channel, parent title to the chunk before embedding | **zero model calls** | estimated in project reviews at 5–15% recall; the parent title gave nDCG@5 0.61 → 0.73 on an internal set |
| Context per document | one context paragraph per document, reused on all its chunks | one call per document | the same accuracy as per chunk, **three times cheaper** (reproducible benchmark 06.2026, 10 synthetic contracts and 50 queries, small sample) |
| Context or questions per chunk | one or two sentences of context or synthetic questions for each chunk | a model call on **every** chunk | a published reduction of the failure rate in top-20 by 35 / 49 / 67% |

Note: **35 / 49 / 67% must be quoted together with the nature of the measurement:** this is Anthropic, September 2024,
the metric is the failure rate in top-20 on their own corpus, the embedder is Gemini Text 004. And the other
side: a practitioner who reproduced the method on their own data got a gain of a few percent.
Both sides are right; the number is not an industry norm.

**The economics of enrichment in plain words.** Enrichment is a **one-time fee at load**, not a fee
on every query. You ran the corpus through the model once and then use the result
for free for the whole life of the system. Plus the prompt cache: if the whole document is fed to the model once
and reused on all its chunks, the repeated text is billed at the cache rate rather than at
the full one. This is exactly what makes the expensive step affordable. The order of price at current rates: about
$2.8 per million corpus tokens (rates checked 10.08.2026, prices go stale within weeks).

### 5. Synthetic questions per chunk: what it is for

In plain words. The user writes a **short question**, while the database holds a **long piece of text**.
In embedding space these two things lie rather far from each other simply because they are
of different nature: a question is a question, a document is a document. The trick is that at load time
you ask the model to come up with several questions for each chunk **that this chunk answers**,
and put the vectors of those questions into the index, not only of the text. Then search turns
into matching a question with a question, which is a much fairer comparison. At query time there is no
extra latency: all the work was done in advance.

What was measured:

| What | Result | Source | Caveat |
|---|---|---|---|
| Hypothetical questions instead of the chunk text | claim recall (the share of answer claims supported by what was found) 53.6 → **71.5**; context precision 42.3 → **63.5**; hallucination rate 26.0 → 19.9 | arXiv 2607.29402, 2026, average over 6 datasets | on one of the datasets, when returning a single document, the method is **worse** than the naive one and catches up only at greater depth |
| Number of questions per chunk | Top-1 context accuracy ~73% → ~76% when going from 5 to 10–20 questions | arXiv 2502.10976, 16.02.2025 | the gain holds across different embedders |

Note: **A mandatory consequence: deduplicating the results.** If every chunk is indexed with a dozen of its own
questions, one source text can easily take half the top with its own questions. So you need to pull many times more
candidates from the index and **collapse them by source text** before handing them to the model.

A related technique for an FAQ corpus: vectorize **only the questions**, and attach the answers as a pair.

### 6. A table summary as text, the raw table as a value

A table embeds badly: it is a grid of numbers, not coherent speech. A working layout: **embed
a short verbal description of the table** ("quarterly revenue by region for 2024–2026, four
regions, monthly"), and **store the table itself as a metadata value** and give it to the model or
the user in its original form when the chunk is found. Search goes by the description, the answer is built
from the data. Keep the table schema separately: column names and types will be useful if SQL
generation is layered on top.

### 7. One call instead of seven, and a key dictionary against synonyms

**One-call enrichment.** The naive implementation runs the model once for each metadata
field: a separate call for the title, a separate one for the summary, a separate one for the keywords.
Seven fields is seven passes over the same text and a sevenfold price. The approach that is called
MDKeyChunker in one of the open chunkers does the same thing **in one call**: the model
gets the chunk and a structured response schema and returns all seven fields at once (title,
summary, keywords, entities, questions, semantic key, related keys).

**A rolling key dictionary.** The second half of the same technique. When the model labels chunks one
by one, it does not remember which tags it created earlier, and after a thousand chunks the index holds
"billing", "биллинг" and "оплата" as three different values. A filter on any one of them will find a third
of what is needed. The cure is simple: accumulate a list of already used values and **feed it to the model right
in the prompt** with the instruction "if an existing value fits, take it, create a new one only
if none fits". The dictionary grows as the corpus is processed, hence the word "rolling".

This is a special case of the general rule: **categorical fields are resolved into a controlled vocabulary
at intake, free text in a filterable field is unacceptable.** Free text yields values that
will never be grouped, and any attempt to automatically extract a filter from the user's question
will miss on the value, not on the field.

### 8. The price of filtering: numbers that change the design

A metadata filter is not "a bit slower". There are two ways to apply it, and both break
in their own way.

**Filter after search.** The losses are arithmetic, not random: the predicate matches 10% of
the corpus, the engine returned 50 candidates from the whole corpus, after the filter about five remain.
The user asked for ten, got five, **and the answer says nothing about it**. Make the predicate
stricter and zero remain, which looks like "there is nothing in the database".

**Filter before search.** It protects recall, but on a graph index it can fall apart: if the
filter cuts off 96% of points, less than one link per node remains, and graph traversal just gets stuck
in someone else's neighborhood.

A measurement on 1M points, a public repro kit, parameters m=16 and hnsw_ef=64:

| Filter selectivity | Plain graph | Plus ACORN at query time | Index with filter-aware links | Planner plus ACORN |
|---|---|---|---|---|
| 20% | 62.9% @1.6 ms | 98.9% @4.4 ms | 94.8% @1.2 ms | 100% @10.9 ms |
| 10% | 20.6% @1.7 ms | 98.1% @4.3 ms | 99.0% @1.1 ms | 99.9% @8.5 ms |
| **1%** | **0.1% @1.6 ms** | 67.7% @4.7 ms | **99.8% @1.0 ms** | 100% @1.5 ms |
| 10%, filter matches the query topic | 88.4% @1.7 ms | 98.6% @3.5 ms | 99.0% @1.2 ms | 99.9% @7.2 ms |
| Two conditions at once, 4% | 0.1% @3.9 ms | 95.2% @7.7 ms | 63.7% @1.2 ms | 99.9% @13.9 ms |
| Two conditions at once, 0.012% | 0.5% @2.5 ms | 0.6% @2.6 ms | 1.8% @2.6 ms | **100% @1.3 ms** |

It reads like this. The row with a one percent filter: the plain index answers in 1.6 milliseconds
and returns **0.1% of what is needed**. The dashboard is green, latency is great, the answers are junk.
**Latency monitoring does not see this failure at all.**

Note: **The caveat is mandatory together with the table:** one dataset, one dimensionality, one value
of the connectivity parameter. The spread between rebuilds on a double 1% filter was 70.7 / 72.7 /
74.1%, so a difference of a couple of points cannot be interpreted. The repro kit is open, your own measurement costs
one day of work.

The price of the mode at build time: filter-aware links make indexing a million points more expensive, from 171 seconds
to 448–560, that is 2.6–3.3 times.

### 9. Who fixes filtering how

Settings between databases **do not transfer**. This is a table for choosing, not for memorizing.

| Database | Mechanism | What it requires in advance | How it breaks | Backfilling a field after the fact |
|---|---|---|---|---|
| Qdrant | filter-aware links inside a category, ACORN, a planner by predicate cardinality | an index on the field **before** loading | a combination of two or more strict filters tears the graph; ACORN is off by default | the value is appended cheaply; an index on a new field without a rebuild gives no additional links |
| Weaviate | the allow-list from the inverted index is passed to bypass the graph | nothing at build time, it is a change of the algorithm at query time only | a filter that cuts off exactly what is nearest to the query | no build-time restrictions |
| pgvector | before 0.8.0 the filter was applied after the index scan, from 0.8.0 an iterative scan | nothing, but you need a sensible plan and partial indexes | a 10% predicate with a small `ef_search` gives on average 4 rows out of 10 (release notes, 11.11.2024) | an ordinary column UPDATE, the vector index is not touched |
| Pinecone | native filtering, separation by namespaces | a metadata schema and a layout by namespaces | you cannot search across namespaces in one call | update by identifier or by filter, a limit of 100,000 records per request, **a field cannot be deleted** |
| Milvus | pre-filtering is declared native, separation by partition key | not checked | not checked | not checked |

**A dispute worth knowing about.** One vendor fixes filtering by building links inside categories
and suggests raising the graph connectivity. The original ACORN work directly criticizes raising connectivity
for flattening the graph. At the same time the same vendor implemented the second approach too, and another made
it the default strategy. There is no ready answer: **the choice of mode is a function of the shape of your
filters, not a checkbox in the config.**

**Three operations that are constantly confused.** This is the most frequent mistake in conversation about "a field
after the fact":

1. **Appending a value to an existing index** is cheap, embeddings are not recomputed.
2. **Making a fast and accurate filter on this field** is already a rebuild of the vector index.
3. **Taking a value that the source does not store and that was visible only at the moment of intake**
   is impossible altogether.

The statement "a field cannot be introduced without a full reindexing" is wrong as an absolute and right as
a warning about the price.

**The externalized metadata pattern.** A separate fork: keep embeddings in the vector database
and metadata in a relational one, and do a join at search time. It removes the issue of frequent changes to the schema
and fields, but brings back filtering after search with all its arithmetic losses. It is an honest
fork, not a free solution.

### 10. Permissions are an intake contract, not a query filter

The source of truth for permissions is the source system, the index is its projection. Hence two rules.

**The intake rule:** a document without an owner or without permissions is **not indexed at all**, it goes
to a triage queue. An empty value in the permissions field is an incident, not an omission.

**The query rule:** the search scope is assembled **on the server from a verified token**. Permission fields
that came from the client's request body are discarded. If the backend calls search with one shared service
credential, authorization is performed as the service, and the user's permissions are bypassed entirely.

Why filtering after search does not work for permissions: the data has already left the store, and **for audit there is
no difference between "pulled and discarded" and "not pulled"**. Plus arithmetic: if the relevant chunks of
a specific client lie at positions 40, 55 and 71, the global top-10 may consist entirely
of other people's documents, and after filtering nothing remains.

What to take into account when designing:

- Store permissions as **group identifiers**, not emails and display names: emails change,
  and nested groups do not expand by themselves.
- A permission change in the source is handled as "closed by default": the affected chunks are marked as awaiting
  reindexing and excluded from the results. Under uncertainty the system loses recall,
  not confidentiality.
- Effective permissions are often the **intersection** of container permissions and document restrictions, and
  restrictions are inherited downward. In popular wikis the restrictions API **does not return inherited ones**:
  whoever does not walk the ancestors leaks closed child pages.
- There is usually no batch permission check: 200 candidates at query time means 200 calls and several seconds.
- Permission changes often **generate no events at all**; you find out on the next traversal.

An honest frame for a conversation with security does not sound like "we have no leaks" but like "the
desync window is N minutes, here is how it is measured and here is what does not fall into it".

### 11. A date in metadata does not fix a stale answer

A typical situation: the database holds both the old instruction and an article saying it is no longer in force.
The bot answers from the old one. There is a date field in the metadata. Why it does not help: **the stale
chunk is semantically more relevant**, it is written exactly about what was asked, while the article
about invalidity is written about something else. The mere presence of a date does not change the order of results.

It is fixed in one of two ways: a hard cut by validity period **before** ranking or an explicit decay
in the ranking formula. In both cases you need fields that are usually absent: until what date the document
is in force and which document it replaces.

How a working layer on top of search is built (the retriever does not change):

- **Three validity states:** expired (removed hard), in force, an active time window.
  The third state is usually forgotten, and it is needed.
- **Three kinds of document:** permanent (definitions, reference books), versioned (policies, specs),
  event-based (announcements, outages). Boosting for freshness makes sense only for event-based ones.
- **Decay with a floor.** A formula of the form `0.5 ^ (age / half-life)` and a mandatory
  **minimum per "document type plus kind" pair**, otherwise reference material from 1954 gets
  a multiplier near zero and sinks not because it is wrong but because it is old. Example
  values from the open code of one project: math and constants 0.95, reference books 0.70,
  research 0.10 (09.05.2026).
- Note: **A scale catch.** If search is hybrid and the results are merged by ranks, the raw fusion scores
  are on the order of one sixtieth. An unclamped decay in the range from zero to one will simply
  override them. In one vendor's documentation the decay multiplier is therefore set to 0.1.

**Conflict resolution by type.** A temporal conflict is resolved in favor of the fresher one at comparable
trust; an authority conflict in favor of the source with higher trust; **a scope conflict
is not resolved at all**, both sources are shown.

### 12. The citation: what exactly to record so the link does not rot

The most frequent mistake is a link to a **position number in the results**. The marker `[2]` means "the second element
of the array assembled for this particular query". The array depends on the query, the embedder, the chunker,
the index and the weights. Changed the chunk size, added a reranker, re-embedded: each action is
routine, and each one silently redirects all saved citations. The link keeps opening,
it just points to something else.

A working contract: `SourceRef = { docId, contentHash, start, end, revision }`. `docId` survives
rechunking and re-embedding; `contentHash` (sha256 of the normalized text) finds the same
text in whatever chunk it ends up; `start` and `end` provide graceful degradation, that is,
the ability to highlight the place even if the hash did not match; `revision` records which version was actually
read. **`chunk_id` is deliberately not part of the contract**: it is an artifact of a specific load run.

Four outcomes when showing a link: exact match, the text moved, the version is stale, the source
is gone. A test that catches the problem in one run: ask a question, reindex the corpus
with a different chunk size and check that no citation has turned into "source gone".
The citation verification layer is covered in full in artifact 8.

---

## Typical mistakes

| What not to do | What it leads to | What to do instead |
|---|---|---|
| Introduce metadata at the moment the first filter is needed | A field that was not there at intake has nowhere to come from if the source does not store it. An observation of the moment of intake cannot be restored after the fact | First the schema and the intake contract, then the first bulk load |
| Glue the whole document together with state fields into one string and load it | The frequent value outweighs the content, search measurably gets worse, and any status change requires recomputing the embedding | Semantics in the text, hard conditions in fields. **Price, size, boolean flags and statuses must never be an embedding signal** |
| Permissive date parsing and free text in categorical fields | In numeric dates the order of day and month is ambiguous, a wrong guess gives a plausible and silently wrong date. Free text yields values that will never be grouped | Strict ISO parsing that fails on ambiguities, everything in UTC. Categorical values only through a controlled vocabulary |
| Write fields into the index exactly as they came from the export | Empty strings clog the index with junk values, a date does not sort without type conversion, a hierarchy arrives as a human-readable string instead of a field | A separate cleaning layer: filter out empties, convert dates to ISO, parse the hierarchy into a parent field |
| Hang the filter only on the vector branch of hybrid search | The lexical branch will drag other people's documents into the merged results. This is a direct hole in access separation | The same filter in **both** branches, an index on every filter field |
| Pull forty documents and discard thirty by permissions | The data has already left the store, there is no difference for audit. Plus the results collapse to empty | The filter inside the query, permissions as expanded groups by identifiers |
| Index every chunk with a dozen synthetic questions and leave the results as is | One source text takes half the top with its own questions | Pull many times more candidates and collapse by source text |
| Sort the results by date or cut off everything older than a year | Freshness overrides relevance, reference materials sink not because they are wrong but because they are old | A soft shift by decay with a floor by document type, a hard cut only by an explicit validity period |
| Automatically extract a filter from the question text and not verify the result | Five failure modes, all silent: the model invents a value instead of a field; relative dates without substituting today's date; incompatible filter dialects across databases; the filter failed to build and the question was silently simplified; results are returned despite the failed filter | A value validator against the dictionary, a fallback to pure vector on failure, the extracted filter logged as a separate metric. Permissions must never be extracted this way |

---

## Layer readiness checklist

The metadata layer can be considered designed when every item has an answer in the project
repository, not in someone's head.

- [ ] The chunk field schema is written explicitly, as JSON or a code structure, and lives in the repository.
- [ ] For each mandatory field the behavior on omission is fixed: reject or quarantine.
- [ ] The completeness of mandatory fields is checked automatically and tends to 100%.
- [ ] All categorical fields have a controlled vocabulary of values, and there is a procedure for a new
      value.
- [ ] Dates are parsed strictly, stored in UTC, and the source's date and the date of entry
      into the corpus are distinguished.
- [ ] The priority rule for a conflict of two sources on one field is written down.
- [ ] Every chunk has an embedder version and chunking parameters: without this, regression diagnostics
      turns into excavation.
- [ ] A list of 10 real questions is compiled, and for each it is verified that the needed filter field
      is in the schema.
- [ ] An index is created in the database for each filter field, and created **before** the bulk load.
- [ ] The typical selectivity of filters is known, and for narrow filters the database mode is chosen deliberately.
- [ ] Permissions are stored as group identifiers, the search scope is assembled on the server from the token.
- [ ] There is a permission version field that lets you invalidate a chunk without recomputing the embedding.
- [ ] For aging documents there is a validity period and a link to the replacing document.
- [ ] The citation contract contains no chunk identifier and is verified by a reindexing test.
- [ ] The price of expensive enrichment is computed on your own corpus, and the decision is recorded together with the number.

---

## What to read

Primary sources, public. Dates are given so it is visible what could have gone stale.

| What | Where | Why |
|---|---|---|
| Contextual Retrieval, Anthropic, September 2024 | https://www.anthropic.com/news/contextual-retrieval | The source of the 35 / 49 / 67% figures, with the nature of the measurement and the price of the method |
| HyPE: hypothetical questions at indexing | arXiv 2607.29402 | The largest measured gain among enrichment techniques, together with the authors' caveat |
| QuOTE: how many questions per chunk to generate | arXiv 2502.10976 | The dependence of quality on the number of questions and the requirement to deduplicate results |
| ACORN: filtered search on a graph index | arXiv 2403.04871 | The other side of the dispute about how to fix filtering, and the critique of raising connectivity |
| pgvector 0.8.0 release notes | https://github.com/pgvector/pgvector/releases | Iterative index scans and the filtering behavior before this release |
| Qdrant documentation: filtering, hybrid queries, formulas | https://qdrant.tech/documentation/concepts/filtering/ · `/hybrid-queries/` | An index on a field is created before loading; a planner by predicate cardinality; a decay multiplier of 0.1 |
| Pinecone documentation: updating metadata | https://docs.pinecone.io/guides/manage-data/update-data | The limit of 100,000 records per request and the impossibility of deleting a field |
| Weaviate documentation: filtered search and ACORN | https://weaviate.io/developers/weaviate/concepts/filtering | The allow-list in graph traversal, the default strategy |
| Confluence REST API v2 and Jira Cloud REST API v3 | https://developer.atlassian.com/cloud/confluence/rest/v2/intro/ · `/jira/platform/rest/v3/` | Cursor pagination and page ancestors; comments truncated to 20, no total result count |
| OWASP: RAG security recommendations | https://cheatsheetseries.owasp.org/ | Permissions as an intake contract, limits on context size |

**What is not there, and that is honest.** Nobody has published public quality thresholds for Russian-language
corpora. Nobody has comparative measurements of "whole document versus typed chunks" on one corpus
with one metric. The filtering mechanics in Milvus were not checked in this review.
