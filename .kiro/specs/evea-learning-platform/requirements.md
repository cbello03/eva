# Requirements Document

## Introduction

EVA (Entorno Virtual de Enseñanza-Aprendizaje) is a production-grade learning platform inspired by Duolingo, extended with social, collaborative, and real-world learning features. The platform integrates four pedagogical models: Conductismo (reinforcement via XP, streaks, rewards), Cognitivismo (structured progression, adaptive learning, spaced repetition), Conectivismo (forums, real-time chat, peer interaction), and Constructivismo (collaborative exercises, real-world projects).

The system consists of a Django backend (`backend-eva`) and a React frontend (`frontend-eva`), deployed via Docker with PostgreSQL, Redis, Celery, and Django Channels.

## Glossary

- **EVA**: Entorno Virtual de Enseñanza-Aprendizaje — the learning platform system
- **Auth_Service**: The authentication and authorization subsystem handling JWT tokens, sessions, and role management
- **Course_Service**: The subsystem managing the Course → Unit → Lesson → Exercise content hierarchy
- **Exercise_Engine**: The subsystem responsible for rendering, validating, and scoring exercises
- **Gamification_Service**: The subsystem managing XP, levels, streaks, achievements, and leaderboards
- **Adaptive_Engine**: The subsystem that tracks learner weaknesses and adjusts difficulty dynamically
- **Social_Service**: The subsystem managing forums, real-time chat, and peer interactions
- **Teacher_Dashboard**: The interface and subsystem for course creation, lesson building, and student analytics
- **Collaboration_Service**: The subsystem managing group exercises, shared submissions, and team tasks
- **Project_Service**: The subsystem managing real-world project definitions, submissions, rubrics, and peer review
- **Analytics_Service**: The subsystem aggregating and presenting student progress, teacher insights, and performance data
- **Notification_Service**: The subsystem delivering real-time and asynchronous notifications to users
- **Student**: A user with the student role who consumes courses and completes exercises
- **Teacher**: A user with the teacher role who creates and manages courses and monitors student progress
- **Admin**: A user with the admin role who manages the platform, users, and system configuration
- **XP**: Experience points earned by completing exercises and activities
- **Streak**: A count of consecutive days a Student has completed at least one learning activity
- **Access_Token**: A short-lived JWT stored in memory, used to authenticate API requests
- **Refresh_Token**: A long-lived JWT stored in an httpOnly cookie, used to obtain new Access_Tokens
- **Spaced_Repetition**: A learning technique that schedules review of material at increasing intervals based on retention
- **Leaderboard**: A ranked list of Students ordered by XP within a defined time period
- **Rubric**: A scoring guide with defined criteria used to evaluate project submissions
- **Channel_Layer**: The Redis-backed Django Channels layer used for WebSocket communication

## Requirements

### Requirement 1: User Registration

**User Story:** As a visitor, I want to register an account on EVA, so that I can access the learning platform.

#### Acceptance Criteria

1. WHEN a visitor submits a valid registration form with email, password, and display name, THE Auth_Service SHALL create a new Student account and return a success response within 2 seconds
2. WHEN a visitor submits a registration form with an email already associated with an existing account, THE Auth_Service SHALL reject the registration and return a descriptive error indicating the email is already in use
3. THE Auth_Service SHALL hash all passwords using Django's default password hasher (PBKDF2) before storing them
4. WHEN a visitor submits a registration form with a password shorter than 8 characters or missing uppercase, lowercase, or numeric characters, THE Auth_Service SHALL reject the registration and return a validation error describing the password requirements
5. WHEN a visitor submits a registration form with an invalid email format, THE Auth_Service SHALL reject the registration and return a validation error

### Requirement 2: User Authentication (Login/Logout)

**User Story:** As a registered user, I want to log in and log out securely, so that I can access my personalized learning experience.

#### Acceptance Criteria

