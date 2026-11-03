# Layer 1. Data and preparation

> Module 2 artifact "Context management: RAG and CAG".
> Prices, versions and tool statuses were checked on **10.08.2026**. Anything that costs money or
> lives in someone else's release cycle goes stale within weeks: check the primary source before deciding.

This is the first layer of the pipeline: turn what you actually have lying around in the company into text that
can be chunked and embedded. The layer is boring, and it is the one that eats from a third to half of the project
(this is a practitioners' estimate from experience, not a measurement). Errors here are invisible in a demo and surface on the second
reindexing, when fixing them costs a full recompute of the corpus.

Terms used below without explanation: **chunk** — a piece of text that becomes one
unit of search; **embedding** — a numeric vector the model turns text into so that
similar texts end up close together; **retrieval** — the stage at which the system
pulls candidates from the store before the model writes anything; **recall** — the share
of the needed documents that search found at all; **OCR** — recognizing text in an image;
**VLM** — a model that "looks" at a page as an image and reads it whole.

---

## How to use this document

The document is meant not for reading but for conversation.

1. Connect the file to your agent (Claude Code, Cursor, Codex — any one that reads files
   from the project): put it next to your course project and say "read
   `01-data-preparation.md` in full".
2. Give it a frame: *"You are helping me design the data preparation layer for my project.
   Ask the questions from the 'Questions for brainstorming' section one at a time, press me if I answer
   vaguely, and after each block record the decision made in one line"*.
3. The output should be a short decision document: which sources, which parser
   for each, where the human sits, what orchestrates the run, what gets dropped at intake.
4. Run it against the checklist at the end of the file. Unclosed items are your backlog for the data layer.

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

**Closest links of this layer.** Whatever you extract with the parser is what can be written into fields:
the metadata schema is designed together with this layer ([`02-metadata.md`](02-metadata.md)).
Normalization and text quality directly determine what comes out of chunking
([`03-chunking.md`](03-chunking.md)). If the source is live — wiki, tracker, drive — look right away at
how updates and deletions will be caught ([`09-corpus-lifecycle.md`](09-corpus-lifecycle.md)),
and if foreign or user content gets into the corpus — at how it can poison the results
([`10-security.md`](10-security.md)). Before the first measurement, check where the corpus came from
and look through the finished chunks by eye: §1 in
[`12-pipeline-field-lessons.md`](12-pipeline-field-lessons.md).

---

## Layer decision map

```
WHAT RAW MATERIAL I HAVE               WHAT TO READ IT WITH
├─ text (PDF, DOCX, HTML, Markdown)    ├─ step 1: the file's text layer
├─ tables and reports                  ├─ step 2: a layout model in-house
├─ images and diagrams                 ├─ step 3: VLM over the page image
├─ audio and video                     └─ step 4: agentic re-checking
├─ wiki and issue tracker                       │
└─ correspondence and chats                     ▼
         │                             TYPE OF PREPARATION
         ▼                             ├─ A. deterministic (parser, regexes, hashes)
   SINGLE TEXT FORMAT        ◄──────   ├─ B. model at the perception level (VLM reads the page)
         │                             └─ C. LLM preparation at the meaning level (rewrite into a schema)
         ▼
   WHAT WE DROP AT INTAKE              WHAT RUNS IT
   ├─ stale (before indexing)          ├─ schedule and dependencies (Airflow)
   ├─ exact duplicates (hash)          ├─ data-aware bookkeeping (Dagster)
   ├─ near-duplicates (SimHash/MinHash)├─ parallel stream processing (Ray Data)
   └─ empty and junk chunks            └─ idempotency + backpressure are mandatory
         │
         ▼
   LENGTH NORMALIZATION  ← without it long formats capture the results by arithmetic, not by meaning
```

The main fork of the layer is put in one phrase: **you clean the raw material or you rewrite it**.
The first is deterministic preparation: it is reproducible and diffable. The second is LLM preparation:
it extracts what is not in the file as text, and pays for it with nondeterminism. Mixing them
in one step is not allowed: you lose the ability to tell where an error came from.

---

## Questions for brainstorming with the agent

**About sources**

1. List all the sources my project will take knowledge from. For each: volume in
   documents, average document length, how often it changes, who owns it.
2. Which of them already exist as text, and which will have to be recognized? What on my list
   is actually not a document but an event stream (ticket, correspondence, log)?
3. How many levels of document complexity do I have: plain text, text with images, text
   with tables, text with formulas? The level determines the pipeline; the file extension does not.
4. If I reduce all sources to three classes of objects (document, ticket, message thread),
   what will not fit? What to do about it: a separate branch or dropping the source?

**About parsing**

5. For each source: which step of the parser ladder is the minimum sufficient one? Are there
   documents that will not survive that step, and how will I find out without reading them all?
6. How will I arrange routing: by file type as a whole or by page features? Which feature
   will I use to detect a scan?
7. What about Russian in the sources? Did I check that the chosen parser reads
   Cyrillic with default settings at all?
8. How will I measure the parser on my corpus: how many pages, which ones, and by what criterion
   will I declare it unfit?

**About preparation and images**

9. Where in my pipeline does deterministic processing sit, where the perception model, where
   LLM rewriting into a schema? Is there a place where I applied the third type where it does not belong?
10. What do I do with images: discard them, store them by reference or describe them in text at intake?
    Did I check on a hundred random images how many of them carry information that is not
    in the adjacent text?
11. If I apply LLM preparation: what must my extractor return for the result to be
    verifiable? Does every object have a verbatim quote and a link to the primary source?
12. Where in my process does the human sit, and by what feature does a task reach them: by the document
    as a whole or by a specific field?

**About normalization, dedup and orchestration**

13. How much do my sources differ in length? What happens to the results if one source
    yields documents twenty times longer than another?
14. What near-duplicates do I have: copies of pages between wiki spaces, contract versions,
    quoting in email chains? Which of these classes is more expensive to lose than to keep?
15. What do I launch intake with: a cron script, an orchestrator, stream processing? What happens
    if the job crashes in the middle and I run it again?
16. Where is the throughput bottleneck of my pipeline and what happens when the sink
    (embedding API or database) starts to lag?
17. What do I deliberately **not** index and why? Do I have a rule for dropping stale content
    before indexing rather than after?

---

## 1. Length normalization: why long formats capture the results

This is the first thing that breaks on a mixed corpus, and almost nobody checks it in advance.

**What happens.** Say you have three sources: wiki pages (4000 words on average), tickets
(median 184 tokens, 95th percentile 612) and chat messages (20–30 words each). You cut everything
with one chunker at 400 tokens. The wiki yields about 20 chunks per page, a ticket one, a chat
message a third of a chunk. Then search returns the top 10 **chunks**, and the wiki takes eight places
out of ten. Not because it is more relevant, but because it has twenty times more tickets
in the lottery. This is arithmetic, not quality, and no reranker fixes it: it ranks what
was brought to it.

**How to normalize.** Four techniques, applied together.

| Technique | What it does | When mandatory |
|---|---|---|
| Reduce to three classes of objects | Document, ticket, message thread. Each has its own chunker and its own target size of the search unit | Always on a mixed corpus |
| Cap on the number of chunks from one document in the results | Grouping by `doc_id`: no more than 2–3 chunks of one document in the top, the remaining slots go to others | When the corpus has long documents |
| Balanced selection across sources | Take the top 10 from the wiki **and** the top 10 from tickets, then merge, instead of a top 20 from the common pile | When sources differ in size or language |
| Gluing small pieces together | Replies shorter than a threshold are not indexed one by one but are assembled into a thread or a "post plus comments" bundle | Always where there is chat |

**Why small pieces must be glued separately.** Short replies like "+", "top", "agree"
get a vector that matches nothing meaningfully: there is no content in it. Such a chunk
takes a slot in the index and is never found. A working technique: when embedding, feed the model
a concatenation of several adjacent messages as a prefix, but store only the vector of the target
message.

---

## 2. The parser ladder: not a ranking, but four steps

**There is no best parser.** There is a ladder ordered by how hard the
document is to read, and a rule: take the lowest step your documents survive. Most teams
stand one step higher than needed and pay for a capability their inputs do not require —
and the price gap between the extreme steps reaches **250 times**.

| Step | What we read with | When it is the right choice | Order of price per 1000 pages |
|---|---|---|---|
| 1. Text layer | extract what already lies inside the file | digital PDF, one column, prose. Milliseconds per page, no GPU | ~0 |
| 2. Layout model in-house | layout detection plus table structure recognition | there is a text layer, the problem is the layout: columns, nested tables, inset boxes | 0 plus your own GPU |
| 3. VLM (vision model) | the page is rendered to an image and read whole | scan, photo, handwriting, dense financial tables, formulas, multilingual | $4–30 |
| 4. Agentic correction | the model re-checks the regions it is itself unsure about | the cost of an error is higher than the cost of a page. On the order of +20% accuracy on hard documents | $30–60 |

**The two-line rule, verbatim.** Never send a clean digital PDF to a VLM: it is more expensive,
slower, and the model may invent characters that the text layer returned correctly. Never
send a scan to a text-layer extractor: there is nothing to read there, and you will index
emptiness.

**A cheap scan detector** that costs one line: divide the number of characters extracted
from the document by the number of pages. Under a hundred means a scan. A practitioners' heuristic, but it works.

**What breaks the usual selection logic.** High per-character OCR accuracy **does not translate**
into search quality. Structure and meaning errors (a lost table header, merged columns,
a caption that drifted into a row) drag retrieval down despite excellent character-level numbers. A parser
that won on letters loses on answers.

**About benchmarks.** Ranks between the four most cited leaderboards do not match,
and two of them (ParseBench, RD-TableBench) were run by vendors whose products take first place
in those same runs. OmniDocBench and RealDocBench are more independent. The scale of incomparability: one
and the same tool in a single run scores 66.1 on visual grounding and 1.0
on semantic formatting.

**The only meaningful measurement is yours.** Take 20–50 of your own pages, making sure to include the
ugly ones (a scanned appendix, a twelve-column table, a multilingual contract), run them through
two or three candidates and assess one thing: **how much a human will have to fix before the embedder**. A rough
half-hour version: 10 documents, 5 questions for each, a threshold of "fewer than 8 of 10 correct answers
means the parser is wrong for this corpus".

**Prices (checked 10.08.2026).** One popular managed parser has four tiers:
$1.25 / $3.75 / $12.50 / $56.25 per 1000 pages, and **the cheapest tier does not return Markdown
at all** — the request returns a validation error. If the architecture says "PDF to Markdown",
the real lower bound of the price is three times the advertised one. For cloud services, flat OCR costs $1.50
at all three major providers (it is a commodity), and the difference begins at structure: tables
$10–15, form fields $10–50 for the same work. There is usually no batch discount on document parsing.

**The Russian layer.** Here the rule "always take the latest version" does direct harm: a case confirmed by
the maintainer — a popular OCR has a regression on Cyrillic in its new version: a word
that occurs in a document 24 times was found 16 times in the old version and **zero times in the new one**.
An independent measurement on a Russian corpus (24.04.2026) shows a twentyfold spread in text error
between tools (0.510% versus 10.715%), and on table structure a hand-assembled pipeline
on an ordinary CPU beat all the off-the-shelf VLM solutions. A cheap lever: post-processing the OCR
result with a light language model cuts the character error in half and the word error to a third — but it works
only with page context, not line by line.

---

## 3. Three types of preparation, and why they cannot be mixed in one step

By the time of chunking you should have a **single text format**, not a zoo. The only question
is what exactly you use to get there.

**Type A, deterministic.** Parser, regular expressions, Unicode normalization, hashes, stripping
headers and footers by positional statistics. Reproducible, diffable, cheap, does not hallucinate.
Does not understand meaning: cannot tell a caption under a table from a table row.

**Type B, model at the perception level.** A VLM reads the page and returns markup. Takes what
determinism cannot take in principle. Pays with nondeterminism, and its scale is worth knowing:
20 runs of one model on one chart gave a discrepancy in 99.4% of cases, and in 49.0% even
the dimensions of the extracted table differed.

**Type C, LLM preparation at the meaning level.** The raw material is not cleaned but **rewritten into the target
schema**: typed units are extracted from the text stream, and what comes out is immediately what
goes into the index. This is not improved parsing, it is a different operation.

*Example of type C: a pipeline with LLM preparation over video transcripts and chat exports.*
The input is a transcript without punctuation or speaker separation, or a chat dump. The output is a
typed object: unit type (pain, recommendation, case, tool, opinion, figure),
short summary, details, **a verbatim quote from the primary source**, link, date, tags, roles,
sentiment. The summary and details are indexed; the quote with the link sits alongside as proof.
Without the quote the object is unverifiable, and the whole scheme turns into a retelling by the model.

**Routing rule.** Put determinism first and as low as possible. Call the perception model
where determinism returned emptiness or mush, and **by page features, not by corpus
type**. Apply type C where the raw material is by nature not a document: transcript, correspondence,
ticket, log. A sign that you applied type C where it does not belong: you find yourself needing to
check on every object whether the model made it up.

**What type C must deliver, otherwise it is not production-grade:** a fixed output schema and validation
against it instead of free text; a verbatim quote and a link in every object; idempotency
by input hash so that a repeat does not spawn a second object; the model and prompt version in the metadata,
because when they change the corpus will be rewritten differently.

**An honest limitation.** On formalized tasks LLM labeling works. On subtle domain
nuances it noticeably loses to a human: a measurement of sentiment labeling in a hard domain
turned out unsatisfactory. The opposite school ("don't label by hand, let the model build
links in raw data") is also alive. This is not a dispute about facts, these are different classes of tasks, and
you will have to choose.

**A human in the loop is cheaper than a perfect parser.** Thirty seconds of manually marking table
boundaries plus page-by-page processing gave 100% where the model gave 90. Why 90%
is not enough: if the model extracts 90% of 200–300 contract line items, losing 20–30 items
makes manual verification equivalent to full manual entry. Design rule:
**route to a human by field, not by document**, with the threshold set by the cost of an error in the specific
field. An asymmetry of the tools worth knowing in advance: classic OCR returns
confidence for every word, while a language model does not return confidence at all, and a scheme built on confidence
thresholds is left without an input signal.

**Images: describe at indexing time, not at query time.** This is not a matter of taste but of arithmetic (a production
measurement over millions of queries, 01.06.2026). Sending images to the model on every query is plus 27%
to the query cost at one provider and plus 51% at another, with a physical ceiling of about
25 images per query. Describing once at intake with a cheap model and storing as text is plus
1–6%, with significantly better quality. Keeping the caption as a **separate chunk** rather than pasting it
into the parent — 6% against 19%, because inline bloats the chunk that goes into the context
on every call. Multimodal embeddings lose here: they wash out exactly the fine
detail for which the image is indexed in the first place.

---

## 4. When you do not need a vector database at all: markdown plus a router

A guideline worth checking before standing up infrastructure: **up to roughly 10 thousand
documents** an architecture of "a folder of markdown files plus something that can
pick the right file" is competitive. No embeddings, no database, everything in git, everything readable by eye.

Two public examples worth looking at before choosing.

**Andrej Karpathy's "LLM wiki" pattern.** Published not as a repository but as a gist:
`https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f` — a file of ideas that the author
suggests copying into your agent. The idea is the opposite of ordinary RAG: instead of
pulling pieces from raw documents every time, the agent **incrementally builds and maintains a
wiki** — a linked set of markdown pages between you and the sources. A new source
is not indexed but read in: the agent updates entity pages, edits summaries, flags
where new data contradicts old. Knowledge is compiled once and maintained,
rather than derived again on every query. Three layers: immutable sources, the wiki (written only
by the model) and a schema file (`CLAUDE.md` / `AGENTS.md`) with the maintenance rules. Search: the agent first
reads `index.md` — a catalog of all pages with one-line annotations — and only then goes
to the ones it needs. The author writes that at a scale of about a hundred sources and several hundred pages this
works surprisingly well and removes the need for vector infrastructure. A family of open implementations
has already grown around the gist, so starting from scratch is not necessary.

**Graphify** (`https://github.com/Graphify-Labs/graphify`, Apache 2.0). The second path without
embeddings: turn the project into a knowledge graph that the agent traverses instead of grep. Code is parsed
locally via tree-sitter, deterministically, with no model calls, about 40 languages; `calls` / `imports` / `inherits`
links are resolved across files. Documents, PDFs and images go through
a separate semantic pass, this time with a model. A key detail: **every edge is labeled**
as `EXTRACTED` (written explicitly in the source) or `INFERRED` (derived), so you can see where there is a fact
and where a guess. The output is a clickable `graph.html`, a report with key nodes and `graph.json`,
which can be queried. There is no vector index at all.

**When this path breaks**, and it must be named honestly: the corpus grows faster than the model
can maintain the summaries; there are tens of thousands of sources; you need search by arbitrary wording,
not traversal by structure; you need document-level access permissions. Then go back
to the vector database. But starting with one when you have three hundred documents means fixing a problem
you do not have yet.

---

## 5. Wiki and issue tracker: the corpus you already have

Three illusions that break the same way for everyone.

**Illusion one: exporting the wiki is one API call.** In practice: pagination is cursor-based
(there are no offsets, and that is correct — if a page is inserted during the traversal an item would otherwise be lost
or arrive twice); quotas have been counted by the hour since 2026, and a full traversal is no longer
free; there are no webhooks at all for a script on an API token, only polling by modification date;
deletions are **never caught** by polling by date — you need a separate reconciliation pass over the list of
identifiers, otherwise orphaned vectors accumulate in the index.

**Illusion two: HTML will turn into Markdown by itself.** The wiki's storage format is XML
with its own namespaces, not HTML. Naive tag stripping with a regular expression
throws out the structure entirely. And most importantly: **dynamic macros are empty in the export**. A "section
table of contents" page that looks to a human like a list of thirty links is, for the index,
one paragraph of preamble. The workaround is to take rendered HTML and fix its known
defects, or to take the storage format and record the loss of macros among the system's known limitations.
There is no third option where everything converges on its own.

**A silent failure worth knowing in advance:** attachment metadata is returned with code 200,
while the download link from that same metadata responds **401**. The integration looks like it works
and silently downloads not a single image. It is cured by calling the endpoint of the previous API version,
which is not on the deprecation list.

**Illusion three: a ticket is a document.** A ticket is not cut into chunks: median 184 tokens, 95th
percentile 612, it is already semantically whole. There is one fork: **whole, if the system answers
questions like "what did we decide on this topic"; typed (description, acceptance criteria, comment,
linked ticket — as separate chunks), if the system generates artifacts from the ticket** — specs,
tests, subtasks. Nobody has comparative measurements of the two schools on one corpus,
so this is a decision by task profile, not by data.

What we take from a ticket into the embedded text: the key with the title, the description, comments in
chronological order. Everything else goes into metadata (project, type, status, priority, labels,
components, version, dates, links, URL). Two mines: comments in the search response are **truncated
to 20 items**, while the value of a long ticket lies precisely in the long discussion; and integrations
that still send the old pagination parameter **silently return zero tickets** — a
valid empty page comes back, dashboards keep working, search quietly degrades.

---

## 6. Deduplication at intake, in plain language

First, a difference that people confuse. **Dropping the stale** is a decision about what should not
get into the index at all: you compared similar documents, looked at dates and scope, and
left half out. It is done **before** indexing and is cheaper than any later filtering.
**Deduplication** is not hygiene but **editing the distribution of the corpus**, and it can
quietly eat a rare class.

**What a near-duplicate is.** An exact duplicate is byte-for-byte identical text, caught by an ordinary hash.
A near-duplicate is "the same thing, but with edits": the date was updated, a paragraph added, a page copied
to another wiki space, an email quoted in full in a reply. An ordinary hash does not catch them
in principle: it is built so that one changed letter changes the whole fingerprint.

**How SimHash and MinHash work.** The idea is simple: you need a hash that changes **a little**
when the text changes a little. The mechanics: the text is cut into short overlapping fragments
(usually runs of five consecutive words, called shingles), an ordinary hash is computed for each,
and from this pile one short fingerprint is assembled — for example 64 bits. For two similar texts
the fingerprints differ by a few bits. Then it is the fingerprints that are compared, not the texts, and this
turns the task from "compare each with each" into something practically linear.

**A cascade, and the order in it matters.**

| Step | By what | What it removes | Cost |
|---|---|---|---|
| 1 | exact hash of normalized content | 10–30% in web crawls, 30–50% in technical corpora | linear, free |
| 2 | SimHash or MinHash with banding | another 30–50% | nearly linear |
| 3 | embedding cosine **only within candidate pairs** from step 2 | the remainder | a full pass costs the corpus in tokens, the bill is counted before launch |

Not the other way round. Running embeddings over all pairs means paying for the whole corpus for work that
a free hash does 80% of.

**Thresholds.** The standard for the second step is 0.85 by Jaccard measure on five-word shingles; by text type
0.92 for technical and 0.80–0.85 for narrative; for SimHash — a difference of fewer than 10 bits out of 64.
Note: all of these numbers are **reproducible practitioners' heuristics; the specific values
have no academic primary source**. And another thing: the threshold is a property of the model and the corpus together;
when the embedder changes, it is redefined from scratch.

**Three things that make this step dangerous.**

1. **The threshold edits the corpus, it does not clean it.** A shift from 0.85 to 0.80 can move the share
   of retained documents of an individual slice by thirty points, and what disappears is not a redundant copy
   but the only hard example of a rare class.
2. **Similarity is not transitive, but grouping by connected components assumes it is.**
   A is similar to B, B is similar to C, A and C are not similar at all — yet they end up in one group. On
   a real corpus this percolates: lowering the threshold from 0.94 to 0.88 turned a group of
   twelve documents into a component of forty thousand.
3. **Silent breakage.** If normalization before hashing drifts, dedup stops
   working, but nothing crashes. The metrics are green, and the model reads three copies of one fact
   as three independent confirmations.

**Calibrating your own threshold in an hour:** take a stratified sample over eight similarity
bands, label 200 pairs by hand, look at precision per band and set the threshold where
it crosses your tolerance.

**Four artifacts to look at after every dedup run:** the distribution of cluster sizes
(the very chart where percolation shows), the share retained by slice, an audit of the choice of
representative from a group, a diff against the previous run.

**A cheap win for correspondence:** removing quoted text in email chains removes
50–80% of duplication before any chunking. Every email in a thread carries a copy of all the previous ones,
and without this cleaning you index the same paragraph ten times.

**An open question with no answer.** Dedupe chunks, or keep the duplicates and filter
by metadata at retrieval. The distinguishing feature: the first works if you have a "what replaced
what" field; if there is no such field, the second remains.

---

## 7. Cleaning and normalization: concrete thresholds

The order of steps is fixed, and cleaning must happen **before** chunking.

| Step | Specifics |
|---|---|
| Encoding | A detection cascade, then text repair, then NFC normalization |
| Sign of a broken document | The share of the replacement character U+FFFD above 1–2% |
| Junk lines | Minimum line length 5 characters, minimum share of letters 0.4 |
| Headers and footers | A line in the top or bottom band on 80% of pages; a short line up to 30 characters repeated more than twice |
| Positional statistics | Computed **separately** for HTML and PDF: their boilerplate is different in nature |
| HTML | A reader-mode extractor **before** everything else. Naive text extraction drags in navigation, cookie banners and "related articles", and the "privacy policy" starts to outrank the content |
| PDF artifacts | Stripping `(cid:NNN)` and `glyph<...>`, ligatures, soft hyphens |
| Format priority | HTML → TeX → PDF. Parse DOCX directly, **not via conversion to PDF** |

**What must not be done**, and this repeats across sources independently: do not lowercase,
do not remove stop words, do not lemmatize **before embedding** — similarity drops.
The only sensible preprocessing of this kind is masking sensitive data.

Two more classes that are caught only here. **An empty chunk is worse than a missing one:** a scan
from which a text extractor returned emptiness cannot be silently embedded — it will take a vector
slot that will never match anything; log a warning and send it to OCR.
And **the bibliography as a retrieval trap:** a page of literature references steadily lands in the top
because of high keyword density, poisoning the results with a structurally irrelevant piece. It is cured
at intake, not by a reranker.

---

## 8. Orchestrating intake: what runs all this

The shape of the minimal pipeline on which sources converge:
**fetch → detect type → convert → OCR if needed → extract → store →
embed**. The raw file is saved, the type is detected, conversion goes first, OCR is called
only when page features require it.

**Three tools you will meet, in human terms.**

- **Airflow** — a scheduler. Thinks in tasks and schedules: "every night at three o'clock walk the wiki,
  then the tracker, then assemble, then load; if the second step failed, do not start the third". Good
  when there are few steps and they are large. Does not know what lies inside the data, only knows that the task
  completed.
- **Dagster** — the same scheduler, but it thinks not in tasks but in **data**: "here is a set of
  parsed documents, here is a set of chunks, here is a collection in the database; these are stale because
  the source changed". More convenient when the question "what is already done and what needs recomputing" matters,
  and when the pipeline is often partially restarted.
- **Ray Data** — not a schedule but a processing pipeline across many processes and machines: a stream of documents
  goes through stages, and the stages work simultaneously. Taken when you hit the CPU
  or GPU limit on parsing and embedding, not the dependency logic.

The choice between them is not a choice of quality but a choice of what hurts for you: scheduling,
recomputation or throughput. On a corpus of a few thousand documents the honest answer
is often "a script on cron", and that is fine.

**An idempotent job** is one that can be run a second time with the same input and produce
the same result, without a single extra write. How it is done: the record key is computed from the hash of
the content plus the config version, and the write goes through upsert (update or insert),
not through insert. Without idempotency any rerun after a crash doubles part of the corpus,
and it is discovered by the model starting to count one fact as confirmed three times.

**Backpressure** is a mechanism that makes the pipeline **slow down**
when the sink cannot keep up. The sink here is the embedding API with its request limit or the vector
database with its indexing queue. Without backpressure there are two outcomes, both bad: the queue
grows in memory until the process is killed by out-of-memory, or the API starts answering with code 429,
and documents are lost silently.

**Three architecture-level facts.**

- **Offline indexing and online query are two different pipelines.** The first is batch, hours long, the second
  is hundreds of milliseconds. Teams collapse them into one script and later regret it.
- **Streaming execution instead of sequential** moves the total time from the sum of the stages
  to the maximum of them: the first chunks go to embedding while the parser is still working. The trap:
  the stream scheduler itself needs cores, and if you give them all to the parsers the pipeline stalls, and it looks
  like a hang.
- **The bottleneck is usually not the parser.** A production measurement: one pod pulled in 2400 documents per hour
  and hit the embedding API limit at 2.8 chunks per second. Before optimizing
  parsing, measure where you actually stand.

**A checkpoint that costs pennies:** write a JSON snapshot of the parsed document to disk
**before** embedding. Then a failure of the embedder or the database does not force you to reparse the corpus again.

---

## Typical mistakes

| What not to do | What it leads to | What to do instead |
|---|---|---|
| Send the whole corpus to the most powerful parser "to be sure" | You pay for a capability that 20% of documents need; the price gap between steps is up to 250 times | Routing by page features: light down, heavy up |
| Choose a parser by its place on a leaderboard | Ranks differ between benchmarks, two of four were run by winning vendors | 20–50 of your own pages, including ugly ones, criterion "how much a human has to fix" |
| Treat per-character OCR accuracy as a measure of quality | Structural errors drag search down despite excellent WER and CER | Measure hitting the answer on five questions to ten documents |
| Cut all sources with one chunker | The long source captures the results by arithmetic: 8 places out of 10 | Three classes of objects, a cap on chunks per document, balanced selection |
| Send images to the model on every query | +27% and +51% to the query cost, ceiling ~25 images | Describe once at intake with a cheap model: +1–6%, as a separate chunk |
| Paste the image description inside the parent chunk | +19% versus +6%: the bloated chunk goes into the context on every call | A separate chunk tied to the document by metadata |
| Run embeddings over all pairs for dedup | You pay for the whole corpus in tokens for work a free hash does | A cascade: exact hash → SimHash/MinHash → embeddings only within candidate pairs |
| Tweak the dedup threshold "by eye" | The threshold edits the corpus: a shift 0.85 → 0.80 wipes out a rare class, metrics are green | Calibration on 200 labeled pairs, four artifacts after every run |
| Assume similarity is transitive | A group of 12 documents turns into a component of 40,000 | Look at the cluster size distribution after every run |
| Lowercase and lemmatize text before embedding | Similarity drops, and it is unclear why | Leave the text as is; from preprocessing only masking of sensitive data |
| Silently embed an empty parsing result | A vector slot that will never match anything | A warning in the log and sending it to OCR |
| Build intake on wiki and tracker webhooks | Deletions do not arrive, order is not guaranteed, cascading deletions generate no events | A webhook as a signal to reread, polling by date as insurance, reconciliation of the ID list for deletions |
| Rerun a crashed job without an idempotency key | Part of the corpus is doubled; the model reads the duplicate as confirmation of a fact | A key from the content hash plus the config version, upsert instead of insert |
| Start with a vector database on three hundred documents | Infrastructure that you have nothing to fill with and no reason to maintain | Markdown plus a router up to a guideline of 10 thousand documents |
| Check parsing quality on beautiful documents | In production the corpus consists of ugly ones | Deliberately put a scanned appendix and a twelve-column table in the test set |

---

## Layer readiness checklist

The layer can be considered closed when every item has an answer, not an intention.

**Sources and frame**
- [ ] All sources are listed; for each the volume, average length and change frequency are known.
- [ ] Sources are reduced to three classes of objects; what did not fit is named explicitly.
- [ ] For each source the document complexity level is determined, and the pipeline is chosen accordingly.
- [ ] It is written down what we deliberately do **not** index and why.

**Parsing**
- [ ] The minimum sufficient step of the ladder is chosen for each source.
- [ ] There is routing by page features, not by file type as a whole.
- [ ] Your own measurement is done: 20–50 of your pages, two or three candidates, the criterion is written down.
- [ ] Cyrillic is checked on the default settings of the chosen tool.
- [ ] The parser version and the model version are fixed (pinned), not "latest".

**Preparation**
- [ ] Deterministic processing, the perception model and LLM rewriting are explicitly separated.
- [ ] If there is LLM preparation: the output schema is fixed and validated; every object holds
      a verbatim quote and a link; the model and prompt version are written to the metadata.
- [ ] An image strategy is defined, and it is measured on a hundred random images.
- [ ] It is defined where the human sits and by which field (not by document) a task reaches them.

**Normalization and dedup**
- [ ] Length normalization is done: a cap on chunks per document or balanced selection.
- [ ] Small replies are glued into bundles rather than indexed one by one.
- [ ] The dedup cascade is in the right order, the threshold is calibrated on your own sample.
- [ ] After a dedup run the cluster size distribution and the diff against the previous one are examined.
- [ ] Cleaning thresholds (U+FFFD, line length, share of letters, headers and footers) are set and written down.

**Orchestration**
- [ ] Jobs are idempotent: a key from the content hash plus the config version.
- [ ] There is backpressure or an explicit rate limit on the embedding and write side.
- [ ] A checkpoint of the parsed document is written before embedding.
- [ ] Incremental update is designed from the start, including **deletions**.
- [ ] Offline indexing and online query are separated into two pipelines.
- [ ] It is known and measured where the pipeline bottleneck is.

---

## Links

**Patterns without a vector database**
- Andrej Karpathy's "LLM wiki" pattern (a gist describing the idea and the three-layer structure):
  https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Graphify — a knowledge graph over code and documents, local AST parsing, no embeddings:
  https://github.com/Graphify-Labs/graphify

**Parsing benchmarks** (look at the slice for your own document types, not the overall score)
- OmniDocBench — academic, closest to "overall parser strength": https://github.com/opendatalab/OmniDocBench
- olmOCR-Bench — 7010 pass/fail tests, skewed toward scientific texts: https://github.com/allenai/olmocr
- Note: ParseBench and RD-TableBench are cited often, but both were run by vendors whose products
  are in first place in those runs. Do not use them as a ranking; they can be used as a source of methodology.

**Preparation libraries**
- Docling — document conversion, hierarchical parsing, table header repetition: https://github.com/docling-project/docling
- Unstructured — 30+ formats, splitting by headings: https://github.com/Unstructured-IO/unstructured
- trafilatura — reader-mode extraction of the main text from HTML: https://github.com/adbar/trafilatura
- ftfy — repairing text with broken encoding: https://github.com/rspeer/python-ftfy

**Orchestration**
- Apache Airflow: https://airflow.apache.org/docs/
- Dagster: https://docs.dagster.io/
- Ray Data: https://docs.ray.io/en/latest/data/data.html

**Corpus deduplication**
- datasketch — a practical implementation of MinHash and LSH: https://github.com/ekzhu/datasketch
- A description of recipes for cleaning large corpora (FineWeb): https://huggingface.co/spaces/HuggingFaceFW/blogpost-fineweb-v1

**Official documentation of the sources**
- Confluence Cloud REST API v2: https://developer.atlassian.com/cloud/confluence/rest/v2/intro/
- Jira Cloud REST API v3: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
- The ADF format (structure of descriptions and comments in the tracker): https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/
