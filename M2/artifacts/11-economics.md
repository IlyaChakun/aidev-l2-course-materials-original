# RAG economics: a calculation template, thresholds, what to agree on

> Module 2 artifact. **All prices were checked against vendor price pages on 10.08.2026.** The date
> here is part of the content: prices move faster than guides get updated, and any calculation
> without a date is useless.

## What this is and how to use it

This is a **calculation template, not a price list and not a benchmark.** The numbers in the example
are there only to show the formula and the order of magnitude. Your task is not to memorize them but
to substitute your own and get your own estimate.

RAG economics is not settled at the cost-control stage but **in the first week of the project**.
Three questions (how often the data changes, what freshness is required, how many queries there are
per ingestion) determine which layers of infrastructure will appear in the project at all. Each
answer adds or removes a **layer**, not a percentage on the price.

The order of work. Connect this file to your agent, give it the parameters of your corpus and load,
and ask it to recompute the table from the "Calculation template" section line by line, showing the
formulas. Then go through the thresholds: they answer the questions "do we need a vector database at
all", "when to move off a managed service", "does a reranker pay off". The output should be a file in
the project repository with your estimate, the date of the calculation and a list of assumptions.

Warning: **One caution before you begin.** On a typical corpus, the choice of generation model changes the
total bill by a factor of 3.5, while the argument about which vector database to take is an argument
about ten percent of an amount that itself is about seven percent of the real total cost of
ownership. **Do not start optimizing with the database.**

---

## Map of the set: this file is one of twelve

The module's artifacts take the pipeline apart layer by layer, and the decisions in them are
coupled: the upper bound of a chunk runs into the embedder's window, the metadata schema determines
what you can filter by at search time at all, and cost is the sum of decisions from every layer at
once. That is why the files live in one folder and are meant to be used together: this one is read
in full, the others are opened as needed.

> **Instruction to the agent.** You are reading one file of twelve; the others lie next to it, in
> the same folder. As soon as the conversation goes beyond the boundary of this layer, open the
> relevant file and read the corresponding section before advising. Do not retell the neighboring
> layer from memory: the artifacts contain thresholds, figures with measurement conditions and
> failure modes that general knowledge does not. Read on demand, not everything at once: this file
> first, then whatever the conversation needs. If the file you need is not there, say plainly which
> one is needed and ask for it instead of guessing. When a decision in one layer breaks a decision
> in a neighboring one, say so right away, without waiting to be asked.