1. WHEN a user submits valid credentials (email and password), THE Auth_Service SHALL return an Access_Token in the response body and set a Refresh_Token as an httpOnly secure cookie
2. WHEN a user submits invalid credentials, THE Auth_Service SHALL return a generic authentication error without revealing whether the email or password was incorrect
3. THE Auth_Service SHALL set the Access_Token expiration to 15 minutes
4. THE Auth_Service SHALL set the Refresh_Token expiration to 7 days
5. WHEN a user sends a logout request, THE Auth_Service SHALL invalidate the current Refresh_Token and clear the httpOnly cookie
6. THE Auth_Service SHALL include CSRF protection on the Refresh_Token cookie

### Requirement 3: Token Refresh and Rotation

**User Story:** As an authenticated user, I want my session to persist seamlessly, so that I do not need to re-enter credentials frequently.

#### Acceptance Criteria

1. WHEN a user sends a request with a valid Refresh_Token, THE Auth_Service SHALL issue a new Access_Token and a new Refresh_Token (token rotation)
2. WHEN a user sends a request with an expired or invalid Refresh_Token, THE Auth_Service SHALL reject the request with a 401 status and clear the cookie
3. WHEN a previously used (rotated-out) Refresh_Token is presented, THE Auth_Service SHALL invalidate all Refresh_Tokens for that user (replay detection) and return a 401 status
4. THE Auth_Service SHALL store a token family identifier to detect Refresh_Token reuse across rotation chains

### Requirement 4: Role-Based Access Control

**User Story:** As a platform administrator, I want to enforce role-based permissions, so that users can only access features appropriate to their role.

#### Acceptance Criteria

1. THE Auth_Service SHALL support three roles: Student, Teacher, and Admin
2. WHEN an authenticated user requests a resource restricted to a role the user does not hold, THE Auth_Service SHALL return a 403 Forbidden response
3. THE Auth_Service SHALL include the user role in the Access_Token claims
4. WHEN an Admin assigns or changes a user role, THE Auth_Service SHALL update the role and invalidate existing tokens for that user
5. THE Auth_Service SHALL enforce role checks at the API layer before executing any service logic

### Requirement 5: Course Management

**User Story:** As a Teacher, I want to create and manage courses with a structured hierarchy, so that I can organize learning content effectively.

#### Acceptance Criteria

1. THE Course_Service SHALL enforce a four-level content hierarchy: Course → Unit → Lesson → Exercise
2. WHEN a Teacher creates a new Course, THE Course_Service SHALL require a title, description, and at least one Unit before publishing
3. WHEN a Teacher creates a Unit within a Course, THE Course_Service SHALL assign a sequential order number to the Unit
4. WHEN a Teacher creates a Lesson within a Unit, THE Course_Service SHALL assign a sequential order number to the Lesson
5. WHEN a Teacher reorders Units or Lessons, THE Course_Service SHALL update all affected order numbers to maintain a contiguous sequence
6. WHEN a Teacher publishes a Course, THE Course_Service SHALL validate that every Lesson contains at least one Exercise
7. WHEN a Student requests a Course listing, THE Course_Service SHALL return only published Courses
8. WHEN a Teacher requests a Course listing, THE Course_Service SHALL return both published and draft Courses owned by that Teacher

### Requirement 6: Exercise System

**User Story:** As a Teacher, I want to create diverse exercise types within lessons, so that Students can practice through varied question formats.

#### Acceptance Criteria

1. THE Exercise_Engine SHALL support four exercise types: multiple choice, fill in the blank, matching, and free text
2. WHEN a Teacher creates a multiple choice exercise, THE Exercise_Engine SHALL require at least two options and exactly one correct answer
3. WHEN a Teacher creates a fill in the blank exercise, THE Exercise_Engine SHALL require the blank position and a list of accepted answers (case-insensitive matching)
4. WHEN a Teacher creates a matching exercise, THE Exercise_Engine SHALL require at least two pairs of items to match
5. WHEN a Teacher creates a free text exercise, THE Exercise_Engine SHALL require a rubric or model answer for evaluation guidance
6. WHEN a Student submits an answer to a multiple choice, fill in the blank, or matching exercise, THE Exercise_Engine SHALL evaluate the answer and return immediate feedback indicating correctness within 500 milliseconds
7. WHEN a Student submits an answer to a free text exercise, THE Exercise_Engine SHALL store the submission for Teacher review and notify the Teacher via the Notification_Service

