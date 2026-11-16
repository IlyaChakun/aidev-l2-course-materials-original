# RUNBOOK · Demo 04 · Multi-tenancy

Below is the real output of the run from 01.11.2026 (Qdrant 1.19.2, pgvector 0.8.7-pg17, embedding cache filled), shortened in places. Each step after `make up` takes 2–5 seconds.

## Preparation before the lecture (a day before and 15 minutes before)

A day before:
1. Docker Desktop is running. Ports 6371, 6372, 5451 and 8471 are free: `lsof -iTCP -sTCP:LISTEN | grep -E '6371|6372|5451|8471'` prints nothing.
2. Fill the embedding cache (needs a key, once):
   ```bash
   cd M2-Ilya/demo/04-multitenancy
   export OPENAI_API_KEY=...       # do not print, do not commit
   make up && make seed
   ```
   Check: `find data/cache -name '*.json' | wc -l` → `222`.
3. Run all steps once (`make leak fixed acl test idf tiered rls`). Then `make clean`.

15 minutes before:
1. `make up && make seed`. The key is no longer needed: everything comes from `data/cache`.
2. Open the Qdrant Web UI: http://localhost:6371/dashboard, collection `kb_shared`.
3. A terminal with a large font, at least 160 characters wide: the result lines are long.

If you need your own, new question to the API during the lecture, run `make up` in a shell where `OPENAI_API_KEY` is set. Without the key the API answers `503` with a message about the cache.

---

## Step 0 · Start-up and loading

**Command:** `make up && make seed`

**Expected output:**
```
api ready: http://127.0.0.1:8471
chunks: 212 {'acme': 64, 'globex': 92, 'initech': 56}
embeddings ready (cache: data/cache)
qdrant kb_shared: {'acme': 64, 'globex': 92, 'initech': 56}
postgres chunks (as superuser): {'acme': 64, 'globex': 92, 'initech': 56}
```

**What to say:** "One collection for all customers. Every chunk has `tenant_id` and `groups` in its payload. The `tenant_id` field is indexed as `keyword` with `is_tenant: true`, the graph is `payload_m: 16, m: 0`, that is, a small graph of its own for each tenant."

**Watch for:** in the Web UI open a point and show the payload: `tenant_id`, `groups`, `doc_id`. Note that the `doc_id` `support-hours-and-sla` exists in all three tenants.

**What it proves:** a shared collection is one collection and a field in the payload, not three databases.

**Fallback:** if `make seed` prints `OPENAI_API_KEY is not set`, the cache is empty or deleted. You need a key (see preparation) or a `data/cache` copied in advance.

---

## Step 1 · The leak: an endpoint without the tenant filter

**Command:** `make leak`

**Expected output:**
```
endpoint : /debug/search_unsafe
caller   : tenant=acme groups=['all']
question : Is there a discount code I can give a customer who asks for a discount?
filter   : None

1. [FOREIGN TENANT] globex   enterprise-contracts-and-discounts / What first-line agents can and cannot do  score=0.5161  groups=['all']
2. [own           ] acme     enterprise-contracts-and-discounts / What first-line agents can and cannot do  score=0.5138  groups=['all']
3. [FOREIGN TENANT] initech  initech-internal-pricing / Loyalty discount code  score=0.5105  groups=['finance']  CODE: INITECH-TPS-0042
4. [FOREIGN TENANT] initech  enterprise-contracts-and-discounts / What first-line agents can and cannot do  score=0.5098  groups=['all']
5. [NO ACCESS (group)] acme     acme-internal-pricing / Partner discount code  score=0.4907  groups=['finance']  CODE: ACME-FIN-7731
6. [FOREIGN TENANT] globex   globex-internal-pricing / VIP discount code  score=0.4848  groups=['finance']  CODE: GLOBEX-VIP-2026
7. [own           ] acme     enterprise-contracts-and-discounts / Frequently asked questions  score=0.4656  groups=['all']
8. [FOREIGN TENANT] initech  enterprise-contracts-and-discounts / Frequently asked questions  score=0.4594  groups=['all']

result   : 6 of 8 hits are not allowed for this user  -> LEAK
```

**What to say:** "The user is honestly logged in as acme. But the endpoint calls a 'convenient helper' without a filter, and the first result is a Globex document. Below it are the discount codes of Initech and Globex. The model will put them into the answer to an acme customer and will not notice."

**Watch for:** the line `filter : None`; the codes `INITECH-TPS-0042` and `GLOBEX-VIP-2026`; the fifth line is acme's own secret, but of the `finance` group, and the user does not have it.

**What it proves:** a tenant index does not isolate anything by itself. OWASP LLM08:2025 describes exactly this: "context leakage between users".

