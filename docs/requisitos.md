# Documento de Requisitos

## Introducción

EVA (Entorno Virtual de Enseñanza-Aprendizaje) es una plataforma de aprendizaje de nivel productivo inspirada en Duolingo, ampliada con funcionalidades sociales, colaborativas y de aprendizaje aplicado al mundo real. La plataforma integra cuatro modelos pedagógicos: Conductismo (refuerzo mediante XP, rachas, recompensas), Cognitivismo (progresión estructurada, aprendizaje adaptativo, repetición espaciada), Conectivismo (foros, chat en tiempo real, interacción entre pares) y Constructivismo (ejercicios colaborativos, proyectos del mundo real).

El sistema consta de un backend en Django (`backend-eva`) y un frontend en React (`frontend-eva`), desplegado mediante Docker con PostgreSQL, Redis, Celery y Django Channels.

## Glosario

- **EVA**: Entorno Virtual de Enseñanza-Aprendizaje — el sistema de la plataforma de aprendizaje
- **Auth_Service**: El subsistema de autenticación y autorización que gestiona tokens JWT, sesiones y administración de roles
- **Course_Service**: El subsistema que gestiona la jerarquía de contenido Curso → Unidad → Lección → Ejercicio
- **Exercise_Engine**: El subsistema responsable de renderizar, validar y calificar ejercicios
- **Gamification_Service**: El subsistema que gestiona XP, niveles, rachas, logros y tablas de clasificación
- **Adaptive_Engine**: El subsistema que rastrea las debilidades del estudiante y ajusta la dificultad de forma dinámica
- **Social_Service**: El subsistema que gestiona foros, chat en tiempo real e interacciones entre pares
- **Teacher_Dashboard**: La interfaz y subsistema para la creación de cursos, construcción de lecciones y analíticas de estudiantes
- **Collaboration_Service**: El subsistema que gestiona ejercicios grupales, entregas compartidas y tareas en equipo
- **Project_Service**: El subsistema que gestiona definiciones de proyectos del mundo real, entregas, rúbricas y revisión entre pares
- **Analytics_Service**: El subsistema que agrega y presenta el progreso de los estudiantes, información para docentes y datos de rendimiento
- **Notification_Service**: El subsistema que entrega notificaciones en tiempo real y asíncronas a los usuarios
- **Student**: Un usuario con el rol de estudiante que consume cursos y completa ejercicios
- **Teacher**: Un usuario con el rol de docente que crea y gestiona cursos y monitorea el progreso de los estudiantes
- **Admin**: Un usuario con el rol de administrador que gestiona la plataforma, los usuarios y la configuración del sistema
- **XP**: Puntos de experiencia obtenidos al completar ejercicios y actividades
- **Streak**: Un conteo de días consecutivos en los que un Student ha completado al menos una actividad de aprendizaje
- **Access_Token**: Un JWT de corta duración almacenado en memoria, utilizado para autenticar solicitudes a la API
- **Refresh_Token**: Un JWT de larga duración almacenado en una cookie httpOnly, utilizado para obtener nuevos Access_Tokens
- **Spaced_Repetition**: Una técnica de aprendizaje que programa la revisión de material a intervalos crecientes basados en la retención
- **Leaderboard**: Una lista clasificada de Students ordenados por XP dentro de un período de tiempo definido
- **Rubric**: Una guía de calificación con criterios definidos utilizada para evaluar entregas de proyectos
- **Channel_Layer**: La capa de Django Channels respaldada por Redis utilizada para la comunicación por WebSocket

## Requisitos

### Requisito 1: Registro de Usuarios

**Historia de Usuario:** Como visitante, quiero registrar una cuenta en EVA, para poder acceder a la plataforma de aprendizaje.

#### Criterios de Aceptación

