# RUNBOOK: demo M2-05 "End-to-end RAG in n8n without code"

All outputs below are from the real run of 01.11.2026 (n8n 2.39.10, Qdrant 1.19.2, `text-embedding-3-small`, `gpt-4o-mini`), shortened. The full agent answers are in `runs/eval-20261101-1558.md`. A second run on 15.11.2026 gave the same results (211 points, the same two chat answers, 17/17, the same step 6 error); where it differs, this file says so. Its full answers are in `runs/eval-20261115-1302.md`.

Where it fits in the lecture (deck of 12.11.2026): the live demo at the end of the RAG chapter, slide 53, about 4 minutes: steps 1–4 live, step 5 as a table run in advance; step 6 is optional.

The model answers are not word-for-word repeatable even at temperature 0: the agent words its own search query, and the query can differ between runs. The facts and the verdicts above were stable over both runs, except m03 (step 5).

## Preparation before the lecture (≈ 5 minutes, better the day before)

1. `cd M2-Ilya/demo/05-n8n-rag`, the key: `cp .env.example .env` and put in `OPENAI_API_KEY` (or `export OPENAI_API_KEY=...` in the same terminal).
2. `make up` — ≈ 25 s. Expected: `waiting for n8n readiness................. ok`.
3. `make setup` — ≈ 35 s. Expected:
   ```
   owner created: demo@example.com (HTTP 200)
   Successfully imported 2 credentials.
   Successfully imported 1 workflow.
   Successfully imported 1 workflow.
   restarting n8n to register the chat webhook...
   done. UI: http://localhost:5681 (login demo@example.com / see DEMO05_PASSWORD in .env.example)
   ```
   On a repeated run the first line is `owner already exists`, which is normal. A line `Please restart n8n for changes to take effect if n8n is currently running.` may appear before the restart: it comes from publishing the chat workflow, and the script restarts n8n right after it.
4. A dry run: `make ingest`, `make ask`, `make ask Q="How do I connect Lumen to Salesforce?"` — ≈ 25 s and less than a cent.
5. Decide whether you show the loading live. If so, the collection can stay: the workflow deletes and recreates it by itself.
6. Browser, three tabs: the editor `http://localhost:5681` (log in `demo@example.com` / `Demo05Lumen2026`) with the workflow "Demo 05 · Lumen ingest" open, the workflow "Demo 05 · Lumen support chat (RAG)", and Qdrant `http://localhost:6381/dashboard#/collections/lumen_kb`. Zoom 125–150 %.
   The demo needs internet: the agent calls OpenAI, and the public chat page (`make chat-url`) loads its widget `@n8n/chat` from `cdn.jsdelivr.net`. The **Open chat** panel inside the editor does not depend on that CDN.
7. Take the screenshots for the fallback (list at the end) and put them next to the deck.

---

## Step 1. The stand and the ingestion workflow (30 s)

**What to click:** the tab with the workflow "Demo 05 · Lumen ingest". Move the cursor along the chain from left to right, then over the three nodes at the bottom.

**What you see:** `Start → Reset collection lumen_kb → Read corpus files → Extract text → Source, title, text → Qdrant insert lumen_kb`, below, `Embeddings OpenAI` and `Default Data Loader` are connected to Qdrant, and `Markdown splitter` (1600 characters, overlap 200) to the loader.

**What to say:** "These are the same five ingestion steps from the RAG chapter, only as blocks: read the files, cut them, attach metadata, compute embeddings, write. Not a line of code. In the homework you write this path as a script, because you need hybrid, and this node cannot do it."

**Watch for:** do not dive into the settings of every node. Open only `Default Data Loader` → Options → Metadata: `source`, `title`.

**What it proves:** RAG ingestion is built from ready-made nodes, and the metadata is set explicitly.

**Fallback:** screenshot 1.

---

## Step 2. Loading: 211 points in Qdrant (40 s)

**What to click / run:** in the editor the **Execute workflow** button (≈ 12 s) or `make ingest` in the terminal.

**Expected output of `make ingest`:**

```
running workflow demo05LumenIngest inside m2-demo-n8n-rag-n8n ...
ingestion ok in 12 s
collection lumen_kb: points=211 vector={'size': 1536, 'distance': 'Cosine'}
documents=22 chunks=211 chunk chars min/avg/max=132/1096/1597
payload keys: ['content', 'metadata'] metadata keys: ['blobType', 'loc', 'source', 'title']
```

Then the Qdrant dashboard tab → `lumen_kb` → open any point. An example of a real point:

