"""Curated food list with ground truth КБЖУ per 100 g.

Source: USDA FoodData Central SR Legacy (https://fdc.nal.usda.gov/).
Values are per 100 g of the food as described in the query.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroundTruth:
    calories: int
    protein_g: float
    fat_g: float
    carbs_g: float


@dataclass(frozen=True)
class BenchmarkFood:
    query: str  # exactly what we send to /api/meal/text
    name_en: str  # English reference name
    category: str
    per_100g: GroundTruth


FOODS: list[BenchmarkFood] = [
    # ── PROTEINS ────────────────────────────────────────────────────────────
    BenchmarkFood(
        "100 г варёной куриной грудки без кожи",
        "Chicken breast, cooked",
        "protein",
        GroundTruth(165, 31.0, 3.6, 0.0),
    ),
    BenchmarkFood(
        "100 г жареного говяжьего фарша (80% мяса)",
        "Ground beef 80%, cooked",
        "protein",
        GroundTruth(272, 26.1, 18.0, 0.0),
    ),
    BenchmarkFood(
        "100 г сырого лосося", "Atlantic salmon, raw", "protein", GroundTruth(208, 20.4, 13.4, 0.0)
    ),
    BenchmarkFood(
        "100 г яйца куриного варёного вкрутую",
        "Egg, hard-boiled",
        "protein",
        GroundTruth(155, 12.6, 10.6, 1.1),
    ),
    BenchmarkFood(
        "100 г тунца в собственном соку (консервы)",
        "Tuna, canned in water",
        "protein",
        GroundTruth(109, 25.5, 0.5, 0.0),
    ),
    BenchmarkFood(
        "100 г запечённой свиной вырезки",
        "Pork tenderloin, roasted",
        "protein",
        GroundTruth(143, 22.4, 5.6, 0.0),
    ),
    BenchmarkFood(
        "100 г варёной грудки индейки без кожи",
        "Turkey breast, cooked",
        "protein",
        GroundTruth(189, 28.7, 7.4, 0.0),
    ),
    BenchmarkFood(
        "100 г варёной трески", "Cod, cooked", "protein", GroundTruth(105, 22.8, 0.9, 0.0)
    ),
    BenchmarkFood(
        "100 г сырых королевских креветок",
        "Shrimp, raw",
        "protein",
        GroundTruth(85, 20.1, 0.9, 0.0),
    ),
    # ── DAIRY ────────────────────────────────────────────────────────────────
    BenchmarkFood(
        "100 г цельного молока 3.2%", "Whole milk 3.2%", "dairy", GroundTruth(61, 3.2, 3.6, 4.7)
    ),
    BenchmarkFood(
        "100 г натурального греческого йогурта 2%",
        "Greek yogurt 2%, plain",
        "dairy",
        GroundTruth(73, 10.3, 2.0, 3.6),
    ),
    BenchmarkFood(
        "100 г творога 5% жирности", "Cottage cheese 5%", "dairy", GroundTruth(121, 16.7, 5.0, 2.7)
    ),
    BenchmarkFood("100 г кефира 2.5%", "Kefir 2.5%", "dairy", GroundTruth(50, 3.4, 2.5, 3.6)),
    BenchmarkFood(
        "100 г сыра чеддер", "Cheddar cheese", "dairy", GroundTruth(403, 25.3, 33.3, 1.3)
    ),
    BenchmarkFood("100 г сметаны 15%", "Sour cream 15%", "dairy", GroundTruth(163, 2.8, 15.0, 4.3)),
    # ── GRAINS (cooked) ───────────────────────────────────────────────────────
    BenchmarkFood(
        "100 г варёного белого риса",
        "White rice, cooked",
        "grain",
        GroundTruth(130, 2.7, 0.3, 28.2),
    ),
    BenchmarkFood(
        "100 г варёной гречки", "Buckwheat, cooked", "grain", GroundTruth(92, 3.4, 0.6, 19.9)
    ),
    BenchmarkFood(
        "100 г варёных макарон из твёрдых сортов пшеницы",
        "Pasta, cooked",
        "grain",
        GroundTruth(131, 5.0, 1.1, 25.1),
    ),
    BenchmarkFood(
        "100 г овсяной каши на воде",
        "Oatmeal, cooked in water",
        "grain",
        GroundTruth(71, 2.5, 1.4, 12.0),
    ),
    BenchmarkFood(
        "100 г белого пшеничного хлеба", "White bread", "grain", GroundTruth(265, 9.0, 3.2, 49.2)
    ),
    BenchmarkFood(
        "100 г варёной перловой крупы",
        "Pearl barley, cooked",
        "grain",
        GroundTruth(123, 2.3, 0.4, 28.2),
    ),
    BenchmarkFood(
        "100 г варёного пшена", "Millet, cooked", "grain", GroundTruth(119, 3.5, 1.0, 23.7)
    ),
    # ── VEGETABLES ───────────────────────────────────────────────────────────
    BenchmarkFood(
        "100 г варёного картофеля без кожи",
        "Potato, boiled",
        "vegetable",
        GroundTruth(87, 1.9, 0.1, 20.1),
    ),
    BenchmarkFood(
        "100 г сырой моркови", "Carrot, raw", "vegetable", GroundTruth(41, 0.9, 0.2, 9.6)
    ),
    BenchmarkFood(
        "100 г свежей брокколи", "Broccoli, raw", "vegetable", GroundTruth(34, 2.8, 0.4, 6.6)
    ),
    BenchmarkFood(
        "100 г свежего помидора", "Tomato, raw", "vegetable", GroundTruth(18, 0.9, 0.2, 3.9)
    ),
    BenchmarkFood(
        "100 г свежего огурца", "Cucumber, raw", "vegetable", GroundTruth(15, 0.7, 0.1, 3.6)
    ),
    BenchmarkFood(
        "100 г свежей белокочанной капусты",
        "Cabbage, raw",
        "vegetable",
        GroundTruth(25, 1.3, 0.1, 5.8),
    ),
    BenchmarkFood(
        "100 г репчатого лука", "Onion, raw", "vegetable", GroundTruth(40, 1.1, 0.1, 9.3)
    ),
    BenchmarkFood(
        "100 г свежего красного болгарского перца",
        "Red bell pepper, raw",
        "vegetable",
        GroundTruth(31, 1.0, 0.3, 6.0),
    ),
    BenchmarkFood(
        "100 г свежего шпината", "Spinach, raw", "vegetable", GroundTruth(23, 2.9, 0.4, 3.6)
    ),
    BenchmarkFood(
        "100 г варёной свёклы", "Beet, cooked", "vegetable", GroundTruth(44, 1.7, 0.2, 10.0)
    ),
    # ── FRUITS ───────────────────────────────────────────────────────────────
    BenchmarkFood("100 г свежего яблока", "Apple, raw", "fruit", GroundTruth(52, 0.3, 0.2, 13.8)),
    BenchmarkFood("100 г банана", "Banana, raw", "fruit", GroundTruth(89, 1.1, 0.3, 22.8)),
    BenchmarkFood("100 г апельсина", "Orange, raw", "fruit", GroundTruth(47, 0.9, 0.1, 11.8)),
    BenchmarkFood("100 г клубники", "Strawberry, raw", "fruit", GroundTruth(32, 0.7, 0.3, 7.7)),
    BenchmarkFood("100 г арбуза", "Watermelon, raw", "fruit", GroundTruth(30, 0.6, 0.2, 7.6)),
    BenchmarkFood("100 г винограда", "Grapes, raw", "fruit", GroundTruth(69, 0.7, 0.2, 18.1)),
    BenchmarkFood("100 г груши", "Pear, raw", "fruit", GroundTruth(57, 0.4, 0.1, 15.2)),
    # ── LEGUMES (cooked) ──────────────────────────────────────────────────────
    BenchmarkFood(
        "100 г варёной красной чечевицы",
        "Red lentils, cooked",
        "legume",
        GroundTruth(116, 9.0, 0.4, 20.1),
    ),
    BenchmarkFood(
        "100 г варёного нута", "Chickpeas, cooked", "legume", GroundTruth(164, 8.9, 2.6, 27.4)
    ),
    BenchmarkFood(
        "100 г варёной красной фасоли",
        "Red kidney beans, cooked",
        "legume",
        GroundTruth(127, 8.7, 0.5, 22.8),
    ),
    # ── FATS / OILS ───────────────────────────────────────────────────────────
    BenchmarkFood("100 г оливкового масла", "Olive oil", "fat", GroundTruth(884, 0.0, 100.0, 0.0)),
    BenchmarkFood(
        "100 г сливочного масла 82.5%", "Butter 82.5%", "fat", GroundTruth(745, 0.9, 82.5, 0.1)
    ),
    BenchmarkFood("100 г авокадо", "Avocado, raw", "fat", GroundTruth(160, 2.0, 14.7, 8.5)),
    # ── NUTS / SEEDS ──────────────────────────────────────────────────────────
    BenchmarkFood(
        "100 г сырого миндаля", "Almonds, raw", "nut", GroundTruth(579, 21.2, 49.9, 21.6)
    ),
    BenchmarkFood("100 г грецких орехов", "Walnuts", "nut", GroundTruth(654, 15.2, 65.2, 13.7)),
    BenchmarkFood(
        "100 г семян подсолнечника (очищенных)",
        "Sunflower seeds",
        "nut",
        GroundTruth(584, 20.8, 51.5, 20.0),
    ),
    # ── OTHER / PROCESSED ─────────────────────────────────────────────────────
    BenchmarkFood("100 г мёда", "Honey", "other", GroundTruth(304, 0.3, 0.0, 82.4)),
    BenchmarkFood(
        "100 г молочного шоколада", "Milk chocolate", "other", GroundTruth(535, 7.7, 29.7, 59.4)
    ),
    BenchmarkFood(
        "100 г варёной докторской колбасы",
        "Boiled sausage (doktorskaya)",
        "other",
        GroundTruth(257, 12.8, 22.2, 1.8),
    ),
    BenchmarkFood(
        "100 г отварного куриного яйца (белок)",
        "Egg white, cooked",
        "other",
        GroundTruth(52, 10.9, 0.2, 0.7),
    ),
    BenchmarkFood(
        "100 г картофельных чипсов", "Potato chips", "other", GroundTruth(536, 7.0, 35.0, 53.0)
    ),
]
