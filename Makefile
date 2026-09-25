PYTHON ?= python3

.DEFAULT_GOAL := help
.PHONY: help install-dev lint format format-check typecheck test check build dist-check ci clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  make %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-dev: ## Install the package and development tools
	$(PYTHON) -m pip install -e '.[dev]'

lint: ## Run Ruff lint checks
	ruff check .

format: ## Format Python files with Ruff
	ruff format .

format-check: ## Check Ruff formatting without changing files
	ruff format --check .

typecheck: ## Run strict mypy checks
	mypy

test: ## Run the pytest suite
	pytest

check: lint format-check typecheck test ## Run lint, formatting, typing, and tests

build: ## Build sdist and wheel distributions
	$(PYTHON) -m build

dist-check: build ## Validate built distributions with Twine
	twine check dist/*

ci: check dist-check ## Run every local CI check

clean: ## Remove generated build and tool-cache files
	rm -rf build dist src/*.egg-info .mypy_cache .pytest_cache .ruff_cache .coverage coverage.xml
