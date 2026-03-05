# Benchmark

Измеряет точность оценки КБЖУ нашим LLM-пайплайном.

## Зависимости

`httpx` уже есть в основных зависимостях проекта.

## Запуск

```bash
# API должен быть запущен (docker compose up -d или uv run uvicorn ...)

# Текстовый бенчмарк (55 продуктов из USDA, не нужны доп. файлы)
uv run python benchmarks/benchmark.py text \
    --api-url http://localhost:8001 \
    --token "YOUR_BOT_TOKEN" \
    --user-id 12345 \
    --limit 55

# Фото-бенчмарк (нужен датасет, см. ниже)
uv run python benchmarks/benchmark.py photo \
    --api-url http://localhost:8001 \
    --token "YOUR_BOT_TOKEN" \
    --user-id 12345 \
    --dataset ./benchmarks/nutrition5k_samples \
    --limit 50
```

`--delay 1.0` — пауза между запросами (по умолчанию). Можно снизить до 0.5 если API локальный.

## Фото-датасет: Nutrition5k

Google Research, ~5k блюд с весом и КБЖУ. Два способа получить:

### Вариант A — gsutil (нужен Google Cloud)

```bash
pip install gsutil
gsutil -m cp -r "gs://nutrition5k_dataset/nutrition5k_dataset/imagery/realsense_overhead/" ./benchmarks/nutrition5k_samples
```

Скачает ~22 GB. Для бенчмарка достаточно первых 50 папок — можно прервать после.

### Вариант B — ручной CSV

Подготовить файл `benchmarks/nutrition5k_samples/benchmark_photos.csv` с колонками:

```
image_path,calories,protein_g,fat_g,carbs_g,portion_g,description
/path/to/photo.jpg,450,32.0,14.0,48.0,380,Dish name
```

`calories`, `protein_g` и т.д. — абсолютные значения для всего блюда (не на 100 г).
Сравнение происходит нормализованно на 100 г.

## Ожидаемый вывод (text)

```
  [ 1/55] Chicken breast, cooked              cal_err=+12  conf=high
  [ 2/55] Ground beef 80%, cooked             cal_err= -8  conf=medium
  ...

============================ TEXT BENCHMARK SUMMARY ============================
Category     Food (EN)                                Cal±   P±     F±     C±   Conf
----------------------------------------------------------------------------------
dairy        Cheddar cheese                          +28  +1.2   +2.1  -0.4  high
...
Metric               Calories    Protein        Fat      Carbs
MAE                      45.2        3.1        2.9        4.3
MAPE (calories)          12.3%
Bias (calories)          +8.1  (overestimates)
```

## Что делать с результатами

- **MAPE < 15%** — хорошая точность для LLM-пайплайна
- **Bias > 0** — модель систематически завышает калории (типично для жирных блюд)
- Высокие ошибки в категории `fat` — известная слабость visual LLM, жиры плохо распознаются по фото
- Если `confidence=low` у большинства записей — пересмотреть промпт в `adapters/prompts.py`
