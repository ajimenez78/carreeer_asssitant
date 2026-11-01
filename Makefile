UV ?= uv
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 3000
NPM ?= npm
export npm_config_cache ?= $(CURDIR)/.cache/npm
export NEXT_TELEMETRY_DISABLED ?= 1
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export PLAYWRIGHT_BROWSERS_PATH ?= $(CURDIR)/.cache/ms-playwright

.PHONY: setup dev up down db-up db-down db-init db-migrate storage-cleanup integration ai-smoke ai-evaluate test browser-install e2e lint check frontend-setup frontend-dev frontend-check frontend-browser-install frontend-e2e frontend-preview

setup:
	$(UV) sync --project backend --locked

dev:
	$(UV) run --project backend --locked uvicorn career_assistant.main:app --host 127.0.0.1 --port $(BACKEND_PORT) --reload

up:
	docker compose up --build --wait

down:
	docker compose down

db-up:
	docker compose up --wait db

db-down:
	docker compose stop db

db-init: db-up
	$(UV) run --project backend --locked python -m career_assistant.db_cli init

db-migrate:
	$(UV) run --project backend --locked python -m career_assistant.db_cli migrate

storage-cleanup:
	$(UV) run --project backend --locked python -m career_assistant.db_cli cleanup

integration: db-up
	$(UV) run --project backend --locked pytest backend/tests/integration --cov=career_assistant --cov-report=term-missing

ai-smoke:
	$(UV) run --project backend --locked python -m career_assistant.ai_cli smoke

ai-evaluate:
	$(UV) run --project backend --locked python -m career_assistant.ai_cli evaluate

test:
	$(UV) run --project backend --locked pytest backend/tests --ignore=backend/tests/e2e --ignore=backend/tests/integration --cov=career_assistant --cov-report=term-missing

browser-install:
	$(UV) run --project backend --locked playwright install chromium

e2e:
	$(UV) run --project backend --locked pytest backend/tests/e2e --browser chromium

lint:
	$(UV) run --project backend --locked ruff check backend
	$(UV) run --project backend --locked ruff format --check backend

check: lint test

frontend-setup:
	$(NPM) --prefix frontend ci

frontend-dev:
	$(NPM) --prefix frontend run dev -- --hostname 127.0.0.1 --port $(FRONTEND_PORT)

frontend-check:
	$(NPM) --prefix frontend run check

frontend-browser-install:
	cd frontend && $(NPM) exec playwright install chromium

frontend-e2e:
	$(NPM) --prefix frontend run test:e2e

frontend-preview:
	$(UV) run --project backend --locked python -m http.server $(FRONTEND_PORT) --bind 127.0.0.1 --directory frontend/out
