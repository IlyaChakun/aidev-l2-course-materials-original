# RUNBOOK: demo M2-01 "Embeddings from scratch and filling a vector DB"

All outputs below are from a real run on 01.11.2026 (Qdrant 1.19.2, `text-embedding-3-small`), abridged; steps 0, 4 and 8-11 from 05.11.2026. Full output: `data/expected-output.txt`.

## Preparation before the lecture (10-15 minutes, better the day before)

1. `cd M2-Ilya/demo/01-embeddings`
2. `make setup` — about 30 seconds with `uv`.
3. `make up` — Qdrant starts in 5-10 seconds, the command waits for the healthcheck. Check: `make status` shows the container as `healthy`.
4. `export OPENAI_API_KEY=...` (or `.env`), then `make warm`. Expected: `Done: 670 texts, matrix (670, 1536)` (315 unique: the chunk variants of step 9 share most sections with the default chunking), then `bge-m3 ... matrix (163, 1024)` and `BAAI/bge-small-en-v1.5 ... matrix (163, 384)`. The first time — a few API requests, less than a cent, Ollama with `bge-m3` running and a ~70 MB FastEmbed download; after that everything comes from `data/cache/`, already filled in git, so on a prepared machine `make warm` only confirms it.
5. Dry run: `make all` — about 15 seconds for steps 0-11 on a fresh Qdrant. Make sure there are no red lines. Step 10 answers are cached for both orders used in the lecture (`make all`, and step 10 right after step 5); a new order or a changed corpus needs the key once.
6. Check the demo survives losing the network: `make all OPENAI_API_KEY= DEMO_OLLAMA_URL=http://localhost:1` must pass with `API requests 0` everywhere.
7. Terminal: width of at least 140 columns (otherwise `DEMO_WIDTH=120 make step3`), large font, dark theme. A browser tab with `http://localhost:6341/dashboard`.
8. If you show steps 6-7 separately from 5, the collection must already exist: run `make step5` beforehand.

The order in the lecture (deck of 12.11.2026): step 1 in Search (slides 11–18), steps 2, 5, 7 in Vectors (24, 30, 32; step 11 as numbers on 26), steps 3 and 6 in Hybrid (36, 39), steps 0, 4, 9 as numbers on the RAG slides (46–48), steps 8 and 10 live in RAG (50, 52). Steps 0-4 do not need Qdrant.

---

## Step 0. The corpus and the golden set

**Command:** `make step0` (no Qdrant, no API)

**Expected output (abridged):**

```
0.1 The corpus  _shared/corpus/*.md
│ Policy    │  8 │ 15 445 │ complaints-handling-procedure, data-privacy-and-gdpr-requests, ... │
│ Billing   │  4 │  9 678 │ ...
│ Account   │  2 │  4 997 │ account-and-login, team-and-roles │
│ total     │ 22 │ 49 452 │
---
title: Account and Login Guide
section: Account
date: 2026-03-12
---

0.2 Two corpus rules
│ reset link lifetime │ 60 minutes  │ account-and-login │
│ extra seat price    │ $5 per seat │ plans-and-pricing │
5 of 5 facts sit in exactly one document.
│ Salesforce │ 0 │   │ dark mode │ 0 │ ...
5 of 5 trap topics appear in no document.

0.3 The golden set  _shared/golden.json
│ core  │ 10 │ I clicked 'forgot password' but the reset email never showed up. ... │ account-and-login.md │
│ multi │  5 │ I'm on the Starter plan and need to export about 50,000 rows. ...     │ reports-and-exports.md, plans-and-pricing.md │
│ trap  │  2 │ How do I connect Lumen to Salesforce?                                 │ none: the agent must refuse │
The marked answers cover 15 of 22 documents. Origin of the questions: model-drafted, human review pending.
```

**What to say:** "Before any search there are two files. The corpus is everything the agent can know: 22 help-center documents for one role, each with title, section and date. Two rules make it measurable: a fact lives in one document, so every question has one right document, and some topics like Salesforce are kept out on purpose, so the trap has no answer. The golden set is the answer key: questions in the users' words with the right document marked before the pipeline is built."

**Watch for:** the homework asks for about 15 documents for the role in your own project; nobody writes a spec for your corpus, so rule 1 is checked by hand for the facts your questions ask about. The questions here are model-drafted, which the homework asks to mark.

**What it proves:** search quality can only be measured against a corpus and a golden set fixed in advance.

**If it does not start:** an offline step; if `_shared/` is missing, the demo folder was copied without it.

---

## Step 1. Inverted index and BM25

**Command:** `make step1`

**Expected output (abridged):**

