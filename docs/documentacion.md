# EVA — Documentación del Proyecto

## Descripción General

EVA (Entorno Virtual de Enseñanza-Aprendizaje) es una plataforma de aprendizaje de grado productivo inspirada en Duolingo, extendida con funcionalidades sociales, colaborativas y de aprendizaje aplicado al mundo real. Integra cuatro modelos pedagógicos: conductismo, cognitivismo, conectivismo y constructivismo.

## Modelos Pedagógicos

- Conductismo: XP, rachas, recompensas, tablas de clasificación
- Cognitivismo: progresión estructurada, aprendizaje adaptativo, repetición espaciada
- Conectivismo: foros, chat en tiempo real, interacción entre pares
- Constructivismo: ejercicios colaborativos, proyectos del mundo real con rúbricas y revisión entre pares

## Roles de Usuario

| Rol | Descripción |
|---|---|
| Estudiante | Consume cursos, completa ejercicios, gana XP |
| Profesor | Crea y gestiona cursos, revisa entregas, consulta analíticas |
| Administrador | Gestiona la plataforma, usuarios y configuración del sistema |

## Arquitectura

### Monorepo

```
backend-eva/       # Backend Django
frontend-eva/      # Frontend React (Next.js App Router)
docs/              # Documentación del proyecto
docker-compose.yml # Orquestación de servicios
```

### Stack Tecnológico

#### Backend
- Python 3.12+ con uv como gestor de paquetes
- Django 6.0 como framework web
- Django Ninja 1.4 para API REST (esquemas Pydantic, soporte async, generación OpenAPI)
- Django Channels + Daphne para WebSocket (chat, notificaciones, colaboración)
- Celery + Celery Beat para tareas asíncronas
- PostgreSQL vía psycopg3
- Redis para Channel Layer, caché, rate limiting y tablas de clasificación
- PyJWT para manejo de tokens JWT
- pydantic-settings para configuración desde `.env`
- nh3 para sanitización XSS

#### Frontend
- React 19 con TypeScript (modo estricto)
- Next.js 15 con App Router para SSR y enrutamiento basado en archivos
- TanStack Query para estado del servidor
- Zustand para estado del cliente
- MUI (Material UI) v7 para componentes
- Tailwind CSS v4 para estilos utilitarios
- Axios con interceptores para refresh de JWT
- react-hook-form + Zod v4 para formularios y validación
- WebSocketManager personalizado con reconexión exponencial

#### Infraestructura
- Docker Compose para desarrollo local (Django, React, PostgreSQL, Redis, Celery worker, Celery beat)
- Variables de entorno desde archivos `.env`

## Dominios del Backend

### Cuentas (accounts)
Autenticación basada en email con JWT. Incluye rotación de tokens y detección de replay basada en familias de tokens. Tres roles: estudiante, profesor y administrador. Registro, login, refresh y logout implementados.

### Cursos (courses)
Jerarquía de contenido: Curso → Unidad → Lección → Ejercicio. Los cursos tienen estados (borrador/publicado) y pertenecen a un profesor. Los estudiantes se inscriben mediante el modelo Enrollment.

### Ejercicios (exercises)
Cuatro tipos de ejercicio: opción múltiple, completar espacios, emparejamiento y texto libre. Cada ejercicio tiene configuración JSON flexible, dificultad y tema. El sistema incluye sesiones de lección que rastrean el progreso del estudiante y una cola de reintentos estilo Duolingo.

### Aprendizaje Adaptativo
Sistema de puntuación de dominio por tema que ajusta la dificultad de los ejercicios. Implementa repetición espaciada para programar revisiones de temas según el rendimiento del estudiante.

### Gamificación (gamification)
- XP: se otorga por respuestas correctas y completar lecciones
- Niveles: progresión basada en XP acumulado
- Rachas: días consecutivos de actividad, con reset automático vía Celery
- Logros: desbloqueables por hitos específicos
- Tablas de clasificación: globales y por curso, respaldadas por Redis sorted sets, con reset periódico

### Progreso (progress)
Seguimiento de progreso por curso y lección. Incluye mapa de calor de actividad diaria, dominio por tema y modelos de repetición espaciada. Proporciona dashboards de analíticas tanto para estudiantes como para profesores.

### Social
- Foros: hilos de discusión por curso con respuestas y votos positivos
- Chat en tiempo real: comunicación vía WebSocket dentro de cursos, con historial persistente

