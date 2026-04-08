#!/usr/bin/env bash
set -e

# Install/sync dependencies (needed because source is volume-mounted over the image)
uv sync --frozen --no-install-project

# Run migrations
uv run python manage.py migrate --noinput

# Collect static files (Django admin CSS/JS)
uv run python manage.py collectstatic --noinput

# Seed demo data (idempotent - skips if already exists)
uv run python manage.py seed_users
uv run python manage.py seed_course

# Execute the CMD passed to this entrypoint
exec "$@"
