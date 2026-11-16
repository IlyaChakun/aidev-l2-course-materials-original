# Demo 05: RAG end-to-end in n8n (n8n + Qdrant). See README.md and RUNBOOK.md.
-include .env
export

N8N_URL := http://localhost:$(or $(DEMO05_N8N_PORT),5681)
QDRANT_URL := http://localhost:$(or $(DEMO05_QDRANT_PORT),6381)
CHAT_URL := $(N8N_URL)/webhook/d05c4a70-0000-4000-8000-000000000005/chat
Q ?= How long does the invitation link stay valid when I add a new teammate?

.PHONY: help up setup ingest chat-url ask eval status logs down clean

help:
	@echo "make up       - start n8n ($(N8N_URL)) and Qdrant ($(QDRANT_URL))"
	@echo "make setup    - owner + credentials + workflows (needs OPENAI_API_KEY)"
	@echo "make ingest   - run the ingestion workflow, print point count"
	@echo "make chat-url - print the chat URL"
	@echo "make ask Q='...' - one question through the chat webhook"
	@echo "make eval     - golden set through the agent (17 questions), table to runs/"
	@echo "make status   - containers and point count"
	@echo "make down     - stop (data kept);  make clean - stop and delete volumes"

up:
	docker compose up -d
	@printf "waiting for n8n readiness"; for i in $$(seq 1 120); do \
	  [ "$$(curl -s -o /dev/null -w '%{http_code}' $(N8N_URL)/healthz/readiness)" = "200" ] && echo " ok" && exit 0; \
	  printf "."; sleep 1; done; echo " timeout"; exit 1

setup:
	@bash scripts/setup.sh

ingest:
	@bash scripts/ingest.sh

chat-url:
	@echo "UI (editor):   $(N8N_URL)  login $(or $(DEMO05_EMAIL),demo@example.com)"
	@echo "Public chat:   $(CHAT_URL)"
	@echo "Qdrant UI:     $(QDRANT_URL)/dashboard#/collections/lumen_kb"

ask:
	@curl -s -m 180 -X POST "$(CHAT_URL)" -H 'Content-Type: application/json' \
	  -d "$$(python3 -c 'import json,sys,uuid; print(json.dumps({"action":"sendMessage","sessionId":"ask-"+uuid.uuid4().hex[:8],"chatInput":sys.argv[1]}))' "$(Q)")" \
	  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("output"))'

eval:
	@python3 scripts/eval.py $(if $(ONLY),--only $(ONLY),)

status:
	@docker compose ps
	@curl -s $(QDRANT_URL)/collections/lumen_kb | python3 -c 'import json,sys; d=json.load(sys.stdin); r=d.get("result"); print("lumen_kb points:", r["points_count"] if r else d.get("status"))'

logs:
	docker compose logs --tail 50 n8n

down:
	docker compose down

clean:
	docker compose down -v
