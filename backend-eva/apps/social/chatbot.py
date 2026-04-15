"""Course-scoped chatbot service using LangChain + LangGraph + Gemini."""

from __future__ import annotations

from typing import TypedDict

from django.conf import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from apps.courses.models import Unit
from apps.projects.models import Project
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
    course_sources: list[dict[str, str]]
    answer: str


class CourseChatbotService:
    """Answers questions strictly limited to the current course context."""

    _graph = None

    @staticmethod
    def _build_course_context(course) -> tuple[str, list[dict[str, str]]]:
        units = (
            Unit.objects.filter(course=course)
            .prefetch_related("lessons__exercises")
            .order_by("order")
        )
        projects = list(Project.objects.filter(course=course).order_by("created_at"))
        key_topics: set[str] = set()
        key_terms: set[str] = set()
        sources: list[dict[str, str]] = [
            {"label": f"Curso: {course.title}", "href": f"/courses/{course.pk}"}
        ]

        context_lines = [
            f"Curso: {course.title}",
            f"Descripcion: {course.description}",
            "",
            "Estructura del curso:",
        ]
        for unit in units:
            context_lines.append(f"- Unidad {unit.order}: {unit.title}")
            sources.append(
                {
                    "label": f"Unidad {unit.order}: {unit.title}",
                    "href": f"/courses/{course.pk}",
                }
            )
            key_terms.update(unit.title.lower().split())
            lessons = list(unit.lessons.all().order_by("order"))
            for lesson in lessons:
                context_lines.append(f"  - Leccion {lesson.order}: {lesson.title}")
                sources.append(
                    {
                        "label": f"Unidad {unit.order}, Leccion {lesson.order}: {lesson.title}",
                        "href": f"/courses/{course.pk}/lessons/{lesson.pk}",
                    }
                )
                key_terms.update(lesson.title.lower().split())
                exercises = list(lesson.exercises.all().order_by("order"))
                for exercise in exercises:
                    topic = exercise.topic or "sin tema"
                    if topic and topic != "sin tema":
                        key_topics.add(topic)
                    key_terms.update(exercise.question_text.lower().split())
                    context_lines.append(
                        f"    - Ejercicio {exercise.order} [{exercise.exercise_type}] ({topic}): {exercise.question_text}"
                    )
                    sources.append(
                        {
                            "label": f"Leccion {lesson.order}, Ejercicio {exercise.order}: {exercise.question_text[:80]}",
                            "href": f"/courses/{course.pk}/lessons/{lesson.pk}",
                        }
                    )
            if not lessons:
                context_lines.append("  - Sin lecciones")

        if not units:
            context_lines.append("- Curso sin unidades definidas")

        context_lines.append("")
        context_lines.append("Temas clave del curso:")
        if key_topics:
            context_lines.append("- " + ", ".join(sorted(key_topics)))
        else:
            context_lines.append("- Sin temas explicitos")

        context_lines.append("")
        context_lines.append("Proyectos del curso:")
        if not projects:
            context_lines.append("- Sin proyectos definidos")
        else:
            for idx, project in enumerate(projects, start=1):
                context_lines.append(f"- Proyecto {idx}: {project.title}")
                sources.append(
                    {
                        "label": f"Proyecto {idx}: {project.title}",
                        "href": f"/projects/{project.pk}",
                    }
                )
                context_lines.append(f"  - Descripcion: {project.description}")
                if isinstance(project.rubric, list) and project.rubric:
                    criteria = [
                        str(item.get("criterion", "")).strip()
                        for item in project.rubric
                        if isinstance(item, dict) and item.get("criterion")
                    ]
                    if criteria:
                        context_lines.append(
                            f"  - Criterios de evaluacion: {', '.join(criteria)}"
                        )

        deduped_sources = []
        seen = set()
        for source in sources:
            source_label = source.get("label", "")
            if source_label in seen:
                continue
            seen.add(source_label)
            deduped_sources.append(source)
        return "\n".join(context_lines), deduped_sources[:12]

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
                "Puedes explicar conceptos base del curso (definiciones y ejemplos sencillos) "
                "cuando sean coherentes con el titulo, descripcion, temas o ejercicios del curso.\n"
                "Al final de cada respuesta agrega una linea con este formato exacto:\n"
                "Fuentes: <lista separada por '; ' con 1 a 3 referencias concretas del curso>.\n"
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
                "Referencias disponibles:\n"
                f"{'; '.join(source.get('label', '') for source in state.get('course_sources', []))}\n\n"
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
    ) -> tuple[str, list[dict[str, str]]]:
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
        course_context, course_sources = cls._build_course_context(course)
        graph = cls._get_graph()
        result = graph.invoke(
            {
                "question": question,
                "mode": mode,
                "history": history,
                "course_context": course_context,
                "course_sources": course_sources,
            }
        )
        raw_answer = result.get("answer", "").strip()
        default_sources = course_sources[:3]
        if "Fuentes:" not in raw_answer:
            return raw_answer, default_sources

        answer_text, _, sources_text = raw_answer.partition("Fuentes:")
        parsed_sources = [
            source.strip()
            for source in sources_text.split(";")
            if source.strip()
        ]
        if not parsed_sources:
            return answer_text.strip(), default_sources

        source_map = {
            source.get("label", "").strip().lower(): source for source in course_sources
        }
        matched_sources: list[dict[str, str]] = []
        for parsed in parsed_sources:
            normalized = parsed.lower()
            matched = source_map.get(normalized)
            if matched is None:
                for source in course_sources:
                    label = source.get("label", "").lower()
                    if normalized in label or label in normalized:
                        matched = source
                        break
            if matched and matched not in matched_sources:
                matched_sources.append(matched)
            if len(matched_sources) >= 3:
                break

        return answer_text.strip(), (matched_sources if matched_sources else default_sources)
