"""Projects app models — Project, ProjectSubmission, SubmissionFile, ProjectReview, PeerReviewAssignment."""

from django.db import models

from apps.accounts.models import User
from apps.courses.models import Course
from common.models import TimestampedModel


class Project(TimestampedModel):
    """A real-world project assignment."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="projects"
    )
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_projects"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    rubric = models.JSONField()  # [{"criterion": "...", "max_score": 10}, ...]
    submission_deadline = models.DateTimeField()
    peer_review_enabled = models.BooleanField(default=False)
    peer_reviewers_count = models.PositiveSmallIntegerField(default=2)

    class Meta:
        db_table = "projects_project"

    def __str__(self) -> str:
        return self.title


class ProjectSubmission(TimestampedModel):
    """A student's project submission."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="project_submissions"
    )
    description = models.TextField(blank=True)
    is_late = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "projects_submission"
        unique_together = [("project", "student")]

    def __str__(self) -> str:
        return f"{self.student.email} — {self.project.title}"


class SubmissionFile(TimestampedModel):
    """File attached to a project submission."""

    submission = models.ForeignKey(
        ProjectSubmission, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to="project_submissions/")
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # bytes

    class Meta:
        db_table = "projects_submission_file"

    def __str__(self) -> str:
        return self.filename


class ProjectReview(TimestampedModel):
    """Review of a project submission (teacher or peer)."""

    class ReviewType(models.TextChoices):
        TEACHER = "teacher"
        PEER = "peer"

    submission = models.ForeignKey(
        ProjectSubmission, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="project_reviews"
    )
    review_type = models.CharField(max_length=10, choices=ReviewType.choices)
    scores = models.JSONField()  # dict mapping criterion name to score
    feedback = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        db_table = "projects_review"

    def __str__(self) -> str:
        return f"Review by {self.reviewer.email} on {self.submission}"


class PeerReviewAssignment(TimestampedModel):
    """Tracks peer review assignments."""

    submission = models.ForeignKey(
        ProjectSubmission,
        on_delete=models.CASCADE,
        related_name="peer_review_assignments",
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="peer_review_assignments"
    )
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "projects_peer_review_assignment"
        unique_together = [("submission", "reviewer")]

    def __str__(self) -> str:
        return f"Peer review: {self.reviewer.email} → {self.submission}"