1. CUANDO un visitante envía un formulario de registro válido con correo electrónico, contraseña y nombre para mostrar, Auth_Service DEBE crear una nueva cuenta de Student y devolver una respuesta exitosa en un máximo de 2 segundos
2. CUANDO un visitante envía un formulario de registro con un correo electrónico ya asociado a una cuenta existente, Auth_Service DEBE rechazar el registro y devolver un error descriptivo indicando que el correo electrónico ya está en uso
3. Auth_Service DEBE cifrar todas las contraseñas utilizando el hasher de contraseñas predeterminado de Django (PBKDF2) antes de almacenarlas
4. CUANDO un visitante envía un formulario de registro con una contraseña de menos de 8 caracteres o sin caracteres en mayúscula, minúscula o numéricos, Auth_Service DEBE rechazar el registro y devolver un error de validación describiendo los requisitos de la contraseña
5. CUANDO un visitante envía un formulario de registro con un formato de correo electrónico inválido, Auth_Service DEBE rechazar el registro y devolver un error de validación

### Requisito 2: Autenticación de Usuarios (Inicio/Cierre de Sesión)

**Historia de Usuario:** Como usuario registrado, quiero iniciar y cerrar sesión de forma segura, para poder acceder a mi experiencia de aprendizaje personalizada.

#### Criterios de Aceptación

1. CUANDO un usuario envía credenciales válidas (correo electrónico y contraseña), Auth_Service DEBE devolver un Access_Token en el cuerpo de la respuesta y establecer un Refresh_Token como una cookie httpOnly segura
2. CUANDO un usuario envía credenciales inválidas, Auth_Service DEBE devolver un error de autenticación genérico sin revelar si el correo electrónico o la contraseña fueron incorrectos
3. Auth_Service DEBE establecer la expiración del Access_Token en 15 minutos
4. Auth_Service DEBE establecer la expiración del Refresh_Token en 7 días
5. CUANDO un usuario envía una solicitud de cierre de sesión, Auth_Service DEBE invalidar el Refresh_Token actual y limpiar la cookie httpOnly
6. Auth_Service DEBE incluir protección CSRF en la cookie del Refresh_Token

### Requisito 3: Renovación y Rotación de Tokens

**Historia de Usuario:** Como usuario autenticado, quiero que mi sesión persista de forma transparente, para no tener que volver a ingresar mis credenciales con frecuencia.

#### Criterios de Aceptación

1. CUANDO un usuario envía una solicitud con un Refresh_Token válido, Auth_Service DEBE emitir un nuevo Access_Token y un nuevo Refresh_Token (rotación de tokens)
2. CUANDO un usuario envía una solicitud con un Refresh_Token expirado o inválido, Auth_Service DEBE rechazar la solicitud con un estado 401 y limpiar la cookie
3. CUANDO se presenta un Refresh_Token previamente utilizado (rotado), Auth_Service DEBE invalidar todos los Refresh_Tokens de ese usuario (detección de reutilización) y devolver un estado 401
4. Auth_Service DEBE almacenar un identificador de familia de tokens para detectar la reutilización de Refresh_Token a través de cadenas de rotación

### Requisito 4: Control de Acceso Basado en Roles

**Historia de Usuario:** Como administrador de la plataforma, quiero aplicar permisos basados en roles, para que los usuarios solo puedan acceder a las funcionalidades apropiadas para su rol.

#### Criterios de Aceptación

1. Auth_Service DEBE soportar tres roles: Student, Teacher y Admin
2. CUANDO un usuario autenticado solicita un recurso restringido a un rol que el usuario no posee, Auth_Service DEBE devolver una respuesta 403 Forbidden
3. Auth_Service DEBE incluir el rol del usuario en las claims del Access_Token
4. CUANDO un Admin asigna o cambia el rol de un usuario, Auth_Service DEBE actualizar el rol e invalidar los tokens existentes de ese usuario
5. Auth_Service DEBE aplicar las verificaciones de rol en la capa de la API antes de ejecutar cualquier lógica de servicio

### Requisito 5: Gestión de Cursos

**Historia de Usuario:** Como Teacher, quiero crear y gestionar cursos con una jerarquía estructurada, para poder organizar el contenido de aprendizaje de manera efectiva.

