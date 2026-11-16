# M2 demo "What happens inside a vector DB" (Qdrant v1.19.2, ports 6351/6352).
# All Python runs in the `demo` container (python:3.12-slim, pinned requirements).

COMPOSE := docker compose
RUN := $(COMPOSE) run --rm demo python

.PHONY: help up build data embed load prep step1 step2 step3 step4 step5 step6 step7 all status down clean

help:
	@echo "make prep    - up + build + data + embed + load (before the lecture, ~15-20 min)"
	@echo "make step1 .. step7, make all"
	@echo "make down    - stop containers, delete Qdrant volume (data/ and cache/ stay)"
	@echo "make clean   - down + delete data/ and cache/"

up:
	$(COMPOSE) up -d --wait qdrant

build:
	$(COMPOSE) build demo

data: build
	$(RUN) scripts/prepare_data.py

# Embeds the 50 queries once (needs OPENAI_API_KEY in the environment or .env), then works offline.
embed: up
	$(RUN) -c "import sys; sys.path.insert(0, 'scripts'); from common import get_queries; l, v, s = get_queries(); print(s, v.shape)"

load: up
	$(RUN) scripts/load.py

prep: up build data embed load

step1: up ; $(RUN) scripts/step1_small.py
step2: up ; $(RUN) scripts/step2_exact_vs_hnsw.py
step3: up ; $(RUN) scripts/step3_hnsw_knobs.py
step4: up ; $(RUN) scripts/step4_quantization.py
step5: up ; $(RUN) scripts/step5_filters.py
step6: up ; $(RUN) scripts/step6_consistency.py
step7: ; $(RUN) scripts/step7_sizing.py

all: step1 step2 step3 step4 step5 step6 step7

status:
	@curl -s http://localhost:6351/collections | python3 -m json.tool

down:
	$(COMPOSE) down -v

clean: down
	rm -rf data cache
