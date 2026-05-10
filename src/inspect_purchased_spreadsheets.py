#!/usr/bin/env python3
"""抽取已购地级市房地产 Excel 的字段级元数据。"""

from __future__ import annotations

import argparse
import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, timedelta
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
DEFAULT_OUTPUT = REPO_ROOT / "data" / "purchased-field-registry.csv"

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

DATASET_ID = "prefecture-real-estate-indicators-2000-2024"
SOURCE_REGISTRY_ID = "SRC_CN_PURCHASED_PREF_RE_INDICATORS"

VARIABLE_BY_KEYWORD = [
    ("房价", "VAR_PRICE_NEW"),
    ("住宅销售面积", "VAR_VOLUME_TRANSACTION"),
    ("住宅销售额", "VAR_VOLUME_TRANSACTION"),
    ("商品房销售面积", "VAR_VOLUME_TRANSACTION"),
    ("商品房销售额", "VAR_VOLUME_TRANSACTION"),
    ("住宅开发投资额", "VAR_CONSTRUCTION"),
    ("房地产开发投资额", "VAR_CONSTRUCTION"),
]

FIELDNAMES = [
    "dataset_id",
    "source_registry_id",
    "relative_path",
    "file_name",
    "sheet_name",
    "field_name",
    "field_role",
    "inferred_variable_id",
    "metric_name",
    "city_granularity",
    "unit",
    "year_start",
    "year_end",
    "year_count",
    "row_count",
    "column_count",
    "header_row",
    "data_start_row",
    "observed_cell_count",
    "missing_cell_count",
    "missing_rate",
    "source_columns",
    "fill_method_risk",
    "notes",
]


@dataclass(frozen=True)
class SheetRef:
    name: str
    path: str


def col_to_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + ord(ch.upper()) - 64
    return idx - 1


def excel_serial_to_year(value: str) -> str | None:
    if not re.fullmatch(r"\d+(?:\.0)?", value):
        return None
    number = int(float(value))
    if 1900 <= number <= 2100:
        return str(number)
    if 30000 <= number <= 50000:
        return str((date(1899, 12, 30) + timedelta(days=number)).year)
    return None


def normalize_text(value: str) -> str:
    return value.strip().replace("\n", " ")