```
 Inverted index: word → which documents (tf) and its IDF
│ lumen    │ d0:1, d1:1, d2:1           │  3 │ 0.134 │
│ page     │ d0:1, d2:1                 │  2 │ 0.470 │
│ e-4031   │ d1:1                       │  1 │ 0.981 │
│ export   │ d2:5                       │  1 │ 0.981 │

 Saturation: contribution of the word 'export' (IDF=0.981) at tf = 1..10
│ tf │ TF-IDF │ BM25, k1=1.2 │ BM25, k1=2.0 │
│  1 │  0.981 │        0.981 │        0.981 │
│  3 │  2.942 │        1.541 │        1.765 │
│ 10 │  9.808 │        1.927 │        2.452 │
BM25 ceiling = IDF * (k1 + 1) = 2.158 at k1=1.2

 Queries → BM25 document scores
│ reset password link    │ 3.489 │     0 │     0 │ exact words → finds d0
│ What does E-4031 mean? │     0 │ 0.969 │     0 │ error code → finds d1
│ Lumen export           │ 0.142 │ 0.132 │ 1.839 │ 'lumen' is everywhere and weighs almost nothing
│ can't log in           │     0 │     0 │     0 │ no words in common → zero everywhere
│ сбросить пароль        │     0 │     0 │     0 │ another language → zero everywhere
```

**What to say:** "Search before LLMs is a dictionary 'word → documents' and a formula. A rare word weighs more, and repeating a word quickly stops helping. BM25 finds an error code perfectly well — and gives zero on 'can't log in', because the document says 'reset password'."

**Watch for:** the saturation table is the key one, linger on the tf=10 row. The "can't log in" row is a bridge to step 2.

**What it proves:** BM25 = word match + IDF + saturation; its blind spots are synonyms and another language.

**If it does not start:** the step depends on neither network nor Docker; with a broken `.venv` — `make distclean setup`. As a last resort, show the "Step 1" block from `data/expected-output.txt`.

---

## Step 2. Text → embedding

**Command:** `make step2`

**Expected output:**

```
│ I can't log in to my account │  1536 │ +0.0788 +0.0032 +0.0459 -0.0132 +0.0511 -0.0112 -0.0044 +0.0584 │ 1.0000 │

 Closeness to the phrase "I can't log in to my account"
│ phrase                                                │ shared words │ cosine │    dot │ euclid │
│ Не могу войти в аккаунт                               │            0 │ 0.5955 │ 0.5954 │ 0.8994 │
│ How do I reset my password?                           │            0 │ 0.4716 │ 0.4715 │ 1.0278 │
│ Where can I download my invoice for the last payment? │            0 │ 0.2655 │ 0.2655 │ 1.2121 │
│ The weather in Lisbon is sunny today                  │            0 │ 0.0493 │ 0.0493 │ 1.3790 │
cosine and dot match (the difference is at most 0.0002, float rounding)
```

(The Russian phrase "Не могу войти в аккаунт" means "I can't log in to my account".)

**What to say:** "The model turns text into 1536 numbers of length 1. The numbers on their own mean nothing, the meaning is in the distances. Not one phrase has a word in common with the query, and the order is right: the Russian phrase is closest, the password reset is next to it, the billing invoice is further away, the weather in Lisbon is almost zero."

**Watch for:** the absolute values of `text-embedding-3-small` are compressed (0.47 means "close"); stress the order, not the number. Do not confuse 1536 (the dimension) with the model's window or the chunk size — that is the next slide.

**What it proves:** an embedding captures meaning without shared words and across languages; for normalized vectors cosine = dot.

**If it does not start:** without a key and without a cache you will see "No OPENAI_API_KEY...". The fix is `make warm` with a key, or show the block from `data/expected-output.txt`. The cache in `data/cache/` already contains all the phrases of the step.

---

## Step 3. BM25 vs dense on the whole corpus

**Command:** `make step3`

**Expected output (abridged to top-5 for each method):**

