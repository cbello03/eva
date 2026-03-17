# Plan de Implementación: Plataforma de Aprendizaje EVA

## Descripción General

Este plan implementa la plataforma de aprendizaje EVA (Entorno Virtual de Enseñanza-Aprendizaje) siguiendo un enfoque de backend primero, luego frontend. El backend utiliza Django + Django Ninja + Django Channels + Celery, y el frontend utiliza React + TanStack Router + TanStack Query + Zustand + MUI. Todas las tareas están ordenadas de modo que cada una se construye sobre la anterior, sin código huérfano.

## Tareas

- [ ] 1. Scaffolding del proyecto e infraestructura compartida
  - [ ] 1.1 Inicializar proyecto Django del backend con UV y configurar settings
    - Crear `backend-eva/` con paquete `config/`: `settings.py` (pydantic-settings), `urls.py`, `asgi.py`, `wsgi.py`, `celery.py`
    - Configurar PostgreSQL, Redis, Celery, Django Channels en settings
    - Agregar `pyproject.toml` con todas las dependencias (django, django-ninja, channels, celery, redis, hypothesis, pytest, pytest-django, ruff, mypy, bleach, pyjwt)
    - Crear `manage.py` y paquete vacío `apps/`
    - _Requisitos: 23.2_

  - [ ] 1.2 Crear módulo de utilidades comunes
    - Crear `backend-eva/common/` con `models.py` (modelo base TimestampedModel), `permissions.py` (decoradores de permisos basados en roles para Student, Teacher, Admin), `pagination.py` (paginación por cursor/offset), `sanitization.py` (sanitización XSS usando bleach), `rate_limiting.py` (limitador de tasa basado en Redis)
    - Crear `backend-eva/common/exceptions.py` con todas las clases de excepciones de dominio: `DomainError`, `DuplicateEmailError`, `InvalidCredentialsError`, `InsufficientRoleError`, `NotEnrolledError`, `CourseNotPublishedError`, `PublishValidationError`, `RateLimitExceededError`, `FileTooLargeError`, `TooManyFilesError`
    - Crear `backend-eva/common/schemas.py` con esquemas Pydantic `ErrorResponse` y `FieldError`
    - Registrar manejador global de excepciones en Django Ninja API para subclases de DomainError
    - _Requisitos: 21.4, 21.5, 21.6_

  - [ ]* 1.3 Escribir pruebas de propiedades para limitación de tasa y sanitización XSS
    - **Propiedad 47: Aplicación de limitación de tasa** — Para cualquier IP realizando solicitudes a un endpoint con límite de tasa, las primeras N solicitudes dentro de la ventana tienen éxito (N=10 para login, N=5 para registro), la solicitud N+1 retorna 429 con encabezado Retry-After
    - **Valida: Requisitos 21.1, 21.2, 21.3**
    - **Propiedad 48: Sanitización XSS** — Para cualquier texto generado por el usuario que contenga etiquetas HTML o JavaScript, el contenido almacenado tiene los elementos peligrosos eliminados/escapados, el contenido recuperado nunca contiene etiquetas de script ejecutables
    - **Valida: Requisitos 21.5**

  - [ ] 1.4 Inicializar proyecto React del frontend con Bun y configurar herramientas
    - Crear `frontend-eva/` con scaffold Vite + React + TypeScript
    - Agregar `package.json` con todas las dependencias (react, @tanstack/react-router, @tanstack/react-query, zustand, @mui/material, react-hook-form, zod, axios, fast-check, vitest, @testing-library/react, oxlint)
    - Configurar `vite.config.ts`, `tsconfig.json`
    - Crear `src/app/` con `App.tsx`, `providers.tsx` (proveedores de QueryClient, Router, Theme), `theme.ts` (tema personalizado MUI)
    - Crear `src/lib/api-client.ts` (instancia Axios con URL base, withCredentials, placeholder de interceptores)
    - Crear `src/lib/websocket.ts` (gestor de conexión WebSocket con lógica de reconexión)
    - Crear directorio `src/shared/` para componentes, hooks, utils y tipos compartidos
    - _Requisitos: 24.1, 24.2, 24.3, 24.4, 24.5_

- [ ] 2. Punto de control — Verificar scaffolding del proyecto
  - Asegurar que ambos proyectos se inicializan sin errores, consultar al usuario si surgen dudas.

- [ ] 3. App Accounts — Autenticación y autorización
  - [ ] 3.1 Crear modelos y migraciones de la app accounts
    - Crear app `backend-eva/apps/accounts/` con `models.py`: enum `Role`, modelo `User` (extendiendo AbstractUser con email como USERNAME_FIELD, display_name, role, timezone), modelo `RefreshToken` (FK usuario, token_hash, family_id UUID, is_revoked, expires_at, índices)
    - Crear y ejecutar migraciones
    - Registrar modelos en `admin.py`
    - _Requisitos: 1.1, 4.1_

  - [ ] 3.2 Implementar esquemas de accounts
    - Crear `backend-eva/apps/accounts/schemas.py` con esquemas Pydantic: `RegisterIn` (email, password, display_name con validación), `LoginIn` (email, password), `TokenOut` (access_token), `UserOut` (id, email, display_name, role, timezone), `RoleChangeIn` (role)
    - Agregar validación de contraseña (≥8 caracteres, mayúscula, minúscula, numérico) en RegisterIn
    - _Requisitos: 1.1, 1.4, 1.5_

  - [ ] 3.3 Implementar AuthService
    - Crear `backend-eva/apps/accounts/services.py` con clase `AuthService`:
    - `register()`: validar entrada, verificar email duplicado, hashear contraseña con PBKDF2 de Django, crear User con rol Student, retornar User
    - `login()`: autenticar credenciales, generar Access_Token (JWT, 15min, incluye claim de rol) y Refresh_Token (JWT, 7 días, family_id), almacenar hash de RefreshToken, retornar TokenPair
    - `logout()`: revocar refresh token, limpiar cookie
    - `refresh_tokens()`: validar refresh token, verificar family_id para detección de replay (si se reutiliza token rotado → revocar toda la familia), emitir nuevo par de tokens con mismo family_id
    - `change_role()`: actualizar rol de usuario, invalidar todos los refresh tokens de ese usuario
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 4.1, 4.3, 4.4_

  - [ ] 3.4 Implementar rutas API de accounts
    - Crear `backend-eva/apps/accounts/api.py` con router Django Ninja:
    - `POST /auth/register` — sin auth, limitado por tasa (5/min/IP), llama a AuthService.register
    - `POST /auth/login` — sin auth, limitado por tasa (10/min/IP), llama a AuthService.login, establece Refresh_Token como cookie httpOnly segura con protección CSRF
    - `POST /auth/logout` — auth Bearer, llama a AuthService.logout, limpia cookie
    - `POST /auth/refresh` — auth Cookie, llama a AuthService.refresh_tokens
    - `GET /auth/me` — auth Bearer, retorna perfil del usuario actual
    - `PATCH /users/{id}/role` — solo Admin, llama a AuthService.change_role
    - Montar router en `config/urls.py` bajo `/api/v1/`
    - _Requisitos: 1.1, 2.1, 2.5, 2.6, 3.1, 4.2, 4.4, 4.5, 21.1, 21.2, 21.3_

  - [ ]* 3.5 Escribir pruebas de propiedades para accounts (Propiedades 1–9)
    - **Propiedad 1: El registro crea una cuenta válida** — Para cualquier entrada de registro válida, Auth_Service crea un usuario con rol Student y contraseña hasheada
    - **Valida: Requisitos 1.1, 1.3**
    - **Propiedad 2: El registro rechaza entrada inválida** — Para cualquier entrada inválida (email duplicado, formato incorrecto, contraseña débil), el registro es rechazado y el conteo de usuarios no cambia
    - **Valida: Requisitos 1.2, 1.4, 1.5**
    - **Propiedad 3: Login retorna par de tokens bien formado** — Para cualquier usuario registrado con credenciales válidas, login retorna Access_Token (15min, claim de rol) y Refresh_Token (7 días, family_id)
    - **Valida: Requisitos 2.1, 2.3, 2.4, 3.4, 4.3**
    - **Propiedad 4: Credenciales inválidas producen errores indistinguibles** — Para cualquier login con email incorrecto o contraseña incorrecta, la respuesta de error es idéntica
    - **Valida: Requisitos 2.2**
    - **Propiedad 5: Logout invalida refresh token** — Después del logout, el Refresh_Token es rechazado con 401
    - **Valida: Requisitos 2.5**
    - **Propiedad 6: Ciclo completo de rotación de tokens** — Refrescar retorna nuevos tokens, token antiguo inválido, token nuevo válido
    - **Valida: Requisitos 3.1, 3.2**
    - **Propiedad 7: Detección de replay de refresh token** — Reutilizar token rotado A invalida toda la familia incluyendo token B
    - **Valida: Requisitos 3.3**
    - **Propiedad 8: Aplicación de acceso basado en roles** — Usuario con rol incorrecto obtiene 403, rol correcto obtiene éxito
    - **Valida: Requisitos 4.2**
    - **Propiedad 9: Cambio de rol invalida tokens existentes** — Después del cambio de rol, todos los tokens previos son rechazados
    - **Valida: Requisitos 4.4**

  - [ ]* 3.6 Escribir pruebas unitarias para accounts
    - Probar registro con entradas válidas/inválidas conocidas
    - Probar login con credenciales correctas e incorrectas
    - Probar flujo de refresh de tokens y casos límite de detección de replay
    - Probar decoradores de permisos basados en roles
    - Probar limitación de tasa en endpoints de login y registro
    - _Requisitos: 1.1–1.5, 2.1–2.6, 3.1–3.4, 4.1–4.5_

