from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.api.deps import get_current_user
from calorie_app.config import settings
from calorie_app.core.domain import User, UserSettings
from calorie_app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(calorie_target: int = 2000) -> User:
    return User(
        telegram_id=777888999,
        username="settingsuser",
        first_name="Settings",
        settings=UserSettings(calorie_target=calorie_target),
    )


def _valid_init_data(user_id: int = 777888999) -> str:
    token = settings.telegram_bot_token or "test-bot-token"
    user_json = json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":"))
    params = {"auth_date": "1700000000", "user": user_json}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def _auth_headers(user_id: int = 777888999) -> dict[str, str]:
    return {"x-telegram-init-data": _valid_init_data(user_id)}


# ---------------------------------------------------------------------------
# Tests: auth dependency
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    async def test_missing_header_returns_422(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/user/settings")
        assert resp.status_code == 422

    async def test_invalid_init_data_returns_401(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/user/settings",
                headers={"x-telegram-init-data": "auth_date=123&user={}&hash=bad"},
            )
        assert resp.status_code == 401

    async def test_valid_init_data_calls_repo_get(self) -> None:
        """validate_init_data succeeds → repo.get called (mock to avoid token dependency)."""
        fake_user_data = {"id": "777888999", "username": "settingsuser"}
        mock_repo_get = AsyncMock(return_value=_make_user())

        with (
            patch("calorie_app.api.deps.validate_init_data", return_value=fake_user_data),
            patch("calorie_app.api.deps.UserRepo") as MockRepo,
        ):
            MockRepo.return_value.get = mock_repo_get
            MockRepo.return_value.upsert = AsyncMock(return_value=_make_user())
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/api/user/settings", headers={"x-telegram-init-data": "any"}
                )
        mock_repo_get.assert_called_once()
        assert resp.status_code != 401

    async def test_new_user_upserted(self) -> None:
        """When repo.get returns None, repo.upsert is called to create user."""
        fake_user_data = {"id": "777888999", "first_name": "Test"}
        new_user = _make_user()

        with (
            patch("calorie_app.api.deps.validate_init_data", return_value=fake_user_data),
            patch("calorie_app.api.deps.UserRepo") as MockRepo,
        ):
            MockRepo.return_value.get = AsyncMock(return_value=None)
            MockRepo.return_value.upsert = AsyncMock(return_value=new_user)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/api/user/settings", headers={"x-telegram-init-data": "any"}
                )
        MockRepo.return_value.upsert.assert_called_once()
        assert resp.status_code != 401


# ---------------------------------------------------------------------------
# Tests: settings endpoints
# ---------------------------------------------------------------------------


class TestSettingsEndpoints:
    @pytest.fixture(autouse=True)
    def override_auth(self) -> None:
        fake_user = _make_user(calorie_target=2000)
        app.dependency_overrides[get_current_user] = lambda: fake_user
        yield
        app.dependency_overrides.clear()

    async def test_get_settings_returns_calorie_target(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/user/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["calorie_target"] == 2000

    async def test_get_settings_contains_macro_fields(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/user/settings")
        data = resp.json()
        assert "protein_target_g" in data
        assert "fat_target_g" in data
        assert "carbs_target_g" in data

    async def test_post_settings_returns_updated(self) -> None:
        payload = {
            "calorie_target": 1800,
            "protein_target_g": 140,
            "fat_target_g": 60,
            "carbs_target_g": 200,
            "breakfast_time": "08:00",
            "lunch_time": "13:00",
            "dinner_time": "19:00",
            "timezone": "Europe/Moscow",
            "meal_reminders_enabled": True,
            "summary_enabled": True,
            "profile_text": "",
            "goal_description": "",
            "kitchen_equipment": [],
            "food_preferences": "",
            "body_data": {},
        }
        mock_update = AsyncMock()
        with patch("calorie_app.api.settings.UserRepo") as MockRepo:
            MockRepo.return_value.update_settings = mock_update
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/user/settings", json=payload)
        assert resp.status_code == 200
        assert resp.json()["calorie_target"] == 1800
        mock_update.assert_called_once()

    async def test_parse_profile_success(self) -> None:
        parsed_result = {
            "calorie_target": 1600,
            "protein_target_g": 130,
            "fat_target_g": 55,
            "carbs_target_g": 180,
            "goal_description": "Похудеть",
            "kitchen_equipment": ["духовка"],
            "food_preferences": "без глютена",
            "body_data": {"weight_kg": 70},
        }
        mock_parse = AsyncMock(return_value=parsed_result)
        mock_update = AsyncMock()
        with (
            patch("calorie_app.api.settings.gemini_adapter.parse_profile", mock_parse),
            patch("calorie_app.api.settings.UserRepo") as MockRepo,
        ):
            MockRepo.return_value.update_settings = mock_update
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/user/profile/parse",
                    json={"profile_text": "Женщина, 30 лет, 70 кг, хочу похудеть"},
                )
        assert resp.status_code == 200
        data = resp.json()
        assert data["calorie_target"] == 1600
        assert data["goal_description"] == "Похудеть"
        mock_update.assert_called_once()

    async def test_parse_profile_gemini_error_returns_502(self) -> None:
        with patch(
            "calorie_app.api.settings.gemini_adapter.parse_profile",
            AsyncMock(side_effect=RuntimeError("LLM down")),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/user/profile/parse",
                    json={"profile_text": "любой текст"},
                )
        assert resp.status_code == 502