```
Chunks: 147, embedding matrix (147, 1536). embeddings: from cache 150, API requests 0

 Error code: "What does E-4031 mean?"
│ 1 │ integrations-and-api > Frequently asked questions  4.346 │ troubleshooting-and-error-codes > Quick reference of error codes 0.411 │
│ 2 │ payment-errors-reference > E-4031 ...  <- answer   4.051 │ payment-errors-reference > E-4012 Payment method rejected        0.398 │
│ 4 │ ...                                                      │ payment-errors-reference > E-4031 ...  <- answer                 0.393 │

 Paraphrase: "I'm a viewer on my company's workspace. Why is the export button missing for me?"
│ 1 │ team-and-roles > Intro  <- answer                 12.519 │ data-privacy-and-gdpr-requests > Requesting a data export        0.465 │
│ 2 │ team-and-roles > Common questions  <- answer       9.884 │ team-and-roles > Intro  <- answer                                0.456 │

 Russian question: "Ссылка для сброса пароля перестала работать. Сколько она вообще действует?"
│ 1 │ — no matching words —                                    │ account-and-login > Forgot password  <- answer                   0.356 │

 Summary: rank of the first chunk with the answer (out of all corpus chunks)
│ Error code       │      BM25: 2  │ Dense: 4 │
│ Paraphrase       │      BM25: 1  │ Dense: 2 │
│ Russian question │ BM25: not found │ Dense: 1 │
```

(The Russian question means "The password reset link stopped working. How long is it valid at all?")

**What to say:** "The same corpus, two ways. Error code: BM25 keeps it near the top, while dense understands 'this is about error codes' and puts the general code reference first — right meaning, wrong code. Paraphrase: dense put the GDPR data export first — similar, but not it; BM25 was saved by the word viewer. Russian question: BM25 — zero, dense — straight on target. Each has its own blind spot, which is why the homework uses a hybrid."

**Watch for:** the first BM25 row on E-4031 is the API FAQ, which contains "What does the Retry-After header mean?": the rare service word `mean` outweighed the rest. A good chance to say that BM25 does not know which word is important, only which word is rare. The document with the answer is highlighted in green, "<- answer" marks the specific chunk.

**What it proves:** BM25 is stronger on exact identifiers, dense on another language and synonyms; "similar" is not the same as "needed".

**If it does not start:** the step does not need Qdrant. Without a cache and a key — the block from `data/expected-output.txt`.

---

## Step 4. Chunking by headings

**Command:** `make step4`

**Expected output:**

```
│ documents                            │                 22 │
│ tokens in the corpus                 │             49 452 │
│ tokens per document: min / avg / max │ 1747 / 2248 / 2618 │
│ chunks                               │                147 │
│ tokens per chunk: min / avg / max    │    155 / 341 / 496 │
│ chunks in the 300-500 range          │         111 of 147 │
│ chunks shorter than 300              │                 36 │

 Overlap and blocks that must stay whole (homework requirements)
│ sections longer than 500, split into pieces │                                                 2 │
│ chunks that start with overlap              │ Available integrations (2 tok); Webhooks (16 tok) │
│ overlap share of all chunk tokens           │                                             0.04% │
│ tables kept whole in one chunk              │                                          58 of 58 │
│ code blocks kept whole in one chunk         │                                          27 of 27 │

 Chunk length distribution (tokens)
│ < 200    │  3 │ ###
│ 250-299  │ 26 │ ##########################
│ 300-349  │ 53 │ #####################################################
│ 450-500  │ 11 │ ###########

 Shortest chunks
│ integrations-and-api > Frequently asked questions │ 155 │

╭── account-and-login > Forgot password · 352 tokens · chunk #2 ──╮
│ Account and Login Guide > Forgot password                        │
│ ...                                                              │
│ The reset link is valid for **60 minutes** and can be used once. │
```

**What to say:** "The config says 300-500, the fact is from 155 to 496, and a quarter of the chunks are shorter than 300. That is normal, but it has to be printed, not assumed. The first line of a chunk is 'Title > Heading': without it the 'Frequently asked questions' chunk does not know what it is about."

**Watch for:** the count is in `tiktoken cl100k_base` tokens, not words or characters. The chunk number (`chunk #2`) will be needed in step 5 for the id. The homework asks for 10-15% overlap: here it fires only on the 2 split sections, the other borders are headings; say so instead of quoting the config. Step 9 measures a real 12% overlap.

**What it proves:** chunking is a separate decision with a measurable result; min/avg/max is a mandatory line of the homework report.

**If it does not start:** an offline step; if tiktoken fails without a network — the dictionary is already in `data/cache/tiktoken/`.

---

## Step 5. Loading into Qdrant step by step

**Command:** `make step5` (Qdrant must be up: `make up`)

**Expected output (abridged):**

