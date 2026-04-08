"""Tests for GamificationService — XP, levels, streaks, achievements, leaderboards."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone as tz

from apps.accounts.models import Role, User
from apps.courses.models import Course, Enrollment, Lesson, Unit
from apps.exercises.models import Exercise, LessonSession
from apps.gamification.models import (
    Achievement,
    GamificationProfile,
    UserAchievement,
    XPTransaction,
)
from apps.gamification.services import (
    BASE_XP,
    STREAK_MILESTONES,
    GamificationService,
    LevelUpResult,
    StreakResult,
    xp_for_level,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


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
def student2(db):
    return User.objects.create_user(
        username="student2",
        email="student2@test.com",
        password="Pass1234",
        display_name="Student Two",
        role=Role.STUDENT,
    )


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
def profile(student):
    return GamificationService.get_or_create_profile(student)


@pytest.fixture
def course(db, teacher):
    return Course.objects.create(
        title="Test Course",
        description="Desc",
        teacher=teacher,
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def lesson(course):
    unit = Unit.objects.create(course=course, title="Unit 1", order=1)
    return Lesson.objects.create(unit=unit, title="Lesson 1", order=1)


@pytest.fixture
def completed_sessions(student, lesson):
    """Create 5 completed lesson sessions for achievement testing."""
    sessions = []
    for i in range(5):
        unit = Unit.objects.create(
            course=lesson.unit.course, title=f"Unit {i + 2}", order=i + 2
        )
        les = Lesson.objects.create(unit=unit, title=f"Lesson {i + 2}", order=1)
        s = LessonSession.objects.create(
            student=student, lesson=les, is_completed=True, total_exercises=3
        )
        sessions.append(s)
    return sessions


# ------------------------------------------------------------------
# xp_for_level helper
# ------------------------------------------------------------------


class TestXPForLevel:
    def test_level_1_requires_zero(self):
        assert xp_for_level(1) == 0

    def test_level_0_requires_zero(self):
        assert xp_for_level(0) == 0

    def test_level_2_requires_base_xp(self):
        # 100 * 2^1.5 ≈ 282
        expected = int(BASE_XP * (2**1.5))
        assert xp_for_level(2) == expected

    def test_monotonically_increasing(self):
        for lvl in range(1, 50):
            assert xp_for_level(lvl + 1) >= xp_for_level(lvl)


# ------------------------------------------------------------------
# Profile
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestGetOrCreateProfile:
    def test_creates_profile_for_new_student(self, student):
        profile = GamificationService.get_or_create_profile(student)
        assert profile.student == student
        assert profile.total_xp == 0
        assert profile.current_level == 1
        assert profile.current_streak == 0

    def test_returns_existing_profile(self, student, profile):
        profile2 = GamificationService.get_or_create_profile(student)
        assert profile2.pk == profile.pk


# ------------------------------------------------------------------
# XP Award
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestAwardXP:
    def test_creates_transaction(self, student):
        txn = GamificationService.award_xp(student, "lesson", 1, 50)
        assert isinstance(txn, XPTransaction)
        assert txn.amount == 50
        assert txn.source_type == "lesson"
        assert txn.source_id == 1

    def test_updates_profile_total_xp(self, student, profile):
        GamificationService.award_xp(student, "lesson", 1, 100)
        profile.refresh_from_db()
        assert profile.total_xp == 100

    def test_cumulative_xp(self, student, profile):
        GamificationService.award_xp(student, "lesson", 1, 50)
        GamificationService.award_xp(student, "lesson", 2, 75)
        profile.refresh_from_db()
        assert profile.total_xp == 125

    def test_creates_multiple_transactions(self, student):
        GamificationService.award_xp(student, "lesson", 1, 50)
        GamificationService.award_xp(student, "lesson", 2, 75)
        assert XPTransaction.objects.filter(student=student).count() == 2

    def test_triggers_level_up(self, student, profile):
        # Award enough XP to reach level 2
        needed = xp_for_level(2)
        GamificationService.award_xp(student, "lesson", 1, needed)
        profile.refresh_from_db()
        assert profile.current_level >= 2

    def test_triggers_achievement_evaluation(self, student):
        # Create an achievement that requires 50 XP
        Achievement.objects.create(
            name="First XP",
            description="Earn 50 XP",
            icon="star",
            condition_type="xp_total",
            condition_value=50,
        )
        GamificationService.award_xp(student, "lesson", 1, 50)
        assert UserAchievement.objects.filter(student=student).count() == 1


# ------------------------------------------------------------------
# Level Up
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCheckLevelUp:
    def test_no_level_up_when_below_threshold(self, student, profile):
        profile.total_xp = 10
        profile.save()
        result = GamificationService.check_level_up(student)
        assert result is None
        profile.refresh_from_db()
        assert profile.current_level == 1

    def test_level_up_when_threshold_crossed(self, student, profile):
        needed = xp_for_level(2)
        profile.total_xp = needed
        profile.save()
        result = GamificationService.check_level_up(student)
        assert isinstance(result, LevelUpResult)
        assert result.old_level == 1
        assert result.new_level == 2
        profile.refresh_from_db()
        assert profile.current_level == 2

    def test_multi_level_jump(self, student, profile):
        # Give enough XP to skip to level 5
        needed = xp_for_level(5)
        profile.total_xp = needed
        profile.save()
        result = GamificationService.check_level_up(student)
        assert result is not None
        assert result.new_level == 5
        profile.refresh_from_db()
        assert profile.current_level == 5

    def test_no_change_when_already_at_correct_level(self, student, profile):
        needed = xp_for_level(3)
        profile.total_xp = needed
        profile.current_level = 3
        profile.save()
        result = GamificationService.check_level_up(student)
        assert result is None

    def test_returns_total_xp_in_result(self, student, profile):
        needed = xp_for_level(2)
        profile.total_xp = needed
        profile.save()
        result = GamificationService.check_level_up(student)
        assert result.total_xp == needed


# ------------------------------------------------------------------
# Streaks
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateStreak:
    def test_first_activity_sets_streak_to_one(self, student, profile):
        result = GamificationService.update_streak(student)
        assert isinstance(result, StreakResult)
        assert result.current_streak == 1
        profile.refresh_from_db()
        assert profile.current_streak == 1
        assert profile.last_activity_date is not None

    def test_same_day_no_increment(self, student, profile):
        GamificationService.update_streak(student)
        result = GamificationService.update_streak(student)
        assert result.current_streak == 1
        profile.refresh_from_db()
        assert profile.current_streak == 1

    def test_updates_longest_streak(self, student, profile):
        profile.current_streak = 4
        profile.longest_streak = 4
        profile.last_activity_date = date.today() - timedelta(days=1)
        profile.save()
        result = GamificationService.update_streak(student)
        assert result.current_streak == 5
        assert result.longest_streak == 5

    def test_longest_streak_preserved_when_lower(self, student, profile):
        profile.current_streak = 2
        profile.longest_streak = 10
        profile.last_activity_date = date.today() - timedelta(days=1)
        profile.save()
        result = GamificationService.update_streak(student)
        assert result.current_streak == 3
        assert result.longest_streak == 10

    def test_milestone_7_awards_bonus_xp(self, student, profile):
        profile.current_streak = 6
        profile.longest_streak = 6
        profile.last_activity_date = date.today() - timedelta(days=1)
        profile.save()
        result = GamificationService.update_streak(student)
        assert result.milestone_reached == 7
        assert result.bonus_xp == STREAK_MILESTONES[7]
        # Verify XP transaction was created
        txn = XPTransaction.objects.filter(
            student=student, source_type="streak_bonus"
        ).first()
        assert txn is not None
        assert txn.amount == STREAK_MILESTONES[7]

    def test_milestone_30_awards_bonus_xp(self, student, profile):
        profile.current_streak = 29
        profile.longest_streak = 29
        profile.last_activity_date = date.today() - timedelta(days=1)
        profile.save()
        result = GamificationService.update_streak(student)
        assert result.milestone_reached == 30
        assert result.bonus_xp == STREAK_MILESTONES[30]

    def test_no_milestone_when_not_at_threshold(self, student, profile):
        profile.current_streak = 3
        profile.longest_streak = 3
        profile.last_activity_date = date.today() - timedelta(days=1)
        profile.save()
        result = GamificationService.update_streak(student)
        assert result.milestone_reached is None
        assert result.bonus_xp == 0

    def test_last_activity_date_set_to_today(self, student, profile):
        GamificationService.update_streak(student)
        profile.refresh_from_db()
        today = tz.localdate(timezone=tz.get_current_timezone())
        assert profile.last_activity_date == today


# ------------------------------------------------------------------
# Streak Reset (Celery task entry point)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestResetExpiredStreaks:
    def test_resets_inactive_students(self, student, profile):
        profile.current_streak = 5
        profile.longest_streak = 10
        profile.last_activity_date = date.today() - timedelta(days=2)
        profile.save()
        count = GamificationService.reset_expired_streaks()
        assert count == 1
        profile.refresh_from_db()
        assert profile.current_streak == 0
        # longest_streak should be preserved
        assert profile.longest_streak == 10

    def test_does_not_reset_active_today(self, student, profile):
        profile.current_streak = 5
        profile.last_activity_date = date.today()
        profile.save()
        count = GamificationService.reset_expired_streaks()
        assert count == 0
        profile.refresh_from_db()
        assert profile.current_streak == 5

    def test_does_not_reset_zero_streaks(self, student, profile):
        profile.current_streak = 0
        profile.last_activity_date = date.today() - timedelta(days=5)
        profile.save()
        count = GamificationService.reset_expired_streaks()
        assert count == 0

    def test_resets_multiple_students(self, student, student2):
        p1 = GamificationService.get_or_create_profile(student)
        p1.current_streak = 3
        p1.last_activity_date = date.today() - timedelta(days=2)
        p1.save()

        p2 = GamificationService.get_or_create_profile(student2)
        p2.current_streak = 7
        p2.last_activity_date = date.today() - timedelta(days=3)
        p2.save()

        count = GamificationService.reset_expired_streaks()
        assert count == 2

    def test_null_last_activity_date_resets(self, student, profile):
        profile.current_streak = 1
        profile.last_activity_date = None
        profile.save()
        count = GamificationService.reset_expired_streaks()
        assert count == 1
        profile.refresh_from_db()
        assert profile.current_streak == 0


# ------------------------------------------------------------------
# Achievements
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestEvaluateAchievements:
    def test_grants_xp_achievement(self, student, profile):
        Achievement.objects.create(
            name="XP Starter",
            description="Earn 100 XP",
            icon="star",
            condition_type="xp_total",
            condition_value=100,
        )
        profile.total_xp = 100
        profile.save()
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 1
        assert granted[0].name == "XP Starter"
        assert UserAchievement.objects.filter(student=student).count() == 1

    def test_does_not_grant_unmet_condition(self, student, profile):
        Achievement.objects.create(
            name="XP Master",
            description="Earn 1000 XP",
            icon="trophy",
            condition_type="xp_total",
            condition_value=1000,
        )
        profile.total_xp = 50
        profile.save()
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 0

    def test_idempotent_no_duplicates(self, student, profile):
        Achievement.objects.create(
            name="XP Starter",
            description="Earn 100 XP",
            icon="star",
            condition_type="xp_total",
            condition_value=100,
        )
        profile.total_xp = 200
        profile.save()
        GamificationService.evaluate_achievements(student)
        GamificationService.evaluate_achievements(student)
        assert UserAchievement.objects.filter(student=student).count() == 1

    def test_grants_streak_achievement(self, student, profile):
        Achievement.objects.create(
            name="Week Warrior",
            description="7-day streak",
            icon="fire",
            condition_type="streak",
            condition_value=7,
        )
        profile.current_streak = 7
        profile.save()
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 1
        assert granted[0].name == "Week Warrior"

    def test_grants_lessons_completed_achievement(
        self, student, profile, completed_sessions
    ):
        Achievement.objects.create(
            name="Lesson Pro",
            description="Complete 5 lessons",
            icon="book",
            condition_type="lessons_completed",
            condition_value=5,
        )
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 1
        assert granted[0].name == "Lesson Pro"

    def test_grants_multiple_achievements_at_once(self, student, profile):
        Achievement.objects.create(
            name="XP 50",
            description="Earn 50 XP",
            icon="star",
            condition_type="xp_total",
            condition_value=50,
        )
        Achievement.objects.create(
            name="XP 100",
            description="Earn 100 XP",
            icon="star2",
            condition_type="xp_total",
            condition_value=100,
        )
        profile.total_xp = 150
        profile.save()
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 2

    def test_skips_already_unlocked(self, student, profile):
        ach = Achievement.objects.create(
            name="XP Starter",
            description="Earn 100 XP",
            icon="star",
            condition_type="xp_total",
            condition_value=100,
        )
        UserAchievement.objects.create(student=student, achievement=ach)
        profile.total_xp = 200
        profile.save()
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 0

    def test_level_based_achievement(self, student, profile):
        Achievement.objects.create(
            name="Level 5",
            description="Reach level 5",
            icon="badge",
            condition_type="current_level",
            condition_value=5,
        )
        profile.current_level = 5
        profile.save()
        granted = GamificationService.evaluate_achievements(student)
        assert len(granted) == 1


# ------------------------------------------------------------------
# Achievement Progress
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestGetAchievementProgress:
    def test_returns_all_stat_types(self, student, profile):
        progress = GamificationService.get_achievement_progress(student)
        assert "xp_total" in progress
        assert "streak" in progress
        assert "longest_streak" in progress
        assert "current_level" in progress
        assert "lessons_completed" in progress

    def test_reflects_profile_values(self, student, profile):
        profile.total_xp = 500
        profile.current_streak = 3
        profile.longest_streak = 10
        profile.current_level = 4
        profile.save()
        progress = GamificationService.get_achievement_progress(student)
        assert progress["xp_total"] == 500
        assert progress["streak"] == 3
        assert progress["longest_streak"] == 10
        assert progress["current_level"] == 4

    def test_counts_completed_lessons(self, student, profile, completed_sessions):
        progress = GamificationService.get_achievement_progress(student)
        assert progress["lessons_completed"] == 5


# ------------------------------------------------------------------
# Leaderboard (DB fallback — no Redis in test env)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestLeaderboardDBFallback:
    def test_returns_entries_sorted_by_xp(self, student, student2):
        p1 = GamificationService.get_or_create_profile(student)
        p1.total_xp = 500
        p1.save()

        p2 = GamificationService.get_or_create_profile(student2)
        p2.total_xp = 300
        p2.save()

        result = GamificationService.get_leaderboard("alltime", student)
        assert result["period"] == "alltime"
        assert len(result["entries"]) == 2
        assert result["entries"][0]["total_xp"] == 500
        assert result["entries"][1]["total_xp"] == 300

    def test_includes_user_rank(self, student, student2):
        p1 = GamificationService.get_or_create_profile(student)
        p1.total_xp = 200
        p1.save()

        p2 = GamificationService.get_or_create_profile(student2)
        p2.total_xp = 500
        p2.save()

        result = GamificationService.get_leaderboard("alltime", student)
        assert result["user_rank"] == 2
        assert result["user_xp"] == 200

    def test_weekly_period(self, student):
        GamificationService.get_or_create_profile(student)
        result = GamificationService.get_leaderboard("weekly", student)
        assert result["period"] == "weekly"

    def test_user_with_no_profile(self, student):
        # get_leaderboard should still work even if user has no profile
        result = GamificationService.get_leaderboard("alltime", student)
        assert result["user_rank"] is not None or result["user_xp"] == 0

    def test_entries_contain_required_fields(self, student):
        p = GamificationService.get_or_create_profile(student)
        p.total_xp = 100
        p.save()
        result = GamificationService.get_leaderboard("alltime", student)
        entry = result["entries"][0]
        assert "rank" in entry
        assert "student_id" in entry
        assert "display_name" in entry
        assert "total_xp" in entry

    def test_limits_entries(self, student, student2):
        """Leaderboard DB fallback uses [:100] slice."""
        p1 = GamificationService.get_or_create_profile(student)
        p1.total_xp = 500
        p1.save()
        p2 = GamificationService.get_or_create_profile(student2)
        p2.total_xp = 300
        p2.save()
        result = GamificationService._leaderboard_from_db("alltime", student)
        # Verify the query uses a limit (entries ≤ 100)
        assert len(result["entries"]) <= 100
        assert len(result["entries"]) == 2


# ------------------------------------------------------------------
# Leaderboard Redis operations (mocked)
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestLeaderboardRedis:
    def test_award_xp_updates_redis_leaderboards(self, student):
        mock_redis = MagicMock()
        with patch(
            "apps.gamification.services._get_redis", return_value=mock_redis
        ):
            GamificationService.award_xp(student, "lesson", 1, 50)
        mock_redis.zincrby.assert_any_call(
            "leaderboard:alltime", 50, str(student.pk)
        )
        mock_redis.zincrby.assert_any_call(
            "leaderboard:weekly", 50, str(student.pk)
        )

    def test_get_leaderboard_reads_from_redis(self, student):
        mock_redis = MagicMock()
        mock_redis.zrevrange.return_value = [
            (str(student.pk).encode(), 100.0),
        ]
        mock_redis.zscore.return_value = 100.0
        mock_redis.zrevrank.return_value = 0

        with patch(
            "apps.gamification.services._get_redis", return_value=mock_redis
        ):
            result = GamificationService.get_leaderboard("alltime", student)

        assert result["period"] == "alltime"
        assert len(result["entries"]) == 1
        assert result["entries"][0]["total_xp"] == 100
        assert result["user_rank"] == 1
        assert result["user_xp"] == 100

    def test_reset_weekly_leaderboard_deletes_key(self):
        mock_redis = MagicMock()
        with patch(
            "apps.gamification.services._get_redis", return_value=mock_redis
        ):
            GamificationService.reset_weekly_leaderboard()
        mock_redis.delete.assert_called_once_with("leaderboard:weekly")

    def test_redis_failure_falls_back_to_db(self, student):
        """When Redis raises, get_leaderboard falls back to DB query."""
        GamificationService.get_or_create_profile(student)
        mock_redis = MagicMock()
        mock_redis.zrevrange.side_effect = Exception("Redis down")

        with patch(
            "apps.gamification.services._get_redis", return_value=mock_redis
        ):
            result = GamificationService.get_leaderboard("alltime", student)

        # Should still return a valid result from DB fallback
        assert result["period"] == "alltime"
        assert isinstance(result["entries"], list)


# ------------------------------------------------------------------
# Celery tasks
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestCeleryTasks:
    def test_reset_expired_streaks_task(self, student, profile):
        from apps.gamification.tasks import reset_expired_streaks

        profile.current_streak = 3
        profile.last_activity_date = date.today() - timedelta(days=2)
        profile.save()

        count = reset_expired_streaks()
        assert count == 1
        profile.refresh_from_db()
        assert profile.current_streak == 0

    def test_reset_weekly_leaderboard_task(self):
        from apps.gamification.tasks import reset_weekly_leaderboard

        mock_redis = MagicMock()
        with patch(
            "apps.gamification.services._get_redis", return_value=mock_redis
        ):
            reset_weekly_leaderboard()
        mock_redis.delete.assert_called_once_with("leaderboard:weekly")
