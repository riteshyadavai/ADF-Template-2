.PHONY: install dev lint typecheck test contract integration eval openapi run docker-build clean

install:
	uv sync --all-groups

dev: install
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	uv run ruff check app agents shared factories config tests examples

typecheck:
	uv run mypy app agents shared factories config --ignore-missing-imports

test:
	uv run pytest tests -m "not integration"

contract:
	uv run pytest tests/contract tests/mcp -v

integration:
	uv run pytest tests/integration -v

eval:
	uv run pytest tests/evaluation -v

openapi:
	uv run python -c "from app.main import export_openapi; export_openapi()"

run:
	uv run factory

docker-build:
	docker build -t multi-agent-factory:latest .

clean:
	rm -rf dist data .pytest_cache .mypy_cache .ruff_cache
