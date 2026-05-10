#!/usr/bin/env python3
"""从城市覆盖核对表生成项目城市主键表。"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "prefecture-city-coverage-audit.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "city-registry.csv"

MUNICIPALITIES = {"北京", "天津", "上海", "重庆"}
KNOWN_ADMIN_NOTES = {
    "巢湖": ("historical_adjustment", "原地级巢湖市已撤销，需按年份和口径决定是否并入合肥、芜湖、马鞍山等后续区划。"),
    "莱芜": ("historical_adjustment", "原莱芜市已并入济南，跨年份分析需单独处理。"),
    "那曲": ("coverage_gap", "缺商品房销售额和住宅销售额，需核对统计口径和数据可得性。"),
    "哈密": ("name_normalization", "原始数据存在零宽字符，已规范化为哈密。"),
}
KNOWN_PROVINCES = {
    "巢湖": "安徽",
    "莱芜": "山东",
}

FIELDNAMES = [
    "city_key",
    "city_name",
    "province",
    "raw_city_variants",
    "province_variants",
    "city_level",
    "workbook_count",
    "coverage_status",
    "workbooks_missing",
    "has_zero_width_chars",
    "admin_status",
    "needs_manual_review",
    "review_reason",
    "notes",
]


def stable_key(city_name: str, province: str) -> str:
    base = f"{province}:{city_name}" if province else city_name
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:8]
    return f"cn_city_{digest}"


def choose_province(row: dict[str, str]) -> str:
    variants = [item for item in row["province_variants"].split(";") if item and item != "中国"]
    if row["normalized_city"] in MUNICIPALITIES:
        return row["normalized_city"]
    if row["normalized_city"] in KNOWN_PROVINCES:
        return KNOWN_PROVINCES[row["normalized_city"]]
    return variants[0] if variants else ""


def city_level(city_name: str) -> str:
    return "直辖市" if city_name in MUNICIPALITIES else "地级市"


def coverage_status(row: dict[str, str]) -> str:
    return "complete" if row["workbook_count"] == "7" else "partial"


def review_fields(row: dict[str, str], admin_status: str, admin_note: str) -> tuple[str, str]:
    reasons: list[str] = []
    if row["workbook_count"] != "7":
        reasons.append("工作簿覆盖不完整")
    if row["has_zero_width_chars"] == "yes":
        reasons.append("原始城市名含不可见字符")
    if admin_status != "normal":
        reasons.append(admin_note)
    return ("yes" if reasons else "no", "；".join(reasons))


def build_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as f:
        coverage_rows = list(csv.DictReader(f))

    rows: list[dict[str, str]] = []
    for row in coverage_rows:
        city_name = row["normalized_city"]
        province = choose_province(row)
        admin_status, admin_note = KNOWN_ADMIN_NOTES.get(city_name, ("normal", ""))
        needs_review, review_reason = review_fields(row, admin_status, admin_note)

        rows.append(
            {
                "city_key": stable_key(city_name, province),
                "city_name": city_name,
                "province": province,
                "raw_city_variants": row["raw_city_variants"],
                "province_variants": row["province_variants"],
                "city_level": city_level(city_name),
                "workbook_count": row["workbook_count"],
                "coverage_status": coverage_status(row),
                "workbooks_missing": row["workbooks_missing"],
                "has_zero_width_chars": row["has_zero_width_chars"],
                "admin_status": admin_status,
                "needs_manual_review": needs_review,
                "review_reason": review_reason,
                "notes": row["notes"],
            }
        )

    return sorted(rows, key=lambda item: (item["province"], item["city_name"], item["city_key"]))


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="城市覆盖核对表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出城市主键表")
    args = parser.parse_args()

    rows = build_rows(args.input.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
