#!/usr/bin/env python3
"""核对已购地级市房地产指标的城市覆盖差异。"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    REPO_ROOT
    / "data"
    / "raw"
    / "purchased"
    / "prefecture-real-estate-indicators-2000-2024"
)
DEFAULT_OUTPUT = REPO_ROOT / "data" / "prefecture-city-coverage-audit.csv"
INSPECT_SCRIPT = REPO_ROOT / "src" / "inspect_purchased_spreadsheets.py"
ZERO_WIDTH_CHARS = "\u200b\u200c\u200d\ufeff"
PROVINCE_NAMES = {
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "西藏",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
}


FIELDNAMES = [
    "normalized_city",
    "raw_city_variants",
    "province_variants",
    "workbook_count",
    "workbooks_present",
    "workbooks_missing",
    "has_zero_width_chars",
    "notes",
]


def load_inspect_module():
    spec = importlib.util.spec_from_file_location("inspect_purchased_spreadsheets", INSPECT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {INSPECT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def clean_text(value: str) -> str:
    text = value.strip()
    for ch in ZERO_WIDTH_CHARS:
        text = text.replace(ch, "")
    return text.strip()


def normalize_city(value: str) -> str:
    text = clean_text(value)
    if text.startswith("(DC)"):
        text = text.removeprefix("(DC)")
    return text[:-1] if text.endswith("市") and len(text) > 2 else text


def has_zero_width(value: str) -> bool:
    return any(ch in value for ch in ZERO_WIDTH_CHARS)


def find_column(header: list[str], candidates: list[str]) -> int | None:
    for candidate in candidates:
        if candidate in header:
            return header.index(candidate)
    return None


def city_from_label(label: str) -> str:
    parts = [clean_text(part) for part in label.split(":") if clean_text(part)]
    return parts[-1] if len(parts) >= 2 else ""


def choose_city(raw_city: str, label: str) -> str:
    city = normalize_city(raw_city)
    if city in PROVINCE_NAMES:
        label_city = normalize_city(city_from_label(label))
        if label_city and label_city not in PROVINCE_NAMES:
            return label_city
    return city


def parse_workbook(path: Path, inspect_mod) -> tuple[str, list[dict[str, str]]]:
    with ZipFile(path) as zf:
        shared_strings = inspect_mod.read_shared_strings(zf)
        sheet = inspect_mod.read_sheets(zf)[0]
        rows = inspect_mod.read_rows(zf, sheet.path, shared_strings)
        header_idx, header, _year_cols, _years = inspect_mod.detect_header(rows)
        data_rows = [row for row in rows[header_idx + 1 :] if inspect_mod.is_data_row(row)]
        first_label = next((row[0] for row in data_rows if row and row[0]), "")
        metric = inspect_mod.infer_metric(path.name, sheet.name, first_label)

    city_col = find_column(header, ["城市", "次国家"])
    province_col = find_column(header, ["省份", "区域"])
    if city_col is None:
        raise ValueError(f"cannot find city column in {path.name}")

    records: list[dict[str, str]] = []
    for row in data_rows:
        raw_city = row[city_col] if len(row) > city_col else ""
        label = row[0] if row else ""
        city = choose_city(raw_city, label)
        if not city:
            continue
        province = row[province_col] if province_col is not None and len(row) > province_col else ""
        records.append(
            {
                "metric": metric,
                "raw_city": raw_city,
                "normalized_city": city,
                "province": clean_text(province),
                "has_zero_width_chars": "yes" if has_zero_width(raw_city) else "no",
            }
        )

    return metric, records


def build_rows(input_dir: Path) -> list[dict[str, str]]:
    inspect_mod = load_inspect_module()
    workbooks = sorted(input_dir.glob("*.xlsx"))
    metrics: list[str] = []
    coverage: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))

    for workbook in workbooks:
        metric, records = parse_workbook(workbook, inspect_mod)
        metrics.append(metric)
        for record in records:
            coverage[record["normalized_city"]][metric].append(record)

    rows: list[dict[str, str]] = []
    all_metrics = sorted(set(metrics))
    for city in sorted(coverage):
        present = sorted(coverage[city])
        missing = [metric for metric in all_metrics if metric not in coverage[city]]
        raw_variants = sorted({r["raw_city"] for records in coverage[city].values() for r in records})
        province_variants = sorted({r["province"] for records in coverage[city].values() for r in records if r["province"]})
        zero_width = any(
            r["has_zero_width_chars"] == "yes" for records in coverage[city].values() for r in records
        )

        notes: list[str] = []
        if missing:
            notes.append("不是所有工作簿都覆盖")
        if len(raw_variants) > 1:
            notes.append("原始城市名存在多个写法")
        if zero_width:
            notes.append("原始城市名包含不可见字符")

        rows.append(
            {
                "normalized_city": city,
                "raw_city_variants": ";".join(raw_variants),
                "province_variants": ";".join(province_variants),
                "workbook_count": str(len(present)),
                "workbooks_present": ";".join(present),
                "workbooks_missing": ";".join(missing),
                "has_zero_width_chars": "yes" if zero_width else "no",
                "notes": "；".join(notes),
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
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="待核对的 Excel 目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 CSV 路径")
    args = parser.parse_args()

    rows = build_rows(args.input.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
