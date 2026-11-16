# SPEC · Demo 04 · Multi-tenancy

A short specification from which the demo can be rebuilt or extended.

## Goal

Show how a production vector DB isolates tenants (a field with `is_tenant` + a server-side filter, ACL, shards, RLS) and how isolation breaks (a forgotten filter). Every claim is backed by the output of a script or a test.

## Environment

- Docker Compose, project `m2-demo-multitenancy`. Ports listen on 127.0.0.1 only: Qdrant 6371 (REST) and 6372 (gRPC), Postgres 5451, API 8471.
- `qdrant/qdrant:v1.19.2` in distributed mode with a single node: `QDRANT__CLUSTER__ENABLED=true`, `--uri http://qdrant:6335`. This is required for shard keys.
- `pgvector/pgvector:0.8.7-pg17`, database `kb`. The init script `sql/01-init.sql` creates the table, the policies and the `app_user` role.
- Python 3.12-slim. Dependencies are pinned: fastapi 0.162.0, uvicorn 0.54.0, httpx 0.28.1, psycopg[binary] 3.3.6, pytest 9.2.0. Qdrant and OpenAI are called through `httpx` (REST), no SDKs are used.
- The code is mounted at `/app`, `../_shared` at `/shared` (read-only). Scripts run through the `tools` service (`docker compose run --rm tools ...`).

## Data

- Tenants and variant rules are in `tenants/tenants.json`: `company`, `product`, `base_docs` (file names from `_shared/corpus`), `replace` (string pairs, applied in order).
  - acme: 6 base documents, hours Mon–Sat 07–19 UTC, invoice error window 30 days.
  - globex: 10 base documents (the "large" tenant), Mon–Fri 06–22, 21 days, product Globex Warehouse.
  - initech: 6 base documents, Mon–Fri 10–16, 7 days.
- A tenant's own documents live in `tenants/<tenant>/*.md`. Front matter: `title`, `section`, `date`, `groups` (comma-separated).
  - `*-internal-pricing.md` with `groups: finance` and a unique code: `ACME-FIN-7731`, `GLOBEX-VIP-2026`, `INITECH-TPS-0042`.
  - Acme only: `acme-warehouse-pilot.md` (the word warehouse in one chunk) and `acme-pallet-labels.md` (pallet in three chunks, no warehouse). They are needed for the IDF demo.
- Base documents get `groups: all`.
- Chunking by H2: the intro after H1 is a separate chunk. Chunk text: `"{product} | {title} | {section}\n\n{body}"`. 212 chunks in total: acme 64, globex 92, initech 56.
- Point ID: `uuid5(NS, f"{tenant}/{doc_id}/{chunk}")`. `doc_id` (the file name) is not unique across tenants, and this is intentional.
- Payload: `tenant_id`, `groups[]`, `doc_id`, `title`, `section`, `chunk`, `text`.

## Embeddings

- OpenAI `text-embedding-3-small`, 1536 dimensions, batches of 64. On 429 and 5xx: retry with exponential backoff honoring `Retry-After`, up to 8 attempts.
- Cache: `data/cache/embeddings/<sha256[:2]>/<sha256(model + "\n" + text)>.json`, atomic write (tmp + rename).
- On seed, all questions from `config/demo_queries.json` and the texts of the probe document are cached too, so the lecture and the tests work without a key.
- The key is read from the environment only and is never logged.

## Qdrant

`kb_shared`:
```json
PUT /collections/kb_shared
{"vectors": {"dense": {"size": 1536, "distance": "Cosine"}},
 "sparse_vectors": {"bm25": {"modifier": "idf"}},
 "hnsw_config": {"payload_m": 16, "m": 0}}
PUT /collections/kb_shared/index {"field_name": "tenant_id", "field_schema": {"type": "keyword", "is_tenant": true}}
PUT /collections/kb_shared/index {"field_name": "groups", "field_schema": "keyword"}
PUT /collections/kb_shared/index {"field_name": "doc_id", "field_schema": "keyword"}
```

The `bm25` sparse vector is computed on the client and contains only the TF part of BM25: k1 = 1.2, b = 0.75, avg_len = 250. The term index is `crc32(term) & 0x7fffffff`. Tokens: `[a-z0-9]+`, no stop words, length greater than 1. IDF is added by Qdrant (`modifier: idf`). The query vector has weights of 1.0 over the unique terms.

`kb_tiered` (created by `scripts/tiered.py` from the points of `kb_shared`, with no new embeddings):
1. `PUT /collections/kb_tiered {"vectors": {"dense": ...}, "shard_number": 1, "sharding_method": "custom"}` and a `tenant_id` index with `is_tenant`.
2. `PUT /collections/kb_tiered/shards {"shard_key": "default", "shards_number": 1}`.
3. Upsert each tenant with `"shard_key": {"target": "<tenant>", "fallback": "default"}`.
4. `PUT /collections/kb_tiered/shards {"shard_key": "globex", "shards_number": 1, "replication_factor": 1, "initial_state": "Partial"}`.
5. `POST /collections/kb_tiered/cluster {"replicate_points": {"filter": {"must": {"key": "tenant_id", "match": {"value": "globex"}}}, "from_shard_key": "default", "to_shard_key": "globex"}}`. Then poll `GET /collections/kb_tiered/cluster` until all shards are `Active`.
6. `POST /collections/kb_tiered/points/delete {"filter": <globex>, "shard_key": "default"}`: the copy in the fallback is not deleted by itself (checked: 304 points before the cleanup, 212 after).
7. Query: `shard_key {target, fallback}` + the tenant filter. Each point in the response has a `shard_key` field.

