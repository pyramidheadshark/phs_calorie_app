# phs-calorie-app

Telegram Mini App для персонального учёта КБЖУ с AI-распознаванием еды через Gemini.

Пользователь фотографирует блюдо, описывает его текстом или голосом — приложение возвращает калории, белки, жиры и углеводы. Все данные сохраняются в дневник с историей и статистикой.

> **Этот проект целиком написан AI-агентом** (Claude) по пресетам и инфраструктуре из репозитория [pyramidheadshark/ml-claude-infra](https://github.com/pyramidheadshark/ml-claude-infra). Код, тесты, миграции, Docker-конфиг — всё сгенерировано в рамках агентных сессий без ручного написания кода.

---

## Стек

| Слой | Технология |
|---|---|
| API | FastAPI + uvicorn |
| AI | OpenRouter → `google/gemini-2.5-flash` |
| База данных | PostgreSQL + SQLAlchemy (asyncpg) |
| Миграции | Alembic |
| Фоновые задачи | Celery + Redis |
| Пакеты | uv |
| Деплой | Docker Compose |

---

## Структура проекта

```
src/calorie_app/
├── adapters/
│   ├── db/
│   │   ├── models.py       — SQLAlchemy ORM-модели
│   │   ├── repos.py        — репозитории (MealRepo, UserRepo, RecipeRepo)
│   │   └── session.py      — async engine + фабрика сессий
│   ├── gemini.py           — GeminiAdapter: analyze_photo/text/voice, generate_recipe
│   ├── prompts.py          — все системные промпты как константы
│   ├── storage.py          — сохранение/очистка фото на диске
│   └── telegram.py         — TelegramBot: отправка сообщений, валидация initData
├── api/
│   ├── deps.py             — get_current_user (HMAC-аутентификация Telegram)
│   ├── ratelimit.py        — Redis rate limiter: 30 AI-запросов/час на пользователя
│   ├── logs.py             — GET /api/daily, /api/history, /api/stats/*
│   ├── meals.py            — POST/PATCH/DELETE /api/meal/*
│   ├── recipes.py          — POST/GET /api/recipes, PATCH feedback
│   ├── settings.py         — GET/POST /api/user/settings, POST /api/user/profile/parse
│   └── webhook.py          — POST /webhook/telegram (/start, /help)
├── core/
│   ├── domain.py           — доменные объекты (MealEntry, User, DailyLog и др.)
│   └── calculator.py       — compute_streak, macro_percentages, calorie_progress
├── models/
│   └── schemas.py          — Pydantic-схемы запросов и ответов
├── config.py               — Settings из .env (pydantic-settings)
├── main.py                 — FastAPI app, роутеры, lifespan
└── worker.py               — Celery: cleanup_photos, send_daily_summaries
```

---

## API

### Еда

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/meal/photo-path` | Фото → Gemini Vision → КБЖУ + сохранение пути |
| `POST` | `/api/meal/text` | Текстовое описание → КБЖУ |
| `POST` | `/api/meal/voice` | Аудиофайл (ogg/mp3/wav/aac) → КБЖУ |
| `POST` | `/api/meal/confirm` | Подтвердить и сохранить приём пищи |
| `PATCH` | `/api/meal/{id}` | Редактировать описание / КБЖУ / уверенность |
| `DELETE` | `/api/meal/{id}` | Удалить запись |

### Дневник и статистика

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/daily/{YYYY-MM-DD}` | Приёмы пищи за день + суммарные КБЖУ |
| `GET` | `/api/history?page=1&page_size=30` | Список дней с количеством записей и калориями (пагинация) |
| `GET` | `/api/stats/weekly` | Сводка по макронутриентам за 7 дней |
| `GET` | `/api/stats/streak` | Текущий streak (дней подряд с записями) |
| `GET` | `/api/stats/analytics` | Аналитика за 30 дней: тренд калорий, макро-сплит, топ блюд |

### Профиль и рецепты

| Метод | Путь | Описание |
|---|---|---|
| `GET/POST` | `/api/user/settings` | Настройки: цели, КБЖУ-таргеты, оборудование |
| `POST` | `/api/user/profile/parse` | Gemini парсит свободный текст профиля → обновляет цели |
| `POST` | `/api/recipes/generate` | Генерация рецепта по профилю пользователя |
| `GET` | `/api/recipes` | История сгенерированных рецептов |
| `PATCH` | `/api/recipes/{id}/feedback` | Лайк / дизлайк рецепта |

### Прочее

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Статус сервиса и текущая модель |
| `POST` | `/webhook/telegram` | Входящие апдейты от Telegram |

---

## Аутентификация

Все `/api/*` эндпоинты требуют заголовок:

```
x-telegram-init-data: <Telegram.WebApp.initData>
```

Сервер проверяет HMAC-SHA256 подпись по `BOT_TOKEN`. Если подпись некорректна → `401`.

---

## Rate limiting

AI-эндпоинты (`/photo-path`, `/text`, `/voice`) ограничены **30 запросами в час** на пользователя через Redis. При превышении → `429 Too Many Requests` с заголовком `Retry-After`.

---

## Запуск

### 1. Переменные окружения

Создать `.env` в корне:

```env
# AI
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-3-flash-preview

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBHOOK_SECRET=your-secret

# Приложение
APP_URL=https://your-domain.com

# БД (используется внутри Docker-сети)
POSTGRES_URL=postgresql+asyncpg://calorie:secret@postgres:5432/calorie_dev
POSTGRES_SYNC_URL=postgresql+psycopg2://calorie:secret@postgres:5432/calorie_dev
REDIS_URL=redis://redis:6379/0
```

### 2. Docker Compose

```bash
# Поднять все сервисы (api, postgres, redis, worker, beat, tunnel)
docker compose up -d --build

# Применить миграции БД
docker compose exec api uv run alembic upgrade head

# Проверить
curl http://localhost:8001/health
```

Webhook у Telegram и кнопка Mini App в меню бота **регистрируются автоматически** при старте `api`-контейнера.

### 4. Локальный запуск (без Docker)

```bash
uv sync
uv run uvicorn calorie_app.main:app --reload --port 8001
```

Требует локального PostgreSQL и Redis с настройками по умолчанию из `config.py`.

---

## Тесты

```bash
uv sync --dev
uv run python -m pytest -x -v
```

92 теста, не требуют запущенного PostgreSQL/Redis — всё замокировано. Coverage 77%.

```
tests/
├── conftest.py                — фикстуры: fake_user, fake_analysis, mock_session
├── test_gemini.py             — GeminiAdapter: все методы + парсинг ответов
├── test_repos.py              — unit: MealRepo, UserRepo, RecipeRepo
├── test_api_meals.py          — /photo-path, /text, /voice, confirm, PATCH, DELETE
├── test_api_logs.py           — /daily, /history (с пагинацией), /stats/*
├── test_api_analytics.py      — /stats/analytics
├── test_api_recipes.py        — /recipes generate, history, feedback
├── test_api_settings.py       — /user/settings, /user/profile/parse
├── test_ratelimit.py          — rate limit: лимит, превышение, Redis down
├── test_webhook.py            — /webhook/telegram: /start, /help
├── test_calculator.py         — compute_streak, macro_percentages
├── test_telegram.py           — validate_init_data HMAC
└── test_repos_integration.py  — интеграционные (требуют Postgres, ENVIRONMENT=test)
```

---

## Миграции

```bash
# Создать новую миграцию
uv run alembic revision --autogenerate -m "описание"

# Применить
uv run alembic upgrade head

# Откатить
uv run alembic downgrade -1
```

---

## Архитектурные решения

- **Stateless API** — аутентификация через Telegram initData при каждом запросе, без сессий
- **Фото хранятся локально** на volume `/app/photos`; путь сохраняется в БД, файлы удаляются Celery-задачей через 24 часа
- **UserSettings в JSONB** — гибкая схема без миграций при добавлении новых полей профиля
- **Fail-open rate limiter** — если Redis недоступен, запрос пропускается (не блокируется)
- **Промпты вынесены** в `adapters/prompts.py` — отдельно от логики адаптера
