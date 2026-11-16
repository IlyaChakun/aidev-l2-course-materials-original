# M2 lecture demo: PostgreSQL + pgvector vs Qdrant.
# The CLI runs in the `demo` container (python:3.12-slim + pinned requirements).
RUN = docker compose run --rm demo python demo.py

.PHONY: up build load step1 step2 step3 step4 step5 step6 all psql backup ps logs down clean

up:            ## start postgres (5441) and qdrant (6361/6362), build the CLI image
	docker compose up -d --wait postgres qdrant
	docker compose --profile cli build demo

build:
	docker compose --profile cli build demo

load:          ## chunk, embed (cached), load both databases; needs OPENAI_API_KEY on first run
	$(RUN) load

step1:         ## same data in two stores
	$(RUN) step1
step2:         ## same dense query, EXPLAIN
	$(RUN) step2
step3:         ## transaction + JOIN with business tables
	$(RUN) step3
step4:         ## filtered search: post-filter vs iterative scan vs Qdrant
	$(RUN) step4
step5:         ## hybrid: FTS + vector RRF in SQL vs Qdrant prefetch + rrf, recall@5
	$(RUN) step5
step6:         ## operational notes
	$(RUN) step6

all: up load   ## everything from scratch
	$(RUN) all

psql:          ## interactive psql inside the postgres container
	docker compose exec postgres psql -U demo -d lumen

backup:        ## pg_dump of the whole database + Qdrant snapshot, files go to data/out/
	mkdir -p data/out
	docker compose exec -T postgres pg_dump -U demo -d lumen -Fc > data/out/lumen.dump
	curl -s -X POST "http://127.0.0.1:6361/collections/lumen/snapshots?wait=true"; echo
	ls -lh data/out/lumen.dump

ps:
	docker compose ps
logs:
	docker compose logs --tail=50 postgres qdrant

down:          ## stop containers, keep volumes
	docker compose down

clean:         ## stop containers and delete volumes and outputs (embedding cache is kept)
	docker compose down -v
	rm -rf data/out