**Fallback:** if the API is unavailable, show this output from a slide. To show the leak without secrets, run `make leak-hours`.

### Step 1b (optional) · The same leak on a harmless question

**Command:** `make leak-hours`
```
1. [own           ] acme     support-hours-and-sla / Business hours  score=0.612  groups=['all']
2. [FOREIGN TENANT] globex   support-hours-and-sla / Business hours  score=0.6024  groups=['all']
3. [FOREIGN TENANT] initech  support-hours-and-sla / Business hours  score=0.574  groups=['all']
...
result   : 4 of 6 hits are not allowed for this user  -> LEAK
```
**What to say:** "There are no secrets here, but three different schedules got into the context: 07–19, 06–22 and 10–16. The model will pick one at random. A leak between tenants also means wrong answers."

---

## Step 2 · The fixed path

**Command:** `make fixed`

**Expected output:**
```
endpoint : /search
caller   : tenant=acme groups=['all']
filter   : {'must': [{'key': 'tenant_id', 'match': {'value': 'acme'}}, {'key': 'groups', 'match': {'any': ['all']}}]}

1. [own           ] acme     enterprise-contracts-and-discounts / What first-line agents can and cannot do  score=0.5138  groups=['all']
2. [own           ] acme     enterprise-contracts-and-discounts / Frequently asked questions  score=0.4656  groups=['all']
...
8. [own           ] acme     enterprise-contracts-and-discounts / What an order form is  score=0.3687  groups=['all']

result   : 0 of 8 hits are not allowed for this user  -> isolated
```

**What to say:** "The filter is built by `TenantScope` from the token, not from the request. A handler cannot forget it: the API has no other path to Qdrant. Look at the scores: the first acme result has the same one, 0.5138. The filter does not spoil the search, it removes what belongs to others."

**Watch for:** `filter` now contains `tenant_id` and `groups`; there are no secret codes.

**What it proves:** isolation is provided by the server that adds the filter. Neither the index nor the prompt provides it.

**Fallback:** `curl -s -G localhost:8471/search --data-urlencode "q=What are the support hours?" -H "Authorization: Bearer tok-acme-support"`.

---

## Step 3 · Permissions inside a tenant

**Command:** `make acl`

**Expected output:**
```
tok-acme-support: groups=['all']
  - acme plans-and-pricing / Frequently asked questions groups=['all']
  - acme plans-and-pricing / Plan overview groups=['all']
  - acme plans-and-pricing / Plan comparison table groups=['all']

tok-acme-finance: groups=['all', 'finance']
  - acme acme-internal-pricing / Partner discount code groups=['finance'] CODE: ACME-FIN-7731
  - acme plans-and-pricing / Frequently asked questions groups=['all']
  - acme acme-internal-pricing / Floor price and approvals groups=['finance']
```

**What to say:** "One tenant, one question, two users. Document permissions are a second filter, `groups match any`. Glean and Copilot do the same thing: they mirror the source ACLs and check them on every query."

**Watch for:** finance gets `acme-internal-pricing`, support does not.

**What it proves:** the ACL is part of the search, not post-processing in the prompt.

**Fallback:** the output from a slide.

---

## Step 4 · The isolation test: green on the safe path, red on the buggy one

**Command:** `make test`, then `make test-buggy`

**Expected output:**
```
$ make test
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 2.32s

$ make test-buggy
...
60 failed, 25 passed, 6 deselected in 1.57s
--- first failure in detail:
E   AssertionError: acme received chunks of other tenants: [('globex', 'enterprise-contracts-and-discounts'), ('initech', 'initech-internal-pricing'), ...
```

**What to say:** "The test is parameterized: 5 users × 8 questions, and for each pair two properties are checked: no foreign tenant and no foreign group. For each user it is checked separately that the results contain no foreign secret codes. Plus checks that the tenant cannot be spoofed with a parameter, a header or the upsert body, and that delete with a foreign `doc_id` removes 0 points. A test like this belongs in CI."

**Watch for:** the 25 "passed" on the buggy path are questions that happened to return only own chunks. That is why one question in a test is not enough, you need a set of questions.

**What it proves:** isolation can be checked automatically, and the test catches a forgotten filter.

**Fallback:** `docker compose run --rm tools -m pytest -q tests -k spoofed` is one quick test.

---

## Step 5 · Shared IDF and tenant IDF (Qdrant 1.19)

**Command:** `make idf`

