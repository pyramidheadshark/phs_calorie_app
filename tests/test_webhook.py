from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from calorie_app.config import settings
from calorie_app.main import app

_SECRET = settings.telegram_webhook_secret or "test-secret"


def _headers() -> dict[str, str]:
    return {"x-telegram-bot-api-secret-token": _SECRET}


def _update(text: str, chat_id: int = 999) -> dict:
    return {"message": {"chat": {"id": chat_id}, "text": text, "from": {"id": chat_id}}}


class TestTelegramWebhook:
    async def test_wrong_secret_returns_403(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/webhook/telegram",
                json=_update("/start"),
                headers={"x-telegram-bot-api-secret-token": "wrong"},
            )
        assert resp.status_code == 403

    async def test_no_chat_id_returns_ok(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/webhook/telegram",
                json={"message": {}},
                headers=_headers(),
            )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    async def test_start_command_sends_message(self) -> None:
        mock_send = AsyncMock()
        with patch("calorie_app.api.webhook.telegram_bot.send_message", mock_send):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/webhook/telegram",
                    json=_update("/start"),
                    headers=_headers(),
                )
        assert resp.status_code == 200
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == 999  # chat_id
        assert "Привет" in call_args[0][1]

    async def test_help_command_sends_message(self) -> None:
        mock_send = AsyncMock()
        with patch("calorie_app.api.webhook.telegram_bot.send_message", mock_send):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/webhook/telegram",
                    json=_update("/help"),
                    headers=_headers(),
                )
        assert resp.status_code == 200
        mock_send.assert_called_once()
        assert "Как пользоваться" in mock_send.call_args[0][1]

    async def test_unknown_command_returns_ok_no_send(self) -> None:
        mock_send = AsyncMock()
        with patch("calorie_app.api.webhook.telegram_bot.send_message", mock_send):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/webhook/telegram",
                    json=_update("просто текст"),
                    headers=_headers(),
                )
        assert resp.status_code == 200
        mock_send.assert_not_called()
