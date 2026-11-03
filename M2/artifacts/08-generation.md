# Artifact 8. Answer generation: refusal, citations, order

## What this is and how to use it

This is a helper document for the last layer of a RAG system: **how an answer is assembled from
the found chunks**. What the prompt looks like, what the model must do when there is no answer,
where the source link comes from, and how to check that the answer really rests on the documents
and not on the model's memory.

The main idea of the layer: **the answer is assembled under a contract, not written by the
model.** Everything that can be checked by code is checked by code, not by a request in the
prompt.

How to use it: attach the file to your agent and build the prompt and the checks with it **for
your course project**. The section "A ready-made template" holds a prompt that you can take whole
and start editing for yourself instead of composing from scratch.

Starter prompt:

```
Read the attached document about the generation layer in RAG. My project: <description: which
documents, which questions, who the user is, what happens on a wrong answer>. Take the prompt
template from section 1 and adapt it to my case: change the rules, the chunk format and the
refusal string. Then walk me through the questions from the section "Brainstorming questions".
At the end, put together: (1) the final prompt, (2) a list of checks on the finished answer
that I will implement in code, (3) the metrics I will watch in production.
```

**What is not in this document.** It does not cover search and fusion (artifact 6), the reranker
(artifact 7), or which fields to put into metadata (artifact 2). On the number of chunks and
their order there is only a short digest here; the full analysis is in artifact 7.

**Definitions.** *Faithfulness* is the share of the answer's claims that are supported by the
supplied chunks. *Answer relevancy* is how well the answer addresses the question asked. These
two metrics **are read only as a pair**; it will become clear why further on.

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

