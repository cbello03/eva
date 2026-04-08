# EVA — Tech Stack & Build

## Backend (`backend-eva/`)

- Python 3.12+, managed with `uv`
- Django 6.0 as the web framework
- Django Ninja 1.4 for REST API (Pydantic schemas, async support, OpenAPI generation)
- Django Channels + Daphne for WebSocket (chat, notifications, collaboration)
- Celery + Celery Beat for async tasks (email notifications, streak resets, leaderboard resets, analytics aggregation, spaced repetition scheduling)
- PostgreSQL via `psycopg` (psycopg3), configured directly in pydantic-settings
- Redis for Channel Layer, caching, rate limiting (sorted sets for leaderboards)
- PyJWT for JWT token handling
- pydantic-settings for environment configuration (`.env` file)
- nh3 for XSS sanitization of user-generated content (Rust-based replacement for deprecated bleach)

### Backend Dev Tools
- pytest + pytest-django for testing
- hypothesis for property-based testing
- ruff for linting
- mypy for type checking

### Backend Commands
```bash
# From backend-eva/
uv sync                          # Install dependencies
uv run python manage.py runserver  # Dev server
uv run python manage.py migrate    # Run migrations
uv run python manage.py makemigrations  # Create migrations
uv run pytest                      # Run tests
uv run ruff check .                # Lint
uv run mypy .                      # Type check
uv run celery -A backend_eva worker -l info  # Celery worker
uv run celery -A backend_eva beat -l info    # Celery beat scheduler
```

## Frontend (`frontend-eva/`)

- React 19 with TypeScript (strict mode)
- Next.js 15 with App Router for SSR and file-based routing
- TanStack Query for server state management
- Zustand for client state management
- MUI (Material UI) v7 for component library
- Tailwind CSS v4 for utility styling
- Axios for HTTP client (with interceptors for JWT refresh)
- react-hook-form + Zod v4 for form handling and validation
- Custom `WebSocketManager` class in `src/lib/websocket.ts`
- Bun as package manager (bun.lock)

### Frontend Dev Tools
- vitest for testing
- @testing-library/react for component tests
- fast-check for property-based testing
- oxlint for linting
- oxfmt for formatting

### Frontend Commands
```bash
# From frontend-eva/
bun install              # Install dependencies
bun run dev              # Dev server on port 3000
bun run build            # Production build
bun run test             # Run tests (vitest --run)
bun run lint             # Lint (oxlint)
bun run format           # Format (oxfmt)
bun run check            # Lint + format fix
```

## Infrastructure

- Docker Compose for local development (Django, React, PostgreSQL, Redis, Celery worker, Celery beat)
- Environment variables loaded from `.env` files