```
payload.content:  "Error E-2210 \"Export too large\"\n\nWhen a report has more rows than your plan allows, Lumen refuses ..."
payload.metadata: {"source": "reports-and-exports.md", "title": "Reports and Exports",
                   "blobType": "text/plain", "loc": {"lines": {"from": 82, "to": 95}}}
vector:           unnamed, 1536 numbers
```

**What to say:** "22 documents turned into 211 chunks. Look at the point: the text is in `content`, everything else in `metadata`, the vector has no name. This is not an accident: it is exactly the schema the n8n node expects. If in the homework you fill the collection with your own script, the payload and the vector name must be the same."

**Watch for:** in the UI after Execute the Qdrant insert node should show a green number of items. A repeated run does not duplicate the points (the first node deletes the collection): after the second run there are 211 again.

**What it proves:** the point schema is compatible with the n8n node: `content` + `metadata`, unnamed dense 1536 Cosine.

**Fallback:** screenshots 2 and 3.

---

## Step 3. A question with a source (1 min)

**What to click:** the workflow "Demo 05 · Lumen support chat (RAG)" → the **Open chat** button at the bottom of the editor (or the public page from `make chat-url`). The question:

`How long does the invitation link stay valid when I add a new teammate?`

**Expected answer (real, ≈ 4 s):**

```
The invitation link for adding a new teammate is valid for **7 days**. If the invited person does not
accept the invitation within this period, the link will expire, and you will need to re-send it. ...

Sources: team-and-roles.md, account-and-login.md
```

Then in the execution log on the right open the `lumen_knowledge_base` call: the input is `{"input": "invitation link validity new teammate"}`, the output is five fragments with `metadata.source`.

**What to click in the log** (the panel next to the chat after the answer; the same tree is in the **Executions** tab of the workflow, every chat message and every `make eval` question is saved there). Open the entries top to bottom, they follow the order of events:

| # | Entry in the log | What it shows | What it explains |
|---|---|---|---|
| 1 | `OpenAI Chat Model`, first call | no answer text, a tool call instead: `{"name": "lumen_knowledge_base", "args": {"input": "..."}, "type": "tool_call"}` (one per search) | the model did not answer: it decided to call the search tool and wrote the query |
| 2 | `lumen_knowledge_base` → Input | `{"input": "invitation link validity new teammate"}` | the agent wrote its own short query, not the user's sentence |
| 3 | `Embeddings OpenAI` under the tool | Input `query`, Output a list of 1,536 numbers | this query is turned into a vector with the same model as at load time |
| 4 | `lumen_knowledge_base` → Output | 5 items: `pageContent`, `metadata.source`, `id` | what Qdrant returned: the 5 nearest chunks; the node does not show scores |
| 5 | `OpenAI Chat Model`, second call | the answer with `Sources:` | the answer is written only from these 5 fragments |

The tool may run twice for one question. On m01 the agent reworded the same query ("Starter plan export limit", then "exporting data plans limits"). On m04 ("Our contract promises a 10% discount but my invoice does not show it. Can support fix that, and where do I find the invoice?", 15.11.2026) it split the question in two: "10% discount invoice issue", then "how to find invoice"; together the two searches brought both needed documents, and the answer cites both. That is query decomposition, the fix named for m03 on slide 50, done by the agent itself; a good question to show if there is time. Qdrant itself keeps no query log: everything about the search is seen through this tool call. Double-clicking the `lumen_knowledge_base` node on the canvas shows the same Input and Output for the last run.

**What to say:** "The agent decided by itself to call the search and formulated the query itself: short, in keywords. The tool returned five fragments, the answer is built only from them, and at the end there is a source. This is part 3 of the homework in full: the Qdrant Vector Store node in the 'As Tool for AI Agent' mode, top-k 5, the same embedding model as at load time."

**Watch for:** in the `lumen_knowledge_base` node show two fields: the mode `Retrieve Documents (As Tool for AI Agent)` and `Limit` = 5. The agent sometimes cites an extra document (`account-and-login.md` here); it is a reason to talk about citation quality, not about search.

**What it proves:** search is an agent tool; the answer relies on what was found and is signed with a source.

**Fallback:** screenshots 4 and 5. Without a browser: `make ask` in the terminal.

---

## Step 4. The trap: Salesforce (40 s)

**What to click:** in the same chat (or a new session) the question `How do I connect Lumen to Salesforce?`

**Expected answer (real):**

```
I could not find this in the Lumen knowledge base. Currently, Lumen supports integrations with Shopify,
WooCommerce, Zapier, and Slack, but Salesforce is not listed as an available integration. You may consider
using Zapier or the API to create a custom connection to Salesforce.

Sources: integrations-and-api.md
```

