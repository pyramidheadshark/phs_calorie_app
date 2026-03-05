#!/usr/bin/env python3
"""Настройка бота: устанавливает webhook и кнопку меню (Mini App).

Запуск:
    uv run python scripts/setup_bot.py
    uv run python scripts/setup_bot.py --webhook-url https://custom-domain.com/webhook/telegram
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Добавляем src в path чтобы импортировать calorie_app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calorie_app.adapters.telegram import telegram_bot
from calorie_app.config import settings


async def main(webhook_url: str | None) -> None:
    if not settings.telegram_bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN не задан в .env")
        sys.exit(1)

    if not settings.app_url or settings.app_url == "https://example.com":
        print("ERROR: APP_URL не задан или стоит заглушка в .env")
        sys.exit(1)

    effective_webhook = webhook_url or f"{settings.app_url}/webhook/telegram"

    print(f"Bot token : ...{settings.telegram_bot_token[-8:]}")
    print(f"App URL   : {settings.app_url}")
    print(f"Webhook   : {effective_webhook}")
    print()

    # 1. Webhook
    print("1/2  Устанавливаю webhook...", end=" ", flush=True)
    ok = await telegram_bot.set_webhook(effective_webhook)
    print("OK" if ok else "FAILED")

    # 2. Menu button
    print("2/2  Устанавливаю кнопку меню (Mini App)...", end=" ", flush=True)
    ok = await telegram_bot.set_menu_button(settings.app_url)
    print("OK" if ok else "FAILED")

    print()
    print("Готово. Откройте бота в Telegram — внизу чата появится кнопка «Дневник».")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--webhook-url", help="Явный URL webhook (по умолчанию: APP_URL/webhook/telegram)"
    )
    args = parser.parse_args()
    asyncio.run(main(args.webhook_url))
