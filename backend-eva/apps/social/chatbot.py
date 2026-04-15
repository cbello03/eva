"""Course-scoped chatbot service using LangChain + LangGraph + Gemini."""

from __future__ import annotations

from typing import TypedDict

from django.conf import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from apps.courses.models import Unit
from apps.social.services import ForumService
from common.exceptions import DomainError


class ChatbotUnavailableError(DomainError):
    status_code = 503
    code = "chatbot_unavailable"

    def __init__(self, detail: str = "Course chatbot is not configured"):
        super().__init__(detail)


class ChatbotState(TypedDict):
    question: str
    mode: str
    history: list[dict[str, str]]
    course_context: str
    answer: str


class CourseChatbotService:
    """Answers questions strictly limited to the current course context."""

    _graph = None

    @staticmethod
    def _build_course_context(course) -> str:
        units = (
            Unit.objects.filter(course=course)
            .prefetch_related("lessons__exercises")
            .order_by("order")
        )

        context_lines = [
            f"Curso: {course.title}",
            f"Descripcion: {course.description}",
            "",
            "Estructura del curso:",
        ]
        for unit in units:
            context_lines.append(f"- Unidad {unit.order}: {unit.title}")
            lessons = list(unit.lessons.all().order_by("order"))
            for lesson in lessons:
                context_lines.append(f"  - Leccion {lesson.order}: {lesson.title}")
                exercises = list(lesson.exercises.all().order_by("order"))
                for exercise in exercises:
                    topic = exercise.topic or "sin tema"
                    context_lines.append(
                        f"    - Ejercicio {exercise.order} [{exercise.exercise_type}] ({topic}): {exercise.question_text}"
                    )
            if not lessons:
                context_lines.append("  - Sin lecciones")

        if not units:
            context_lines.append("- Curso sin unidades definidas")

        return "\n".join(context_lines)

    @classmethod
    def _get_graph(cls):
        if cls._graph is not None:
            return cls._graph

        if not settings.GEMINI_API_KEY:
            raise ChatbotUnavailableError(
                "Missing GEMINI_API_KEY in environment configuration"
            )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
        )

        def answer_node(state: ChatbotState) -> dict[str, str]:
            mode = state.get("mode", "brief")
            history = state.get("history", [])
            style_instruction = (
                "Modo de respuesta: breve. Responde en 2-4 oraciones claras y directas."
                if mode == "brief"
                else "Modo de respuesta: detallada. Responde con explicacion paso a paso, "
                "incluyendo contexto y ejemplo corto cuando sea util."
            )
            system_prompt = (
                "Eres el asistente del curso EVA.\n"
                "Tu estilo de comunicacion es cercano, amable y honesto, con calidez del vocabulario venezolano.\n"
                "Habla en espanol claro y natural, con tono de apoyo, paciencia y respeto.\n"
                "Puedes usar expresiones suaves y cotidianas venezolanas (por ejemplo: 'pana', 'tranqui', "
                "'vamos paso a paso') cuando encajen de forma natural.\n"
                "Evita exageraciones, caricaturas o modismos forzados.\n"
                "Responde solo usando la informacion del curso proporcionada.\n"
                f"{style_instruction}\n"
                "Si la pregunta no pertenece al curso o no se puede responder con ese contexto, "
                "responde exactamente: 'Solo puedo responder preguntas sobre este curso en particular.'\n"
                "No inventes contenido ni uses conocimiento externo."
            )
            history_text = "\n".join(
                f"{'Estudiante' if turn['role'] == 'user' else 'Asistente'}: {turn['content']}"
                for turn in history
            )
            user_prompt = (
                f"Contexto del curso:\n{state['course_context']}\n\n"
                f"Historial reciente (si existe):\n{history_text or 'Sin historial previo'}\n\n"
                f"Pregunta del estudiante:\n{state['question']}"
            )
            response = llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
            content = response.content
            if isinstance(content, str):
                answer = content
            else:
                answer = str(content)
            return {"answer": answer.strip()}

        graph = StateGraph(ChatbotState)
        graph.add_node("answer", answer_node)
        graph.add_edge(START, "answer")
        graph.add_edge("answer", END)
        cls._graph = graph.compile()
        return cls._graph

    @classmethod
    def ask(
        cls,
        user,
        course_id: int,
        question: str,
        mode: str = "brief",
        history: list[dict[str, str]] | None = None,
    ) -> str:
        question = question.strip()
        if not question:
            raise DomainError("Question is required")
        if len(question) > 2000:
            raise DomainError("Question is too long (max 2000 characters)")
        if mode not in {"brief", "detailed"}:
            raise DomainError("Invalid chatbot mode")
        history = history or []
        if len(history) > 8:
            history = history[-8:]

        course = ForumService.ensure_course_access(user, course_id)
        course_context = cls._build_course_context(course)
        graph = cls._get_graph()
        result = graph.invoke(
            {
                "question": question,
                "mode": mode,
                "history": history,
                "course_context": course_context,
            }
        )
        return result.get("answer", "").strip()
