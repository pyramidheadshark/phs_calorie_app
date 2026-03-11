from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.api.deps import get_current_user
from calorie_app.api.ratelimit import check_ai_rate_limit
from calorie_app.core.domain import MacroTargets, MealEntry, NutritionFacts, User, UserSettings
from calorie_app.main import app


def _make_user() -> User:
    return User(
        telegram_id=999111222,
        username="chatuser",
        first_name="Chat",
        settings=UserSettings(
            calorie_target=2000,
            macro_targets=MacroTargets(protein_g=120, fat_g=70, carbs_g=250),
            goal_description="Похудение",
        ),
    )


def _make_meal(calories: float = 400.0) -> MealEntry:
    return MealEntry(
        id=uuid.uuid4(),
        user_id=999111222,
        description="Овсянка",
        nutrition=NutritionFacts(
            calories=calories, protein_g=12.0, fat_g=8.0, carbs_g=55.0, portion_g=300
        ),
        confidence="high",
        confirmed=True,
        logged_at=datetime.now(UTC),
    )


class TestChatEndpoint:
    @pytest.fixture(autouse=True)
    def override_auth(self) -> None:
        fake_user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[check_ai_rate_limit] = lambda: fake_user
        yield
        app.dependency_overrides.clear()

    async def test_returns_reply(self) -> None:
        with (
            patch("calorie_app.api.chat.MealRepo") as MockRepo,
            patch("calorie_app.api.chat.gemini_adapter") as mock_gemini,
        ):
            mock_repo = AsyncMock()
            mock_repo.get_by_date = AsyncMock(return_value=[_make_meal()])
            mock_repo.get_weekly_summary = AsyncMock(
                return_value=[{"calories": 1800}, {"calories": 2000}]
            )
            MockRepo.return_value = mock_repo
            mock_gemini.chat = AsyncMock(return_value="Хороший вопрос! Рекомендую добавить белка.")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/chat", json={"message": "Что мне поесть?"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"] == "Хороший вопрос! Рекомендую добавить белка."

    async def test_empty_meals_uses_no_data_string(self) -> None:
        """When user has no meals today, meals_list should be 'нет записей'."""
        with (
            patch("calorie_app.api.chat.MealRepo") as MockRepo,
            patch("calorie_app.api.chat.gemini_adapter") as mock_gemini,
        ):
            mock_repo = AsyncMock()
            mock_repo.get_by_date = AsyncMock(return_value=[])
            mock_repo.get_weekly_summary = AsyncMock(return_value=[])
            MockRepo.return_value = mock_repo
            mock_gemini.chat = AsyncMock(return_value="Сегодня вы ещё ничего не ели.")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/chat", json={"message": "Что у меня сегодня?"})

        assert resp.status_code == 200
        # Verify gemini.chat was called with empty meals context
        call_kwargs = mock_gemini.chat.call_args.kwargs
        assert call_kwargs["meals_list"] == "нет записей"
        assert call_kwargs["today_calories"] == 0

    async def test_weekly_avg_calculated_from_summary(self) -> None:
        """avg_calories string should reflect weekly data."""
        with (
            patch("calorie_app.api.chat.MealRepo") as MockRepo,
            patch("calorie_app.api.chat.gemini_adapter") as mock_gemini,
        ):
            mock_repo = AsyncMock()
            mock_repo.get_by_date = AsyncMock(return_value=[])
            mock_repo.get_weekly_summary = AsyncMock(
                return_value=[{"calories": 1800}, {"calories": 2200}]
            )
            MockRepo.return_value = mock_repo
            mock_gemini.chat = AsyncMock(return_value="Ответ")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await client.post("/api/chat", json={"message": "Как моя неделя?"})

        call_kwargs = mock_gemini.chat.call_args.kwargs
        # Average of 1800 and 2200 = 2000
        assert "2000" in call_kwargs["avg_calories"]

    async def test_no_weekly_data_uses_placeholder(self) -> None:
        with (
            patch("calorie_app.api.chat.MealRepo") as MockRepo,
            patch("calorie_app.api.chat.gemini_adapter") as mock_gemini,
        ):
            mock_repo = AsyncMock()
            mock_repo.get_by_date = AsyncMock(return_value=[])
            mock_repo.get_weekly_summary = AsyncMock(return_value=[])
            MockRepo.return_value = mock_repo
            mock_gemini.chat = AsyncMock(return_value="Ответ")

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await client.post("/api/chat", json={"message": "тест"})

        call_kwargs = mock_gemini.chat.call_args.kwargs
        assert call_kwargs["avg_calories"] == "нет данных"

    async def test_missing_message_returns_422(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/chat", json={})
        assert resp.status_code == 422

    async def test_gemini_error_returns_502(self) -> None:
        with (
            patch("calorie_app.api.chat.MealRepo") as MockRepo,
            patch("calorie_app.api.chat.gemini_adapter") as mock_gemini,
        ):
            mock_repo = AsyncMock()
            mock_repo.get_by_date = AsyncMock(return_value=[])
            mock_repo.get_weekly_summary = AsyncMock(return_value=[])
            MockRepo.return_value = mock_repo
            mock_gemini.chat = AsyncMock(side_effect=RuntimeError("Gemini down"))

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/chat", json={"message": "тест"})

        assert resp.status_code == 502
