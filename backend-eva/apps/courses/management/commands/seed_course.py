"""Seed a demo course: Introducción a la Informática con Python."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import Exercise, ExerciseType
from apps.projects.models import Project

COURSE_TITLE = "Introducción a la Informática con Python"
COURSE_DESC = (
    "Curso introductorio que cubre los fundamentos de la programación "
    "utilizando Python. Aprenderás desde variables y tipos de datos hasta "
    "estructuras de control, funciones y manejo básico de archivos."
)

UNITS = [
    {
        "title": "Fundamentos de Python",
        "lessons": [
            {
                "title": "Variables y tipos de datos",
                "exercises": [
                    {
                        "type": ExerciseType.MULTIPLE_CHOICE,
                        "question": "¿Cuál de los siguientes es un tipo de dato válido en Python?",
                        "difficulty": 1,
                        "topic": "tipos de datos",
                        "config": {
                            "options": [
                                {"id": "a", "text": "int"},
                                {"id": "b", "text": "number"},
                                {"id": "c", "text": "decimal"},
                                {"id": "d", "text": "integer"},
                            ],
                            "correct": "a",
                        },
                    },
                    {
                        "type": ExerciseType.FILL_BLANK,
                        "question": "Para asignar el valor 10 a una variable llamada edad, escribimos: edad ___ 10",
                        "difficulty": 1,
                        "topic": "variables",
                        "config": {
                            "blanks": [{"id": "b1", "correct": "="}],
                        },
                    },
                    {
                        "type": ExerciseType.MATCHING,
                        "question": "Relaciona cada tipo de dato con su ejemplo:",
                        "difficulty": 1,
                        "topic": "tipos de datos",
                        "config": {
                            "pairs": [
                                {"left": "int", "right": "42"},
                                {"left": "str", "right": '"hola"'},
                                {"left": "float", "right": "3.14"},
                                {"left": "bool", "right": "True"},
                            ],
                        },
                    },
                ],
            },
            {
                "title": "Operadores y expresiones",
                "exercises": [
                    {
                        "type": ExerciseType.MULTIPLE_CHOICE,
                        "question": "¿Qué operador se usa para la división entera en Python?",
                        "difficulty": 1,
                        "topic": "operadores",
                        "config": {
                            "options": [
                                {"id": "a", "text": "/"},
                                {"id": "b", "text": "//"},
                                {"id": "c", "text": "%"},
                                {"id": "d", "text": "**"},
                            ],
                            "correct": "b",
                        },
                    },
                    {
                        "type": ExerciseType.FILL_BLANK,
                        "question": "El resultado de 10 ___ 3 es 1 (resto de la división).",
                        "difficulty": 1,
                        "topic": "operadores",
                        "config": {
                            "blanks": [{"id": "b1", "correct": "%"}],
                        },
                    },
                ],
            },
        ],
    },
    {
        "title": "Estructuras de control",
        "lessons": [
            {
                "title": "Condicionales (if, elif, else)",
                "exercises": [
                    {
                        "type": ExerciseType.MULTIPLE_CHOICE,
                        "question": "¿Qué palabra clave se usa para evaluar una segunda condición en Python?",
                        "difficulty": 2,
                        "topic": "condicionales",
                        "config": {
                            "options": [
                                {"id": "a", "text": "else if"},
                                {"id": "b", "text": "elseif"},
                                {"id": "c", "text": "elif"},
                                {"id": "d", "text": "elsif"},
                            ],
                            "correct": "c",
                        },
                    },
                    {
                        "type": ExerciseType.FREE_TEXT,
                        "question": "Escribe un bloque if-else que imprima 'mayor' si la variable x es mayor que 10, y 'menor o igual' en caso contrario.",
                        "difficulty": 2,
                        "topic": "condicionales",
                        "config": {
                            "sample_answer": "if x > 10:\n    print('mayor')\nelse:\n    print('menor o igual')",
                            "keywords": ["if", "else", "print", ">", "10"],
                        },
                    },
                ],
            },
            {
                "title": "Bucles (for y while)",
                "exercises": [
                    {
                        "type": ExerciseType.FILL_BLANK,
                        "question": "Para recorrer una lista llamada frutas, escribimos: ___ fruta in frutas:",
                        "difficulty": 2,
                        "topic": "bucles",
                        "config": {
                            "blanks": [{"id": "b1", "correct": "for"}],
                        },
                    },
                    {
                        "type": ExerciseType.MATCHING,
                        "question": "Relaciona cada tipo de bucle con su caso de uso:",
                        "difficulty": 2,
                        "topic": "bucles",
                        "config": {
                            "pairs": [
                                {"left": "for", "right": "Recorrer una secuencia conocida"},
                                {"left": "while", "right": "Repetir mientras se cumpla una condición"},
                                {"left": "break", "right": "Salir del bucle inmediatamente"},
                                {"left": "continue", "right": "Saltar a la siguiente iteración"},
                            ],
                        },
                    },
                    {
                        "type": ExerciseType.MULTIPLE_CHOICE,
                        "question": "¿Cuántas veces se ejecuta el cuerpo de: for i in range(5)?",
                        "difficulty": 1,
                        "topic": "bucles",
                        "config": {
                            "options": [
                                {"id": "a", "text": "4"},
                                {"id": "b", "text": "5"},
                                {"id": "c", "text": "6"},
                                {"id": "d", "text": "Depende de i"},
                            ],
                            "correct": "b",
                        },
                    },
                ],
            },
        ],
    },
    {
        "title": "Funciones y módulos",
        "lessons": [
            {
                "title": "Definición de funciones",
                "exercises": [
                    {
                        "type": ExerciseType.FILL_BLANK,
                        "question": "Para definir una función en Python usamos la palabra clave: ___",
                        "difficulty": 2,
                        "topic": "funciones",
                        "config": {
                            "blanks": [{"id": "b1", "correct": "def"}],
                        },
                    },
                    {
                        "type": ExerciseType.FREE_TEXT,
                        "question": "Escribe una función llamada 'suma' que reciba dos parámetros y retorne su suma.",
                        "difficulty": 2,
                        "topic": "funciones",
                        "config": {
                            "sample_answer": "def suma(a, b):\n    return a + b",
                            "keywords": ["def", "suma", "return"],
                        },
                    },
                ],
            },
            {
                "title": "Parámetros y retorno",
                "exercises": [
                    {
                        "type": ExerciseType.MULTIPLE_CHOICE,
                        "question": "¿Qué retorna una función en Python si no tiene sentencia return?",
                        "difficulty": 2,
                        "topic": "funciones",
                        "config": {
                            "options": [
                                {"id": "a", "text": "0"},
                                {"id": "b", "text": "None"},
                                {"id": "c", "text": '""'},
                                {"id": "d", "text": "Error"},
                            ],
                            "correct": "b",
                        },
                    },
                ],
            },
        ],
    },
]

PROJECTS = [
    {
        "title": "Calculadora interactiva",
        "description": (
            "Crea un programa en Python que funcione como calculadora interactiva. "
            "Debe soportar las cuatro operaciones básicas (+, -, *, /), validar la "
            "entrada del usuario y manejar errores como la división por cero. "
            "El programa debe ejecutarse en un bucle hasta que el usuario elija salir."
        ),
        "rubric": [
            {"criterion": "Funcionalidad completa (4 operaciones)", "max_score": 30},
            {"criterion": "Validación de entrada y manejo de errores", "max_score": 25},
            {"criterion": "Uso correcto de funciones", "max_score": 20},
            {"criterion": "Legibilidad del código y comentarios", "max_score": 15},
            {"criterion": "Bucle principal y opción de salida", "max_score": 10},
        ],
        "peer_review_enabled": True,
    },
    {
        "title": "Juego de adivinanza de números",
        "description": (
            "Desarrolla un juego donde el programa genera un número aleatorio entre "
            "1 y 100, y el usuario debe adivinarlo. El programa debe dar pistas "
            "('más alto' o 'más bajo') y contar los intentos. Al final, muestra "
            "el número de intentos utilizados."
        ),
        "rubric": [
            {"criterion": "Generación de número aleatorio correcta", "max_score": 20},
            {"criterion": "Lógica de comparación y pistas", "max_score": 25},
            {"criterion": "Contador de intentos", "max_score": 15},
            {"criterion": "Uso de bucles y condicionales", "max_score": 25},
            {"criterion": "Experiencia de usuario (mensajes claros)", "max_score": 15},
        ],
        "peer_review_enabled": False,
    },
]


class Command(BaseCommand):
    help = "Seed a demo course: Introducción a la Informática con Python."

    def handle(self, *args, **options):
        # Ensure teacher exists
        teacher = User.objects.filter(role=Role.TEACHER).first()
        if not teacher:
            self.stderr.write(self.style.ERROR(
                "No teacher found. Run 'seed_users' first."
            ))
            return

        # Idempotent: skip if course already exists
        if Course.objects.filter(title=COURSE_TITLE).exists():
            self.stdout.write("  ⏭  Course already exists, skipping.")
            return

        # Create course
        course = Course.objects.create(
            title=COURSE_TITLE,
            description=COURSE_DESC,
            teacher=teacher,
            status=Course.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"  ✔  Course: {course.title}"))

        # Create units → lessons → exercises
        for unit_order, unit_data in enumerate(UNITS, start=1):
            unit = Unit.objects.create(
                course=course, title=unit_data["title"], order=unit_order
            )
            self.stdout.write(f"     Unit {unit_order}: {unit.title}")

            for lesson_order, lesson_data in enumerate(unit_data["lessons"], start=1):
                lesson = Lesson.objects.create(
                    unit=unit, title=lesson_data["title"], order=lesson_order
                )
                self.stdout.write(f"       Lesson {lesson_order}: {lesson.title}")

                for ex_order, ex_data in enumerate(lesson_data["exercises"], start=1):
                    Exercise.objects.create(
                        lesson=lesson,
                        exercise_type=ex_data["type"],
                        question_text=ex_data["question"],
                        order=ex_order,
                        config=ex_data["config"],
                        difficulty=ex_data["difficulty"],
                        topic=ex_data["topic"],
                    )
                self.stdout.write(f"         {len(lesson_data['exercises'])} exercises")

        # Create projects
        for proj_data in PROJECTS:
            Project.objects.create(
                course=course,
                teacher=teacher,
                title=proj_data["title"],
                description=proj_data["description"],
                rubric=proj_data["rubric"],
                submission_deadline=timezone.now() + timedelta(days=30),
                peer_review_enabled=proj_data["peer_review_enabled"],
            )
            self.stdout.write(self.style.SUCCESS(f"  ✔  Project: {proj_data['title']}"))

        # Enroll demo student if exists
        student = User.objects.filter(role=Role.STUDENT).first()
        if student:
            Enrollment.objects.create(student=student, course=course)
            self.stdout.write(self.style.SUCCESS(f"  ✔  Enrolled {student.email}"))

        self.stdout.write(self.style.SUCCESS("\nDone. Demo course seeded."))
