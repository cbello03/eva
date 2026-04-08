"""Projects API routes — project CRUD, submissions, and reviews."""

from django.http import HttpRequest
from ninja import File, Form, Router, UploadedFile

from apps.accounts.api import jwt_auth
from apps.accounts.models import Role
from apps.courses.models import Enrollment
from apps.projects.models import ProjectSubmission
from apps.projects.schemas import (
    ProjectCreateIn,
    ProjectOut,
    ReviewIn,
    ReviewOut,
    SubmissionFileOut,
    SubmissionOut,
)
from apps.projects.services import ProjectService
from common.exceptions import NotEnrolledError
from common.permissions import require_role

router = Router(tags=["projects"], auth=jwt_auth)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _project_out(project) -> ProjectOut:
    """Build a ProjectOut from a Project model instance."""
    return ProjectOut(
        id=project.pk,
        course_id=project.course_id,
        teacher_id=project.teacher_id,
        title=project.title,
        description=project.description,
        rubric=project.rubric,
        submission_deadline=project.submission_deadline,
        peer_review_enabled=project.peer_review_enabled,
        peer_reviewers_count=project.peer_reviewers_count,
        created_at=project.created_at,
    )


def _submission_out(submission) -> SubmissionOut:
    """Build a SubmissionOut from a ProjectSubmission instance with files."""
    files = [
        SubmissionFileOut(
            id=f.pk,
            filename=f.filename,
            file_size=f.file_size,
        )
        for f in submission.files.all()
    ]
    return SubmissionOut(
        id=submission.pk,
        project_id=submission.project_id,
        student_id=submission.student_id,
        description=submission.description,
        is_late=submission.is_late,
        submitted_at=submission.submitted_at,
        files=files,
    )


def _review_out(review) -> ReviewOut:
    """Build a ReviewOut from a ProjectReview model instance."""
    return ReviewOut(
        id=review.pk,
        submission_id=review.submission_id,
        reviewer_id=review.reviewer_id,
        review_type=review.review_type,
        scores=review.scores,
        feedback=review.feedback,
        is_complete=review.is_complete,
        created_at=review.created_at,
    )


# ------------------------------------------------------------------
# Project endpoints
# ------------------------------------------------------------------


@router.post("/projects", response={201: ProjectOut})
@require_role(Role.TEACHER)
def create_project(request: HttpRequest, payload: ProjectCreateIn):
    """Create a new project for a course (Teacher only)."""
    project = ProjectService.create_project(request.auth, payload.course_id, payload)
    return 201, _project_out(project)


@router.get("/projects/{project_id}", response=ProjectOut)
def get_project(request: HttpRequest, project_id: int):
    """Get project detail (Bearer + enrolled or teacher/admin)."""
    project = ProjectService._get_project(project_id)
    user = request.auth

    # Allow teacher who owns the course or admin
    if user.role == Role.ADMIN or project.course.teacher_id == user.pk:
        return _project_out(project)

    # Otherwise require active enrollment
    if not Enrollment.objects.filter(
        student=user, course=project.course, is_active=True
    ).exists():
        raise NotEnrolledError()

    return _project_out(project)


# ------------------------------------------------------------------
# Submission endpoints
# ------------------------------------------------------------------


@router.post("/projects/{project_id}/submit", response={201: SubmissionOut})
@require_role(Role.STUDENT)
def submit_project(
    request: HttpRequest,
    project_id: int,
    description: str = Form(""),
    files: list[UploadedFile] = File(None),  # type: ignore[assignment]
):
    """Submit a project with optional file uploads (Student + Enrolled)."""
    upload_files = files if files is not None else []
    submission = ProjectService.submit_project(
        request.auth, project_id, description, upload_files
    )
    return 201, _submission_out(submission)


# ------------------------------------------------------------------
# Review endpoints
# ------------------------------------------------------------------


@router.post("/submissions/{submission_id}/review", response={201: ReviewOut})
@require_role(Role.TEACHER)
def teacher_review(request: HttpRequest, submission_id: int, payload: ReviewIn):
    """Submit a teacher review for a project submission."""
    review = ProjectService.teacher_review(request.auth, submission_id, payload)
    return 201, _review_out(review)


@router.post("/submissions/{submission_id}/peer-review", response={201: ReviewOut})
@require_role(Role.STUDENT)
def peer_review(request: HttpRequest, submission_id: int, payload: ReviewIn):
    """Submit a peer review for a project submission."""
    review = ProjectService.submit_peer_review(request.auth, submission_id, payload)
    return 201, _review_out(review)


@router.get("/submissions/{submission_id}/reviews", response=list[ReviewOut])
def get_reviews(request: HttpRequest, submission_id: int):
    """Get all visible reviews for a submission."""
    reviews = ProjectService.get_reviews(request.auth, submission_id)
    return [_review_out(r) for r in reviews]
