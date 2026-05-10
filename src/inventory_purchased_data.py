#!/usr/bin/env python3
"""生成本地购买数据的可提交元数据清单。"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "purchased"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "purchased-data-inventory.csv"


@dataclass(frozen=True)
class DatasetInfo:
    source_registry_id: str
    name: str


DATASETS = {
    "prefecture-real-estate-indicators-2000-2024": DatasetInfo(
        "SRC_CN_PURCHASED_PREF_RE_INDICATORS",
        "地级市房地产指标 2000-2024",
    ),
    "china-real-estate-statistical-yearbook-1999-2025": DatasetInfo(
        "SRC_CN_PURCHASED_RE_YEARBOOK",
        "中国房地产统计年鉴 1999-2025",
    ),
    "china-city-database-v202603-2000-2024": DatasetInfo(
        "SRC_CN_PURCHASED_CITY_DB",
        "中国城市数据库 v202603 版 2000-2024",
    ),
}


ROLE_BY_EXT = {
    ".xlsx": "spreadsheet_data",
    ".xls": "spreadsheet_data",
    ".csv": "table_data",
    ".zip": "archive",
    ".rar": "archive",
    ".pdf": "documentation",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".md": "source_note",
}

SKIP_NAMES = {".DS_Store"}


FIELDNAMES = [
    "dataset_id",
    "source_registry_id",
    "dataset_name",
    "relative_path",
    "file_name",
    "extension",
    "role",
    "size_bytes",
    "size_mb",
    "git_policy",
    "notes",
]


def classify(path: Path) -> tuple[str, str]:
    if path.name == "DATA_SOURCE.md":
        return "source_note", "唯一应提交的购买数据目录说明文件"

    role = ROLE_BY_EXT.get(path.suffix.lower(), "unknown")
    if role in {"spreadsheet_data", "table_data", "archive", "documentation", "image"}:
        return role, "原始购买数据或配套材料，不提交到 Git"
    return role, "未知类型，后续接入前需人工确认"


def git_policy(path: Path) -> str:
    return "tracked_metadata" if path.name == "DATA_SOURCE.md" else "ignored_raw_asset"


def build_rows(input_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for dataset_dir in sorted(p for p in input_dir.iterdir() if p.is_dir()):
        info = DATASETS.get(dataset_dir.name, DatasetInfo("UNREGISTERED", dataset_dir.name))

        for file_path in sorted(p for p in dataset_dir.rglob("*") if p.is_file()):
            if file_path.name in SKIP_NAMES:
                continue
            role, notes = classify(file_path)
            size_bytes = file_path.stat().st_size
            rows.append(
                {
                    "dataset_id": dataset_dir.name,
                    "source_registry_id": info.source_registry_id,
                    "dataset_name": info.name,
                    "relative_path": file_path.relative_to(REPO_ROOT).as_posix(),
                    "file_name": file_path.name,
                    "extension": file_path.suffix.lower() or "none",
                    "role": role,
                    "size_bytes": str(size_bytes),
                    "size_mb": f"{size_bytes / 1024 / 1024:.3f}",
                    "git_policy": git_policy(file_path),
                    "notes": notes,
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
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="购买数据目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 CSV 路径")
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_path = args.output.resolve()
    if not input_dir.exists():
        raise SystemExit(f"input directory not found: {input_dir}")

    rows = build_rows(input_dir)
    write_csv(rows, output_path)
    print(f"wrote {len(rows)} rows to {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
