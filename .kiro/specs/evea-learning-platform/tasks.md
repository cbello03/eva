# Implementation Plan: EVA Learning Platform

## Overview

This plan implements the EVA (Entorno Virtual de Enseñanza-Aprendizaje) learning platform following a backend-first, then frontend approach. The backend uses Django + Django Ninja + Django Channels + Celery, and the frontend uses React + Next.js + TanStack Query + Zustand + MUI. All tasks are ordered so each builds on the previous, with no orphaned code.

## Tasks

- [x] 1. Project scaffolding and shared infrastructure
  - [x] 1.1 Initialize backend Django project with UV and configure settings
    - Create `backend-eva/` and inside use the django-admin startproject tool to generate the basic scallfolding with "django-admin startproject backend-eva .", then in the same folder django initializes that contains the `settings.py` create the `celery.py` file 
    - Configure PostgreSQL, Redis, Celery, Django Channels in settings
    - Add `pyproject.toml` with all dependencies (django, django-ninja, channels, celery, redis, hypothesis, pytest, pytest-django, ruff, mypy, bleach, pyjwt)
    - Create `manage.py` and empty `apps/` package
    - _Requirements: 23.2_

  - [x] 1.2 Create common utilities module
    - Create `backend-eva/common/` with `models.py` (TimestampedModel base), `permissions.py` (role-based permission decorators for Student, Teacher, Admin), `pagination.py` (cursor/offset pagination), `sanitization.py` (XSS sanitization using bleach), `rate_limiting.py` (Redis-based rate limiter)
    - Create `backend-eva/common/exceptions.py` with all domain exception classes: `DomainError`, `DuplicateEmailError`, `InvalidCredentialsError`, `InsufficientRoleError`, `NotEnrolledError`, `CourseNotPublishedError`, `PublishValidationError`, `RateLimitExceededError`, `FileTooLargeError`, `TooManyFilesError`
    - Create `backend-eva/common/schemas.py` with `ErrorResponse` and `FieldError` Pydantic schemas
    - Register global exception handler in Django Ninja API for DomainError subclasses
    - _Requirements: 21.4, 21.5, 21.6_

  - [ ]* 1.3 Write property tests for rate limiting and XSS sanitization
    - **Property 47: Rate limiting enforcement** — For any IP making requests to a rate-limited endpoint, the first N requests within the window succeed (N=10 for login, N=5 for registration), request N+1 returns 429 with Retry-After header
    - **Validates: Requirements 21.1, 21.2, 21.3**
    - **Property 48: XSS sanitization** — For any user-generated text containing HTML tags or JavaScript, stored content has dangerous elements removed/escaped, retrieved content never contains executable script tags
    - **Validates: Requirements 21.5**

  - [x] 1.4 Initialize frontend React (Next.js) project with Bun and configure tooling
    - `frontend-eva/` already created
    - Add `package.json` with all dependencies (@tanstack/react-query, zustand, @mui/material, react-hook-form, zod, axios, fast-check, vitest, @testing-library/react, oxlint, oxfmt)
    - Configure `next.config.ts`, `tsconfig.json`
    - Create `src/app/layout.tsx` (root layout with providers, Suspense), `src/lib/providers.tsx` (QueryClient, Theme providers), `src/lib/theme.ts` (MUI custom theme)
    - Create `src/lib/api-client.ts` (Axios instance with base URL, withCredentials, interceptors placeholder)
    - Create `src/lib/websocket.ts` (WebSocket connection manager with reconnection logic)
    - Create `src/shared/` directory structure for shared components, hooks, utils, types
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_

- [x] 2. Checkpoint — Verify project scaffolding
  - Ensure both projects initialize without errors, ask the user if questions arise.

- [x] 3. Accounts app — Authentication and authorization
  - [x] 3.1 Create accounts app models and migrations
    - Create `backend-eva/apps/accounts/` app with `models.py`: `Role` enum, `User` model (extending AbstractUser with email as USERNAME_FIELD, display_name, role, timezone), `RefreshToken` model (user FK, token_hash, family_id UUID, is_revoked, expires_at, indexes)
    - Register models in `admin.py`
    - _Requirements: 1.1, 4.1_

  - [x] 3.2 Implement accounts schemas
    - Create `backend-eva/apps/accounts/schemas.py` with Pydantic schemas: `RegisterIn` (email, password, display_name with validation), `LoginIn` (email, password), `TokenOut` (access_token), `UserOut` (id, email, display_name, role, timezone), `RoleChangeIn` (role)
    - Add password validation (≥8 chars, uppercase, lowercase, numeric) in RegisterIn
    - _Requirements: 1.1, 1.4, 1.5_

  - [x] 3.3 Implement AuthService
    - Create `backend-eva/apps/accounts/services.py` with `AuthService` class:
    - `register()`: validate input, check duplicate email, hash password with Django's PBKDF2, create User with Student role, return User
    - `login()`: authenticate credentials, generate Access_Token (JWT, 15min, includes role claim) and Refresh_Token (JWT, 7 days, family_id), store RefreshToken hash, return TokenPair
    - `logout()`: revoke refresh token, clear cookie
    - `refresh_tokens()`: validate refresh token, check family_id for replay detection (if rotated-out token reused → revoke entire family), issue new token pair with same family_id
    - `change_role()`: update user role, invalidate all refresh tokens for that user
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 4.1, 4.3, 4.4_

  - [x] 3.4 Implement accounts API routes
    - Create `backend-eva/apps/accounts/api.py` with Django Ninja router:
    - `POST /auth/register` — no auth, rate limited (5/min/IP), calls AuthService.register
    - `POST /auth/login` — no auth, rate limited (10/min/IP), calls AuthService.login, sets Refresh_Token as httpOnly secure cookie with CSRF protection
    - `POST /auth/logout` — Bearer auth, calls AuthService.logout, clears cookie
    - `POST /auth/refresh` — Cookie auth, calls AuthService.refresh_tokens
    - `GET /auth/me` — Bearer auth, returns current user profile
    - `PATCH /users/{id}/role` — Admin only, calls AuthService.change_role
    - Mount router in `config/urls.py` under `/api/v1/`
    - _Requirements: 1.1, 2.1, 2.5, 2.6, 3.1, 4.2, 4.4, 4.5, 21.1, 21.2, 21.3_

  - [ ]* 3.5 Write property tests for accounts (Properties 1–9)
    - **Property 1: Registration creates a valid account** — For any valid registration input, Auth_Service creates a user with Student role and hashed password
    - **Validates: Requirements 1.1, 1.3**
    - **Property 2: Registration rejects invalid input** — For any invalid input (duplicate email, bad format, weak password), registration is rejected and user count unchanged
    - **Validates: Requirements 1.2, 1.4, 1.5**
    - **Property 3: Login returns well-formed token pair** — For any registered user with valid credentials, login returns Access_Token (15min, role claim) and Refresh_Token (7 days, family_id)
    - **Validates: Requirements 2.1, 2.3, 2.4, 3.4, 4.3**
    - **Property 4: Invalid credentials produce indistinguishable errors** — For any login with wrong email or wrong password, error response is identical
    - **Validates: Requirements 2.2**
    - **Property 5: Logout invalidates refresh token** — After logout, the Refresh_Token is rejected with 401
    - **Validates: Requirements 2.5**
    - **Property 6: Token rotation round trip** — Refreshing returns new tokens, old token invalid, new token valid
    - **Validates: Requirements 3.1, 3.2**
    - **Property 7: Refresh token replay detection** — Reusing rotated-out token A invalidates entire family including token B
    - **Validates: Requirements 3.3**
    - **Property 8: Role-based access enforcement** — User with wrong role gets 403, correct role gets success
    - **Validates: Requirements 4.2**
    - **Property 9: Role change invalidates existing tokens** — After role change, all previous tokens rejected
    - **Validates: Requirements 4.4**

  - [x] 3.6 Write unit tests for accounts
    - Test registration with known valid/invalid inputs
    - Test login with correct and incorrect credentials
    - Test token refresh flow and replay detection edge cases
    - Test role-based permission decorators
    - Test rate limiting on login and registration endpoints
    - _Requirements: 1.1–1.5, 2.1–2.6, 3.1–3.4, 4.1–4.5_

