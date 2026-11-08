# All project commands in one place. Compatible with GNU Make 3.81 (macOS).
# Configuration comes from .env (if present). Secrets are never printed.

-include .env
.EXPORT_ALL_VARIABLES:

SUPPORT_DB_PATH ?= ./data/support.sqlite
M ?= 1
NAME ?= run
CMD ?= echo "set CMD=..."

PY := mcp_server/.venv/bin/python
INSPECTOR_VERSION ?= 2.13.0

.PHONY: help setup test test-m1 test-scripts test-server selfcheck db-reset db-seed db-shell \
        server-stdio server-http inspector inspector-check ide-db runlog

help:
	@echo "Targets: setup test test-m1 selfcheck db-reset db-seed db-shell server-stdio server-http"
	@echo "         inspector inspector-check ide-db runlog"

setup:
	cd mcp_server && uv venv --python 3.13 .venv -q && uv pip install --python .venv/bin/python -r requirements.txt

db-reset:
	@bash db/reset.sh

db-seed:
	@bash db/seed.sh

ide-db:
	@SUPPORT_DB_PATH=./data/ide-scenario.sqlite bash db/reset.sh && SUPPORT_DB_PATH=./data/ide-scenario.sqlite bash db/seed.sh

db-shell:
	@sqlite3 "$(SUPPORT_DB_PATH)"

test-scripts:
	python3 -m unittest scripts/test_mask_secrets.py

test-server:
	cd mcp_server && .venv/bin/python -m unittest discover -s tests -t .

selfcheck:
	cd mcp_server && .venv/bin/python selfcheck.py

server-stdio:
	@bash scripts/server-stdio.sh

server-http:
	cd mcp_server && MCP_TRANSPORT=streamable-http .venv/bin/python -m support

inspector:
	MCP_CATALOG_PATH=$$(mktemp -d)/catalog.json npx -y @modelcontextprotocol/inspector@$(INSPECTOR_VERSION) $(CURDIR)/scripts/server-stdio.sh

inspector-check:
	@bash scripts/inspector_check.sh

test: test-scripts test-server

test-m1: test

runlog:
	@bash scripts/runlog.sh "$(M)" "$(NAME)" "$(CMD)"