**What to say:** "Search always finds something: dense search cannot say 'nothing is there', it returns the five nearest chunks. The agent has to refuse. Here the refusal is done by the prompt: the phrase is built into the system message. The advice about Zapier is not invented: the integrations document says outright that an unknown integration can be built through Zapier or the API."

**What to click in the log:** the same tree as in step 3. Open `lumen_knowledge_base` → Output: there are still 5 chunks (integrations, notifications, onboarding), none about Salesforce. Search never says "nothing found"; the refusal appears only in the second `OpenAI Chat Model` call, because the system message (`AI Agent` → Options → System Message) tells the model to refuse.

**Watch for:** if the model answered without the refusal phrase, do not argue with it live; show the table from step 5, where you can see 2/2 traps.

**What it proves:** refusal on a trap is a homework requirement; the search is not empty here, and the decision is made by the model.

**Fallback:** screenshot 6. Without a browser: `make ask Q="How do I connect Lumen to Salesforce?"`.

---

## Step 5. The golden set through the agent (1.5 min; run in advance or in the background)

**Command:** `make eval` (1–1.5 min for 17 questions: 61 s on 01.11, 95 s on 15.11, 4–8 s per question) or open the ready `runs/eval-20261101-1558.md`. Too long to wait for live: run it before the lecture or in a second terminal while you talk.

**Expected output (shortened):**

```
| id  | kind  | expected                         | retrieved by tool (top-k)                             | cited in answer                  | expected cited | refused | verdict |
| q01 | core  | account-and-login.md             | account-and-login.md                                  | account-and-login.md             | 1/1 | no  | PASS |
| q05 | core  | notifications-and-alerts.md      | release-notes-and-known-issues.md, notifications-...  | release-notes-..., notifications-... | 1/1 | no  | PASS |
| t01 | trap  | -                                | integrations-and-api.md, notifications-..., onboard...| integrations-and-api.md          | -   | yes | PASS |
| t02 | trap  | -                                | mobile-app-guide.md, notifications-and-alerts.md      | mobile-app-guide.md, notif...    | -   | yes | PASS |
| m01 | multi | reports-and-exports.md, plans-...| reports-and-exports.md, plans-and-pricing.md, ...     | reports-and-exports.md, plans-...| 2/2 | no  | PASS |
| m03 | multi | service-status-..., support-hours-and-sla.md | troubleshooting-..., integrations-..., service-status-..., support-hours-..., refund-... | troubleshooting-..., support-hours-and-sla.md | 1/2 | no | PASS |

PASS 17/17
report: runs/eval-20261101-1558.md
```

The history of the first version of the prompt (`runs/eval-20261101-1554-prompt-v1.md`, 16/17): on m01 ("Starter, I need to export 50,000 rows, which plan do I need?") the agent answered correctly (Team, up to 100,000 rows) but started the answer with the refusal phrase. The rule "refuse if what was found does not contain exactly what was asked" fired on the number 50,000, which is not in the documents. The fix is one phrase in the prompt: "do not refuse if the facts are there, even if you have to compare a number from the question with a limit from a table".

**What to say:** "The golden set is the same 17 questions as in Lab 01: 10 core, 5 two-document, 2 traps. In the homework you write your own on your corpus: 10 questions and 2 traps, plus 5 two-document questions in block A. The script sends them to the chat webhook and shows for each one: what the tool returned, what the agent cited, whether it refused. The first version of the prompt gave a false refusal on a question where the answer exists. Refusal by prompt breaks in both directions, so you measure it instead of believing it."

**Watch for:** the column `retrieved by tool` is the search, `cited in answer` is the model. m03 = 1/2 in both runs, but for different reasons: on 01.11 the tool found both needed documents and the agent cited one (a model problem); on 15.11 the tool never returned `service-status-and-incidents.md` (a search problem), because the agent worded its query differently. Same question, same prompt, temperature 0, a different layer at fault. This is the "worst question" analysis from the homework: look at the run, not at the verdict.

A second trap in m03: in a manual rerun on 15.11 the agent answered the Business response time with "2 business days" (the complaints procedure, `complaints-handling-procedure.md`) instead of "4 hours" (`support-hours-and-sla.md`), and still cited `support-hours-and-sla.md`. `eval.py` would count that as PASS: it checks citations and refusals, not facts. Read the "Answers" section of the report.

**What it proves:** search and answer are evaluated separately; without running the golden set, false refusals are not visible; a PASS on citations is not a check of the facts.

**Fallback:** screenshot 7 or open `runs/eval-20261101-1558.md` (or the second run, `runs/eval-20261115-1302.md`).

---

## Step 6 (optional). Why the vector must be unnamed (1 min)