#### Criterios de Aceptación

1. Course_Service DEBE aplicar una jerarquía de contenido de cuatro niveles: Curso → Unidad → Lección → Ejercicio
2. CUANDO un Teacher crea un nuevo Curso, Course_Service DEBE requerir un título, una descripción y al menos una Unidad antes de publicar
3. CUANDO un Teacher crea una Unidad dentro de un Curso, Course_Service DEBE asignar un número de orden secuencial a la Unidad
4. CUANDO un Teacher crea una Lección dentro de una Unidad, Course_Service DEBE asignar un número de orden secuencial a la Lección
5. CUANDO un Teacher reordena Unidades o Lecciones, Course_Service DEBE actualizar todos los números de orden afectados para mantener una secuencia contigua
6. CUANDO un Teacher publica un Curso, Course_Service DEBE validar que cada Lección contenga al menos un Ejercicio
7. CUANDO un Student solicita un listado de Cursos, Course_Service DEBE devolver únicamente los Cursos publicados
8. CUANDO un Teacher solicita un listado de Cursos, Course_Service DEBE devolver tanto los Cursos publicados como los borradores pertenecientes a ese Teacher

### Requisito 6: Sistema de Ejercicios

**Historia de Usuario:** Como Teacher, quiero crear diversos tipos de ejercicios dentro de las lecciones, para que los Students puedan practicar mediante formatos de preguntas variados.

#### Criterios de Aceptación

1. Exercise_Engine DEBE soportar cuatro tipos de ejercicios: opción múltiple, completar espacios en blanco, emparejamiento y texto libre
2. CUANDO un Teacher crea un ejercicio de opción múltiple, Exercise_Engine DEBE requerir al menos dos opciones y exactamente una respuesta correcta
3. CUANDO un Teacher crea un ejercicio de completar espacios en blanco, Exercise_Engine DEBE requerir la posición del espacio en blanco y una lista de respuestas aceptadas (coincidencia sin distinción de mayúsculas y minúsculas)
4. CUANDO un Teacher crea un ejercicio de emparejamiento, Exercise_Engine DEBE requerir al menos dos pares de elementos para emparejar
5. CUANDO un Teacher crea un ejercicio de texto libre, Exercise_Engine DEBE requerir una rúbrica o respuesta modelo como guía de evaluación
6. CUANDO un Student envía una respuesta a un ejercicio de opción múltiple, completar espacios en blanco o emparejamiento, Exercise_Engine DEBE evaluar la respuesta y devolver retroalimentación inmediata indicando la corrección en un máximo de 500 milisegundos
7. CUANDO un Student envía una respuesta a un ejercicio de texto libre, Exercise_Engine DEBE almacenar la entrega para revisión del Teacher y notificar al Teacher a través del Notification_Service

### Requisito 7: Reproductor de Lecciones

**Historia de Usuario:** Como Student, quiero completar lecciones en un reproductor interactivo estilo Duolingo, para poder aprender mediante secuencias de ejercicios atractivas.

#### Criterios de Aceptación

1. CUANDO un Student inicia una Lección, Exercise_Engine DEBE presentar los ejercicios en el orden definido dentro de la Lección
2. CUANDO un Student responde un ejercicio correctamente, Exercise_Engine DEBE mostrar un indicador de retroalimentación positiva y avanzar al siguiente ejercicio
3. CUANDO un Student responde un ejercicio incorrectamente, Exercise_Engine DEBE mostrar la respuesta correcta y poner en cola el ejercicio para reintento al final de la Lección
4. CUANDO un Student completa todos los ejercicios de una Lección (incluyendo reintentos), Exercise_Engine DEBE marcar la Lección como completada y otorgar XP a través del Gamification_Service
5. MIENTRAS un Student está completando una Lección, Exercise_Engine DEBE mostrar una barra de progreso indicando el porcentaje de ejercicios completados
6. SI un Student sale de una Lección antes de completarla, ENTONCES Exercise_Engine DEBE guardar el progreso actual y permitir la reanudación desde el último ejercicio sin responder