```
Qdrant 1.19.2 at http://localhost:6341, collection "lumen_demo".

5.1 Creating the collection: unnamed dense + named sparse "bm25"  PUT /collections/lumen_demo
{ "vectors": {"size": 1536, "distance": "Cosine"},
  "sparse_vectors": {"bm25": {"modifier": "idf"}},
  "metadata": {"embedding_model": "text-embedding-3-small", "sparse_model": "Qdrant/bm25", "chunker": "h2-400tok"} }
5.2 Index on metadata.source before loading  PUT /collections/lumen_demo/index
5.3 Embeddings: 147 chunks from 22 documents → matrix (147, 1536), 0.0 s. from cache 147, API requests 0
5.4 Chunk identifier: uuid5(namespace, "account-and-login.md#0") = 89d810a8-fe18-5abf-88bb-29a2b3911e0b
5.5 Upsert in batches of 64, wait=true
      "vector": { "": [0.0178, 0.0118, ...], "bm25": {"text": "Account and Login Guide > Intro ...", "model": "Qdrant/bm25"} }
  batch 1: points 64, status completed, 0.14 s
  batch 2: points 64, status completed, 0.14 s
  batch 3: points 19, status completed, 0.04 s

 5.6 Verification after loading
│ chunks sent                            │ 147 │
│ points in the collection (count exact) │ 147 │
│ collection status                      │ green │
│ payload indexes                        │ metadata.source │

One point as Qdrant stores it (dense truncated; sparse "bm25": 99 non-zero dimensions out of 2^32 possible)
    "bm25": { "indices": [8834632, 42416133, ...], "values": [1.168, 1.168, 1.6995, ...] }
Dashboard: http://localhost:6341/dashboard#/collections/lumen_demo
```

**What to say:** "The schema is exactly as in the homework: dense without a name, sparse with the name `bm25`. We do not compute the sparse vector — we hand Qdrant the text and the model name `Qdrant/bm25`, and it turns it into a sparse vector itself. The id is uuid5 of 'document#number': a restart gives the same ids. `wait=true` makes the count right after loading honest. Check: we sent 147, the database has 147."

**Watch for:** after the step open the dashboard (`make dashboard`) and show a point: the `content` + `metadata` payload, two vectors. The model name is stored in the collection `metadata` — this is what the homework asks you to check before a run.

**What it proves:** loading is five verifiable actions, not "LangChain magic"; three irreversible decisions (payload schema, id formula, model) are visible in a single JSON.

**If it does not start:** "Qdrant is not reachable" → `make up`, `make status`; port 6341 is taken → `docker ps | grep 6341`. If Docker does not come up at all — show the "Step 5" block from `data/expected-output.txt` and do not open the dashboard.

---

## Step 6. Queries: dense, bm25, hybrid

**Command:** `make step6`

**Expected output (abridged):**

```
The whole hybrid query (vector truncated): two branches in prefetch with 20 candidates each, then RRF fusion and top-5
{ "prefetch": [ {"query": [-0.0075, -0.0412, ...], "limit": 20},
                {"query": {"text": "What does E-4031 mean?", "model": "Qdrant/bm25"}, "using": "bm25", "limit": 20} ],
  "query": {"fusion": "rrf"}, "limit": 5, "with_payload": true }

 Summary: rank of the chunk with the answer (top-5) and the score of the first result
│ question         │ dense │ bm25 │ hybrid │ dense top-1 │ hybrid top-1 │
│ Error code       │     4 │    2 │      3 │      0.4108 │       0.6667 │
│ Paraphrase       │     2 │    1 │      1 │      0.4651 │       0.8333 │
│ Russian question │     1 │ none │      1 │      0.3563 │       0.5000 │
│ Trap             │     — │    — │      — │      0.5783 │       0.8333 │
Trap: the database still returned 5 chunks. The dense top-1 of the trap is 0.5783 — higher than that of the three questions above (maximum 0.4651).

 RRF by hand for "What does E-4031 mean?": score = sum of 1/(k + rank), rank from 0, k = 2
│ troubleshooting-and-error-codes > Quick reference of error codes │ 0 │  4 │ 0.6667 │ 0.6667 │
│ payment-errors-reference > Intro                                 │ 4 │  0 │ 0.6667 │ 0.6667 │
│ payment-errors-reference > E-4031 Currency not supported by card │ 3 │  1 │ 0.5333 │ 0.5333 │
│ payment-errors-reference > E-4012 Payment method rejected        │ 1 │ 11 │ 0.4103 │ 0.4103 │
Matches. In Qdrant 1.19 k can be set explicitly: "query": {"rrf": {"k": 60}}
```

**What to say:** "One endpoint, `/points/query`, for everything. Hybrid is two branches in `prefetch`, each pulls 20, and RRF adds up ranks, not scores: cosine and BM25 are not comparable. The hybrid never failed: the Russian question was saved by dense, the paraphrase by BM25. Now the trap: the corpus says not a word about Salesforce, yet the database returned five chunks, and the cosine of the first is higher than for any real question. A score threshold is not a refusal; the agent refuses."

