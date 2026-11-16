# M2 demo 01: embeddings from scratch and filling Qdrant step by step.
# Qdrant runs in Docker (ports 6341/6342), Python scripts run on the host in .venv.

SHELL := /bin/bash
PY := .venv/bin/python
COMPOSE := docker compose

# Read .env if present (OPENAI_API_KEY and optional DEMO_* overrides). Never printed.
ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help setup up warm step0 step1 step2 step3 step4 step5 step6 step7 step8 step9 step10 step11 all dashboard status down clean distclean

help:
	@echo "make setup      - create .venv (Python 3.12 via uv, or python3 -m venv) and install requirements"
	@echo "make up         - start Qdrant v1.19.2 on http://localhost:6341 and wait until it is healthy"
	@echo "make warm       - precompute all embeddings into data/cache (needs OPENAI_API_KEY once)"
	@echo "make step0..11  - run one step (0: corpus and golden set, 8-9: metrics, 10: answers, 11: other embedding models)"
	@echo "                  add DEMO_EXPLAIN=1 for 'how to read this' notes (self-study), e.g. make step3 DEMO_EXPLAIN=1"
	@echo "make all        - up + steps 0-11"
	@echo "make dashboard  - open the Qdrant Web UI"
	@echo "make down       - stop Qdrant, keep the data volume"
	@echo "make clean      - stop Qdrant and delete the data volume (embedding cache stays)"
	@echo "make distclean  - clean + remove .venv"

$(PY):
	@if command -v uv >/dev/null 2>&1; then uv venv --python 3.12 .venv && uv pip install --python $(PY) -r requirements.txt; \
	else python3 -m venv .venv && $(PY) -m pip install -q -r requirements.txt; fi

setup: $(PY)

up:
	$(COMPOSE) up -d --wait

warm: $(PY)
	$(PY) warm.py

step0: $(PY) ; $(PY) step0_corpus.py
step1: $(PY) ; $(PY) step1_bm25.py
step2: $(PY) ; $(PY) step2_embeddings.py
step3: $(PY) ; $(PY) step3_bm25_vs_dense.py
step4: $(PY) ; $(PY) step4_chunking.py
step5: $(PY) ; $(PY) step5_ingest.py
step6: $(PY) ; $(PY) step6_query.py
step7: $(PY) ; $(PY) step7_reingest.py
step8: $(PY) ; $(PY) step8_eval.py
step9: $(PY) ; $(PY) step9_experiment.py
step10: $(PY) ; $(PY) step10_answers.py
step11: $(PY) ; $(PY) step11_models.py

all: up step0 step1 step2 step3 step4 step5 step6 step7 step8 step9 step10 step11

dashboard:
	open "http://localhost:6341/dashboard#/collections/lumen_demo" 2>/dev/null || xdg-open "http://localhost:6341/dashboard" 

status:
	@$(COMPOSE) ps
	@curl -s http://localhost:6341/collections/lumen_demo/points/count -H 'content-type: application/json' -d '{"exact":true}' || true; echo

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

distclean: clean
	rm -rf .venv
