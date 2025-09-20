# Makefile for Job Description Ingestion Engine

.PHONY: help install dev clean test lint format db-init db-migrate server sample-data

# Default target
help:
	@echo "Job Description Ingestion Engine - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install       Install Python dependencies"
	@echo "  dev           Install development dependencies"
	@echo "  clean         Clean up temporary files and caches"
	@echo ""
	@echo "Database:"
	@echo "  db-init       Initialize database and create tables"
	@echo "  db-migrate    Run database migrations"
	@echo "  sample-data   Create sample data for testing"
	@echo "  seed-phase2   Create Phase 2 sample data (users, translation, collaboration)"
	@echo ""
	@echo "Development:"
	@echo "  server        Start development server with auto-reload"
	@echo "  test          Run test suite"
	@echo "  lint          Run code linting"
	@echo "  format        Format code with black"
	@echo "  type-check    Run type checking with mypy"
	@echo ""
	@echo "Quality:"
	@echo "  check         Run all quality checks (lint, format, type-check)"
	@echo "  fix           Fix all auto-fixable issues"

# Installation
install:
	pip install -r requirements.txt

dev: install
	pip install pytest pytest-asyncio black flake8 mypy

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/

# Database operations
db-init:
	python scripts/init_db.py

db-migrate:
	alembic upgrade head

sample-data: db-init
	python scripts/sample_data.py

seed-phase2: db-migrate
	python scripts/seed_phase2_data.py

# Development server
server:
	python scripts/dev_server.py

# Testing
test:
	pytest tests/ -v --tb=short --no-cov --dist=no

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code quality
format:
	black src/ scripts/ --line-length 88

format-check:
	black src/ scripts/ --check --line-length 88

lint:
	flake8 src/ scripts/ --max-line-length 88 --extend-ignore E203,W503

type-check:
	mypy src/jd_ingestion --ignore-missing-imports

# Combined quality checks
check: format-check lint type-check

fix: format

# Full setup for new development environment
setup: install db-init sample-data
	@echo ""
	@echo "✅ Setup complete! You can now:"
	@echo "  - Start the server: make server"
	@echo "  - Run tests: make test"
	@echo "  - Access API docs: http://localhost:8000/api/docs"

# Docker commands (if using Docker)
docker-build:
	docker build -t jd-ingestion-engine .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Production deployment helpers
prod-install:
	pip install -r requirements.txt --no-dev

prod-check:
	python -m jd_ingestion.api.main --help

# Backup and restore (placeholder)
backup-db:
	@echo "Database backup functionality - implement based on your PostgreSQL setup"

restore-db:
	@echo "Database restore functionality - implement based on your PostgreSQL setup"