- [ ] 4. Punto de control — Verificar sistema de autenticación
  - Asegurar que todas las pruebas de accounts pasan, consultar al usuario si surgen dudas.

- [ ] 5. App Courses — Gestión de cursos e inscripción
  - [ ] 5.1 Crear modelos y migraciones de la app courses
    - Crear app `backend-eva/apps/courses/` con `models.py`: `Course` (title, description, FK teacher, enum status draft/published, published_at), `Unit` (FK course, title, order, unique_together course+order), `Lesson` (FK unit, title, order, unique_together unit+order), `Enrollment` (FK student, FK course, is_active, enrolled_at, unique_together student+course)
    - Crear y ejecutar migraciones
    - Registrar modelos en `admin.py`
    - _Requisitos: 5.1, 22.1_

  - [ ] 5.2 Implementar esquemas de courses
    - Crear `backend-eva/apps/courses/schemas.py`: `CourseCreateIn`, `CourseUpdateIn`, `CourseOut` (con units/lessons anidados), `UnitCreateIn`, `UnitOut`, `LessonCreateIn`, `LessonOut`, `EnrollmentOut`, `ReorderIn`
    - _Requisitos: 5.1, 5.2, 22.4_

  - [ ] 5.3 Implementar CourseService
    - Crear `backend-eva/apps/courses/services.py` con `CourseService`:
    - `create_course()`: crear curso en borrador para el profesor
    - `update_course()`: actualizar campos del curso (solo teacher+propietario)
    - `publish_course()`: validar al menos una unidad, cada lección tiene ≥1 ejercicio, establecer status=published
    - `add_unit()` / `add_lesson()`: asignar números de orden secuenciales
    - `reorder_units()` / `reorder_lessons()`: actualizar todos los números de orden para mantener secuencia contigua
    - `list_courses()`: Estudiantes ven solo publicados; Profesores ven sus propios cursos (borrador+publicados)
    - `enroll()`: crear Enrollment, verificar duplicado, inicializar progreso vía ProgressService
    - `unenroll()`: establecer is_active=False, preservar datos de progreso
    - `list_enrollments()`: retornar cursos inscritos con porcentaje de progreso
    - _Requisitos: 5.1–5.8, 22.1–22.5_

  - [ ] 5.4 Implementar rutas API de courses
    - Crear `backend-eva/apps/courses/api.py` con router Django Ninja:
    - `GET /courses` — Bearer, listar cursos por rol
    - `POST /courses` — Teacher, crear curso
    - `GET /courses/{id}` — Bearer, detalle del curso con jerarquía
    - `PATCH /courses/{id}` — Teacher+Propietario, actualizar curso
    - `POST /courses/{id}/publish` — Teacher+Propietario, publicar con validación
    - `POST /courses/{id}/units` — Teacher+Propietario, agregar unidad
    - `PATCH /units/{id}` — Teacher+Propietario, actualizar unidad
    - `POST /units/{id}/lessons` — Teacher+Propietario, agregar lección
    - `PATCH /lessons/{id}` — Teacher+Propietario, actualizar lección
    - `POST /courses/{id}/enroll` — Student, inscribirse
    - `DELETE /courses/{id}/enroll` — Student, desinscribirse
    - `GET /enrollments` — Student, listar inscripciones con progreso
    - _Requisitos: 5.1–5.8, 22.1–22.5_

  - [ ]* 5.5 Escribir pruebas de propiedades para courses (Propiedades 10–12, 49–50)
    - **Propiedad 10: Invariante de ordenamiento de jerarquía de contenido** — Después de cualquier secuencia de agregar/eliminar/reordenar, los números de orden forman secuencia contigua desde 1
    - **Valida: Requisitos 5.3, 5.4, 5.5**
    - **Propiedad 11: Validación de publicación de curso** — La publicación falla si alguna lección tiene 0 ejercicios; tiene éxito si todas las lecciones tienen ≥1 ejercicio y existe ≥1 unidad
    - **Valida: Requisitos 5.2, 5.6**
    - **Propiedad 12: Visibilidad de curso por rol** — Estudiante ve solo publicados; Profesor ve sus propios borrador+publicados, no los borradores de otros profesores
    - **Valida: Requisitos 5.7, 5.8**
    - **Propiedad 49: Unicidad e ciclo de vida de inscripción** — Una inscripción activa por estudiante+curso; duplicado falla; desinscripción preserva progreso; reinscripción reactiva
    - **Valida: Requisitos 22.1, 22.2, 22.5**
    - **Propiedad 50: La inscripción inicializa progreso** — Nueva inscripción crea CourseProgress y LessonProgress para cada lección del curso
    - **Valida: Requisitos 22.3**

  - [ ]* 5.6 Escribir pruebas unitarias para courses
    - Probar operaciones CRUD de cursos
    - Probar casos límite de validación de publicación
    - Probar ciclo de vida de inscripción (inscribir, duplicado, desinscribir, reinscribir)
    - Probar operaciones de ordenamiento
    - _Requisitos: 5.1–5.8, 22.1–22.5_

- [ ] 6. App Exercises — Sistema de ejercicios y reproductor de lecciones
  - [ ] 6.1 Crear modelos y migraciones de la app exercises
    - Crear app `backend-eva/apps/exercises/` con `models.py`: enum `ExerciseType`, `Exercise` (FK lesson, exercise_type, question_text, order, config JSONField, difficulty 1-5, topic, is_collaborative, collab_group_size), `LessonSession` (FK student, FK lesson, current_exercise_index, retry_queue JSON, is_completed, completed_at, correct_first_attempt, total_exercises), `AnswerRecord` (FK student, FK exercise, FK session, submitted_answer JSON, is_correct, is_first_attempt, answered_at)
    - Crear y ejecutar migraciones
    - _Requisitos: 6.1, 7.1_

  - [ ] 6.2 Implementar esquemas de exercises
    - Crear `backend-eva/apps/exercises/schemas.py`: `ExerciseCreateIn` (con validación de config específica por tipo — MC: ≥2 opciones + 1 correcta; fill_blank: blank_position + accepted_answers; matching: ≥2 pares; free_text: rúbrica/respuesta_modelo), `ExerciseOut`, `AnswerIn`, `AnswerResult` (is_correct, correct_answer si es incorrecto, feedback), `LessonSessionOut` (ejercicio actual, porcentaje de progreso, cola de reintentos)
    - _Requisitos: 6.1–6.6, 7.1–7.6_

  - [ ] 6.3 Implementar ExerciseService y lógica del reproductor de lecciones
    - Crear `backend-eva/apps/exercises/services.py` con `ExerciseService`:
    - `create_exercise()`: validar config específica por tipo, asignar orden
    - `update_exercise()` / `delete_exercise()`: mantener contigüidad de orden
    - `start_lesson()`: crear LessonSession, cargar ejercicios en orden, retornar primer ejercicio
    - `submit_answer()`: evaluar respuesta (MC: coincidencia de índice; fill_blank: coincidencia insensible a mayúsculas contra accepted_answers; matching: comparación de pares), registrar AnswerRecord, si es incorrecto agregar a retry_queue, si es correcto avanzar índice, retornar feedback
    - `resume_lesson()`: cargar sesión existente, retornar estado actual
    - Manejar completación de lección: cuando todos los ejercicios + reintentos terminados, marcar completado, otorgar XP vía GamificationService, actualizar progreso vía ProgressService
    - Envíos de texto libre: almacenar para revisión del profesor, disparar notificación
    - _Requisitos: 6.1–6.7, 7.1–7.6_

  - [ ] 6.4 Implementar rutas API de exercises
    - Crear `backend-eva/apps/exercises/api.py` con router Django Ninja:
    - `POST /lessons/{id}/exercises` — Teacher+Propietario, crear ejercicio
    - `PATCH /exercises/{id}` — Teacher+Propietario, actualizar ejercicio
    - `DELETE /exercises/{id}` — Teacher+Propietario, eliminar ejercicio
    - `GET /lessons/{id}/start` — Student+Inscrito, iniciar reproductor de lección
    - `POST /exercises/{id}/submit` — Student+Inscrito, enviar respuesta
    - `GET /lessons/{id}/resume` — Student+Inscrito, reanudar lección
    - _Requisitos: 6.1–6.7, 7.1–7.6_

  - [ ]* 6.5 Escribir pruebas de propiedades para exercises (Propiedades 13–18)
    - **Propiedad 13: Validación de configuración por tipo de ejercicio** — MC necesita ≥2 opciones + 1 correcta; fill_blank necesita posición + respuestas; matching necesita ≥2 pares; free_text necesita rúbrica. Configs inválidas rechazadas
    - **Valida: Requisitos 6.2, 6.3, 6.4, 6.5**
    - **Propiedad 14: Coincidencia insensible a mayúsculas en completar espacios** — Cualquier respuesta aceptada en cualquier combinación de mayúsculas/minúsculas se evalúa como correcta
    - **Valida: Requisitos 6.3**
    - **Propiedad 15: Feedback de ejercicios auto-calificados** — Envío a MC/fill_blank/matching retorna booleano de corrección y respuesta correcta si es incorrecto
    - **Valida: Requisitos 6.6, 7.2, 7.3**
    - **Propiedad 16: Respuestas incorrectas encoladas para reintento** — Cada respuesta incorrecta aparece en la cola de reintentos; después de todos los reintentos, la lección se marca como completada
    - **Valida: Requisitos 7.3, 7.4**
    - **Propiedad 17: Cálculo de progreso de lección** — Progreso = completados/total × 100; ejercicios en cola de reintentos cuentan hacia el total pero no como completados hasta ser correctos
    - **Valida: Requisitos 7.5**
    - **Propiedad 18: Ciclo completo de guardar y reanudar sesión de lección** — Reanudar restaura estado exacto: índice de ejercicio, cola de reintentos, conteos de completación
    - **Valida: Requisitos 7.6**

  - [ ]* 6.6 Escribir pruebas unitarias para exercises
    - Probar creación y validación de cada tipo de ejercicio
    - Probar flujo del reproductor de lecciones: iniciar, responder, reintentar, completar
    - Probar almacenamiento de envío de texto libre y disparo de notificación
    - _Requisitos: 6.1–6.7, 7.1–7.6_