### Requirement 7: Lesson Player

**User Story:** As a Student, I want to complete lessons in an interactive, Duolingo-style player, so that I can learn through engaging exercise sequences.

#### Acceptance Criteria

1. WHEN a Student starts a Lesson, THE Exercise_Engine SHALL present exercises in the defined order within the Lesson
2. WHEN a Student answers an exercise correctly, THE Exercise_Engine SHALL display a positive feedback indicator and advance to the next exercise
3. WHEN a Student answers an exercise incorrectly, THE Exercise_Engine SHALL display the correct answer and queue the exercise for retry at the end of the Lesson
4. WHEN a Student completes all exercises in a Lesson (including retries), THE Exercise_Engine SHALL mark the Lesson as completed and award XP via the Gamification_Service
5. WHILE a Student is completing a Lesson, THE Exercise_Engine SHALL display a progress bar showing the percentage of exercises completed
6. IF a Student exits a Lesson before completion, THEN THE Exercise_Engine SHALL save the current progress and allow resumption from the last unanswered exercise

### Requirement 8: XP and Leveling System

**User Story:** As a Student, I want to earn XP and level up, so that I feel motivated to continue learning.

#### Acceptance Criteria

1. WHEN a Student completes a Lesson, THE Gamification_Service SHALL award XP based on the number of exercises answered correctly on the first attempt
2. WHEN a Student's total XP reaches a level threshold, THE Gamification_Service SHALL advance the Student to the next level and send a notification via the Notification_Service
3. THE Gamification_Service SHALL calculate level thresholds using a defined progression formula that increases XP requirements per level
4. WHEN a Student earns XP, THE Gamification_Service SHALL update the Student's total XP and current level in real time
5. THE Gamification_Service SHALL record all XP transactions with a timestamp, source (Lesson ID, achievement ID), and amount

### Requirement 9: Streak System

**User Story:** As a Student, I want to maintain a daily learning streak, so that I build a consistent study habit.

#### Acceptance Criteria

