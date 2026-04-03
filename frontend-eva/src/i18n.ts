import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

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
      "view_all": "View all",
      "view_profile": "View Profile",
      "logout": "Sign Out",
      "learning_progress": "Learning Progress",
      "linear_progress": "Linear progress",
      "activity": "Activity",
      "graphs": "Graphs",
      "gamification_achievements": "Gamification & Achievements",
      "recent_badges": "Recent Badges",
      "upcoming_challenges": "Upcoming Challenges",
      "leaderboard": "Leaderboard",
      "continue": "Continue",
      
      // Profile & Gamification
      "profile_achievements_title": "My Achievements",
      "profile_achievements_desc": "Complete lessons and maintain your streak to unlock rewards.",
      "no_achievements": "No achievements available on the platform yet.",
      "unlocked_on": "Unlocked on:",
      "locked": "Locked",
      "level": "Level",
      "total_xp": "XP Total",

      // Landing
      "landing_news": "New: EVA 2.0 is out! 🚀",
      "landing_title": "The Next Generation of",
      "landing_title_hl": "Learning",
      "landing_desc": "EVA is a premium Virtual Learning Environment, designed with extreme gamification to boost your academic experience. Take the leap to the future.",

      // Login
      "login_title": "Welcome Back",
      "login_subtitle": "Sign in to access Eva Learning",
      "login_invalid": "Invalid credentials or network error.",
      "login_email": "Email Address",
      "login_password": "Password",
      "login_btn": "Sign In",
      "login_btn_pending": "Authenticating...",
      "login_no_account": "Don't have an account? Sign up",

      // Register
      "register_title": "Create an Account",
      "register_subtitle": "Join Eva Learning and unlock your potential",
      "register_error": "Registration failed. Email might be in use.",
      "register_username": "Username",
      "register_btn": "Sign Up",
      "register_btn_pending": "Registering...",
      "register_has_account": "Already have an account? Sign in",
      "learn_more": "Start Learning",

      // Settings
      "settings_title": "Preferences & Settings",
      "settings_subtitle": "Manage your account, appearance, and language preferences.",
      "settings_language": "Language",
      "settings_language_desc": "Select your preferred language for the interface.",
      "settings_theme": "Theme",
      "settings_theme_desc": "Choose between light or dark mode.",
      "settings_notifications": "Notifications",
      "settings_notifications_desc": "Receive email alerts about your courses and achievements.",
      "settings_save": "Save Changes",
      "settings_saved": "Settings saved successfully!",
      "settings_profile": "Profile Menu"
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
      "view_all": "Ver todos",
      "view_profile": "Ver Perfil",
      "logout": "Cerrar Sesión",
      "learning_progress": "Progreso de Aprendizaje",
      "linear_progress": "Avance lineal",
      "activity": "Actividad",
      "graphs": "Gráficos",
      "gamification_achievements": "Gamificación y Logros",
      "recent_badges": "Insignias recientes",
      "upcoming_challenges": "Próximos Desafíos",
      "leaderboard": "Clasificación",
      "continue": "Continuar",

      // Profile & Gamification
      "profile_achievements_title": "Mis Logros",
      "profile_achievements_desc": "Completa lecciones y mantén tu racha para desbloquear recompensas.",
      "no_achievements": "Aún no hay logros disponibles en la plataforma.",
      "unlocked_on": "Obtenido el:",
      "locked": "Bloqueado",
      "level": "Nivel",
      "total_xp": "XP Total",

      // Landing
      "landing_news": "Novedad: ¡EVA 2.0 está disponible! 🚀",
      "landing_title": "La Siguiente Generación del",
      "landing_title_hl": "Aprendizaje",
      "landing_desc": "EVA es un Entorno Virtual de Enseñanza-Aprendizaje premium, diseñado con gamificación extrema para potenciar tu experiencia académica. Da el salto al futuro.",

      // Login
      "login_title": "Bienvenido de nuevo",
      "login_subtitle": "Inicia sesión para acceder a Eva Learning",
      "login_invalid": "Credenciales inválidas o error de conexión.",
      "login_email": "Correo Electrónico",
      "login_password": "Contraseña",
      "login_btn": "Entrar",
      "login_btn_pending": "Autenticando...",
      "login_no_account": "¿No tienes una cuenta? Regístrate",

      // Register
      "register_title": "Crea una Cuenta",
      "register_subtitle": "Únete a Eva Learning y desbloquea tu potencial",
      "register_error": "Error al registrar. El correo podría estar en uso.",
      "register_username": "Nombre de usuario",
      "register_btn": "Registrarse",
      "register_btn_pending": "Registrando...",
      "register_has_account": "¿Ya tienes una cuenta? Inicia Sesión",
      "learn_more": "Comenzar Gratis",

      // Settings
      "settings_title": "Preferencias y Ajustes",
      "settings_subtitle": "Gestiona tu cuenta, apariencia y preferencias de idioma.",
      "settings_language": "Idioma",
      "settings_language_desc": "Selecciona tu idioma preferido para la interfaz.",
      "settings_theme": "Tema",
      "settings_theme_desc": "Elige entre el modo claro y oscuro.",
      "settings_notifications": "Notificaciones",
      "settings_notifications_desc": "Recibe alertas por correo sobre tus cursos y logros.",
      "settings_save": "Guardar Cambios",
      "settings_saved": "¡Configuración guardada exitosamente!",
      "settings_profile": "Menú de Perfil"
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
      escapeValue: false,
    }
  });

export default i18n;