- [x] 4. Checkpoint — Verify authentication system
  - Ensure all accounts tests pass, ask the user if questions arise.

- [x] 5. Courses app — Course management and enrollment
  - [x] 5.1 Create courses app models and migrations
    - Create `backend-eva/apps/courses/` app with `models.py`: `Course` (title, description, teacher FK, status enum draft/published, published_at), `Unit` (course FK, title, order, unique_together course+order), `Lesson` (unit FK, title, order, unique_together unit+order), `Enrollment` (student FK, course FK, is_active, enrolled_at, unique_together student+course)
    - Create and run migrations
    - Register models in `admin.py`
    - _Requirements: 5.1, 22.1_

  - [x] 5.2 Implement courses schemas
    - Create `backend-eva/apps/courses/schemas.py`: `CourseCreateIn`, `CourseUpdateIn`, `CourseOut` (with nested units/lessons), `UnitCreateIn`, `UnitOut`, `LessonCreateIn`, `LessonOut`, `EnrollmentOut`, `ReorderIn`
    - _Requirements: 5.1, 5.2, 22.4_

  - [x] 5.3 Implement CourseService
    - Create `backend-eva/apps/courses/services.py` with `CourseService`:
    - `create_course()`: create draft course for teacher
    - `update_course()`: update course fields (teacher+owner only)
    - `publish_course()`: validate at least one unit, every lesson has ≥1 exercise, set status=published
    - `add_unit()` / `add_lesson()`: assign sequential order numbers
    - `reorder_units()` / `reorder_lessons()`: update all order numbers to maintain contiguous sequence
    - `list_courses()`: Students see only published; Teachers see own courses (draft+published)
    - `enroll()`: create Enrollment, check duplicate, initialize progress via ProgressService
    - `unenroll()`: set is_active=False, preserve progress data
    - `list_enrollments()`: return enrolled courses with progress percentage
    - _Requirements: 5.1–5.8, 22.1–22.5_

  - [x] 5.4 Implement courses API routes
    - Create `backend-eva/apps/courses/api.py` with Django Ninja router:
    - `GET /courses` — Bearer, list courses by role
    - `POST /courses` — Teacher, create course
    - `GET /courses/{id}` — Bearer, course detail with hierarchy
    - `PATCH /courses/{id}` — Teacher+Owner, update course
    - `POST /courses/{id}/publish` — Teacher+Owner, publish with validation
    - `POST /courses/{id}/units` — Teacher+Owner, add unit
    - `PATCH /units/{id}` — Teacher+Owner, update unit
    - `POST /units/{id}/lessons` — Teacher+Owner, add lesson
    - `PATCH /lessons/{id}` — Teacher+Owner, update lesson
    - `POST /courses/{id}/enroll` — Student, enroll
    - `DELETE /courses/{id}/enroll` — Student, unenroll
    - `GET /enrollments` — Student, list enrollments with progress
    - _Requirements: 5.1–5.8, 22.1–22.5_

  - [ ]* 5.5 Write property tests for courses (Properties 10–12, 49–50)
    - **Property 10: Content hierarchy ordering invariant** — After any sequence of add/remove/reorder, order numbers form contiguous sequence from 1
    - **Validates: Requirements 5.3, 5.4, 5.5**
    - **Property 11: Course publish validation** — Publish fails if any lesson has 0 exercises; succeeds if all lessons have ≥1 exercise and ≥1 unit exists
    - **Validates: Requirements 5.2, 5.6**
    - **Property 12: Course visibility by role** — Student sees only published; Teacher sees own draft+published, not other teachers' drafts
    - **Validates: Requirements 5.7, 5.8**
    - **Property 49: Enrollment uniqueness and lifecycle** — One active enrollment per student+course; duplicate fails; unenroll preserves progress; re-enroll reactivates
    - **Validates: Requirements 22.1, 22.2, 22.5**
    - **Property 50: Enrollment initializes progress** — New enrollment creates CourseProgress and LessonProgress for every lesson in the course
    - **Validates: Requirements 22.3**

  - [x] 5.6 Write unit tests for courses
    - Test course CRUD operations
    - Test publish validation edge cases
    - Test enrollment lifecycle (enroll, duplicate, unenroll, re-enroll)
    - Test ordering operations
    - _Requirements: 5.1–5.8, 22.1–22.5_

- [x] 6. Exercises app — Exercise system and lesson player
  - [x] 6.1 Create exercises app models and migrations
    - Create `backend-eva/apps/exercises/` app with `models.py`: `ExerciseType` enum, `Exercise` (lesson FK, exercise_type, question_text, order, config JSONField, difficulty 1-5, topic, is_collaborative, collab_group_size), `LessonSession` (student FK, lesson FK, current_exercise_index, retry_queue JSON, is_completed, completed_at, correct_first_attempt, total_exercises), `AnswerRecord` (student FK, exercise FK, session FK, submitted_answer JSON, is_correct, is_first_attempt, answered_at)
    - Create and run migrations
    - _Requirements: 6.1, 7.1_

  - [x] 6.2 Implement exercises schemas
    - Create `backend-eva/apps/exercises/schemas.py`: `ExerciseCreateIn` (with type-specific config validation — MC: ≥2 options + 1 correct; fill_blank: blank_position + accepted_answers; matching: ≥2 pairs; free_text: rubric/model_answer), `ExerciseOut`, `AnswerIn`, `AnswerResult` (is_correct, correct_answer if wrong, feedback), `LessonSessionOut` (current exercise, progress percentage, retry queue)
    - _Requirements: 6.1–6.6, 7.1–7.6_

  - [x] 6.3 Implement ExerciseService and lesson player logic
    - Create `backend-eva/apps/exercises/services.py` with `ExerciseService`:
    - `create_exercise()`: validate type-specific config, assign order
    - `update_exercise()` / `delete_exercise()`: maintain order contiguity
    - `start_lesson()`: create LessonSession, load exercises in order, return first exercise
    - `submit_answer()`: evaluate answer (MC: index match; fill_blank: case-insensitive match against accepted_answers; matching: pair comparison), record AnswerRecord, if incorrect add to retry_queue, if correct advance index, return feedback
    - `resume_lesson()`: load existing session, return current state
    - Handle lesson completion: when all exercises + retries done, mark completed, award XP via GamificationService, update progress via ProgressService
    - Free text submissions: store for teacher review, trigger notification
    - _Requirements: 6.1–6.7, 7.1–7.6_

  - [x] 6.4 Implement exercises API routes
    - Create `backend-eva/apps/exercises/api.py` with Django Ninja router:
    - `POST /lessons/{id}/exercises` — Teacher+Owner, create exercise
    - `PATCH /exercises/{id}` — Teacher+Owner, update exercise
    - `DELETE /exercises/{id}` — Teacher+Owner, delete exercise
    - `GET /lessons/{id}/start` — Student+Enrolled, start lesson player
    - `POST /exercises/{id}/submit` — Student+Enrolled, submit answer
    - `GET /lessons/{id}/resume` — Student+Enrolled, resume lesson
    - _Requirements: 6.1–6.7, 7.1–7.6_

  - [ ]* 6.5 Write property tests for exercises (Properties 13–18)
    - **Property 13: Exercise type configuration validation** — MC needs ≥2 options + 1 correct; fill_blank needs position + answers; matching needs ≥2 pairs; free_text needs rubric. Invalid configs rejected
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
    - **Property 14: Fill-in-the-blank case-insensitive matching** — Any accepted answer in any case combination evaluates as correct
    - **Validates: Requirements 6.3**
    - **Property 15: Auto-graded exercise feedback** — Submission to MC/fill_blank/matching returns correctness boolean and correct answer if wrong
    - **Validates: Requirements 6.6, 7.2, 7.3**
    - **Property 16: Incorrect answers queued for retry** — Every incorrect answer appears in retry queue; after all retries, lesson marked completed
    - **Validates: Requirements 7.3, 7.4**
    - **Property 17: Lesson progress calculation** — Progress = completed/total × 100; retry queue exercises count toward total but not completed until correct
    - **Validates: Requirements 7.5**
    - **Property 18: Lesson session save and resume round trip** — Resuming restores exact state: exercise index, retry queue, completion counts
    - **Validates: Requirements 7.6**

  - [x] 6.6 Write unit tests for exercises
    - Test each exercise type creation and validation
    - Test lesson player flow: start, answer, retry, complete
    - Test free text submission storage and notification trigger
    - _Requirements: 6.1–6.7, 7.1–7.6_