- [ ] 7. Punto de control — Verificar sistema de cursos y ejercicios
  - Asegurar que todas las pruebas de courses y exercises pasan, consultar al usuario si surgen dudas.

- [ ] 8. App Gamification — XP, niveles, rachas, logros, tablas de clasificación
  - [ ] 8.1 Crear modelos y migraciones de la app gamification
    - Crear app `backend-eva/apps/gamification/` con `models.py`: `GamificationProfile` (OneToOne student, total_xp, current_level, current_streak, longest_streak, last_activity_date), `XPTransaction` (FK student, amount, source_type, source_id, timestamp), `Achievement` (name unique, description, icon, condition_type, condition_value), `UserAchievement` (FK student, FK achievement, unlocked_at, unique_together student+achievement)
    - Crear y ejecutar migraciones
    - _Requisitos: 8.1, 8.5, 9.5, 10.1, 10.5_

  - [ ] 8.2 Implementar esquemas de gamification
    - Crear `backend-eva/apps/gamification/schemas.py`: `GamificationProfileOut`, `XPTransactionOut`, `AchievementOut` (con estado de desbloqueo y progreso), `LeaderboardEntryOut`, `LeaderboardOut` (entradas + rango/xp del usuario solicitante), `StreakOut`
    - _Requisitos: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.4_

  - [ ] 8.3 Implementar GamificationService
    - Crear `backend-eva/apps/gamification/services.py` con `GamificationService`:
    - `award_xp()`: crear XPTransaction, actualizar GamificationProfile.total_xp, actualizar sorted sets de Redis (tablas de clasificación semanal + histórica), verificar subida de nivel
    - `check_level_up()`: calcular umbrales de nivel usando fórmula de progresión, avanzar nivel si se cruza el umbral, enviar notificación
    - `evaluate_achievements()`: después de cada evento de XP, verificar todas las condiciones de logros contra estadísticas del estudiante, otorgar nuevos logros (idempotente — unique_together previene duplicados), enviar notificaciones
    - `update_streak()`: si last_activity_date != hoy (zona horaria del estudiante), incrementar racha, actualizar longest_streak si es necesario, verificar hitos de racha (7, 30, 100, 365), otorgar XP bonus
    - `get_leaderboard()`: leer del sorted set de Redis, retornar top 100 + rango/xp del usuario solicitante
    - _Requisitos: 8.1–8.5, 9.1, 9.4, 9.5, 10.1–10.5, 11.1–11.4_

  - [ ] 8.4 Implementar tareas Celery de gamification
    - Crear `backend-eva/apps/gamification/tasks.py`:
    - `reset_expired_streaks`: diario a las 00:00 UTC, encontrar estudiantes con last_activity_date < ayer, establecer current_streak=0
    - `reset_weekly_leaderboard`: cada lunes 00:00 UTC, limpiar sorted set semanal de Redis
    - Registrar tareas en el schedule de Celery Beat
    - _Requisitos: 9.2, 9.3, 11.5_

  - [ ] 8.5 Implementar rutas API de gamification
    - Crear `backend-eva/apps/gamification/api.py` con router Django Ninja:
    - `GET /gamification/profile` — Bearer, retornar XP, nivel, racha, logros
    - `GET /gamification/leaderboard` — Bearer, parámetro de consulta period=weekly|alltime
    - `GET /gamification/achievements` — Bearer, todos los logros con estado de desbloqueo
    - `GET /gamification/xp-history` — Bearer, registro de transacciones de XP
    - _Requisitos: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.4_

  - [ ]* 8.6 Escribir pruebas de propiedades para gamification (Propiedades 19–25)
    - **Propiedad 19: Otorgamiento de XP y registro de transacciones** — Lección completada otorga XP = f(first_attempt_correct), XPTransaction creada con cantidad correcta, source_type="lesson", source_id, timestamp
    - **Valida: Requisitos 8.1, 8.5**
    - **Propiedad 20: Progresión de niveles** — XP cruzando umbral de nivel avanza current_level exactamente por el número de umbrales cruzados, siguiendo fórmula definida
    - **Valida: Requisitos 8.2, 8.3, 8.4**
    - **Propiedad 21: Incremento de racha e invariante** — Completar lección en nuevo día calendario incrementa racha en 1; longest_streak ≥ current_streak siempre; last_activity_date = hoy
    - **Valida: Requisitos 9.1, 9.5**
    - **Propiedad 22: Reinicio de racha por inactividad** — Estudiante con last_activity_date antes de ayer obtiene current_streak=0, longest_streak preservado
    - **Valida: Requisitos 9.2**
    - **Propiedad 23: Idempotencia de otorgamiento de logros** — Otorgar el mismo logro dos veces resulta en exactamente un registro UserAchievement
    - **Valida: Requisitos 10.5**
    - **Propiedad 24: Desbloqueo de logro al cumplir condición** — Cuando las estadísticas del estudiante cumplen la condición del logro después de un evento de XP, el logro se otorga y se crea notificación
    - **Valida: Requisitos 10.2, 10.3, 9.4**
    - **Propiedad 25: Ordenamiento y completitud de tabla de clasificación** — Retorna ≤100 entradas ordenadas por XP desc; el rango del estudiante solicitante siempre incluido aunque no esté en el top 100
    - **Valida: Requisitos 11.2, 11.3**

  - [ ]* 8.7 Escribir pruebas unitarias para gamification
    - Probar otorgamiento de XP y cálculos de subida de nivel
    - Probar incremento, reinicio y detección de hitos de racha
    - Probar evaluación de logros e idempotencia
    - Probar operaciones Redis de tabla de clasificación
    - Probar tareas Celery (reinicio de racha, reinicio de tabla de clasificación)
    - _Requisitos: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.5_

