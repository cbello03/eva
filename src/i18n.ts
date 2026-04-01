import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// The translations
const resources = {
  en: {
    translation: {
      "dashboard_title": "Dashboard",
      "my_courses": "My Courses",
      "assignments": "Assignments",
      "achievements": "Achievements",
      "community": "Community",
      "settings": "Settings",
      "search_placeholder": "Search",
      "hello": "Good morning, {{name}}!",
      "new_badge": "NEW",
      "view_details": "View Details",
      "course_catalog": "Course Catalog",
      "filter_categories": "Filter Categories",
      "login_btn": "Sign In",
      "register_btn": "Sign Up",
      "learn_more": "Start Learning",
      // ... Add more over time
    }
  },
  es: {
    translation: {
      "dashboard_title": "Panel Principal",
      "my_courses": "Mis Cursos",
      "assignments": "Tareas",
      "achievements": "Logros",
      "community": "Comunidad",
      "settings": "Configuración",
      "search_placeholder": "Buscar",
      "hello": "¡Buenos días, {{name}}!",
      "new_badge": "NUEVO",
      "view_details": "Ver Detalles",
      "course_catalog": "Catálogo de Cursos",
      "filter_categories": "Filtrar Categorías",
      "login_btn": "Iniciar Sesión",
      "register_btn": "Registrarse",
      "learn_more": "Comenzar Gratis",
      // ... Add more over time
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    interpolation: {
      escapeValue: false, // react already safes from xss
    }
  });

export default i18n;