### Requisito 8: Sistema de XP y Nivelación

**Historia de Usuario:** Como Student, quiero ganar XP y subir de nivel, para sentirme motivado a continuar aprendiendo.

#### Criterios de Aceptación

1. CUANDO un Student completa una Lección, Gamification_Service DEBE otorgar XP basado en la cantidad de ejercicios respondidos correctamente en el primer intento
2. CUANDO el XP total de un Student alcanza un umbral de nivel, Gamification_Service DEBE avanzar al Student al siguiente nivel y enviar una notificación a través del Notification_Service
3. Gamification_Service DEBE calcular los umbrales de nivel utilizando una fórmula de progresión definida que incrementa los requisitos de XP por nivel
4. CUANDO un Student gana XP, Gamification_Service DEBE actualizar el XP total y el nivel actual del Student en tiempo real
5. Gamification_Service DEBE registrar todas las transacciones de XP con una marca de tiempo, origen (ID de Lección, ID de logro) y cantidad

### Requisito 9: Sistema de Rachas

**Historia de Usuario:** Como Student, quiero mantener una racha de aprendizaje diaria, para construir un hábito de estudio consistente.

#### Criterios de Aceptación

1. CUANDO un Student completa al menos una Lección en un día calendario (basado en la zona horaria del Student), Gamification_Service DEBE incrementar el conteo de Streak del Student en uno
2. CUANDO un Student no completa ninguna Lección en un día calendario, Gamification_Service DEBE restablecer el conteo de Streak del Student a cero mediante una tarea programada de Celery
3. Gamification_Service DEBE ejecutar la tarea de restablecimiento de Streak una vez al día a medianoche UTC
4. CUANDO el Streak de un Student alcanza un hito (7, 30, 100, 365 días), Gamification_Service DEBE otorgar un logro de Streak y XP de bonificación
5. Gamification_Service DEBE almacenar el conteo actual de Streak del Student, el conteo de Streak más largo y la fecha de última actividad

### Requisito 10: Sistema de Logros

**Historia de Usuario:** Como Student, quiero desbloquear logros al alcanzar hitos, para tener objetivos adicionales que perseguir.

#### Criterios de Aceptación

1. Gamification_Service DEBE soportar definiciones de logros con un nombre, descripción, identificador de ícono y condición de desbloqueo
2. CUANDO un Student cumple la condición de desbloqueo de un logro, Gamification_Service DEBE otorgar el logro y enviar una notificación a través del Notification_Service
3. Gamification_Service DEBE evaluar las condiciones de logros después de cada evento que otorgue XP
4. CUANDO un Student visualiza su perfil, Gamification_Service DEBE devolver una lista de logros obtenidos y el progreso hacia los logros bloqueados
5. Gamification_Service DEBE prevenir la concesión duplicada de logros para la misma combinación de Student y logro

### Requisito 11: Tabla de Clasificación

**Historia de Usuario:** Como Student, quiero ver cómo me clasifico frente a otros estudiantes, para sentir motivación competitiva.

#### Criterios de Aceptación

1. Gamification_Service DEBE mantener Leaderboards para períodos semanal y de todos los tiempos
2. CUANDO un Student solicita el Leaderboard, Gamification_Service DEBE devolver los 100 mejores Students clasificados por XP para el período seleccionado
3. CUANDO un Student solicita el Leaderboard, Gamification_Service DEBE incluir la clasificación y el XP del Student solicitante incluso si el Student no está entre los 100 mejores
4. Gamification_Service DEBE actualizar el Leaderboard semanal en tiempo casi real (dentro de los 60 segundos posteriores a un cambio de XP)
5. Gamification_Service DEBE restablecer el Leaderboard semanal cada lunes a las 00:00 UTC mediante una tarea programada de Celery


### Requisito 12: Aprendizaje Adaptativo

**Historia de Usuario:** Como Student, quiero que la plataforma se adapte a mis debilidades, para dedicar más tiempo a los temas en los que tengo dificultades.

