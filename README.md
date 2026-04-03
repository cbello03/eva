# EVA - Plataforma Educativa (Entorno Virtual de Aprendizaje) 🚀

EVA es una plataforma educativa integral diseñada para ofrecer una experiencia de aprendizaje moderna, interactiva y gamificada. El proyecto está dividido en un frontend reactivo con las últimas tecnologías web y un backend eficiente basado en Python.

---

## 🌟 Características Principales

### Para Estudiantes 🎓
- **Dashboard Personalizado:** Seguimiento detallado del progreso, cursos activos y próximas tareas.
- **Aprendizaje Interactivo:** Lecciones fluidas con diversos tipos de ejercicios (opción múltiple, completar espacios).
- **Gamificación:** Sistema de logros e insignias, y una tabla de posiciones (Leaderboard) global.
- **Análisis de Progreso:** Visualización clara de la maestría por temas mediante gráficosHeatmaps y mastery charts.
- **Colaboración:** Foros de discusión por curso y chats en tiempo real.

### Para Profesores 👨‍🏫
- **Gestión de Cursos:** Herramientas para crear y organizar contenido educativo de manera intuitiva.
- **Monitoreo de Estudiantes:** Visión general del rendimiento y participación del grupo.

---

## 💻 Stack Tecnológico

### Frontend (`/frontend-eva`)
- **Framework:** [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Lenguaje:** [TypeScript](https://www.typescriptlang.org/)
- **UI/UX:** [Material UI (MUI)](https://mui.com/), [Framer Motion](https://www.framer.com/motion/) (para animaciones fluidas) y [Emotion](https://emotion.sh/).
- **Enrutamiento:** [TanStack Router](https://tanstack.com/router) (type-safe routing).
- **Gestión de Estado y Datos:** [TanStack Query](https://tanstack.com/query) y [Zustand](https://zustand-demo.pmnd.rs/).
- **Formularios:** React Hook Form + Zod.
- **Internacionalización:** i18next (Multi-idioma ready).

### Backend (`/backend-eva`)
- **Lenguaje:** Python
- **Gestión de Dependencias:** [uv](https://github.com/astral-sh/uv) (gestor de paquetes de alto rendimiento).
- **Framework:** Basado en Python (Django/FastAPI).

---

## 🛠️ Instalación y Configuración

### Prerrequisitos
- [Node.js](https://nodejs.org/) (recomendado v18+) o [Bun](https://bun.sh/).
- [Python 3.11+](https://www.python.org/).

### Configuración del Frontend
1. Navega al directorio del frontend:
   ```bash
   cd frontend-eva/frontend-eva
   ```
2. Instala las dependencias:
   ```bash
   bun install
   # o npm install
   ```
3. Inicia el servidor de desarrollo:
   ```bash
   bun run dev
   ```

### Configuración del Backend
1. Navega al directorio del backend:
   ```bash
   cd backend-eva
   ```
2. Sigue las instrucciones específicas en el [README del backend](./backend-eva/README.md).

---

## 👨‍💻 Contribución

1. Haz un **Fork** del proyecto.
2. Crea una nueva rama (**Branch**): `git checkout -b feature/NuevaFuncionalidad`.
3. Haz tus cambios y **Commit**: `git commit -am 'Añadir nueva funcionalidad'`.
4. Sube tus cambios (**Push**): `git push origin feature/NuevaFuncionalidad`.
5. Abre un **Pull Request**.

---

## 📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

Desarrollado con ❤️ por [Tu Nombre/Empresa].
