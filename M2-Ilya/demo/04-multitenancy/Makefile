# Demo 04: multitenancy in a vector DB. All Python runs inside the 'tools' container.
DC  := docker compose
RUN := $(DC) run --rm tools

.PHONY: up seed leak leak-hours fixed acl test test-buggy offboard tiered idf rls down clean ps logs

up:          ## start qdrant, postgres, api and wait until the api answers
	$(DC) up -d --build qdrant postgres api
	@for i in $$(seq 1 40); do curl -sf http://127.0.0.1:8471/health >/dev/null && echo "api ready: http://127.0.0.1:8471" && exit 0; sleep 1; done; echo "api did not start"; $(DC) logs api | tail -20; exit 1

seed:        ## build tenant corpora, embed (cached), load qdrant + postgres
	$(RUN) -m app.seed

leak:        ## acme support user, endpoint WITHOUT tenant filter
	$(RUN) scripts/leak_demo.py --path /debug/search_unsafe

leak-hours:  ## same bug, harmless question: three tenants' support hours mixed in one context
	$(RUN) scripts/leak_demo.py --path /debug/search_unsafe --q "What are the support hours?" -k 6

fixed:       ## same user, same question, safe endpoint
	$(RUN) scripts/leak_demo.py --path /search

acl:         ## same tenant, support vs finance group
	$(RUN) scripts/acl_demo.py

test:        ## isolation tests against the safe endpoint (must pass)
	$(RUN) -m pytest -q -p no:cacheprovider tests

test-buggy:  ## the same isolation tests against the unsafe endpoint (must fail)
	-$(DC) run --rm -e SEARCH_PATH=/debug/search_unsafe tools -m pytest -q --tb=no -p no:cacheprovider tests -k search_isolation
	@echo "--- first failure in detail:"
	-$(DC) run --rm -e SEARCH_PATH=/debug/search_unsafe tools -m pytest -q -x --tb=line -p no:cacheprovider tests -k "search_isolation_tenant and acme-support" 2>&1 | grep -E "AssertionError|failed"

offboard:    ## delete tenant initech everywhere, verify counts (re-run 'make seed' to restore)
	$(RUN) scripts/offboard.py initech

tiered:      ## tiered multitenancy: shard keys + promote globex to a dedicated shard
	$(RUN) scripts/tiered.py

idf:         ## BM25 with global IDF vs per-tenant IDF (Qdrant 1.19 params.idf)
	$(RUN) scripts/idf_demo.py

rls:         ## pgvector + Row Level Security, incl. HNSW + RLS returning fewer than k
	$(RUN) scripts/rls_demo.py

ps:
	$(DC) ps
logs:
	$(DC) logs --tail 50 api

down:        ## stop containers, keep volumes and cache
	$(DC) down

clean:       ## stop and delete volumes (Qdrant + Postgres data). Embedding cache in data/ stays.
	$(DC) --profile tools down -v