| File | Layer | Open when |
|---|---|---|
| [`01-data-preparation.md`](01-data-preparation.md) | Data | the input is not ready text: PDF, scan, HTML, wiki, tracker; you need a parser, OCR, normalization, deduplication at ingestion |
| [`02-metadata.md`](02-metadata.md) | Metadata | you are deciding which fields go next to a chunk: source, freshness, permissions, version, and what to filter by afterwards |
| [`03-chunking.md`](03-chunking.md) | Chunking | you are choosing size, boundaries and overlap; questions about tables, code and structural splitting |
| [`04-embeddings.md`](04-embeddings.md) | Embeddings | you are choosing a model for the language and domain, dimensionality, local or via API; the cost of switching models |
| [`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md) | Database and indexes | choosing a database, HNSW settings, quantization, memory, tenant isolation, backups |
| [`06-search-and-fusion.md`](06-search-and-fusion.md) | Search and fusion | dense and keyword search, fusing the branches, filters, query processing |
| [`07-reranking-and-context.md`](07-reranking-and-context.md) | Reranking and context | candidates are found but the order is bad; assembling what actually goes to the model |
| [`08-generation.md`](08-generation.md) | Generation | the answer prompt, the refusal mechanism, source citation, gates on the finished answer |
| [`09-corpus-lifecycle.md`](09-corpus-lifecycle.md) | Lifecycle | updates and deletion, record manager, statuses, index versions, embedder migration |
| [`10-security.md`](10-security.md) | Security | search as an authorization decision: permissions, isolation, corpus poisoning, personal data |
| [`11-economics.md`](11-economics.md) | Economics | what it costs: indexing versus traffic, "below X do this, above X do that" thresholds, levers for reduction |
| [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md) | End to end | checking what has been built: errors where the pipeline runs and the metrics are green but the system lies; a checklist of 24 checks |

**Closest connections of this layer.** The number of vectors is set by the splitting
([`03-chunking.md`](03-chunking.md)) and the model's dimensionality
([`04-embeddings.md`](04-embeddings.md)), memory and disk by the index settings and quantization
([`05-vector-db-and-indexes.md`](05-vector-db-and-indexes.md)). The cost of each query is made up of
search ([`06-search-and-fusion.md`](06-search-and-fusion.md)), the reranker
([`07-reranking-and-context.md`](07-reranking-and-context.md)) and answer tokens
([`08-generation.md`](08-generation.md)). The main lever on a live corpus is not paying for what
has not changed: incremental instead of a full reload
([`09-corpus-lifecycle.md`](09-corpus-lifecycle.md)) and the two-hash mechanism, §4.2 in
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

---

## Map of the layer's decisions

```
1. THREE QUESTIONS OF WEEK ONE   change frequency · freshness · queries per ingestion
      ↓ each answer adds or removes a layer of infrastructure
2. NATURE OF THE COSTS           ingestion once · storage forever · query every time
      ↓
3. FOUR EXPLICIT ITEMS           embeddings → database → reranker → generation
   FIVE FORGOTTEN ONES           parsing · egress traffic · index rebuild ·
                                 index overhead · minimum plan
      ↓
4. CALCULATION TEMPLATE          a formula for every line
      ↓
5. THRESHOLDS                    CAG vs RAG · managed vs self-hosted · reranker
      ↓
6. REDUCTION LEVERS              in descending order of effect, not by habit
      ↓
7. LATENCY                       also a design decision and also a budget
      ↓
8. CONTRACT                      what to measure, what to promise, when to stop
```

---

## Brainstorm questions with the agent

**1. How often does your data change?**
Static data (regulations, product documentation) means a one-time ingestion and almost zero
operating cost. A live catalog (prices, stock levels, tickets, correspondence) means a pipeline, a
queue and monitoring of desynchronization. **The difference between them is not a line in the
estimate but whether the project has a data engineer.**

**2. What is your freshness requirement, stated as a number?**
"A change is visible in search after N minutes". Whether you need an event stream depends on it.

**3. How many queries are there per unit of ingestion?**
If there are few queries, an always-hot database is not needed. If there are many queries and writes
are rare, a reserved machine wins. **The four vector database pricing models are chosen by exactly
this ratio, not by the price per gigabyte.**

**4. How many documents do you have and how many tokens are in an average document?**
Without these two numbers the calculation does not begin.

**5. How many queries a day do you expect in the first year?**
And separately: how many of them will fall in the peak hour.

**6. Which generation model, and why exactly that one?**
This is the most expensive line of the estimate. Ask the agent what changes if you take a model one
class cheaper and add a cascade.

**7. How many chunks do you put into the context and how many output tokens?**
Both numbers multiply directly by the number of queries.

**8. Do you have text documents or scans?**
This is the biggest fork in the whole calculation: zero or fifteen hundred dollars on the same
corpus.

**9. Who will operate this and how much does their hour cost?**
The "person" line on a typical corpus is bigger than all the infrastructure put together.

**10. How much does one wrong answer cost in your domain?**
This number determines how many protective layers are justified. Without it the argument about the
reranker and the checks has no basis.

**11. What will you do when the bill grows tenfold?**
The right answer contains a specific lever and its expected effect, not "we will optimize".

**12. Which of your costs are one-time and which are forever?**
Embedding a document is paid once. The vector dimensionality is paid every month for as long as the
project lives.

**13. For how long do you fix the prices in your estimate?**
The answer "forever" is wrong: for one of the models an intro price expires on **31.08.2026**.

**14. What will you write in the contract about quality?**
And separately: what acceptance test on your own data will you run **before** signing.

**15. At what indicators will you stop the project?**
The stop criterion is written into the project charter before the start. A project that cannot be
closed cannot be honest.

---

## The nature of costs: once, forever, every time

| When it is paid | What goes here | Main lever |
|---|---|---|
| **Once per document** | parsing, corpus embedding, chunk enrichment, index building | incremental instead of a full run |
| **Constantly, by volume** | vector storage, index memory, replicas, backups | **dimensionality and storage precision**, not the number of documents |
| **Every query** | query embedding, database read, reranker, generation, tracing | the generation model and the number of chunks in the context |

**An asymmetry that almost nobody accepts consciously.** An embedding is a one-time payment per
document. The ongoing payment is the dimensionality. The decision "take 3072 dimensions instead of
1024" is made in a minute on day one and paid for over years.

A practical conclusion follows: **you should not save on the embedder.** Even at a hundred million
tokens a month the most expensive embedding API costs about 18 dollars.

**Four explicit items:** embeddings → vector database → reranker → generation. **Five forgotten
ones, and they are what spoils the forecast:**

- **document parsing**: on scans it is the largest one-time item;
- **egress traffic**: about $0.08–0.10 per gigabyte, surfaces during a migration;
- **index rebuild**: $12–40 per 10 million vectors on a managed service against $3–12 on your own;
- **index storage overhead**: roughly 1.5 times the volume of the vectors themselves;
- **the minimum plan**, which at small volumes is the dominant item.

Teams underestimate the bill by 2–3 times because they count only generation.

Warning: and an item that on a typical corpus is bigger than all the others put together: **supporting a
production system eats 20–30% of a senior engineer's time.** The estimate comes without a disclosed
methodology, but the order of magnitude is plausible and **flips the conclusion about managed versus
self-hosted**.

---

## Calculation template: formulas line by line

The example's assumptions. Change them: they are here precisely so that there is something to change.

```
D    = 10,000       documents
T    = 3,000        tokens in an average document
C    = 500          chunk size in tokens
O    = 0.15         overlap
Q    = 2,000        queries per day (60,000 per month)
K    = 5            chunks in the context after the reranker
OUT  = 400          output tokens
DIM  = 1536         vector dimensionality
```

**Derived quantities:**

```
Corpus tokens         = D × T                       = 30,000,000
Number of chunks      = D × T / (C × (1 − O))       ≈ 70,000
Tokens to embed       = number of chunks × C        ≈ 35M       (the overlap is paid for twice)
Bytes in storage      = chunks × DIM × 4 × 1.5      ≈ 645 MB
Input tokens/month    = Q_month × (50 + K × C)      = 60,000 × 2,550 = 153M
Output tokens/month   = Q_month × OUT               = 24M
```

**The estimate, two configurations side by side:**

| Item | Formula | Managed stack | Own Qdrant, no reranker |
|---|---|---|---|
| Parsing, one-time | pages × price per page | **$0** (text) or **$1,500** (scans) | same |
| Corpus embedding, one-time | 35M × $0.02 / 1M | $0.70 | $0.70 |
| Chunk enrichment, one-time | ≈ $2.8 × corpus tokens / 1M | $83 (optional) | $83 |
| Storage | 645 MB, database rate | $50 (plan minimum) | $0 (free tier) or $30 (own machine) |
| Query embedding | 3M × $0.02 / 1M | $0.06 | $0.06 |
| Database reads | 60K × ~5 units × $16 / 1M | $4.80 (inside the minimum) | $0 |
| Reranker | 60,000 × $2.00 / 1000 | $120 | $0 |
| Generation (Haiku 4.5) | 153M × $1 + 24M × $5 | $273 | $273 |
| **Total per month** | | **≈ $443** | **≈ $275–305** |
| **Cost per query** | total / 60,000 | **$0.0074** | **$0.0046** |
| **The engineer who keeps it running** | 20–30% of a senior's time | **≈ $6,000/month** | **≈ $6,000/month** |

**This is a calculation, not a measurement.** All the assumptions are above, any line can be
rechecked with arithmetic.

**Now change one line, the generation model:**

| Model | Input / output per 1M | Generation per month | Total, managed stack |
|---|---|---|---|
| Claude Haiku 4.5 | $1 / $5 | $273 | $443 |
| Claude Sonnet 5, intro **until 31.08.2026** | $2 / $10 | $546 | $716 |
| Claude Sonnet 5, **from 01.09.2026** | $3 / $15 | $819 | $989 |
| Claude Opus 5 | $5 / $25 | $1,365 | $1,535 |

**A 3.5x spread from a single config line.** No decision about the vector database, chunking or
embedder comes anywhere near it in influence at this scale.

Warning: **Two caveats that must appear next to this table.**

1. **The Sonnet 5 intro price expires on 31.08.2026.** Whoever builds $2/$10 into the budget will
   get plus 50% from 1 September.
2. **The tokenizer of version 4.7 and newer models produces roughly 30% more tokens on the same
   text.** So a direct comparison of price per token between generations is misleading: **an equal
   price per token means a bill a third higher.** Count on your own text, not by the price list.

**Where the enrichment at $2.8 per million corpus tokens came from.** The original reference point
in the literature is $1.02 per million, and it has not been recomputed since September 2024. A
recomputation by the same method at the prices of 10.08.2026 and a cheap model: a chunk of 800
tokens, a document of 8 thousand, a context of 100 tokens, with prompt caching the document is read
10 times (once as a cache write at a 1.25 multiplier and nine times as a read at a 0.1 multiplier),
that is 17.2 thousand effective input tokens per document of 8 thousand. On a corpus of 30M tokens
that is 3,750 documents, 64.5M of effective input and 3.75M of output. The total is about $83, that
is **roughly $2.8 per 1M corpus tokens.** Recompute it for your own model and your own chunk size.

---

## Prices as of 10.08.2026

**Generation (Anthropic, per 1M tokens):**

| Model | Input | Cache write, 5 min | Cache write, 1 hour | Cache read | Output |
|---|---|---|---|---|---|
| Claude Opus 5 | $5 | $6.25 | $10 | $0.50 | $25 |
| Claude Sonnet 5 (until 31.08.2026) | $2 | $2.50 | $4 | $0.20 | $10 |
| Claude Sonnet 5 (from 01.09.2026) | $3 | $3.75 | $6 | $0.30 | $15 |
| Claude Haiku 4.5 | $1 | $1.25 | $2 | $0.10 | $5 |

Cache multipliers: **write 1.25 at a five-minute lifetime and 2 at one hour, read 0.1.**

**Embedders (per 1M tokens):** OpenAI text-embedding-3-small $0.02 ($0.01 in batch) ·
text-embedding-3-large $0.13 · Cohere Embed 4 $0.12 for text and $0.47 for images ·
Google text-embedding-005 $0.00625 · local models are free plus hardware.

**Rerankers:** Cohere Rerank 4 Fast $2.00 and Rerank 4 Pro $2.50 per 1000 searches. Warning: one search is a
query and up to 100 documents, but **a document longer than 500 tokens is automatically split, and
each part is counted as a separate document.** Long documents quietly turn one paid call into
several.

**Vector databases.** Pinecone: storage $0.33 per GB per month, write units $4–4.50 per million,
read units $16–18 per million, egress traffic $0.10 per GB, **minimum $50 per month.**
Qdrant Cloud: pricing by cluster resources hourly, **zero for queries and writes**, a perpetual free
tier of 0.5 core, 1 GB memory, 4 GB disk. Your own Qdrant on a machine with 16 GB of memory is about
$96 per month.

**The structural difference matters more than the numbers: some price operations, others the size
of the cluster.** For an agent's memory that writes a hundred thousand vectors a day and reads
little, it is the difference between "we pay for traffic" and "we pay for the box".

Warning: **Any cost figure from a blog needs recomputing against the live price list.** A fresh summary
guide from May 2026 counts generation at a price 25% below the actual one and relies on a model that
has already been shut down. The dominant line is wrong, and the conclusion looks convincing.

---

## How proportions shift with scale

The absolute numbers from public tables by scale level are not reproducible (recomputing at verified
prices gives a difference of several times), so here are only the **proportions**, and they are
stable:

| Scale | Documents | Queries per day | What dominates the bill |
|---|---|---|---|
| Pilot | 10,000 | 1,000 | the vector database's minimum plan, about half of the bill |
| Startup | 100,000 | 10,000 | generation, about 50% |
| Mid-size business | 1,000,000 | 50,000 | generation, about 65% |
| Large | 10,000,000 | 200,000 | generation, about 70% |

The share of embeddings falls as it grows from about 10% to about 2%.

---

## "Below X do this, above X do that" thresholds

| Threshold | Below | Above |
|---|---|---|
| A corpus of **about 25,000 tokens** (roughly 60 pages) | cache is cheaper than search, a vector database is not needed | search is cheaper on input tokens, despite the 90% discount on cache reads |
| A managed-service bill of **$300/month three months in a row** | managed, and do not think about it: engineer-hours cost more than hardware | count the migration, but by headcount, not by volume |
| **10–15 million embeddings per month** | a cloud API is cheaper and simpler | your own embedding model wins several times over |

### The CAG versus RAG threshold, computed explicitly

The cache gives a 90% discount on reads, but **the whole corpus** is read, while search sends only
what was retrieved. Hence the formula:

```
CAG is cheaper on input tokens as long as:  corpus_size × 0.1  <  retrieved_context_size
```

With five chunks of 500 tokens (2,500 tokens of context), the corpus threshold is **about 25,000
tokens**, around 60 pages. Numerically, on a corpus of 100 thousand tokens and a thousand queries a
day: the cache gives $0.01 per query on input against $0.00255 for search on a cheap model, that is
**search is four times cheaper**, despite the discount.

Warning: this directly contradicts the common vendor recommendation "if the corpus is under 200 thousand
tokens, drop search in favor of full caching". Both sides are right within their frame: the vendor
optimizes simplicity, latency and quality, the calculation above optimizes tokens. Choose
consciously and know what exactly you are optimizing.

**The break-even point of the cache itself.** At a five-minute lifetime, the cache pays off from the
second read (1.25 + 0.1 = 1.35 against 2.0 for two uncached runs). At one hour, from the third
(2.0 + 0.2 = 2.2 against 3.0). The practical threshold: hit the cache at least once an hour,
otherwise with a one-hour lifetime it expires and the write is paid for again. If the cache is
rewritten more often than once per 10,000 reads, search is cheaper.

Warning: **Saving input tokens is not the same as saving money.** A reproducible measurement: full caching of
the corpus came out **8.8% more expensive** than search, because the model, having the whole corpus
in its context, generated longer answers (698 output tokens against 467), and output costs five
times as much as input. On the same bench there is also the opposite result ($7.54 against $11.10
per 1000 queries). Both are real, the difference is in the answer profile. **Count the full cost of
a query, not the saving on input.**

**What works almost always:** cache the small hot core that every query touches (schema, policies,
the canonical reference) and search the large volatile tail. The cache hit rate in production across
various publications is 80–95%, there is no vendor norm. The measured reduction in API cost on
agentic tasks from prompt caching: 41–80% (500+ sessions, three providers).

### Reranker: we count, we do not believe

A reranker pays off not through quality, **but through trimming the context.** In the calculation
above: without a reranker the top-10 goes into the context, that is 5,050 input tokens, with a
reranker the top-5, that is 2,550. The difference is 2,500 tokens × 60,000 queries = 150 million
input tokens a month.

| Generation model | Saving on context | Reranker price | Result |
|---|---|---|---|
| Haiku 4.5 | $150 | $120 | **+$30, borderline** |
| Sonnet 5 (intro) | $300 | $120 | **+$180, confidently** |
| Opus 5 | $750 | $120 | **+$630, indisputably** |

**The rule: the more expensive the generation model, the more obviously the reranker pays off.** On
the cheapest model, a reranker is bought for quality, not for money, and that should be said
honestly.

### Managed versus self-hosted: four scales and one resolving one

The threshold is named in four incompatible ways, and all four are right, because they measure
different things: by the bill ($300 a month three months in a row) · by queries (60–80 million a
month) · by volume (3–5 times cheaper at 100 million vectors) · by GPU utilization.

**A fifth position settles the argument: the real break is by headcount, not by volume.** A platform
team that already runs a fleet of databases pays a near-zero marginal cost for one more instance. A
single developer pays the whole checklist for the sake of one.

An honest correction: an analysis of the total cost of your own installation shows that the
"hardware" line is not where the money is. Self-hosting is $25–90 for the primary machine, the same
for a standby, $5 for backups, $10 for monitoring **and 4–6 hours of your time a month**. At a rate
of $80–120 an hour the time comes to $320–720 a month, which is more than all the other lines put
together. And what hurts is not the average but the spread: one incident eats a week.

Warning: **A caveat is mandatory: both public total-cost analyses are written by interested parties from
opposite sides.** One sells buying, the other building. Take not the number but the axis along which
to compute your own case. Outside the American market the sign of the conclusion may flip because of
the difference in rates.

---

## Six reduction levers, in descending order of effect

1. **Change the generation model.** Up to 3.5 times on the total bill. A cascade: a cheap model on
   simple queries, an expensive one only on complex ones. A working scheme: cheap large-context
   models gather and aggregate, the expensive one only double-checks.
2. **Caching.** A 50–80% reduction in the number of model calls, on agentic tasks a measured
   reduction in API cost of 41–80%.
3. **Vector quantization.** int8 gives a fourfold compression at a loss of under 1%. Warning: binary
   theoretically gives 32, **the real gain is closer to sevenfold**, because the index graph and the
   metadata are not compressed.
4. **Dimensionality reduction.** A vector of 768 dimensions costs half as much as 1536 in storage
   and memory, linearly.
5. **Splitting hot and cold data.** 10–20% of the vectors serve 80–90% of queries, moving the cold
   tail out gives 40–60% savings on storage.
6. **Reducing search depth.** top-3 instead of top-10 pays less twice: in the database and in the
   context.

---

## Latency is also a budget

Medians by stage, so there is something to check against: query rewriting 50–150 ms without a model
and 500–1500 ms through a model · query embedding 30–150 ms · search 20–400 ms · reranking
100–800 ms · time to first token 300–1500 ms. End to end **0.8–5.5 seconds**.

What actually decides your upper percentile: **a lightweight reranker costs about 12 ms per
document, a hundred candidates is about 740 ms.** What drives you into the tail is **the number of
candidates**, not the choice of reranker model. Plus an architectural property: cross-encoders
fundamentally cannot be batched across queries, so under a spike it is the upper tail that breaks,
not the median.

The argument about the main bottleneck is unresolved (some name reranking, others generation), but
**everyone agrees on one thing: without traces broken down by stage, guessing is useless.**

---

## What to measure from day one and what to agree on

**Half of this set cannot be reconstructed after the fact.**

| When | What we set up |
|---|---|
| Day 0 | **Two separate trace spans**, search and generation, in one request. A merged span hides the most common production bug: search returned garbage, and the generator wrote something fluent |
| Day 0 | The fields of the search span: the query after rewriting · the number of results · chunk identifiers and scores · filters · **the index and embedder version** |
| Day 0 | **Two boolean fields:** empty result after the filter · context truncation. The most benefit per unit of effort, automatic instrumentation does not set them |
| Day 0 | An append-only table `{answer, documents[], time, query hash}`: **the only item that is physically unrecoverable after the fact** |
| Week 1 | A daily aggregate of the distribution of the first score and of the gap between the first and fifth position. The first two weeks are not yet an alert, but collecting a baseline |
| Week 1 | An anchor set of 20–30 queries plus 5 deliberately unanswerable ones, on a schedule |
| Do not do | a judge model on 100% of traffic · alerts on absolute thresholds from someone else's blog · a dashboard of forty charts · buying a platform before understanding the needed fields |

Warning: **Observability can outrun inference in money.** RAG telemetry is 10–50 times larger than that of an
equivalent simple call, the typical growth of the bill after instrumentation is 40–200%. A judge
model on all traffic at $0.001 per check and a million queries is $1000 a day. Online checks are done
on a sample of 1–5% of traffic, asynchronously and never blocking the answer.

**What to agree on in the contract** (for leads and architects this is the most portable part):

| What the contract does not catch | What to demand instead |
|---|---|
| 99.9% availability and a hallucination on every fifth query do not violate a single clause | 95th and 99th percentiles instead of the average |
| The pipeline's overall availability is computed as a **product**, not as a minimum | 30 days' notice of a model version change, the right to pin the version for 90 days |
| "Accuracy" without specifying the slice and the set cannot be verified | the right to roll back on a degradation of the test set by more than 10% or a latency growth of more than 20% |
| A quality promise without an acceptance test | **an acceptance test on your own data before signing** |

**The stop criterion is written into the project charter before the start.** A sample: if the weekly
active audience is below 30% of the target group in the third month, the project is stopped and the
scope is rebuilt.

And about the ceiling of expectations: a product ceiling in the region of 80–85% satisfactory
answers on a real stream. This is a practitioner's subjective estimate without a disclosed
methodology, but something measured stands next to it: in an open competition of 43 teams, nobody
cleared the 80 bar. **A system that is right in 80% of cases is often useless:** an expert knows
that one answer in five is wrong but does not know which, so they recheck all five. The question is
not the average percentage but **on which slice of questions the system is right enough that
checking is not needed.**

---

## Common mistakes

| What not to do | What it leads to | What to do |
|---|---|---|
| Compute generation, multiply by queries and call it a budget | An underestimate by 2–3 times: parsing, the minimum plan, egress traffic, index rebuild and storage overhead are forgotten | Four explicit items plus five forgotten ones, each on its own line |
| Take a price from a fresh guide | The dominant line of the estimate is understated, and the conclusion looks convincing | Open the vendor's price page on the day of the calculation, put the date next to the number |
| Optimize the vector database instead of the generation model | A week of work for a $50 line when next to it is a $273 line and a person at $6,000 | Start with the biggest line, and it is almost always generation |
| Build the intro price into the budget | Plus 50% from the date the promotion ends, and that is already 1 September 2026 | Compute on the permanent price, keep the intro discount as a temporary reserve |
| Compare the price per token between model generations directly | The new tokenizer gives roughly 30% more tokens on the same text: an equal price per token means a bill a third higher | Compare the cost of your typical whole query, not the rate |
| Treat the saving of input tokens as a saving of money | Full caching of the corpus came out 8.8% more expensive than search because of longer answers | Count input and output together: output costs five times as much |
| Take a reranker because that is what people do | On a cheap generation model it pays off barely, and you should know that in advance | Compute the saving on context against the price of the calls on your own load |
| Not counting the cost of a person | The whole argument about managed versus self-hosted is conducted around a line that is tens of times smaller than the "engineer" line | Keep the order of "20–30% of a senior's time" in the estimate, remembering that it is an estimate without a disclosed methodology |
| Turn on full tracing without sampling | The observability bill grows faster than the inference bill | Structural fields always, text bodies consciously, judge scores only on a 1–5% sample |
| Promise "accuracy" in the contract without an acceptance test | The argument about what counts as a correct answer starts after the launch | A test on your own data before signing, the right to a repeat test, publication of the scores |

---

## Layer readiness checklist

- [ ] The three questions of week one are answered: change frequency, freshness requirement, ratio of
      queries to ingestion.
- [ ] The estimate is assembled by lines with formulas, not as a single number.
- [ ] The estimate contains all five forgotten items.
- [ ] Next to every price stands the date it was checked, and it is no older than a week.
- [ ] The cost of one query is computed and compared with the value of one answer.
- [ ] The estimate has a "person" line.
- [ ] The threshold of caching versus search is checked on your own corpus size.
- [ ] The reranker's payback is computed on your own generation model.
- [ ] It is written down what you will do at a tenfold growth in load, with a specific lever.
- [ ] The latency budget is broken down by stage.
- [ ] Separate trace spans for search and generation are set up, with the index and embedder version.
- [ ] The project's stop criterion is written down.
- [ ] For an external customer: the acceptance test on your own data was run before signing.

---

## Public links

The main habit worth taking away: **go to the vendor's price page on the day of the calculation,
not to a blog from the month before last.**

- Anthropic, prices and caching multipliers: https://www.anthropic.com/pricing
- OpenAI, prices: https://openai.com/api/pricing/
- Cohere, embedding and reranker prices: https://cohere.com/pricing
- Qdrant Cloud, pricing by cluster resources and the free tier: https://qdrant.tech/pricing/
- Pinecone, pricing by operations: https://www.pinecone.io/pricing/
- Prompt caching, documentation with multipliers and invalidation rules:
  https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- A measurement of caching savings on agentic tasks: https://arxiv.org/abs/2601.06007
