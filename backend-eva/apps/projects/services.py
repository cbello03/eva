"""ProjectService — project management, submissions, and peer review business logic."""

from __future__ import annotations

import random

from django.db import transaction
from django.utils import timezone as tz

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment
from apps.projects.models import (
    PeerReviewAssignment,
    Project,
    ProjectReview,
    ProjectSubmission,
    SubmissionFile,
)
from apps.projects.schemas import MAX_FILE_SIZE, MAX_FILES_PER_SUBMISSION, ProjectCreateIn, ReviewIn
from common.exceptions import (
    CourseNotPublishedError,
    DomainError,
    FileTooLargeError,
    InsufficientRoleError,
    NotEnrolledError,
    TooManyFilesError,
)
from common.sanitization import sanitize_html


# ------------------------------------------------------------------
# Domain-specific errors
# ------------------------------------------------------------------


class ProjectNotFoundError(DomainError):
    status_code = 404
    code = "project_not_found"

    def __init__(self, detail: str = "Project not found"):
        super().__init__(detail)


class SubmissionNotFoundError(DomainError):
    status_code = 404
    code = "submission_not_found"

    def __init__(self, detail: str = "Submission not found"):
        super().__init__(detail)


class DuplicateSubmissionError(DomainError):
    status_code = 409
    code = "duplicate_submission"

    def __init__(self, detail: str = "You have already submitted this project"):
        super().__init__(detail)


class ReviewAssignmentNotFoundError(DomainError):
    status_code = 404
    code = "review_assignment_not_found"

    def __init__(self, detail: str = "Peer review assignment not found"):
        super().__init__(detail)


class DeadlineNotPassedError(DomainError):
    status_code = 400
    code = "deadline_not_passed"

    def __init__(self, detail: str = "Submission deadline has not passed yet"):
        super().__init__(detail)


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------


