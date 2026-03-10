#!/usr/bin/env python3
"""Benchmark: точность оценки КБЖУ нашим LLM-пайплайном.

Два режима:
  text   — USDA ground truth, 55 продуктов, текстовые запросы
  photo  — Nutrition5k ground truth, фото → /api/meal/photo-path

Аутентификация:
  Передать --init-data (готовая строка) или --token + --user-id (скрипт
  сгенерирует валидный initData автоматически).

Примеры:
  python benchmarks/benchmark.py text \\
      --api-url http://localhost:8001 \\
      --token 123:ABC --user-id 42

  python benchmarks/benchmark.py photo \\
      --dataset ./nutrition5k_samples \\
      --api-url http://localhost:8001 \\
      --token 123:ABC --user-id 42 --limit 50
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import httpx

# ── path fix so we can import foods.py from the same dir ─────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from foods import FOODS, BenchmarkFood, GroundTruth  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────


def gen_init_data(bot_token: str, user_id: int, username: str = "benchmark") -> str:
    """Generate a valid Telegram Web App initData string."""
    user_json = json.dumps(
        {"id": user_id, "first_name": "Benchmark", "username": username},
        separators=(",", ":"),
    )
    params = {"auth_date": str(int(time.time())), "user": user_json}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params["hash"] = hash_val
    return urlencode(params)


# ─────────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class FoodResult:
    food: BenchmarkFood
    predicted: GroundTruth
    portion_g: int
    confidence: str
    error: str | None = None

    @property
    def cal_err(self) -> float:
        return self.predicted.calories - self.food.per_100g.calories

    @property
    def protein_err(self) -> float:
        return self.predicted.protein_g - self.food.per_100g.protein_g

    @property
    def fat_err(self) -> float:
        return self.predicted.fat_g - self.food.per_100g.fat_g

    @property
    def carbs_err(self) -> float:
        return self.predicted.carbs_g - self.food.per_100g.carbs_g


@dataclass
class PhotoResult:
    image_path: str
    description: str
    true_gt: GroundTruth
    true_portion_g: int
    predicted: GroundTruth
    predicted_portion_g: int
    confidence: str
    error: str | None = None

    def _norm(self, gt: GroundTruth, portion: int) -> GroundTruth:
        """Normalize to per-100g for fair comparison."""
        if portion == 0:
            return gt
        factor = 100.0 / portion
        return GroundTruth(
            calories=round(gt.calories * factor),
            protein_g=round(gt.protein_g * factor, 1),
            fat_g=round(gt.fat_g * factor, 1),
            carbs_g=round(gt.carbs_g * factor, 1),
        )

    @property
    def true_per100(self) -> GroundTruth:
        return self._norm(self.true_gt, self.true_portion_g)

    @property
    def pred_per100(self) -> GroundTruth:
        return self._norm(self.predicted, self.predicted_portion_g)

    @property
    def cal_err(self) -> float:
        return self.pred_per100.calories - self.true_per100.calories


# ─────────────────────────────────────────────────────────────────────────────
# Text benchmark
# ─────────────────────────────────────────────────────────────────────────────


def run_text_benchmark(
    api_url: str,
    init_data: str,
    limit: int,
    delay: float,
    offset: int = 0,
) -> list[FoodResult]:
    foods = FOODS[offset:offset + limit]
    results: list[FoodResult] = []

    with httpx.Client(base_url=api_url, timeout=30.0, trust_env=False) as client:
        for i, food in enumerate(foods, 1):
            print(f"  [{i:2d}/{len(foods)}] {food.name_en[:45]:<45}", end=" ", flush=True)
            try:
                resp = client.post(
                    "/api/meal/text",
                    json={"description": food.query},
                    headers={"x-telegram-init-data": init_data},
                )
                resp.raise_for_status()
                data = resp.json()
                n = data["nutrition"]
                predicted = GroundTruth(
                    calories=n["calories"],
                    protein_g=n["protein_g"],
                    fat_g=n["fat_g"],
                    carbs_g=n["carbs_g"],
                )
                result = FoodResult(
                    food=food,
                    predicted=predicted,
                    portion_g=n["portion_g"],
                    confidence=data["confidence"],
                )
                sign = "+" if result.cal_err >= 0 else ""
                print(f"cal_err={sign}{result.cal_err:+.0f}  conf={result.confidence}")
            except Exception as exc:
                print(f"ERROR: {exc}")
                result = FoodResult(
                    food=food,
                    predicted=GroundTruth(0, 0, 0, 0),
                    portion_g=0,
                    confidence="low",
                    error=str(exc),
                )
            results.append(result)
            if i < len(foods):
                time.sleep(delay)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Photo benchmark
# ─────────────────────────────────────────────────────────────────────────────


def load_photo_dataset(dataset_path: Path, limit: int) -> list[dict]:  # type: ignore[type-arg]
    """Load photo samples from a CSV or Nutrition5k directory.

    Supported formats:
    1. CSV file (benchmark_photos.csv) with columns:
       image_path, calories, protein_g, fat_g, carbs_g, portion_g, description
    2. Nutrition5k directory: reads dish_*/rgb.png + dish_metadata_cafe*.txt
       See benchmarks/README.md for the expected file layout.
    """
    csv_path = dataset_path / "benchmark_photos.csv"
    if csv_path.exists():
        samples = []
        with csv_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                samples.append(row)
                if len(samples) >= limit:
                    break
        return samples

    # Nutrition5k directory layout
    samples = []
    for dish_dir in sorted(dataset_path.glob("dish_*")):
        if len(samples) >= limit:
            break
        img = dish_dir / "rgb.png"
        if not img.exists():
            continue
        meta = next(dish_dir.glob("dish_metadata_cafe*.txt"), None)
        if meta is None:
            continue
        lines = meta.read_text().splitlines()
        if len(lines) < 6:
            continue
        try:
            # Nutrition5k metadata: line 2=total_calories, 3=total_weight(g),
            # 4=total_fat(g), 5=total_carb(g), 6=total_protein(g)
            samples.append(
                {
                    "image_path": str(img),
                    "calories": lines[1].strip(),
                    "portion_g": lines[2].strip(),
                    "fat_g": lines[3].strip(),
                    "carbs_g": lines[4].strip(),
                    "protein_g": lines[5].strip(),
                    "description": dish_dir.name,
                }
            )
        except (IndexError, ValueError):
            continue

    if not samples:
        print(f"No samples found in {dataset_path}. See benchmarks/README.md.")
        sys.exit(1)
    return samples


def run_photo_benchmark(
    api_url: str,
    init_data: str,
    dataset_path: Path,
    limit: int,
    delay: float,
) -> list[PhotoResult]:
    samples = load_photo_dataset(dataset_path, limit)
    results: list[PhotoResult] = []

    with httpx.Client(base_url=api_url, timeout=60.0, trust_env=False) as client:
        for i, sample in enumerate(samples, 1):
            img_path = Path(sample["image_path"])
            label = img_path.parent.name or img_path.name
            print(f"  [{i:2d}/{len(samples)}] {label[:45]:<45}", end=" ", flush=True)
            try:
                with img_path.open("rb") as f:
                    resp = client.post(
                        "/api/meal/photo-path",
                        files={"file": (img_path.name, f, "image/png")},
                        data={"context": sample.get("description", "")},
                        headers={"x-telegram-init-data": init_data},
                    )
                resp.raise_for_status()
                data = resp.json()
                n = data["nutrition"]
                true_gt = GroundTruth(
                    calories=int(float(sample["calories"])),
                    protein_g=float(sample["protein_g"]),
                    fat_g=float(sample["fat_g"]),
                    carbs_g=float(sample["carbs_g"]),
                )
                predicted = GroundTruth(
                    calories=n["calories"],
                    protein_g=n["protein_g"],
                    fat_g=n["fat_g"],
                    carbs_g=n["carbs_g"],
                )
                result = PhotoResult(
                    image_path=str(img_path),
                    description=data.get("description", ""),
                    true_gt=true_gt,
                    true_portion_g=int(float(sample.get("portion_g", 100) or 100)),
                    predicted=predicted,
                    predicted_portion_g=n["portion_g"] or 100,
                    confidence=data["confidence"],
                )
                print(f"cal/100g_err={result.cal_err:+.0f}  conf={result.confidence}")
            except Exception as exc:
                print(f"ERROR: {exc}")
                result = PhotoResult(
                    image_path=str(img_path),
                    description="",
                    true_gt=GroundTruth(0, 0, 0, 0),
                    true_portion_g=100,
                    predicted=GroundTruth(0, 0, 0, 0),
                    predicted_portion_g=100,
                    confidence="low",
                    error=str(exc),
                )
            results.append(result)
            if i < len(samples):
                time.sleep(delay)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Metrics & reporting
# ─────────────────────────────────────────────────────────────────────────────


def _pct(value: float, total: float) -> str:
    if total == 0:
        return "n/a"
    return f"{abs(value) / total * 100:.1f}%"


def print_text_report(results: list[FoodResult]) -> None:
    ok = [r for r in results if r.error is None]
    if not ok:
        print("No successful results.")
        return

    print("\n" + "=" * 90)
    print(f"{'TEXT BENCHMARK SUMMARY':^90}")
    print("=" * 90)
    print(f"{'Category':<12} {'Food (EN)':<40} {'Cal±':>6} {'P±':>6} {'F±':>6} {'C±':>6}  {'Conf'}")
    print("-" * 90)

    categories: dict[str, list[FoodResult]] = {}
    for r in ok:
        categories.setdefault(r.food.category, []).append(r)

    for cat in sorted(categories):
        for r in categories[cat]:
            print(
                f"{cat:<12} {r.food.name_en[:40]:<40} "
                f"{r.cal_err:>+6.0f} {r.protein_err:>+6.1f} "
                f"{r.fat_err:>+6.1f} {r.carbs_err:>+6.1f}  {r.confidence}"
            )

    print("-" * 90)
    cal_errs = [abs(r.cal_err) for r in ok]
    p_errs = [abs(r.protein_err) for r in ok]
    f_errs = [abs(r.fat_err) for r in ok]
    c_errs = [abs(r.carbs_err) for r in ok]
    cal_true = [r.food.per_100g.calories for r in ok]

    mae_cal = sum(cal_errs) / len(ok)
    mae_p = sum(p_errs) / len(ok)
    mae_f = sum(f_errs) / len(ok)
    mae_c = sum(c_errs) / len(ok)

    mape_cal = sum(
        abs(e) / t * 100 for e, t in zip([r.cal_err for r in ok], cal_true, strict=False) if t > 0
    ) / len(ok)
    bias_cal = sum(r.cal_err for r in ok) / len(ok)

    print(f"\n{'Metric':<20} {'Calories':>10} {'Protein':>10} {'Fat':>10} {'Carbs':>10}")
    print(f"{'MAE':<20} {mae_cal:>10.1f} {mae_p:>10.1f} {mae_f:>10.1f} {mae_c:>10.1f}")
    print(f"{'MAPE (calories)':<20} {mape_cal:>9.1f}%")
    print(
        f"{'Bias (calories)':<20} {bias_cal:>+10.1f}  ({'overestimates' if bias_cal > 0 else 'underestimates'})"
    )

    conf_counts: dict[str, int] = {}
    for r in ok:
        conf_counts[r.confidence] = conf_counts.get(r.confidence, 0) + 1
    print(f"\nConfidence distribution: {conf_counts}")
    print(f"Success: {len(ok)}/{len(results)} foods  |  Errors: {len(results) - len(ok)}")


def print_photo_report(results: list[PhotoResult]) -> None:
    ok = [r for r in results if r.error is None]
    if not ok:
        print("No successful results.")
        return

    print("\n" + "=" * 80)
    print(f"{'PHOTO BENCHMARK SUMMARY (per 100g)':^80}")
    print("=" * 80)
    print(f"{'Dish':<35} {'Cal/100g±':>10} {'PredPortion':>12} {'TruePortion':>12}  {'Conf'}")
    print("-" * 80)

    for r in ok:
        print(
            f"{Path(r.image_path).parent.name[:35]:<35} "
            f"{r.cal_err:>+10.0f} "
            f"{r.predicted_portion_g:>12}g "
            f"{r.true_portion_g:>12}g  {r.confidence}"
        )

    print("-" * 80)
    cal_errs = [abs(r.cal_err) for r in ok]
    mae_cal = sum(cal_errs) / len(ok)
    bias_cal = sum(r.cal_err for r in ok) / len(ok)
    mape_cal = sum(
        abs(r.cal_err) / r.true_per100.calories * 100 for r in ok if r.true_per100.calories > 0
    ) / len(ok)

    print(f"\n{'MAE (cal/100g)':<25} {mae_cal:.1f}")
    print(f"{'MAPE (calories)':<25} {mape_cal:.1f}%")
    print(
        f"{'Bias (calories)':<25} {bias_cal:+.1f}  ({'overestimates' if bias_cal > 0 else 'underestimates'})"
    )
    print(f"\nSuccess: {len(ok)}/{len(results)}  |  Errors: {len(results) - len(ok)}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api-url", default="http://localhost:8001")
    common.add_argument("--init-data", help="Raw x-telegram-init-data string")
    common.add_argument("--token", help="Bot token (used to generate init-data)")
    common.add_argument(
        "--user-id", type=int, default=1, help="Telegram user ID for generated init-data"
    )
    common.add_argument("--limit", type=int, default=55, help="Max number of items to test")
    common.add_argument("--offset", type=int, default=0, help="Skip first N foods")
    common.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")

    sub.add_parser("text", parents=[common], help="Run text pipeline benchmark (USDA foods)")
    photo_p = sub.add_parser("photo", parents=[common], help="Run photo pipeline benchmark")
    photo_p.add_argument(
        "--dataset", required=True, help="Path to dataset dir (Nutrition5k or CSV)"
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.init_data:
        init_data = args.init_data
    elif args.token:
        init_data = gen_init_data(args.token, args.user_id)
        print(f"Generated init-data for user_id={args.user_id}")
    else:
        print("Error: provide --init-data or --token + --user-id", file=sys.stderr)
        sys.exit(1)

    if args.mode == "text":
        n = min(args.limit, len(FOODS) - args.offset)
        print(f"\nRunning TEXT benchmark: {n} foods (offset={args.offset}) -> {args.api_url}\n")
        results = run_text_benchmark(args.api_url, init_data, args.limit, args.delay, args.offset)
        print_text_report(results)

    elif args.mode == "photo":
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            print(f"Dataset path not found: {dataset_path}", file=sys.stderr)
            sys.exit(1)
        print(f"\nRunning PHOTO benchmark: {args.limit} dishes -> {args.api_url}\n")
        results = run_photo_benchmark(args.api_url, init_data, dataset_path, args.limit, args.delay)
        print_photo_report(results)


if __name__ == "__main__":
    main()