**What to do:** create a neighboring collection with a named dense vector, as people mistakenly do in the homework, and query Qdrant without a vector name, the way the n8n node queries it:

```bash
curl -s -X PUT localhost:6381/collections/lumen_named -H 'Content-Type: application/json' \
  -d '{"vectors":{"dense":{"size":1536,"distance":"Cosine"}},"sparse_vectors":{"bm25":{"modifier":"idf"}}}'
python3 -c "import json; print(json.dumps({'query':[0.01]*1536,'limit':1}))" | \
  curl -s -X POST localhost:6381/collections/lumen_named/points/query -H 'Content-Type: application/json' -d @-
curl -s -X DELETE localhost:6381/collections/lumen_named
```

**Expected output (real, the same on 01.11 and 15.11):**

```
{"status":{"error":"Wrong input: Not existing vector name error: "},"time":0.001148792}
```

The n8n node on such a collection (checked in `load` mode via `n8n execute`) fails with `Bad request - please check your parameters`. The homework text has `Collection requires specified vector name in the request`: a different Qdrant version, the same meaning.

**What to say:** "The n8n node sends the vector without a name. Give the dense vector a name and the node stops searching altogether, even with plain dense. Sparse is always named, keep dense unnamed."

**Watch for:** do not touch `lumen_kb`. The last command deletes only `lumen_named`. How the error looks in tool mode (inside the agent) was not checked on the stand.

**What it proves:** the vector name is a compatibility condition with n8n, not a matter of style.

---

## After the lecture

```bash
make down    # stop, the data is kept
make clean   # stop and remove the volumes: n8n (credentials, history) and Qdrant
```

The OpenAI key lives only in the encrypted n8n database in the `n8n_data` volume; `make clean` deletes it too.

## Screenshots for the fallback

1. The whole canvas "Demo 05 · Lumen ingest" (the chain and the three nodes at the bottom).
2. The `Qdrant insert lumen_kb` node after Execute: green, the number of items.
3. The Qdrant dashboard: collection `lumen_kb`, 211 points, an open point with `content` and `metadata`.
4. The canvas "Demo 05 · Lumen support chat (RAG)" and the `lumen_knowledge_base` node with the mode "Retrieve Documents (As Tool for AI Agent)" and Limit 5.
5. The chat: the question about the invitation link and the answer with `Sources: ...`; next to it the log with the `lumen_knowledge_base` call.
6. The chat: Salesforce and the answer with the refusal phrase.
7. The `make eval` table in the terminal (PASS 17/17).

## If something goes wrong

| Symptom | Cause | What to do |
|---|---|---|
| `SQLITE_ERROR: duplicate column name: role`, n8n in a restart loop | The n8n CLI was started while the server was still migrating the database (`/healthz` answers 200 before the database is ready) | `make clean up setup`. The scripts wait for `/healthz/readiness`, not `/healthz` |
| `n8n Task Broker's port 5679 is already in use` on `n8n execute` | The running n8n already holds the task runners broker port | Run through `make ingest`: it passes `N8N_RUNNERS_BROKER_PORT=5690` |
| `make ask` or `eval` give HTTP 404 right after `make setup` | The webhook is registered a few seconds after the restart | Wait 5–10 s; `eval.py` repeats the request by itself |
| `setup.sh` prints `owner already exists`, but you cannot log in / the script goes to the wrong place | Variables of another project are exported in the shell | The stand reads only `DEMO05_*`; check `make chat-url`, the port must be 5681 |
| The agent answers without `Sources` or with a 401 error | A wrong or empty key in the n8n credentials | Fix `OPENAI_API_KEY`, repeat `make setup` (the credentials are overwritten) |
| HTTP 500 and `429` in the logs (`make logs`) | OpenAI rate limit | Wait a minute; `eval.py` retries up to 4 times with a pause |
| Nothing changed after editing `workflows/*.json` | The old version from the n8n database is running | `make setup` (re-import, publish, restart) |
| `Read corpus files` fails with an access error | n8n 2.x reads files only from the allowed folder | `docker-compose.yml` must have `N8N_RESTRICT_FILE_ACCESS_TO=/data/corpus` and the mount of `../_shared/corpus` |
| Port 5681 or 6381 is taken | Another stand | Set `DEMO05_N8N_PORT` / `DEMO05_QDRANT_PORT` in `.env`, `make clean up setup` |
| The public chat page from `make chat-url` stays blank | Its widget loads from `cdn.jsdelivr.net`, which is blocked or offline | Use **Open chat** inside the editor, or `make ask` in the terminal |
| No network at the lecture | The agent needs OpenAI, so no live answers at all | Screenshots 1–7 and `runs/eval-20261101-1558.md` |
