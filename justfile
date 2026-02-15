# LLM Hold'Em Tournament - Task Runner
# Usage: just <recipe>

# Default recipe - show available commands
default:
    @just --list

# ──────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────

# Start both frontend and backend in development mode
dev:
    @just dev-backend &
    @just dev-frontend

# Start the backend server
dev-backend:
    cd backend && uv run uvicorn llm_holdem.main:app --reload --host 0.0.0.0 --port 8000

# Start the frontend dev server
dev-frontend:
    cd frontend && pnpm dev

# ──────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────

# Run all tests
test: test-backend test-frontend

# Run backend tests with coverage
test-backend:
    cd backend && uv run pytest

# Run backend tests without coverage enforcement (useful during development)
test-backend-no-cov:
    cd backend && uv run pytest --no-cov

# Run frontend tests
test-frontend:
    cd frontend && pnpm test

# Run frontend tests with coverage
test-frontend-cov:
    cd frontend && pnpm test:coverage

# ──────────────────────────────────────────────
# Linting & Formatting
# ──────────────────────────────────────────────

# Lint everything
lint: lint-backend lint-frontend

# Lint backend (ruff check + ty)
lint-backend:
    cd backend && uv run ruff check src tests

# Lint frontend (eslint)
lint-frontend:
    cd frontend && pnpm lint

# Format everything
format: format-backend format-frontend

# Format backend (ruff format)
format-backend:
    cd backend && uv run ruff format src tests

# Format frontend (prettier)
format-frontend:
    cd frontend && pnpm format

# Check formatting without modifying files
format-check: format-check-backend format-check-frontend

# Check backend formatting
format-check-backend:
    cd backend && uv run ruff format --check src tests

# Check frontend formatting
format-check-frontend:
    cd frontend && pnpm format:check

# ──────────────────────────────────────────────
# Installation & Setup
# ──────────────────────────────────────────────

# Install all dependencies
install: install-backend install-frontend

# Install backend dependencies
install-backend:
    cd backend && uv sync

# Install frontend dependencies
install-frontend:
    cd frontend && pnpm install

# Setup pre-commit hooks
setup-hooks:
    pre-commit install

# ──────────────────────────────────────────────
# Cleaning
# ──────────────────────────────────────────────

# Clean all generated files
clean:
    rm -rf backend/.venv
    rm -rf frontend/node_modules
    rm -rf frontend/dist
    rm -f backend/*.db
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
