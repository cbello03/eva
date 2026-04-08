"""Tests for AdaptiveService — mastery, spaced repetition, difficulty adjustment."""

import datetime

import pytest

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.adaptive import (
    ALPHA,
    MASTERY_THRESHOLD,
    MAX_REVIEW_EXERCISES,
    SPACED_INTERVALS,
    AdaptiveService,
    ReviewRecommendation,
)
from apps.exercises.models import AnswerRecord, Exercise, LessonSession
from apps.progress.models import SpacedRepetitionItem, TopicMastery


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


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
def student(db):
    return User.objects.create_user(
        username="student",
        email="student@test.com",
        password="Pass1234",
        display_name="Student",
        role=Role.STUDENT,
    )


@pytest.fixture
def course(teacher):
    return Course.objects.create(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def unit(course):
    return Unit.objects.create(course=course, title="Unit 1", order=1)


@pytest.fixture
def lesson(unit):
    return Lesson.objects.create(unit=unit, title="Lesson 1", order=1)


@pytest.fixture
def enrollment(student, course):
    return Enrollment.objects.create(student=student, course=course)


def _make_exercise(lesson, topic="math", difficulty=1, order=1):
    return Exercise.objects.create(
        lesson=lesson,
        exercise_type="multiple_choice",
        question_text="Q",
        order=order,
        config={"options": ["A", "B"], "correct_index": 0},
        difficulty=difficulty,
        topic=topic,
    )


# ------------------------------------------------------------------
# record_answer
# ------------------------------------------------------------------


class TestRecordAnswer:
    def test_creates_mastery_on_first_correct(self, student, lesson):
        ex = _make_exercise(lesson, topic="algebra")
        AdaptiveService.record_answer(student, ex, is_correct=True)

        tm = TopicMastery.objects.get(student=student, topic="algebra")
        assert tm.correct_count == 1
        assert tm.total_count == 1
        assert tm.mastery_score == pytest.approx(ALPHA * 1.0)
        assert tm.last_reviewed is not None

    def test_creates_mastery_on_first_incorrect(self, student, lesson):
        ex = _make_exercise(lesson, topic="algebra")
        AdaptiveService.record_answer(student, ex, is_correct=False)

        tm = TopicMastery.objects.get(student=student, topic="algebra")
        assert tm.correct_count == 0
        assert tm.total_count == 1
        assert tm.mastery_score == pytest.approx(0.0)

    def test_recency_weighting(self, student, lesson):
        ex = _make_exercise(lesson, topic="algebra")

        # First correct: score = 0.3 * 1 + 0.7 * 0 = 0.3
        AdaptiveService.record_answer(student, ex, is_correct=True)
        tm = TopicMastery.objects.get(student=student, topic="algebra")
        assert tm.mastery_score == pytest.approx(0.3)

        # Second correct: score = 0.3 * 1 + 0.7 * 0.3 = 0.51
        AdaptiveService.record_answer(student, ex, is_correct=True)
        tm.refresh_from_db()
        assert tm.mastery_score == pytest.approx(0.3 + 0.7 * 0.3)

    def test_incorrect_lowers_score(self, student, lesson):
        ex = _make_exercise(lesson, topic="algebra")

        # Build up score
        AdaptiveService.record_answer(student, ex, is_correct=True)
        tm = TopicMastery.objects.get(student=student, topic="algebra")
        score_after_correct = tm.mastery_score

        # Incorrect answer should lower score
        AdaptiveService.record_answer(student, ex, is_correct=False)
        tm.refresh_from_db()
        assert tm.mastery_score < score_after_correct

    def test_skips_exercise_without_topic(self, student, lesson):
        ex = _make_exercise(lesson, topic="")
        AdaptiveService.record_answer(student, ex, is_correct=True)
        assert TopicMastery.objects.count() == 0

    def test_increments_counts(self, student, lesson):
        ex = _make_exercise(lesson, topic="algebra")
        AdaptiveService.record_answer(student, ex, is_correct=True)
        AdaptiveService.record_answer(student, ex, is_correct=False)
        AdaptiveService.record_answer(student, ex, is_correct=True)

        tm = TopicMastery.objects.get(student=student, topic="algebra")
        assert tm.correct_count == 2
        assert tm.total_count == 3


# ------------------------------------------------------------------
# get_mastery_scores
# ------------------------------------------------------------------


class TestGetMasteryScores:
    def test_returns_scores(self, student, course, lesson):
        ex1 = _make_exercise(lesson, topic="algebra", order=1)
        ex2 = _make_exercise(lesson, topic="geometry", order=2)

        AdaptiveService.record_answer(student, ex1, is_correct=True)
        AdaptiveService.record_answer(student, ex2, is_correct=False)

        scores = AdaptiveService.get_mastery_scores(student, course.pk)
        assert "algebra" in scores
        assert "geometry" in scores
        assert scores["algebra"] > scores["geometry"]

    def test_empty_when_no_records(self, student, course):
        scores = AdaptiveService.get_mastery_scores(student, course.pk)
        assert scores == {}


# ------------------------------------------------------------------
# should_recommend_review
# ------------------------------------------------------------------


class TestShouldRecommendReview:
    def test_recommends_when_weak_topic(self, student, unit, lesson):
        ex = _make_exercise(lesson, topic="algebra")
        # Record incorrect answer → mastery = 0.0
        AdaptiveService.record_answer(student, ex, is_correct=False)

        rec = AdaptiveService.should_recommend_review(student, unit.pk)
        assert rec.should_review is True
        assert len(rec.weak_topics) == 1
        assert rec.weak_topics[0]["topic"] == "algebra"

    def test_no_recommendation_when_strong(self, student, unit, lesson):
        ex = _make_exercise(lesson, topic="algebra")
        # Build up mastery above threshold
        TopicMastery.objects.create(
            student=student,
            topic="algebra",
            course=unit.course,
            correct_count=10,
            total_count=12,
            mastery_score=0.8,
        )

        rec = AdaptiveService.should_recommend_review(student, unit.pk)
        assert rec.should_review is False
        assert rec.weak_topics == []

    def test_topics_sorted_by_mastery(self, student, unit, lesson):
        _make_exercise(lesson, topic="algebra", order=1)
        _make_exercise(lesson, topic="geometry", order=2)

        TopicMastery.objects.create(
            student=student, topic="algebra", course=unit.course,
            correct_count=3, total_count=10, mastery_score=0.4,
        )
        TopicMastery.objects.create(
            student=student, topic="geometry", course=unit.course,
            correct_count=1, total_count=10, mastery_score=0.2,
        )

        rec = AdaptiveService.should_recommend_review(student, unit.pk)
        assert rec.should_review is True
        assert rec.weak_topics[0]["topic"] == "geometry"
        assert rec.weak_topics[1]["topic"] == "algebra"

    def test_unknown_topic_defaults_to_zero(self, student, unit, lesson):
        """Topic with no mastery record should be treated as 0.0 (weak)."""
        _make_exercise(lesson, topic="new_topic")

        rec = AdaptiveService.should_recommend_review(student, unit.pk)
        assert rec.should_review is True
        assert rec.weak_topics[0]["topic"] == "new_topic"
        assert rec.weak_topics[0]["mastery_score"] == 0.0

    def test_nonexistent_unit(self, student):
        rec = AdaptiveService.should_recommend_review(student, 9999)
        assert rec.should_review is False

    def test_no_topics_in_unit(self, student, unit):
        """Unit with no exercises → no recommendation."""
        rec = AdaptiveService.should_recommend_review(student, unit.pk)
        assert rec.should_review is False


# ------------------------------------------------------------------
# generate_review_session
# ------------------------------------------------------------------


class TestGenerateReviewSession:
    def test_selects_from_weak_topics(self, student, course, unit, lesson):
        ex = _make_exercise(lesson, topic="algebra")
        TopicMastery.objects.create(
            student=student, topic="algebra", course=course,
            correct_count=1, total_count=10, mastery_score=0.2,
        )

        exercises = AdaptiveService.generate_review_session(student, course.pk)
        assert len(exercises) >= 1
        assert all(e.topic == "algebra" for e in exercises)

    def test_prioritises_lowest_mastery(self, student, course, unit, lesson):
        _make_exercise(lesson, topic="algebra", order=1)
        _make_exercise(lesson, topic="geometry", order=2)

        TopicMastery.objects.create(
            student=student, topic="algebra", course=course,
            mastery_score=0.4,
        )
        TopicMastery.objects.create(
            student=student, topic="geometry", course=course,
            mastery_score=0.2,
        )

        exercises = AdaptiveService.generate_review_session(student, course.pk)
        # Geometry (0.2) should come before algebra (0.4)
        geo_indices = [i for i, e in enumerate(exercises) if e.topic == "geometry"]
        alg_indices = [i for i, e in enumerate(exercises) if e.topic == "algebra"]
        if geo_indices and alg_indices:
            assert min(geo_indices) < min(alg_indices)

    def test_respects_max_limit(self, student, course, unit, lesson):
        for i in range(15):
            _make_exercise(lesson, topic="algebra", order=i + 1)
        TopicMastery.objects.create(
            student=student, topic="algebra", course=course,
            mastery_score=0.1,
        )

        exercises = AdaptiveService.generate_review_session(student, course.pk)
        assert len(exercises) <= MAX_REVIEW_EXERCISES

    def test_empty_when_all_strong(self, student, course, unit, lesson):
        _make_exercise(lesson, topic="algebra")
        TopicMastery.objects.create(
            student=student, topic="algebra", course=course,
            mastery_score=0.9,
        )

        exercises = AdaptiveService.generate_review_session(student, course.pk)
        assert exercises == []

    def test_empty_when_no_mastery_records(self, student, course):
        exercises = AdaptiveService.generate_review_session(student, course.pk)
        assert exercises == []


# ------------------------------------------------------------------
# schedule_spaced_repetition
# ------------------------------------------------------------------


class TestScheduleSpacedRepetition:
    def test_incorrect_creates_item(self, student, lesson):
        ex = _make_exercise(lesson)
        AdaptiveService.schedule_spaced_repetition(student, ex, is_correct=False)

        item = SpacedRepetitionItem.objects.get(student=student, exercise=ex)
        assert item.interval_days == 1
        assert item.next_review_date == datetime.date.today() + datetime.timedelta(days=1)
        assert item.review_count == 0

    def test_incorrect_resets_existing(self, student, lesson):
        ex = _make_exercise(lesson)
        # Create an item at interval 7
        SpacedRepetitionItem.objects.create(
            student=student, exercise=ex,
            interval_days=7,
            next_review_date=datetime.date.today() + datetime.timedelta(days=7),
            review_count=3,
        )

        AdaptiveService.schedule_spaced_repetition(student, ex, is_correct=False)

        item = SpacedRepetitionItem.objects.get(student=student, exercise=ex)
        assert item.interval_days == 1
        assert item.next_review_date == datetime.date.today() + datetime.timedelta(days=1)

    def test_correct_advances_interval(self, student, lesson):
        ex = _make_exercise(lesson)
        today = datetime.date.today()

        # Create item at interval 1
        SpacedRepetitionItem.objects.create(
            student=student, exercise=ex,
            interval_days=1,
            next_review_date=today + datetime.timedelta(days=1),
            review_count=0,
        )

        AdaptiveService.schedule_spaced_repetition(student, ex, is_correct=True)
        item = SpacedRepetitionItem.objects.get(student=student, exercise=ex)
        assert item.interval_days == 3  # 1 → 3
        assert item.next_review_date == today + datetime.timedelta(days=3)
        assert item.review_count == 1

    def test_interval_progression(self, student, lesson):
        """Walk through the full interval sequence: 1 → 3 → 7 → 14 → 30."""
        ex = _make_exercise(lesson)
        today = datetime.date.today()

        SpacedRepetitionItem.objects.create(
            student=student, exercise=ex,
            interval_days=1,
            next_review_date=today + datetime.timedelta(days=1),
            review_count=0,
        )

        expected_intervals = [3, 7, 14, 30]
        for expected in expected_intervals:
            AdaptiveService.schedule_spaced_repetition(student, ex, is_correct=True)
            item = SpacedRepetitionItem.objects.get(student=student, exercise=ex)
            assert item.interval_days == expected

    def test_stays_at_max_interval(self, student, lesson):
        ex = _make_exercise(lesson)
        today = datetime.date.today()

        SpacedRepetitionItem.objects.create(
            student=student, exercise=ex,
            interval_days=30,
            next_review_date=today + datetime.timedelta(days=30),
            review_count=4,
        )

        AdaptiveService.schedule_spaced_repetition(student, ex, is_correct=True)
        item = SpacedRepetitionItem.objects.get(student=student, exercise=ex)
        assert item.interval_days == 30  # stays at max

    def test_correct_without_existing_item_is_noop(self, student, lesson):
        ex = _make_exercise(lesson)
        AdaptiveService.schedule_spaced_repetition(student, ex, is_correct=True)
        assert SpacedRepetitionItem.objects.count() == 0


# ------------------------------------------------------------------
# adjust_difficulty
# ------------------------------------------------------------------


class TestAdjustDifficulty:
    def _create_session(self, student, lesson):
        return LessonSession.objects.create(
            student=student, lesson=lesson, total_exercises=5,
        )

    def _record_answer(self, student, exercise, session, is_correct):
        return AnswerRecord.objects.create(
            student=student,
            exercise=exercise,
            session=session,
            submitted_answer={},
            is_correct=is_correct,
            is_first_attempt=True,
        )

    def test_increase_after_3_correct(self, student, lesson, enrollment):
        session = self._create_session(student, lesson)
        ex = _make_exercise(lesson, difficulty=2)

        for _ in range(3):
            self._record_answer(student, ex, session, is_correct=True)

        suggested = AdaptiveService.adjust_difficulty(student, ex)
        assert suggested == 3

    def test_decrease_after_2_incorrect(self, student, lesson, enrollment):
        session = self._create_session(student, lesson)
        ex = _make_exercise(lesson, difficulty=3)

        for _ in range(2):
            self._record_answer(student, ex, session, is_correct=False)

        suggested = AdaptiveService.adjust_difficulty(student, ex)
        assert suggested == 2

    def test_no_change_mixed_answers(self, student, lesson, enrollment):
        session = self._create_session(student, lesson)
        ex = _make_exercise(lesson, difficulty=3)

        self._record_answer(student, ex, session, is_correct=True)
        self._record_answer(student, ex, session, is_correct=False)
        self._record_answer(student, ex, session, is_correct=True)

        suggested = AdaptiveService.adjust_difficulty(student, ex)
        assert suggested == 3

    def test_capped_at_max_difficulty(self, student, lesson, enrollment):
        session = self._create_session(student, lesson)
        ex = _make_exercise(lesson, difficulty=5)

        for _ in range(3):
            self._record_answer(student, ex, session, is_correct=True)

        suggested = AdaptiveService.adjust_difficulty(student, ex)
        assert suggested == 5

    def test_capped_at_min_difficulty(self, student, lesson, enrollment):
        session = self._create_session(student, lesson)
        ex = _make_exercise(lesson, difficulty=1)

        for _ in range(2):
            self._record_answer(student, ex, session, is_correct=False)

        suggested = AdaptiveService.adjust_difficulty(student, ex)
        assert suggested == 1

    def test_no_answers_returns_current(self, student, lesson, enrollment):
        ex = _make_exercise(lesson, difficulty=3)
        suggested = AdaptiveService.adjust_difficulty(student, ex)
        assert suggested == 3