- [x] 7. Checkpoint — Verify course and exercise system
  - Ensure all courses and exercises tests pass, ask the user if questions arise.

- [x] 8. Gamification app — XP, levels, streaks, achievements, leaderboards
  - [x] 8.1 Create gamification app models and migrations
    - Create `backend-eva/apps/gamification/` app with `models.py`: `GamificationProfile` (student OneToOne, total_xp, current_level, current_streak, longest_streak, last_activity_date), `XPTransaction` (student FK, amount, source_type, source_id, timestamp), `Achievement` (name unique, description, icon, condition_type, condition_value), `UserAchievement` (student FK, achievement FK, unlocked_at, unique_together student+achievement)
    - Create and run migrations
    - _Requirements: 8.1, 8.5, 9.5, 10.1, 10.5_

  - [x] 8.2 Implement gamification schemas
    - Create `backend-eva/apps/gamification/schemas.py`: `GamificationProfileOut`, `XPTransactionOut`, `AchievementOut` (with unlock status and progress), `LeaderboardEntryOut`, `LeaderboardOut` (entries + requesting user rank/xp), `StreakOut`
    - _Requirements: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.4_

  - [x] 8.3 Implement GamificationService
    - Create `backend-eva/apps/gamification/services.py` with `GamificationService`:
    - `award_xp()`: create XPTransaction, update GamificationProfile.total_xp, update Redis sorted sets (weekly + alltime leaderboards), check level up
    - `check_level_up()`: calculate level thresholds using progression formula, advance level if threshold crossed, send notification
    - `evaluate_achievements()`: after each XP event, check all achievement conditions against student stats, grant new achievements (idempotent — unique_together prevents duplicates), send notifications
    - `update_streak()`: if last_activity_date != today (student timezone), increment streak, update longest_streak if needed, check streak milestones (7, 30, 100, 365), award bonus XP
    - `get_leaderboard()`: read from Redis sorted set, return top 100 + requesting user's rank/xp
    - _Requirements: 8.1–8.5, 9.1, 9.4, 9.5, 10.1–10.5, 11.1–11.4_

  - [x] 8.4 Implement gamification Celery tasks
    - Create `backend-eva/apps/gamification/tasks.py`:
    - `reset_expired_streaks`: daily at 00:00 UTC, find students with last_activity_date < yesterday, set current_streak=0
    - `reset_weekly_leaderboard`: every Monday 00:00 UTC, clear Redis weekly sorted set
    - Register tasks in Celery Beat schedule
    - _Requirements: 9.2, 9.3, 11.5_

  - [x] 8.5 Implement gamification API routes
    - Create `backend-eva/apps/gamification/api.py` with Django Ninja router:
    - `GET /gamification/profile` — Bearer, return XP, level, streak, achievements
    - `GET /gamification/leaderboard` — Bearer, query param period=weekly|alltime
    - `GET /gamification/achievements` — Bearer, all achievements with unlock status
    - `GET /gamification/xp-history` — Bearer, XP transaction log
    - _Requirements: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.4_

  - [ ]* 8.6 Write property tests for gamification (Properties 19–25)
    - **Property 19: XP award and transaction recording** — Completed lesson awards XP = f(first_attempt_correct), XPTransaction created with correct amount, source_type="lesson", source_id, timestamp
    - **Validates: Requirements 8.1, 8.5**
    - **Property 20: Level progression** — XP crossing level threshold advances current_level by exactly the number of thresholds crossed, following defined formula
    - **Validates: Requirements 8.2, 8.3, 8.4**
    - **Property 21: Streak increment and invariant** — Completing lesson on new calendar day increments streak by 1; longest_streak ≥ current_streak always; last_activity_date = today
    - **Validates: Requirements 9.1, 9.5**
    - **Property 22: Streak reset on inactivity** — Student with last_activity_date before yesterday gets current_streak=0, longest_streak preserved
    - **Validates: Requirements 9.2**
    - **Property 23: Achievement grant idempotence** — Granting same achievement twice results in exactly one UserAchievement record
    - **Validates: Requirements 10.5**
    - **Property 24: Achievement unlock on condition met** — When student stats meet achievement condition after XP event, achievement granted and notification created
    - **Validates: Requirements 10.2, 10.3, 9.4**
    - **Property 25: Leaderboard ordering and completeness** — Returns ≤100 entries sorted by XP desc; requesting student's rank always included even if not in top 100
    - **Validates: Requirements 11.2, 11.3**

  - [x] 8.7 Write unit tests for gamification
    - Test XP award and level-up calculations
    - Test streak increment, reset, and milestone detection
    - Test achievement evaluation and idempotence
    - Test leaderboard Redis operations
    - Test Celery tasks (streak reset, leaderboard reset)
    - _Requirements: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.5_

