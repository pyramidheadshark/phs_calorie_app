from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.adapters.db.session import get_session
from calorie_app.api.deps import get_current_user
from calorie_app.core.domain import NutritionFacts, RecipeEntry, User, UserSettings
from calorie_app.main import app


def _make_fake_user() -> User:
    return User(
        telegram_id=111222333,
        username="testuser",
        first_name="Test",
        settings=UserSettings(calorie_target=2000),
    )


def _make_fake_recipe(user_id: int = 111222333) -> RecipeEntry:
    return RecipeEntry(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Овсяная каша с ягодами",
        description="Полезный завтрак",
        ingredients=[{"name": "Овсянка", "amount": "100г"}, {"name": "Ягоды", "amount": "50г"}],
        instructions=["Сварить овсянку", "Добавить ягоды"],
        nutrition_estimate=NutritionFacts(
            calories=320, protein_g=10.0, fat_g=6.0, carbs_g=55.0, portion_g=300
        ),
        cooking_time_min=10,
        equipment_used=["плита"],
        liked=None,
        created_at=datetime.now(UTC),
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
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestGetRecipeHistory:
    async def test_returns_recipe_list(self, client_with_overrides: AsyncClient) -> None:
        fake_recipe = _make_fake_recipe()

        class MockRepo:
            async def get_history(self, user_id: int) -> list[RecipeEntry]:
                return [fake_recipe]

        with patch("calorie_app.api.recipes.RecipeRepo", return_value=MockRepo()):
            async with client_with_overrides as client:
                resp = await client.get(
                    "/api/recipes", headers={"x-telegram-init-data": "test"}
                )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Овсяная каша с ягодами"
        assert data[0]["cooking_time_min"] == 10

    async def test_returns_empty_list(self, client_with_overrides: AsyncClient) -> None:
        class MockRepo:
            async def get_history(self, user_id: int) -> list[RecipeEntry]:
                return []

        with patch("calorie_app.api.recipes.RecipeRepo", return_value=MockRepo()):
            async with client_with_overrides as client:
                resp = await client.get(
                    "/api/recipes", headers={"x-telegram-init-data": "test"}
                )

        assert resp.status_code == 200
        assert resp.json() == []


class TestGenerateRecipe:
    async def test_generate_success(self, client_with_overrides: AsyncClient) -> None:
        fake_recipe = _make_fake_recipe()

        class MockRepo:
            async def get_liked_titles(self, user_id: int) -> list[str]:
                return []

            async def get_disliked_titles(self, user_id: int) -> list[str]:
                return []

            async def save(self, recipe: RecipeEntry) -> RecipeEntry:
                return fake_recipe

        mock_gemini = AsyncMock(return_value=fake_recipe)
        with (
            patch("calorie_app.api.recipes.RecipeRepo", return_value=MockRepo()),
            patch("calorie_app.api.recipes.gemini_adapter.generate_recipe", mock_gemini),
        ):
            async with client_with_overrides as client:
                resp = await client.post(
                    "/api/recipes/generate", headers={"x-telegram-init-data": "test"}
                )

        assert resp.status_code == 200
        assert resp.json()["title"] == "Овсяная каша с ягодами"

    async def test_generate_gemini_error_returns_502(
        self, client_with_overrides: AsyncClient
    ) -> None:
        class MockRepo:
            async def get_liked_titles(self, user_id: int) -> list[str]:
                return []

            async def get_disliked_titles(self, user_id: int) -> list[str]:
                return []

        mock_gemini = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        with (
            patch("calorie_app.api.recipes.RecipeRepo", return_value=MockRepo()),
            patch("calorie_app.api.recipes.gemini_adapter.generate_recipe", mock_gemini),
        ):
            async with client_with_overrides as client:
                resp = await client.post(
                    "/api/recipes/generate", headers={"x-telegram-init-data": "test"}
                )

        assert resp.status_code == 502
        assert "Recipe generation failed" in resp.json()["detail"]


class TestSetRecipeFeedback:
    async def test_like_recipe(self, client_with_overrides: AsyncClient) -> None:
        fake_recipe = _make_fake_recipe()
        fake_recipe.liked = True

        class MockRepo:
            async def set_feedback(
                self, recipe_id: uuid.UUID, user_id: int, liked: bool
            ) -> RecipeEntry:
                return fake_recipe

        with patch("calorie_app.api.recipes.RecipeRepo", return_value=MockRepo()):
            async with client_with_overrides as client:
                resp = await client.patch(
                    f"/api/recipes/{fake_recipe.id}/feedback",
                    json={"liked": True},
                    headers={"x-telegram-init-data": "test"},
                )

        assert resp.status_code == 200
        assert resp.json()["liked"] is True

    async def test_recipe_not_found(self, client_with_overrides: AsyncClient) -> None:
        class MockRepo:
            async def set_feedback(
                self, recipe_id: uuid.UUID, user_id: int, liked: bool
            ) -> None:
                return None

        with patch("calorie_app.api.recipes.RecipeRepo", return_value=MockRepo()):
            async with client_with_overrides as client:
                resp = await client.patch(
                    f"/api/recipes/{uuid.uuid4()}/feedback",
                    json={"liked": False},
                    headers={"x-telegram-init-data": "test"},
                )

        assert resp.status_code == 404
