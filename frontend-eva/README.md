# EVA - Entorno Virtual de Aprendizaje (Frontend)

Este repositorio contiene la arquitectura **Frontend Premium** de la plataforma colaborativa de aprendizaje EVA, desarrollada como un Minimum Viable Product (MVP) altamente escalable. Fue construida poniendo máxima atención al rendimiento, calidad de UI/UX, animaciones fluidas y seguridad tipada.

![EVA Learning Platform Banner](https://img.shields.io/badge/Status-Beta%20Ready-success?style=for-the-badge&logo=appveyor)

## 🚀 Tecnologías Core (The Stack)

*   **⚡ Vite + React + TypeScript:** Ecosistema moderno compaginado con una estricta configuración de tipeo TS.
*   **🛣️ TanStack Router:** Enrutamiento de última generación, con seguridad de tipos en cada URL (cargos asíncronos y precaching veloz).
*   **📡 TanStack Query (React Query):** Motor robusto para manejo de estado asíncrono y promesas HTTP, listo para conectar a REST APIs complejas.
*   **🐻 Zustand:** Manejo del estado central de la app. Reemplaza por completo el viejo *Redux* y los frágiles *React Context*, dando una performance atómica asombrosa para el estado de autenticación (Tokens) y roles.
*   **🎭 Material UI (MUI v6):** Todo el sistema visual y de componentes atómicos. Totalmente sobrescrito a nivel de Theme `palette` para obtener una estética de Dark Mode Premium (Slate/Índigo/Pink).
*   **🛡️ Zod + React Hook Form:** Validación de formularios estructurada y segura en la capa del navegador, blindando las entradas de datos (`/login`, `/register`).
*   **✨ Framer Motion:** Para coreografiar de forma experta la manera en la que los Skeletons de carga, la navegación y las tarjetas interactúan en la pantalla.
*   **🌍 i18Next:** Motor de internacionalización dinámico integrado con banderas de la barra lateral (Listo para operar bilingüe: ES/EN).

## 🎓 Características Destacadas de esta Megabuild

1.  **Diseño Oscuro Premium (Dark Mode):** Creado en base a tonos profundos Slate (`#0f172a`, `#1e293b`), cristalización sutil de bordes (Glassmorphism), fuentes de alta legibilidad *Google Fonts (Inter & Outfit)* y detalles interactivos que simulan la estética de grandes dashboards como Vercel o GitHub.
2.  **Dashboard Colaborativo & Gamificación:** Rutas preparadas simulando un tablero personal donde cada lección y ejercicio múltiple finalizado incrementa la puntuación (XP), desbloqueando insignias secretas.
3.  **Sala de Clases Virtual Responsiva (`LessonViewer`):** Recreamos de la nada la sección más sagrada de una escuela online. Contiene: Reproductor de inmersión multimedia falso, motor lector de teóricos en formato markdown, y un Quiz interactivo validado.
4.  **Responsive Layout Drawer:** Navegación por Drawer Lateral completamente resuelta para escalabilidad. Fijo en monitores grandes `.permanent` y retráctil en teléfonos mediante Menú de Hamburguesa `.temporary`.

## ⚙️ Estructura del Código

```text
src/
├── app/        # Config inicial de Providers y superposición de Themes MIUI
├── components/ # Atomic UI y componentes abstractos de la App (Layout Sidebar Responsive)
├── features/   # Cada bloque conceptual separado limpiamente (auth, progress, exercises, admin)
├── routes/     # TanStack Tree (Aquí viven el Dashboard, Perfil, Cursos, Salas de Clase, Login)
└── lib/        # API Client & Interceptores (El MockAxios y la conexión WebSocket actual)
```

## 🔧 Instrucciones para Correr la Arquitectura Local
Como la plataforma usa manejadores de ambiente modernos *(Bun / Vite)*, iniciarla es inmediato:

```bash
# 1. Instalar dependencias si usas npm (aunque idealmente usamos Bun)
bun install

# 2. Levantar el proyecto corriendo en el puerto 3004
bun run dev

# 3. Compilar para un servidor real de producción
bun run build
```

---
*Mantenido por Joseph Orrorque en 2026. Proyecto Front-End finalizado listo para acoplar bases de datos de Backend (Go/Python).*