class ProjectService:
    """Handles project CRUD, submissions, reviews, and peer review assignment."""

    # ------------------------------------------------------------------
    # Project creation
    # ------------------------------------------------------------------

    @staticmethod
    def create_project(teacher: User, course_id: int, data: ProjectCreateIn) -> Project:
        """Create a new project for a course. Only the course owner may create."""
        course = ProjectService._get_course(course_id)
        if course.teacher_id != teacher.pk:
            raise InsufficientRoleError("You do not own this course")

        return Project.objects.create(
            course=course,
            teacher=teacher,
            title=sanitize_html(data.title),
            description=sanitize_html(data.description),
            rubric=data.rubric,
            submission_deadline=data.submission_deadline,
            peer_review_enabled=data.peer_review_enabled,
            peer_reviewers_count=data.peer_reviewers_count,
        )

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    @staticmethod
    def submit_project(
        student: User,
        project_id: int,
        description: str,
        files: list,
    ) -> ProjectSubmission:
        """Submit a project. Validates enrollment, duplicates, and file constraints."""
        project = ProjectService._get_project(project_id)

        # Course must be published
        if project.course.status != Course.Status.PUBLISHED:
            raise CourseNotPublishedError()

        # Student must be actively enrolled
        if not Enrollment.objects.filter(
            student=student, course=project.course, is_active=True
        ).exists():
            raise NotEnrolledError()

        # Check duplicate submission
        if ProjectSubmission.objects.filter(
            project=project, student=student
        ).exists():
            raise DuplicateSubmissionError()

        # Validate file constraints
        if len(files) > MAX_FILES_PER_SUBMISSION:
            raise TooManyFilesError(
                f"Maximum {MAX_FILES_PER_SUBMISSION} files allowed per submission"
            )
        for f in files:
            if f.size > MAX_FILE_SIZE:
                raise FileTooLargeError(
                    f"File '{f.name}' exceeds the maximum size of {MAX_FILE_SIZE // (1024 * 1024)}MB"
                )

        # Determine late status
        is_late = tz.now() > project.submission_deadline

        with transaction.atomic():
            submission = ProjectSubmission.objects.create(
                project=project,
                student=student,
                description=sanitize_html(description),
                is_late=is_late,
            )

            for f in files:
                SubmissionFile.objects.create(
                    submission=submission,
                    file=f,
                    filename=f.name,
                    file_size=f.size,
                )

        # Reload with files for the response
        submission = ProjectSubmission.objects.prefetch_related("files").get(
            pk=submission.pk
        )
        return submission

    # ------------------------------------------------------------------
    # Teacher review
    # ------------------------------------------------------------------

    @staticmethod
    def teacher_review(
        teacher: User, submission_id: int, data: ReviewIn
    ) -> ProjectReview:
        """Create a teacher review for a submission."""
        submission = ProjectService._get_submission(submission_id)

        if submission.project.course.teacher_id != teacher.pk:
            raise InsufficientRoleError("You do not own this course")

        return ProjectReview.objects.create(
            submission=submission,
            reviewer=teacher,
            review_type=ProjectReview.ReviewType.TEACHER,
            scores=data.scores,
            feedback=sanitize_html(data.feedback),
            is_complete=True,
        )

    # ------------------------------------------------------------------
    # Peer review assignment
    # ------------------------------------------------------------------

    @staticmethod
    def assign_peer_reviews(project_id: int) -> list[PeerReviewAssignment]:
        """Assign peer reviewers for all submissions of a project.

        Uses round-robin assignment ensuring no student reviews their own
        submission. Requires at least (peer_reviewers_count + 1) submissions.
        """
        project = ProjectService._get_project(project_id)

        if not project.peer_review_enabled:
            return []

        submissions = list(
            project.submissions.select_related("student").all()
        )
        num_submissions = len(submissions)
        reviewers_needed = project.peer_reviewers_count

        if num_submissions < reviewers_needed + 1:
            return []

        # Build a shuffled list of submissions for fair assignment
        shuffled = list(submissions)
        random.shuffle(shuffled)

        assignments: list[PeerReviewAssignment] = []

        with transaction.atomic():
            for i, submission in enumerate(shuffled):
                assigned_count = 0
                offset = 1
                while assigned_count < reviewers_needed and offset < num_submissions:
                    reviewer_submission = shuffled[(i + offset) % num_submissions]
                    reviewer = reviewer_submission.student

                    # No self-review
                    if reviewer.pk != submission.student_id:
                        assignment, created = PeerReviewAssignment.objects.get_or_create(
                            submission=submission,
                            reviewer=reviewer,
                            defaults={"is_completed": False},
                        )
                        if created:
                            assignments.append(assignment)
                        assigned_count += 1

                    offset += 1

        return assignments

    # ------------------------------------------------------------------
    # Peer review submission
    # ------------------------------------------------------------------

    @staticmethod
    def submit_peer_review(
        student: User, submission_id: int, data: ReviewIn
    ) -> ProjectReview:
        """Submit a peer review. Student must have a PeerReviewAssignment."""
        submission = ProjectService._get_submission(submission_id)

        try:
            assignment = PeerReviewAssignment.objects.get(
                submission=submission, reviewer=student
            )
        except PeerReviewAssignment.DoesNotExist:
            raise ReviewAssignmentNotFoundError()

        review = ProjectReview.objects.create(
            submission=submission,
            reviewer=student,
            review_type=ProjectReview.ReviewType.PEER,
            scores=data.scores,
            feedback=sanitize_html(data.feedback),
            is_complete=True,
        )

        assignment.is_completed = True
        assignment.save(update_fields=["is_completed", "updated_at"])

        return review

    # ------------------------------------------------------------------
    # Get reviews
    # ------------------------------------------------------------------

    @staticmethod
    def get_reviews(user: User, submission_id: int) -> list[ProjectReview]:
        """Return visible reviews for a submission.

        Teacher reviews are always visible.
        Peer reviews are visible only when ALL assigned peer reviews for
        that submission are complete.
        """
        submission = ProjectService._get_submission(submission_id)

        reviews: list[ProjectReview] = []

        # Teacher reviews are always visible
        teacher_reviews = list(
            submission.reviews.filter(
                review_type=ProjectReview.ReviewType.TEACHER
            )
        )
        reviews.extend(teacher_reviews)

        # Peer reviews visible only when all assignments are complete
        all_assignments = submission.peer_review_assignments.all()
        if all_assignments.exists():
            all_complete = not all_assignments.filter(is_completed=False).exists()
            if all_complete:
                peer_reviews = list(
                    submission.reviews.filter(
                        review_type=ProjectReview.ReviewType.PEER
                    )
                )
                reviews.extend(peer_reviews)

        return reviews

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_project(project_id: int) -> Project:
        try:
            return Project.objects.select_related("course").get(pk=project_id)
        except Project.DoesNotExist:
            raise ProjectNotFoundError()

    @staticmethod
    def _get_submission(submission_id: int) -> ProjectSubmission:
        try:
            return (
                ProjectSubmission.objects.select_related(
                    "project", "project__course"
                ).get(pk=submission_id)
            )
        except ProjectSubmission.DoesNotExist:
            raise SubmissionNotFoundError()

    @staticmethod
    def _get_course(course_id: int) -> Course:
        from apps.courses.services import CourseNotFoundError

        try:
            return Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            raise CourseNotFoundError()