- [ ] 9. Aprendizaje adaptativo — dentro de las apps exercises/progress
  - [ ] 9.1 Crear modelos y migraciones de aprendizaje adaptativo
    - Agregar a `backend-eva/apps/progress/models.py`: `TopicMastery` (FK student, topic, FK course, correct_count, total_count, mastery_score, last_reviewed, unique_together student+topic+course), `SpacedRepetitionItem` (FK student, FK exercise, next_review_date, interval_days, review_count)
    - Crear y ejecutar migraciones
    - _Requisitos: 12.1, 12.2, 12.4_

  - [ ] 9.2 Implementar AdaptiveService
    - Crear `backend-eva/apps/exercises/adaptive.py` (o dentro de services.py) con `AdaptiveService`:
    - `record_answer()`: actualizar TopicMastery para el tema del ejercicio — incrementar correct_count/total_count, recalcular mastery_score con ponderación por recencia
    - `get_mastery_scores()`: retornar puntuaciones de dominio por tema para un estudiante en un curso
    - `should_recommend_review()`: verificar si algún tema prerrequisito de una unidad tiene mastery_score < 0.6, retornar recomendación
    - `generate_review_session()`: seleccionar ejercicios de temas débiles, priorizar puntuaciones de dominio más bajas
    - `schedule_spaced_repetition()`: en respuesta incorrecta, crear SpacedRepetitionItem con next_review_date = hoy + 1 día; en revisión, progresar intervalo a través de [1, 3, 7, 14, 30]
    - `adjust_difficulty()`: después de 3 correctas consecutivas → aumentar dificultad; después de 2 incorrectas consecutivas → disminuir dificultad
    - _Requisitos: 12.1–12.6_

  - [ ] 9.3 Implementar tarea Celery de repetición espaciada
    - Crear tarea en `backend-eva/apps/progress/tasks.py`:
    - `process_spaced_repetition`: tarea diaria, encontrar SpacedRepetitionItems donde next_review_date = hoy, crear sesiones de revisión para estudiantes afectados
    - Registrar en schedule de Celery Beat
    - _Requisitos: 12.4_

  - [ ]* 9.4 Escribir pruebas de propiedades para aprendizaje adaptativo (Propiedades 26–30)
    - **Propiedad 26: Cálculo de puntuación de dominio** — Dominio = ratio ponderado correcto/total; agregar respuesta correcta nunca disminuye la puntuación; agregar incorrecta nunca la aumenta
    - **Valida: Requisitos 12.2**
    - **Propiedad 27: Umbral de recomendación de revisión** — Dominio de tema prerrequisito < 0.6 dispara recomendación de revisión; todos ≥ 0.6 significa sin recomendación
    - **Valida: Requisitos 12.3**
    - **Propiedad 28: Programación de repetición espaciada** — Respuesta incorrecta crea ítem con next_review = hoy + 1; intervalos progresan a través de [1, 3, 7, 14, 30]
    - **Valida: Requisitos 12.4**
    - **Propiedad 29: Selección de ejercicios para sesión de revisión** — Todos los ejercicios seleccionados de temas con dominio bajo el umbral; temas con menor dominio aparecen primero
    - **Valida: Requisitos 12.5**
    - **Propiedad 30: Ajuste adaptativo de dificultad** — 3 correctas consecutivas → dificultad igual o mayor siguiente; 2 incorrectas consecutivas → dificultad igual o menor siguiente
    - **Valida: Requisitos 12.6**

  - [ ]* 9.5 Escribir pruebas unitarias para aprendizaje adaptativo
    - Probar cálculo de puntuación de dominio con secuencias específicas de respuestas
    - Probar lógica de recomendación de revisión
    - Probar progresión de intervalos de repetición espaciada
    - Probar umbrales de ajuste de dificultad
    - _Requisitos: 12.1–12.6_

- [ ] 10. Punto de control — Verificar gamification y aprendizaje adaptativo
  - Asegurar que todas las pruebas de gamification y aprendizaje adaptativo pasan, consultar al usuario si surgen dudas.

- [ ] 11. App Social — Foros y chat en tiempo real
  - [ ] 11.1 Crear modelos y migraciones de la app social
    - Crear app `backend-eva/apps/social/` con `models.py`: `ForumThread` (FK course, FK author, title, body, is_hidden, last_activity_at), `ForumReply` (FK thread, FK author, body, is_hidden, upvote_count), `ReplyUpvote` (FK reply, FK user, unique_together reply+user), `ChatMessage` (FK course, FK author, content max 2000, sent_at)
    - Crear y ejecutar migraciones
    - _Requisitos: 13.1, 13.2, 14.1, 14.4_

  - [ ] 11.2 Implementar esquemas de social
    - Crear `backend-eva/apps/social/schemas.py`: `ThreadCreateIn`, `ThreadOut`, `ReplyCreateIn`, `ReplyOut` (con upvote_count), `ChatMessageOut`, `ThreadListOut` (paginado, 20 por página)
    - _Requisitos: 13.2, 13.4, 14.3_

  - [ ] 11.3 Implementar SocialService (foros)
    - Crear `backend-eva/apps/social/services.py` con `ForumService`:
    - `create_thread()`: requerir título + cuerpo, asociar con curso y autor, sanitizar contenido
    - `list_threads()`: retornar hilos ordenados por last_activity_at desc, paginados 20/página
    - `create_reply()`: agregar respuesta, actualizar last_activity_at del hilo, notificar al autor del hilo vía NotificationService, sanitizar contenido
    - `flag_post()`: solo Teacher/Admin, establecer is_hidden=True, notificar al autor de la publicación
    - `toggle_upvote()`: crear/eliminar ReplyUpvote, actualizar upvote_count
    - _Requisitos: 13.1–13.6_

  - [ ] 11.4 Implementar consumer WebSocket de chat
    - Crear `backend-eva/apps/social/consumers.py` con `ChatConsumer` (Django Channels):
    - `connect()`: autenticar JWT desde parámetro de consulta, verificar inscripción en curso, unirse al grupo de canal, enviar últimos 50 mensajes como historial
    - `receive()`: validar mensaje, persistir ChatMessage en BD, difundir al grupo
    - `disconnect()`: abandonar grupo de canal
    - Configurar enrutamiento en `config/asgi.py`
    - _Requisitos: 14.1–14.6_

  - [ ] 11.5 Implementar rutas API de social
    - Crear `backend-eva/apps/social/api.py` con router Django Ninja:
    - `GET /courses/{id}/forum/threads` — Bearer+Inscrito, lista paginada de hilos
    - `POST /courses/{id}/forum/threads` — Bearer+Inscrito, crear hilo
    - `GET /forum/threads/{id}` — Bearer+Inscrito, detalle del hilo con respuestas
    - `POST /forum/threads/{id}/replies` — Bearer+Inscrito, responder al hilo
    - `POST /forum/posts/{id}/flag` — Teacher|Admin, marcar publicación
    - `POST /forum/replies/{id}/upvote` — Bearer+Inscrito, alternar voto positivo
    - _Requisitos: 13.1–13.6_

  - [ ]* 11.6 Escribir pruebas de propiedades para social (Propiedades 31–35)
    - **Propiedad 31: Ordenamiento de hilos del foro** — Hilos ordenados por last_activity_at desc; agregar respuesta mueve el hilo al inicio
    - **Valida: Requisitos 13.4**
    - **Propiedad 32: Marcado de publicación del foro oculta contenido** — Publicación marcada no aparece en listados públicos; autor notificado
    - **Valida: Requisitos 13.5**
    - **Propiedad 33: Historial de chat al conectar** — Conectarse entrega min(N, 50) mensajes más recientes en orden cronológico
    - **Valida: Requisitos 14.3**
    - **Propiedad 34: Ciclo completo de persistencia de mensaje de chat** — Mensaje enviado persistido en BD; consulta retorna contenido, autor, curso coincidentes
    - **Valida: Requisitos 14.4**
    - **Propiedad 35: Aplicación de inscripción en sala de chat** — Usuario no inscrito rechazado; usuario inscrito se conecta exitosamente
    - **Valida: Requisitos 14.5**

  - [ ]* 11.7 Escribir pruebas unitarias para social
    - Probar CRUD de foro, paginación, marcado
    - Probar comportamiento de alternancia de voto positivo
    - Probar flujo de connect/disconnect/message del consumer de chat
    - Probar aplicación de inscripción en WebSocket
    - _Requisitos: 13.1–13.6, 14.1–14.6_

