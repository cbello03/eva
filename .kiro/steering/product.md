# EVA — Product Overview

EVA (Entorno Virtual de Enseñanza-Aprendizaje) is a production-grade learning platform inspired by Duolingo, extended with social, collaborative, and real-world applied learning features.

## Pedagogical Models

The platform integrates four pedagogical models:
- Behaviorism: XP, streaks, rewards, leaderboards
- Cognitivism: structured progression, adaptive learning, spaced repetition
- Connectivism: forums, real-time chat, peer interaction
- Constructivism: collaborative exercises, real-world projects with rubrics and peer review

## User Roles

- Student: consumes courses, completes exercises, earns XP
- Teacher: creates/manages courses, reviews submissions, views analytics
- Admin: manages platform, users, and system configuration

## Core Domains

- Authentication (JWT with token rotation and family-based replay detection)
- Courses (Course → Unit → Lesson → Exercise hierarchy)
- Exercise Engine (multiple choice, fill-blank, matching, free text + Duolingo-style lesson player)
- Gamification (XP, levels, streaks, achievements, leaderboards)
- Adaptive Learning (mastery scores, spaced repetition, difficulty adjustment)
- Social (threaded forums per course, real-time chat via WebSocket)
- Collaboration (group exercises with shared workspaces)
- Projects (real-world projects with rubrics, deadlines, peer review)
- Notifications (in-app via WebSocket + email via Celery)
- Analytics (student progress dashboards, teacher analytics with heatmaps)

## Language

Project documentation (requirements, design, tasks) is written in Spanish. Code, comments, and variable names are in English.
