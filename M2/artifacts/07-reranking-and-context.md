# Artifact 7. Reranker and context assembly: the last mile

## What this is and how to use it

This is a helper document for two neighboring decisions that are made **after** search has
found something and **before** the model starts writing the answer:

1. **Reranker:** whether you need a second, more precise pass over the candidates that were found.
2. **Context assembly:** how many chunks to put into the prompt, in what order, and what to do
   with them before that.

How to use it: attach the file to your agent and work through both decisions **for your course
project**. The main thing you should take away from here is not "installed a reranker" but
a **number**: what recall your search has at depth 50. Everything else depends on it.

Starter prompt:

```
Read the attached document about the reranker and context assembly. My project: <description:
what the corpus is, what search is already built, what latency budget I have per answer,
whether I have a labeled set of questions>. Walk me through the questions from the section
"Brainstorming questions". Start with diagnostics: help me plan a recall measurement for my
search before I add anything. At the end, put together: (1) a reranker decision with its
rationale, (2) context assembly parameters, (3) what I will measure after rollout.
```

**What is not in this document.** It does not cover search itself or branch fusion (artifact 6),
the prompt and citation rules (artifact 8), or chunking (artifact 3).

**Definitions.** *Recall@50* (recall at depth 50) is the share of the needed documents that made
it into the first 50 search results. *nDCG@10* is the quality of the ordering in the top ten: not
only whether the needed document was found, but whether it sits at the top. *p95* and *p99* are
the latency that 95% and 99% of requests fit within, that is, the tail, not the average.

---

## Map of the set: this file is one of twelve

The module's artifacts walk through the pipeline layer by layer, and the decisions in them are
coupled: the upper bound on chunk size runs into the embedder's window, the metadata schema
determines what you can filter on at search time at all, and cost is the sum of decisions across
all layers at once. That is why the files sit in one folder and are meant to work together: this
one is read in full, the others are opened as needed.

> **Instruction to the agent.** You are reading one file out of twelve; the others are right
> next to it, in the same folder. As soon as the conversation goes beyond the boundary of this
> layer, open the relevant file and read the corresponding section before giving advice. Do not
> retell the neighboring layer from memory: the artifacts contain thresholds, numbers with their
> measurement conditions, and failure modes that are not in general knowledge. Read on demand,
> not everything at once: this file first, then whatever turns out to be needed during the
> conversation. If the needed file is not next to you, say directly which one is needed and ask
> for it instead of guessing. When a decision in one layer breaks a decision in a neighboring
> one, say so immediately, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at intake |
| [`02-metadata.md`](02-metadata.md) | Metadata | deciding which fields go next to a chunk: source, freshness, permissions, version, and what you will then filter by |
| [`03-chunking.md`](03-chunking.md) | Chunking | choosing size, boundaries and overlap; questions about tables, code and structural splitting |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | choosing a model for the language and domain, dimensionality, local or via API; the cost of switching models |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, branch fusion, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanics, source citation, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletion, record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reducing cost |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End to end | checking what has been built: errors where the pipeline works and the metrics are green but the system lies; a checklist of 24 checks |