- [ ] 12. App Projects — Proyectos del mundo real y revisión por pares
  - [ ] 12.1 Crear modelos y migraciones de la app projects
    - Crear app `backend-eva/apps/projects/` con `models.py`: `Project` (FK course, FK teacher, title, description, rubric JSON, submission_deadline, peer_review_enabled, peer_reviewers_count default 2), `ProjectSubmission` (FK project, FK student, description, is_late, submitted_at, unique_together project+student), `SubmissionFile` (FK submission, file FileField, filename, file_size), `ProjectReview` (FK submission, FK reviewer, review_type teacher/peer, scores JSON, feedback, is_complete), `PeerReviewAssignment` (FK submission, FK reviewer, is_completed, unique_together submission+reviewer)
    - Crear y ejecutar migraciones
    - _Requisitos: 18.1–18.6_

  - [ ] 12.2 Implementar esquemas de projects
    - Crear `backend-eva/apps/projects/schemas.py`: `ProjectCreateIn` (title, description, rubric, deadline, peer_review_enabled), `ProjectOut`, `SubmissionOut`, `ReviewIn` (puntuaciones por criterio, feedback), `ReviewOut`, `PeerReviewAssignmentOut`
    - Validar restricciones de archivos: máximo 10MB por archivo, máximo 5 archivos
    - _Requisitos: 18.1, 18.2_

  - [ ] 12.3 Implementar ProjectService
    - Crear `backend-eva/apps/projects/services.py` con `ProjectService`:
    - `create_project()`: crear proyecto con rúbrica y fecha límite
    - `submit_project()`: aceptar archivos (máximo 10MB cada uno, máximo 5), descripción de texto, marcar como tardío si es después de la fecha límite
    - `teacher_review()`: puntuar cada criterio de la rúbrica, proporcionar feedback
    - `assign_peer_reviews()`: después de la fecha límite, asignar cada envío a 2 otros estudiantes (sin auto-revisión)
    - `submit_peer_review()`: registrar puntuaciones y feedback, marcar asignación como completa
    - `get_reviews()`: retornar revisiones; revisiones de pares visibles solo cuando todas las revisiones asignadas están completas
    - _Requisitos: 18.1–18.6_

  - [ ] 12.4 Implementar rutas API de projects
    - Crear `backend-eva/apps/projects/api.py` con router Django Ninja:
    - `POST /projects` — Teacher, crear proyecto
    - `GET /projects/{id}` — Bearer+Inscrito, detalle del proyecto
    - `POST /projects/{id}/submit` — Student+Inscrito, envío multipart
    - `POST /submissions/{id}/review` — Teacher, revisión del profesor
    - `POST /submissions/{id}/peer-review` — Student, revisión por pares
    - `GET /submissions/{id}/reviews` — Bearer, obtener revisiones
    - _Requisitos: 18.1–18.6_

  - [ ]* 12.5 Escribir pruebas de propiedades para projects (Propiedades 41–43)
    - **Propiedad 41: Marcado de envío tardío de proyecto** — Si submitted_at > deadline, is_late=True; si ≤ deadline, is_late=False
    - **Valida: Requisitos 18.3**
    - **Propiedad 42: Asignación de revisión por pares** — Con peer_review_enabled y N≥3 envíos, cada uno obtiene exactamente peer_reviewers_count revisores; sin auto-revisión
    - **Valida: Requisitos 18.5**
    - **Propiedad 43: Visibilidad de revisión por pares** — Revisiones visibles para el autor solo cuando todas las revisiones asignadas están completas
    - **Valida: Requisitos 18.6**

  - [ ]* 12.6 Escribir pruebas unitarias para projects
    - Probar creación y validación de proyectos
    - Probar envío con restricciones de archivos
    - Probar detección de envío tardío
    - Probar algoritmo de asignación de revisión por pares
    - Probar reglas de visibilidad de revisiones
    - _Requisitos: 18.1–18.6_

- [ ] 13. App Collaboration — Ejercicios grupales y espacios de trabajo compartidos
  - [ ] 13.1 Crear modelos y migraciones de la app collaboration
    - Crear app `backend-eva/apps/collaboration/` con `models.py`: `CollabGroup` (FK exercise, max_size, workspace_state JSON, is_submitted), `CollabGroupMember` (FK group, FK student, joined_at, last_contribution_at, unique_together group+student), `CollabSubmission` (FK group, submitted_answer JSON, submitted_at)
    - Crear y ejecutar migraciones
    - _Requisitos: 17.1, 17.2_

  - [ ] 13.2 Implementar CollaborationService
    - Crear `backend-eva/apps/collaboration/services.py` con `CollaborationService`:
    - `join_exercise()`: encontrar grupo con espacios disponibles (miembros < max_size) o crear nuevo grupo, agregar estudiante como miembro
    - `submit_group_work()`: registrar CollabSubmission, otorgar XP igual a todos los miembros del grupo vía GamificationService
    - `get_group_info()`: retornar miembros del grupo, estado del espacio de trabajo
    - `check_inactive_members()`: encontrar miembros sin contribución en 48 horas, notificar al miembro + profesor
    - _Requisitos: 17.1–17.5_

  - [ ] 13.3 Implementar consumer WebSocket de colaboración
    - Crear `backend-eva/apps/collaboration/consumers.py` con `CollabConsumer`:
    - `connect()`: autenticar JWT, verificar membresía en grupo, unirse al grupo de canal para exercise+group
    - `receive()`: actualizar workspace_state, difundir a miembros del grupo, actualizar last_contribution_at
    - `disconnect()`: abandonar grupo de canal
    - Configurar enrutamiento en `config/asgi.py`
    - _Requisitos: 17.3_

  - [ ] 13.4 Implementar rutas API de collaboration
    - Crear `backend-eva/apps/collaboration/api.py` con router Django Ninja:
    - `POST /exercises/{id}/collab/join` — Student+Inscrito, unirse a ejercicio colaborativo
    - `POST /collab/groups/{id}/submit` — Student+MiembroGrupo, enviar trabajo grupal
    - `GET /collab/groups/{id}` — Student+MiembroGrupo, obtener info del grupo y estado del espacio de trabajo
    - _Requisitos: 17.1–17.5_

  - [ ] 13.5 Implementar tarea Celery de collaboration
    - Crear `backend-eva/apps/collaboration/tasks.py`:
    - `check_inactive_collab_members`: tarea periódica, encontrar miembros de grupo con last_contribution_at > 48 horas desde inicio del ejercicio, notificar vía NotificationService
    - _Requisitos: 17.5_

  - [ ]* 13.6 Escribir pruebas de propiedades para collaboration (Propiedades 39–40)
    - **Propiedad 39: Asignación de grupo colaborativo** — Estudiante asignado a grupo con espacios disponibles; si no hay, se crea nuevo grupo; ningún grupo excede max_size
    - **Valida: Requisitos 17.2**
    - **Propiedad 40: Envío colaborativo otorga XP igual** — Cada miembro del grupo recibe XPTransaction con la misma cantidad
    - **Valida: Requisitos 17.4**

  - [ ]* 13.7 Escribir pruebas unitarias para collaboration
    - Probar asignación de grupo con varias disponibilidades de espacios
    - Probar envío grupal y distribución de XP
    - Probar actualizaciones de espacio de trabajo por WebSocket
    - Probar detección de miembros inactivos
    - _Requisitos: 17.1–17.5_

- [ ] 14. App Notifications — Notificaciones in-app y por email
  - [ ] 14.1 Crear modelos y migraciones de la app notifications
    - Crear app `backend-eva/apps/notifications/` con `models.py`: `Notification` (FK recipient, notification_type, title, body, data JSON, enum channel in_app/email/both, is_read, email_sent)
    - Crear y ejecutar migraciones
    - _Requisitos: 19.1_

  - [ ] 14.2 Implementar NotificationService
    - Crear `backend-eva/apps/notifications/services.py` con `NotificationService`:
    - `create_notification()`: crear registro Notification, despachar a canales configurados
    - `send_in_app()`: enviar vía WebSocket al canal de notificaciones del usuario
    - `get_notifications()`: lista paginada para el usuario
    - `get_unread_count()`: conteo desde BD (cacheado en Redis)
    - `mark_read()`: actualizar is_read, decrementar conteo de no leídos en Redis
    - `mark_all_read()`: actualización masiva, reiniciar conteo en Redis
    - _Requisitos: 19.1–19.5_

  - [ ] 14.3 Implementar consumer WebSocket de notificaciones
    - Crear `backend-eva/apps/notifications/consumers.py` con `NotificationConsumer`:
    - `connect()`: autenticar JWT, unirse al grupo de canal específico del usuario
    - Entrega en tiempo real: cuando se crea notificación, enviar al WebSocket del usuario si está conectado
    - `disconnect()`: abandonar grupo de canal
    - Configurar enrutamiento en `config/asgi.py`
    - _Requisitos: 19.3_

  - [ ] 14.4 Implementar tareas Celery de notificaciones
    - Crear `backend-eva/apps/notifications/tasks.py`:
    - `send_email_notification`: enviar email para notificaciones con channel=email|both, política de reintentos: 3 intentos con backoff exponencial
    - Configurar `autoretry_for`, `retry_backoff=True`, `max_retries=3`, `retry_backoff_max=300`
    - _Requisitos: 19.6_

  - [ ] 14.5 Implementar rutas API de notifications
    - Crear `backend-eva/apps/notifications/api.py` con router Django Ninja:
    - `GET /notifications` — Bearer, lista paginada de notificaciones
    - `GET /notifications/unread-count` — Bearer, conteo de no leídas
    - `POST /notifications/{id}/read` — Bearer, marcar como leída
    - `POST /notifications/read-all` — Bearer, marcar todas como leídas
    - _Requisitos: 19.1–19.5_

  - [ ]* 14.6 Escribir prueba de propiedades para notifications (Propiedad 44)
    - **Propiedad 44: Consistencia del conteo de no leídas** — Conteo de no leídas = conteo de registros Notification donde is_read=False; marcar como leída decrementa exactamente en 1
    - **Valida: Requisitos 19.4, 19.5**

  - [ ]* 14.7 Escribir pruebas unitarias para notifications
    - Probar creación de notificación para cada tipo de evento
    - Probar entrega por WebSocket
    - Probar comportamiento de reintentos de tarea de email
    - Probar marcar como leída / marcar todas como leídas
    - _Requisitos: 19.1–19.6_

