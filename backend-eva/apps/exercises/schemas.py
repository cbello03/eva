"""Exercises app Pydantic schemas for request/response validation."""

from typing import Self

from ninja import Schema
from pydantic import field_validator, model_validator

from apps.exercises.models import ExerciseType


# ------------------------------------------------------------------
# Config schemas (type-specific exercise configuration)
# ------------------------------------------------------------------


class MatchingPair(Schema):
    """A single left-right pair for matching exercises."""

    left: str
    right: str


class MultipleChoiceConfig(Schema):
    """Config for multiple-choice exercises."""

    options: list[str]
    correct_index: int

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("Multiple choice requires at least 2 options")
        return v

    @model_validator(mode="after")
    def validate_correct_index(self) -> Self:
        if self.correct_index < 0 or self.correct_index >= len(self.options):
            raise ValueError(
                "correct_index must be a valid index into options"
            )
        return self


class FillBlankConfig(Schema):
    """Config for fill-in-the-blank exercises."""

    blank_position: int
    accepted_answers: list[str]

    @field_validator("blank_position")
    @classmethod
    def validate_blank_position(cls, v: int) -> int:
        if v < 0:
            raise ValueError("blank_position must be >= 0")
        return v

    @field_validator("accepted_answers")
    @classmethod
    def validate_accepted_answers(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("At least one accepted answer is required")
        return v


class MatchingConfig(Schema):
    """Config for matching exercises."""

    pairs: list[MatchingPair]

    @field_validator("pairs")
    @classmethod
    def validate_pairs(cls, v: list[MatchingPair]) -> list[MatchingPair]:
        if len(v) < 2:
            raise ValueError("Matching exercises require at least 2 pairs")
        return v


class FreeTextConfig(Schema):
    """Config for free-text exercises."""

    model_answer: str = ""
    rubric: str

    @field_validator("rubric")
    @classmethod
    def validate_rubric(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Rubric is required and must be non-empty")
        return v


# ------------------------------------------------------------------
# Config validator mapping
# ------------------------------------------------------------------

_CONFIG_VALIDATORS: dict[str, type[Schema]] = {
    ExerciseType.MULTIPLE_CHOICE: MultipleChoiceConfig,
    ExerciseType.FILL_BLANK: FillBlankConfig,
    ExerciseType.MATCHING: MatchingConfig,
    ExerciseType.FREE_TEXT: FreeTextConfig,
}


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class ExerciseCreateIn(Schema):
    """Payload for creating an exercise."""

    exercise_type: str
    question_text: str
    config: dict
    difficulty: int = 1
    topic: str = ""
    is_collaborative: bool = False
    collab_group_size: int | None = None

    @field_validator("exercise_type")
    @classmethod
    def validate_exercise_type(cls, v: str) -> str:
        valid = {choice.value for choice in ExerciseType}
        if v not in valid:
            raise ValueError(
                f"exercise_type must be one of {sorted(valid)}"
            )
        return v

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question_text is required")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("difficulty must be between 1 and 5")
        return v

    @model_validator(mode="after")
    def validate_config_and_collab(self) -> Self:
        # Validate config against exercise type
        validator_cls = _CONFIG_VALIDATORS.get(self.exercise_type)
        if validator_cls is not None:
            validator_cls(**self.config)

        # Validate collaborative fields
        if self.is_collaborative:
            if self.collab_group_size is None:
                raise ValueError(
                    "collab_group_size is required when is_collaborative is True"
                )
            if self.collab_group_size < 2 or self.collab_group_size > 5:
                raise ValueError("collab_group_size must be between 2 and 5")

        return self


class ExerciseUpdateIn(Schema):
    """Payload for partially updating an exercise."""

    question_text: str | None = None
    config: dict | None = None
    difficulty: int | None = None
    topic: str | None = None
    is_collaborative: bool | None = None
    collab_group_size: int | None = None

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("difficulty must be between 1 and 5")
        return v


class AnswerIn(Schema):
    """Payload for submitting an answer to an exercise."""

    answer: dict


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class ExerciseOut(Schema):
    """Exercise representation in API responses."""

    id: int
    exercise_type: str
    question_text: str
    order: int
    config: dict
    difficulty: int
    topic: str
    is_collaborative: bool
    collab_group_size: int | None


class AnswerResult(Schema):
    """Response schema for answer feedback."""

    is_correct: bool
    correct_answer: dict | None = None
    feedback: str = ""


class LessonSessionOut(Schema):
    """Response schema for lesson session state."""

    id: int
    lesson_id: int
    current_exercise: ExerciseOut | None
    progress_percentage: float
    is_completed: bool
    correct_first_attempt: int
    total_exercises: int
    retry_queue_size: int
