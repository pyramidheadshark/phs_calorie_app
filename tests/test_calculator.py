from __future__ import annotations

from datetime import date, timedelta

import pytest

from calorie_app.core.calculator import calorie_progress, compute_streak, macro_percentages
from calorie_app.core.domain import DailyLog, MealEntry, NutritionFacts, UserSettings


class TestMacroPercentages:
    def test_normal_meal(self) -> None:
        n = NutritionFacts(calories=500, protein_g=25.0, fat_g=20.0, carbs_g=50.0)
        result = macro_percentages(n)
        assert result["protein"] + result["fat"] + result["carbs"] == pytest.approx(100.0, abs=1.0)
        assert result["fat"] > result["protein"]  # 9 kcal/g vs 4 kcal/g

    def test_zero_macros_returns_zeros(self) -> None:
        result = macro_percentages(NutritionFacts())
        assert result == {"protein": 0.0, "fat": 0.0, "carbs": 0.0}

    def test_only_protein(self) -> None:
        n = NutritionFacts(protein_g=100.0)
        result = macro_percentages(n)
        assert result["protein"] == 100.0
        assert result["fat"] == 0.0
        assert result["carbs"] == 0.0

    def test_rounds_to_one_decimal(self) -> None:
        n = NutritionFacts(protein_g=10.0, fat_g=10.0, carbs_g=10.0)
        result = macro_percentages(n)
        for v in result.values():
            assert isinstance(v, float)
            assert round(v, 1) == v


class TestCalorieProgress:
    def _make_log(self, calories: int) -> DailyLog:
        log = DailyLog(user_id=1, date="2026-03-05")
        log.meals.append(
            MealEntry(
                user_id=1,
                description="test",
                nutrition=NutritionFacts(calories=calories),
            )
        )
        return log

    def test_normal_progress(self) -> None:
        log = self._make_log(1500)
        result = calorie_progress(log, UserSettings(calorie_target=2000))
        assert result["consumed"] == 1500
        assert result["target"] == 2000
        assert result["remaining"] == 500
        assert result["percent"] == pytest.approx(75.0)

    def test_over_target_remaining_is_zero(self) -> None:
        log = self._make_log(2500)
        result = calorie_progress(log, UserSettings(calorie_target=2000))
        assert result["remaining"] == 0

    def test_zero_target_percent_is_zero(self) -> None:
        log = self._make_log(500)
        result = calorie_progress(log, UserSettings(calorie_target=0))
        assert result["percent"] == 0.0

    def test_empty_log(self) -> None:
        log = DailyLog(user_id=1, date="2026-03-05")
        result = calorie_progress(log, UserSettings(calorie_target=2000))
        assert result["consumed"] == 0
        assert result["remaining"] == 2000


class TestComputeStreak:
    def _today(self) -> str:
        return date.today().isoformat()

    def _days_ago(self, n: int) -> str:
        return (date.today() - timedelta(days=n)).isoformat()

    def test_empty_list(self) -> None:
        assert compute_streak([]) == 0

    def test_streak_starting_today(self) -> None:
        dates = [self._today(), self._days_ago(1), self._days_ago(2)]
        assert compute_streak(dates) == 3

    def test_streak_starting_yesterday(self) -> None:
        dates = [self._days_ago(1), self._days_ago(2), self._days_ago(3)]
        assert compute_streak(dates) == 3

    def test_broken_streak(self) -> None:
        dates = [self._today(), self._days_ago(2), self._days_ago(3)]
        assert compute_streak(dates) == 1

    def test_single_day_today(self) -> None:
        assert compute_streak([self._today()]) == 1

    def test_duplicate_dates_counted_once(self) -> None:
        today = self._today()
        yesterday = self._days_ago(1)
        assert compute_streak([today, today, yesterday, yesterday]) == 2

    def test_only_old_dates_no_streak(self) -> None:
        dates = [self._days_ago(5), self._days_ago(6)]
        assert compute_streak(dates) == 0