- [ ] 15. Punto de control — Verificar collaboration y notifications
  - Asegurar que todas las pruebas de collaboration y notifications pasan, consultar al usuario si surgen dudas.

- [ ] 16. App Progress — Seguimiento de progreso del estudiante y analíticas del profesor
  - [ ] 16.1 Crear modelos y migraciones de la app progress
    - Crear app `backend-eva/apps/progress/` con `models.py`: `CourseProgress` (FK student, FK course, completion_percentage, total_score, lessons_completed, total_lessons, unique_together student+course), `LessonProgress` (FK student, FK lesson, is_completed, score, completed_at, unique_together student+lesson), `DailyActivity` (FK student, date, lessons_completed, xp_earned, time_spent_minutes, unique_together student+date)
    - Nota: `TopicMastery` y `SpacedRepetitionItem` ya creados en la tarea 9.1
    - Crear y ejecutar migraciones
    - _Requisitos: 20.1–20.5, 16.1–16.5_

  - [ ] 16.2 Implementar ProgressService
    - Crear `backend-eva/apps/progress/services.py` con `ProgressService`:
    - `initialize_course_progress()`: crear CourseProgress + LessonProgress para cada lección del curso
    - `update_lesson_progress()`: marcar lección completada, actualizar puntuación, recalcular completion_percentage de CourseProgress
    - `get_dashboard()`: retornar total_xp, current_level, current_streak, courses_enrolled, courses_completed (desde GamificationProfile + registros Enrollment)
    - `get_course_progress()`: retornar completación y puntuación por unidad, por lección
    - `get_activity_heatmap()`: retornar últimos 90 días de DailyActivity, rellenar días faltantes con ceros
    - `get_mastery_scores()`: retornar datos de TopicMastery por tema
    - _Requisitos: 20.1–20.5_

  - [ ] 16.3 Implementar AnalyticsService (analíticas del profesor)
    - Crear `backend-eva/apps/progress/analytics.py` con `AnalyticsService`:
    - `get_course_analytics()`: total inscritos, tasa promedio de completación, puntuación promedio, tiempo promedio por lección
    - `get_student_list()`: porcentaje de progreso por estudiante, puntuación, racha, última actividad
    - `get_student_detail()`: estado de completación y puntuación por unidad y lección
    - `get_performance_heatmap()`: tasas de precisión de ejercicios por temas
    - _Requisitos: 16.1–16.4_

  - [ ] 16.4 Implementar tarea Celery de analíticas
    - Crear tarea en `backend-eva/apps/progress/tasks.py`:
    - `aggregate_analytics`: tarea horaria, pre-computar estadísticas agregadas para el dashboard del profesor
    - Registrar en schedule de Celery Beat
    - _Requisitos: 16.5_

  - [ ] 16.5 Implementar rutas API de progress y analytics
    - Crear `backend-eva/apps/progress/api.py` con router Django Ninja:
    - Endpoints de progreso del estudiante:
      - `GET /progress/dashboard` — Student, estadísticas generales
      - `GET /progress/courses/{id}` — Student+Inscrito, detalle por curso
      - `GET /progress/activity` — Student, mapa de calor de actividad de 90 días
      - `GET /progress/mastery` — Student, puntuaciones de dominio por tema
    - Endpoints de analíticas del profesor:
      - `GET /teacher/courses/{id}/analytics` — Teacher+Propietario, estadísticas agregadas
      - `GET /teacher/courses/{id}/students` — Teacher+Propietario, lista de estudiantes
      - `GET /teacher/courses/{id}/students/{sid}` — Teacher+Propietario, detalle del estudiante
      - `GET /teacher/courses/{id}/heatmap` — Teacher+Propietario, mapa de calor de precisión
    - _Requisitos: 20.1–20.5, 16.1–16.5_

  - [ ]* 16.6 Escribir pruebas de propiedades para progress y analytics (Propiedades 36–38, 45–46)
    - **Propiedad 36: Completitud de lista de cursos del dashboard del profesor** — Todos los cursos del profesor incluidos con estado correcto, conteo de inscripciones, fecha de última modificación
    - **Valida: Requisitos 15.1**
    - **Propiedad 37: Precisión de agregados de analíticas del profesor** — Estadísticas agregadas (total inscritos, promedio completación, promedio puntuación) matemáticamente consistentes con registros subyacentes
    - **Valida: Requisitos 16.1**
    - **Propiedad 38: Consistencia de detalle de progreso del estudiante** — Vista detallada por unidad/lección coincide con registros reales de LessonProgress
    - **Valida: Requisitos 16.2, 16.3**
    - **Propiedad 45: Consistencia del dashboard de progreso del estudiante** — Dashboard total_xp, current_level, current_streak coinciden con GamificationProfile; courses_enrolled/completed coinciden con registros Enrollment
    - **Valida: Requisitos 20.1**
    - **Propiedad 46: Rango de datos del mapa de calor de actividad** — Retorna exactamente 90 días calendario, una entrada por día, valores cero para días inactivos
    - **Valida: Requisitos 20.4**

  - [ ]* 16.7 Escribir pruebas unitarias para progress y analytics
    - Probar inicialización de progreso al inscribirse
    - Probar actualizaciones de completación de lección
    - Probar agregación de datos del dashboard
    - Probar cálculos de analíticas del profesor
    - Probar generación de datos del mapa de calor
    - _Requisitos: 20.1–20.5, 16.1–16.5_

- [ ] 17. Punto de control — Verificar progress y analytics
  - Asegurar que todas las pruebas de progress y analytics pasan, consultar al usuario si surgen dudas.

- [ ] 18. Integración del backend — Conectar todas las apps y configurar ASGI/Celery
  - [ ] 18.1 Configurar enrutamiento ASGI para todos los consumers WebSocket
    - Actualizar `backend-eva/config/asgi.py` para incluir todas las rutas WebSocket:
    - `ws/chat/{course_id}/` → ChatConsumer
    - `ws/notifications/` → NotificationConsumer
    - `ws/collab/{exercise_id}/{group_id}/` → CollabConsumer
    - Agregar middleware de autenticación JWT para conexiones WebSocket
    - _Requisitos: 14.1, 17.3, 19.3_

  - [ ] 18.2 Configurar schedule de Celery Beat con todas las tareas periódicas
    - Actualizar `backend-eva/config/celery.py` con schedule completo de beat:
    - Reinicio de rachas: diario 00:00 UTC
    - Reinicio de tabla de clasificación: semanal lunes 00:00 UTC
    - Agregación de analíticas: horaria
    - Programador de repetición espaciada: diario
    - Verificación de miembros inactivos de colaboración: periódica
    - _Requisitos: 9.2, 9.3, 11.5, 12.4, 16.5, 17.5_

  - [ ] 18.3 Montar todos los routers API en la configuración raíz de URLs
    - Actualizar `backend-eva/config/urls.py` para montar todos los routers de apps bajo `/api/v1/`:
    - accounts, courses, exercises, gamification, progress, social, projects, collaboration, notifications
    - Configurar middleware CORS permitiendo solo el origen del frontend configurado
    - _Requisitos: 21.6_

  - [ ]* 18.4 Escribir pruebas de integración del backend
    - Probar flujos entre apps: inscripción → inicio de lección → respuesta → otorgamiento de XP → verificación de logros → notificación
    - Probar autenticación WebSocket y aplicación de inscripción
    - _Requisitos: 7.4, 8.1, 10.3, 19.2_

- [ ] 19. Punto de control — Verificar integración completa del backend
  - Asegurar que todas las pruebas del backend pasan, consultar al usuario si surgen dudas.

