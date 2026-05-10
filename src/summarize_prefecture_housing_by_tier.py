#!/usr/bin/env python3
"""按城市层级生成地级市房地产指标覆盖质量摘要。"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "purchased"
    / "prefecture-real-estate-indicators-long.csv"
)
DEFAULT_TIER_SEED = REPO_ROOT / "data" / "city-tier-seed-v1.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "prefecture-housing-tier-coverage-summary.csv"

FIELDNAMES = [
    "metric_name",
    "inferred_variable_id",
    "unit",
    "city_tier_v1",
    "tier_rank",
    "tier_confidence",
    "year_start",
    "year_end",
    "year_count",
    "city_count",
    "record_count",
    "observed_count",
    "missing_count",
    "missing_rate",
    "manual_review_city_count",
    "manual_review_cities",
    "special_city_count",
    "special_city_types",
    "coverage_grade",
    "coverage_notes",
]


def load_city_tiers(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        tiers = {row["city_key"]: row for row in csv.DictReader(f)}
    if not tiers:
        raise ValueError(f"城市层级种子表为空: {path}")
    return tiers


def coverage_grade(missing_rate: float, year_count: int, city_count: int) -> str:
    if city_count == 0 or year_count == 0:
        return "unusable"
    if missing_rate <= 0.02:
        return "good"
    if missing_rate <= 0.10:
        return "usable_with_caution"
    if missing_rate <= 0.25:
        return "weak"
    return "poor"


def build_summary(input_path: Path, tier_seed_path: Path) -> list[dict[str, str]]:
    city_tiers = load_city_tiers(tier_seed_path)
    grouped: dict[tuple[str, str, str, str], dict[str, object]] = defaultdict(
        lambda: {
            "tier_rank": "",
            "tier_confidence": "",
            "years": set(),
            "cities": set(),
            "manual_review_cities": set(),
            "special_city_types": set(),
            "special_cities": set(),
            "record_count": 0,
            "observed_count": 0,
            "missing_count": 0,
        }
    )

    with input_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            city_key = row["city_key"]
            if city_key not in city_tiers:
                raise ValueError(f"城市缺少层级映射: {city_key}")
            tier = city_tiers[city_key]
            key = (
                row["metric_name"],
                row["inferred_variable_id"],
                row["unit"],
                tier["city_tier_v1"],
            )

            item = grouped[key]
            item["tier_rank"] = tier["tier_rank"]
            item["tier_confidence"] = tier["tier_confidence"]
            item["years"].add(row["year"])
            item["cities"].add(city_key)
            item["record_count"] += 1
            if row["value_status"] == "missing":
                item["missing_count"] += 1
            else:
                item["observed_count"] += 1

            if tier["needs_manual_review"] == "yes":
                item["manual_review_cities"].add(row["city_normalized"])
            if tier["special_city_type"] != "normal":
                item["special_cities"].add(row["city_normalized"])
                item["special_city_types"].add(tier["special_city_type"])

    rows: list[dict[str, str]] = []
    for (metric_name, variable_id, unit, city_tier), item in sorted(
        grouped.items(),
        key=lambda pair: (int(pair[1]["tier_rank"]), pair[0][0]),
    ):
        years = sorted(item["years"])
        cities = sorted(item["cities"])
        manual_review_cities = sorted(item["manual_review_cities"])
        special_city_types = sorted(item["special_city_types"])
        record_count = int(item["record_count"])
        observed_count = int(item["observed_count"])
        missing_count = int(item["missing_count"])
        missing_rate = missing_count / record_count if record_count else 0.0

        notes: list[str] = []
        if missing_count:
            notes.append("存在缺失值")
        if manual_review_cities:
            notes.append("包含需人工核查城市")
        if special_city_types:
            notes.append("包含特殊城市标记")

        rows.append(
            {
                "metric_name": metric_name,
                "inferred_variable_id": variable_id,
                "unit": unit,
                "city_tier_v1": city_tier,
                "tier_rank": str(item["tier_rank"]),
                "tier_confidence": str(item["tier_confidence"]),
                "year_start": years[0],
                "year_end": years[-1],
                "year_count": str(len(years)),
                "city_count": str(len(cities)),
                "record_count": str(record_count),
                "observed_count": str(observed_count),
                "missing_count": str(missing_count),
                "missing_rate": f"{missing_rate:.4f}",
                "manual_review_city_count": str(len(manual_review_cities)),
                "manual_review_cities": ";".join(manual_review_cities),
                "special_city_count": str(len(item["special_cities"])),
                "special_city_types": ";".join(special_city_types),
                "coverage_grade": coverage_grade(missing_rate, len(years), len(cities)),
                "coverage_notes": "；".join(notes),
            }
        )

    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="本地长表路径")
    parser.add_argument("--tier-seed", type=Path, default=DEFAULT_TIER_SEED, help="城市层级种子表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出摘要 CSV 路径")
    args = parser.parse_args()

    rows = build_summary(args.input.resolve(), args.tier_seed.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