#### Criterios de Aceptación

1. CUANDO un Student responde un ejercicio incorrectamente, Adaptive_Engine DEBE registrar el tema, tipo de ejercicio y marca de tiempo de la respuesta incorrecta
2. Adaptive_Engine DEBE calcular una puntuación de dominio por tema para cada Student basada en la proporción de respuestas correctas sobre el total, ponderada por recencia
3. CUANDO un Student inicia una nueva Lección en una Unidad donde la puntuación de dominio de cualquier tema prerrequisito está por debajo del 60%, Adaptive_Engine DEBE recomendar una sesión de repaso del tema débil antes de continuar
4. Adaptive_Engine DEBE programar ejercicios de repaso utilizando intervalos de Spaced_Repetition (1 día, 3 días, 7 días, 14 días, 30 días) después de una respuesta incorrecta
5. CUANDO Adaptive_Engine genera una sesión de repaso, Adaptive_Engine DEBE seleccionar ejercicios de los temas débiles del Student, priorizando los temas con las puntuaciones de dominio más bajas
6. Adaptive_Engine DEBE ajustar la dificultad de los ejercicios dentro de una Lección basándose en el rendimiento reciente del Student: aumentar la dificultad después de 3 respuestas correctas consecutivas, disminuir después de 2 respuestas incorrectas consecutivas

### Requisito 13: Sistema de Foros

**Historia de Usuario:** Como Student, quiero participar en los foros del curso, para poder hacer preguntas y discutir temas con compañeros y Teachers.

#### Criterios de Aceptación

1. Social_Service DEBE proporcionar un foro basado en hilos para cada Curso
2. CUANDO un usuario crea un nuevo hilo en el foro, Social_Service DEBE requerir un título y un cuerpo, y asociar el hilo con el Curso y el autor
3. CUANDO un usuario responde a un hilo del foro, Social_Service DEBE agregar la respuesta al hilo y notificar al autor del hilo a través del Notification_Service
4. CUANDO un usuario solicita la lista de hilos del foro de un Curso, Social_Service DEBE devolver los hilos ordenados por actividad más reciente (última respuesta o fecha de creación) con paginación (20 hilos por página)
5. CUANDO un Teacher o Admin marca una publicación del foro como inapropiada, Social_Service DEBE ocultar la publicación de la vista pública y notificar al autor de la publicación
6. Social_Service DEBE soportar votos positivos en las respuestas del foro, y mostrar el conteo de votos junto a cada respuesta

### Requisito 14: Chat en Tiempo Real

**Historia de Usuario:** Como Student, quiero chatear en tiempo real con otros estudiantes de mi curso, para poder colaborar y obtener ayuda rápida.

#### Criterios de Aceptación

1. Social_Service DEBE proporcionar una sala de chat en tiempo real para cada Curso utilizando Django Channels y el Channel_Layer
2. CUANDO un usuario autenticado envía un mensaje de chat, Social_Service DEBE transmitir el mensaje a todos los usuarios conectados en la misma sala de chat del Curso en un máximo de 1 segundo
3. CUANDO un usuario se conecta a una sala de chat de un Curso, Social_Service DEBE entregar los últimos 50 mensajes como historial de chat
4. Social_Service DEBE persistir todos los mensajes de chat en la base de datos para su recuperación
5. CUANDO un usuario que no está inscrito en un Curso intenta unirse a la sala de chat del Curso, Social_Service DEBE rechazar la conexión WebSocket con un error apropiado
6. SI una conexión WebSocket se pierde, ENTONCES Social_Service DEBE permitir al cliente reconectarse y reanudar la recepción de mensajes sin duplicación

### Requisito 15: Panel del Docente — Constructor de Cursos

**Historia de Usuario:** Como Teacher, quiero un panel de control para crear y editar cursos con un constructor visual, para poder crear contenido de aprendizaje de manera eficiente.

#### Criterios de Aceptación