- [x] 9. Adaptive learning — within exercises/progress apps
  - [x] 9.1 Create adaptive learning models and migrations
    - Add to `backend-eva/apps/progress/models.py`: `TopicMastery` (student FK, topic, course FK, correct_count, total_count, mastery_score, last_reviewed, unique_together student+topic+course), `SpacedRepetitionItem` (student FK, exercise FK, next_review_date, interval_days, review_count)
    - Create and run migrations
    - _Requirements: 12.1, 12.2, 12.4_

  - [x] 9.2 Implement AdaptiveService
    - Create `backend-eva/apps/exercises/adaptive.py` (or within services.py) with `AdaptiveService`:
    - `record_answer()`: update TopicMastery for the exercise's topic — increment correct_count/total_count, recalculate mastery_score with recency weighting
    - `get_mastery_scores()`: return mastery scores per topic for a student in a course
    - `should_recommend_review()`: check if any prerequisite topic for a unit has mastery_score < 0.6, return recommendation
    - `generate_review_session()`: select exercises from weak topics, prioritize lowest mastery scores
    - `schedule_spaced_repetition()`: on incorrect answer, create SpacedRepetitionItem with next_review_date = today + 1 day; on review, progress interval through [1, 3, 7, 14, 30]
    - `adjust_difficulty()`: after 3 consecutive correct → increase difficulty; after 2 consecutive incorrect → decrease difficulty
    - _Requirements: 12.1–12.6_

  - [x] 9.3 Implement spaced repetition Celery task
    - Create task in `backend-eva/apps/progress/tasks.py`:
    - `process_spaced_repetition`: daily task, find SpacedRepetitionItems where next_review_date = today, create review sessions for affected students
    - Register in Celery Beat schedule
    - _Requirements: 12.4_

  - [ ]* 9.4 Write property tests for adaptive learning (Properties 26–30)
    - **Property 26: Mastery score calculation** — Mastery = weighted correct/total ratio; adding correct answer never decreases score; adding incorrect never increases it
    - **Validates: Requirements 12.2**
    - **Property 27: Review recommendation threshold** — Prerequisite topic mastery < 0.6 triggers review recommendation; all ≥ 0.6 means no recommendation
    - **Validates: Requirements 12.3**
    - **Property 28: Spaced repetition scheduling** — Incorrect answer creates item with next_review = today + 1; intervals progress through [1, 3, 7, 14, 30]
    - **Validates: Requirements 12.4**
    - **Property 29: Review session exercise selection** — All selected exercises from topics with mastery below threshold; lower mastery topics appear first
    - **Validates: Requirements 12.5**
    - **Property 30: Adaptive difficulty adjustment** — 3 consecutive correct → equal or higher difficulty next; 2 consecutive incorrect → equal or lower difficulty next
    - **Validates: Requirements 12.6**

  - [x] 9.5 Write unit tests for adaptive learning
    - Test mastery score calculation with specific answer sequences
    - Test review recommendation logic
    - Test spaced repetition interval progression
    - Test difficulty adjustment thresholds
    - _Requirements: 12.1–12.6_

- [x] 10. Checkpoint — Verify gamification and adaptive learning
  - Ensure all gamification and adaptive learning tests pass, ask the user if questions arise.

- [x] 11. Social app — Forums and real-time chat
  - [x] 11.1 Create social app models and migrations
    - Create `backend-eva/apps/social/` app with `models.py`: `ForumThread` (course FK, author FK, title, body, is_hidden, last_activity_at), `ForumReply` (thread FK, author FK, body, is_hidden, upvote_count), `ReplyUpvote` (reply FK, user FK, unique_together reply+user), `ChatMessage` (course FK, author FK, content max 2000, sent_at)
    - Create and run migrations
    - _Requirements: 13.1, 13.2, 14.1, 14.4_

  - [x] 11.2 Implement social schemas
    - Create `backend-eva/apps/social/schemas.py`: `ThreadCreateIn`, `ThreadOut`, `ReplyCreateIn`, `ReplyOut` (with upvote_count), `ChatMessageOut`, `ThreadListOut` (paginated, 20 per page)
    - _Requirements: 13.2, 13.4, 14.3_

  - [x] 11.3 Implement SocialService (forums)
    - Create `backend-eva/apps/social/services.py` with `ForumService`:
    - `create_thread()`: require title + body, associate with course and author, sanitize content
    - `list_threads()`: return threads sorted by last_activity_at desc, paginated 20/page
    - `create_reply()`: append reply, update thread last_activity_at, notify thread author via NotificationService, sanitize content
    - `flag_post()`: Teacher/Admin only, set is_hidden=True, notify post author
    - `toggle_upvote()`: create/delete ReplyUpvote, update upvote_count
    - _Requirements: 13.1–13.6_

  - [x] 11.4 Implement chat WebSocket consumer
    - Create `backend-eva/apps/social/consumers.py` with `ChatConsumer` (Django Channels):
    - `connect()`: authenticate JWT from query param, verify enrollment in course, join channel group, send last 50 messages as history
    - `receive()`: validate message, persist ChatMessage to DB, broadcast to group
    - `disconnect()`: leave channel group
    - Configure routing in `config/asgi.py`
    - _Requirements: 14.1–14.6_

  - [x] 11.5 Implement social API routes
    - Create `backend-eva/apps/social/api.py` with Django Ninja router:
    - `GET /courses/{id}/forum/threads` — Bearer+Enrolled, paginated thread list
    - `POST /courses/{id}/forum/threads` — Bearer+Enrolled, create thread
    - `GET /forum/threads/{id}` — Bearer+Enrolled, thread detail with replies
    - `POST /forum/threads/{id}/replies` — Bearer+Enrolled, reply to thread
    - `POST /forum/posts/{id}/flag` — Teacher|Admin, flag post
    - `POST /forum/replies/{id}/upvote` — Bearer+Enrolled, toggle upvote
    - _Requirements: 13.1–13.6_

  - [ ]* 11.6 Write property tests for social (Properties 31–35)
    - **Property 31: Forum thread ordering** — Threads sorted by last_activity_at desc; adding reply moves thread to top
    - **Validates: Requirements 13.4**
    - **Property 32: Forum post flagging hides content** — Flagged post not in public listings; author notified
    - **Validates: Requirements 13.5**
    - **Property 33: Chat history on connect** — Connecting delivers min(N, 50) most recent messages in chronological order
    - **Validates: Requirements 14.3**
    - **Property 34: Chat message persistence round trip** — Sent message persisted to DB; querying returns matching content, author, course
    - **Validates: Requirements 14.4**
    - **Property 35: Chat room enrollment enforcement** — Unenrolled user rejected; enrolled user connects successfully
    - **Validates: Requirements 14.5**

  - [x] 11.7 Write unit tests for social
    - Test forum CRUD, pagination, flagging
    - Test upvote toggle behavior
    - Test chat consumer connect/disconnect/message flow
    - Test enrollment enforcement on WebSocket
    - _Requirements: 13.1–13.6, 14.1–14.6_

