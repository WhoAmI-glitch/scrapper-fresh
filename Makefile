.PHONY: install dev test lint typecheck fmt clean run-discover run-enrich run-export

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest --cov=scrapper --cov-report=term-missing

lint:
	ruff check src/ tests/

typecheck:
	mypy src/scrapper/

fmt:
	ruff check --fix src/ tests/
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache *.egg-info

run-discover:
	scrapper discover --source fake

run-enrich:
	scrapper enrich --batch-size 5

run-export:
	scrapper export --format xlsx

run-stats:
	scrapper stats

init-db:
	scrapper init-db