1. CUANDO un Teacher accede al Teacher_Dashboard, Teacher_Dashboard DEBE mostrar una lista de todos los Cursos pertenecientes al Teacher con estado (borrador, publicado), cantidad de inscripciones y fecha de última modificación
2. CUANDO un Teacher abre el constructor de cursos, Teacher_Dashboard DEBE mostrar la jerarquía del Curso (Unidades, Lecciones, Ejercicios) en una vista de árbol editable
3. CUANDO un Teacher agrega, edita o elimina una Unidad, Lección o Ejercicio, Teacher_Dashboard DEBE guardar los cambios a través de la API del Course_Service y reflejar la jerarquía actualizada inmediatamente
4. CUANDO un Teacher utiliza el constructor de lecciones, Teacher_Dashboard DEBE proporcionar un formulario para cada tipo de ejercicio (opción múltiple, completar espacios en blanco, emparejamiento, texto libre) con validación que coincida con los requisitos del Exercise_Engine
5. CUANDO un Teacher hace clic en publicar un Curso, Teacher_Dashboard DEBE invocar la validación de publicación del Course_Service y mostrar cualquier error de validación que impida la publicación

### Requisito 16: Panel del Docente — Analíticas de Estudiantes

**Historia de Usuario:** Como Teacher, quiero ver analíticas sobre el rendimiento de mis estudiantes, para poder identificar estudiantes con dificultades y mejorar mis cursos.

#### Criterios de Aceptación

1. CUANDO un Teacher selecciona un Curso en el Teacher_Dashboard, Analytics_Service DEBE mostrar estadísticas agregadas: total de Students inscritos, tasa promedio de finalización, puntuación promedio y tiempo promedio por Lección
2. CUANDO un Teacher visualiza la lista de estudiantes de un Curso, Analytics_Service DEBE mostrar el porcentaje de progreso de cada Student, puntuación actual, conteo de Streak y fecha de última actividad
3. CUANDO un Teacher selecciona un Student específico, Analytics_Service DEBE mostrar una vista detallada de progreso mostrando el estado de finalización y puntuación por Unidad y Lección
4. Analytics_Service DEBE generar un mapa de calor de rendimiento mostrando las tasas de precisión en ejercicios por temas para un Curso
5. Analytics_Service DEBE agregar los datos de analíticas mediante tareas programadas de Celery, actualizándose al menos una vez cada hora

### Requisito 17: Aprendizaje Colaborativo

**Historia de Usuario:** Como Student, quiero trabajar en ejercicios grupales con mis compañeros, para poder aprender a través de la colaboración.

#### Criterios de Aceptación

1. CUANDO un Teacher crea un ejercicio colaborativo, Collaboration_Service DEBE permitir al Teacher definir un tamaño de grupo (de 2 a 5 Students)
2. CUANDO un Student se une a un ejercicio colaborativo, Collaboration_Service DEBE asignar al Student a un grupo, creando un nuevo grupo si ningún grupo existente tiene espacios disponibles
3. MIENTRAS un grupo está trabajando en un ejercicio colaborativo, Collaboration_Service DEBE proporcionar un espacio de trabajo compartido visible para todos los miembros del grupo en tiempo real a través de Django Channels
4. CUANDO un grupo envía un ejercicio colaborativo, Collaboration_Service DEBE registrar la entrega para todos los miembros del grupo y otorgar XP equitativamente a cada miembro a través del Gamification_Service
5. SI un miembro del grupo no contribuye dentro de las 48 horas posteriores al inicio del ejercicio, ENTONCES Collaboration_Service DEBE notificar al miembro del grupo y al Teacher a través del Notification_Service

### Requisito 18: Proyectos del Mundo Real

**Historia de Usuario:** Como Student, quiero completar proyectos del mundo real con rúbricas definidas, para poder aplicar mi aprendizaje a escenarios prácticos.

#### Criterios de Aceptación

