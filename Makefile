POETRY ?= $(HOME)/.local/bin/poetry

.PHONY: install-poetry
install-poetry:
	@curl -sSL https://install.python-poetry.org | python -

.PHONY: install-deps
install-deps:
	@$(POETRY) install -vv --extras "aiohttp starlette"

.PHONY: install
install: install-poetry install-deps

.PHONY: lint-black
lint-black:
	@echo "\033[92m< linting using black...\033[0m"
	@$(POETRY) run black --check --diff .
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint-flake8
lint-flake8:
	@echo "\033[92m< linting using flake8...\033[0m"
	@$(POETRY) run flake8 aiodogstatsd examples tests
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint-isort
lint-isort:
	@echo "\033[92m< linting using isort...\033[0m"
	@$(POETRY) run isort --check-only --diff .
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint-mypy
lint-mypy:
	@echo "\033[92m< linting using mypy...\033[0m"
	@$(POETRY) run mypy --ignore-missing-imports --follow-imports=silent aiodogstatsd examples tests
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint
lint: lint-black lint-flake8 lint-isort lint-mypy

.PHONY: test
test:
	@$(POETRY) run pytest --cov-report=term --cov-report=html --cov-report=xml --cov=aiodogstatsd -vv $(opts)

.PHONY: publish
publish:
	@$(POETRY) publish --username=$(PYPI_USERNAME) --password=$(PYPI_PASSWORD) --build

.PHONY: docs-serve
docs-serve:
	@$(POETRY) run mkdocs serve

.PHONY: docs-build
docs-build:
	@$(POETRY) run mkdocs build
