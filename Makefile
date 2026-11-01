UV ?= uv
BACKEND_PORT ?= 8000
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export PLAYWRIGHT_BROWSERS_PATH ?= $(CURDIR)/.cache/ms-playwright

.PHONY: setup dev up down db-up db-down test browser-install e2e lint check

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

test:
	$(UV) run --project backend --locked pytest backend/tests --ignore=backend/tests/e2e --cov=career_assistant --cov-report=term-missing

browser-install:
	$(UV) run --project backend --locked playwright install chromium

e2e:
	$(UV) run --project backend --locked pytest backend/tests/e2e --browser chromium

lint:
	$(UV) run --project backend --locked ruff check backend
	$(UV) run --project backend --locked ruff format --check backend

check: lint test