**Expected output:**
```
query: 'warehouse pallet'  tenant: acme  points: all=212, acme=64

term       df all  idf all  df acme  idf acme
pallet          3     4.11        3      2.92
warehouse      93     0.82        1      3.77

-- global IDF (default)
   1. acme/acme-pallet-labels / Label sizes  score=6.427
   2. acme/acme-pallet-labels / Printing labels  score=6.282
   3. acme/acme-pallet-labels / When a label prints incorrectly  score=6.220

-- per-tenant IDF: params.idf.corpus = tenant filter
   params: {'idf': {'corpus': {'must': [{'key': 'tenant_id', 'match': {'value': 'acme'}}]}}}
   1. acme/acme-warehouse-pilot / Pilot overview  score=6.736
   2. acme/acme-pallet-labels / Label sizes  score=4.565
   3. acme/acme-pallet-labels / Printing labels  score=4.462
```

**What to say:** "The neighbor's product is called Globex Warehouse, so the word warehouse appears in 93 chunks out of 212. For BM25 it is almost a stop word, IDF 0.82. For acme this word appears once and matters, IDF 3.77. The tenant filter is in both queries, yet the ranking differs: the statistics are shared. 1.19 added `params.idf.corpus`."

**Watch for:** both queries have a `filter` on acme, there are no foreign chunks. The only difference is the weights.

**What it proves:** a "noisy neighbor" affects not only load but also search quality.

**Fallback:** the `df/idf` table from the output above, on a slide. Important: the script counts df over the `corpus/` files, so run it before `make offboard`.

---

## Step 6 · Tiered multi-tenancy: moving a large tenant to its own shard

**Command:** `make tiered`

**Expected output (shortened):**
```
-- 1. PUT /collections/kb_tiered
   {"vectors": {...}, "shard_number": 1, "sharding_method": "custom"}
-- 2. PUT /collections/kb_tiered/shards  (fallback shard for all small tenants)
   {"shard_key": "default", "shards_number": 1}
-- 3. upsert every tenant with shard_key {target: <tenant>, fallback: default}
   shard_key=default  points= 212 state=Active
-- 4. promote 'globex': PUT /collections/kb_tiered/shards
   {"shard_key": "globex", "shards_number": 1, "replication_factor": 1, "initial_state": "Partial"}
   shard_key=globex   points=   0 state=Partial
-- 5. POST /collections/kb_tiered/cluster
   {"replicate_points": {"filter": {...globex...}, "from_shard_key": "default", "to_shard_key": "globex"}}
   shard_key=default  points= 212 state=Active
   shard_key=globex   points=  92 state=Active
   total exact count (no shard_key): 304  <- 'globex' is now in BOTH shards
-- 6. clean up the copy in the fallback: POST /collections/kb_tiered/points/delete
   shard_key=default  points= 120 state=Active
   shard_key=globex   points=  92 state=Active
   total exact count: 212
-- 7. the same query code for every tenant: shard_key {target: tenant, fallback: default} + tenant filter
   acme    -> acme/support-hours-and-sla (shard default), ...
   globex  -> globex/support-hours-and-sla (shard globex), ...
```

**What to say:** "Small tenants live in a shared shard. When a tenant grows (Qdrant gives a threshold of roughly 20,000 points), a shard of its own is created for it and the points are copied without stopping writes. The query code does not change: target is the tenant, fallback is `default`. If there is no shard of its own, the query goes to the shared one."

**Watch for:** after step 5 there are 304 points: the copy of globex stayed in the fallback shard, and it must be removed manually (step 6). The tenant filter stays in the query after the move too.

**What it proves:** between "a field in a shared collection" and "a collection per tenant" there is a middle path, and a tenant can be moved without downtime.

**Fallback:** if Qdrant is started without `QDRANT__CLUSTER__ENABLED=true`, step 2 fails with "Qdrant is running in standalone mode". Check `docker-compose.yml` and run `make clean && make up && make seed`.

---

## Step 7 · pgvector + Row Level Security

**Command:** `make rls`

**Expected output:**
```
-- 1. superuser (postgres): RLS does not apply to superusers / BYPASSRLS roles
   SELECT tenant_id, count(*) ... -> [('acme', 64), ('globex', 92), ('initech', 56)]
   roles: [('app_user', False, False), ('postgres', True, True)]
-- 2. app_user, app.tenant NOT set: fail closed
   SELECT count(*) FROM chunks -> 0
-- 3. app_user, SET LOCAL app.tenant='acme', app.groups='all'
   SELECT tenant_id, count(*) FROM chunks GROUP BY 1      -> [('acme', 60)]  (no WHERE)
   SELECT count(*) FROM chunks WHERE tenant_id = 'globex' -> 0
   finance-only rows visible to a support user             -> 0
   vector search 'What are the support hours?' LIMIT 5, no WHERE:
     acme/support-hours-and-sla / Business hours
     ...
-- 4. app_user as acme tries to INSERT a row for globex
   InsufficientPrivilege: new row violates row-level security policy for table "chunks"
-- 5. RLS + HNSW: the policy is a filter applied AFTER the index scan -> fewer than k rows
   default plan: Limit -> Sort -> Index Scan using chunks_tenant_idx
   forced plan : Limit -> Index Scan using chunks_embedding_hnsw
   hnsw.ef_search=10, iterative_scan=off          LIMIT 10 -> 3 rows
   hnsw.ef_search=10, iterative_scan=strict_order LIMIT 10 -> 10 rows
```

