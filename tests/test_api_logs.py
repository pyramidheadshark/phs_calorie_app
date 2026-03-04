from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.api.deps import get_current_user
from calorie_app.adapters.db.session import get_session
from calorie_app.core.domain import MealEntry, NutritionFacts, User, UserSettings, WaterEntry
from calorie_app.main import app


def _make_fake_user() -> User:
    return User(
        telegram_id=999888777,
        username="loguser",
        first_name="Log",
        settings=UserSettings(calorie_target=2000, water_target_ml=2000),
    )


@pytest.fixture()
def mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture()
def client_with_overrides(mock_db_session: AsyncMock) -> AsyncClient:
    async def override_user() -> User:
        return _make_fake_user()

    async def override_session():  # type: ignore[return]
        yield mock_db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestGetHistory:
    async def test_returns_history_days(
        self, client_with_overrides: AsyncClient
    ) -> None:
        summary = [
            {"date": "2026-03-04", "meal_count": 4, "calories": 2100},
            {"date": "2026-03-03", "meal_count": 3, "calories": 1750},
            {"date": "2026-03-02", "meal_count": 2, "calories": 900},
        ]

        with patch("calorie_app.api.logs.MealRepo") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_history_summary = AsyncMock(return_value=summary)
            MockRepo.return_value = mock_repo_instance

            async with client_with_overrides as client:
                response = await client.get("/api/history")

        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert len(data["days"]) == 3
        assert data["days"][0]["date"] == "2026-03-04"
        assert data["days"][0]["meal_count"] == 4
        assert data["days"][1]["calories"] == 1750

    async def test_returns_empty_when_no_history(
        self, client_with_overrides: AsyncClient
    ) -> None:
        with patch("calorie_app.api.logs.MealRepo") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_history_summary = AsyncMock(return_value=[])
            MockRepo.return_value = mock_repo_instance

            async with client_with_overrides as client:
                response = await client.get("/api/history")

        assert response.status_code == 200
        assert response.json()["days"] == []


class TestGetDailyLog:
    async def test_returns_daily_log(
        self, client_with_overrides: AsyncClient
    ) -> None:
        meal = MealEntry(
            user_id=999888777,
            description="Борщ",
            nutrition=NutritionFacts(calories=300, protein_g=12.0, fat_g=8.0, carbs_g=40.0, portion_g=400),
            confidence="high",
            confirmed=True,
            logged_at=datetime(2026, 3, 4, 12, 0, 0, tzinfo=timezone.utc),
        )
        water = WaterEntry(user_id=999888777, amount_ml=250)

        with patch("calorie_app.api.logs.MealRepo") as MockMealRepo, \
             patch("calorie_app.api.logs.WaterRepo") as MockWaterRepo:
            mock_meal_repo = AsyncMock()
            mock_meal_repo.get_by_date = AsyncMock(return_value=[meal])
            MockMealRepo.return_value = mock_meal_repo

            mock_water_repo = AsyncMock()
            mock_water_repo.get_by_date = AsyncMock(return_value=[water])
            MockWaterRepo.return_value = mock_water_repo

            async with client_with_overrides as client:
                response = await client.get("/api/daily/2026-03-04")

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2026-03-04"
        assert len(data["meals"]) == 1
        assert data["meals"][0]["description"] == "Борщ"
        assert data["total_nutrition"]["calories"] == 300
        assert data["total_water_ml"] == 250

    async def test_empty_day_returns_zero_totals(
        self, client_with_overrides: AsyncClient
    ) -> None:
        with patch("calorie_app.api.logs.MealRepo") as MockMealRepo, \
             patch("calorie_app.api.logs.WaterRepo") as MockWaterRepo:
            mock_meal_repo = AsyncMock()
            mock_meal_repo.get_by_date = AsyncMock(return_value=[])
            MockMealRepo.return_value = mock_meal_repo

            mock_water_repo = AsyncMock()
            mock_water_repo.get_by_date = AsyncMock(return_value=[])
            MockWaterRepo.return_value = mock_water_repo

            async with client_with_overrides as client:
                response = await client.get("/api/daily/2026-03-01")

        assert response.status_code == 200
        data = response.json()
        assert data["total_nutrition"]["calories"] == 0
        assert data["total_water_ml"] == 0


class TestAuthRequired:
    async def test_missing_header_returns_error(self) -> None:
        original_overrides = app.dependency_overrides.copy()
        app.dependency_overrides.clear()
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/history")
            # 422 = missing required header, 401 = invalid header
            assert response.status_code in (401, 422)
        finally:
            app.dependency_overrides.update(original_overrides)