- [ ] 20. Frontend — Módulo de autenticación y cliente API
  - [ ] 20.1 Implementar cliente API con interceptor de refresh de tokens
    - Completar `frontend-eva/src/lib/api-client.ts`:
    - Instancia Axios con baseURL `/api/v1`, withCredentials: true
    - Interceptor de solicitud: adjuntar Access_Token del store Zustand como encabezado Bearer
    - Interceptor de respuesta: en 401, llamar a `/auth/refresh` (cookie), actualizar store Zustand, reintentar solicitud original una vez; en segundo 401, redirigir a login
    - Manejar 403 (notificación de acceso denegado), 429 (notificación de retry-after), 5xx (error genérico)
    - _Requisitos: 24.2, 24.7, 24.8_

  - [ ] 20.2 Implementar store Zustand de auth y hooks
    - Crear `frontend-eva/src/features/auth/store.ts`: store Zustand con accessToken (solo en memoria), objeto user, isAuthenticated, setAccessToken, setUser, logout
    - Crear `frontend-eva/src/features/auth/api.ts`: funciones API login, register, logout, refreshToken, getMe
    - Crear `frontend-eva/src/features/auth/hooks.ts`: hooks `useAuth()`, `useUser()`, `useLogin()`, `useRegister()`, `useLogout()` usando mutaciones de TanStack Query
    - _Requisitos: 24.3, 24.7_

  - [ ] 20.3 Implementar páginas de auth (Login, Registro)
    - Crear `frontend-eva/src/routes/login.tsx`: formulario de login con React Hook Form + validación Zod, campos email + password, visualización de errores, redirección al tener éxito
    - Crear `frontend-eva/src/routes/register.tsx`: formulario de registro con email, password, display_name, validación de fortaleza de contraseña coincidiendo con reglas del backend
    - Crear `frontend-eva/src/features/auth/components/` con componentes de formulario
    - _Requisitos: 1.1, 1.4, 1.5, 2.1, 24.1_

  - [ ]* 20.4 Escribir pruebas de propiedades del frontend para auth (Propiedades 51–52)
    - **Propiedad 51: Almacenamiento de access token solo en memoria del frontend** — Después del login, Access_Token existe solo en el store Zustand; localStorage y sessionStorage no contienen valores de token
    - **Valida: Requisitos 24.7**
    - **Propiedad 52: Refresh automático de token en 401** — En respuesta 401, el cliente API llama al endpoint de refresh, actualiza el store Zustand, reintenta la solicitud original exactamente una vez
    - **Valida: Requisitos 24.8**

  - [ ]* 20.5 Escribir pruebas unitarias para la funcionalidad de auth
    - Probar transiciones de estado del store Zustand
    - Probar comportamiento del interceptor del cliente API
    - Probar validación de formularios de login/registro
    - _Requisitos: 24.7, 24.8_

- [ ] 21. Frontend — Shell de la aplicación, enrutamiento y layout
  - [ ] 21.1 Configurar TanStack Router con enrutamiento basado en archivos
    - Crear `frontend-eva/src/routes/__root.tsx`: layout raíz con React Suspense, MUI ThemeProvider, barra de navegación, indicador de notificaciones
    - Crear `frontend-eva/src/routes/index.tsx`: página de inicio
    - Configurar guardias de ruta para rutas autenticadas/basadas en roles
    - Configurar React Suspense con indicadores de carga como fallback para todos los componentes a nivel de ruta
    - _Requisitos: 24.1, 24.6_

  - [ ] 21.2 Implementar gestor de conexión WebSocket
    - Completar `frontend-eva/src/lib/websocket.ts`:
    - Clase WebSocket con auth JWT vía parámetro de consulta
    - Reconexión automática con backoff exponencial (1s, 2s, 4s, 8s, máx 30s)
    - Cola de mensajes para mensajes durante reconexión, vaciada al reconectar
    - Detección de conexión obsoleta vía ping/pong (intervalo de 30s)
    - _Requisitos: 14.6, 19.3_

  - [ ] 21.3 Implementar módulo de notificaciones
    - Crear `frontend-eva/src/features/notifications/api.ts`: getNotifications, getUnreadCount, markRead, markAllRead
    - Crear `frontend-eva/src/features/notifications/hooks.ts`: `useNotifications()`, `useUnreadCount()`, `useMarkRead()`
    - Crear `frontend-eva/src/features/notifications/components/`: NotificationBell (con badge de conteo de no leídas), NotificationList, NotificationItem
    - Conectar a WebSocket `ws/notifications/` para entrega en tiempo real
    - _Requisitos: 19.1–19.5_

- [ ] 22. Frontend — Navegación de cursos e inscripción
  - [ ] 22.1 Implementar módulo de cursos
    - Crear `frontend-eva/src/features/courses/api.ts`: listCourses, getCourse, enrollInCourse, unenrollFromCourse, listEnrollments
    - Crear `frontend-eva/src/features/courses/hooks.ts`: `useCourses()`, `useCourse()`, `useEnroll()`, `useUnenroll()`, `useEnrollments()`
    - Crear `frontend-eva/src/features/courses/types.ts`: tipos TypeScript Course, Unit, Lesson, Enrollment
    - _Requisitos: 5.7, 22.1, 22.4_

  - [ ] 22.2 Implementar páginas de cursos
    - Crear `frontend-eva/src/routes/courses/index.tsx`: página de listado de cursos con búsqueda/filtro, estado de inscripción
    - Crear `frontend-eva/src/routes/courses/$courseId.tsx`: página de detalle del curso con jerarquía unidad/lección, botón inscribir/desinscribir, visualización de progreso
    - Crear `frontend-eva/src/features/courses/components/`: CourseCard, CourseList, UnitAccordion, LessonItem
    - _Requisitos: 5.7, 22.1, 22.4, 24.4, 24.5_

- [ ] 23. Frontend — Reproductor de lecciones (estilo Duolingo)
  - [ ] 23.1 Implementar módulo de ejercicios
    - Crear `frontend-eva/src/features/exercises/api.ts`: startLesson, submitAnswer, resumeLesson
    - Crear `frontend-eva/src/features/exercises/hooks.ts`: `useLessonSession()`, `useSubmitAnswer()`
    - Crear `frontend-eva/src/features/exercises/types.ts`: tipos Exercise, LessonSession, AnswerResult
    - _Requisitos: 6.1, 7.1_

  - [ ] 23.2 Implementar página del reproductor de lecciones y componentes de ejercicios
    - Crear `frontend-eva/src/routes/courses/$courseId/lessons/$lessonId.tsx`: página del reproductor de lecciones con barra de progreso, renderizado de ejercicios, visualización de feedback, manejo de cola de reintentos
    - Crear `frontend-eva/src/features/exercises/components/`:
      - `MultipleChoiceExercise`: opciones con radio buttons, selección, feedback
      - `FillBlankExercise`: input de texto con indicador de espacio en blanco, feedback
      - `MatchingExercise`: arrastrar y soltar o seleccionar pares coincidentes, feedback
      - `FreeTextExercise`: textarea con envío para revisión del profesor
      - `ProgressBar`: muestra M/N ejercicios completados
      - `FeedbackIndicator`: animación de correcto/incorrecto
      - `LessonComplete`: pantalla de completación con XP ganado
    - _Requisitos: 6.1–6.7, 7.1–7.6, 24.4_

- [ ] 24. Frontend — Funcionalidades de gamification
  - [ ] 24.1 Implementar módulo de gamification
    - Crear `frontend-eva/src/features/gamification/api.ts`: getProfile, getLeaderboard, getAchievements, getXPHistory
    - Crear `frontend-eva/src/features/gamification/hooks.ts`: `useGamificationProfile()`, `useLeaderboard()`, `useAchievements()`
    - Crear `frontend-eva/src/features/gamification/components/`:
      - `XPDisplay`: XP actual y nivel con progreso al siguiente nivel
      - `StreakDisplay`: racha actual con ícono de llama
      - `AchievementGrid`: logros obtenidos + bloqueados con progreso
      - `LeaderboardTable`: top 100 + rango del usuario actual
      - `LevelUpModal`: modal de celebración al subir de nivel
    - _Requisitos: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.4_

  - [ ] 24.2 Implementar página del dashboard del estudiante
    - Crear `frontend-eva/src/routes/dashboard/index.tsx`: dashboard del estudiante con XP, nivel, racha, cursos inscritos, actividad reciente
    - Crear `frontend-eva/src/routes/profile/index.tsx`: página de perfil con logros, estadísticas
    - _Requisitos: 20.1, 24.4_