### Colaboración (collaboration)
Ejercicios grupales con espacios de trabajo compartidos. Los estudiantes se asignan a grupos y pueden enviar soluciones colaborativas. Incluye gestión de estado del grupo y notificaciones de actividad.

### Proyectos (projects)
Proyectos del mundo real con rúbricas detalladas y fechas límite. Soporte para entregas con archivos adjuntos. Revisión por pares opcional con asignación automática de revisores.

### Notificaciones (notifications)
Sistema dual: notificaciones in-app vía WebSocket y notificaciones por email vía Celery. Soporte para marcar como leídas y eliminación.

## Estructura del Backend

Cada app sigue esta estructura interna:
- `models.py` — Modelos Django
- `services.py` — Lógica de negocio (patrón Service Layer)
- `schemas.py` — DTOs de request/response con Pydantic
- `api.py` — Endpoints del router Django Ninja
- `tasks.py` — Tareas Celery (si aplica)
- `consumers.py` — Consumers WebSocket de Django Channels (si aplica)
- `admin.py` — Registro en Django Admin
- `tests/` — Tests organizados por capa

### Convenciones
- Toda la lógica de negocio vive en `services.py`; las rutas API y consumers son wrappers delgados
- Comunicación entre apps a través de imports del service layer
- Todos los modelos heredan de `TimestampedModel` (proporciona `created_at`, `updated_at`)
- API versionada bajo `/api/v1/`
- Excepciones de dominio heredan de `DomainError`
- Control de acceso por roles vía decorador `@require_role()`
- Contenido generado por usuarios sanitizado con `nh3`
- Rate limiting basado en Redis
- Email como campo de login (no username)

## Estructura del Frontend

```
frontend-eva/src/
├── app/           # Next.js App Router (layouts, páginas, estados de carga)
├── features/      # Módulos por funcionalidad
│   └── {feature}/
│       ├── api.ts       # Llamadas API
│       ├── hooks.ts     # React hooks
│       ├── store.ts     # Store Zustand
│       ├── types.ts     # Tipos TypeScript
│       └── components/  # Componentes específicos
├── shared/        # Componentes, hooks y utilidades compartidas
├── components/    # Componentes de layout (Header, Footer, ThemeToggle)
└── lib/
    ├── api-client.ts    # Instancia Axios con interceptores JWT
    ├── providers.tsx    # Proveedores QueryClient y Theme
    ├── theme.ts         # Tema personalizado MUI
    └── websocket.ts     # Gestor de conexiones WebSocket
```

### Convenciones
- Alias de ruta: `#/*` y `@/*` mapean a `./src/*`
- TypeScript estricto con `verbatimModuleSyntax`
- MUI + Tailwind CSS coexisten
- Soporte para modo oscuro vía atributo `data-theme`
- Fuentes: Fraunces (serif, títulos), Manrope (sans-serif, cuerpo)
- Estado del servidor: TanStack Query; Estado del cliente: Zustand

## Comandos de Desarrollo

### Backend
```bash
# Desde backend-eva/
uv sync                              # Instalar dependencias
uv run python manage.py runserver    # Servidor de desarrollo
uv run python manage.py migrate      # Ejecutar migraciones
uv run python manage.py seed_users   # Crear usuarios demo
uv run python manage.py seed_course  # Crear curso demo
uv run pytest                        # Ejecutar tests
uv run ruff check .                  # Linting
uv run mypy .                        # Verificación de tipos
```

### Frontend
```bash
# Desde frontend-eva/
bun install        # Instalar dependencias
bun run dev        # Servidor de desarrollo (puerto 3000)
bun run build      # Build de producción
bun run test       # Ejecutar tests
bun run lint       # Linting
bun run format     # Formateo
```

### Docker Compose
```bash
docker compose up --build    # Levantar todos los servicios
docker compose down          # Detener servicios
```

Al iniciar con Docker Compose, el backend ejecuta automáticamente migraciones y seeders antes de arrancar el servidor.

## Datos de Prueba

El sistema incluye seeders idempotentes que crean:

### Usuarios
| Email | Rol | Contraseña |
|---|---|---|
| student@eva.local | Estudiante | student123 |
| teacher@eva.local | Profesor | teacher123 |
| admin@eva.local | Administrador | admin123 |
| superadmin@eva.local | Administrador + Superusuario | superadmin123 |

### Curso Demo
"Introducción a la Informática con Python" — curso publicado con 3 unidades, 7 lecciones, 14 ejercicios de los 4 tipos, y 2 proyectos con rúbricas. El estudiante demo se inscribe automáticamente.
