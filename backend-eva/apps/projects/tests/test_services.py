"""Tests for ProjectService — project creation, submissions, reviews, and peer review."""

from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone as tz

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import Exercise
from apps.projects.models import (
    PeerReviewAssignment,
    Project,
    ProjectReview,
    ProjectSubmission,
    SubmissionFile,
)
from apps.projects.schemas import MAX_FILE_SIZE, MAX_FILES_PER_SUBMISSION, ProjectCreateIn, ReviewIn
from apps.projects.services import (
    DeadlineNotPassedError,
    DuplicateSubmissionError,
    ProjectNotFoundError,
    ProjectService,
    SubmissionNotFoundError,
    ReviewAssignmentNotFoundError,
)
from common.exceptions import (
    CourseNotPublishedError,
    FileTooLargeError,
    InsufficientRoleError,
    NotEnrolledError,
    TooManyFilesError,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

VALID_RUBRIC = [{"criterion": "Quality", "max_score": 10}]


@pytest.fixture
def teacher(db):
    return User.objects.create_user(
        username="teacher",
        email="teacher@test.com",
        password="Pass1234",
        display_name="Teacher",
        role=Role.TEACHER,
    )


@pytest.fixture
def other_teacher(db):
    return User.objects.create_user(
        username="other_teacher",
        email="other_teacher@test.com",
        password="Pass1234",
        display_name="Other Teacher",
        role=Role.TEACHER,
    )


@pytest.fixture
def student(db):
    return User.objects.create_user(
        username="student",
        email="student@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def course(db, teacher):
    return Course.objects.create(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def draft_course(db, teacher):
    return Course.objects.create(
        title="Draft Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.DRAFT,
    )


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


@pytest.fixture
def future_deadline():
    return tz.now() + timedelta(days=7)


@pytest.fixture
def past_deadline():
    return tz.now() - timedelta(days=1)


@pytest.fixture
def project(course, teacher, future_deadline):
    return Project.objects.create(
        course=course,
        teacher=teacher,
        title="Test Project",
        description="Project description",
        rubric=VALID_RUBRIC,
        submission_deadline=future_deadline,
        peer_review_enabled=False,
    )


@pytest.fixture
def peer_review_project(course, teacher, future_deadline):
    return Project.objects.create(
        course=course,
        teacher=teacher,
        title="Peer Review Project",
        description="Project with peer review",
        rubric=VALID_RUBRIC,
        submission_deadline=future_deadline,
        peer_review_enabled=True,
        peer_reviewers_count=2,
    )


def _make_file(name="test.txt", size=100, content=None):
    """Helper to create a SimpleUploadedFile for testing."""
    if content is None:
        content = b"x" * size
    return SimpleUploadedFile(name, content, content_type="text/plain")


def _make_students(db, count, course):
    """Create multiple enrolled students."""
    students = []
    for i in range(count):
        s = User.objects.create_user(
            username=f"student_{i}",
            email=f"student_{i}@test.com",
            password="Pass1234",
            display_name=f"Student {i}",
            role=Role.STUDENT,
        )
        Enrollment.objects.create(student=s, course=course)
        students.append(s)
    return students


# ------------------------------------------------------------------
# Project creation
# ------------------------------------------------------------------


class TestCreateProject:
    def test_creates_project(self, teacher, course, future_deadline):
        data = ProjectCreateIn(
            course_id=course.pk,
            title="New Project",
            description="Description",
            rubric=VALID_RUBRIC,
            submission_deadline=future_deadline,
        )
        project = ProjectService.create_project(teacher, course.pk, data)

        assert project.pk is not None
        assert project.title == "New Project"
        assert project.course_id == course.pk
        assert project.teacher_id == teacher.pk
        assert project.peer_review_enabled is False

    def test_sanitizes_title_and_description(self, teacher, course, future_deadline):
        data = ProjectCreateIn(
            course_id=course.pk,
            title="Title <script>alert('xss')</script>",
            description="Desc <script>bad</script>",
            rubric=VALID_RUBRIC,
            submission_deadline=future_deadline,
        )
        project = ProjectService.create_project(teacher, course.pk, data)

        assert "<script>" not in project.title
        assert "<script>" not in project.description

    def test_non_owner_rejected(self, other_teacher, course, future_deadline):
        data = ProjectCreateIn(
            course_id=course.pk,
            title="Project",
            description="Desc",
            rubric=VALID_RUBRIC,
            submission_deadline=future_deadline,
        )
        with pytest.raises(InsufficientRoleError):
            ProjectService.create_project(other_teacher, course.pk, data)

    def test_creates_with_peer_review(self, teacher, course, future_deadline):
        data = ProjectCreateIn(
            course_id=course.pk,
            title="Peer Project",
            description="Desc",
            rubric=VALID_RUBRIC,
            submission_deadline=future_deadline,
            peer_review_enabled=True,
            peer_reviewers_count=3,
        )
        project = ProjectService.create_project(teacher, course.pk, data)

        assert project.peer_review_enabled is True
        assert project.peer_reviewers_count == 3


# ------------------------------------------------------------------
# Submission
# ------------------------------------------------------------------


class TestSubmitProject:
    def test_submits_successfully(self, student, project, enrollment):
        files = [_make_file("doc.txt", 500)]
        submission = ProjectService.submit_project(
            student, project.pk, "My submission", files
        )

        assert submission.pk is not None
        assert submission.student_id == student.pk
        assert submission.project_id == project.pk
        assert submission.is_late is False
        assert submission.files.count() == 1

    def test_submits_without_files(self, student, project, enrollment):
        submission = ProjectService.submit_project(
            student, project.pk, "No files", []
        )

        assert submission.pk is not None
        assert submission.files.count() == 0

    def test_sanitizes_description(self, student, project, enrollment):
        submission = ProjectService.submit_project(
            student, project.pk, "Desc <script>alert('xss')</script>", []
        )

        assert "<script>" not in submission.description

    def test_late_submission_flagged(self, student, course, teacher, enrollment):
        past = tz.now() - timedelta(days=1)
        late_project = Project.objects.create(
            course=course,
            teacher=teacher,
            title="Late Project",
            description="Desc",
            rubric=VALID_RUBRIC,
            submission_deadline=past,
        )
        submission = ProjectService.submit_project(
            student, late_project.pk, "Late work", []
        )

        assert submission.is_late is True

    def test_on_time_submission_not_flagged(self, student, project, enrollment):
        submission = ProjectService.submit_project(
            student, project.pk, "On time", []
        )

        assert submission.is_late is False

    def test_duplicate_submission_rejected(self, student, project, enrollment):
        ProjectService.submit_project(student, project.pk, "First", [])

        with pytest.raises(DuplicateSubmissionError):
            ProjectService.submit_project(student, project.pk, "Second", [])

    def test_not_enrolled_rejected(self, student, project):
        # No enrollment fixture
        with pytest.raises(NotEnrolledError):
            ProjectService.submit_project(student, project.pk, "Desc", [])

    def test_unpublished_course_rejected(self, student, draft_course, teacher):
        Enrollment.objects.create(student=student, course=draft_course)
        draft_project = Project.objects.create(
            course=draft_course,
            teacher=teacher,
            title="Draft Project",
            description="Desc",
            rubric=VALID_RUBRIC,
            submission_deadline=tz.now() + timedelta(days=7),
        )

        with pytest.raises(CourseNotPublishedError):
            ProjectService.submit_project(student, draft_project.pk, "Desc", [])

    def test_too_many_files_rejected(self, student, project, enrollment):
        files = [_make_file(f"file_{i}.txt", 100) for i in range(MAX_FILES_PER_SUBMISSION + 1)]

        with pytest.raises(TooManyFilesError):
            ProjectService.submit_project(student, project.pk, "Desc", files)

    def test_file_too_large_rejected(self, student, project, enrollment):
        big_file = _make_file("big.txt", MAX_FILE_SIZE + 1)

        with pytest.raises(FileTooLargeError):
            ProjectService.submit_project(student, project.pk, "Desc", [big_file])

    def test_max_files_allowed(self, student, project, enrollment):
        files = [_make_file(f"file_{i}.txt", 100) for i in range(MAX_FILES_PER_SUBMISSION)]
        submission = ProjectService.submit_project(student, project.pk, "Desc", files)

        assert submission.files.count() == MAX_FILES_PER_SUBMISSION

    def test_project_not_found(self, student):
        with pytest.raises(ProjectNotFoundError):
            ProjectService.submit_project(student, 99999, "Desc", [])

    def test_multiple_files_stored(self, student, project, enrollment):
        files = [_make_file(f"doc_{i}.txt", 200) for i in range(3)]
        submission = ProjectService.submit_project(
            student, project.pk, "Multi-file", files
        )

        assert submission.files.count() == 3
        filenames = set(submission.files.values_list("filename", flat=True))
        assert filenames == {"doc_0.txt", "doc_1.txt", "doc_2.txt"}


# ------------------------------------------------------------------
# Teacher review
# ------------------------------------------------------------------


class TestTeacherReview:
    def test_creates_teacher_review(self, teacher, student, project, enrollment):
        submission = ProjectService.submit_project(student, project.pk, "Work", [])
        data = ReviewIn(scores={"Quality": 8}, feedback="Good work")

        review = ProjectService.teacher_review(teacher, submission.pk, data)

        assert review.pk is not None
        assert review.review_type == ProjectReview.ReviewType.TEACHER
        assert review.scores == {"Quality": 8}
        assert review.is_complete is True
        assert review.reviewer_id == teacher.pk

    def test_sanitizes_feedback(self, teacher, student, project, enrollment):
        submission = ProjectService.submit_project(student, project.pk, "Work", [])
        data = ReviewIn(
            scores={"Quality": 5},
            feedback="Nice <script>alert('xss')</script>",
        )

        review = ProjectService.teacher_review(teacher, submission.pk, data)

        assert "<script>" not in review.feedback

    def test_non_owner_rejected(self, other_teacher, teacher, student, project, enrollment):
        submission = ProjectService.submit_project(student, project.pk, "Work", [])
        data = ReviewIn(scores={"Quality": 5})

        with pytest.raises(InsufficientRoleError):
            ProjectService.teacher_review(other_teacher, submission.pk, data)

    def test_submission_not_found(self, teacher):
        data = ReviewIn(scores={"Quality": 5})

        with pytest.raises(SubmissionNotFoundError):
            ProjectService.teacher_review(teacher, 99999, data)


# ------------------------------------------------------------------
# Peer review assignment
# ------------------------------------------------------------------


class TestAssignPeerReviews:
    def test_assigns_reviewers(self, db, peer_review_project, course):
        students = _make_students(db, 4, course)
        for s in students:
            ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )

        assignments = ProjectService.assign_peer_reviews(peer_review_project.pk)

        assert len(assignments) > 0
        # No self-reviews
        for a in assignments:
            assert a.reviewer_id != a.submission.student_id

    def test_no_self_reviews(self, db, peer_review_project, course):
        students = _make_students(db, 5, course)
        for s in students:
            ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )

        assignments = ProjectService.assign_peer_reviews(peer_review_project.pk)

        for a in assignments:
            assert a.reviewer_id != a.submission.student_id

    def test_not_enough_submissions_returns_empty(self, db, peer_review_project, course):
        # peer_reviewers_count=2, need at least 3 submissions
        students = _make_students(db, 2, course)
        for s in students:
            ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )

        assignments = ProjectService.assign_peer_reviews(peer_review_project.pk)

        assert assignments == []

    def test_disabled_peer_review_returns_empty(self, db, project, course):
        # project has peer_review_enabled=False
        students = _make_students(db, 4, course)
        for s in students:
            ProjectSubmission.objects.create(
                project=project, student=s, description="Work"
            )

        assignments = ProjectService.assign_peer_reviews(project.pk)

        assert assignments == []

    def test_each_submission_gets_reviewers(self, db, peer_review_project, course):
        students = _make_students(db, 4, course)
        submissions = []
        for s in students:
            sub = ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )
            submissions.append(sub)

        ProjectService.assign_peer_reviews(peer_review_project.pk)

        for sub in submissions:
            reviewer_count = PeerReviewAssignment.objects.filter(
                submission=sub
            ).count()
            assert reviewer_count == peer_review_project.peer_reviewers_count

    def test_no_duplicate_assignments(self, db, peer_review_project, course):
        students = _make_students(db, 4, course)
        for s in students:
            ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )

        ProjectService.assign_peer_reviews(peer_review_project.pk)

        # Verify no duplicate (submission, reviewer) pairs exist
        from django.db.models import Count

        duplicates = (
            PeerReviewAssignment.objects.filter(
                submission__project=peer_review_project
            )
            .values("submission_id", "reviewer_id")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
        )
        assert duplicates.count() == 0