- [ ] 25. Frontend — Seguimiento de progreso del estudiante
  - [ ] 25.1 Implementar módulo de progreso
    - Crear `frontend-eva/src/features/progress/api.ts`: getDashboard, getCourseProgress, getActivityHeatmap, getMasteryScores
    - Crear `frontend-eva/src/features/progress/hooks.ts`: `useProgressDashboard()`, `useCourseProgress()`, `useActivityHeatmap()`, `useMasteryScores()`
    - Crear `frontend-eva/src/features/progress/components/`:
      - `ProgressOverview`: visualización de estadísticas totales
      - `CourseProgressDetail`: completación y puntuación por unidad, por lección
      - `ActivityHeatmap`: mapa de calor de calendario de 90 días (similar a contribuciones de GitHub)
      - `MasteryChart`: visualización de dominio por tema
    - _Requisitos: 20.1–20.5, 24.4_

- [ ] 26. Punto de control — Verificar funcionalidades principales del frontend
  - Asegurar que todas las pruebas del frontend pasan, consultar al usuario si surgen dudas.

- [ ] 27. Frontend — Funcionalidades sociales (foro y chat)
  - [ ] 27.1 Implementar módulo social
    - Crear `frontend-eva/src/features/social/api.ts`: listThreads, createThread, getThread, createReply, flagPost, toggleUpvote
    - Crear `frontend-eva/src/features/social/hooks.ts`: `useForumThreads()`, `useThread()`, `useCreateThread()`, `useCreateReply()`, `useUpvote()`
    - Crear `frontend-eva/src/features/social/components/`:
      - `ThreadList`: lista paginada de hilos ordenados por actividad
      - `ThreadDetail`: hilo con respuestas, botones de voto positivo
      - `ThreadForm`: formulario para crear nuevo hilo
      - `ReplyForm`: formulario para responder al hilo
      - `ChatRoom`: componente de chat en tiempo real con lista de mensajes, input, auto-scroll
      - `ChatMessage`: visualización de mensaje individual
    - _Requisitos: 13.1–13.6, 14.1–14.6_

  - [ ] 27.2 Implementar páginas de foro y chat
    - Crear `frontend-eva/src/routes/courses/$courseId/forum.tsx`: página de foro del curso con lista de hilos y creación
    - Crear `frontend-eva/src/routes/courses/$courseId/chat.tsx`: página de chat del curso con conexión WebSocket a `ws/chat/{course_id}/`
    - _Requisitos: 13.1, 14.1, 24.1_

- [ ] 28. Frontend — Proyectos y revisión por pares
  - [ ] 28.1 Implementar módulo de proyectos
    - Crear `frontend-eva/src/features/projects/api.ts`: getProject, submitProject, submitReview, getReviews
    - Crear `frontend-eva/src/features/projects/hooks.ts`: `useProject()`, `useSubmitProject()`, `useSubmitReview()`, `useReviews()`
    - Crear `frontend-eva/src/features/projects/components/`:
      - `ProjectDetail`: descripción del proyecto, rúbrica, fecha límite
      - `SubmissionForm`: carga de archivos (máx 5 archivos, 10MB cada uno) + descripción de texto
      - `ReviewForm`: puntuación por criterio de rúbrica + textarea de feedback
      - `ReviewList`: visualización de revisiones (profesor + pares)
    - _Requisitos: 18.1–18.6_

  - [ ] 28.2 Implementar páginas de proyectos
    - Crear `frontend-eva/src/routes/projects/index.tsx`: listado de proyectos
    - Crear `frontend-eva/src/routes/projects/$projectId.tsx`: detalle del proyecto con envío y revisión
    - _Requisitos: 18.1–18.6, 24.1_

- [ ] 29. Frontend — Aprendizaje colaborativo
  - [ ] 29.1 Implementar módulo de colaboración
    - Crear `frontend-eva/src/features/collaboration/api.ts`: joinCollabExercise, submitGroupWork, getGroupInfo
    - Crear `frontend-eva/src/features/collaboration/hooks.ts`: `useCollabGroup()`, `useJoinCollab()`, `useSubmitGroupWork()`
    - Crear `frontend-eva/src/features/collaboration/components/`:
      - `CollabWorkspace`: espacio de trabajo compartido con actualizaciones en tiempo real vía WebSocket `ws/collab/{exercise_id}/{group_id}/`
      - `GroupMembers`: visualización de miembros del grupo y estado de contribución
      - `GroupSubmitForm`: formulario de envío grupal
    - _Requisitos: 17.1–17.5_

- [ ] 30. Frontend — Dashboard del profesor
  - [ ] 30.1 Implementar módulo del dashboard del profesor
    - Crear `frontend-eva/src/features/teacher/api.ts`: getCourseAnalytics, getStudentList, getStudentDetail, getHeatmap
    - Crear `frontend-eva/src/features/teacher/hooks.ts`: `useCourseAnalytics()`, `useStudentList()`, `useStudentDetail()`, `useHeatmap()`
    - _Requisitos: 15.1, 16.1–16.5_

  - [ ] 30.2 Implementar páginas del dashboard del profesor
    - Crear `frontend-eva/src/routes/teacher/index.tsx`: dashboard del profesor con lista de cursos (estado, conteo de inscripciones, última modificación)
    - Crear `frontend-eva/src/routes/teacher/analytics/$courseId.tsx`: página de analíticas del curso con estadísticas agregadas, lista de estudiantes, mapa de calor de rendimiento
    - _Requisitos: 15.1, 16.1–16.4_

  - [ ] 30.3 Implementar páginas del constructor de cursos
    - Crear `frontend-eva/src/routes/teacher/courses/$courseId/builder.tsx`: constructor visual de cursos con vista de árbol editable (unidades → lecciones → ejercicios)
    - Crear `frontend-eva/src/features/teacher/components/`:
      - `CourseTree`: árbol de jerarquía editable
      - `ExerciseForm`: formulario para cada tipo de ejercicio con validación coincidiendo con reglas del backend
      - `PublishButton`: publicar con visualización de errores de validación
      - `StudentAnalyticsTable`: lista de estudiantes con progreso
      - `PerformanceHeatmap`: visualización de mapa de calor de precisión de ejercicios
    - _Requisitos: 15.1–15.5, 16.1–16.4_

- [ ] 31. Punto de control — Verificar todas las funcionalidades del frontend
  - Asegurar que todas las pruebas del frontend pasan, consultar al usuario si surgen dudas.

- [ ] 32. Entorno de desarrollo Docker
  - [ ] 32.1 Crear configuración de Docker Compose
    - Crear `docker-compose.yml` con 6 servicios:
      - `backend`: app Django (Dockerfile en backend-eva/), depende de postgres + redis, montaje de volumen para código fuente, health check
      - `frontend`: app React (Dockerfile en frontend-eva/), montaje de volumen para código fuente, hot-reload
      - `postgres`: PostgreSQL con health check, volumen para persistencia de datos
      - `redis`: Redis con health check, volumen para persistencia de datos
      - `celery-worker`: misma imagen que backend, ejecuta `celery -A config worker`, depende de postgres + redis + backend
      - `celery-beat`: misma imagen que backend, ejecuta `celery -A config beat`, depende de postgres + redis + backend
    - _Requisitos: 23.1, 23.3, 23.4, 23.5_

  - [ ] 32.2 Crear Dockerfiles para backend y frontend
    - Crear `backend-eva/Dockerfile`: base Python, UV para gestión de dependencias, instalar dependencias, copiar código fuente
    - Crear `frontend-eva/Dockerfile`: base Node/Bun, instalar dependencias, copiar código fuente, servidor de desarrollo Vite
    - _Requisitos: 23.1_

  - [ ] 32.3 Crear configuración de entorno
    - Crear `.env.example` con todas las variables de entorno requeridas: DATABASE_URL, REDIS_URL, SECRET_KEY, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CELERY_BROKER_URL, configuraciones EMAIL_*
    - Crear `.env` (ignorado por git) con valores por defecto de desarrollo
    - _Requisitos: 23.2_

  - [ ] 32.4 Configurar health checks y dependencias de servicios
    - Agregar health checks para PostgreSQL (`pg_isready`) y Redis (`redis-cli ping`)
    - Configurar servicio backend para esperar postgres y redis saludables usando `depends_on` con `condition: service_healthy`
    - Configurar servicios Celery para depender del backend
    - _Requisitos: 23.5_

- [ ] 33. Punto de control final — Verificación completa del sistema
  - Asegurar que todas las pruebas de backend y frontend pasan
  - Verificar que Docker Compose inicia los 6 servicios exitosamente
  - Consultar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los puntos de control aseguran validación incremental en límites lógicos
- Las pruebas de propiedades validan propiedades universales de corrección del documento de diseño (52 en total)
- Las pruebas unitarias validan ejemplos específicos y casos límite
- Las tareas de backend (3–19) van antes que las tareas de frontend (20–31) para asegurar disponibilidad de la API
- La configuración de Docker (32) va al final ya que envuelve la aplicación completada
