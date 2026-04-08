"""Tests for projects Pydantic schema validation."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from apps.projects.schemas import (
    ProjectCreateIn,
    SubmissionCreateIn,
    ReviewIn,
    MAX_FILE_SIZE,
    MAX_FILES_PER_SUBMISSION,
)

VALID_RUBRIC = [{"criterion": "Quality", "max_score": 10}]
VALID_DEADLINE = datetime(2030, 1, 1, tzinfo=timezone.utc)


class TestProjectCreateIn:
    def test_valid_input(self):
        p = ProjectCreateIn(
            course_id=1,
            title="My Project",
            description="A description",
            rubric=VALID_RUBRIC,
            submission_deadline=VALID_DEADLINE,
        )
        assert p.title == "My Project"
        assert p.course_id == 1
        assert p.peer_review_enabled is False
        assert p.peer_reviewers_count == 2

    def test_title_stripped(self):
        p = ProjectCreateIn(
            course_id=1,
            title="  Spaced  ",
            description="Desc",
            rubric=VALID_RUBRIC,
            submission_deadline=VALID_DEADLINE,
        )
        assert p.title == "Spaced"

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="   ",
                description="Desc",
                rubric=VALID_RUBRIC,
                submission_deadline=VALID_DEADLINE,
            )

    def test_title_over_200_chars_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="A" * 201,
                description="Desc",
                rubric=VALID_RUBRIC,
                submission_deadline=VALID_DEADLINE,
            )

    def test_empty_description_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="Title",
                description="   ",
                rubric=VALID_RUBRIC,
                submission_deadline=VALID_DEADLINE,
            )

    def test_empty_rubric_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="Title",
                description="Desc",
                rubric=[],
                submission_deadline=VALID_DEADLINE,
            )

    def test_rubric_missing_criterion_key_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="Title",
                description="Desc",
                rubric=[{"max_score": 10}],
                submission_deadline=VALID_DEADLINE,
            )

    def test_rubric_missing_max_score_key_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="Title",
                description="Desc",
                rubric=[{"criterion": "Quality"}],
                submission_deadline=VALID_DEADLINE,
            )

    def test_rubric_zero_max_score_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="Title",
                description="Desc",
                rubric=[{"criterion": "Quality", "max_score": 0}],
                submission_deadline=VALID_DEADLINE,
            )

    def test_peer_reviewers_count_below_2_when_enabled_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreateIn(
                course_id=1,
                title="Title",
                description="Desc",
                rubric=VALID_RUBRIC,
                submission_deadline=VALID_DEADLINE,
                peer_review_enabled=True,
                peer_reviewers_count=1,
            )

    def test_peer_reviewers_count_below_2_when_disabled_allowed(self):
        p = ProjectCreateIn(
            course_id=1,
            title="Title",
            description="Desc",
            rubric=VALID_RUBRIC,
            submission_deadline=VALID_DEADLINE,
            peer_review_enabled=False,
            peer_reviewers_count=1,
        )
        assert p.peer_reviewers_count == 1


class TestSubmissionCreateIn:
    def test_default_empty_description(self):
        s = SubmissionCreateIn()
        assert s.description == ""

    def test_with_description(self):
        s = SubmissionCreateIn(description="My submission notes")
        assert s.description == "My submission notes"


class TestReviewIn:
    def test_valid_scores(self):
        r = ReviewIn(scores={"Quality": 8, "Completeness": 9.5})
        assert r.scores["Quality"] == 8

    def test_negative_score_rejected(self):
        with pytest.raises(ValidationError):
            ReviewIn(scores={"Quality": -1})

    def test_zero_score_allowed(self):
        r = ReviewIn(scores={"Quality": 0})
        assert r.scores["Quality"] == 0

    def test_default_empty_feedback(self):
        r = ReviewIn(scores={"Quality": 5})
        assert r.feedback == ""


class TestConstants:
    def test_max_file_size(self):
        assert MAX_FILE_SIZE == 10 * 1024 * 1024

    def test_max_files_per_submission(self):
        assert MAX_FILES_PER_SUBMISSION == 5
