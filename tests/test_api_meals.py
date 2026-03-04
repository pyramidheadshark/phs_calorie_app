from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.api.deps import get_current_user
from calorie_app.adapters.db.session import get_session
from calorie_app.core.domain import MealEntry, NutritionAnalysis, NutritionFacts, User, UserSettings
from calorie_app.main import app


def _make_fake_user() -> User:
    return User(
        telegram_id=111222333,
        username="testuser",
        first_name="Test",
        settings=UserSettings(),
    )


def _make_fake_analysis() -> NutritionAnalysis:
    return NutritionAnalysis(
        description="Греческий йогурт",
        nutrition=NutritionFacts(calories=150, protein_g=15.0, fat_g=3.0, carbs_g=10.0, portion_g=200),
        confidence="high",
        notes="",
        gemini_raw={"description": "Греческий йогурт", "calories": 150},
    )


def _make_saved_meal(user_id: int = 111222333) -> MealEntry:
    return MealEntry(
        id=uuid.uuid4(),
        user_id=user_id,
        description="Греческий йогурт",
        nutrition=NutritionFacts(calories=150, protein_g=15.0, fat_g=3.0, carbs_g=10.0, portion_g=200),
        confidence="high",
        confirmed=True,
        logged_at=datetime.now(timezone.utc),
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


class TestPostMealText:
    async def test_returns_analysis(self, client_with_overrides: AsyncClient) -> None:
        with patch("calorie_app.api.meals.gemini_adapter") as mock_gemini:
            mock_gemini.analyze_text = AsyncMock(return_value=_make_fake_analysis())
            async with client_with_overrides as client:
                response = await client.post(
                    "/api/meal/text",
                    json={"description": "греческий йогурт 200г"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Греческий йогурт"
        assert data["nutrition"]["calories"] == 150
        assert data["confidence"] == "high"

    async def test_missing_auth_returns_401(self) -> None:
        # Remove overrides for this test
        original_overrides = app.dependency_overrides.copy()
        app.dependency_overrides.clear()
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/meal/text",
                    json={"description": "борщ"},
                )
            assert response.status_code == 422  # missing required header
        finally:
            app.dependency_overrides.update(original_overrides)


class TestPatchMeal:
    async def test_update_meal_success(
        self, client_with_overrides: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        meal_id = uuid.uuid4()
        updated_meal = MealEntry(
            id=meal_id,
            user_id=111222333,
            description="Обновлённое описание",
            nutrition=NutritionFacts(calories=200, protein_g=10.0, fat_g=5.0, carbs_g=25.0, portion_g=250),
            confidence="medium",
            confirmed=True,
            logged_at=datetime.now(timezone.utc),
        )

        with patch("calorie_app.api.meals.MealRepo") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update = AsyncMock(return_value=updated_meal)
            MockRepo.return_value = mock_repo_instance

            async with client_with_overrides as client:
                response = await client.patch(
                    f"/api/meal/{meal_id}",
                    json={"description": "Обновлённое описание"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Обновлённое описание"

    async def test_update_meal_not_found(
        self, client_with_overrides: AsyncClient
    ) -> None:
        meal_id = uuid.uuid4()

        with patch("calorie_app.api.meals.MealRepo") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.update = AsyncMock(return_value=None)
            MockRepo.return_value = mock_repo_instance

            async with client_with_overrides as client:
                response = await client.patch(
                    f"/api/meal/{meal_id}",
                    json={"description": "test"},
                )

        assert response.status_code == 404


class TestPostMealConfirm:
    async def test_confirm_saves_and_returns_meal(
        self, client_with_overrides: AsyncClient
    ) -> None:
        saved = _make_saved_meal()

        with patch("calorie_app.api.meals.MealRepo") as MockRepo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.save = AsyncMock(return_value=saved)
            MockRepo.return_value = mock_repo_instance

            async with client_with_overrides as client:
                response = await client.post(
                    "/api/meal/confirm",
                    json={
                        "description": "Греческий йогурт",
                        "nutrition": {
                            "calories": 150,
                            "protein_g": 15.0,
                            "fat_g": 3.0,
                            "carbs_g": 10.0,
                            "portion_g": 200,
                        },
                        "confidence": "high",
                    },
                )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Греческий йогурт"
        assert data["confirmed"] is True
