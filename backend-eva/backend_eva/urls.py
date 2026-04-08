"""Root URL configuration for the EVA backend.

Creates the Django Ninja API instance with a global exception handler
that converts ``DomainError`` subclasses into structured JSON responses.
"""

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import path
from ninja import NinjaAPI

from apps.accounts.api import router as accounts_router
from apps.courses.api import router as courses_router
from apps.exercises.api import router as exercises_router
from apps.gamification.api import router as gamification_router
from apps.social.api import router as social_router
from apps.projects.api import router as projects_router
from apps.collaboration.api import router as collaboration_router
from apps.notifications.api import router as notifications_router
from apps.progress.api import router as progress_router
from common.exceptions import DomainError, RateLimitExceededError
from common.schemas import ErrorResponse

api = NinjaAPI(
    title="EVA Learning Platform API",
    version="1.0.0",
    urls_namespace="api",
)


@api.exception_handler(DomainError)
def domain_error_handler(
    request: HttpRequest,
    exc: DomainError,
) -> HttpResponse:
    """Return a structured JSON error for any ``DomainError``."""
    body = ErrorResponse(
        detail=exc.detail,
        code=exc.code,
        errors=[],
    )
    response = api.create_response(
        request,
        body.dict(),
        status=exc.status_code,
    )
    # Add Retry-After header for rate-limit errors.
    if isinstance(exc, RateLimitExceededError):
        response["Retry-After"] = str(exc.retry_after)
    return response


# ---------------------------------------------------------------------------
# Mount app routers
# ---------------------------------------------------------------------------
api.add_router("", accounts_router)
api.add_router("", courses_router)
api.add_router("", exercises_router)
api.add_router("", gamification_router)
api.add_router("", social_router)
api.add_router("", projects_router)
api.add_router("", collaboration_router)
api.add_router("", notifications_router)
api.add_router("", progress_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]
