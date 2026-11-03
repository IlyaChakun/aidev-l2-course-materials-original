# Layer 4. Embeddings: choosing a model and calling it correctly

> Module 2 artifact "Context management: RAG and CAG".
> All prices, dimensionalities and model statuses were checked on **10.08.2026**. This is the layer that goes stale
> fastest of all: price lists change, models are deprecated, leaderboards are rebuilt every
> month. Check with the vendor before deciding.

An **embedding** is a vector, a set of numbers into which a model turns text so that texts close
in meaning end up close in space. Vector search looks not for words but for neighbors
in this space.

The main idea of the layer, worth accepting right away: **the choice of model matters less than the correctness
of the call**. The most expensive mistake here costs one line of configuration, does not crash the system,
is not written to any log and is discovered weeks later through an overall drop in quality.

Terms below without explanation: **recall@k** — the share of cases when the needed document
landed in the first k results; **nDCG@10** — a metric that accounts not only for a hit
but also for the position in the top ten; **pp** — percentage points; **reranker** — a model that
reorders the candidates already found; **tokenizer** — what cuts text into tokens
before it is fed to the model.

---

## How to use this document

1. Attach the file to your agent (Claude Code, Cursor, Codex): put it next to your course
   project and say "read `04-embeddings.md` in full".
2. Give it a frame: *"You are helping me choose and correctly call an embedder for my project.
   Walk me through the questions in the section "Questions for brainstorming", one at a time. If I name a model,
   ask where I got that decision and what I checked it with. After each block, record the decision
   in one line"*.
3. Separately, ask the agent to **count the money**: corpus volume in tokens × price per million,
   plus storage at the chosen dimensionality. These are the two numbers that most often turn out to be
   unexpected.
4. Run the result through the checklist at the end.

An honesty check: if after the conversation you can name only the model's name but cannot
show the line of code that calls it, the conversation is not finished. Half of the errors of this layer
live exactly in the call line.

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

