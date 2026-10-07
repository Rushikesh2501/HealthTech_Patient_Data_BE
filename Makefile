.PHONY: help install dev test lint format migrate seed run-dev run-prod docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install all production and development dependencies"
	@echo "  make dev         - Run local development server with auto-reload"
	@echo "  make test        - Run test suite with pytest"
	@echo "  make lint        - Run ruff and mypy"
	@echo "  make format      - Format code with black and ruff"
	@echo "  make migrate     - Run database migrations"
	@echo "  make seed        - Seed database with clinical sample data"
	@echo "  make docker-up   - Start local services with docker-compose"
	@echo "  make docker-down - Stop local docker services"

install:
	uv pip install -e ".[dev]"

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

lint:
	ruff check .
	mypy app

format:
	black .
	ruff check . --fix

migrate:
	alembic upgrade head

seed:
	python scripts/seed_database.py

docker-up:
	docker compose -f docker-compose.dev.yml up -d

docker-down:
	docker compose -f docker-compose.dev.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
