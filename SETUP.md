# Инструкция по запуску

## Что мы сделали

```
Telegram ──/start──► Bot (webhook.py) ──► отвечает с кнопкой "Открыть дневник"
                                                    │
                                                    ▼
                                         Telegram Mini App
                                         (frontend/dist/)
                                                    │  HTTP + x-telegram-init-data
                                                    ▼
                                         FastAPI backend (:8001)
                                                    │
                                         Gemini / PostgreSQL / Redis
```

**Бот** — принимает команды `/start` и `/help`, отправляет кнопку входа в приложение.
**Mini App** — веб-страница, которая открывается прямо в Telegram. Telegram автоматически
передаёт ей `window.Telegram.WebApp.initData` — это строка с данными пользователя и подписью.
Фронтенд шлёт её как заголовок `x-telegram-init-data`, бэкенд проверяет HMAC и авторизует.

---

## Шаг 1 — BotFather

1. Откройте @BotFather → `/newbot` → задайте имя и username
2. Скопируйте **Bot Token**
3. (Опционально) `/setdescription` — описание бота
4. Никаких дополнительных команд в BotFather не нужно — webhook и кнопку меню
   мы выставим скриптом автоматически

---

## Шаг 2 — .env

Создайте `.env` в корне проекта:

```env
# Обязательные
OPENROUTER_API_KEY=sk-or-v1-...
TELEGRAM_BOT_TOKEN=123456789:AAF...
APP_URL=https://your-domain.com          # публичный HTTPS URL (Mini App открывается отсюда)

# База данных (для Docker совпадают с docker-compose.yml)
POSTGRES_URL=postgresql+asyncpg://calorie:secret@postgres:5432/calorie_dev
POSTGRES_SYNC_URL=postgresql+psycopg2://calorie:secret@postgres:5432/calorie_dev
REDIS_URL=redis://redis:6379/0

# Опциональные
TELEGRAM_WEBHOOK_SECRET=my-random-secret   # произвольная строка, защищает /webhook/telegram
DEBUG=false
```

> **APP_URL** — единственный Mini App специфичный параметр. Это URL откуда Telegram
> загружает веб-страницу. Должен быть публичным HTTPS (например, через tuna/ngrok в разработке).

---

## Шаг 3 — Запуск стека

```bash
docker compose up -d --build
docker compose exec api uv run alembic upgrade head
```

Или локально без Docker:
```bash
uv sync
uv run uvicorn calorie_app.main:app --reload --port 8001
```

---

## Шаг 4 — Настройка бота (webhook + кнопка меню)

```bash
uv run python scripts/setup_bot.py
```

Скрипт:
1. Регистрирует webhook: `APP_URL/webhook/telegram`
2. Устанавливает **постоянную кнопку меню** — кнопка «Дневник» появится внизу каждого
   чата с ботом и будет открывать Mini App одним тапом

Если у вас кастомный URL для webhook:
```bash
uv run python scripts/setup_bot.py --webhook-url https://custom.domain.com/webhook/telegram
```

---

## Шаг 5 — Проверка

1. Откройте бота в Telegram
2. Отправьте `/start` — должна прийти кнопка «Открыть дневник»
3. Внизу чата должна быть постоянная кнопка «Дневник»
4. `GET /health` → `{"status": "ok", ...}`

---

## Туннель для локальной разработки (tuna)

Если используете tuna (как в нашем `start-dev.bat`):

```bash
# .env
APP_URL=https://phs-calorie.ru.tuna.am

# После запуска туннеля:
uv run python scripts/setup_bot.py
```

> Webhook нужно переустанавливать при каждом перезапуске туннеля с новым URL.

---

## Фронтенд

Фронтенд (HTML/JS/CSS) должен лежать в `frontend/dist/`. FastAPI раздаёт его автоматически
если папка существует. Разработка фронтенда ведётся отдельно.

Минимальный `frontend/dist/index.html` для проверки:
```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Calorie App</title></head>
<body>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<script>
  const tg = window.Telegram.WebApp;
  tg.ready();
  document.body.innerHTML = `<p>Hello, ${tg.initDataUnsafe?.user?.first_name}!</p>`;
</script>
</body>
</html>
```
