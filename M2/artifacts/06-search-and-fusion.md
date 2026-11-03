# Artifact 6. Search and fusion: why the database always returns something

## What this is and how to use it

This is a helper document for the **search** layer: what exactly to ask the database, in how many ways to search,
how to combine the results of several ways into one list, and how to tell that the answer is not in the database.

How to use it: connect the file to your agent and work through search **for your course
project** with it. The document is not for reading straight through, it is for working through questions. The result should be
a list of decisions with numbers. A prompt to start with:

```
Read the attached document on the search layer in RAG. My project: <description: what data,
what questions will be asked, whether there are identifiers such as SKUs and ticket numbers,
which embedder I plan to use>. Walk me through the questions from the "Brainstorm questions" section
one at a time. For each decision, ask what I will back it up with: a measurement or an assumption.
At the end, assemble: (1) the search scheme, (2) a decision log in the format "implemented, measured, kept
or rejected, wrote down the number", (3) a list of what I decided not to do, and why.
```

**What is not in the document.** There is no reranker or context assembly here (the neighboring artifact 7), no
answer generation (artifact 8), no internals of indexes and vector databases (artifact 5). The mechanics of
metadata filters are covered in artifact 2, here only what concerns a filter specifically
in hybrid search.

**How to read the numbers.** Each one has a source and a date next to it. Any foreign threshold is a foreign corpus
and a foreign model: on your data the number will be different. All quality thresholds in the document were taken
on English-language corpora, there are no public thresholds for Russian.

**Explanations of terms that keep coming up below.** *Recall* is the share
of the needed material that the search got at all: if the corpus has five correct documents and three were found,
recall is 0.6. *Hit@10* is "did the needed document land in the top ten of the results", the share of queries
where it did. *nDCG@10* is the quality of the **order** in the top ten: not only whether the needed item was found,
but whether it sits at the top. *MRR@10* is the mean reciprocal rank of the first correct answer.

---

## Set map: this file is one of twelve

The module's artifacts walk through the pipeline layer by layer, and the decisions in them are interlinked: the upper
bound of a chunk runs into the embedder's window, the metadata schema determines what you can filter by
at search time at all, and cost is the sum of the decisions of all layers at once. That is why the files
sit in one folder and are designed to be used together: read this one in full, open the others
as needed.

> **Instruction to the agent.** You are reading one file out of twelve; the others are next to it, in the same
> folder. As soon as the conversation goes beyond the boundary of this layer, open the relevant file and read the
> relevant section before giving advice. Do not retell the neighboring layer from memory:
> the artifacts contain thresholds, figures with measurement conditions, and failure modes that are not in
> general knowledge. Read on demand, not everything at once: this file first, then whatever is needed
> as the conversation goes. If the file you need is not next to this one, say plainly which one is needed and ask for it,
> instead of making it up. When a decision in one layer breaks a decision in a neighboring layer, say
> so right away, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at ingestion |
| [`02-metadata.md`](02-metadata.md) | Metadata | you are deciding which fields go next to a chunk: source, freshness, permissions, version, and what to filter by later |
| [`03-chunking.md`](03-chunking.md) | Chunking | you are choosing size, boundaries and overlap; questions about tables, code and structural chunking |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | you are choosing a model for the language and domain, dimensionality, local or via API; the price of changing the model |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, branch fusion, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanics, source citation, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletion, record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reduction |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End-to-end | checking what was built: errors where the pipeline works and the metrics are green, but the system lies; a checklist of 24 checks |

