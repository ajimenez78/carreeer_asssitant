FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.14-slim

COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --no-editable \
    && useradd --system --uid 10001 --create-home app \
    && mkdir -p /data/documents \
    && chown app:app /data/documents \
    && chmod 700 /data/documents

USER app
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn career_assistant.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