1. WHEN a Student completes at least one Lesson in a calendar day (based on the Student's timezone), THE Gamification_Service SHALL increment the Student's Streak count by one
2. WHEN a Student does not complete any Lesson in a calendar day, THE Gamification_Service SHALL reset the Student's Streak count to zero via a scheduled Celery task
3. THE Gamification_Service SHALL run the Streak reset task once daily at midnight UTC
4. WHEN a Student's Streak reaches a milestone (7, 30, 100, 365 days), THE Gamification_Service SHALL award a Streak achievement and bonus XP
5. THE Gamification_Service SHALL store the Student's current Streak count, longest Streak count, and last activity date

### Requirement 10: Achievements System

**User Story:** As a Student, I want to unlock achievements for reaching milestones, so that I have additional goals to pursue.

#### Acceptance Criteria

1. THE Gamification_Service SHALL support achievement definitions with a name, description, icon identifier, and unlock condition
2. WHEN a Student meets the unlock condition for an achievement, THE Gamification_Service SHALL grant the achievement and send a notification via the Notification_Service
3. THE Gamification_Service SHALL evaluate achievement conditions after each XP-granting event
4. WHEN a Student views their profile, THE Gamification_Service SHALL return a list of earned achievements and progress toward locked achievements
5. THE Gamification_Service SHALL prevent duplicate achievement grants for the same Student and achievement combination

### Requirement 11: Leaderboard

**User Story:** As a Student, I want to see how I rank against other learners, so that I feel competitive motivation.

#### Acceptance Criteria

1. THE Gamification_Service SHALL maintain Leaderboards for weekly and all-time periods
2. WHEN a Student requests the Leaderboard, THE Gamification_Service SHALL return the top 100 Students ranked by XP for the selected period
3. WHEN a Student requests the Leaderboard, THE Gamification_Service SHALL include the requesting Student's rank and XP even if the Student is not in the top 100
4. THE Gamification_Service SHALL update the weekly Leaderboard in near real-time (within 60 seconds of an XP change)
5. THE Gamification_Service SHALL reset the weekly Leaderboard every Monday at 00:00 UTC via a scheduled Celery task


### Requirement 12: Adaptive Learning

**User Story:** As a Student, I want the platform to adapt to my weaknesses, so that I spend more time on topics I struggle with.

#### Acceptance Criteria

1. WHEN a Student answers an exercise incorrectly, THE Adaptive_Engine SHALL record the topic, exercise type, and timestamp of the incorrect answer
2. THE Adaptive_Engine SHALL calculate a mastery score per topic for each Student based on the ratio of correct to total answers, weighted by recency
3. WHEN a Student starts a new Lesson in a Unit where the mastery score for any prerequisite topic is below 60%, THE Adaptive_Engine SHALL recommend a review session for the weak topic before proceeding
4. THE Adaptive_Engine SHALL schedule review exercises using Spaced_Repetition intervals (1 day, 3 days, 7 days, 14 days, 30 days) after an incorrect answer
5. WHEN the Adaptive_Engine generates a review session, THE Adaptive_Engine SHALL select exercises from the Student's weak topics, prioritizing topics with the lowest mastery scores
6. THE Adaptive_Engine SHALL adjust exercise difficulty within a Lesson based on the Student's recent performance: increase difficulty after 3 consecutive correct answers, decrease after 2 consecutive incorrect answers

### Requirement 13: Forum System

**User Story:** As a Student, I want to participate in course forums, so that I can ask questions and discuss topics with peers and Teachers.

#### Acceptance Criteria

1. THE Social_Service SHALL provide a thread-based forum for each Course
2. WHEN a user creates a new forum thread, THE Social_Service SHALL require a title and body, and associate the thread with the Course and the author
3. WHEN a user replies to a forum thread, THE Social_Service SHALL append the reply to the thread and notify the thread author via the Notification_Service
4. WHEN a user requests the forum thread list for a Course, THE Social_Service SHALL return threads sorted by most recent activity (latest reply or creation date) with pagination (20 threads per page)
5. WHEN a Teacher or Admin flags a forum post as inappropriate, THE Social_Service SHALL hide the post from public view and notify the post author
6. THE Social_Service SHALL support upvoting on forum replies, and display the vote count alongside each reply

### Requirement 14: Real-Time Chat

**User Story:** As a Student, I want to chat in real time with other learners in my course, so that I can collaborate and get quick help.

#### Acceptance Criteria

1. THE Social_Service SHALL provide a real-time chat room for each Course using Django Channels and the Channel_Layer
2. WHEN an authenticated user sends a chat message, THE Social_Service SHALL broadcast the message to all connected users in the same Course chat room within 1 second
3. WHEN a user connects to a Course chat room, THE Social_Service SHALL deliver the last 50 messages as chat history
4. THE Social_Service SHALL persist all chat messages to the database for retrieval
5. WHEN a user who is not enrolled in a Course attempts to join the Course chat room, THE Social_Service SHALL reject the WebSocket connection with an appropriate error
6. IF a WebSocket connection is lost, THEN THE Social_Service SHALL allow the client to reconnect and resume receiving messages without duplication

### Requirement 15: Teacher Dashboard — Course Builder

**User Story:** As a Teacher, I want a dashboard to create and edit courses with a visual builder, so that I can efficiently author learning content.

#### Acceptance Criteria

1. WHEN a Teacher accesses the Teacher_Dashboard, THE Teacher_Dashboard SHALL display a list of all Courses owned by the Teacher with status (draft, published), enrollment count, and last modified date
2. WHEN a Teacher opens the course builder, THE Teacher_Dashboard SHALL display the Course hierarchy (Units, Lessons, Exercises) in an editable tree view
3. WHEN a Teacher adds, edits, or removes a Unit, Lesson, or Exercise, THE Teacher_Dashboard SHALL save changes via the Course_Service API and reflect the updated hierarchy immediately
4. WHEN a Teacher uses the lesson builder, THE Teacher_Dashboard SHALL provide a form for each exercise type (multiple choice, fill in the blank, matching, free text) with validation matching the Exercise_Engine requirements
5. WHEN a Teacher clicks publish on a Course, THE Teacher_Dashboard SHALL invoke the Course_Service publish validation and display any validation errors preventing publication

### Requirement 16: Teacher Dashboard — Student Analytics

**User Story:** As a Teacher, I want to view analytics about my students' performance, so that I can identify struggling students and improve my courses.

#### Acceptance Criteria

1. WHEN a Teacher selects a Course in the Teacher_Dashboard, THE Analytics_Service SHALL display aggregate statistics: total enrolled Students, average completion rate, average score, and average time per Lesson
2. WHEN a Teacher views the student list for a Course, THE Analytics_Service SHALL display each Student's progress percentage, current score, Streak count, and last activity date
3. WHEN a Teacher selects a specific Student, THE Analytics_Service SHALL display a detailed progress view showing completion status and score per Unit and Lesson
4. THE Analytics_Service SHALL generate a performance heatmap showing exercise accuracy rates across topics for a Course
5. THE Analytics_Service SHALL aggregate analytics data via scheduled Celery tasks, updating at least once every hour

### Requirement 17: Collaborative Learning

**User Story:** As a Student, I want to work on group exercises with my peers, so that I can learn through collaboration.

#### Acceptance Criteria

1. WHEN a Teacher creates a collaborative exercise, THE Collaboration_Service SHALL allow the Teacher to define a group size (2 to 5 Students)
2. WHEN a Student joins a collaborative exercise, THE Collaboration_Service SHALL assign the Student to a group, creating a new group if no existing group has available slots
3. WHILE a group is working on a collaborative exercise, THE Collaboration_Service SHALL provide a shared workspace visible to all group members in real time via Django Channels
4. WHEN a group submits a collaborative exercise, THE Collaboration_Service SHALL record the submission for all group members and award XP equally to each member via the Gamification_Service
5. IF a group member does not contribute within 48 hours of the exercise start, THEN THE Collaboration_Service SHALL notify the group member and the Teacher via the Notification_Service

### Requirement 18: Real-World Projects

**User Story:** As a Student, I want to complete real-world projects with defined rubrics, so that I can apply my learning to practical scenarios.

#### Acceptance Criteria

1. WHEN a Teacher creates a project, THE Project_Service SHALL require a title, description, rubric with scored criteria, and a submission deadline
2. WHEN a Student submits a project, THE Project_Service SHALL accept file uploads (max 10 MB per file, max 5 files) and a text description, and record the submission timestamp
3. WHEN a Student submits a project after the deadline, THE Project_Service SHALL accept the submission but flag it as late
4. WHEN a Teacher reviews a project submission, THE Project_Service SHALL allow the Teacher to score each rubric criterion and provide written feedback
5. WHERE peer review is enabled for a project, THE Project_Service SHALL assign each submission to 2 other Students for review after the submission deadline
6. WHEN a peer reviewer submits a review, THE Project_Service SHALL record the scores and feedback and make the review visible to the submission author after all assigned reviews are complete

### Requirement 19: Notification System

**User Story:** As a user, I want to receive timely notifications about relevant events, so that I stay informed about my learning activities.

#### Acceptance Criteria

1. THE Notification_Service SHALL support two delivery channels: in-app (real-time via WebSocket) and email (asynchronous via Celery)
2. WHEN a notification event occurs (achievement unlock, forum reply, project review, streak milestone, group activity), THE Notification_Service SHALL create a notification record and deliver it via the configured channels
3. WHEN a user is connected via WebSocket, THE Notification_Service SHALL deliver in-app notifications in real time
4. WHEN a user has unread notifications, THE Notification_Service SHALL return the unread count in API responses via a dedicated endpoint
5. WHEN a user marks a notification as read, THE Notification_Service SHALL update the notification status and decrement the unread count
6. THE Notification_Service SHALL process email notifications via Celery worker tasks with a retry policy of 3 attempts with exponential backoff

### Requirement 20: Student Progress Tracking

**User Story:** As a Student, I want to view my learning progress across all courses, so that I can understand my advancement and plan my study.

#### Acceptance Criteria

1. WHEN a Student accesses the progress dashboard, THE Analytics_Service SHALL display overall statistics: total XP, current level, current Streak, courses enrolled, and courses completed
2. WHEN a Student selects a Course, THE Analytics_Service SHALL display progress per Unit and Lesson, showing completion status and score
3. THE Analytics_Service SHALL calculate and display a mastery percentage per topic based on exercise accuracy
4. WHEN a Student views the progress dashboard, THE Analytics_Service SHALL display a calendar heatmap of daily learning activity for the past 90 days
5. THE Analytics_Service SHALL update Student progress data in real time after each Lesson completion

### Requirement 21: Rate Limiting and API Security

**User Story:** As a platform administrator, I want to protect the API from abuse, so that the platform remains available and performant for all users.

#### Acceptance Criteria

1. THE Auth_Service SHALL enforce rate limiting on the login endpoint: a maximum of 10 requests per minute per IP address
2. THE Auth_Service SHALL enforce rate limiting on the registration endpoint: a maximum of 5 requests per minute per IP address
3. WHEN a client exceeds the rate limit, THE Auth_Service SHALL return a 429 Too Many Requests response with a Retry-After header
4. THE EVA API SHALL validate all input data using Pydantic schemas before processing any request
5. THE EVA API SHALL sanitize all user-generated text content to prevent XSS attacks before storing it in the database
6. THE EVA API SHALL enforce CORS policies allowing only the configured frontend origin

### Requirement 22: Course Enrollment

**User Story:** As a Student, I want to enroll in courses, so that I can access course content and track my progress.

#### Acceptance Criteria

1. WHEN a Student requests enrollment in a published Course, THE Course_Service SHALL create an enrollment record linking the Student to the Course
2. WHEN a Student attempts to enroll in a Course in which the Student is already enrolled, THE Course_Service SHALL return an error indicating duplicate enrollment
3. WHEN a Student enrolls in a Course, THE Course_Service SHALL initialize progress tracking for all Units and Lessons in the Course via the Analytics_Service
4. WHEN a Student requests their enrolled courses, THE Course_Service SHALL return the list of Courses with enrollment date and current progress percentage
5. WHEN a Student unenrolls from a Course, THE Course_Service SHALL mark the enrollment as inactive and retain the progress data for potential re-enrollment

### Requirement 23: Docker Development Environment

**User Story:** As a developer, I want a fully Dockerized development environment, so that I can run the entire platform locally with a single command.

#### Acceptance Criteria

1. THE EVA system SHALL provide a Docker Compose configuration defining services for: backend (Django), frontend (React), PostgreSQL, Redis, Celery worker, and Celery beat
2. THE EVA system SHALL use environment variables loaded from a .env file for all service configuration (database credentials, secret keys, Redis URL, allowed hosts)
3. WHEN a developer runs `docker compose up`, THE EVA system SHALL start all services and make the frontend accessible on a configured port and the backend API accessible on a separate configured port
4. THE EVA system SHALL use volume mounts for backend and frontend source code to enable hot-reloading during development
5. THE EVA system SHALL include a health check for the PostgreSQL and Redis services, and the backend service SHALL wait for healthy dependencies before starting

### Requirement 24: Frontend Application Shell

**User Story:** As a Student, I want a responsive, fast-loading web application, so that I can learn comfortably on any device.

#### Acceptance Criteria

1. THE EVA frontend SHALL use Next.js App Router with file-based routing (route groups, layouts, and pages in `src/app/`) for all page navigation
2. THE EVA frontend SHALL use TanStack Query for all server state management and API data fetching
3. THE EVA frontend SHALL use Zustand for client-side state management (authentication state, UI state)
4. THE EVA frontend SHALL use MUI components as the base component library with a custom theme
5. THE EVA frontend SHALL use Tailwind CSS for utility styling alongside MUI components, with a custom theme defined in `src/app/theme.ts`
6. THE EVA frontend SHALL implement Next.js loading conventions (`loading.tsx`) and React Suspense with fallback loading indicators for all route-level components
7. THE EVA frontend SHALL store the Access_Token in memory (Zustand store) and never persist it to localStorage or sessionStorage
8. WHEN the Access_Token expires, THE EVA frontend SHALL automatically request a new token using the Refresh_Token cookie before retrying the failed request