- [x] 12. Projects app — Real-world projects and peer review
  - [x] 12.1 Create projects app models and migrations
    - Create `backend-eva/apps/projects/` app with `models.py`: `Project` (course FK, teacher FK, title, description, rubric JSON, submission_deadline, peer_review_enabled, peer_reviewers_count default 2), `ProjectSubmission` (project FK, student FK, description, is_late, submitted_at, unique_together project+student), `SubmissionFile` (submission FK, file FileField, filename, file_size), `ProjectReview` (submission FK, reviewer FK, review_type teacher/peer, scores JSON, feedback, is_complete), `PeerReviewAssignment` (submission FK, reviewer FK, is_completed, unique_together submission+reviewer)
    - Create and run migrations
    - _Requirements: 18.1–18.6_

  - [x] 12.2 Implement projects schemas
    - Create `backend-eva/apps/projects/schemas.py`: `ProjectCreateIn` (title, description, rubric, deadline, peer_review_enabled), `ProjectOut`, `SubmissionOut`, `ReviewIn` (scores per criterion, feedback), `ReviewOut`, `PeerReviewAssignmentOut`
    - Validate file constraints: max 10MB per file, max 5 files
    - _Requirements: 18.1, 18.2_

  - [x] 12.3 Implement ProjectService
    - Create `backend-eva/apps/projects/services.py` with `ProjectService`:
    - `create_project()`: require title, description, rubric with scored criteria, deadline
    - `submit_project()`: accept files (max 10MB each, max 5), text description, flag as late if after deadline
    - `teacher_review()`: score each rubric criterion, provide feedback
    - `assign_peer_reviews()`: after deadline, assign each submission to 2 other students (no self-review)
    - `submit_peer_review()`: record scores and feedback, mark assignment complete
    - `get_reviews()`: return reviews; peer reviews visible only when all assigned reviews complete
    - _Requirements: 18.1–18.6_

  - [x] 12.4 Implement projects API routes
    - Create `backend-eva/apps/projects/api.py` with Django Ninja router:
    - `POST /projects` — Teacher, create project
    - `GET /projects/{id}` — Bearer+Enrolled, project detail
    - `POST /projects/{id}/submit` — Student+Enrolled, multipart submission
    - `POST /submissions/{id}/review` — Teacher, teacher review
    - `POST /submissions/{id}/peer-review` — Student, peer review
    - `GET /submissions/{id}/reviews` — Bearer, get reviews
    - _Requirements: 18.1–18.6_

  - [ ]* 12.5 Write property tests for projects (Properties 41–43)
    - **Property 41: Project late submission flagging** — If submitted_at > deadline, is_late=True; if ≤ deadline, is_late=False
    - **Validates: Requirements 18.3**
    - **Property 42: Peer review assignment** — With peer_review_enabled and N≥3 submissions, each gets exactly peer_reviewers_count reviewers; no self-review
    - **Validates: Requirements 18.5**
    - **Property 43: Peer review visibility** — Reviews visible to author only when all assigned reviews are complete
    - **Validates: Requirements 18.6**

  - [x] 12.6 Write unit tests for projects
    - Test project creation and validation
    - Test submission with file constraints
    - Test late submission detection
    - Test peer review assignment algorithm
    - Test review visibility rules
    - _Requirements: 18.1–18.6_

- [x] 13. Collaboration app — Group exercises and shared workspaces
  - [x] 13.1 Create collaboration app models and migrations
    - Create `backend-eva/apps/collaboration/` app with `models.py`: `CollabGroup` (exercise FK, max_size, workspace_state JSON, is_submitted), `CollabGroupMember` (group FK, student FK, joined_at, last_contribution_at, unique_together group+student), `CollabSubmission` (group FK, submitted_answer JSON, submitted_at)
    - Create and run migrations
    - _Requirements: 17.1, 17.2_

  - [x] 13.2 Implement CollaborationService
    - Create `backend-eva/apps/collaboration/services.py` with `CollaborationService`:
    - `join_exercise()`: find group with available slots (members < max_size) or create new group, add student as member
    - `submit_group_work()`: record CollabSubmission, award equal XP to all group members via GamificationService
    - `get_group_info()`: return group members, workspace state
    - `check_inactive_members()`: find members with no contribution within 48 hours, notify member + teacher
    - _Requirements: 17.1–17.5_

  - [x] 13.3 Implement collaboration WebSocket consumer
    - Create `backend-eva/apps/collaboration/consumers.py` with `CollabConsumer`:
    - `connect()`: authenticate JWT, verify group membership, join channel group for exercise+group
    - `receive()`: update workspace_state, broadcast to group members, update last_contribution_at
    - `disconnect()`: leave channel group
    - Configure routing in `config/asgi.py`
    - _Requirements: 17.3_

  - [x] 13.4 Implement collaboration API routes
    - Create `backend-eva/apps/collaboration/api.py` with Django Ninja router:
    - `POST /exercises/{id}/collab/join` — Student+Enrolled, join collaborative exercise
    - `POST /collab/groups/{id}/submit` — Student+GroupMember, submit group work
    - `GET /collab/groups/{id}` — Student+GroupMember, get group info and workspace state
    - _Requirements: 17.1–17.5_

  - [x] 13.5 Implement collaboration Celery task
    - Create `backend-eva/apps/collaboration/tasks.py`:
    - `check_inactive_collab_members`: periodic task, find group members with last_contribution_at > 48 hours from exercise start, notify via NotificationService
    - _Requirements: 17.5_

  - [ ]* 13.6 Write property tests for collaboration (Properties 39–40)
    - **Property 39: Collaborative group assignment** — Student assigned to group with available slots; if none, new group created; no group exceeds max_size
    - **Validates: Requirements 17.2**
    - **Property 40: Collaborative submission awards equal XP** — Every group member receives XPTransaction with same amount
    - **Validates: Requirements 17.4**

  - [x] 13.7 Write unit tests for collaboration
    - Test group assignment with various slot availability
    - Test group submission and XP distribution
    - Test WebSocket workspace updates
    - Test inactive member detection
    - _Requirements: 17.1–17.5_

- [x] 14. Notifications app — In-app and email notifications
  - [x] 14.1 Create notifications app models and migrations
    - Create `backend-eva/apps/notifications/` app with `models.py`: `Notification` (recipient FK, notification_type, title, body, data JSON, channel enum in_app/email/both, is_read, email_sent)
    - Create and run migrations
    - _Requirements: 19.1_

  - [x] 14.2 Implement NotificationService
    - Create `backend-eva/apps/notifications/services.py` with `NotificationService`:
    - `create_notification()`: create Notification record, dispatch to configured channels
    - `send_in_app()`: push via WebSocket to user's notification channel
    - `get_notifications()`: paginated list for user
    - `get_unread_count()`: count from DB (cached in Redis)
    - `mark_read()`: update is_read, decrement Redis unread count
    - `mark_all_read()`: bulk update, reset Redis count
    - _Requirements: 19.1–19.5_

  - [x] 14.3 Implement notification WebSocket consumer
    - Create `backend-eva/apps/notifications/consumers.py` with `NotificationConsumer`:
    - `connect()`: authenticate JWT, join user-specific channel group
    - Real-time delivery: when notification created, send to user's WebSocket if connected
    - `disconnect()`: leave channel group
    - Configure routing in `config/asgi.py`
    - _Requirements: 19.3_

  - [x] 14.4 Implement notification Celery tasks
    - Create `backend-eva/apps/notifications/tasks.py`:
    - `send_email_notification`: send email for notifications with channel=email|both, retry policy: 3 attempts with exponential backoff
    - Configure `autoretry_for`, `retry_backoff=True`, `max_retries=3`, `retry_backoff_max=300`
    - _Requirements: 19.6_

  - [x] 14.5 Implement notifications API routes
    - Create `backend-eva/apps/notifications/api.py` with Django Ninja router:
    - `GET /notifications` — Bearer, paginated notification list
    - `GET /notifications/unread-count` — Bearer, unread count
    - `POST /notifications/{id}/read` — Bearer, mark as read
    - `POST /notifications/read-all` — Bearer, mark all as read
    - _Requirements: 19.1–19.5_

  - [ ]* 14.6 Write property test for notifications (Property 44)
    - **Property 44: Notification unread count consistency** — Unread count = count of Notification records where is_read=False; marking read decrements by exactly 1
    - **Validates: Requirements 19.4, 19.5**

  - [x] 14.7 Write unit tests for notifications
    - Test notification creation for each event type
    - Test WebSocket delivery
    - Test email task retry behavior
    - Test mark read / mark all read
    - _Requirements: 19.1–19.6_