**What to say:** "In Postgres you can forget the filter in code, but not in the database. The RLS policy adds a condition to every query of the `app_user` role. Without `SET LOCAL app.tenant` the query returns zero rows. Two traps. First: a superuser and an owner with BYPASSRLS see everything, so the application must not connect to the database as them. Second: HNSW first takes `ef_search` candidates, and the policy cuts out the foreign ones only afterwards. We asked for 10 and got 3. The cure is `hnsw.iterative_scan` (pgvector 0.8+)."

**Watch for:** 60 rows, not 64: the four `finance` chunks were cut by the RESTRICTIVE policy. On a small table the planner itself chooses an exact search over the tenant btree index; we force HNSW to show the behavior of a large table.

**What it proves:** RLS is isolation at the DB level, but it has a price: the result can be shorter than k, and queries slower.

**Fallback:** `docker compose exec postgres psql -U app_user -d kb -c "select count(*) from chunks"` → `0`.

---

## Step 8 · Tenant offboarding

**Command:** `make offboard`

**Expected output:**
```
BEFORE
  qdrant kb_shared : {'acme': 64, 'globex': 92, 'initech': 56}
  qdrant kb_tiered : {'acme': 64, 'globex': 92, 'initech': 56}
  postgres chunks : {'acme': 64, 'globex': 92, 'initech': 56}

qdrant: POST /collections/<c>/points/delete {'filter': {'must': [{'key': 'tenant_id', 'match': {'value': 'initech'}}]}}
postgres: as app_user, SET LOCAL app.tenant, then DELETE FROM chunks  (no WHERE: RLS scopes it)
  rows deleted: 56

AFTER
  qdrant kb_shared : {'acme': 64, 'globex': 92, 'initech': 0}
  qdrant kb_tiered : {'acme': 64, 'globex': 92, 'initech': 0}
  postgres chunks : {'acme': 64, 'globex': 92}

NOT covered by this script (offboarding checklist):
  - embedding cache (data/cache) is keyed by text hash, not by tenant
  - Qdrant snapshots / Cloud backups and Postgres backups still contain the tenant
  - API logs, traces (prompts, retrieved chunks), eval datasets, LLM provider logs
  - deleted Qdrant points are only marked deleted until the vacuum optimizer runs
```

**What to say:** "A customer has left and asks us to delete their data. In a shared collection that is a delete by filter and a counter check before and after. In Pinecone or Weaviate it is one operation on a namespace or shard. But the database is not everything: cache, backups, traces with prompts. This is a checklist, not a single command."

**Watch for:** in Postgres `DELETE FROM chunks` without WHERE removed exactly 56 initech rows: the condition was added by RLS.

**What it proves:** tenant deletion is verified with numbers, and how complete it is depends on where else the tenant's data lives.

**Fallback:** to restore the data, `make seed` (from the cache, 9 seconds).

---

## Cleanup

```bash
make down      # stop, the data in the volumes is kept
make clean     # stop and remove the Qdrant and Postgres volumes; data/cache stays
```

## Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| `make up`: `port is already allocated` | port 6371/6372/5451/8471 is taken | `lsof -iTCP:6371 -sTCP:LISTEN`; other demos use their own ports, do not stop other people's containers |
| `api did not start` | import error, or Qdrant/Postgres is not healthy | `make logs`, `make ps` |
| API answers `503 ... not in data/cache` | a new question and there is no key in the api container | `export OPENAI_API_KEY=...; docker compose up -d api` |
| `make seed`: `OPENAI_API_KEY is not set` | the cache is empty | set the key or restore `data/cache` |
| `tiered`: `Qdrant is running in standalone mode` | Qdrant without cluster mode (a volume from an old configuration) | `make clean && make up && make seed` |
| `idf`: the df table does not match the results | run after `offboard` | `make seed`, then `make idf` |
| `rls`: `connection refused` on 5451 | Postgres is still starting | `make ps`, wait for healthy |
| No `chunks` table in Postgres | the init script runs only on an empty volume | `make clean && make up && make seed` |
| After `offboard` the initech tests are empty | initech was deleted | `make seed` |
