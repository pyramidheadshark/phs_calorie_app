from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from calorie_app.api.deps import get_current_user
from calorie_app.api.ratelimit import check_ai_rate_limit
from calorie_app.core.domain import NutritionAnalysis, NutritionFacts, User, UserSettings
from calorie_app.main import app

_FAKE_IMAGE = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG-like bytes


def _make_fake_user() -> User:
    return User(
        telegram_id=999888777,
        username="uploader",
        first_name="Up",
        settings=UserSettings(),
    )


def _make_fake_analysis() -> NutritionAnalysis:
    return NutritionAnalysis(
        description="Салат Цезарь",
        nutrition=NutritionFacts(
            calories=400, protein_g=20.0, fat_g=18.0, carbs_g=30.0, portion_g=250
        ),
        confidence="high",
        notes="",
        gemini_raw={},
    )


@pytest.fixture(autouse=True)
def override_auth() -> None:
    async def override_user() -> User:
        return _make_fake_user()

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[check_ai_rate_limit] = override_user
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(check_ai_rate_limit, None)


class TestAnalyzePhotoPath:
    async def test_success_returns_analysis(self) -> None:
        fake_analysis = _make_fake_analysis()
        mock_analyze = AsyncMock(return_value=fake_analysis)
        mock_save = lambda b: "/app/photos/test.jpg"  # noqa: E731

        with (
            patch("calorie_app.api.meals.gemini_adapter.analyze_photo", mock_analyze),
            patch("calorie_app.api.meals.photo_storage.save", mock_save),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/meal/photo-path",
                    files={"file": ("meal.jpg", _FAKE_IMAGE, "image/jpeg")},
                    data={"context": "обед"},
                    headers={"x-telegram-init-data": "test"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Салат Цезарь"
        assert data["nutrition"]["calories"] == 400
        assert data["confidence"] == "high"

    async def test_unsupported_image_type_returns_415(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/meal/photo-path",
                files={"file": ("doc.pdf", b"%PDF", "application/pdf")},
                headers={"x-telegram-init-data": "test"},
            )
        assert resp.status_code == 415

    async def test_oversized_file_returns_413(self) -> None:
        big_image = b"\xff\xd8\xff\xe0" + b"\x00" * (11 * 1024 * 1024)
        mock_analyze = AsyncMock(return_value=_make_fake_analysis())

        with patch("calorie_app.api.meals.gemini_adapter.analyze_photo", mock_analyze):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/meal/photo-path",
                    files={"file": ("big.jpg", big_image, "image/jpeg")},
                    headers={"x-telegram-init-data": "test"},
                )
        assert resp.status_code == 413


class TestAnalyzeVoice:
    async def test_success_returns_analysis(self) -> None:
        fake_analysis = _make_fake_analysis()
        mock_analyze = AsyncMock(return_value=fake_analysis)

        with patch("calorie_app.api.meals.gemini_adapter.analyze_voice", mock_analyze):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/meal/voice",
                    files={"file": ("note.ogg", b"OggS" + b"\x00" * 50, "audio/ogg")},
                    headers={"x-telegram-init-data": "test"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Салат Цезарь"
        assert data["nutrition"]["calories"] == 400

    async def test_unsupported_audio_type_returns_415(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/meal/voice",
                files={"file": ("note.mp4", b"\x00\x00\x00", "video/mp4")},
                headers={"x-telegram-init-data": "test"},
            )
        assert resp.status_code == 415