- [x] 15. Checkpoint — Verify collaboration and notifications
  - Ensure all collaboration and notification tests pass, ask the user if questions arise.

- [ ] 16. Progress app — Student progress tracking and teacher analytics
  - [x] 16.1 Create progress app models and migrations
    - Create `backend-eva/apps/progress/` app with `models.py`: `CourseProgress` (student FK, course FK, completion_percentage, total_score, lessons_completed, total_lessons, unique_together student+course), `LessonProgress` (student FK, lesson FK, is_completed, score, completed_at, unique_together student+lesson), `DailyActivity` (student FK, date, lessons_completed, xp_earned, time_spent_minutes, unique_together student+date)
    - Note: `TopicMastery` and `SpacedRepetitionItem` already created in task 9.1
    - Create and run migrations
    - _Requirements: 20.1–20.5, 16.1–16.5_

  - [x] 16.2 Implement ProgressService
    - Create `backend-eva/apps/progress/services.py` with `ProgressService`:
    - `initialize_course_progress()`: create CourseProgress + LessonProgress for every lesson in course
    - `update_lesson_progress()`: mark lesson completed, update score, recalculate CourseProgress completion_percentage
    - `get_dashboard()`: return total_xp, current_level, current_streak, courses_enrolled, courses_completed (from GamificationProfile + Enrollment records)
    - `get_course_progress()`: return per-unit, per-lesson completion and score
    - `get_activity_heatmap()`: return last 90 days of DailyActivity, fill missing days with zeros
    - `get_mastery_scores()`: return TopicMastery data per topic
    - _Requirements: 20.1–20.5_

  - [x] 16.3 Implement AnalyticsService (teacher analytics)
    - Create `backend-eva/apps/progress/analytics.py` with `AnalyticsService`:
    - `get_course_analytics()`: total enrolled, average completion rate, average score, average time per lesson
    - `get_student_list()`: per-student progress percentage, score, streak, last activity
    - `get_student_detail()`: completion status and score per unit and lesson
    - `get_performance_heatmap()`: exercise accuracy rates across topics
    - _Requirements: 16.1–16.4_

  - [x] 16.4 Implement analytics Celery task
    - Create task in `backend-eva/apps/progress/tasks.py`:
    - `aggregate_analytics`: hourly task, pre-compute aggregate statistics for teacher dashboard
    - Register in Celery Beat schedule
    - _Requirements: 16.5_

  - [x] 16.5 Implement progress and analytics API routes
    - Create `backend-eva/apps/progress/api.py` with Django Ninja router:
    - Student progress endpoints:
      - `GET /progress/dashboard` — Student, overall stats
      - `GET /progress/courses/{id}` — Student+Enrolled, per-course detail
      - `GET /progress/activity` — Student, 90-day activity heatmap
      - `GET /progress/mastery` — Student, topic mastery scores
    - Teacher analytics endpoints:
      - `GET /teacher/courses/{id}/analytics` — Teacher+Owner, aggregate stats
      - `GET /teacher/courses/{id}/students` — Teacher+Owner, student list
      - `GET /teacher/courses/{id}/students/{sid}` — Teacher+Owner, student detail
      - `GET /teacher/courses/{id}/heatmap` — Teacher+Owner, accuracy heatmap
    - _Requirements: 20.1–20.5, 16.1–16.5_

  - [ ]* 16.6 Write property tests for progress and analytics (Properties 36–38, 45–46)
    - **Property 36: Teacher dashboard course list completeness** — All courses owned by teacher included with correct status, enrollment count, last modified date
    - **Validates: Requirements 15.1**
    - **Property 37: Teacher analytics aggregate accuracy** — Aggregate stats (total enrolled, avg completion, avg score) mathematically consistent with underlying records
    - **Validates: Requirements 16.1**
    - **Property 38: Student progress detail consistency** — Detailed view per unit/lesson matches actual LessonProgress records
    - **Validates: Requirements 16.2, 16.3**
    - **Property 45: Student progress dashboard consistency** — Dashboard total_xp, current_level, current_streak match GamificationProfile; courses_enrolled/completed match Enrollment records
    - **Validates: Requirements 20.1**
    - **Property 46: Activity heatmap data range** — Returns exactly 90 calendar days, one entry per day, zero values for inactive days
    - **Validates: Requirements 20.4**

  - [x] 16.7 Write unit tests for progress and analytics
    - Test progress initialization on enrollment
    - Test lesson completion updates
    - Test dashboard data aggregation
    - Test teacher analytics calculations
    - Test heatmap data generation
    - _Requirements: 20.1–20.5, 16.1–16.5_

- [x] 17. Checkpoint — Verify progress and analytics
  - Ensure all progress and analytics tests pass, ask the user if questions arise.

- [ ] 18. Backend integration — Wire all apps together and configure ASGI/Celery
  - [x] 18.1 Configure ASGI routing for all WebSocket consumers
    - Update `backend-eva/config/asgi.py` to include all WebSocket routes:
    - `ws/chat/{course_id}/` → ChatConsumer
    - `ws/notifications/` → NotificationConsumer
    - `ws/collab/{exercise_id}/{group_id}/` → CollabConsumer
    - Add JWT authentication middleware for WebSocket connections
    - _Requirements: 14.1, 17.3, 19.3_

  - [x] 18.2 Configure Celery Beat schedule with all periodic tasks
    - Update `backend-eva/config/celery.py` with complete beat schedule:
    - Streak reset: daily 00:00 UTC
    - Leaderboard reset: weekly Monday 00:00 UTC
    - Analytics aggregation: hourly
    - Spaced repetition scheduler: daily
    - Inactive collab member check: periodic
    - _Requirements: 9.2, 9.3, 11.5, 12.4, 16.5, 17.5_

  - [x] 18.3 Mount all API routers in root URL configuration
    - Update `backend-eva/config/urls.py` to mount all app routers under `/api/v1/`:
    - accounts, courses, exercises, gamification, progress, social, projects, collaboration, notifications
    - Configure CORS middleware allowing only configured frontend origin
    - _Requirements: 21.6_

  - [x] 18.4 Write backend integration tests
    - Test cross-app flows: enrollment → lesson start → answer → XP award → achievement check → notification
    - Test WebSocket authentication and enrollment enforcement
    - _Requirements: 7.4, 8.1, 10.3, 19.2_

- [x] 19. Checkpoint — Verify full backend integration
  - Ensure all backend tests pass, ask the user if questions arise.

