SHELL := /bin/bash

PY_DIR := python
VENV := $(PY_DIR)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help setup setup_py setup_node dev clean test report

help:
	@echo "Targets:"
	@echo "  make dev     # install deps (if needed) and run Next.js + Python API"
	@echo "  make test   # run triage tests (45 golden tickets, multiple thresholds)"
	@echo "  make report # generate METRICS_REPORT.md (run after make test)"
	@echo "  make clean  # remove node_modules, .next, and python venv"

setup: setup_node setup_py

setup_node:
	@command -v npm >/dev/null 2>&1 || (echo "ERROR: npm not found. Install Node.js 18+." && exit 1)
	@test -d node_modules || npm install

setup_py:
	@command -v python3 >/dev/null 2>&1 || (echo "ERROR: python3 not found. Install Python 3.10+." && exit 1)
	@test -d $(VENV) || (cd $(PY_DIR) && python3 -m venv .venv)
	@$(PIP) -q install --upgrade pip
	@$(PIP) -q install -r $(PY_DIR)/requirements.txt

dev: setup
	@npm run dev

test: setup_py
	@$(PY) -m pytest $(PY_DIR)/tests/test_triage.py -v

report: test
	@$(PY) $(PY_DIR)/scripts/generate_metrics_report.py

clean:
	rm -rf node_modules .next
	rm -rf $(VENV)
	rm -rf $(PY_DIR)/__pycache__
