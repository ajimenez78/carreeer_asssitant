UV ?= uv
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 3000
FRONTEND_API_BASE_URL ?= http://127.0.0.1:$(BACKEND_PORT)/api
RELEASE_IMAGE ?= career-assistant:part11
OPERATIONS_IMAGE ?= career-assistant-operations:part11
NPM ?= npm
export npm_config_cache ?= $(CURDIR)/.cache/npm
export NEXT_TELEMETRY_DISABLED ?= 1
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export PLAYWRIGHT_BROWSERS_PATH ?= $(CURDIR)/.cache/ms-playwright

.PHONY: setup dev up down db-up db-down db-init db-migrate owner storage-cleanup integration workflow-live clarity-live chat-live operations-image release-image release-check ai-smoke ai-evaluate test browser-install e2e lint check frontend-setup frontend-dev frontend-check frontend-test frontend-contract frontend-browser-install frontend-e2e frontend-preview

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

owner:
	$(UV) run --project backend --locked python -m career_assistant.db_cli owner

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

e2e: frontend-check db-up
	$(UV) run --project backend --locked pytest backend/tests/e2e --browser chromium

workflow-live: frontend-check db-up
	$(UV) run --project backend --locked pytest backend/tests/e2e/test_live_workflow.py --browser chromium --live-openai

clarity-live:
	$(UV) run --project backend --locked python backend/tests/clarity_live_check.py

chat-live:
	$(UV) run --project backend --locked python backend/tests/chat_live_check.py

operations-image:
	docker build -f backend/operations.Dockerfile -t $(OPERATIONS_IMAGE) .

release-image:
	docker build -f backend/Dockerfile -t $(RELEASE_IMAGE) .

release-check: release-image db-up
	CAREER_RELEASE_IMAGE=$(RELEASE_IMAGE) $(UV) run --project backend --locked python backend/tests/release_check.py

lint:
	$(UV) run --project backend --locked ruff check backend
	$(UV) run --project backend --locked ruff format --check backend

check: lint test

frontend-setup:
	$(NPM) --prefix frontend ci

frontend-dev:
	NEXT_PUBLIC_API_BASE_URL=$(FRONTEND_API_BASE_URL) $(NPM) --prefix frontend run dev -- --hostname 127.0.0.1 --port $(FRONTEND_PORT)

frontend-check:
	$(NPM) --prefix frontend run check

frontend-test:
	$(NPM) --prefix frontend test

frontend-contract: frontend-test
	$(UV) run --project backend --locked python frontend/tests/validate_contract.py

frontend-browser-install:
	cd frontend && $(NPM) exec playwright install chromium

frontend-e2e:
	$(NPM) --prefix frontend run test:e2e

frontend-preview:
	$(UV) run --project backend --locked python -m http.server $(FRONTEND_PORT) --bind 127.0.0.1 --directory frontend/out
