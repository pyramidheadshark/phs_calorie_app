"""Integration tests for DB repos — only run in CI where ENVIRONMENT=test."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from calorie_app.adapters.db.models import Base
from calorie_app.adapters.db.repos import MealRepo, RecipeRepo, UserRepo
from calorie_app.config import settings
from calorie_app.core.domain import (
    MealEntry,
    NutritionFacts,
    RecipeEntry,
    User,
    UserSettings,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    os.getenv("ENVIRONMENT") != "test",
    reason="Integration tests only run in CI (ENVIRONMENT=test)",
)


@pytest.fixture()
async def db_session():
    # Function-scoped engine avoids event loop mismatch with asyncpg
    engine = create_async_engine(settings.postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture()
async def user_repo(db_session: AsyncSession) -> UserRepo:
    return UserRepo(db_session)


@pytest.fixture()
async def meal_repo(db_session: AsyncSession) -> MealRepo:
    return MealRepo(db_session)


@pytest.fixture()
async def recipe_repo(db_session: AsyncSession) -> RecipeRepo:
    return RecipeRepo(db_session)


def _uid() -> int:
    """Unique telegram_id per test to avoid cross-test interference."""
    return uuid.uuid4().int % (10**15)


def _make_user(uid: int) -> User:
    return User(
        telegram_id=uid,
        username=f"u{uid}",
        first_name="Test",
        settings=UserSettings(calorie_target=2000),
    )


def _make_meal(uid: int, *, calories: int = 500, hours_ago: int = 0) -> MealEntry:
    return MealEntry(
        user_id=uid,
        description="Тест еда",
        nutrition=NutritionFacts(
            calories=calories,
            protein_g=20.0,
            fat_g=10.0,
            carbs_g=50.0,
            portion_g=300,
        ),
        confidence="high",
        confirmed=True,
        logged_at=datetime.now(UTC) - timedelta(hours=hours_ago),
    )


# ---------------------------------------------------------------------------
# UserRepo
# ---------------------------------------------------------------------------


class TestUserRepo:
    async def test_upsert_creates_user(self, user_repo: UserRepo) -> None:
        uid = _uid()
        user = await user_repo.upsert(_make_user(uid))
        assert user.telegram_id == uid
        assert user.username == f"u{uid}"

    async def test_get_returns_user(self, user_repo: UserRepo) -> None:
        uid = _uid()
        await user_repo.upsert(_make_user(uid))
        fetched = await user_repo.get(uid)
        assert fetched is not None
        assert fetched.telegram_id == uid

    async def test_get_missing_returns_none(self, user_repo: UserRepo) -> None:
        result = await user_repo.get(999999999999)
        assert result is None

    async def test_upsert_updates_username(self, user_repo: UserRepo) -> None:
        uid = _uid()
        await user_repo.upsert(_make_user(uid))
        updated = User(
            telegram_id=uid,
            username="newname",
            first_name="New",
            settings=UserSettings(),
        )
        result = await user_repo.upsert(updated)
        assert result.username == "newname"

    async def test_update_settings_merges(self, user_repo: UserRepo) -> None:
        uid = _uid()
        await user_repo.upsert(_make_user(uid))
        await user_repo.update_settings(uid, {"calorie_target": 1800})
        user = await user_repo.get(uid)
        assert user is not None
        assert user.settings.calorie_target == 1800

    async def test_update_settings_missing_user_is_noop(self, user_repo: UserRepo) -> None:
        # Should not raise
        await user_repo.update_settings(999999999998, {"calorie_target": 500})


# ---------------------------------------------------------------------------
# MealRepo
# ---------------------------------------------------------------------------


class TestMealRepo:
    async def _setup_user(self, user_repo: UserRepo, uid: int) -> None:
        await user_repo.upsert(_make_user(uid))

    async def test_save_and_get_by_date(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        await meal_repo.save(_make_meal(uid, calories=600))

        today = datetime.now(UTC).date()
        meals = await meal_repo.get_by_date(uid, today)
        assert len(meals) == 1
        assert meals[0].nutrition.calories == 600

    async def test_get_by_date_empty(self, meal_repo: MealRepo) -> None:
        from datetime import date

        meals = await meal_repo.get_by_date(999999999997, date(2000, 1, 1))
        assert meals == []

    async def test_get_dates_with_logs(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        await meal_repo.save(_make_meal(uid))
        dates = await meal_repo.get_dates_with_logs(uid)
        assert len(dates) == 1

    async def test_get_history_summary(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        await meal_repo.save(_make_meal(uid, calories=1000))
        await meal_repo.save(_make_meal(uid, calories=500))
        summary = await meal_repo.get_history_summary(uid)
        assert len(summary) == 1
        assert summary[0]["calories"] == 1500
        assert summary[0]["meal_count"] == 2

    async def test_update_description(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        saved = await meal_repo.save(_make_meal(uid))
        updated = await meal_repo.update(saved.id, user_id=uid, description="Обновлённое")
        assert updated is not None
        assert updated.description == "Обновлённое"

    async def test_update_not_found(self, meal_repo: MealRepo) -> None:
        result = await meal_repo.update(uuid.uuid4(), user_id=1)
        assert result is None

    async def test_delete(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        saved = await meal_repo.save(_make_meal(uid))
        deleted = await meal_repo.delete(saved.id, user_id=uid)
        assert deleted is True
        today = datetime.now(UTC).date()
        meals = await meal_repo.get_by_date(uid, today)
        assert all(m.id != saved.id for m in meals)

    async def test_delete_wrong_user_returns_false(
        self, user_repo: UserRepo, meal_repo: MealRepo
    ) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        saved = await meal_repo.save(_make_meal(uid))
        deleted = await meal_repo.delete(saved.id, user_id=uid + 1)
        assert deleted is False

    async def test_get_weekly_summary(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        await meal_repo.save(_make_meal(uid, calories=1200))
        weekly = await meal_repo.get_weekly_summary(uid)
        assert len(weekly) == 1
        assert weekly[0]["calories"] == 1200
        assert "protein_g" in weekly[0]

    async def test_get_analytics(self, user_repo: UserRepo, meal_repo: MealRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        await meal_repo.save(_make_meal(uid, calories=2000))
        analytics = await meal_repo.get_analytics(uid, calorie_target=2000)
        assert "calorie_trend" in analytics
        assert "macro_split" in analytics
        assert "top_meals" in analytics
        assert analytics["total_days"] == 1
        assert analytics["avg_daily_calories"] == 2000


# ---------------------------------------------------------------------------
# RecipeRepo
# ---------------------------------------------------------------------------


def _make_recipe(uid: int) -> RecipeEntry:
    return RecipeEntry(
        user_id=uid,
        title="Борщ",
        description="Классический борщ",
        ingredients=["свёкла", "капуста"],
        instructions=["Варить"],
        nutrition_estimate=NutritionFacts(calories=350, protein_g=10.0),
        cooking_time_min=60,
        equipment_used=["кастрюля"],
    )


class TestRecipeRepo:
    async def _setup_user(self, user_repo: UserRepo, uid: int) -> None:
        await user_repo.upsert(_make_user(uid))

    async def test_save_and_get_history(self, user_repo: UserRepo, recipe_repo: RecipeRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        await recipe_repo.save(_make_recipe(uid))
        history = await recipe_repo.get_history(uid)
        assert len(history) == 1
        assert history[0].title == "Борщ"

    async def test_get_history_empty(self, recipe_repo: RecipeRepo) -> None:
        history = await recipe_repo.get_history(999999999996)
        assert history == []

    async def test_set_feedback_like(self, user_repo: UserRepo, recipe_repo: RecipeRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        saved = await recipe_repo.save(_make_recipe(uid))
        result = await recipe_repo.set_feedback(saved.id, uid, liked=True)
        assert result is not None
        assert result.liked is True

    async def test_set_feedback_not_found(self, recipe_repo: RecipeRepo) -> None:
        result = await recipe_repo.set_feedback(uuid.uuid4(), user_id=1, liked=True)
        assert result is None

    async def test_get_liked_titles(self, user_repo: UserRepo, recipe_repo: RecipeRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        saved = await recipe_repo.save(_make_recipe(uid))
        await recipe_repo.set_feedback(saved.id, uid, liked=True)
        titles = await recipe_repo.get_liked_titles(uid)
        assert "Борщ" in titles

    async def test_get_disliked_titles(self, user_repo: UserRepo, recipe_repo: RecipeRepo) -> None:
        uid = _uid()
        await self._setup_user(user_repo, uid)
        saved = await recipe_repo.save(_make_recipe(uid))
        await recipe_repo.set_feedback(saved.id, uid, liked=False)
        disliked = await recipe_repo.get_disliked_titles(uid)
        assert "Борщ" in disliked
