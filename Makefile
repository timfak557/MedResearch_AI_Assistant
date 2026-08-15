.PHONY: install dev lint typecheck test test-unit test-integration download prepare ingest evaluate run mcp docker-up docker-down

install:
	pip install -r requirements.txt

lint:
	ruff check app scripts tests

format:
	ruff check --fix app scripts tests
	ruff format app scripts tests

typecheck:
	mypy app

test:
	pytest -q

test-unit:
	pytest tests/unit -q

test-integration:
	pytest tests/integration -q -m integration

download:
	python scripts/download_medquad.py

prepare:
	python scripts/prepare_medquad.py

ingest:
	python scripts/ingest_medquad.py

evaluate:
	python scripts/evaluate_rag.py

run:
	uvicorn app.main:app --reload

mcp:
	python -m app.mcp.server

docker-up:
	docker compose up -d

docker-down:
	docker compose down
