#!/usr/bin/env python3
"""生成已购地级市房地产长表的可提交聚合质量摘要。"""

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
DEFAULT_CITY_REGISTRY = REPO_ROOT / "data" / "city-registry.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "prefecture-housing-quality-summary.csv"

FIELDNAMES = [
    "metric_name",
    "inferred_variable_id",
    "unit",
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
    "coverage_notes",
]


def load_manual_review_cities(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as f:
        return {row["city_key"] for row in csv.DictReader(f) if row["needs_manual_review"] == "yes"}


def build_summary(input_path: Path, city_registry_path: Path) -> list[dict[str, str]]:
    manual_review_city_keys = load_manual_review_cities(city_registry_path)
    grouped: dict[tuple[str, str, str], dict[str, object]] = defaultdict(
        lambda: {
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
            key = (row["metric_name"], row["inferred_variable_id"], row["unit"])
            item = grouped[key]
            item["years"].add(row["year"])
            item["cities"].add(row["city_key"])
            item["record_count"] += 1
            if row["value_status"] == "missing":
                item["missing_count"] += 1
            else:
                item["observed_count"] += 1
            if row["city_key"] in manual_review_city_keys:
                item["manual_review_cities"].add(row["city_normalized"])

    rows: list[dict[str, str]] = []
    for (metric_name, variable_id, unit), item in sorted(grouped.items()):
        years = sorted(item["years"])
        cities = sorted(item["cities"])
        manual_cities = sorted(item["manual_review_cities"])
        record_count = int(item["record_count"])
        missing_count = int(item["missing_count"])
        observed_count = int(item["observed_count"])
        missing_rate = missing_count / record_count if record_count else 0.0

        notes: list[str] = []
        if manual_cities:
            notes.append("包含需人工核查城市")
        if missing_count:
            notes.append("存在缺失值")

        rows.append(
            {
                "metric_name": metric_name,
                "inferred_variable_id": variable_id,
                "unit": unit,
                "year_start": years[0],
                "year_end": years[-1],
                "year_count": str(len(years)),
                "city_count": str(len(cities)),
                "record_count": str(record_count),
                "observed_count": str(observed_count),
                "missing_count": str(missing_count),
                "missing_rate": f"{missing_rate:.4f}",
                "manual_review_city_count": str(len(manual_cities)),
                "manual_review_cities": ";".join(manual_cities),
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
    parser.add_argument("--city-registry", type=Path, default=DEFAULT_CITY_REGISTRY, help="城市主键表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出摘要 CSV 路径")
    args = parser.parse_args()

    rows = build_summary(args.input.resolve(), args.city_registry.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
