from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.adapters.db.session import get_session
from calorie_app.api.deps import get_current_user
from calorie_app.core.domain import User, UserSettings
from calorie_app.main import app


def _make_fake_user() -> User:
    return User(
        telegram_id=111222333,
        username="testuser",
        first_name="Test",
        settings=UserSettings(calorie_target=2000),
    )


_FAKE_ANALYTICS = {
    "calorie_trend": [{"date": "2026-03-04", "calories": 1800}],
    "macro_split": {"protein_pct": 30, "fat_pct": 30, "carbs_pct": 40},
    "weekday_avg": {"Пн": 1900, "Вт": 2100},
    "top_meals": [{"description": "Овсянка", "avg_calories": 350, "count": 5}],
    "avg_daily_calories": 1950,
    "goal_adherence_pct": 80,
    "total_days": 14,
}


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
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()


class TestGetAnalytics:
    async def test_returns_analytics_data(self, client_with_overrides: AsyncClient) -> None:
        class MockRepo:
            async def get_analytics(self, user_id: int, calorie_target: int) -> dict:
                return _FAKE_ANALYTICS

        with patch("calorie_app.api.analytics.MealRepo", return_value=MockRepo()):
            async with client_with_overrides as client:
                resp = await client.get(
                    "/api/stats/analytics", headers={"x-telegram-init-data": "test"}
                )

        assert resp.status_code == 200
        data = resp.json()
        assert "calorie_trend" in data
        assert "macro_split" in data
        assert "top_meals" in data
        assert data["total_days"] == 14
        assert data["goal_adherence_pct"] == 80
