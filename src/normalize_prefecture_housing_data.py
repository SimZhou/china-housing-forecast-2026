#!/usr/bin/env python3
"""把已购地级市房地产指标宽表转换为本地长表。

输出文件属于购买数据的衍生数据，默认写入 `data/processed/`，不提交到 Git。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from decimal import Decimal, InvalidOperation
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
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "purchased"
    / "prefecture-real-estate-indicators-long.csv"
)
DEFAULT_CITY_REGISTRY = REPO_ROOT / "data" / "city-registry.csv"
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
    "dataset_id",
    "source_registry_id",
    "source_file",
    "sheet_name",
    "metric_name",
    "inferred_variable_id",
    "province",
    "city_key",
    "city_raw",
    "city_normalized",
    "unit",
    "data_source",
    "frequency",
    "year",
    "value",
    "value_status",
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


def parse_decimal(value: str) -> str:
    if value == "":
        return ""
    try:
        return str(Decimal(value))
    except InvalidOperation:
        return value


def find_column(header: list[str], candidates: list[str]) -> int | None:
    for candidate in candidates:
        if candidate in header:
            return header.index(candidate)
    return None


def load_city_registry(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    registry = {row["city_name"]: row["city_key"] for row in rows}
    if not registry:
        raise ValueError(f"empty city registry: {path}")
    return registry


def city_from_label(label: str) -> str:
    parts = [clean_text(part) for part in label.split(":") if clean_text(part)]
    return parts[-1] if len(parts) >= 2 else ""


def choose_city(raw_city: str, label: str) -> tuple[str, str]:
    city = normalize_city(raw_city)
    if city in PROVINCE_NAMES:
        label_city = normalize_city(city_from_label(label))
        if label_city and label_city not in PROVINCE_NAMES:
            return label_city, f"城市列疑似省级名称，已从原始指标列恢复城市：{label_city}"
    return city, ""


def read_workbook(path: Path, inspect_mod, city_registry: dict[str, str]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []

    with ZipFile(path) as zf:
        shared_strings = inspect_mod.read_shared_strings(zf)
        sheet = inspect_mod.read_sheets(zf)[0]
        rows = inspect_mod.read_rows(zf, sheet.path, shared_strings)
        header_idx, header, year_cols, years = inspect_mod.detect_header(rows)
        data_rows = [row for row in rows[header_idx + 1 :] if inspect_mod.is_data_row(row)]
        first_label = next((row[0] for row in data_rows if row and row[0]), "")
        metric = inspect_mod.infer_metric(path.name, sheet.name, first_label)
        unit = inspect_mod.detect_unit(header, data_rows, sheet.name)
        variable_id = inspect_mod.infer_variable_id(metric)

    city_col = find_column(header, ["城市", "次国家"])
    province_col = find_column(header, ["省份", "区域"])
    unit_col = find_column(header, ["单位"])
    source_col = find_column(header, ["数据来源"])
    frequency_col = find_column(header, ["频率"])
    label_col = 0

    if city_col is None:
        raise ValueError(f"cannot find city column in {path.name}")

    for row in data_rows:
        city_raw = row[city_col] if len(row) > city_col else ""
        city_normalized = normalize_city(city_raw)
        if not city_normalized:
            continue
        province = row[province_col] if province_col is not None and len(row) > province_col else ""
        row_unit = row[unit_col] if unit_col is not None and len(row) > unit_col and row[unit_col] else unit
        data_source = row[source_col] if source_col is not None and len(row) > source_col else ""
        frequency = row[frequency_col] if frequency_col is not None and len(row) > frequency_col else ""
        label = row[label_col] if len(row) > label_col else ""
        city_normalized, city_note = choose_city(city_raw, label)
        city_key = city_registry.get(city_normalized)
        if city_key is None:
            raise ValueError(f"city not found in registry: {city_normalized} ({path.name})")

        for year_col, year in zip(year_cols, years):
            raw_value = row[year_col] if len(row) > year_col else ""
            output_rows.append(
                {
                    "dataset_id": inspect_mod.DATASET_ID,
                    "source_registry_id": inspect_mod.SOURCE_REGISTRY_ID,
                    "source_file": path.name,
                    "sheet_name": sheet.name,
                    "metric_name": metric,
                    "inferred_variable_id": variable_id,
                    "province": clean_text(province),
                    "city_key": city_key,
                    "city_raw": city_raw,
                    "city_normalized": city_normalized,
                    "unit": clean_text(row_unit),
                    "data_source": clean_text(data_source),
                    "frequency": clean_text(frequency),
                    "year": year,
                    "value": parse_decimal(raw_value),
                    "value_status": "missing" if raw_value == "" else "observed",
                    "notes": "；".join(
                        item
                        for item in [
                            "本地购买数据衍生长表，不提交 Git",
                            city_note,
                            f"原始指标列：{label}" if label else "",
                        ]
                        if item
                    ),
                }
            )

    return output_rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="待转换的 Excel 目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 CSV 路径")
    parser.add_argument("--city-registry", type=Path, default=DEFAULT_CITY_REGISTRY, help="城市主键表")
    args = parser.parse_args()

    inspect_mod = load_inspect_module()
    city_registry = load_city_registry(args.city_registry.resolve())
    rows: list[dict[str, str]] = []
    files = sorted(args.input.resolve().glob("*.xlsx"))
    if not files:
        raise SystemExit(f"no xlsx files found in {args.input}")
    for file_path in files:
        rows.extend(read_workbook(file_path, inspect_mod, city_registry))

    write_csv(rows, args.output.resolve())
    print(f"converted {len(files)} workbooks, wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