- [ ] 20. Frontend — Auth feature module and API client
  - [x] 20.1 Implement API client with token refresh interceptor
    - Complete `frontend-eva/src/lib/api-client.ts`:
    - Axios instance with baseURL `/api/v1`, withCredentials: true
    - Request interceptor: attach Access_Token from Zustand store as Bearer header
    - Response interceptor: on 401, call `/auth/refresh` (cookie), update Zustand store, retry original request once; on second 401, redirect to login
    - Handle 403 (access denied notification), 429 (retry-after notification), 5xx (generic error)
    - _Requirements: 24.2, 24.7, 24.8_

  - [x] 20.2 Implement auth Zustand store and hooks
    - Create `frontend-eva/src/features/auth/store.ts`: Zustand store with accessToken (in memory only), user object, isAuthenticated, setAccessToken, setUser, logout
    - Create `frontend-eva/src/features/auth/api.ts`: login, register, logout, refreshToken, getMe API functions
    - Create `frontend-eva/src/features/auth/hooks.ts`: `useAuth()`, `useUser()`, `useLogin()`, `useRegister()`, `useLogout()` hooks using TanStack Query mutations
    - _Requirements: 24.3, 24.7_

  - [x] 20.3 Implement auth pages (Login, Register)
    - Create `frontend-eva/src/app/login/page.tsx`: login form with React Hook Form + Zod validation, email + password fields, error display, redirect on success
    - Create `frontend-eva/src/app/register/page.tsx`: registration form with email, password, display_name, password strength validation matching backend rules
    - Create `frontend-eva/src/features/auth/components/` with form components
    - _Requirements: 1.1, 1.4, 1.5, 2.1, 24.1_

  - [ ]* 20.4 Write frontend property tests for auth (Properties 51–52)
    - **Property 51: Frontend access token memory-only storage** — After login, Access_Token exists only in Zustand store; localStorage and sessionStorage contain no token values
    - **Validates: Requirements 24.7**
    - **Property 52: Automatic token refresh on 401** — On 401 response, API client calls refresh endpoint, updates Zustand store, retries original request exactly once
    - **Validates: Requirements 24.8**

  - [x] 20.5 Write unit tests for auth feature
    - Test Zustand store state transitions
    - Test API client interceptor behavior
    - Test login/register form validation
    - _Requirements: 24.7, 24.8_

- [ ] 21. Frontend — App shell, routing, and layout
  - [x] 21.1 Configure Next.js App Router with file-based routing
    - Create `frontend-eva/src/app/layout.tsx`: root layout with React Suspense, MUI ThemeProvider, navigation bar, notification indicator
    - Create `frontend-eva/src/app/page.tsx`: landing page
    - Set up route guards for authenticated/role-based routes using Next.js middleware
    - Configure React Suspense with `loading.tsx` files for all route-level components
    - _Requirements: 24.1, 24.6_

  - [x] 21.2 Implement WebSocket connection manager
    - Complete `frontend-eva/src/lib/websocket.ts`:
    - WebSocket class with JWT auth via query param
    - Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, max 30s)
    - Message queue for messages during reconnection, flushed on reconnect
    - Stale connection detection via ping/pong (30s interval)
    - _Requirements: 14.6, 19.3_

  - [x] 21.3 Implement notification feature module
    - Create `frontend-eva/src/features/notifications/api.ts`: getNotifications, getUnreadCount, markRead, markAllRead
    - Create `frontend-eva/src/features/notifications/hooks.ts`: `useNotifications()`, `useUnreadCount()`, `useMarkRead()`
    - Create `frontend-eva/src/features/notifications/components/`: NotificationBell (with unread count badge), NotificationList, NotificationItem
    - Connect to WebSocket `ws/notifications/` for real-time delivery
    - _Requirements: 19.1–19.5_

- [ ] 22. Frontend — Course browsing and enrollment
  - [x] 22.1 Implement courses feature module
    - Create `frontend-eva/src/features/courses/api.ts`: listCourses, getCourse, enrollInCourse, unenrollFromCourse, listEnrollments
    - Create `frontend-eva/src/features/courses/hooks.ts`: `useCourses()`, `useCourse()`, `useEnroll()`, `useUnenroll()`, `useEnrollments()`
    - Create `frontend-eva/src/features/courses/types.ts`: Course, Unit, Lesson, Enrollment TypeScript types
    - _Requirements: 5.7, 22.1, 22.4_

  - [x] 22.2 Implement course pages
    - Create `frontend-eva/src/app/courses/page.tsx`: course listing page with search/filter, enrollment status
    - Create `frontend-eva/src/app/courses/[courseId]/page.tsx`: course detail page with unit/lesson hierarchy, enroll/unenroll button, progress display
    - Create `frontend-eva/src/features/courses/components/`: CourseCard, CourseList, UnitAccordion, LessonItem
    - _Requirements: 5.7, 22.1, 22.4, 24.4, 24.5_

- [ ] 23. Frontend — Lesson player (Duolingo-style)
  - [x] 23.1 Implement exercises feature module
    - Create `frontend-eva/src/features/exercises/api.ts`: startLesson, submitAnswer, resumeLesson
    - Create `frontend-eva/src/features/exercises/hooks.ts`: `useLessonSession()`, `useSubmitAnswer()`
    - Create `frontend-eva/src/features/exercises/types.ts`: Exercise, LessonSession, AnswerResult types
    - _Requirements: 6.1, 7.1_

  - [x] 23.2 Implement lesson player page and exercise components
    - Create `frontend-eva/src/app/courses/[courseId]/lessons/[lessonId]/page.tsx`: lesson player page with progress bar, exercise rendering, feedback display, retry queue handling
    - Create `frontend-eva/src/features/exercises/components/`:
      - `MultipleChoiceExercise`: radio button options, selection, feedback
      - `FillBlankExercise`: text input with blank indicator, feedback
      - `MatchingExercise`: drag-and-drop or select matching pairs, feedback
      - `FreeTextExercise`: textarea with submit for teacher review
      - `ProgressBar`: shows M/N exercises completed
      - `FeedbackIndicator`: correct/incorrect animation
      - `LessonComplete`: completion screen with XP earned
    - _Requirements: 6.1–6.7, 7.1–7.6, 24.4_

- [ ] 24. Frontend — Gamification features
  - [x] 24.1 Implement gamification feature module
    - Create `frontend-eva/src/features/gamification/api.ts`: getProfile, getLeaderboard, getAchievements, getXPHistory
    - Create `frontend-eva/src/features/gamification/hooks.ts`: `useGamificationProfile()`, `useLeaderboard()`, `useAchievements()`
    - Create `frontend-eva/src/features/gamification/components/`:
      - `XPDisplay`: current XP and level with progress to next level
      - `StreakDisplay`: current streak with flame icon
      - `AchievementGrid`: earned + locked achievements with progress
      - `LeaderboardTable`: top 100 + current user rank
      - `LevelUpModal`: celebration modal on level up
    - _Requirements: 8.1–8.5, 9.1–9.5, 10.1–10.5, 11.1–11.4_

  - [x] 24.2 Implement student dashboard page
    - Create `frontend-eva/src/app/dashboard/page.tsx`: student dashboard with XP, level, streak, enrolled courses, recent activity
    - Create `frontend-eva/src/app/profile/page.tsx`: profile page with achievements, stats
    - _Requirements: 20.1, 24.4_