**Closest links of this layer.** The context arrives from
[`07-reranking-and-context.md`](07-reranking-and-context.md), and the fields for the citation
come from [`02-metadata.md`](02-metadata.md). Context and answer tokens are a cost item on every
request ([`11-economics.md`](11-economics.md)), and everything the model reads in the context is
an attack surface ([`10-security.md`](10-security.md)). Two measurement errors that kill the
refusal check are covered in [`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md): why
a refusal example must not be taken from the eval set (§6.1) and why refusal is not hung on a
score threshold (§6.2).

---

## Decision map of the layer

```
found chunks
  ▼
1. CUTOFF BEFORE THE MODEL CALL   nothing above the threshold → refusal,
  ▼                               the model is NOT called, 0 tokens
2. PROMPT ASSEMBLY (two zones)    static part into the cacheable prefix
  ▼                               ─ breakpoint ─ chunks + question last
3. GENERATION                     temperature 0.1–0.2 · source labeling ·
  ▼                               list first, then answer
4. FOUR GATES ON THE ANSWER       retrieval · citation · numbers · grounding
  ▼
5. WHAT THE HUMAN SEES
```

Two lines of defense, and both are needed: **before generation**, a threshold on the reranker
score; **after generation**, a check of the finished answer against the sources. An instruction
in the prompt is the third, weakest line: it costs nothing and works as a wish.

---

## Brainstorming questions with the agent

**Prompt**

1. Take the template from section 1 and rewrite it for my documents and my users. What in it is
   superfluous for my case, and what is missing?
2. Which part of my prompt does not change between requests, and which part does? Are they
   positioned correctly relative to each other?
3. What temperature do I have now? What does it give on the task "answer strictly from the
   documents"?
4. In what language are my documents written and in what language will users ask? What will
   happen if the context is in English and the question is in Russian?

**Refusal**

5. What does my system answer now if nothing relevant was found? Let's check: formulate five
   questions from an unrelated subject area and describe what will happen with each.
6. What cutoff threshold does my framework have by default? If it is zero, does that mean I have
   no refusal at all?
7. What does the **refusal string** look like in my system? Is it literal and identical, or does
   the model word it differently each time? How will I count it in the metrics?
8. What does the user see on a refusal: an empty list, an error message, or a separate screen
   state with hints on what to do next?

**Citations**

9. Where does the source link in my system come from: from the text the model wrote, or from the
   list that search returned?
10. What will happen to already saved citations if I reindex the corpus with a different chunk
    size? Plan a test that will check this.
11. What fields is my link built from, and are they enough to show the user the **specific
    place** in the document, not the document as a whole?
12. Which of the eight citation failure classes (the table in section 3) are real for my project?
    For each, name how I catch it.
13. Do I count claims **without** citations? Or do I check only those that have a citation?

**Checks and metrics**

14. Which of the four gates can I implement in code in a day? Start with the cheapest.
15. Are there numbers in my answers? How will I check that each number appears in the cited
    source verbatim?
16. Which two metrics do I watch in production without labeling: the share of answers without
    a citation and the share of empty results? What alert threshold do I set?
17. What will I answer to the question "why did the answer usefulness metric drop after we fixed
    the refusals"?

---

## 1. A ready-made prompt template

Take it whole and edit it for yourself. Every line here is there for a reason; the reasons are
listed below.

```
──── SYSTEM PART (cacheable prefix, does not change between requests) ────

Answer only from the chunks in the CONTEXT block below.

WORKFLOW
 1. List the identifiers of all chunks, and for each write
    "relevant" or "not relevant". One line per chunk.
 2. Only after that write the answer, relying on the relevant ones.

CITATION
 After every factual claim put the [S<number>] of the chunk
 it was taken from. Do not write a claim without a source. Refer only
 to identifiers that appear in the CONTEXT block.

REFUSAL
 If there are no relevant chunks: output exactly NO_ANSWER_IN_CONTEXT
 and nothing else. Do not use internal knowledge.

LANGUAGE
 Answer in the language of the user's question.

──── CACHE BREAKPOINT ─────────────────────────────────────────────────────

CONTEXT
[S1 | doc=hr-policy-2026.pdf | p. 12 | rev=7 | score 0.87]
<chunk text>
[/S1]

[S2 | doc=hr-faq | anchor=#perenos | rev=3 | score 0.71]
<chunk text>
[/S2]

Reminder: the rules above also apply to this block.

QUESTION: <the user's question verbatim, without rewriting>
```

**Why exactly this way.**

**Two zones and a cache breakpoint.** The unchanging part (citation rules, refusal rule, format)
goes higher, the found chunks and the question lower. The reason is twofold, and both
requirements coincide. Prompt caching requires the static part to be **above** the dynamic part:
otherwise the cache is cut off on every request, because the beginning has changed. Quality
requires the question to be **last** when there are many chunks. The requirements do not
conflict, so use them.

**Forced chunk labeling.** If you have not numbered the chunks by hand, the model has **nothing
to refer to**, and it will invent a reference. The specific syntax does not matter; one thing
does: **it is the only one in the whole system**. Two different labeling formats, in the prompt
and in the answer parser, are a ready source of errors.

**Temperature 0.1–0.2.** The default temperature works against citability on this task: the
model starts paraphrasing the source instead of sticking to it.

**List the sources first, then answer.** That same free technique: plus 5–10% accuracy on the
very same search, without a single extra call. It forces the model to make an explicit decision
on each chunk before it starts writing connected text.

**A repeated reminder after the context block.** A long block of chunks pushes the system
instruction out of the zone of effective attention. One line after the context brings it back.

**A language line written in the user's language.** A separate fix that concerns everyone whose
corpus is Russian. When the context is half English, the model switches to English on about half
of the non-English queries. It is cured by a line "answer in the user's language" written **in
Russian, not in English** (that is, in the language of the user's questions). The rate rises
above 95%.

**The refusal string is literal.** `NO_ANSWER_IN_CONTEXT` is not a matter of style. A literal
string can be grepped in logs, routed to a human, and counted in metrics. Twelve free-form
phrasings of uncertainty ("unfortunately, in the materials provided...") cannot be counted at all.

**On the output format.** If the answer is consumed by code rather than a human, there are
structured-output modes. Note: **keep** schema validation on your side regardless: mid-sized open
models are unstable at holding the format in a RAG context and adapt it to the input data.

---

## 2. Refusal is a mechanism, not a line in the prompt

### Why an instruction is not enough

The line "if you do not know, say that you did not find it" is the weakest form of protection. It
costs nothing and works as a wish, because **an instruction loses to the context**: when five
plausible chunks sit in the prompt, the model will answer from them.

Moreover, search makes the situation **worse**, not better. ICLR 2025, a paper on context
sufficiency, methodology disclosed:

| What was measured | Result |
|---|---|
| Share of wrong answers for one open model | 10.2% **without context** → **66.1% with insufficient context** |
| Willingness to refuse for one commercial model | 84.1% without search → **52% with search** |
| Willingness to refuse for another | 100% → **18.6%** |
| Errors of the best models **with sufficient** context | 14–16% |

It reads like this: **irrelevant context is worse than none**, and refusal becomes less likely
exactly when it is needed most.

And separately: **most frameworks by default return everything with a score above zero.** That
is, you will never have a refusal until you build it, even if the line about refusal in the
prompt is written. Open your framework and look at the default threshold right now.

### What to build instead of an instruction

**The first line, before generation.** A cutoff on the **reranker** score, not on cosine. A
cross-encoder is trained to judge relevance, an ordinary embedder is trained to search quickly;
these are different tasks. A threshold on the fused search score does not work in principle
(analysis in artifact 6), while the reranker score lives on its own scale and is much closer to
what you need. Some cloud search services return it as a separate field on a scale from zero to
four, with a threshold of about 1.5 as a starting point.

Nothing passed the threshold: **the model is not called at all**. Zero tokens, an instant answer.

**An intermediate option.** A grader node before the generator: a cheap call that looks at the
candidates and answers whether they are relevant. Grading costs 200–400 tokens per document. If
all candidates are rejected, the main model is not called.

**The second line, after generation.** Four gates on the finished answer, the table is in
section 3.

Note: **Being honest about the thresholds themselves:** the distributions of in-domain and
out-of-domain questions **overlap**. There is no value that lets through everything needed and
cuts everything extraneous. The threshold is taken on your own base, someone else's is not
transferable, and it is one of the layers of defense, not the whole defense.

### What a refusal looks like for the user

An empty list is not a refusal. A refusal is a **separate screen state**:

```
Model answer:      NO_ANSWER_IN_CONTEXT

Screen state:      The knowledge base has no documents that answer this question.
                   Searched for: "compensation for unused vacation on termination"
                   Sources reviewed: 342, available to you by permissions: 118
                   → refine the wording   → widen the search scope
                   → send the question to the section owner
```

The second line from the bottom is more important than it seems: it answers the question "the
system did not find it, or I am not allowed to see it". Without it the user will think the system
is broken.

### One thing you need to know in advance, or you will take it for a regression

**An honest refusal gives 100% faithfulness with zero hallucinations and collapses answer
relevancy.** A system that honestly refuses on 30% of questions looks worse on the answer
usefulness metric than one that answers something to everything.

This is a **deliberate trade-off, not a degradation**. The metrics here are read only as a pair,
and this has to be talked through with the team before anyone opens the dashboard.

---

## 3. The citation: where it comes from

### Two architectures, not two wordings

There are two answers to the question "where does the citation come from", and they are
fundamentally different systems:

| | Option A: the model names sources | Option B: a registry from search |
|---|---|---|
| Source of the citation | the model refers to the identifiers of the chunks it used | the list that search returned, plus a registry of identifiers issued for this turn |
| Validation | the format is machine-readable, citations are checked by code afterwards | any identifier outside the registry is **rejected before the answer is delivered** |
| What it closes | an invented file name | plus a forged link via document content and a citation pointing at another owner |
| What it costs | nothing, cheaper | an extra layer in the code between search and rendering |

Option B closes a separate security risk: a document can be stuffed with a plausible link to
someone else's identifier, the model will repeat it, and the rendering layer resolves it into
a link without re-checking permissions.

### Where provenance is actually lost

Provenance is lost **not in the model but in your code**. A typical sequence: the database
returned five chunks with identifiers, scores and metadata; the application code pulled out only
the texts, glued them into a string and gave it to the prompt. From that moment even a perfect
call trace will not tie any part of the answer to a source, and the incident review sounds like
"the model hallucinated". That is the end of the chain, not the beginning.

### The citation contract

```
SourceRef = { docId, contentHash, start, end, revision }
```

`chunk_id` is **deliberately not** part of the contract: it is an artifact of a specific ingestion
run. A reference to a position number in the results breaks silently on every reindexing: it
keeps opening, it just points to something else. A detailed analysis of the contract is in
artifact 2.

**A test that catches the problem in one run:** ask a question, save the citations, reindex the
corpus with a different chunk size, and check that no citation has turned into "source gone".

### Correctness and good faith are different things

A subtle point worth walking through with an example. The generator writes prose, and then links
are stitched onto it. The links look like proof but are decoration:

```
Context:  [S1] vacation in the Polish office is 26 working days · [S2] unused days
          carry over until 30 September of the following year · [S3] filing business trips

Honest:   S1 relevant · S2 relevant · S3 not relevant
          Vacation in the Polish office is 26 working days [S1]. Unused days
          carry over until 30 September of the following year [S2].

After the fact:
          Vacation in the Polish office is 26 working days, carry-over until the end of the
          following year, on termination the remainder is compensated in cash [S1].
          ↑ three claims, one marker. The marker is valid, the document exists,
            the link is clickable. The second claim diverges from S2, the third
            is not in the context at all. A check on a single citation misses this.
```

**You have to count all factual claims, not only those that have a citation.** A system that
checked two citations and ignored five claims without citations should not get a pass.

And a general rule: **if a check can be expressed as a string operation, do a string operation,
instead of asking a second generator to grade the first.** A substring check cannot be talked
into a plausible answer.

### Eight citation failure classes

One layer does not catch its neighbor, so the table is read as a list of what you have covered
and what you have not.

| Failure class | Example | What catches it |
|---|---|---|
| Invented reference | the model produces `policy-2026.pdf`, there is no such source | a registry of trusted sources |
| Wrong locator | the file exists, page 84 does not exist in it | a page or element bounds check |
| Evidence mismatch | the page exists, the cited sentence is not on it | a text or value comparison |
| Stale citation | the citation matched an old version of the document | a content fingerprint check |
| Wrong attribution | the evidence lies in a different source | a document identity check |
| Semantic overreach | the chunk is real but does not support the claims | a "claim versus evidence" grader, or a human |
| **A link glued on after the fact** | a relevant source attached after generation | a provenance policy at the level of the individual claim |
| Incomplete coverage | one sentence is supported, three neighboring ones have no citations | a claim inventory and a coverage check |

### Four levels of citation maturity

In ascending order of cost and reliability:

1. **An instruction in the prompt.** Cheap, catches little.
2. **Structured output** of the form `claims[] = {text, supporting_chunk_ids}`. Each claim
   separately, with an explicit list of sources. Already allows counting coverage.
3. **A vendor citation API** with offsets into the source text. Reliable; the price is lock-in to
   a specific provider. The claimed gain in citation recall over a homemade implementation is up
   to 15% (the vendor's estimate, methodology not disclosed).
4. **A post-generation check:** for each claim separately, check whether it follows from the cited
   chunk. The only level that catches a **confident, well-cited, wrong sentence**, and the only
   one everybody skips: it costs an extra model call per claim.

**Two independent axes of citation quality.** Recall: whether every claim is supported.
Precision: whether the chunk supports **this particular** claim. The model can close recall
perfectly by citing something for every sentence.

A practical skew worth building into your scoring scheme: **punish a missed citation harder than
an extra one**. A working ratio from one public scheme: an extra citation minus 0.1, a missed one
minus 0.25…0.3, that is, 2.5 times stricter. The asymmetry is deliberate.

---

## 4. Four gates on the finished answer

What is checked is the **answer against the sources**, not the model against the instruction. All
four are implemented in code.

| Gate | What it checks | Note |
|---|---|---|
| **A. Retrieval** | the best found document is above the threshold | deliberately weak, catches only the obvious |
| **B. Citation** | every source named resolves to an actually retrieved document | catches invented links |
| **C. Numbers** | every number in the answer appears verbatim in the cited source | numbers are where a hallucination costs money, and they are checked cheaply |
| **D. Grounding** | every substantive sentence is attributed to one cited document | the load-bearing gate: **does not require the model's cooperation** |

Order of rollout: B and C are done in a day and catch most of it. D is more expensive, but it is
the one that catches what the others miss. A by itself means almost nothing, but is needed as the
first cutoff.

**A live case showing how much this finds.** An exact-substring check of citations at write time
rejected 122 documents where the "citation" was stitched together from two sentences from
different parts of an article through an ellipsis, plus several hundred documents where the
citation was not in the text at all. More than 500 documents over the cleanup passes.

---

## 5. Order and volume: a short digest

The full analysis is in artifact 7; here is only what affects the prompt.

- **The context cliff at about 2500 tokens.** Above it, reasoning quality drops sharply, and facts
  from the middle are lost with a probability of up to 40%.
- **The best-scoring chunks go to the edges**, not top to bottom in descending order.
- **How many chunks: the dispute is not resolved.** Twenty provided that junk is filtered out by
  a reranker; 4–6 per practical handbooks; 3–5 for security reasons. The condition "provided that
  junk is filtered out" is the point of divergence. This is a product decision, not a search
  engineer's decision.
- **Deduplication of the results by content hash** before prompt assembly: otherwise five nearly
  identical chunks go into the context instead of five different ones.
- **Full text or skip the document.** A half-inserted document is worse than an absent one: when
  the needed sentence is missing, the model does not refuse, it fills in the gap.

---

## 6. What the human sees

Three interface rules that are decided at this layer and that are skipped most often:

1. **Streaming is mandatory.** Waiting ten seconds before the first word appears reads as a hang.
2. **Sources are shown before generation ends**, not after. The user should see what the answer
   is built on while the answer is being written.
3. **An empty result is a separate screen state**, not an empty list.

The display limit: 3–8 chunks and 2–5 source cards; beyond that people stop looking through them.

**An uncomfortable finding worth knowing.** People almost never click on citations. At the same
time, their mere presence raises trust regardless of whether they are real. And the more neatly
the interface presents citations (superscript footnotes, hover previews, highlights), the more
decisively people stop checking. Both sides are true: citations really do raise trust and for
exactly that reason lower checking. The conclusion for us is one: **automatic validation, because
nobody will do it by hand.**

**Whether to show a confidence number.** A dispute that is not resolved. One side: a numeric
score next to the answer interferes with taking advice and guarantees nothing. The other side
(a preregistered experiment, N=404): expressing uncertainty **in the first person** lowers
agreement with the system and **raises the accuracy** of those who use it. Both results are
valid. A working compromise: a textual caveat instead of a falsely precise number.

**Proxy metrics in production without labeling** that you can set up today: the share of answers
without a citation and the share of empty results. The alert threshold for the second is about
5%.

---

## Common mistakes

| What not to do | What it leads to | What to do |
|---|---|---|
| Glue the found texts into one string and add "answer from this text" | The cache is cut off on every request (the dynamic part ended up above the static one), there is nothing to refer to, the model fills in what is missing from its memory | Two zones with a cache breakpoint, chunk labeling, the question last |
| A single line "if there is no answer, say you did not find it", and that is all | Search **lowers** the willingness to refuse: from 84.1% to 52% for one model, from 100% to 18.6% for another. The instruction loses to the context | Two lines of defense: a threshold on the reranker score before generation, four gates after |
| Not checking the framework's default threshold | It is usually zero, everything above zero is returned, there is no refusal although the line about refusal is written. The log is clean, the metrics are green | Open the config and set the threshold explicitly. Check with five out-of-corpus questions |
| A free-form refusal wording | Twelve different phrases about uncertainty cannot be grepped and are not counted in any metric | A literal string, one for the whole system, routed to a human and counted |
| The marker `[2]` meaning "the second element of the array assembled for this query" | The array depends on the query, embedder, chunker, index and weights. Any reindexing silently redirects all saved citations | A `SourceRef` contract without a chunk identifier, plus a reindexing test |
| Parsing citations from the model's prose without a registry | A document can be stuffed with a plausible link to someone else's identifier, and the model will repeat it | A registry of identifiers issued for this turn, and rejection of any foreign one **before** the answer is delivered |
| Checking only the claims that have a citation | Five claims without citations pass the check entirely | An inventory of **all** factual claims, then a coverage check |
| Asking a second model to grade the first where a string operation is enough | The judge makes mistakes, costs money and adds latency. A substring check does not make mistakes | What can be checked by code is checked by code |
| Raising the number of chunks to "be sure it's included" | Contradictions inside the context, growing hallucinations, the bill for input, the best chunks end up in the attention failure zone | Filter with a reranker, deduplicate, 4–6 chunks, the best at the edges |
| Leaving the default temperature | The model paraphrases the source instead of sticking to it, and citability falls | 0.1–0.2 |
| Writing the instruction about the answer language in English | The model switches to English on about half of the non-English queries when the context is in English | Write the language instruction **in the user's language** |
| Seeing the usefulness metric drop after fixing refusals and rolling the change back | An honest refusal collapses this metric by construction, it is a trade-off, not a regression | Read the metrics as a pair: share of confirmed claims and usefulness together |

---

## Layer readiness checklist

- [ ] The prompt is split into two zones, the static part is above the dynamic one, the cache
      breakpoint is set.
- [ ] Each chunk in the context has a forced identifier, and the syntax is the only one in the
      whole system.
- [ ] The user's question is last and is passed verbatim, without rewriting.
- [ ] A repeated reminder of the system rules is placed after the context block.
- [ ] The temperature is set to 0.1–0.2.
- [ ] The instruction about the answer language is written in the user's language.
- [ ] The "list the sources with a relevance mark first, then the answer" technique is enabled.
- [ ] The framework's default threshold was checked, the cutoff before the model call is set
      explicitly.
- [ ] The cutoff goes by the reranker score, not by cosine and not by the fused search score.
- [ ] The refusal string is literal, can be grepped in logs, and is counted in metrics.
- [ ] A refusal is a separate screen state with hints, not an empty list.
- [ ] The citation source is the list from search, not the model's prose; there is a registry of
      issued identifiers.
- [ ] The citation contract does not contain a chunk identifier.
- [ ] The reindexing test is passed: after a chunk size change no citation became "source gone".
- [ ] Gates B (the citation resolves) and C (numbers appear verbatim) are implemented.
- [ ] There is a plan for gate D (sentence grounding) with a cost estimate.
- [ ] **All** factual claims are counted, not only those that have a citation.
- [ ] Production metrics are set up: the share of answers without a citation and the share of
      empty results, the alert threshold is recorded.
- [ ] The team has been warned that an honest refusal collapses the answer usefulness metric, and
      that this is a deliberate trade-off.

---

## What to read

| What | Where | Why |
|---|---|---|
| Sufficient Context, ICLR 2025 | arXiv 2411.06037 | The only careful measurement showing that search lowers the willingness to refuse. The sufficiency labeler was validated on 115 human-labeled examples |
| Self-RAG | arXiv 2310.11511 | Self-checking during generation: labels for relevance, support and usefulness |
| Corrective RAG | arXiv 2401.15884 | A grader between search and generation: corrects before the main model is called |
| Lost in the Middle | arXiv 2307.03172 | Why facts from the middle of the context are lost |
| A paper on AI advice and the willingness to say "I don't know", 15.07.2026, N=3132 | public paper, four of the five experiments preregistered | Users with AI advice are right three times less often with almost doubled confidence |
| First-person uncertainty, N=404, a preregistered experiment | arXiv 2405.00623 | The second side of the dispute about showing confidence: lowers agreement and raises the user's accuracy |
| A taxonomy of RAG failure modes, 28.04.2026, 7 open stacks, 4812 questions | public analysis with disclosed methodology | Shares: search 52% with a bad corpus, fusion 47% with a good one, **pure hallucinations a steady 9–12%** |
| An audit of a conference's bibliography, 17.07.2026, all 4459 papers | public audit | Of 209,985 references, 2 are confirmed nonexistent (0.001%), while 16% of papers carry an unconfirmed claim. That is, the problem is not invented references but unconfirmed claims |
| Documentation of vendor citation APIs | your provider's documentation: fields with the cited text and offsets | The third level of citation maturity together with the price of vendor lock-in |
| OWASP: RAG security recommendations, the section on the context window | https://cheatsheetseries.owasp.org/ | The origin of the "3–5 chunks and 2000–4000 tokens" position |

**What is missing, and that is honest.** Aggregated figures of the kind "half of the answers are
not confirmed by their own citations" circulate in secondary write-ups without named primary
sources, so they are not here: instead there is the table of eight failure classes, which is
mechanical and needs no figures. Nobody has published public quality thresholds for
Russian-language corpora.