# ------------------------------------------------------------------
# Peer review submission
# ------------------------------------------------------------------


class TestSubmitPeerReview:
    def _setup(self, db, peer_review_project, course):
        """Create students, submissions, and assignments for peer review tests."""
        students = _make_students(db, 4, course)
        submissions = []
        for s in students:
            sub = ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )
            submissions.append(sub)

        ProjectService.assign_peer_reviews(peer_review_project.pk)
        return students, submissions

    def test_submits_peer_review(self, db, peer_review_project, course):
        students, submissions = self._setup(db, peer_review_project, course)

        # Find an assignment for the first student as reviewer
        assignment = PeerReviewAssignment.objects.filter(
            reviewer=students[0]
        ).first()
        assert assignment is not None

        data = ReviewIn(scores={"Quality": 7}, feedback="Decent work")
        review = ProjectService.submit_peer_review(
            students[0], assignment.submission_id, data
        )

        assert review.review_type == ProjectReview.ReviewType.PEER
        assert review.is_complete is True

        # Assignment should be marked completed
        assignment.refresh_from_db()
        assert assignment.is_completed is True

    def test_no_assignment_rejected(self, db, peer_review_project, course):
        students = _make_students(db, 4, course)
        sub = ProjectSubmission.objects.create(
            project=peer_review_project, student=students[0], description="Work"
        )
        # No assignment exists for students[1] on this submission
        data = ReviewIn(scores={"Quality": 5})

        with pytest.raises(ReviewAssignmentNotFoundError):
            ProjectService.submit_peer_review(students[1], sub.pk, data)

    def test_sanitizes_peer_feedback(self, db, peer_review_project, course):
        students, submissions = self._setup(db, peer_review_project, course)

        assignment = PeerReviewAssignment.objects.filter(
            reviewer=students[0]
        ).first()
        data = ReviewIn(
            scores={"Quality": 5},
            feedback="Good <script>alert('xss')</script>",
        )
        review = ProjectService.submit_peer_review(
            students[0], assignment.submission_id, data
        )

        assert "<script>" not in review.feedback


