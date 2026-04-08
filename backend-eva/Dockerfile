# ---------- base ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ---------- dev stage (used by docker-compose) ----------
FROM base AS dev

# Install all dependencies including dev
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Source is volume-mounted in docker-compose, but copy for standalone builds
COPY . .

EXPOSE 8000

# Daphne dev server with auto-reload via watchfiles
CMD ["uv", "run", "daphne", "-b", "0.0.0.0", "-p", "8000", "backend_eva.asgi:application"]

# ---------- production stage ----------
FROM base AS production

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["/app/.venv/bin/daphne", "-b", "0.0.0.0", "-p", "8000", "backend_eva.asgi:application"]