**Watch for:** on E-4031 the first two places of the hybrid are tied at 0.6667 — the order between them may change from run to run, that is normal. For the Russian question the bm25 column is empty — the hybrid honestly reduces to dense. The "RRF by hand" table answers the question "what is Qdrant's k".

**What it proves:** the hybrid insures against the blind spots of both methods; the database always returns something; RRF is simple arithmetic over ranks.

**If it does not start:** "Collection does not exist" → `make step5`. Empty bm25 results on all questions → the collection was created without the server-side model; recreate it with `make step5`. Otherwise — the block from `data/expected-output.txt`.

---

## Step 7. Re-ingesting a changed document

**Command:** `make step7` (after step 5; at the end the step restores the original version itself)

**Expected output (abridged):**

```
Old version: 7 chunks, new: 6 chunks.
 What changed in account-and-login.md: chunk by chunk, old version → new version
│ account-and-login.md#0 │ Intro                                   │ same text
│ account-and-login.md#2 │ Forgot password                         │ changed: reset link 60 → 30 minutes
│ account-and-login.md#6 │ Changing the account email address      │ removed: no chunk with this number in the new version
  ... An upsert of the new version overwrites #0–#5; #6 has no new chunk to overwrite it, so only a delete removes it.
7.3 And if the ids were random (uuid4 on every run)
  points in the collection: 154, of which from account-and-login.md: 14
  top-3 for "How long is the password reset link valid?": Forgot password (0.5173) | Forgot password (0.5173) | Sign-in lockout (E-3001)
7.4 New version of the document, upsert WITHOUT deletion (6 chunks on top of 7)
  points in the collection: 147, of which from account-and-login.md: 7
  search says the reset link is valid for: 30 min · removed section in the top 3 for the email question: yes
  orphan d16eb53d-...: "Account and Login Guide > Changing the account email address" — this section no longer exists in the document
7.5 The right way: delete by source, then upsert the new version
  points in the collection: 146, of which from account-and-login.md: 6
  search says the reset link is valid for: 30 min · removed section in the top 3 for the email question: no

 Summary: what each way of reloading leaves in the collection
│ step                     │ document │ ids    │ delete first │ points │ diff │ reset link │ email section found │ what happened
│ 7.1 initial              │ old      │ stable │ –            │    147 │   +0 │ 60 min     │ yes                 │ after step 5
│ 7.2 same ids again       │ old      │ stable │ no           │    147 │   +0 │ 60 min     │ yes                 │ idempotent: overwritten
│ 7.3 random ids           │ old      │ random │ no           │    154 │   +7 │ 60 min     │ yes                 │ +7 duplicates
│ 7.3 fix: delete + upsert │ old      │ stable │ yes          │    147 │   +0 │ 60 min     │ yes                 │ duplicates gone
│ 7.4 new, no delete       │ new      │ stable │ no           │    147 │   +0 │ 30 min     │ yes                 │ orphan inside
│ 7.5 new, delete + upsert │ new      │ stable │ yes          │    146 │   -1 │ 30 min     │ no                  │ equals the new document
│ 7.6 rollback             │ old      │ stable │ yes          │    147 │   +0 │ 60 min     │ yes                 │ as after step 5
```

**What to say:** "The document changed: the link now lives 30 minutes, the section about changing the email was removed. If the ids are random, every re-ingest breeds duplicates, and the same chunk takes up space in the context twice. If the ids are stable but you do not delete the old ones, the count does not change, but there is an orphan inside: the database still answers about the deleted section. The right way: delete by `source`, load again. That is why the id formula is one of the homework decisions that live until the end of the course."

**Watch for:** start on the "What changed" table: #2 changed (60 → 30 minutes), #6 removed. Row 7.4 is the main one: the count is 147 and the reset link already says 30 minutes, so the update looks done, but the removed email section is still found. Only row 7.5 has all three right: 146 points, 30 minutes, no email section. The changed document is assembled in memory, the files in `_shared/corpus/` are not touched.

**What it proves:** the id formula gives idempotency, and delete by filter before upsert gives cleanliness; count does not catch orphans.

**If it does not start:** "Collection does not exist" → `make step5`. If the step was interrupted midway, just run it again — it starts from the current state and restores the original version at the end; if in doubt, `make step5` recreates the collection from scratch.

---

## Step 8. Measuring search on the golden set

**Command:** `make step8` (after step 5)

**Expected output** (run of 15.11.2026 right after `make step5`, abridged):