# ------------------------------------------------------------------
# Review visibility
# ------------------------------------------------------------------


class TestGetReviews:
    def test_teacher_reviews_always_visible(self, teacher, student, project, enrollment):
        submission = ProjectService.submit_project(student, project.pk, "Work", [])
        data = ReviewIn(scores={"Quality": 8}, feedback="Good")
        ProjectService.teacher_review(teacher, submission.pk, data)

        reviews = ProjectService.get_reviews(student, submission.pk)

        assert len(reviews) == 1
        assert reviews[0].review_type == ProjectReview.ReviewType.TEACHER

    def test_peer_reviews_hidden_until_all_complete(self, db, peer_review_project, course, teacher):
        students = _make_students(db, 4, course)
        submissions = []
        for s in students:
            sub = ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )
            submissions.append(sub)

        ProjectService.assign_peer_reviews(peer_review_project.pk)

        target_sub = submissions[0]
        assignments = list(
            PeerReviewAssignment.objects.filter(submission=target_sub)
        )
        assert len(assignments) == 2

        # Complete only the first assignment
        first_reviewer = assignments[0].reviewer
        data = ReviewIn(scores={"Quality": 7}, feedback="OK")
        ProjectService.submit_peer_review(first_reviewer, target_sub.pk, data)

        # Peer reviews should NOT be visible yet
        reviews = ProjectService.get_reviews(students[0], target_sub.pk)
        peer_reviews = [r for r in reviews if r.review_type == ProjectReview.ReviewType.PEER]
        assert len(peer_reviews) == 0

        # Complete the second assignment
        second_reviewer = assignments[1].reviewer
        ProjectService.submit_peer_review(second_reviewer, target_sub.pk, data)

        # Now peer reviews should be visible
        reviews = ProjectService.get_reviews(students[0], target_sub.pk)
        peer_reviews = [r for r in reviews if r.review_type == ProjectReview.ReviewType.PEER]
        assert len(peer_reviews) == 2

    def test_no_reviews_returns_empty(self, student, project, enrollment):
        submission = ProjectService.submit_project(student, project.pk, "Work", [])

        reviews = ProjectService.get_reviews(student, submission.pk)

        assert reviews == []

    def test_submission_not_found(self, student):
        with pytest.raises(SubmissionNotFoundError):
            ProjectService.get_reviews(student, 99999)

    def test_teacher_and_peer_reviews_combined(self, db, peer_review_project, course, teacher):
        students = _make_students(db, 4, course)
        submissions = []
        for s in students:
            sub = ProjectSubmission.objects.create(
                project=peer_review_project, student=s, description="Work"
            )
            submissions.append(sub)

        ProjectService.assign_peer_reviews(peer_review_project.pk)

        target_sub = submissions[0]

        # Add teacher review
        teacher_data = ReviewIn(scores={"Quality": 9}, feedback="Excellent")
        ProjectService.teacher_review(teacher, target_sub.pk, teacher_data)

        # Complete all peer review assignments
        assignments = PeerReviewAssignment.objects.filter(submission=target_sub)
        peer_data = ReviewIn(scores={"Quality": 7}, feedback="Good")
        for a in assignments:
            ProjectService.submit_peer_review(a.reviewer, target_sub.pk, peer_data)

        reviews = ProjectService.get_reviews(students[0], target_sub.pk)

        teacher_reviews = [r for r in reviews if r.review_type == ProjectReview.ReviewType.TEACHER]
        peer_reviews = [r for r in reviews if r.review_type == ProjectReview.ReviewType.PEER]
        assert len(teacher_reviews) == 1
        assert len(peer_reviews) == 2