**Closest links of this layer.** The input is the output of
[`06-search-and-fusion.md`](06-search-and-fusion.md), the output is what ends up in the prompt
([`08-generation.md`](08-generation.md)). How many pieces fit and how large they are was decided
at chunking ([`03-chunking.md`](03-chunking.md)). A reranker costs money and latency; both
budgets are in [`11-economics.md`](11-economics.md). The rule that is especially easy to break
here: similarity is a signal for finding candidates, not a ready decision about whether this is
the right document; §6.3 in [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

---

## Decision map of the layer

```
   search returned 50 candidates
              │
              ▼
   ┌────────────────────────────────────┐
   │ QUESTION 1: do you need a reranker?│
   │ The answer depends on ONE number:  │
   │ your search's recall at depth 50   │
   └───────┬────────────────┬───────────┘
           │ low            │ high
           ▼                ▼
   fix SEARCH        a reranker makes sense
   (a reranker       │
    will not help:   ▼
    it cannot raise  ┌──────────────────────────┐
    what is not      │ QUESTION 2: how many candidates
    there)           │ go in? This determines p99
                     │ more than the model choice │
                     └──────────┬───────────────┘
                                ▼
   ┌─────────────────────────────────────────────────┐
   │ CONTEXT ASSEMBLY                                │
   │ how many chunks · in what order ·               │
   │ deduplication · compression · what to expand to │
   │ a whole document                                │
   └─────────────────────────────────────────────────┘
```

**The formulation that holds the whole layer together: the reranker is the last mile, not the
foundation.** It reorders what it was given. If the needed document is not in the candidate
list, no reranker will add it there.

---

## Brainstorming questions with the agent

**Diagnostics before rollout**

1. Do I have a labeled set of questions with known correct documents? If not, help me build
   a minimal one: how many questions are enough and where to get them.
2. What recall does my search have at depth 50? Plan the measurement: what exactly we count,
   and on what.
3. What recall do I have at depth 3, and what ordering quality in the top ten? What do these
   two numbers together say about whether I need a reranker?
4. Analyze my case: is my problem that the needed document is **not found**, or that it is
   **found but ranked low**? How do I tell one from the other from the logs?

**Cost and risks**

5. What is my latency budget for the whole answer? How much of it am I willing to give to the
   reranker?
6. How many candidates do I plan to give the reranker, and what does that mean for latency at
   peak load, not on average?
7. What will happen to my system if the reranker does not respond within the allotted time?
   Describe three behaviors and pick one, explaining why.
8. If I take open weights, what does their license say about commercial use on my own servers?

**Context assembly**

9. How many chunks do I plan to give the model, and what is that number based on?
10. Do I filter out junk before putting chunks into the prompt? How exactly? The answer
    determines whether I can use many chunks or not.
11. How long is my context in tokens? What will happen to a fact that ends up in the middle
    of it?
12. Do I have nearly identical chunks in the results? How do I collapse them, and by what
    attribute?
13. What is cheaper in my case: passing twenty chunks verbatim, or compressing them into
    a summary and passing that?
14. Do I have documents that make sense to insert whole, using search only to **identify the
    right document**? What is their typical length?

**Verification**

15. How will I know that the reranker made things worse? Which three numbers do I look at before
    and after?
16. What will I write in the decision log after this review: what I rolled out, what I measured,
    what I rejected?

---

## The reranker in plain words

### What it is

When vector search looks, it compares **two precomputed vectors**: the vector of your question
and the vector of a document that has been sitting in the database since load time. The model
that computes these vectors sees the question and the document **separately, at different
times**. It has never seen them side by side. It is like picking a candidate for a job by reading
only the résumé, without matching it line by line against the job description. But it is fast:
millions of documents are processed in milliseconds, because all the heavy work was done in
advance.

The reranker is built differently. It takes **the whole pair**: your question and one specific
document, puts them into one model together, and answers the question "does this text answer
this question". The model sees both sides at once and can match them by words and by meaning.
It is like an interview instead of reading a résumé: more accurate, but one candidate at a time
and not fast.

That is where the whole economics comes from. The first model is trained to **search quickly**
among millions. The second is trained to **judge relevance** among dozens. These are different
tasks, and one does not replace the other.

The working scheme is therefore two-stage: search pulls 50 candidates out of a million, the
reranker picks the best 5 out of those 50. The first stage is responsible for making sure the
needed document gets into the 50 at all. The second is responsible for making sure it ends up
at the top.

### When you need a reranker

In exactly one case: **the first stage retrieves the needed document but ranks it badly**. That
is, the document is in the candidate list but sits at 23rd place, and it does not reach the
model's context because you take only five.

In addition, a reranker is a convenient place for **soft preferences** that cannot be made hard
filters: boost fresher documents, boost the canonical source over a derived one. A hard filter
by date will hide an effective document signed a little before the cutoff; a soft boost hides
nothing.

And third: **the reranker's score is a much more honest signal for a cutoff** than cosine.
Some search services return it as a separate field on a scale from zero to four, and a threshold
of about 1.5 works as a starting point. The reason is simple: a cross-encoder is trained to
judge relevance, while an ordinary embedder is trained to search quickly.

### When a reranker is harmful

**First: when the first stage does not retrieve the needed document.** The reranker's ceiling is
firmly set by the first stage's recall. Spend on search, not on reordering an empty list. Money
and latency will go out in full anyway.

**Second: when you narrow the selection.** A reranker is usually deployed together with
a cutoff: there were 50, now there are 5. Narrowing from 50 to 5 drops recall from 0.94 to 0.78.
If your question requires assembling the answer from several documents, this is a direct loss:
you have just thrown away part of the evidence.

**Third: when the embedder is already strong.** The reranker's effect is inversely proportional
to the strength of the first model. In an independent measurement on a Russian legal corpus
(02.05.2026), a reranker on top of a weak embedder gave plus 9–12 points of ordering quality, on
top of a strong one the result stayed within the margin of error, and **one popular reranker
made the result significantly worse**.

**Fourth: under a load spike.** Cross-encoders fundamentally cannot be batched across requests:
each pair has to be run separately. At low load the batch window dominates, at peak load requests
queue up behind the previous batch, and the latency curve goes vertical. **What breaks is not
the average or the median but the upper tail under a spike**, that is, exactly the cohort of
requests where the user is least patient.

### A bad case

A team built search, and the answer quality is unsatisfactory. They read that a reranker gives
+5…+15 points and install it. Latency grows, the bill grows, quality does not change.

A post-mortem shows that the recall of their search at depth 50 was about 0.6: **in four cases
out of ten the needed document was not among the candidates at all**. The reranker diligently
ordered junk. The money went to a second service in operations, while what needed fixing was
chunking and metadata.

An extreme version of the same on a public benchmark: a reranker on top of lexical search on
a scientific corpus gave **+0.009 points of ordering quality with latency growing roughly 2000
times** (from 0.11 milliseconds to 225), and the gain **did not leave the confidence interval**.
That is, formally it is not an improvement at all. 16.07.2026, 5183 documents, 300 queries, the
interval was computed by bootstrap with 1000 resamples. The condition is visible in the same
run: at depth 5 recall is 0.72, at 10 it is 0.77, at 20 it is 0.82, and the gain from the
reranker appears only at 20. While recall is low, there is nothing to rank.

### A good case

Another team, a support knowledge base of 80 thousand chunks. Before adding anything, they
measured the recall of their hybrid search at depth 50: the needed document made it into the
candidates almost always. At the same time, ordering quality in the top ten was average, meaning
the right answer regularly stood at position 15 while five went into the context.

Diagnosis: **we retrieve, but rank badly**. This is exactly the case the reranker was made for.
After rollout, ordering quality grew substantially, within a controlled latency budget. The
typical size of the gain under such conditions according to benchmark summaries is **+5…+15
points of nDCG@10**: on a classic set lexical search gives 41.7, ordinary vector search 51.0,
and adding a cross-encoder 56.5.

The difference between the bad and the good case is not in the reranker model and not in its
size. The difference is that in the second case they **measured first**.

### Diagnostics: two numbers, not one

A working pair of thresholds that reproduces across several independent practitioners:

- **recall at depth 50 below 0.85** means search needs fixing, not a reranker installed;
- **recall at depth 3 above 0.9** means the reranker is redundant, the needed document is
  already at the top.

Note: this is a practical heuristic. The specific numbers have no academic primary source, it was
taken on English-language corpora, and you have to calibrate it on your own data.

Note: **an important correction: recall at a large depth is blind to exactly what a reranker is
installed for.** Three different result lists can give identical recall at depth 5, equal to
one, and still have ordering quality from 0.53 to 1.0. That is why the diagnostics are
**two-number**: recall at depth 50 answers the question "is there anything to rank", and ordering
quality in the top ten answers the question "does it need ranking".

After rollout you have to measure a triangle: **ordering quality, recall delta, p95 and p99
latency**. Ordering quality alone will hide both the loss of recall from narrowing and a drifted
latency tail.

### A dispute that is not resolved, and that is honest

| The "needed" side | The "overrated" side |
|---|---|
| Typical gain of +5…+15 points of ordering quality; the two-stage scheme is named the most justified way to raise accuracy | The ceiling is firmly set by the first stage's recall; on a public benchmark the gain did not leave the confidence interval while latency grew 2000 times |
| In closed enterprise-search competitions it makes a noticeable difference | An analysis of one production corpus: **in 9 cases out of 100 the reranker puts a worse chunk in first place than a plain cosine baseline** |

The sides measured **different things**: some measured the gain where the first stage already
retrieves the needed document, others measured behavior with a weak first stage and under
a latency budget. The third axis: the effect is inversely proportional to the embedder's
strength. The dispute is not about qualifications, it is about conditions.

### Engineering details that matter more than the model choice

**Depth matters more than the model.** A small popular model spends about 12 milliseconds per
document and about 740 milliseconds per hundred on a GPU. That is, **the number of candidates
determines your p99 more than the model choice**. The model and the depth are chosen together,
not one after the other.

**Model size does not determine quality.** Counterintuitive, but it reproduces: a 149-million
parameter model gives the same top-1 hit rate as a 1.2-billion one, and a 4-billion one loses
to both. Choose by measurement on your own corpus, not by parameter count.

**A practical input limit is about 50 chunks**; beyond that you run into the cross-encoder's
window.

**A cascade of two rerankers** as a way not to overpay: search gives about 1000 candidates,
a light model selects 200, a heavy cross-encoder produces the final 50.

**The license is a selection criterion, not a formality.** Some open weights come under licenses
that **prohibit commercial use on your own servers**. Check the specific model's card before
building it into the architecture, not after.

**What to do if the reranker did not finish in time.** Three fallback branches, and most teams
have not measured any of them:

1. Return the unsorted top. It seems safe, but there is a catch: when a reranker appears, the
   first stage is usually retuned to retrieve **more** candidates and the threshold is loosened,
   so the fallback returns a looser set than there was **before** the reranker was introduced.
2. Return the partially reranked list. Worse: the order stops being monotonic, and the model
   weighs position, and position has become noise.
3. Return an error. Honest, but the user is left without an answer.

The choice is fixed as a decision, not left as a library default.

---

## Context assembly

### How many chunks to give the model: a dispute with three positions

The dispute is not resolved, and that is honest. Three valid positions with different
conditions:

| Position | Number | Condition under which it holds |
|---|---|---|
| Quality measurement from one vendor | top-20 is better than top-10 and top-5 | **provided that junk is filtered out by a reranker** |
| Practical handbook | 4–6 chunks of 300–512 tokens each | from 10 and up, hallucinations grow because of contradictions inside the context |
| Security recommendations | 3–5 chunks, 2000–4000 tokens | a long block pushes the system instruction out of the zone of effective attention |

**The condition "provided that junk is filtered out" is the point of divergence, not
a footnote.** Whoever filters can use twenty. Whoever does not filter will be hurt by twenty.
And most importantly: **this is a product decision, not a search engineer's decision**; it is
recorded as a decision with a rationale, not inherited from a tutorial.

### The context cliff: where exactly it breaks

A practical threshold: **about 2500 tokens of context**. Above it, reasoning quality drops
sharply, and facts from the **middle** of the context are lost with a probability of **up to
40%**. This is not about the model's window limit, it is about its attention.

Hence two techniques:

**Put the best-scoring chunks at the edges.** Not top to bottom in descending order, but first
and last:

```
In descending score order:  S1 S2 S3 S4 S5 S6      ← S4 and S5 fall into the failure zone
At the edges:               S1 S3 S5 S6 S4 S2      ← the best at the first and last position
```

**Change the order of the model's work, and it is free.** First the model lists all chunks with
a "relevant" or "not relevant" mark, and **only then** writes the answer. Plus 5–10% accuracy on
the very same search, without a single extra call.

### Claimed window length versus the length at which the model holds quality

A term that appears in benchmarks: *claimed vs effective length*. In plain terms, it is the
difference between **the window length the vendor wrote in the specification** and **the length
at which the model still holds quality**. A claimed 128 thousand tokens does not mean that at 128
thousand the model works the same as at eight.

Two systematic tools used to measure this:

- **RULER** builds a "claimed versus actually works" table across models and states directly
  that, of the models with a claimed window of 32 thousand tokens and above, only about half hold
  quality at those 32 thousand;
- **HELMET** (59 models) adds an important caveat: **there is no single effective length**, it
  differs by task. Task categories correlate only weakly with each other, and the authors advise
  taking the category with document retrieval as the cheapest predictive indicator for RAG.

A practical conclusion for context assembly: **do not stuff the window because it is large**. You
have to test on your own task, and keep the 2500-token guideline in mind as a boundary beyond
which the risk begins, not as a hard rule.

### Deduplicating the results

A typical, rarely discussed breakage: **five nearly identical chunks go into the context instead
of five different ones**. The causes vary: overlap of neighboring chunks, the same text that got
into the corpus from two sources, synthetic questions per chunk (each chunk is indexed with
a dozen of its own questions and takes the top by itself).

It is cured by collapsing by content hash before assembling the prompt, and at the search stage
by pulling several times more candidates and collapsing them by source document.

### Context compression and inserting whole documents

Two alternatives to "twenty chunks verbatim":

**Compression.** With a separate cheap call, make from the found chunks a summary of only the
relevant passages and pass that. It saves input but adds a call and one more place where a fact
can be lost.

**Whole documents.** The third position, which does not exist in the two-sided dispute about the
number of chunks: search for chunks **to identify the needed documents**, and put those documents
into the context **whole**, as long as they fit in roughly 10 thousand characters. A related rule
from the same place, and an important one: **full text or skip the document**. A half-inserted
document is worse than an absent one, because when the needed sentence is missing, the model does
not refuse, it fills in the gap.

### Small things where quality is lost

- **Rerank with the original query**, not with expanded variants, if the variants aim at
  different entities.
- The order of chunks affects not only attention but also the **prompt cache**: the static part
  must come above the dynamic one. Details are in artifact 8.
- Trimming the context with a sliding window (dropping the beginning when you hit the limit)
  collapses the cache hit rate: in one measurement the hit share fell from ~85% to 45%. Tokens
  from the beginning of the context must not be deleted.

---

## Common mistakes

| What not to do | What it leads to | What to do |
|---|---|---|
| Install a reranker because "everyone does" | If search recall is low, the reranker diligently orders junk. Latency and the bill grow, quality does not change | First measure your search's recall at depth 50. Below 0.85 means fix search |
| Look at one metric after rollout | Ordering quality grew, but recall dropped because of narrowing from 50 to 5, and multi-source questions got worse | Measure the triangle: ordering quality, recall delta, p95 and p99 latency |
| Measure only recall at a large depth | It is blind to exactly what a reranker is installed for: three result lists with the same recall give ordering quality from 0.53 to 1.0 | Diagnostics are two-number: recall at depth 50 plus ordering quality in the top ten |
| Choose a reranker by parameter count | A 149-million model gives the same hit rate as a 1.2-billion one, and a 4-billion one loses to both | Measure on your own corpus. And check the license: some open weights prohibit commercial self-hosting |
| Test latency at average load | Cross-encoders are not batched across requests: the upper tail breaks under a spike, not the median | A load test with a peak, look at p99, not the average |
| Not decide in advance what to do on a reranker timeout | The library default returns a looser set than there was before the reranker, and nobody measured that | Choose the fallback branch deliberately and measure its quality separately |
| Raise the number of chunks "to be sure it's included" | Contradictions inside the context, growing hallucinations, the bill for input, and five nearly identical chunks instead of five different ones | Rerank, deduplicate by content hash, 4–6 chunks, the best at the edges |
| Put chunks into the context in descending score order | Everything after the first lands in the middle, where facts are lost with a probability of up to 40% | The best-scoring at the first and last position |
| Assume the model's claimed window is its working window | 128 thousand tokens claimed, quality holds noticeably earlier, and a model has no single effective length at all | Test on your own task, keep the 2500-token guideline as a risk boundary |
| Insert half a document because it did not fit | When the needed sentence is missing, the model does not refuse, it fills in the gap | Full text or skip the whole document |

---

## Layer readiness checklist

- [ ] Search recall at depth 50 was measured **before** rolling out the reranker, the number is
      recorded.
- [ ] Ordering quality in the top ten was measured, the number is recorded.
- [ ] The decision "install or not install a reranker" is justified by these two numbers, not by
      a general consideration.
- [ ] If a reranker is installed, all three quantities were measured after: ordering quality,
      recall delta, p95 and p99 latency.
- [ ] It was checked that narrowing the selection did not collapse recall on questions requiring
      several sources.
- [ ] A load test with a peak was run, not only with average load.
- [ ] The behavior branch on reranker timeout was chosen and measured.
- [ ] The reranker model's license for commercial use on your own servers was checked.
- [ ] The number of chunks in the context was chosen deliberately and recorded together with the
      condition (whether junk is filtered out).
- [ ] The context length in tokens was measured, not estimated by eye.
- [ ] The best-scoring chunks are placed at the edges of the context.
- [ ] The order-change technique is enabled: relevance labeling first, then the answer.
- [ ] Deduplication of the results by content hash is set up.
- [ ] It was decided whether documents are inserted whole, and the "full text or skip" rule was
      fixed.
- [ ] Everything is entered in the decision log: what I rolled out, what I measured, what I kept
      or rejected, which number.

---

## What to read

| What | Where | Why |
|---|---|---|
| Open retrieval benchmark, a reranker analysis on a scientific corpus, 16.07.2026 | public run, 5183 documents, 300 queries | A sobering result: +0.009 ordering quality with latency growing 2000 times, the confidence interval is computed |
| A comparison of four search paradigms | arXiv 2508.01405 | Tensor search pays off more as reranking on top of candidates than as a separate branch: quality 0.722 versus 0.668 with 86% peak memory savings |
| RULER | arXiv 2404.06654 | The "claimed window length versus actually working" table, the conclusion about half of the models at 32 thousand tokens |
| HELMET | arXiv 2410.02694 | 59 models, the conclusion "there is no single effective length", the document-retrieval category as a predictive indicator for RAG |
| Lost in the Middle | arXiv 2307.03172 | The canonical paper on the loss of facts from the middle of the context |
| Independent measurement on a Russian legal corpus, 02.05.2026 | public analysis, 858 documents, 30 questions | A reranker on a weak embedder plus 9–12 points, on a strong one within the margin of error, one popular reranker made things significantly worse |
| A survey of reranking models with licenses | model cards on Hugging Face | The only way to find out whether commercial self-hosting of specific weights is allowed |
| Cloud search services' documentation on the semantic ranking score | your stack vendor's documentation | An example of a scale from zero to four and of a cutoff threshold as a starting point |

**What is missing, and that is honest.** There are no public quality thresholds for
Russian-language corpora. The recall thresholds of 0.85 and 0.9 are a reproducible practitioner
heuristic without an academic primary source. Nobody has published comparative measurements of
timeout fallback branches: most teams have not measured them.