Tenant IDF (1.19+): `"params": {"idf": {"corpus": <tenant filter>}}` in `/points/query` together with `"using": "bm25"`.

## API (FastAPI, `app/api.py`)

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | `{"ok": true, "unsafe_endpoint": bool}` |
| GET | `/whoami` | the principal from the token |
| GET | `/search?q=&k=` | `TenantScope.search`: filter `must [tenant_id = p.tenant, groups any p.groups]`; the response has `principal`, `qdrant_filter`, `hits` |
| POST | `/docs` | body `{doc_id, title, text, groups=["all"]}`; extra fields (`tenant_id`) are dropped (`extra="ignore"`). `groups` must be among the user's groups, otherwise 403. The `tenant_id` from the token is written to the payload |
| DELETE | `/docs/{doc_id}` | delete by filter `tenant_id AND doc_id`; returns `deleted_points` (the count before deletion) |
| GET | `/pg/search?q=&k=` | Postgres as `app_user`: `set_config('app.tenant', t, true)`, `set_config('app.groups', g, true)`, then `SELECT ... ORDER BY embedding <=> q LIMIT k` without WHERE |
| GET | `/debug/search_unsafe?q=&k=` | mounted only when `DEMO_UNSAFE_ENABLED=1`. A query without a filter: the bug for the demo |

- Authentication: `Authorization: Bearer <token>` → `config/tokens.json`, from which `user`, `tenant` and `groups` are taken. An unknown or empty token → 401. There are no other sources of the tenant.
- `RuntimeError` (for example, no key and no cache) → 503 JSON.
- Rules to follow when extending:
  - access to Qdrant only through `TenantScope`;
  - the tenant is present in every search, upsert and delete;
  - when reading by point ID, `payload.tenant_id` must be checked against the principal (there is no such endpoint yet).

## Postgres (`sql/01-init.sql`)

- `chunks(id uuid pk, tenant_id text, groups text[], doc_id, title, section, text, embedding vector(1536))`. Indexes: btree on `tenant_id`, `hnsw (embedding vector_cosine_ops)`.
- `ENABLE` and `FORCE ROW LEVEL SECURITY`.
- `tenant_isolation`: `USING` and `WITH CHECK` `tenant_id = current_setting('app.tenant', true)`. If the setting is not set, the comparison yields NULL and the query returns 0 rows.
- `acl_groups AS RESTRICTIVE FOR SELECT`: `groups && string_to_array(current_setting('app.groups', true), ',')`.
- Role `app_user`: `NOSUPERUSER NOBYPASSRLS`, DML rights on `chunks`. Seed writes as `postgres` (a superuser, bypasses RLS).

## Scripts and Makefile

| Target | Script | Verified result |
|---|---|---|
| `up` | — | `/health` answers |
| `seed` | `app.seed` | 212 points in Qdrant and 212 rows in Postgres |
| `leak` | `scripts/leak_demo.py --path /debug/search_unsafe` | 6 of 8 foreign, codes `INITECH-TPS-0042`, `GLOBEX-VIP-2026` |
| `leak-hours` | same, a question about hours | 4 of 6 foreign |
| `fixed` | `--path /search` | 0 of 8 foreign |
| `acl` | `scripts/acl_demo.py` | finance sees `ACME-FIN-7731`, support does not |
| `test` | `pytest tests` | 91 passed |
| `test-buggy` | `SEARCH_PATH=/debug/search_unsafe pytest -k search_isolation` | 60 failed, 25 passed |
| `idf` | `scripts/idf_demo.py` | top-1 changes: `acme-pallet-labels` → `acme-warehouse-pilot` |
| `tiered` | `scripts/tiered.py` | default 212 → 120, globex 92, intermediate 304 |
| `rls` | `scripts/rls_demo.py` | 0 without a tenant; 60 acme/all rows; INSERT into globex rejected; HNSW 3 rows vs. 10 |
| `offboard` | `scripts/offboard.py initech` | initech 0 in both collections, 56 rows deleted in PG |
| `down` / `clean` | — | `clean` = `down -v` |

## Tests (`tests/test_isolation.py`)

- `test_search_isolation_tenant`, `test_search_isolation_acl`: 5 tokens × 8 questions; the endpoint is set by `SEARCH_PATH`.
- `test_search_isolation_no_foreign_secret`: the results contain no foreign codes; an own code is allowed only for `finance`.
- Positive control: `test_finance_sees_own_secret`.
- `test_unauthenticated_is_rejected`, `test_spoofed_tenant_param_and_header_are_ignored`, `test_delete_is_tenant_scoped`, `test_upsert_takes_tenant_from_token_not_body`, `test_cannot_write_for_a_group_you_are_not_in`.

## Ideas for extension

- Reading by point ID with a tenant check, and an IDOR test.
- A load measurement of `m: 0` vs. `m: 16` with and without a filter (100k+ points, synthetic vectors).
- A cluster of 2–3 nodes: moving a dedicated shard to another node, `replication_factor: 2`.
- JWT instead of static tokens (claims `tenant`, `groups`) and Qdrant strict mode (`unindexed_filtering_retrieve: false`).
- A leak through a response cache: a cache key without the tenant. A similar mechanism is mentioned in secondary sources about the Asana MCP incident (not cross-checked).
