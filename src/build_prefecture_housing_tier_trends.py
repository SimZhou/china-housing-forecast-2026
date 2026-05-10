#!/usr/bin/env python3
"""生成按城市层级聚合的本地探索性趋势数据和 SVG 图表。

趋势 CSV 属于购买数据衍生数值材料，写入 ignored 路径；SVG 图表可提交用于报告展示。
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
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
DEFAULT_OUTPUT = REPO_ROOT / "data" / "processed" / "purchased" / "prefecture-housing-tier-trends.csv"
DEFAULT_FIGURE_DIR = REPO_ROOT / "reports" / "figures" / "purchased" / "prefecture-housing-tier-trends"

TIER_ORDER = ["一线", "新一线与强二线", "普通二线", "三四线"]
TIER_COLORS = {
    "一线": "#1f77b4",
    "新一线与强二线": "#2ca02c",
    "普通二线": "#ff7f0e",
    "三四线": "#d62728",
}
PLOT_LEFT = 84
PLOT_RIGHT = 32
PLOT_TOP = 48
PLOT_BOTTOM = 112
SOURCE_REFERENCE = "来源登记：SRC_CN_PURCHASED_PREF_RE_INDICATORS；数据：购买数据-地级市房地产指标2000-2024"
SOURCE_NOTE_REFERENCE = "数据说明：data/raw/purchased/prefecture-real-estate-indicators-2000-2024/DATA_SOURCE.md"
SCRIPT_REFERENCE = "生成脚本：src/build_prefecture_housing_tier_trends.py；城市层级：data/city-tier-seed-v1.csv"
METRIC_SLUGS = {
    "地级市房价": "prefecture_price",
    "商品房销售额": "commercial_housing_sales_value",
    "商品房销售面积": "commercial_housing_sales_area",
    "住宅销售额": "residential_sales_value",
    "住宅销售面积": "residential_sales_area",
    "房地产开发投资额": "real_estate_development_investment",
    "住宅开发投资额": "residential_development_investment",
}

FIELDNAMES = [
    "metric_name",
    "inferred_variable_id",
    "unit",
    "city_tier_v1",
    "tier_rank",
    "year",
    "city_count",
    "observed_city_count",
    "missing_city_count",
    "coverage_rate",
    "mean_value",
    "median_value",
    "sum_value",
    "aggregation_notes",
]


def load_city_tiers(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        tiers = {row["city_key"]: row for row in csv.DictReader(f)}
    if not tiers:
        raise ValueError(f"城市层级种子表为空: {path}")
    return tiers


def parse_value(row: dict[str, str]) -> float | None:
    if row["value_status"] == "missing" or not row["value"]:
        return None
    return float(row["value"])


def format_number(value: float | None) -> str:
    if value is None or math.isnan(value):
        return ""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def build_rows(input_path: Path, tier_seed_path: Path) -> list[dict[str, str]]:
    city_tiers = load_city_tiers(tier_seed_path)
    grouped: dict[tuple[str, str, str, str, str], dict[str, object]] = defaultdict(
        lambda: {
            "tier_rank": "",
            "cities": set(),
            "observed_cities": set(),
            "values": [],
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
                row["year"],
            )
            item = grouped[key]
            item["tier_rank"] = tier["tier_rank"]
            item["cities"].add(city_key)

            value = parse_value(row)
            if value is not None:
                item["observed_cities"].add(city_key)
                item["values"].append(value)

    rows: list[dict[str, str]] = []
    for (metric_name, variable_id, unit, city_tier, year), item in sorted(
        grouped.items(),
        key=lambda pair: (pair[0][0], int(pair[0][4]), int(pair[1]["tier_rank"])),
    ):
        cities = item["cities"]
        observed_cities = item["observed_cities"]
        values = item["values"]
        city_count = len(cities)
        observed_city_count = len(observed_cities)
        missing_city_count = city_count - observed_city_count
        coverage_rate = observed_city_count / city_count if city_count else 0.0
        mean_value = statistics.fmean(values) if values else None
        median_value = statistics.median(values) if values else None
        sum_value = None if metric_name == "地级市房价" else sum(values) if values else None
        aggregation_notes = "房价指标只看均值和中位数，不计算城市求和" if metric_name == "地级市房价" else "非房价指标包含观测城市求和"

        rows.append(
            {
                "metric_name": metric_name,
                "inferred_variable_id": variable_id,
                "unit": unit,
                "city_tier_v1": city_tier,
                "tier_rank": str(item["tier_rank"]),
                "year": year,
                "city_count": str(city_count),
                "observed_city_count": str(observed_city_count),
                "missing_city_count": str(missing_city_count),
                "coverage_rate": f"{coverage_rate:.4f}",
                "mean_value": format_number(mean_value),
                "median_value": format_number(median_value),
                "sum_value": format_number(sum_value),
                "aggregation_notes": f"{aggregation_notes}；购买数据衍生聚合趋势，仅用于本地探索，不提交 Git",
            }
        )

    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def points_for_series(
    series: list[tuple[int, float]],
    width: int,
    height: int,
    min_year: int,
    max_year: int,
    min_value: float,
    max_value: float,
) -> str:
    year_span = max(max_year - min_year, 1)
    value_span = max(max_value - min_value, 1.0)

    plot_width = width - PLOT_LEFT - PLOT_RIGHT
    plot_height = height - PLOT_TOP - PLOT_BOTTOM

    points: list[str] = []
    for year, value in series:
        x = PLOT_LEFT + ((year - min_year) / year_span) * plot_width
        y = PLOT_TOP + (1 - (value - min_value) / value_span) * plot_height
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def year_ticks(min_year: int, max_year: int) -> list[int]:
    ticks = {min_year, max_year}
    for year in range(((min_year + 4) // 5) * 5, max_year + 1, 5):
        ticks.add(year)
    return sorted(ticks)


def value_ticks(min_value: float, max_value: float, count: int = 5) -> list[float]:
    if count <= 1 or max_value == min_value:
        return [min_value]
    step = (max_value - min_value) / (count - 1)
    return [min_value + step * index for index in range(count)]


def scale_x(year: int, min_year: int, max_year: int, width: int) -> float:
    year_span = max(max_year - min_year, 1)
    return PLOT_LEFT + ((year - min_year) / year_span) * (width - PLOT_LEFT - PLOT_RIGHT)


def scale_y(value: float, min_value: float, max_value: float, height: int) -> float:
    value_span = max(max_value - min_value, 1.0)
    return PLOT_TOP + (1 - (value - min_value) / value_span) * (height - PLOT_TOP - PLOT_BOTTOM)


def render_svg(metric_name: str, unit: str, rows: list[dict[str, str]], output_path: Path) -> None:
    width, height = 960, 640
    metric_rows = [row for row in rows if row["metric_name"] == metric_name and row["mean_value"]]
    series_by_tier: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for row in metric_rows:
        series_by_tier[row["city_tier_v1"]].append((int(row["year"]), float(row["mean_value"])))

    all_points = [point for series in series_by_tier.values() for point in series]
    years = [year for year, _ in all_points]
    values = [value for _, value in all_points]
    min_year, max_year = min(years), max(years)
    min_value, max_value = min(values), max(values)

    title = f"{metric_name}：按城市层级的均值趋势"
    axis_bottom = height - PLOT_BOTTOM
    axis_right = width - PLOT_RIGHT
    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{PLOT_LEFT}" y="30" font-size="20" font-family="Arial, sans-serif">{title}</text>',
        f'<text x="{PLOT_LEFT}" y="552" font-size="13" font-family="Arial, sans-serif">单位：{unit}；数值为购买数据衍生均值，仅本地探索使用</text>',
        f'<text x="{PLOT_LEFT}" y="574" font-size="12" font-family="Arial, sans-serif">{SOURCE_REFERENCE}</text>',
        f'<text x="{PLOT_LEFT}" y="596" font-size="12" font-family="Arial, sans-serif">{SOURCE_NOTE_REFERENCE}</text>',
        f'<text x="{PLOT_LEFT}" y="618" font-size="12" font-family="Arial, sans-serif">{SCRIPT_REFERENCE}</text>',
        f'<line x1="{PLOT_LEFT}" y1="{axis_bottom}" x2="{axis_right}" y2="{axis_bottom}" stroke="#999" stroke-width="1"/>',
        f'<line x1="{PLOT_LEFT}" y1="{PLOT_TOP}" x2="{PLOT_LEFT}" y2="{axis_bottom}" stroke="#999" stroke-width="1"/>',
    ]

    for year in year_ticks(min_year, max_year):
        x = scale_x(year, min_year, max_year, width)
        lines.append(f'<line x1="{x:.1f}" y1="{PLOT_TOP}" x2="{x:.1f}" y2="{axis_bottom}" stroke="#e5e7eb" stroke-width="1"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{axis_bottom}" x2="{x:.1f}" y2="{axis_bottom + 5}" stroke="#777" stroke-width="1"/>')
        lines.append(f'<text x="{x:.1f}" y="{axis_bottom + 22}" text-anchor="middle" font-size="12" font-family="Arial, sans-serif">{year}</text>')

    for value in value_ticks(min_value, max_value):
        y = scale_y(value, min_value, max_value, height)
        lines.append(f'<line x1="{PLOT_LEFT}" y1="{y:.1f}" x2="{axis_right}" y2="{y:.1f}" stroke="#eef0f3" stroke-width="1"/>')
        lines.append(f'<text x="{PLOT_LEFT - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="12" font-family="Arial, sans-serif">{value:.0f}</text>')

    legend_x = 720
    legend_y = 64
    for index, tier in enumerate(TIER_ORDER):
        series = sorted(series_by_tier.get(tier, []))
        if len(series) < 2:
            continue
        color = TIER_COLORS[tier]
        points = points_for_series(series, width, height, min_year, max_year, min_value, max_value)
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{points}"/>')
        y = legend_y + index * 24
        lines.append(f'<line x1="{legend_x}" y1="{y - 5}" x2="{legend_x + 28}" y2="{y - 5}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text x="{legend_x + 36}" y="{y}" font-size="14" font-family="Arial, sans-serif">{tier}</text>')

    lines.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_figures(rows: list[dict[str, str]], output_dir: Path) -> int:
    metrics = sorted({(row["metric_name"], row["unit"]) for row in rows})
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for metric_name, unit in metrics:
        slug = METRIC_SLUGS.get(metric_name, metric_name)
        render_svg(metric_name, unit, rows, output_dir / f"{slug}.svg")
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="本地长表路径")
    parser.add_argument("--tier-seed", type=Path, default=DEFAULT_TIER_SEED, help="城市层级种子表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出趋势 CSV 路径")
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR, help="输出 SVG 图表目录")
    args = parser.parse_args()

    rows = build_rows(args.input.resolve(), args.tier_seed.resolve())
    write_csv(rows, args.output.resolve())
    figure_count = write_figures(rows, args.figure_dir.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    print(f"wrote {figure_count} SVG files to {args.figure_dir.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
