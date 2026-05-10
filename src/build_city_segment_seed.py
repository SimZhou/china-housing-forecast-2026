#!/usr/bin/env python3
"""生成第一版城市细分种子表。

这张表在 city_tier_v1 之上增加 city_segment_v1，重点拆分三四线城市。
它是人工规则种子，不是最终分组；后续必须用人口、产业、库存、成交和租金数据校正。
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "city-tier-seed-v1.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "city-segment-seed-v1.csv"

METRO_PERIPHERY_CANDIDATES = {
    # 京津冀
    "廊坊",
    "沧州",
    "秦皇岛",
    "张家口",
    "承德",
    # 长三角
    "湖州",
    "镇江",
    "泰州",
    "盐城",
    "淮安",
    "舟山",
    # 珠三角及粤港澳外围
    "江门",
    "肇庆",
    "清远",
    "汕头",
    # 成渝
    "德阳",
    "眉山",
    "资阳",
    "遂宁",
    "广安",
    "泸州",
    # 武汉都市圈
    "鄂州",
    "黄石",
    "孝感",
    "咸宁",
    "黄冈",
    # 长株潭及周边
    "湘潭",
    "岳阳",
    "益阳",
    # 中原城市群
    "开封",
    "新乡",
    "许昌",
    "焦作",
    "平顶山",
    # 关中平原
    "渭南",
    "宝鸡",
    # 海峡西岸
    "漳州",
    "莆田",
}

FIELDNAMES = [
    "city_key",
    "city_name",
    "province",
    "city_tier_v1",
    "tier_rank",
    "city_segment_v1",
    "segment_rank",
    "segment_basis",
    "segment_confidence",
    "special_city_type",
    "needs_manual_review",
    "review_reason",
    "notes",
]


def segment_city(row: dict[str, str]) -> dict[str, str]:
    city = row["city_name"]
    city_tier = row["city_tier_v1"]
    special_type = row["special_city_type"]
    notes = "第一版人工规则种子，后续需用人口、产业、库存、成交、租金和通勤数据校正"

    if city_tier == "一线":
        segment = "一线核心城市"
        rank = "1"
        basis = "继承主层级：一线城市"
        confidence = "high"
    elif city_tier == "新一线与强二线":
        segment = "新一线与强二线核心城市"
        rank = "2"
        basis = "继承主层级：新一线与强二线"
        confidence = "medium"
    elif city_tier == "普通二线":
        segment = "普通二线与区域中心城市"
        rank = "3"
        basis = "继承主层级：普通二线或区域中心候选"
        confidence = "low"
    elif row["needs_manual_review"] == "yes" and special_type != "资源型或收缩型候选":
        segment = "历史区划或数据异常城市"
        rank = "4"
        basis = "城市主键表或覆盖核对表标记为需人工核查"
        confidence = "medium"
    elif "资源型或收缩型候选" in special_type:
        segment = "资源型或收缩型候选城市"
        rank = "5"
        basis = "城市层级种子表 special_city_type 标记为资源型或收缩型候选"
        confidence = "medium"
    elif city in METRO_PERIPHERY_CANDIDATES:
        segment = "都市圈外围承接型候选城市"
        rank = "6"
        basis = "人工规则种子：位于主要都市圈或城市群外围，可能承接通勤、产业或外溢住房需求"
        confidence = "low"
    else:
        segment = "普通三四线城市"
        rank = "7"
        basis = "默认种子：不在特殊城市、资源收缩候选或都市圈外围候选集合"
        confidence = "low"

    return {
        "city_key": row["city_key"],
        "city_name": city,
        "province": row["province"],
        "city_tier_v1": city_tier,
        "tier_rank": row["tier_rank"],
        "city_segment_v1": segment,
        "segment_rank": rank,
        "segment_basis": basis,
        "segment_confidence": confidence,
        "special_city_type": special_type,
        "needs_manual_review": row["needs_manual_review"],
        "review_reason": row["review_reason"],
        "notes": notes,
    }


def build_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))
    rows = [segment_city(row) for row in source_rows]
    return sorted(rows, key=lambda item: (int(item["segment_rank"]), item["province"], item["city_name"], item["city_key"]))


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="城市层级种子表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出城市细分种子表")
    args = parser.parse_args()

    rows = build_rows(args.input.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
