"""Tests for exercises Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from apps.exercises.schemas import (
    AnswerIn,
    AnswerResult,
    ExerciseCreateIn,
    ExerciseOut,
    ExerciseUpdateIn,
    FillBlankConfig,
    FreeTextConfig,
    LessonSessionOut,
    MatchingConfig,
    MatchingPair,
    MultipleChoiceConfig,
)


# ------------------------------------------------------------------
# Config schema tests
# ------------------------------------------------------------------


class TestMultipleChoiceConfig:
    def test_valid(self):
        cfg = MultipleChoiceConfig(options=["A", "B", "C"], correct_index=1)
        assert cfg.correct_index == 1

    def test_too_few_options(self):
        with pytest.raises(ValidationError):
            MultipleChoiceConfig(options=["A"], correct_index=0)

    def test_negative_correct_index(self):
        with pytest.raises(ValidationError):
            MultipleChoiceConfig(options=["A", "B"], correct_index=-1)

    def test_correct_index_out_of_range(self):
        with pytest.raises(ValidationError):
            MultipleChoiceConfig(options=["A", "B"], correct_index=2)


class TestFillBlankConfig:
    def test_valid(self):
        cfg = FillBlankConfig(blank_position=0, accepted_answers=["hello"])
        assert cfg.blank_position == 0

    def test_negative_blank_position(self):
        with pytest.raises(ValidationError):
            FillBlankConfig(blank_position=-1, accepted_answers=["hello"])

    def test_empty_accepted_answers(self):
        with pytest.raises(ValidationError):
            FillBlankConfig(blank_position=0, accepted_answers=[])


class TestMatchingConfig:
    def test_valid(self):
        pairs = [MatchingPair(left="A", right="1"), MatchingPair(left="B", right="2")]
        cfg = MatchingConfig(pairs=pairs)
        assert len(cfg.pairs) == 2

    def test_too_few_pairs(self):
        with pytest.raises(ValidationError):
            MatchingConfig(pairs=[MatchingPair(left="A", right="1")])


class TestFreeTextConfig:
    def test_valid_with_model_answer(self):
        cfg = FreeTextConfig(rubric="Grade on clarity", model_answer="Example")
        assert cfg.model_answer == "Example"

    def test_valid_without_model_answer(self):
        cfg = FreeTextConfig(rubric="Grade on clarity")
        assert cfg.model_answer == ""

    def test_empty_rubric_rejected(self):
        with pytest.raises(ValidationError):
            FreeTextConfig(rubric="   ")


# ------------------------------------------------------------------
# ExerciseCreateIn tests
# ------------------------------------------------------------------


class TestExerciseCreateIn:
    def test_valid_multiple_choice(self):
        ex = ExerciseCreateIn(
            exercise_type="multiple_choice",
            question_text="Pick one",
            config={"options": ["A", "B"], "correct_index": 0},
        )
        assert ex.exercise_type == "multiple_choice"

    def test_valid_fill_blank(self):
        ex = ExerciseCreateIn(
            exercise_type="fill_blank",
            question_text="Fill ___",
            config={"blank_position": 1, "accepted_answers": ["word"]},
        )
        assert ex.difficulty == 1

    def test_valid_matching(self):
        ex = ExerciseCreateIn(
            exercise_type="matching",
            question_text="Match them",
            config={"pairs": [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]},
        )
        assert ex.topic == ""

    def test_valid_free_text(self):
        ex = ExerciseCreateIn(
            exercise_type="free_text",
            question_text="Explain",
            config={"rubric": "Clarity and depth"},
        )
        assert ex.is_collaborative is False

    def test_invalid_exercise_type(self):
        with pytest.raises(ValidationError):
            ExerciseCreateIn(
                exercise_type="essay",
                question_text="Q",
                config={},
            )

    def test_empty_question_text(self):
        with pytest.raises(ValidationError):
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="   ",
                config={"rubric": "ok"},
            )

    def test_difficulty_out_of_range(self):
        with pytest.raises(ValidationError):
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Q",
                config={"rubric": "ok"},
                difficulty=6,
            )

    def test_invalid_config_for_type(self):
        with pytest.raises(ValidationError):
            ExerciseCreateIn(
                exercise_type="multiple_choice",
                question_text="Q",
                config={"options": ["only_one"], "correct_index": 0},
            )

    def test_collaborative_requires_group_size(self):
        with pytest.raises(ValidationError):
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Q",
                config={"rubric": "ok"},
                is_collaborative=True,
            )

    def test_collaborative_group_size_range(self):
        with pytest.raises(ValidationError):
            ExerciseCreateIn(
                exercise_type="free_text",
                question_text="Q",
                config={"rubric": "ok"},
                is_collaborative=True,
                collab_group_size=6,
            )

    def test_valid_collaborative(self):
        ex = ExerciseCreateIn(
            exercise_type="free_text",
            question_text="Q",
            config={"rubric": "ok"},
            is_collaborative=True,
            collab_group_size=3,
        )
        assert ex.collab_group_size == 3


# ------------------------------------------------------------------
# ExerciseUpdateIn tests
# ------------------------------------------------------------------


class TestExerciseUpdateIn:
    def test_all_none(self):
        u = ExerciseUpdateIn()
        assert u.question_text is None
        assert u.config is None

    def test_partial_update(self):
        u = ExerciseUpdateIn(difficulty=3, topic="algebra")
        assert u.difficulty == 3

    def test_invalid_difficulty(self):
        with pytest.raises(ValidationError):
            ExerciseUpdateIn(difficulty=0)


# ------------------------------------------------------------------
# Response schema tests
# ------------------------------------------------------------------


class TestExerciseOut:
    def test_fields(self):
        out = ExerciseOut(
            id=1,
            exercise_type="matching",
            question_text="Q",
            order=1,
            config={"pairs": []},
            difficulty=2,
            topic="math",
            is_collaborative=False,
            collab_group_size=None,
        )
        assert out.id == 1


class TestAnswerSchemas:
    def test_answer_in(self):
        a = AnswerIn(answer={"selected_index": 0})
        assert a.answer["selected_index"] == 0

    def test_answer_result_correct(self):
        r = AnswerResult(is_correct=True)
        assert r.correct_answer is None
        assert r.feedback == ""

    def test_answer_result_incorrect(self):
        r = AnswerResult(
            is_correct=False,
            correct_answer={"selected_index": 1},
            feedback="Try again",
        )
        assert r.feedback == "Try again"


class TestLessonSessionOut:
    def test_fields(self):
        s = LessonSessionOut(
            id=1,
            lesson_id=10,
            current_exercise=None,
            progress_percentage=50.0,
            is_completed=False,
            correct_first_attempt=3,
            total_exercises=6,
            retry_queue_size=1,
        )
        assert s.progress_percentage == 50.0