- [ ] 25. Frontend — Student progress tracking
  - [x] 25.1 Implement progress feature module
    - Create `frontend-eva/src/features/progress/api.ts`: getDashboard, getCourseProgress, getActivityHeatmap, getMasteryScores
    - Create `frontend-eva/src/features/progress/hooks.ts`: `useProgressDashboard()`, `useCourseProgress()`, `useActivityHeatmap()`, `useMasteryScores()`
    - Create `frontend-eva/src/features/progress/components/`:
      - `ProgressOverview`: total stats display
      - `CourseProgressDetail`: per-unit, per-lesson completion and score
      - `ActivityHeatmap`: 90-day calendar heatmap (similar to GitHub contributions)
      - `MasteryChart`: topic mastery visualization
    - _Requirements: 20.1–20.5, 24.4_

- [x] 26. Checkpoint — Verify core frontend features
  - Ensure all frontend tests pass, ask the user if questions arise.

- [ ] 27. Frontend — Social features (forum and chat)
  - [x] 27.1 Implement social feature module
    - Create `frontend-eva/src/features/social/api.ts`: listThreads, createThread, getThread, createReply, flagPost, toggleUpvote
    - Create `frontend-eva/src/features/social/hooks.ts`: `useForumThreads()`, `useThread()`, `useCreateThread()`, `useCreateReply()`, `useUpvote()`
    - Create `frontend-eva/src/features/social/components/`:
      - `ThreadList`: paginated thread list sorted by activity
      - `ThreadDetail`: thread with replies, upvote buttons
      - `ThreadForm`: create new thread form
      - `ReplyForm`: reply to thread form
      - `ChatRoom`: real-time chat component with message list, input, auto-scroll
      - `ChatMessage`: individual message display
    - _Requirements: 13.1–13.6, 14.1–14.6_

  - [x] 27.2 Implement forum and chat pages
    - Create `frontend-eva/src/app/courses/[courseId]/forum/page.tsx`: course forum page with thread list and creation
    - Create `frontend-eva/src/app/courses/[courseId]/chat/page.tsx`: course chat page with WebSocket connection to `ws/chat/{course_id}/`
    - _Requirements: 13.1, 14.1, 24.1_

- [ ] 28. Frontend — Projects and peer review
  - [x] 28.1 Implement projects feature module
    - Create `frontend-eva/src/features/projects/api.ts`: getProject, submitProject, submitReview, getReviews
    - Create `frontend-eva/src/features/projects/hooks.ts`: `useProject()`, `useSubmitProject()`, `useSubmitReview()`, `useReviews()`
    - Create `frontend-eva/src/features/projects/components/`:
      - `ProjectDetail`: project description, rubric, deadline
      - `SubmissionForm`: file upload (max 5 files, 10MB each) + text description
      - `ReviewForm`: rubric criterion scoring + feedback textarea
      - `ReviewList`: display reviews (teacher + peer)
    - _Requirements: 18.1–18.6_

  - [x] 28.2 Implement project pages
    - Create `frontend-eva/src/app/projects/page.tsx`: project listing
    - Create `frontend-eva/src/app/projects/[projectId]/page.tsx`: project detail with submission and review
    - _Requirements: 18.1–18.6, 24.1_

- [ ] 29. Frontend — Collaborative learning
  - [x] 29.1 Implement collaboration feature module
    - Create `frontend-eva/src/features/collaboration/api.ts`: joinCollabExercise, submitGroupWork, getGroupInfo
    - Create `frontend-eva/src/features/collaboration/hooks.ts`: `useCollabGroup()`, `useJoinCollab()`, `useSubmitGroupWork()`
    - Create `frontend-eva/src/features/collaboration/components/`:
      - `CollabWorkspace`: shared workspace with real-time updates via WebSocket `ws/collab/{exercise_id}/{group_id}/`
      - `GroupMembers`: display group members and contribution status
      - `GroupSubmitForm`: group submission form
    - _Requirements: 17.1–17.5_

- [ ] 30. Frontend — Teacher dashboard
  - [x] 30.1 Implement teacher dashboard feature module
    - Create `frontend-eva/src/features/teacher/api.ts`: getCourseAnalytics, getStudentList, getStudentDetail, getHeatmap
    - Create `frontend-eva/src/features/teacher/hooks.ts`: `useCourseAnalytics()`, `useStudentList()`, `useStudentDetail()`, `useHeatmap()`
    - _Requirements: 15.1, 16.1–16.5_

  - [x] 30.2 Implement teacher dashboard pages
    - Create `frontend-eva/src/app/teacher/page.tsx`: teacher dashboard with course list (status, enrollment count, last modified)
    - Create `frontend-eva/src/app/teacher/analytics/[courseId]/page.tsx`: course analytics page with aggregate stats, student list, performance heatmap
    - _Requirements: 15.1, 16.1–16.4_

  - [x] 30.3 Implement course builder pages
    - Create `frontend-eva/src/app/teacher/courses/[courseId]/builder/page.tsx`: visual course builder with editable tree view (units → lessons → exercises)
    - Create `frontend-eva/src/features/teacher/components/`:
      - `CourseTree`: editable hierarchy tree
      - `ExerciseForm`: form for each exercise type with validation matching backend rules
      - `PublishButton`: publish with validation error display
      - `StudentAnalyticsTable`: student list with progress
      - `PerformanceHeatmap`: exercise accuracy heatmap visualization
    - _Requirements: 15.1–15.5, 16.1–16.4_

- [x] 31. Checkpoint — Verify all frontend features
  - Ensure all frontend tests pass, ask the user if questions arise.

- [ ] 32. Docker development environment
  - [x] 32.1 Create Docker Compose configuration
    - Create `docker-compose.yml` with 6 services:
      - `backend`: Django app (Dockerfile in backend-eva/), depends on postgres + redis, volume mount for source code, health check
      - `frontend`: React app (Dockerfile in frontend-eva/), volume mount for source code, hot-reload
      - `postgres`: PostgreSQL with health check, volume for data persistence
      - `redis`: Redis with health check, volume for data persistence
      - `celery-worker`: same image as backend, runs `celery -A config worker`, depends on postgres + redis + backend
      - `celery-beat`: same image as backend, runs `celery -A config beat`, depends on postgres + redis + backend
    - _Requirements: 23.1, 23.3, 23.4, 23.5_

  - [x] 32.2 Create Dockerfiles for backend and frontend
    - Create `backend-eva/Dockerfile`: Python base, UV for dependency management, install dependencies, copy source
    - Create `frontend-eva/Dockerfile`: Node/Bun base, install dependencies, copy source, Next.js dev server
    - _Requirements: 23.1_

  - [x] 32.3 Create environment configuration
    - Create `.env.example` with all required environment variables: DATABASE_URL, REDIS_URL, SECRET_KEY, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CELERY_BROKER_URL, EMAIL_* settings
    - Create `.env` (gitignored) with development defaults
    - _Requirements: 23.2_

  - [x] 32.4 Configure health checks and service dependencies
    - Add health checks for PostgreSQL (`pg_isready`) and Redis (`redis-cli ping`)
    - Configure backend service to wait for healthy postgres and redis using `depends_on` with `condition: service_healthy`
    - Configure Celery services to depend on backend
    - _Requirements: 23.5_

- [ ] 33. Final checkpoint — Full system verification
  - Ensure all backend and frontend tests pass
  - Verify Docker Compose starts all 6 services successfully
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical boundaries
- Property tests validate universal correctness properties from the design document (52 total)
- Unit tests validate specific examples and edge cases
- Backend tasks (3–19) come before frontend tasks (20–31) to ensure API availability
- Docker setup (32) comes last as it wraps the completed application
