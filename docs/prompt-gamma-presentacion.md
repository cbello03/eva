# Prompt para Gamma — Presentación de EVA

Copia y pega el siguiente texto en Gamma (https://gamma.app) para generar una presentación profesional del proyecto EVA.

---

Crea una presentación profesional y visualmente atractiva en español sobre una plataforma educativa llamada EVA (Entorno Virtual de Enseñanza-Aprendizaje). La presentación debe tener un tono académico pero accesible, con un diseño moderno y limpio. Usa colores relacionados con educación y tecnología (azules, verdes, blancos). Incluye iconos y elementos visuales donde sea apropiado.

## Diapositiva 1 — Portada
Título: "EVA — Entorno Virtual de Enseñanza-Aprendizaje"
Subtítulo: "Plataforma de aprendizaje interactivo inspirada en Duolingo con funcionalidades sociales, colaborativas y de aprendizaje aplicado"
Incluir un elemento visual que represente educación digital.

## Diapositiva 2 — Problema y Motivación
Título: "¿Por qué EVA?"
Puntos clave:
- Las plataformas educativas tradicionales carecen de engagement y motivación
- Los estudiantes necesitan retroalimentación inmediata y progresión visible
- Falta de integración entre aprendizaje individual, social y colaborativo
- Necesidad de una plataforma que combine múltiples modelos pedagógicos en una sola experiencia

## Diapositiva 3 — Modelos Pedagógicos
Título: "Fundamentos Pedagógicos"
Mostrar 4 bloques o tarjetas:
1. Conductismo: XP, rachas diarias, recompensas, tablas de clasificación — motivación extrínseca mediante refuerzo positivo
2. Cognitivismo: progresión estructurada (Curso → Unidad → Lección → Ejercicio), aprendizaje adaptativo, repetición espaciada
3. Conectivismo: foros de discusión por curso, chat en tiempo real entre estudiantes, interacción social
4. Constructivismo: ejercicios colaborativos en grupo, proyectos del mundo real con rúbricas y revisión entre pares

## Diapositiva 4 — Roles de Usuario
Título: "Roles del Sistema"
Mostrar 3 columnas con iconos:
- Estudiante: consume cursos, completa ejercicios interactivos, gana XP y sube de nivel, participa en foros y chat, colabora en ejercicios grupales, entrega proyectos
- Profesor: crea y gestiona cursos con jerarquía completa, diseña ejercicios de 4 tipos diferentes, crea proyectos con rúbricas, revisa entregas, consulta analíticas de sus estudiantes
- Administrador: gestiona usuarios y roles, configura la plataforma, acceso al panel de administración Django

## Diapositiva 5 — Funcionalidades Principales
Título: "Características Clave"
Mostrar como grid o lista visual:
- Motor de ejercicios: opción múltiple, completar espacios, emparejamiento, texto libre
- Lesson Player estilo Duolingo con cola de reintentos
- Sistema de gamificación completo (XP, niveles, rachas, logros, leaderboards)
- Aprendizaje adaptativo con ajuste de dificultad por tema
- Repetición espaciada para refuerzo de conocimientos
- Foros de discusión con hilos y votos
- Chat en tiempo real vía WebSocket
- Ejercicios colaborativos con espacios de trabajo compartidos
- Proyectos del mundo real con rúbricas y revisión entre pares
- Notificaciones in-app y por email
- Dashboards de progreso y analíticas

## Diapositiva 6 — Arquitectura del Sistema
Título: "Arquitectura Técnica"
Mostrar un diagrama de arquitectura con estos componentes:
- Frontend: React 19 + Next.js 15 (App Router, SSR)
- Backend: Django 6.0 + Django Ninja (API REST)
- WebSocket: Django Channels + Daphne (chat, notificaciones, colaboración)
- Base de datos: PostgreSQL
- Caché y mensajería: Redis (Channel Layer, leaderboards, rate limiting)
- Tareas asíncronas: Celery + Celery Beat (emails, resets de rachas, repetición espaciada)
- Contenedores: Docker Compose para orquestación

## Diapositiva 7 — Stack Tecnológico
Título: "Tecnologías Utilizadas"
Dividir en dos columnas:
Backend:
- Python 3.12+, Django 6.0, Django Ninja 1.4
- Django Channels, Daphne, Celery
- PostgreSQL, Redis, PyJWT
- pytest, ruff, mypy

Frontend:
- React 19, TypeScript, Next.js 15
- TanStack Query, Zustand
- MUI v7, Tailwind CSS v4
- Axios, react-hook-form, Zod v4
- vitest, Testing Library

## Diapositiva 8 — Estructura de Contenido
Título: "Jerarquía de Contenido Educativo"
Mostrar un diagrama jerárquico:
Curso → Unidades → Lecciones → Ejercicios
Explicar que cada nivel tiene ordenamiento, y los ejercicios tienen 4 tipos con configuración JSON flexible y niveles de dificultad.

## Diapositiva 9 — Sistema de Gamificación
Título: "Gamificación y Motivación"
Mostrar elementos visuales para cada componente:
- XP: puntos por respuestas correctas y lecciones completadas
- Niveles: progresión basada en XP acumulado con umbrales configurables
- Rachas: días consecutivos de actividad, reset automático a medianoche
- Logros: insignias desbloqueables por hitos (primera lección, racha de 7 días, etc.)
- Tablas de clasificación: rankings globales y por curso, respaldados por Redis, con reset semanal/mensual

## Diapositiva 10 — Patrones de Diseño
Título: "Patrones y Convenciones"
Puntos clave:
- Service Layer Pattern: toda la lógica de negocio en services.py, API y consumers como wrappers delgados
- Comunicación entre apps vía service layer, nunca acceso directo a modelos de otras apps
- Esquemas Pydantic para validación de entrada/salida
- Excepciones de dominio con códigos HTTP y códigos de error
- Control de acceso basado en roles con decoradores
- Sanitización XSS con nh3 para contenido generado por usuarios
- Rate limiting basado en Redis

## Diapositiva 11 — Infraestructura y Despliegue
Título: "Entorno de Desarrollo"
Explicar:
- Docker Compose orquesta todos los servicios: Django, React, PostgreSQL, Redis, Celery worker, Celery beat
- Migraciones y seeders se ejecutan automáticamente al iniciar
- Datos de prueba incluyen usuarios demo (estudiante, profesor, admin, superadmin) y un curso completo de "Introducción a la Informática con Python"
- Variables de entorno gestionadas con pydantic-settings desde archivos .env

## Diapositiva 12 — Cierre
Título: "EVA — Aprender nunca fue tan interactivo"
Resumen: EVA combina lo mejor de las plataformas de aprendizaje modernas con fundamentos pedagógicos sólidos, creando una experiencia educativa completa que motiva, adapta y conecta a los estudiantes.
Incluir un call-to-action visual.
