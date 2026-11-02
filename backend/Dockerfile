FROM node:26-bookworm-slim AS frontend
WORKDIR /web
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_API_MODE=live \
    NEXT_PUBLIC_API_BASE_URL=/api
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends catdoc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CAREER_FRONTEND_DIRECTORY=/app/frontend \
    PATH="/app/.venv/bin:$PATH"

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/src ./src
COPY --from=frontend /web/out ./frontend
RUN uv sync --locked --no-dev --no-editable \
    && useradd --system --uid 10001 --create-home app \
    && mkdir -p /data/documents \
    && chown app:app /data/documents \
    && chmod 700 /data/documents

USER app
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn career_assistant.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