**This layer's closest links.** Filters work only on the fields that are set up
in [`02-metadata.md`](02-metadata.md), and they are also what implements access rights
([`10-security.md`](10-security.md)). This layer's results are then reordered
([`07-reranking-and-context.md`](07-reranking-and-context.md)) and go off into the answer
([`08-generation.md`](08-generation.md)); index and sparse-vector settings are in
[`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md). Three things from practice that
are worth reading before the first measurement are in
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md): how many search paths
there actually are in your project and which of them the computed metric refers to (§5.1), who in your
pipeline does saturation and length normalization for BM25 (§5.2), and why a score is not suitable
for "no answer" detectors (§6.2).

---

## Layer decision map

```
 query → QUERY HANDLING      rewrite · extend with dialogue context ·
   │     (often absent)      split into subquestions · pick a route
   ▼
 SEARCH: one branch or several    full-text · learned sparse ·
   │   FILTER into EACH branch    dense (vector) · tensor
   ▼
 FUSION of results   by ranks (RRF) · by distribution · weighted · by a trained ranker
   ▼
 CUTOFF   warning: on the fused score it DOES NOT WORK, see section 4
   ▼
 then the reranker and context assembly (artifact 7)
```

**The order of work is the reverse of the usual one.** First corpus quality, then direct search, then
the reranker, and **only then** query-side tricks. The reason is economic: work at load time
is paid for once, work at query time is paid for for the whole life of the system, so a query-side
trick has to clear a noticeably higher bar.

**The main selection rule, good as the only slide for the whole layer:** do not add a step until
you can name the specific failure it fixes and the latency you are willing to pay for it.
Otherwise it is expensive theater: latency grows, failure analysis gets murkier, and search misses
for the same reasons as before.

---

## Brainstorm questions with the agent

**What we search for and with what**

1. Compose 15 real questions that users will ask my system. For each,
   answer: is this search by meaning, search by exact match, a computation, or a traversal of relations?
2. Does my corpus have "untranslatable" tokens: SKUs, error codes, ticket numbers, function
   names, abbreviations? Will vector search find them, and why not?
3. Which embedder am I taking and how strong is it? Work out: if the model is strong, what exactly will adding
   a lexical branch give me, other than noise?
4. If I enable a sparse branch, what exactly does it compute: word frequencies or learned semantics?
   How can this be checked with a single query?

**Fusion**

5. Do my search branches live in one engine or in different systems? What changes in the amount of work
   in each case?
6. What fusion constant is the default in my database? Does it match the classic 60?
7. What happens if my two branches systematically disagree on what they consider relevant?
8. How will I measure that the hybrid is better than a single branch? Describe the experiment: the query set, the metric,
   how many queries are enough.

**Refusal and thresholds**

9. What will my system answer to a question whose answer is not in the corpus at all? Let's check this right
   now: formulate five questions from a foreign subject area.
10. What cutoff threshold is the default in my framework? If it is zero, does that mean
    I have no refusal?
11. What scale do the numbers returned by my search live in: cosine, a sum of frequencies, a fused rank
    score? Which of these can be compared across queries and which cannot?
12. Does my quality evaluation set have **a separate category of questions whose answers
    are known to be absent from the corpus**? If not, add five.

**Query handling**

13. Do I have a chat or one-off questions? If a chat, what will happen to the second turn "and how much does it
    cost" without the context of the first?
14. Which of the seven query handling techniques do I actually need? For each, name the specific failure
    it fixes on **my** data and the latency I am willing to pay.
15. Can I build a cascade instead of a classifier: cheap first, and the expensive step only on empty
    results? What does the escalation condition look like in my case?

**Agent and tools**

16. Is my search called by code or by an agent? If by an agent, how many tools does it have and what
    does each description say about what it does **badly**?
17. Do I have questions whose answer has to be **computed**, not found? What is called then
    instead of search?
18. Do I have data that changes faster than indexing can complete? What should be done with it
    instead of reindexing every five minutes?

---

## Selection criteria, thresholds, tables

### 1. Four ways to search, not two

| Way | What it computes | Strength | Weakness |
|---|---|---|---|
| Full-text (BM25) | a formula over word frequencies and their rarity in the corpus | exact terms, identifiers, robustness to domain change | blind to synonyms and paraphrases |
| Learned sparse | word weights predicted by a neural network | understands word context while remaining a list of words | this is **not** frequency counting, it may fail to find a SKU |
| Dense (vector) | closeness of two vectors | paraphrases, meaning, different formulations of the same thing | blurs identifiers, all the meaning is squeezed into a single vector |
| Tensor (per token) | the sum of maximum similarities per token | quality close to a reranker without a model pass at query time | the index is tens of times larger than a single-vector one |

Warning: **A trap that people regularly stumble on.** In one popular model, the branch that
is called "sparse" in the config is in fact **learned semantics, not frequencies**. The team
enables it, considers lexical search covered, yet SKUs and error codes are still not found,
and the problem is sought in the embedder. It is checked with a single query: search for an exact rare identifier
and see whether it was found.

And the reverse of the commonplace: **lexical search does not lose by default.** On a Russian-language
benchmark it turned out to be the best single method on 4 sets out of 17, and all four with long
documents: the neural model simply hits a 512-token limit and does not see the text beyond it.

### 2. Hybrid: a default with two watersheds

The debate is three-sided, and there are exactly two axes of disagreement.

**The first axis: where the branches live.** Inside one engine a hybrid is assembled with one query, fusion
is done by the database, the cost of adoption is minimal. As soon as the branches live in different systems, fusion
moves into your code, and there it really does cost evenings of work. From the same source comes the most common
production failure of a hybrid: **desynchronization of the two indexes**.

**The second axis matters more: the strength of the first stage.** Two real cases:

| Case | What there was | Result |
|---|---|---|
| A corpus of 46 thousand chunks stuffed with rare proper names in inconsistent spelling, that is, exactly where a hybrid is supposed to win | compared single branches and fusion | recall at depth 50 matched byte for byte, first-place precision fell by 1.8 points, **the hybrid was rejected**. The author's explanation: a strong embedder already finds what an exact match would find, and fusion mixes in lexical noise |
| A corpus with ticket keys of the form `PAY-1187` | added a lexical branch | MRR@10 rose from 0.54 to 0.61 on 200 labeled queries. An identifier has no semantic neighbor in principle |

**The question that settles the debate for you:** which embedder you have and whether the corpus has untranslatable
tokens. Rejecting a hybrid based on your own measurement is a legitimate architecture, not a defeat.
Rejecting a hybrid without a measurement is guessing.

### 3. How results are combined: rank fusion

The classic formula:

```
RRF(d) = Σ over branches   1 / (k + position_of_the_document_in_that_branch)
```

The constant k is 60 in the original 2009 paper and in almost all implementations. Warning: **In one
popular engine it defaults to 2**, and other people's tuned weights are carried over there
with a correction. One more small thing that wastes time: the constant and the weights are **query parameters**,
not names from the formula, and copying the notation literally produces invalid JSON.

**Why ranks are summed, not scores.** For full-text search the score is a sum over words,
it is unbounded above and depends on the corpus and on the analyzer settings. For vector search the score is
a cosine, which lives from minus one to one and depends on the model. A sum of such numbers is meaningless,
and normalization to the range from zero to one helps only if the score distributions match
across queries, and they do not. Rank fusion throws out both scales. The price: the
information in absolute scores is lost. The benefit: **not a single knob is left that could quietly drift.**

**What follows from this in practice.** Agreement of two branches is worth more than a single strong hit.
A breakdown of a real fusion (a measurement on a working corpus, 10.08.2026, two dense branches with different
embedders):

| What was found | Position in branch A | Position in branch B | Fused score | Final place |
|---|---|---|---|---|
| document 1 | 4 | 3 | 0.031498 | **1** |
| document 2 | 7 | 5 | 0.030310 | 2 |
| document 5 | none | **1** | 0.016393 | 7 |

A document that **neither** branch put in the top three beat a document that an entire
branch put first, by exactly a factor of two. A check of the formula in the same run: 1/64 + 1/63 =
0.03149801587301587, the database's answer matched to the seventeenth digit.

A direct consequence for design: **if your branches systematically disagree, rank
fusion will drown both of their truths.**

Fusion methods, in increasing order of required discipline:

| Method | Is calibration needed | What to tune | When to take |
|---|---|---|---|
| By ranks (RRF) | no | the constant k | the default, hard to break |
| By score distribution (DBSF) | self-calibrating | nothing at query time | you need sensitivity to scores without a manual weight |
| Weighted blending | yes: normalization plus a weight | the weight and the choice of normalization | you have calibrated scores and a large evaluation set |
| Trained ranker | yes | a trained model over features | a mature team and a very large set |

### 4. A threshold on the fused score does not work. Not "badly tuned", but does not work

This is the most important section of the document, and it is not about rhetoric but about a property of the formula.

**The maximum fused score is set by the number of branches and the constant.** For two branches that is 2/61 = 0.0328
**always**. The formula has no term that would depend on whether the corpus contains an answer.
The first position always exists, even when garbage sits in it.

A measurement on a working corpus, three queries, identical settings, 10.08.2026:

| Query | Fused score of first place | Share of the maximum |
|---|---|---|
| a topic the corpus knows cold | 0.0328 | 100% |
| a topic the corpus knows only at the edge | 0.0315 | 96% |
| **a topic that is not in the corpus at all** | **0.0301** | **92%** |

The gap between "knows the subject" and "has never heard of it" was **eight percent**.
There is nowhere to put a threshold that separates one from the other.

A caveat on this measurement: both branches of the corpus are dense, that is, this is a fusion of two embedders,
not of vector search with lexical. The fusion mechanics are shown exactly.

**What exactly came back for an out-of-corpus query.** A question was asked about the diving depth of a submarine
against a database about AI products. What came back: the "depth scale" technique for prompts, "Deep Work, one and a half to four
hours of focused work", "DeepSeek requires 1.3 terabytes of video memory", the DeepSWE benchmark
and the Deeper service. Ten results, scores in the working range, latency normal, **not a single
sign of failure**.

**Five reasons why "raise the cutoff" does not save you, and none is fixed by tuning:**

1. **0.7 is a folk default, not a calibrated value.** Changing the model shifts the whole
   distribution; a narrow domain compresses all scores toward 0.9, and 0.7 loses its meaning.
2. **A global threshold is wrong within a single system.** A pinpoint factual question has to land
   at 0.75 and above, while an exploratory question legitimately lives at 0.5.
3. **Similarity is a proxy for relevance, not a measurement of it.** A question about option taxation will match
   by cosine a document about corporate compensation that does not talk about taxes at all.
   A direct check (July 2026): seven real questions and seven impostors from a neighboring domain
   gave **overlapping** score distributions. Warning: the corpus is five documents, the author himself asks
   to re-measure, but the direction matches the measurement above.
4. **Semantic collapse.** As the database grows, there will always be a topically close but wrong fragment,
   and at high density cosine loses its discriminating power: all legal documents
   look alike.
5. **The bridge between chunks.** The answer is distributed over two fragments, neither of which passes the threshold
   on its own. The answer is in the corpus, but cannot be found.

**What happens next if garbage reaches the model.** ICLR 2025, a paper on context sufficiency:
the share of wrong answers for one open model grows from 10.2% without context
to **66.1% with insufficient context**, that is, bad context is worse than none at all. And in the same place:
retrieval **reduces** the willingness to refuse, from 84.1% to 52% for one model and from 100% to 18.6% for another.
Refusal becomes less likely exactly when it is needed most.

**What to do instead of a threshold.** Gate the **finished answer**, not the confidence before the answer: four
gates are covered in artifact 8. A threshold on the fused score does not work; this is **measured** by a separate
category of out-of-corpus questions in the evaluation set, and **noticed in production** by the share of empty results
and the share of answers without a citation.

Warning: **A detail people learn about late:** most frameworks by default return everything
with a score above zero. That is, you will never have a refusal until you have built one, even if
the line about refusal is written in the prompt.

### 5. The trap of different scales: why 0.5 and 0.95 on the same corpus are not about quality

A separate confusion that costs people a week. In one system search returns scores around
0.95, in another around 0.5, the corpus is the same. The conclusion "the first system is better" is wrong.

The number you see depends on **which formula computed it**:

- raw cosine lives from minus one to one and depends on the embedding model;
- a full-text search score is unbounded above and depends on the corpus and the tokenizer;
- a fused rank score lives around one sixtieth and **does not depend at all on
  how good the document is**, only on its position in the branches;
- a reranker score lives in its own scale, for some services a range from zero to four;
- a normalized score depends on what exactly was taken as the minimum and maximum.

**The practical conclusion.** What you can compare with each other is **the order of documents and the gap between
adjacent positions**, not absolute values. Before setting a threshold, answer for yourself
which scale the number lives in. If there is no answer, it is too early to set a threshold.

### 6. A filter in a hybrid is applied to both branches

A short but mandatory point. **The same filter is put into every branch before fusion**,
not on top of the fused result. If you filter only the vector branch, the lexical one will drag other people's
documents into the results: this is a direct hole in access separation.

```json
{ "prefetch": [
    { "using": "dense", "query": [0.014, -0.082, "..."], "limit": 50,
      "filter": { "must": [ {"key":"tenant_id","match":{"value":"acme"}},
                            {"key":"acl_groups","match":{"any":["finance","all"]}},
                            {"key":"is_deleted","match":{"value":false}} ] } },
    { "using": "bm25",  "query": { "indices": [12,907], "values": [1.4,0.9] }, "limit": 50,
      "filter": { "...the same must block, duplicated on purpose..." } } ],
  "query": { "fusion": "rrf" }, "limit": 20 }
```

The owner identifier comes from a verified session, **never from the user's text**. A limit of
50 in the branches against 20 at the top is headroom for fusion. The mechanics of filters themselves and the price of narrow
predicates are covered in artifact 2.

### 7. Which question goes where

| User question | First route | Why |
|---|---|---|
| "How many open high-level risks without a mitigation plan" | SQL, not search | this is an aggregate, the answer is in no chunk, it has to be computed |
| "Show me risk RSK-1042 with status OPEN" | lexical plus a predicate | an exact identifier and a controlled value |
| "Find incidents about supplier access delay" | vector | narrative similarity over meaningful text |
| "Open risks similar to a supplier failure" | hybrid with fusion | a mix of an exact condition and meaning |
| "Which product lines are affected by the supplier strike" | graph | relations through intermediate entities |
| "Stock levels, ticket statuses, balance" | a live call, not an index | changes faster than indexing can complete |

The last row separately: frequently changing structured data **should not be reindexed,
it should be queried live**. Re-embedding the whole set every five minutes is a race in which
the copy goes stale before indexing finishes.

About SQL generation it is worth knowing the accuracy ladder: on clean textbook schemas about 85%, on dirty
real ones 75-82% (a human gets 92.96%), on deliberately ambiguous questions about 33% (a review of
benchmarks, 05.06.2026). And what matters there is not the numbers themselves but that **the model is the same in all rows**:
a bare model gives 33%, a thin wrapper with schema search 44%, a system with an ontology and a clarifying
question on ambiguity **75.2%**. SQL generation accuracy is a property of the system, not of the model.

### 8. Seven query handling techniques

A layer that is absent from typical materials entirely, and yet the most frequent source of latency.

| Technique | What failure it fixes | Cost | Status in production |
|---|---|---|---|
| Dialogue contextualization | pronouns, ellipsis, references to earlier turns | one cheap call behind a lexical gate | takes root, effectively mandatory for chat |
| Rewriting a single query | typos, abbreviations, a gap with the domain vocabulary | 50-150 ms without a model, 500-1500 ms via a model | roughly 50/50; one case is reliable, translation into domain terminology |
| Decomposition into subquestions | several independent points of evidence in one question | N searches instead of one | takes root, but an agentic loop does this adaptively |
| Expansion and fusion of variants | the wording does not match the corpus vocabulary | N searches plus fusion logic | the gain is small, often eaten further down the pipeline |
| Hypothetical document | a short query, weak lexical anchoring | full generation before search, about 30% extra tokens | contested, only behind a flag and by measurement |
| Step back to the general concept | the question is too narrow, misses the concept | one more call and one more search branch | little data, and that is an honest result |
| Intent routing | a single search mechanism for all question types | about 50 ms semantic, 500-800 ms via a model | takes root, with the caveat from section 10 |

**The only technique that takes root without caveats is dialogue contextualization.** In live
dialogues more than 60% of the second and subsequent turns contain unresolved pronouns or implicit
context (an estimate from one production analysis, 21.04.2026, methodology not disclosed). Two details
that distinguish a working implementation from a textbook one: **a cheap lexical gate before the model call**
(a list of cue words, bare pronouns at the start of a phrase, a length threshold) and **a soft fallback
at every step**: any error returns the original question. Plus: what goes into the dialogue history is what
the user said, not the rewritten query.

```
Turn 1 "What is SSO?" → Turn 2 "And which plans is it included in?"
  without rewriting: search looks for "it" and finds nothing
  with rewriting:    "Which pricing plans include Single Sign-On?" → the pricing page

"why did the dashboard break" ↔ the corpus says "panel rendering errors on data source timeout"
  → no reranker will save what search did not fetch
```

### 9. A negative result worth taking as a vaccine

This is the most useful card in the document, because it prevents work rather than adding it.

**What they did.** They took a working system and added query expansion to it: the model comes up with
several reformulations of the original question, each one gets its own search, and the results are fused
by rank. A classic technique, gives a steady gain on isolated benchmarks.

**What they got.** Raw recall (recall, the share of the needed material that search fetched) did
grow. But **Hit@10** (the share of queries where the needed document landed in the top ten of the final results)
**fell from 0.51 to 0.48**. Plus 0.89 seconds of latency. Conditions: a fixed result depth of 10,
chunks of 512 tokens, the same reranker, 115 corporate support queries, fusion
applied after reranking (arXiv 2603.02153, 2026).

**Why it turned out this way.** The overlap between the lists for the original and the rewritten query turned out to be small,
and reranking against the rewritten query **drowns documents relevant to the original**. The gain
in recall was real, but it was entirely eaten further down the pipeline: by the reranker and the cut to ten.

**A ready-made rule that follows from this:**

> A recall gain at an intermediate stage means nothing by itself. What has to be measured is the **end-to-end**
> metric under the **same constraints** as in production: the same result depth, the same reranker,
> the same context truncation. A technique that improves the middle of the pipeline and worsens the end
> is harmful in production.

A second measurement in the same direction, independent: query expansion on a bench of 46 thousand chunks gave
+2.1 points of recall at depth 5 and was **left disabled by default** as marginal
(02.08.2026).

### 10. A cascade versus a classifier before search

Two statements that look the same on a slide but solve **different problems**. They have to be
separated explicitly.

**The first, about choosing a source.** A classifier directs roughly 80% of questions to vector or
hybrid, about 15% to the graph, the rest to agentic scenarios. The gain from routing itself is on the order of
+6%. This works.

**The second, about choosing the depth of processing.** Preliminary routing **fundamentally
cannot decide** whether a particular query needs additional processing, because that only becomes
visible after the index is consulted. Four different machine learning approaches were tried,
none covered more than **2.2%** of the gap to the ideal solution (arXiv 2605.27220, 2026, 20 thousand
"query and scenario" pairs, a corpus of about 240 thousand articles).

**The coverage illusion.** In the same place: on synthetic queries it came out that additional processing
was needed for more than 90% of requests. On **real traffic of the same system** the hybrid itself returns
documents for 72.2% of queries, escalation is needed only for 27.8%. The reason is structural: real
users write short keyword phrases, while benchmarks consist of wordy conversational
questions.

**What works instead of a classifier: a cascade.**

```
query → hybrid search ─┬─ documents found (72.2%) → on down the pipeline
                       └─ zero → query expansion ─┬─ found → on
                                                  └─ zero again → HyDE
```

The result against the "always generate a hypothetical document" scheme: quality +0.140 points
of the composite metric, **latency minus 31.8%**, the model is called on 27.8% of queries instead of 100%.
The order of the stages matters less than the fact of the cascade itself: in their measurements the cascade beat
"always on" in all the orders tested. The escalation condition must be **a cheap check
of the search output, not a prediction from the query text**.

**About the hypothetical document separately, three numbers side by side and without resolving the dispute:**

| Measurement | Result | Conditions |
|---|---|---|
| +50% precision and recall | an illustration of the mechanism | two queries out of three, a tiny sample, 07.07.2026 |
| -9.7 points of recall at depth 5 | technique rejected | measurement bench, 46 thousand chunks, 02.08.2026 |
| 59.6% unchanged, **21.2% worse**, 19.3% better | losses are systematically larger than gains | 722 real queries where the hybrid had already found it, 2026 |

The failure mechanism generalizes and is worth understanding: a hypothetical document **does not supplement the query
but replaces it** and discards the distinguishing terms the user actually gave. The stronger
the embedder and the more precise the original query, the more likely the technique takes away signal. A third position
that was absent from the two-sided dispute: move the generation of hypothetical content
**to indexing** instead of query time (see artifact 2, synthetic questions per chunk).

### 11. Self-RAG, corrective RAG and query planning in plain words

Three names behind which stand three different ideas. They are often presented as competing schools, though they
add up: they are different layers of one defense.

**Corrective RAG.** Between search and generation a **grader** is placed: a lightweight
model call that looks at each found document and answers whether it is relevant to the question
or not. Then three forks: all documents are good, work as usual; all are bad, throw
them out and go search another way; some are good, supplement them from another source. The key property:
**it corrects before generation**, that is, the main model may not be called at all if there is nothing to fix.
It is placed on top of ordinary RAG without rework, and is in the templates of popular frameworks.
The cost of grading is 200-400 tokens per document.

**Self-RAG.** The model, as it writes the answer, marks itself up: whether to go to search
at all, whether the found fragment is relevant, whether the sentence just written is supported
by the source, whether the answer is useful. In the original paper the model was specially
fine-tuned for this. In practice this is more often reproduced with separate model calls for each check.
The key property: **it corrects during generation**.

**Query planning.** Before searching for anything, the model lays the question out
as a plan: which subquestions need to be closed, in what order, with which tool. Useful on compound
questions where the answer is assembled from several independent points of evidence.

**What to do with this in practice.** This is **an escalation, not an upgrade**. Four typical failures of first
deployments: infinite loops (cured by a hard iteration ceiling, usually 5-6); graders
that never reject anything (checked by the rejection rate: near zero means the grader
does not work); context overflow with accumulated results; a latency spiral where each
iteration multiplies both the time and the bill.

The order of adoption: first the document grader (the cheapest and the most useful), then the choice of processing
depth, and only then self-checking of generation.

### 12. Three agent tools with a shared filter

If search is called by an agent, not by code, the layout of tools is a separate decision. A team
that tried all three variants (one smart tool, three separate ones, one tool
with a rich filter object) stayed with **three tools with a shared filter object**:
`filter_documents` (pure selection by fields), `keyword_search`, `semantic_search`. The argument against
"one smart search" is practical: the model cannot reason about **why** a result
came back, does not recover after a bad result, and tends to repeat the same query
verbatim.

Details, each of which merits a decision of its own:

- the agent sees **only snippets**, the full document body is fetched by a separate call with a separate
  price: this makes it possible to put many results into one tool response;
- semantic search must have a minimum score parameter, otherwise the agent cannot ask for
  "close **or nothing**";
- the filter is pushed **into** the search query, not applied to the results;
- the tool description states what it does **badly**, and what it costs. "Good
  for paraphrases, bad on exact identifiers" is more useful than "performs semantic
  search". Stating the price makes the model narrow with the cheap one first;
- the agent is **not given** a fused hybrid endpoint right away: it hides the debugging signal "lexical found
  the document and vector did not". It is added as a fourth when the latency budget stops tolerating two
  calls.

A ready-made trace worth reproducing for yourself:

```
User: find the email about the third quarter forecast
agent → filter_documents { author: [...], tags: ["email"] }        → 23 hits
agent → semantic_search  { "Q3 forecast", same filter,
                           limit: 5, min_score: 0.7 }              → 2 (0.84, 0.71)
agent → get_document     { document_id: "doc_a1b2" }               → full body
"forecast" would not have been found by keywords: the email was titled "Q3 revenue model"
```

---

## Common mistakes

| How not to | What it leads to | How to |
|---|---|---|
| Enable "sparse" and consider lexical search covered | In some models this branch is semantic, not frequency-based. SKUs and error codes are not found, and the team looks for the problem in the embedder | Check with a single query what your sparse branch computes. If necessary, add a third candidate, plain BM25 |
| Enable a hybrid by default and not measure | The two indexes drift apart (the most common production failure of a hybrid), and there may be no gain at all if the embedder is strong | Compare single branches and fusion on your own set, write the number into the decision log |
| Sum branch scores instead of ranks | One scale is unbounded above and depends on the corpus, the other lives from minus one to one. The sum is meaningless, the weights in it mean nothing | Rank fusion as the default; weighted only when there are calibrated scores and a large evaluation set |
| Set a single threshold on the fused score and a line "if you don't know, refuse" in the prompt | It works on a small database, then stops. An out-of-corpus query gets 92% of the maximum, and the instruction loses to the context | A cutoff **before** the model call by the reranker score plus a code check of the finished answer (artifacts 7 and 8) |
| Compare absolute score values between systems or between queries | 0.95 in one system and 0.5 in another are different formulas, not different quality | Compare the order of documents and the gap between adjacent positions. First find out which scale the number lives in |
| Hang a filter only on the vector branch | The lexical branch will drag other people's documents into the fused results | The same filter in every branch before fusion, the value is taken from a verified session |
| Add a query-side trick because it is written about favorably | Latency grows, failure analysis gets murkier, and the end-to-end metric may **fall**, as in the query expansion case | Name the specific failure the trick fixes and the latency you are willing to pay. Measure the end-to-end metric under production constraints |
| Enable a hypothetical document on every query | On real queries where search had already found it, in 21.2% of cases the result got worse, and losses are larger than gains | Behind a flag, by measurement, only on short queries with a real vocabulary gap. Or move generation to indexing |
| Put a classifier before search to decide whether a query needs heavy processing | This fundamentally does not work: the need is visible only after the index is consulted | A cascade: cheap first, escalation only on empty results |
| Assume that green metrics mean the system is fine | The metrics are green precisely on the class of queries where the system lies, if there are no out-of-corpus questions in the set | A separate golden set category: questions whose answers are known to be absent from the corpus |

---

## Layer readiness checklist

- [ ] A list of question types is drawn up, and for each it is written down which mechanism serves it.
- [ ] It is verified with a single query that the sparse branch (if there is one) finds exact
      identifiers.
- [ ] The decision "hybrid or a single branch" is backed by your own measurement, the number is written down.
- [ ] The fusion constant that is actually set in your database is known.
- [ ] The filter is applied to every branch before fusion, and this is verified on a live query.
- [ ] The permissions filter value is taken from a verified session, not from the user's text.
- [ ] It is known which scale the number returned by your search lives in.
- [ ] The framework's default threshold is checked: if it is zero, refusal is built separately.
- [ ] The quality evaluation set has a separate category of out-of-corpus questions.
- [ ] Production metrics are set: the share of empty results and the share of answers without a citation, with an alert threshold.
- [ ] For each enabled query handling technique the failure it fixes is named, and the end-to-end
      metric is measured under production constraints.
- [ ] If there is a chat, turn contextualization is done and it has a soft fallback to the original
      question.
- [ ] If there is an agent, each tool's description says what it does badly, and the
      minimum cutoff score is specified.
- [ ] If there is an agentic loop, it has an iteration ceiling and the cost of each one is logged.
- [ ] A decision log is set up in the format "implemented, measured, kept or rejected, wrote down the number".

---

## What to read

| What | Where | Why |
|---|---|---|
| Sufficient Context, ICLR 2025 | arXiv 2411.06037 | Shares of fabrications and refusals, and why search reduces the willingness to refuse. The methodology is disclosed, the labeler was checked on 115 examples |
| The coverage illusion and the cascade | arXiv 2605.27220 | 20 thousand "query and scenario" pairs, 72.2% versus 27.8%, and why a classifier before search does not solve the problem |
| Fusion of rewritten queries in production | arXiv 2603.02153 | A negative result with full measurement conditions: Hit@10 0.51 → 0.48 |
| A comparison of four search paradigms | arXiv 2508.01405 | All 11 combinations, and the conclusion about tensor search as reranking, not as a branch |
| The original paper on rank fusion | Cormack, Clarke, Buettcher, SIGIR 2009 | Where the formula and the constant 60 came from |
| Corrective RAG | arXiv 2401.15884 | A grader between search and generation, three routing forks |
| Self-RAG | arXiv 2310.11511 | Self-checking during generation and reflection tokens |
| A survey of agentic search | arXiv 2501.09136 | Five patterns, cost and latency multipliers for each |
| ACORN and the pgvector 0.8.0 release notes | arXiv 2403.04871, https://github.com/pgvector/pgvector/releases | Two strategies of filtered search |
| A survey of SQL generation benchmarks | public survey, 05.06.2026 | The ladder 85% → 75-82% → 33% and the climb 33% → 44% → 75.2% on one model |
| Qdrant documentation: hybrid queries | https://qdrant.tech/documentation/concepts/hybrid-queries/ | Database-side fusion, branch weights, the default constant |

**What is missing, and this is honest.** A live example of "what lexical found that vector did not" is absent from the measurements
above: both branches of that corpus were dense. For the step back to the general concept, there were no production
measurements for 2026 at all. Result deduplication (five nearly identical chunks instead of
five different ones) is not analyzed quantitatively in any public source.
