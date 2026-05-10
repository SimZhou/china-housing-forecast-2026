#!/usr/bin/env python3
"""按城市细分组生成地级市房地产指标覆盖质量摘要。"""

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
DEFAULT_SEGMENT_SEED = REPO_ROOT / "data" / "city-segment-seed-v1.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "prefecture-housing-segment-coverage-summary.csv"

FIELDNAMES = [
    "metric_name",
    "inferred_variable_id",
    "unit",
    "city_segment_v1",
    "segment_rank",
    "segment_confidence",
    "city_tier_v1",
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
    "coverage_grade",
    "coverage_notes",
]


def load_city_segments(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        segments = {row["city_key"]: row for row in csv.DictReader(f)}
    if not segments:
        raise ValueError(f"城市细分种子表为空: {path}")
    return segments


def coverage_grade(missing_rate: float, city_count: int, year_count: int) -> str:
    if city_count == 0 or year_count == 0:
        return "unusable"
    if missing_rate <= 0.02:
        return "good"
    if missing_rate <= 0.10:
        return "usable_with_caution"
    if missing_rate <= 0.25:
        return "weak"
    return "poor"


def build_summary(input_path: Path, segment_seed_path: Path) -> list[dict[str, str]]:
    city_segments = load_city_segments(segment_seed_path)
    grouped: dict[tuple[str, str, str, str], dict[str, object]] = defaultdict(
        lambda: {
            "segment_rank": "",
            "segment_confidence": "",
            "city_tiers": set(),
            "years": set(),
            "cities": set(),
            "manual_review_cities": set(),
            "record_count": 0,
            "observed_count": 0,
            "missing_count": 0,
        }
    )

    with input_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            city_key = row["city_key"]
            if city_key not in city_segments:
                raise ValueError(f"城市缺少细分映射: {city_key}")
            segment = city_segments[city_key]
            key = (
                row["metric_name"],
                row["inferred_variable_id"],
                row["unit"],
                segment["city_segment_v1"],
            )
            item = grouped[key]
            item["segment_rank"] = segment["segment_rank"]
            item["segment_confidence"] = segment["segment_confidence"]
            item["city_tiers"].add(segment["city_tier_v1"])
            item["years"].add(row["year"])
            item["cities"].add(city_key)
            item["record_count"] += 1
            if row["value_status"] == "missing":
                item["missing_count"] += 1
            else:
                item["observed_count"] += 1
            if segment["needs_manual_review"] == "yes":
                item["manual_review_cities"].add(row["city_normalized"])

    rows: list[dict[str, str]] = []
    for (metric_name, variable_id, unit, city_segment), item in sorted(
        grouped.items(),
        key=lambda pair: (int(pair[1]["segment_rank"]), pair[0][0]),
    ):
        years = sorted(item["years"])
        cities = sorted(item["cities"])
        manual_review_cities = sorted(item["manual_review_cities"])
        record_count = int(item["record_count"])
        observed_count = int(item["observed_count"])
        missing_count = int(item["missing_count"])
        missing_rate = missing_count / record_count if record_count else 0.0

        notes: list[str] = []
        if missing_count:
            notes.append("存在缺失值")
        if manual_review_cities:
            notes.append("包含需人工核查城市")
        if float(missing_rate) > 0.10:
            notes.append("缺失率超过10%")

        rows.append(
            {
                "metric_name": metric_name,
                "inferred_variable_id": variable_id,
                "unit": unit,
                "city_segment_v1": city_segment,
                "segment_rank": str(item["segment_rank"]),
                "segment_confidence": str(item["segment_confidence"]),
                "city_tier_v1": ";".join(sorted(item["city_tiers"])),
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
                "coverage_grade": coverage_grade(missing_rate, len(cities), len(years)),
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
    parser.add_argument("--segment-seed", type=Path, default=DEFAULT_SEGMENT_SEED, help="城市细分种子表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出摘要 CSV 路径")
    args = parser.parse_args()

    rows = build_summary(args.input.resolve(), args.segment_seed.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
