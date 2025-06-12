.PHONY: help install test lint format clean run docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=job_url_analyzer --cov-report=html --cov-report=term-missing

lint: ## Run linting
	poetry run ruff check .
	poetry run black --check .
	poetry run mypy src/

format: ## Format code
	poetry run black .
	poetry run ruff check --fix .

clean: ## Clean up generated files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache

run: ## Run development server
	poetry run python -m job_url_analyzer.main

migrate: ## Run database migrations
	poetry run alembic upgrade head

migrate-create: ## Create new migration
	poetry run alembic revision --autogenerate -m "$(name)"

docker-build: ## Build Docker image
	docker build -t job-analyzer .

docker-run: ## Run Docker container
	docker-compose up --build

docker-prod: ## Run production Docker setup
	docker-compose -f docker-compose.prod.yml up -d

setup-dev: install ## Setup development environment
	poetry run pre-commit install
	mkdir -p data logs

reset-db: ## Reset database
	rm -f data/job_analyzer.db
	poetry run alembic upgrade head