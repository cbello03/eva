#!/usr/bin/env bash
set -e

echo "⏳ Running migrations..."
uv run python manage.py migrate --no-input

echo "🌱 Seeding data..."
uv run python manage.py seed_users
uv run python manage.py seed_course

echo "🚀 Starting Daphne..."
exec uv run daphne -b 0.0.0.0 -p 8000 backend_eva.asgi:application