```
Collection check: text-embedding-3-small, 1536 dims, the same model as in the code.

 Where the answer document is: position in the first 10 results (from 1)
│ q07 │ I bought a yearly plan two months ago ... │ refund-and-cancellation-policy │     1 │    3 │      1 │
│ m03 │ Nobody in our company can sign in ...     │ service-status-and-incidents   │  3, 5 │ 6, — │  3, 10 │
│     │                                           │ support-hours-and-sla          │       │      │        │
│ m04 │ Our contract promises a 10% discount ...  │ enterprise-contracts-and-disc. │  1, 6 │ 1, 3 │   1, 4 │

 Retrieval metrics
│ core (10)        │ dense  │ 1.00 (10 of 10) │ 1.00 │ 1.000 │
│ core (10)        │ bm25   │ 1.00 (10 of 10) │ 1.00 │ 0.950 │
│ core (10)        │ hybrid │ 1.00 (10 of 10) │ 1.00 │ 1.000 │
│ two-document (5) │ dense  │   0.80 (4 of 5) │ 1.00 │ 0.785 │
│ two-document (5) │ bm25   │   0.80 (4 of 5) │ 0.80 │ 0.754 │
│ two-document (5) │ hybrid │   0.80 (4 of 5) │ 1.00 │ 0.807 │

Worst question m03 (lowest hybrid NDCG@5): "Nobody in our company can sign in and every page shows a 503. ..."
│ 1 │ troubleshooting-and-error-codes > HTTP 500 and HTTP 503 │ 0.6667 │
│ 3 │ service-status-and-incidents > Severity levels          │ 0.3929 │
positions of the answer document(s): dense 3, 5; bm25 6, —; hybrid 3, 10

| recall@5 | 1.00 (10 of 10) |
| recall@10 | 1.00 (block A) |
| NDCG@5 | 1.00 (block A) |
| recall@5, two-document questions | 0.80 (4 of 5, block A) |
```

**What to say:** "This is the homework's measurement. Seventeen questions with the right documents marked in advance, three searches, the first ten results saved, then arithmetic. recall@5: is the right document in the first five. NDCG@5: and how high. The hybrid passes the threshold with 10 of 10, but so do dense and bm25: these questions are too easy to tell the searches apart. The difference shows on the two-document questions, and the worst one is m03: two intents in one question, the outage words win both branches and the response-time document only reaches 10th place. That is not a chunking problem but a reason to split the question into two searches."

**Watch for:** run it right after `make step5`: after step 7 the collection has been rewritten and the m03 positions shift (on 15.11.2026: hybrid 5, 7, bm25 —, —); the conclusions stay the same. The window is over chunks, as in the homework; a document counts at the position of its first chunk. Traps are not in the metrics: they test the agent's refusal (Lab 05). The questions are model-drafted and still wait for a human review.

**What it proves:** recall@5 ≥ 0.8 is computed by our own code in a few lines; recall@10 against recall@5 and NDCG show what recall alone hides.

**If it does not start:** "Collection does not exist" → `make step5`. A red line about another embedding model → the collection was built by another model: `make step5`.

---

## Step 9. Block A: one change, metrics before and after

**Command:** `make step9` (after step 5; about 3 seconds, the chunk variants come from the cache)

**Expected output (abridged):**

```
 RRF weights: hybrid metrics on the golden set (in brackets: the change against 1:1)
│ 1:1 (before) │ 1.000 │ 1.000          │ 0.800 │ 0.800          │ 0.804          │
│ 3:1          │ 1.000 │ 1.000          │ 0.800 │ 1.000 (+0.200) │ 0.807 (+0.003) │
│ 1:3          │ 1.000 │ 0.963 (-0.037) │ 0.800 │ 0.800          │ 0.798 (-0.005) │

 The chunkings compared
│ 400 (before)      │ 147 │ 341 │ 496 │  2 │  3% │
│ 300               │ 186 │ 272 │ 367 │ 13 │  7% │
│ 300 + overlap 12% │ 186 │ 272 │ 367 │ 15 │ 11% │
│ 500               │ 118 │ 423 │ 620 │  0 │  —  │

 Chunking: hybrid metrics on the golden set (in brackets: the change against 400)
│ 400 (before)      │ 1.000 │ 1.000          │ 0.800 │ 0.800          │ 0.804          │
│ 300               │ 1.000 │ 0.963 (-0.037) │ 0.800 │ 0.800          │ 0.807 (+0.003) │
│ 300 + overlap 12% │ 1.000 │ 0.963 (-0.037) │ 0.800 │ 0.800          │ 0.791 (-0.013) │
│ 500               │ 1.000 │ 0.963 (-0.037) │ 0.800 │ 1.000 (+0.200) │ 0.793 (-0.011) │
The temporary collection "lumen_demo_exp" is deleted; "lumen_demo" was not changed.

Before/after table for report.md (weights 1:1 (before) → 3:1: some metrics up, none down)
```

