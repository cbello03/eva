# EVA — Project Structure & Conventions

## Monorepo Layout

```
backend-eva/       # Django backend
frontend-eva/      # React frontend (Next.js App Router)
docs/              # Project documentation (Spanish): requisitos.md, diseno.md, tareas.md
.kiro/specs/       # Kiro spec files
```

## Backend Architecture

Django project with `backend_eva/` as the project package and `apps/` for domain apps.

```
backend-eva/
├── backend_eva/         # Django project config (settings, urls, asgi, wsgi, celery)
├── apps/                # Domain apps (each is an isolated Django app)
│   ├── accounts/        # Auth, users, roles, JWT tokens
│   ├── courses/         # Course → Unit → Lesson hierarchy, enrollment
│   ├── exercises/       # Exercise types, validation, lesson player, adaptive learning
│   ├── gamification/    # XP, levels, streaks, achievements, leaderboards
│   ├── progress/        # Student progress tracking, analytics, spaced repetition models
│   ├── social/          # Forums, real-time chat
│   ├── projects/        # Real-world projects, rubrics, peer review
│   ├── collaboration/   # Group exercises, shared workspaces
│   └── notifications/   # In-app + email notifications
├── common/              # Shared utilities (not a domain app)
│   ├── models.py        # TimestampedModel base class
│   ├── permissions.py   # Role-based permission decorators
│   ├── pagination.py    # Cursor/offset pagination
│   ├── sanitization.py  # XSS sanitization (nh3)
│   ├── rate_limiting.py # Redis-based rate limiter
│   ├── schemas.py       # Shared Pydantic schemas (ErrorResponse, FieldError)
│   └── exceptions.py    # Domain exception hierarchy (DomainError base)
└── manage.py
```

### Backend Conventions

- Service Layer Pattern: all business logic lives in `services.py`. API routes and Channels consumers are thin wrappers that validate input, call service functions, and return responses. Never access models directly from views.
- Cross-app communication happens through service layer imports, never direct model access between apps.
- Each app follows this internal structure:
  - `models.py` — Django models
  - `services.py` — Business logic
  - `schemas.py` — Pydantic request/response DTOs
  - `api.py` — Django Ninja router endpoints
  - `tasks.py` — Celery tasks (if applicable)
  - `consumers.py` — Django Channels WebSocket consumers (if applicable)
  - `admin.py` — Django admin registration
  - `tests/` — test_services.py, test_api.py, test_properties.py
- All models inherit from `common.models.TimestampedModel` (provides `created_at`, `updated_at`)
- All API routes versioned under `/api/v1/`
- Pydantic schemas for all request/response validation (Django Ninja native)
- Domain exceptions inherit from `common.exceptions.DomainError` with `status_code` and `code` attributes
- Role-based access via `@require_role()` decorator from `common.permissions`
- User-generated text content must be sanitized via `common.sanitization.sanitize_html()`
- Rate limiting via `common.rate_limiting.RateLimiter` decorator
- Settings loaded via pydantic-settings from `.env` file
- Auth uses email as USERNAME_FIELD (not username)

## Frontend Architecture

Feature-based organization with Next.js App Router and file-based routing.

```
frontend-eva/src/
├── app/                 # Next.js App Router (layouts, pages, loading states)
├── features/            # Feature modules (auth, courses, exercises, etc.)
│   └── {feature}/
│       ├── api.ts       # API calls (using apiClient)
│       ├── hooks.ts     # React hooks
│       ├── store.ts     # Zustand store (if needed)
│       ├── types.ts     # TypeScript types
│       └── components/  # Feature-specific components
├── shared/              # Shared components, hooks, utils, types
├── components/          # Layout components (Header, Footer, ThemeToggle)
└── lib/
    ├── api-client.ts    # Axios instance with JWT interceptors
    ├── providers.tsx    # QueryClient, Theme providers
    ├── theme.ts         # MUI custom theme
    └── websocket.ts     # WebSocket connection manager with reconnection
```

### Frontend Conventions

- Path aliases: `#/*` and `@/*` both map to `./src/*`
- Strict TypeScript with `verbatimModuleSyntax`
- MUI + Tailwind CSS coexist: MUI for complex components, Tailwind for utility styling
- Custom theme in `src/lib/theme.ts` with CSS custom properties for colors
- Dark mode support via `data-theme` attribute and `prefers-color-scheme` media query
- Fonts: Fraunces (serif, headings), Manrope (sans-serif, body)
- Forms: react-hook-form + Zod for validation
- Server state: TanStack Query; Client state: Zustand
- WebSocket connections managed via `WebSocketManager` class with exponential backoff reconnection