def read_shared_strings(zf: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("a:si", NS):
        parts = [node.text or "" for node in item.findall(".//a:t", NS)]
        strings.append("".join(parts))
    return strings


def read_sheets(zf: ZipFile) -> list[SheetRef]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    sheets: list[SheetRef] = []

    for sheet in workbook.findall("a:sheets/a:sheet", NS):
        rel_id = sheet.attrib[f"{{{NS['r']}}}id"]
        target = relmap[rel_id]
        path = target if target.startswith("xl/") else f"xl/{target}"
        sheets.append(SheetRef(sheet.attrib["name"], path))

    return sheets


def read_rows(zf: ZipFile, sheet_path: str, shared_strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(zf.read(sheet_path))
    rows: list[list[str]] = []

    for row in root.findall("a:sheetData/a:row", NS):
        values: list[str] = []
        for cell in row.findall("a:c", NS):
            cell_ref = cell.attrib.get("r", "A1")
            col_idx = col_to_index(cell_ref)
            while len(values) <= col_idx:
                values.append("")

            value = ""
            value_node = cell.find("a:v", NS)
            if value_node is not None and value_node.text is not None:
                value = value_node.text
                if cell.attrib.get("t") == "s":
                    value = shared_strings[int(value)]
            elif cell.attrib.get("t") == "inlineStr":
                texts = [node.text or "" for node in cell.findall(".//a:t", NS)]
                value = "".join(texts)
            values[col_idx] = normalize_text(value)
        rows.append(values)

    return rows


def detect_header(rows: list[list[str]]) -> tuple[int, list[str], list[int], list[str]]:
    for idx, row in enumerate(rows[:20]):
        years = [excel_serial_to_year(value) for value in row]
        year_cols = [col for col, year in enumerate(years) if year is not None]
        if len(year_cols) >= 3:
            return idx, row, year_cols, [years[col] or "" for col in year_cols]
    raise ValueError("cannot detect header row with year columns")


def infer_metric(file_name: str, sheet_name: str, first_label: str) -> str:
    name = file_name.removesuffix(".xlsx")
    for suffix in ["（截至2025.12.29更新）"]:
        name = name.replace(suffix, "")
    if "房价数据" in name:
        return "地级市房价"
    for token in ["商品房销售额", "商品房销售面积", "住宅销售额", "住宅销售面积", "住宅开发投资额", "房地产开发投资额"]:
        if token in name:
            return token
    if first_label:
        return first_label.split(":")[0]
    return sheet_name


def infer_variable_id(metric_name: str) -> str:
    for keyword, variable_id in VARIABLE_BY_KEYWORD:
        if keyword in metric_name:
            return variable_id
    return "UNMAPPED"


def detect_unit(header: list[str], data_rows: list[list[str]], sheet_name: str) -> str:
    for col_name in ["单位", "unit"]:
        if col_name in header:
            col = header.index(col_name)
            values = [row[col] for row in data_rows if len(row) > col and row[col]]
            if values:
                return values[0]
    if "元每平方米" in sheet_name:
        return "元/平方米"
    return "待确认"


def detect_city_granularity(header: list[str]) -> str:
    names = set(header)
    if {"省份", "城市"} <= names:
        return "地级市;省份"
    if "城市" in names or "次国家" in names:
        return "地级市"
    return "待确认"


def non_empty_count(rows: list[list[str]], cols: list[int]) -> tuple[int, int]:
    observed = 0
    missing = 0
    for row in rows:
        for col in cols:
            value = row[col] if len(row) > col else ""
            if value == "":
                missing += 1
            else:
                observed += 1
    return observed, missing


def fixed_columns(header: list[str], year_cols: list[int]) -> list[str]:
    year_set = set(year_cols)
    return [value or f"column_{idx + 1}" for idx, value in enumerate(header) if idx not in year_set]


def is_data_row(row: list[str]) -> bool:
    return any(value != "" for value in row)


def inspect_workbook(path: Path) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []

    with ZipFile(path) as zf:
        shared_strings = read_shared_strings(zf)
        for sheet in read_sheets(zf):
            rows = read_rows(zf, sheet.path, shared_strings)
            if not rows:
                continue

            header_idx, header, year_cols, years = detect_header(rows)
            data_rows = [row for row in rows[header_idx + 1 :] if is_data_row(row)]
            first_label = next((row[0] for row in data_rows if row and row[0]), "")
            metric = infer_metric(path.name, sheet.name, first_label)
            unit = detect_unit(header, data_rows, sheet.name)
            observed, missing = non_empty_count(data_rows, year_cols)
            total = observed + missing
            missing_rate = missing / total if total else 0.0
            year_start = min(years)
            year_end = max(years)
            row_count = len(data_rows)
            column_count = max((len(row) for row in rows), default=0)
            source_cols = fixed_columns(header, year_cols)

            rows_out.append(
                {
                    "dataset_id": DATASET_ID,
                    "source_registry_id": SOURCE_REGISTRY_ID,
                    "relative_path": path.relative_to(REPO_ROOT).as_posix(),
                    "file_name": path.name,
                    "sheet_name": sheet.name,
                    "field_name": "annual_value_columns",
                    "field_role": "wide_year_values",
                    "inferred_variable_id": infer_variable_id(metric),
                    "metric_name": metric,
                    "city_granularity": detect_city_granularity(header),
                    "unit": unit,
                    "year_start": year_start,
                    "year_end": year_end,
                    "year_count": str(len(years)),
                    "row_count": str(row_count),
                    "column_count": str(column_count),
                    "header_row": str(header_idx + 1),
                    "data_start_row": str(header_idx + 2),
                    "observed_cell_count": str(observed),
                    "missing_cell_count": str(missing),
                    "missing_rate": f"{missing_rate:.4f}",
                    "source_columns": ";".join(source_cols),
                    "fill_method_risk": "未发现显式填补标记",
                    "notes": "宽表年份列；年份表头可能来自 Excel 日期序列号，脚本已转为年份",
                }
            )

            for col_name in source_cols:
                rows_out.append(
                    {
                        "dataset_id": DATASET_ID,
                        "source_registry_id": SOURCE_REGISTRY_ID,
                        "relative_path": path.relative_to(REPO_ROOT).as_posix(),
                        "file_name": path.name,
                        "sheet_name": sheet.name,
                        "field_name": col_name,
                        "field_role": "metadata_column",
                        "inferred_variable_id": "NOT_APPLICABLE",
                        "metric_name": metric,
                        "city_granularity": detect_city_granularity(header),
                        "unit": unit,
                        "year_start": year_start,
                        "year_end": year_end,
                        "year_count": str(len(years)),
                        "row_count": str(row_count),
                        "column_count": str(column_count),
                        "header_row": str(header_idx + 1),
                        "data_start_row": str(header_idx + 2),
                        "observed_cell_count": "",
                        "missing_cell_count": "",
                        "missing_rate": "",
                        "source_columns": col_name,
                        "fill_method_risk": "不适用",
                        "notes": "元数据列，用于城市、单位、来源或频率识别",
                    }
                )

    return rows_out


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="待检查的 Excel 目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 CSV 路径")
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_path = args.output.resolve()
    files = sorted(input_dir.glob("*.xlsx"))
    if not files:
        raise SystemExit(f"no xlsx files found in {input_dir}")

    rows: list[dict[str, str]] = []
    for file_path in files:
        rows.extend(inspect_workbook(file_path))

    write_csv(rows, output_path)
    print(f"inspected {len(files)} workbooks, wrote {len(rows)} rows to {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