**What to say:** "Block A of the homework: change one thing, measure on the same set. Weights 3:1 towards dense bring the second document of m03 into the top ten and lose nothing. Smaller or bigger chunks, and the 12% overlap, win one column and lose another: that is a trade-off, not an improvement. And with fifteen questions one question is 0.2 of two-document recall, so none of this is a production decision, only a hypothesis to check on other questions."

**Watch for:** the columns are core r@5, core NDCG@5, multi r@5, multi r@10, multi NDCG@5. The chunk variants keep the step 4 rules and change only the target (range × 0.75 ... × 1.25) or the overlap. The step is in-sample: the variants are judged on the same questions that would be used to pick one.

**What it proves:** a before/after table is cheap once the metric script exists; the deliverable is the delta and an honest reading of it.

**If it does not start:** `No OPENAI_API_KEY ... not in the cache` → the chunker or the corpus changed: `make warm` with the key. If the step was interrupted, a leftover `lumen_demo_exp` is harmless: the next run deletes and recreates it.

---

## Step 10. The answer: from found chunks to a cited answer or a refusal

**Command:** `make step10` (after step 5)

**Expected output (abridged):**

```
10.1 The prompt  POST https://api.openai.com/v1/chat/completions
│ ... Use only the facts in the numbered passages. ... end with one line 'Sources: <file names you used>'.
│ If they do not contain the answer, reply exactly: 'Not covered by the knowledge base.' ...

10.2 q02 (core): How long does the invitation link stay valid when I add a new teammate?
│ The invitation link is valid for **7 days**.  Sources: team-and-roles.md │
needed: team-and-roles · search found 1 of 1 · cited: team-and-roles · refused: no → answered with sources
10.3 t01 (trap): How do I connect Lumen to Salesforce?
│ Not covered by the knowledge base. │                                       → correct refusal
10.4 m01 (multi): I'm on the Starter plan and need to export about 50,000 rows. ...
│ No ... Starter ... 10,000 rows ... Team ... 100,000 rows.  Sources: reports-and-exports.md, plans-and-pricing.md │
10.5 m03 (multi): Nobody in our company can sign in and every page shows a 503. ...
│ This situation is classified as a SEV1 incident ... Sources: [4] │      → partial: the search found 1 of 2 documents

 Worst of the four: m03. Where did it break?
│ search         │ are all needed documents in the top 5?        │ no, missing: support-hours-and-sla.md │
│ chunk          │ does the returned chunk hold the fact, whole? │ cannot hold what was not returned     │
│ prompt / model │ did the model use, cite or refuse correctly?  │ follows from the search               │
```

**What to say:** "The model never sees the database, only the five chunks pasted into its message. The easy question is answered with its source. The trap gets five chunks about connecting other things, and only the prompt makes the model refuse. m01 needs a comparison, 50,000 against the limits; the last sentence of the prompt is there because a stricter prompt refused it (Lab 05). m03 is the worst: the search lost the SLA document, so no prompt can fix it. Diagnose top-down: search, then chunk, then prompt."

**Watch for:** the model wrote `Sources: [4]` instead of a file name on m03: the citation format is part of what a run checks. The verdict column is mechanical; a person still reads every answer. The full run through an n8n agent is Lab 05.

**What it proves:** the answer depends on what the search hands the model; refusal is the prompt's job, and a missing document is the search's.

**If it does not start:** `this answer is not in the cache` → the found chunks differ from the cached run (a new order of steps or a changed corpus): run `make step10` once with `OPENAI_API_KEY`. Answers are cached for `make all` and for step 10 right after step 5.

---

## Step 11. Another embedding model

**Command:** `make step11` (after step 5; vectors from the cache, no Ollama needed after `make warm`)

**Expected output (abridged):**