**The closest links of this layer.** The model's dimensionality turns into memory and index settings
([`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md)) and into the indexing bill
([`11-economics.md`](11-economics.md)). The model's window limits the chunk size from above
([`03-chunking.md`](03-chunking.md)). Switching the model is always a full reindexing, the migration
pattern is in [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md). The key trap of the layer: you loaded
with one model and search with another — there will be no error, the search will simply turn into garbage; how this is caught
by cross-checking the model name before the first query, see §3.3, and why on a small corpus the difference between
models is not visible — §1.3 in
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

---

## The decision map of the layer

```
WHAT WE CHOOSE                        WHAT WE CONFIGURE AT CALL TIME
├─ model                              ├─ the role of the text: is it a query or a document?
│   └─ screening by leaderboard,      ├─ dimensionality (chosen ONCE, forever)
│      decision on own 80–100 pairs   ├─ truncation: silently cut the tail or fail with an error?
├─ dimensionality                     └─ normalization after truncating the dimensionality
│   └─ the main cost lever
├─ where it runs: API or own hardware          THREE SILENT FAILURES
└─ license and where the data physically lives ├─ prefix / role forgotten
                                               ├─ the document tail is cut off
        WHAT CANNOT BE ROLLED BACK CHEAPLY     └─ the vector is not normalized
        ├─ switching the model generation = re-embedding the whole corpus
        └─ dimensionality within a collection: different dimensionalities in one are impossible

Warning: matching dimensionalities are more dangerous than mismatching ones: different lengths — a loud error
   on the first insert, identical ones — a silent quality leak for weeks
```

---

## Questions for brainstorming with the agent

**About language and corpus**

1. What language is my corpus in and what language will the queries be in? If there is more than one language — are they
   in one collection or in different ones?
2. What is my domain: general prose, legal text, medicine, finance, code? Is there
   a domain model for it, and is it worth the difference?
3. What length are my chunks and what context window do I need from the model? (For some
   Russian-language models it is 512 tokens, and that overrides any recommendations.)
4. What will happen to my search if the corpus is mixed: will the ranking not shift
   toward one of the languages?

**About the call**

5. Is my model asymmetric? That is, does it encode a query and a document in different modes,
   and if so — where is this role specified: by an API parameter or by a prefix in the text?
6. What does the model card of my model say about prefixes? Did I copy the format verbatim or
   invent my own?
7. What does my SDK do by default if the text is longer than the context: fail with an error or silently
   cut the tail?
8. Does my model return a normalized vector, and does that change after truncating the
   dimensionality? Did I check the norm of the first batch?
9. What are the batch limits and do they depend on the specific model within the family?

**About money and dimensionality**

10. How many tokens are in my corpus, and how much does its full indexing cost today? How much
    will reindexing cost in six months?
11. Which dimensionality do I take and why exactly that one? Do I understand that changing it later = recomputing
    the whole corpus?
12. What dominates my bill: embedder calls or storage and search? (Usually the latter,
    and it is determined by the dimensionality, not by the model price.)
13. Does it make sense to run the embedder myself? Did I count the four cost items: API,
    infrastructure, operations, complexity?

**About choice and verification**

14. Where did my decision on the model come from: a leaderboard, a review or my own measurement?
15. Do I have 80–100 "query — relevant document" pairs on my own data? If not,
    how will I collect them in one day?
16. Did I break down the measurement result by document types and query types separately?
17. Did I check the page of deprecated models **before** indexing, not after?
18. Is the model version written into the collection metadata?

---

## 1. Asymmetry: why a query and a document are encoded differently

The situation in search is asymmetric: a short question of three words has to find a long document.
This is called **asymmetric retrieval**. Symmetric is when you look for similar texts
of roughly the same size and genre: duplicate articles, similar tickets, clustering.

Some models are trained for this asymmetry and **expect you to say what the text is**.
This is specified in two ways.

**Way one: an API parameter.** For Voyage it is `input_type="document"` and `input_type="query"`,
for Cohere — `input_type="search_document"` and `search_query`. One vendor's documentation
honestly shows what happens under the hood: a phrase like "Represent
the query for retrieving supporting documents: " is appended to the text. That is, it is the same prefix, just that
the vendor writes it for you.

**Way two: a prefix by hand, right in the text.** For the open models of the E5 family these are literally
the words `query:` and `passage:` at the start of the string:

```python
doc_vecs = model.encode([f"passage: {t}" for t in chunks], normalize_embeddings=True)
q_vec    = model.encode(f"query: {question}",              normalize_embeddings=True)
```

Exactly like this: not metadata, not a header, but two words in the text. The model learned to see them,
and without them it sees a different task.

**What happens if you forget the prefix.** Not an error. Not a warning. For one family
of Russian-language models, without the prefix the model simply **goes into paraphrase mode**: it works,
responds and solves not your task — it looks for rephrasings instead of answers to the question.

**The price of the mistake, measured.** A developer on their own corpus of about 1200 items
(09.07.2026): without role separation recall@5 = **0.72**; if both sides are set as document
— **0.74**; with proper separation — **0.86**. The conclusion inside the measurement matters more than the numbers themselves:
**setting the parameter is not enough, only separating the roles helps.** The biggest gains go to short
queries of two or three words, that is, the most typical ones.

**There is one rule:** get embeddings exactly as written in the model card. Not "roughly
like that", not "by analogy with another model". Verbatim. For Gemini Embedding 2, for example, the task-type
parameter was removed altogether and replaced with a text prefix of a given format — a habit carried over
from the previous version simply will not work there. And BGE-M3 has no prefixes at all, and you
should not add them.

---

## 2. Three silent failures

One thing unites them: **none is written to a log**. The system works, the metrics are green, the quality is
lower than it could be, and you cannot tell this from the API response.

| What you did | What happened | Where you saw it |
|---|---|---|
| Did not set a prefix or role | Quality is lower by tens of percent | Nowhere |
| Did not touch the truncation setting | The document tail did not get into the index | Nowhere |
| Truncated the dimensionality without renormalizing | Cosine similarity started to lie | Nowhere |

**Truncation.** For some vendors truncation is on by default: text longer than the context is shortened
and a vector is returned without a single warning. For another the limit is shared across all data types,
and the documentation directly says that an excess is silently truncated. **On ingestion the right choice is
to turn truncation off and get a loud error** instead of the quiet loss of half a document. An error
is fixed in a minute, a lost tail is discovered a month later.

**Normalization.** After truncating the dimensionality the vector stops being unit length, and cosine
computed as a dot product starts to give wrong numbers. Some models normalize the truncated
vectors themselves, others require you to do it by hand. A one-line check: compute the
norm of the first batch and make sure it is around one.

**What actually comes back in the response.** A list of numbers and a token counter, nothing else. From the response
you **cannot see** how long the vector should be, or whether it is normalized,
or whether your text was truncated. You are obliged to check all three things yourself.

---

## 3. Dimensionality: the main cost lever

A typical conversation about money goes around the price per million tokens: $0.02 versus $0.13.
The conversation is in the wrong place. You pay for embedder calls once, at indexing, but **you pay for storage
and search for the whole life of the system, and they are determined by the dimensionality**.

An order of magnitude for storage: 10 million vectors at 768 dimensions — about 30 GB,
at 1536 — about 61 GB, at 3072 — about 123 GB. Plus the index on top of that.

**Matryoshka** is a property of some models whereby a vector can be cut to a shorter length
and it remains meaningful (the model is trained so that the first dimensions carry the most meaning).
Measured degradation on one popular model by the overall leaderboard score: 1536 → 62.3;
512 → 61.6; 256 → 61.1; 64 → 57.9. That is, **a sixfold saving costs 1.2 points,
and a twenty-four-fold one already costs 4.4**. The inflection point is somewhere between 256 and 64, and each model
has its own.

Three warnings that are not in most reviews:

- **Truncation and quantization do not always add up.** For some providers the parameters are directly
  mutually exclusive: either shorten the vector or compress the numbers, but not both at once.
- **Truncate, do not pad with zeros**, and renormalize after truncating.
- **Different dimensionalities within one collection are impossible.** Matryoshka gives freedom of choice
  **once, at the design stage**, not at runtime.

And separately: not all models have this property. A popular open multilingual model
that is often recommended for Russian does **not support** Matryoshka at all — it has
a fixed 1024.

---

## 4. Leaderboards do not lie, but they do not add up

The same model today is listed at once as **64.6**, as **58.96** and as **~62**
in three different tables. Three task sets, three ways of averaging, none of the numbers is wrong
and they cannot be added up. This is exactly what half of the reviews you will find by searching do.

What is worth knowing about the tables themselves:

- There is the classic leaderboard (dozens of tasks, English-language bias), there is a multilingual aggregate,
  and there is **RTEB** — launched on 01.10.2025 by the maintainers themselves as a response to contamination:
  part of its datasets are private forever, the domains are those where retrieval brings in money (law,
  medicine, finance, code). **The gap between a model's open and private score is a direct
  indicator of the honesty of its rank.**
- **The order at the top changes every month**, and the gap between the first places is one and a half to two
  points. In the sync of 07.08.2026 a 270-million-parameter model stands at the top above
  an 8-billion-parameter model. This is not a table error, it is a consequence of a different set of tasks.
- **Within one line "newer and bigger" does not mean better.** A third-party measurement across three domains:
  the previous generation gave 0.9429 nDCG@3, the flagship 0.9416 at twice the price. Vendor
  measurements say the opposite. This is the best existing argument against choosing by name.

**The procedure that does not change: the leaderboard screens candidates, the decision is made on your own
data.**

---

## 5. The Russian layer: three things that change the decision

Warning: **A disclaimer that applies to the whole module:** any threshold named in the materials was obtained
on English-language corpora. **For Russian nobody has published thresholds, including commercial
vendors.** Your own measurement is mandatory, and this is not a formality.

**First: on long documents lexical search beats neural models** by 13–27
points. The reason is not the language but the model's context limit: a long document does not fit in the window,
and the vector is computed over a stub. The practical consequence: hybrid search on a Russian corpus
with long documents is not "desirable" but mandatory.

**Second, and it changes the order of work: the reranker's effect is inversely proportional to the strength of the embedder.**
An independent measurement on a Russian legal corpus (02.05.2026, 858 acts, 30 labeled
questions): on a strong embedder the gain from the reranker is **within the margin of error**; on a weak one —
9–12 points of nDCG; and one popular reranker **significantly worsened** the result. So: first the
embedder, the reranker after measurement, and not "let's add it just in case".

**Third: compute metrics separately by language from day one.** An aggregate over a mixed corpus
hides a catastrophe on one half.

**Balanced selection "10 plus 10".** A technique for cross-language search. Usually the top 20
is taken from the combined results — and you get a skew: the ranking shifts toward documents of one language
(losses of up to 40%), because the model systematically ranks them higher. Instead you take
**the top 10 separately from the Russian part of the corpus and the top 10 separately from the English part**, and only then
merge the two lists. The numbers are illustrative: the point is that a quota is given to each language separately,
rather than being contested in the overall standings. The same technique applies not only to languages but also to sources
of different lengths.

**What models there are.** The only public independent measurement on Russian production (the same one,
on 858 acts) showed: three models in the top group are **statistically indistinguishable** — one expensive
proprietary, one mid-range proprietary and one local free one. Indexing that corpus
cost $2.84 at one vendor and $0.63 at another. The author honestly names the limitation: 30 questions,
a narrow domain.

**Conclusion for most projects:** your corpus is Russian and small, the difference between top models
will drown in the confidence interval, and three things will decide — **context (512 or 8192), license
and where the data physically lives**.

---

## 6. The procedure for your own measurement

This is the only part of the layer that will survive a change of all the models.

1. **Collect 80–100 "query — relevant document" pairs** on your own data. Do not invent
   queries: take them from support, from wiki search, from chat history. If you have few of your own,
   pairs can be generated synthetically from the corpus, but real ones are always better.
2. **Take three candidates**, not ten. One expensive proprietary, one cheap, one
   local.
3. **Metrics: Recall@20 and nDCG@10.** Recall@20 shows whether the needed document reached the reranking
   stage at all; nDCG@10 — how it landed in the top ten.
4. **Break the result down by document types and by query types separately.** An aggregate hides
   a catastrophe in one category, and this happens more often than it seems.
5. If the difference between candidates is within the confidence interval — **choose
   by non-quality criteria**: price, context, license, where the data lives, whether there is a
   shutdown date.

**What leaderboards do not measure at all:** cross-language search, long documents, the loss of quality
when truncating dimensionality, cross-modal search. If any of these is your case, the leaderboard
is no help to you even as a filter.

**If you have little domain data.** Domain adaptation of the embedder is cheaper than fine-tuning a generator:
about +7.4% nDCG@10 on 6300 pairs, minutes on a single GPU. What decides it is the quality
of the negative examples (similar but wrong), not the number of positives.

---

## 7. Local or via API

**Throughput, to keep the order of magnitude in mind.** A measurement on a laptop (M5 Max, batch 64,
512 tokens, 23.06.2026): a light model — about 14,200 passages per second, a mid-size one — about 4800,
an eight-billion one — about 580. A 25-fold difference between the extremes means a corpus of 10 million
passages is 12 minutes or almost 5 hours, depending on what you chose.

**The break-even threshold.** There is no single number, and this must be said directly. Reference points: utilization of one
server GPU above 30–40% makes your own hardware roughly 20 times cheaper per million tokens;
in terms of the bill, the switch is discussed at around $500 per month of API spend.
You have to count not two items but four: **API dollars, infrastructure dollars, operations
dollars and complexity dollars**. A live anti-case: a team deployed a GPU for five
queries a day that would have cost a couple of dollars on an API.

**When local wins not on money:** the data cannot leave the perimeter, you need offline,
you need independence from a vendor shutting a model down. Then the threshold is not counted at all.

**Two traps of self-hosting.** First: batching with wrong padding alignment
gives a speedup **and at the same time drops quality** — a case where a batch of up to 50 queries
gave a 7-fold speedup and a noticeable regression. Second, an organizational one: if you are building the pipeline
in a low-code orchestrator, check that there is a ready-made node at all for the chosen local library. A regular story:
the library is alive and wonderful, but there is no node either in the core
or in the community, and "local and free" has to be done with a different tool at both points
(at indexing and at query time) — otherwise you get two different spaces, see section 8.

---

## 8. What cannot be rolled back cheaply

Two decisions of this layer are irreversible.

**Switching the embedder generation is a full re-embedding of the corpus.** The most underestimated cost item
in production RAG. There are no public figures for the cost of one migration in person-hours;
there are stories about a weekend of downtime and a 14% drop in recall on a key segment
followed by a rollback.

**Matching dimensionalities are more dangerous than mismatching ones.** This is the key thesis of the layer, and it is worth
playing out by hand:

```python
a = embed_vendor_model(text, dimensions=1024)   # truncation to 1024
b = embed_open_model(text)                      # native 1024
# a 1024 collection will accept both. There will be no error. No meaning either
```

If the dimensionalities **differ** — the database rejects the write with an error. That is luck: the error is loud
and is caught on the first insert. If the dimensionalities **match** — there will be no error at all. The collection
will accept both vectors, search will work, cosine will be computed, and there will be no meaning in it: numbers
from two different spaces are formally comparable and semantically meaningless. This will be discovered
weeks later, through a drop in quality.

**Hence a requirement that costs pennies: the model version and call parameters live in the collection
metadata**, not in the head of whoever created it. A separate frequent case that this same
requirement covers: a vendor silently updates a model revision under the same name, and "the same model"
starts returning different vectors.

**The page of deprecated models must be viewed before indexing, not after.** And know that the dates there are
approximate in both directions: one model with an announced shutdown date of 14.07.2026 was still
responding on 10.08.2026, because the vendor publishes **the earliest possible** date. The reverse
case — a mismatch of shutdown dates between different environments of one vendor — also occurs.

**A technique that removes part of the pain.** One vendor has implemented asymmetric retrieval
between models of one family: documents are indexed with the senior model, and queries
are served by the junior, cheap one, **without reindexing** — they share the same space. The feature
is rare, but if your vendor has it, it is a direct saving on the most expensive operation.

---

## 9. Model table (checked 10.08.2026)

| Model | Dimensionality | $ per 1M tokens | Context | Russian |
|---|---|---|---|---|
| text-embedding-3-small | 1536 → 512 | 0.02 | 8192 | weak |
| text-embedding-3-large | 3072 → 256 | 0.13 | 8192 | moderate |
| voyage-4-large | 2048 / 1024 / 512 / 256 | 0.12 | 32K | claimed |
| voyage-4 | the same | 0.06 | 32K | claimed |
| voyage-4-lite | the same | 0.02 | 32K | claimed |
| Cohere Embed v4 | 1536 → 256 | 0.12 | 128K | 100+ languages |
| Gemini Embedding 2 | 3072 → 128 | 0.20 (text) | 8192 | 100+ languages |
| BGE-M3 (open) | 1024, **no Matryoshka** | own hardware | 8192 | yes |
| An open RU model under MIT (ruMTEB 69.1) | — | own hardware | 4096 | target |

Three rows that change the bill and are usually absent from reviews:

- **At one vendor the first 200 million tokens are free per account** across the whole line.
  For a course project and most pilots this means embeddings cost zero.
- **The batch discount at this same vendor is 33%, not 50%**, with a 12-hour window, and it does not apply
  to free tokens. At two other large vendors batch gives exactly half.
- **The batch limit depends on the model within the family**: 1M tokens for the light one, 320 thousand
  for the mid-size one, 120 thousand for the senior one. Moving to the senior model can break a working batch,
  and it will look like a sudden error in production.

Warning: a live example on the topic "check the price list before calculating": on one vendor's pricing page in one
row there are at the same time $0.00018 per thousand tokens and $0.12 per million — that is $0.18 versus
$0.12. The discrepancy has been sitting there for a second week.

Warning: check the licenses of open models **on the model card**, not in reviews. The same
line in different generations was released under different licenses, including non-commercial ones, and once
the weights were published under the wrong license and later corrected.

---

## Common mistakes

| What not to do | What it leads to | What to do |
|---|---|---|
| Encode a query and a document the same way | recall@5 0.72 instead of 0.86, and not a single log entry | Separate the roles: by parameter or by prefix, exactly as in the model card |
| Set the role parameter "for show", both sides as document | 0.74 instead of 0.86: the parameter alone does not help | Specifically the **separation** of roles: query as query, document as document |
| Leave truncation on during ingestion | The document tail did not get into the index, and this is not visible anywhere | Turn truncation off and get a loud error; fix the chunk length |
| Truncate the dimensionality and not renormalize | Cosine similarity starts to lie on all queries | Compute the norm of the first batch; it should be around one |
| Mix vectors of two models of the same length in one collection | No error, search works, there is no meaning in it; it will come out weeks later | The model version in the collection metadata; a check on insert |
| Choose a model by its place on the leaderboard | One model is at the same time 64.6 / 58.96 / ~62; the leaders change monthly | The leaderboard to screen candidates, the decision on your own 80–100 pairs |
| Add up scores from different tables | Numbers from different task sets; the comparison is meaningless | Look at the slice for your language and domain within one table |
| Take a newer and larger model within a line "since it is the flagship" | Measurement: previous generation 0.9429 versus 0.9416 at twice the price | Compare on your own corpus; if equal, take the cheap one |
| Optimize the price per million tokens | You argue about $0.02 versus $0.13 and do not notice that you pay for storage for the whole life of the system | Count the dimensionality: it determines storage and search |
| Assume quantization adds up with truncation | For some providers the parameters are mutually exclusive | Check your provider's documentation before designing |
| Add a reranker "just in case" before measuring the embedder | On a strong embedder the gain is within the margin of error, one popular reranker worsened the result | First the embedder, the reranker after measurement |
| Compute metrics over a mixed corpus as one number | The aggregate hides a failure on one language or one document type | Separate metrics by languages and types from day one |
| Take the top 20 from the combined results on a bilingual corpus | The ranking shifts toward one language, losses of up to 40% | Balanced selection: the top 10 per language separately, then merging |
| Index the corpus without looking at the page of deprecated models | The new index sits on a model with an announced shutdown date | View the page of deprecated models **before** indexing |
| Deploy a GPU without counting the load | A GPU for five queries a day that would have cost a couple of dollars | Four cost items: API, infrastructure, operations, complexity |
| Check the local library and not check whether there is a node for it in the orchestrator | There is physically nothing to build the pipeline with; two different spaces at indexing and at query time | The same wrapper at both points, check for the node's existence in advance |
| Trust an open model's license from a review | One line in different generations was released under different licenses, including non-commercial ones | Read the model card before commercial use |

---

## Layer readiness checklist

**Call**
- [ ] It is known whether the model is asymmetric, and the roles are separated: query as query, document as document.
- [ ] The prefix format is copied from the model card verbatim.
- [ ] Truncation on ingestion is off; the chunk length is guaranteed to fit in the window.
- [ ] The norm of the first batch's vector is checked (around one).
- [ ] The batch limits are known for the chosen model specifically, not for the family.

**Choice**
- [ ] 80–100 "query — relevant document" pairs are collected on my own data.
- [ ] Three candidates are compared by Recall@20 and nDCG@10.
- [ ] The result is broken down by document types and by query types separately.
- [ ] For a Russian corpus the metrics are computed separately by language.
- [ ] The model's context window is checked, and the chunk size is chosen to fit it, not the other way around.
- [ ] The license is checked on the model card (if commercial use is planned).

**Money**
- [ ] The cost of full corpus indexing today is calculated.
- [ ] Storage at the chosen dimensionality is calculated, including the index.
- [ ] The free limits and the real size of the batch discount at my vendor are checked.
- [ ] The "API or own hardware" decision is calculated across four items, not one.

**Durability**
- [ ] The model version and call parameters live in the collection metadata.
- [ ] The page of deprecated models was viewed before indexing.
- [ ] The dimensionality is chosen deliberately and fixed: changing it later = recomputing the corpus.
- [ ] It is clear how much re-embedding the corpus costs if the model has to be changed.
- [ ] At indexing and at query time **the same** model and the same call method are used.

---

## Links

**Leaderboards** (look at the slice for your language and domain, not the average score)
- MTEB and its multilingual slice: https://huggingface.co/spaces/mteb/leaderboard
- RTEB — part of the datasets are private forever, domains with money-making retrieval:
  https://huggingface.co/blog/rteb
- ruMTEB — as a filter of candidates for Russian, not as a decision

**Vendor documentation** (prices and pages of deprecated models — check before indexing)
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings
- Voyage AI: https://docs.voyageai.com/docs/embeddings
- Cohere Embed: https://docs.cohere.com/docs/cohere-embed
- Google Gemini Embeddings: https://ai.google.dev/gemini-api/docs/embeddings

**Open models**
- BGE-M3 (dense, sparse and multi-vector in one pass): https://huggingface.co/BAAI/bge-m3
- multilingual-e5-large (the `query:` / `passage:` prefixes): https://huggingface.co/intfloat/multilingual-e5-large
- sentence-transformers — the simplest way to run locally:
  https://sbert.net/

**Theory**
- Matryoshka Representation Learning (2022), where dimensionality truncation came from:
  arXiv **2205.13147**
- FastEmbed — a lightweight local embedder on ONNX: https://github.com/qdrant/fastembed
  (warning: the library is alive, but there is no ready-made node for it in popular low-code orchestrators)