1. CUANDO un Teacher crea un proyecto, Project_Service DEBE requerir un título, descripción, rúbrica con criterios puntuados y una fecha límite de entrega
2. CUANDO un Student entrega un proyecto, Project_Service DEBE aceptar cargas de archivos (máximo 10 MB por archivo, máximo 5 archivos) y una descripción de texto, y registrar la marca de tiempo de la entrega
3. CUANDO un Student entrega un proyecto después de la fecha límite, Project_Service DEBE aceptar la entrega pero marcarla como tardía
4. CUANDO un Teacher revisa la entrega de un proyecto, Project_Service DEBE permitir al Teacher calificar cada criterio de la rúbrica y proporcionar retroalimentación escrita
5. DONDE la revisión entre pares está habilitada para un proyecto, Project_Service DEBE asignar cada entrega a 2 otros Students para revisión después de la fecha límite de entrega
6. CUANDO un revisor par envía una revisión, Project_Service DEBE registrar las puntuaciones y la retroalimentación y hacer visible la revisión al autor de la entrega después de que todas las revisiones asignadas estén completas

### Requisito 19: Sistema de Notificaciones

**Historia de Usuario:** Como usuario, quiero recibir notificaciones oportunas sobre eventos relevantes, para mantenerme informado sobre mis actividades de aprendizaje.

#### Criterios de Aceptación

1. Notification_Service DEBE soportar dos canales de entrega: dentro de la aplicación (en tiempo real vía WebSocket) y correo electrónico (asíncrono vía Celery)
2. CUANDO ocurre un evento de notificación (desbloqueo de logro, respuesta en foro, revisión de proyecto, hito de racha, actividad grupal), Notification_Service DEBE crear un registro de notificación y entregarlo a través de los canales configurados
3. CUANDO un usuario está conectado vía WebSocket, Notification_Service DEBE entregar las notificaciones dentro de la aplicación en tiempo real
4. CUANDO un usuario tiene notificaciones sin leer, Notification_Service DEBE devolver el conteo de no leídas en las respuestas de la API a través de un endpoint dedicado
5. CUANDO un usuario marca una notificación como leída, Notification_Service DEBE actualizar el estado de la notificación y decrementar el conteo de no leídas
6. Notification_Service DEBE procesar las notificaciones por correo electrónico mediante tareas de trabajadores Celery con una política de reintentos de 3 intentos con retroceso exponencial

### Requisito 20: Seguimiento del Progreso del Estudiante

**Historia de Usuario:** Como Student, quiero ver mi progreso de aprendizaje en todos los cursos, para poder comprender mi avance y planificar mi estudio.

#### Criterios de Aceptación

1. CUANDO un Student accede al panel de progreso, Analytics_Service DEBE mostrar estadísticas generales: XP total, nivel actual, Streak actual, cursos inscritos y cursos completados
2. CUANDO un Student selecciona un Curso, Analytics_Service DEBE mostrar el progreso por Unidad y Lección, indicando el estado de finalización y la puntuación
3. Analytics_Service DEBE calcular y mostrar un porcentaje de dominio por tema basado en la precisión en los ejercicios
4. CUANDO un Student visualiza el panel de progreso, Analytics_Service DEBE mostrar un mapa de calor de calendario de la actividad de aprendizaje diaria de los últimos 90 días
5. Analytics_Service DEBE actualizar los datos de progreso del Student en tiempo real después de cada finalización de Lección

### Requisito 21: Limitación de Tasa y Seguridad de la API

**Historia de Usuario:** Como administrador de la plataforma, quiero proteger la API contra abusos, para que la plataforma permanezca disponible y con buen rendimiento para todos los usuarios.

#### Criterios de Aceptación

1. Auth_Service DEBE aplicar limitación de tasa en el endpoint de inicio de sesión: un máximo de 10 solicitudes por minuto por dirección IP
2. Auth_Service DEBE aplicar limitación de tasa en el endpoint de registro: un máximo de 5 solicitudes por minuto por dirección IP
3. CUANDO un cliente excede el límite de tasa, Auth_Service DEBE devolver una respuesta 429 Too Many Requests con un encabezado Retry-After
4. La API de EVA DEBE validar todos los datos de entrada utilizando esquemas Pydantic antes de procesar cualquier solicitud
5. La API de EVA DEBE sanitizar todo el contenido de texto generado por usuarios para prevenir ataques XSS antes de almacenarlo en la base de datos
6. La API de EVA DEBE aplicar políticas CORS permitiendo únicamente el origen del frontend configurado

