from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from calorie_app.adapters.db.repos import MealRepo
from calorie_app.core.domain import NutritionFacts


def _make_meal_model(
    meal_id: uuid.UUID,
    user_id: int = 123,
    description: str = "Тест",
    calories: int = 300,
) -> MagicMock:
    model = MagicMock()
    model.id = meal_id
    model.user_id = user_id
    model.description = description
    model.photo_path = None
    model.calories = calories
    model.protein_g = 15.0
    model.fat_g = 8.0
    model.carbs_g = 40.0
    model.portion_g = 300
    model.confidence = "medium"
    model.gemini_raw = {}
    model.confirmed = True
    model.logged_at = datetime.now(UTC)
    model.created_at = datetime.now(UTC)
    return model


class TestMealRepoUpdate:
    async def test_update_description(self, mock_session: AsyncMock) -> None:
        meal_id = uuid.uuid4()
        model = _make_meal_model(meal_id)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.refresh = AsyncMock(side_effect=lambda m: None)

        repo = MealRepo(mock_session)
        result = await repo.update(meal_id, user_id=123, description="Новое описание")

        assert result is not None
        assert model.description == "Новое описание"
        mock_session.commit.assert_called_once()

    async def test_update_not_found_returns_none(self, mock_session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=result_mock)

        repo = MealRepo(mock_session)
        result = await repo.update(uuid.uuid4(), user_id=999)

        assert result is None
        mock_session.commit.assert_not_called()

    async def test_update_nutrition(self, mock_session: AsyncMock) -> None:
        meal_id = uuid.uuid4()
        model = _make_meal_model(meal_id)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = model
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.refresh = AsyncMock(side_effect=lambda m: None)

        repo = MealRepo(mock_session)
        new_nutrition = NutritionFacts(
            calories=500, protein_g=25.0, fat_g=15.0, carbs_g=55.0, portion_g=400
        )
        result = await repo.update(meal_id, user_id=123, nutrition=new_nutrition)

        assert result is not None
        assert model.calories == 500
        assert model.protein_g == 25.0


class TestMealRepoGetHistorySummary:
    async def test_returns_formatted_rows(self, mock_session: AsyncMock) -> None:
        row1 = MagicMock()
        row1.log_date = "2026-03-01"
        row1.meal_count = 3
        row1.calories = 1800

        row2 = MagicMock()
        row2.log_date = "2026-03-02"
        row2.meal_count = 4
        row2.calories = 2100

        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 2

        rows_mock = MagicMock()
        rows_mock.all.return_value = [row1, row2]

        mock_session.execute = AsyncMock(side_effect=[count_mock, rows_mock])

        repo = MealRepo(mock_session)
        rows, total = await repo.get_history_summary(user_id=123)

        assert total == 2
        assert len(rows) == 2
        assert rows[0]["date"] == "2026-03-01"
        assert rows[0]["meal_count"] == 3
        assert rows[0]["calories"] == 1800
        assert rows[1]["calories"] == 2100

    async def test_handles_null_calories(self, mock_session: AsyncMock) -> None:
        row = MagicMock()
        row.log_date = "2026-03-01"
        row.meal_count = 1
        row.calories = None

        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 1

        rows_mock = MagicMock()
        rows_mock.all.return_value = [row]

        mock_session.execute = AsyncMock(side_effect=[count_mock, rows_mock])

        repo = MealRepo(mock_session)
        rows, total = await repo.get_history_summary(user_id=123)

        assert total == 1
        assert rows[0]["calories"] == 0
