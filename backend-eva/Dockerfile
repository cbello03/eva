# ---------- build stage ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy project source
COPY . .
RUN uv sync --frozen --no-dev

# ---------- runtime stage ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the entire virtual-env + source from builder
COPY --from=builder /app /app

# Daphne listens on 8000
EXPOSE 8000

CMD ["/app/.venv/bin/daphne", "-b", "0.0.0.0", "-p", "8000", "backend_eva.asgi:application"]