### Requisito 22: Inscripción en Cursos

**Historia de Usuario:** Como Student, quiero inscribirme en cursos, para poder acceder al contenido del curso y hacer seguimiento de mi progreso.

#### Criterios de Aceptación

1. CUANDO un Student solicita la inscripción en un Curso publicado, Course_Service DEBE crear un registro de inscripción vinculando al Student con el Curso
2. CUANDO un Student intenta inscribirse en un Curso en el que ya está inscrito, Course_Service DEBE devolver un error indicando inscripción duplicada
3. CUANDO un Student se inscribe en un Curso, Course_Service DEBE inicializar el seguimiento de progreso para todas las Unidades y Lecciones del Curso a través del Analytics_Service
4. CUANDO un Student solicita sus cursos inscritos, Course_Service DEBE devolver la lista de Cursos con fecha de inscripción y porcentaje de progreso actual
5. CUANDO un Student se desinscribe de un Curso, Course_Service DEBE marcar la inscripción como inactiva y retener los datos de progreso para una posible reinscripción

### Requisito 23: Entorno de Desarrollo con Docker

**Historia de Usuario:** Como desarrollador, quiero un entorno de desarrollo completamente Dockerizado, para poder ejecutar toda la plataforma localmente con un solo comando.

#### Criterios de Aceptación

1. El sistema EVA DEBE proporcionar una configuración de Docker Compose definiendo servicios para: backend (Django), frontend (React), PostgreSQL, Redis, trabajador Celery y Celery beat
2. El sistema EVA DEBE utilizar variables de entorno cargadas desde un archivo .env para toda la configuración de servicios (credenciales de base de datos, claves secretas, URL de Redis, hosts permitidos)
3. CUANDO un desarrollador ejecuta `docker compose up`, el sistema EVA DEBE iniciar todos los servicios y hacer accesible el frontend en un puerto configurado y la API del backend en un puerto configurado separado
4. El sistema EVA DEBE utilizar montajes de volúmenes para el código fuente del backend y frontend para habilitar la recarga en caliente durante el desarrollo
5. El sistema EVA DEBE incluir una verificación de salud para los servicios de PostgreSQL y Redis, y el servicio de backend DEBE esperar a que las dependencias estén saludables antes de iniciar

### Requisito 24: Shell de la Aplicación Frontend

**Historia de Usuario:** Como Student, quiero una aplicación web responsiva y de carga rápida, para poder aprender cómodamente en cualquier dispositivo.

#### Criterios de Aceptación

1. El frontend de EVA DEBE utilizar TanStack Router con enrutamiento basado en archivos para toda la navegación de páginas
2. El frontend de EVA DEBE utilizar TanStack Query para toda la gestión de estado del servidor y obtención de datos de la API
3. El frontend de EVA DEBE utilizar Zustand para la gestión de estado del lado del cliente (estado de autenticación, estado de la interfaz de usuario)
4. El frontend de EVA DEBE utilizar componentes MUI como la biblioteca de componentes base con un tema personalizado
5. El frontend de EVA DEBE utilizar módulos CSS para todo el estilizado personalizado, sin frameworks CSS de utilidades
6. El frontend de EVA DEBE implementar React Suspense con indicadores de carga de respaldo para todos los componentes a nivel de ruta
7. El frontend de EVA DEBE almacenar el Access_Token en memoria (almacén Zustand) y nunca persistirlo en localStorage o sessionStorage
8. CUANDO el Access_Token expira, el frontend de EVA DEBE solicitar automáticamente un nuevo token utilizando la cookie del Refresh_Token antes de reintentar la solicitud fallida
