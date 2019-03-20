.PHONY: lint-black
lint-black:
	@echo "\033[92m< linting using black...\033[0m"
	@poetry run black --check --diff .
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint-flake8
lint-flake8:
	@echo "\033[92m< linting using flake8...\033[0m"
	@poetry run flake8 aiodogstatsd example tests
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint-isort
lint-isort:
	@echo "\033[92m< linting using isort...\033[0m"
	@poetry run isort --check-only --diff --recursive .
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint-mypy
lint-mypy:
	@echo "\033[92m< linting using mypy...\033[0m"
	@poetry run mypy --ignore-missing-imports --follow-imports=silent aiodogstatsd examples tests
	@echo "\033[92m> done\033[0m"
	@echo

.PHONY: lint
lint: lint-black lint-flake8 lint-isort lint-mypy

.PHONY: test
test:
	@poetry run pytest --cov-report term --cov-report html --cov=aiodogstatsd -vv

.PHONY: publish
publish:
	@poetry publish --username=$(PYPI_USERNAME) --password=$(PYPI_PASSWORD) --build

.PHONY: ci-poetry
ci-poetry:
	@pip install poetry
	@poetry install -v

.PHONE: ci-quality
ci-quality: ci-poetry lint test

.PHONE: ci-publish
ci-publish: ci-poetry publish