```
11.1 One question, three models: "How long is the password reset link valid?"
│ text-embedding-3-small │ OpenAI API             │ 1536 │ ... │ 0.517 │ 0.158 │
│ bge-m3                 │ Ollama, a local server │ 1024 │ ... │ 0.718 │ 0.378 │
│ BAAI/bge-small-en-v1.5 │ FastEmbed, ONNX ...    │  384 │ ... │ 0.750 │ 0.452 │

11.2 Wrong model: the question embedded by bge-m3 sent to "lumen_demo" (built by text-embedding-3-small)
response 400 Wrong input: Vector dimension error: expected dim: 1536, got 1024

11.3 One collection per model
Collection check (lumen_demo_bge-m3): bge-m3, 1024 dims, the same model as in the code.
Collection check (lumen_demo_bge-small-en-v1-5): BAAI/bge-small-en-v1.5, 384 dims, the same model as in the code.

 The models on the golden set (dense = the model alone, hybrid = with bm25 and RRF)
│ text-embedding-3-small │ 1536 │ 882 KB │ dense  │ 1.000 │ 1.000 │ 0.800 │ 1.000 │ 0.785 │
│ bge-m3                 │ 1024 │ 588 KB │ dense  │ 1.000 │ 1.000 │ 0.800 │ 0.800 │ 0.893 │
│ BAAI/bge-small-en-v1.5 │  384 │ 220 KB │ dense  │ 1.000 │ 1.000 │ 0.600 │ 0.800 │ 0.752 │
```

**What to say:** "The default everywhere is OpenAI. Here the same question through two local models the homework allows: Ollama bge-m3 and FastEmbed. The vector length is set by the model, and so is the cosine scale: 0.5 is high for OpenAI and low for bge. Send a bge-m3 question to the OpenAI collection and Qdrant refuses; with equal sizes there would be no error, only nonsense. So every model gets its own collection, and the same model must embed the questions. On our golden set bge-m3 is even a little better on the two-document questions, but fifteen questions do not rank models: you pick yours on your own set."

**Watch for:** compare the dense rows; bm25 is the same in every hybrid row. The step keeps `lumen_demo_bge-m3` and `lumen_demo_bge-small-en-v1-5` in Qdrant so they can be opened in the dashboard; `make clean` removes them. In n8n Ollama has an Embeddings node, FastEmbed has none (the homework's HTTP Request path).

**What it proves:** the embedding model is a measured choice, and a collection is bound to the model that built it.

**If it does not start:** `Skipped bge-m3: Ollama is not reachable` → the cache was cleared: start Ollama (`ollama serve`, `ollama pull bge-m3`) and run `make warm`. `FastEmbed is not installed` → `make setup`.

---

## After the lecture

- `make down` — stop Qdrant, the data stays in the volume.
- `make clean` — stop and delete the volume `m2-demo-embeddings_qdrant_storage`. The embedding cache in `data/cache/` stays, showing the demo again will not cost money.
- `make distclean` — also delete `.venv`.

## Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| `Qdrant is not reachable at http://localhost:6341` | the container is not up | `make up`, then `make status` |
| `make up` fails: port is already allocated | port 6341/6342 is taken | `docker ps --format '{{.Names}} {{.Ports}}' | grep 634`; stop the other container or change the port in `docker-compose.yml` and `DEMO_QDRANT_URL` |
| The demo writes to the wrong database | the environment has a `DEMO_QDRANT_URL` from another run | `unset DEMO_QDRANT_URL`; the demo deliberately ignores the plain `QDRANT_URL` |
| `No OPENAI_API_KEY in the environment, and some texts are not in the cache` | the text, corpus or chunker was changed, and the cache is stale | export the key and run `make warm` |
| `OpenAI 429, retrying in N s` | rate limit | nothing: the script waits with a growing pause up to 30 s, up to 8 attempts |
| `OpenAI APIConnectionError` on every attempt | no network, or an empty/wrong `OPENAI_BASE_URL` in the environment | the script ignores an empty `OPENAI_BASE_URL` itself; for a wrong one — `unset OPENAI_BASE_URL` |
| `Collection "lumen_demo" does not exist` | steps 6-11 were run before step 5 or after `make clean` | `make step5` |
| `No OPENAI_API_KEY ... this answer is not in the cache` in step 10 | the chunks found differ from the cached run | run `make step10` once with the key |
| `Skipped bge-m3` / `Skipped BAAI/bge-small-en-v1.5` in step 11 | the step 11 cache is missing and Ollama or FastEmbed is not available | `ollama serve` + `ollama pull bge-m3`, `make setup`, then `make warm` |
| `Collection "lumen_demo" was built with <model> ..., this code embeds questions with text-embedding-3-small` | the collection was built by another model (or by hand) | `make step5`; never search a collection with another model, there is no error, only nonsense |
| An extra collection `lumen_demo_exp` in the dashboard | step 9 was interrupted | harmless; the next `make step9` recreates and deletes it, or delete it in the dashboard |
| Tables wrap and break | narrow terminal | `DEMO_WIDTH=120 make stepN` or reduce the font |
| The numbers in step 3/6 differ slightly from the RUNBOOK | the embeddings were recomputed (a new cache) | the order and conclusions are the same; if needed restore `data/cache/` from git |
