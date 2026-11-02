FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl --fail --silent --show-error https://www.postgresql.org/media/keys/ACCC4CF8.asc \
       | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
    && . /etc/os-release \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/postgresql.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-client-18 \
    && apt-get purge -y curl gnupg && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --locked --no-dev --no-editable \
    && useradd --system --uid 10001 --create-home app
USER app
CMD ["python", "-m", "career_assistant.operations", "backup"]
