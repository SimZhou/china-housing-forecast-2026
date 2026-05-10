#!/usr/bin/env python3
"""生成第一版城市层级种子表。

这不是最终城市分层。脚本只给每个 city_key 生成一个可复核的初始层级，
后续应使用人口、产业、收入、库存、成交和租金数据重新校正。
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "city-registry.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "city-tier-seed-v1.csv"

FIRST_TIER = {"北京", "上海", "广州", "深圳"}

NEW_FIRST_OR_STRONG_SECOND = {
    "成都",
    "杭州",
    "重庆",
    "武汉",
    "西安",
    "苏州",
    "南京",
    "天津",
    "郑州",
    "长沙",
    "东莞",
    "佛山",
    "宁波",
    "青岛",
    "合肥",
}

PROVINCIAL_CAPITALS = {
    "石家庄",
    "太原",
    "呼和浩特",
    "沈阳",
    "长春",
    "哈尔滨",
    "济南",
    "南京",
    "杭州",
    "合肥",
    "福州",
    "南昌",
    "郑州",
    "武汉",
    "长沙",
    "广州",
    "南宁",
    "海口",
    "成都",
    "贵阳",
    "昆明",
    "拉萨",
    "西安",
    "兰州",
    "西宁",
    "银川",
    "乌鲁木齐",
}

PLAN_LISTED_OR_SUB_PROVINCIAL = {
    "广州",
    "武汉",
    "哈尔滨",
    "沈阳",
    "成都",
    "南京",
    "西安",
    "长春",
    "济南",
    "杭州",
    "大连",
    "青岛",
    "宁波",
    "厦门",
    "深圳",
}

REGIONAL_SECOND_TIER_CANDIDATES = {
    "无锡",
    "常州",
    "南通",
    "徐州",
    "扬州",
    "温州",
    "绍兴",
    "金华",
    "嘉兴",
    "台州",
    "泉州",
    "珠海",
    "中山",
    "惠州",
    "烟台",
    "潍坊",
    "济宁",
    "临沂",
    "唐山",
    "保定",
    "洛阳",
    "襄阳",
    "宜昌",
    "株洲",
    "绵阳",
    "咸阳",
    "榆林",
    "包头",
    "鄂尔多斯",
    "遵义",
    "桂林",
    "柳州",
}

RESOURCE_OR_SHRINKAGE_CANDIDATES = {
    "七台河",
    "伊春",
    "双鸭山",
    "鸡西",
    "鹤岗",
    "阜新",
    "抚顺",
    "本溪",
    "辽源",
    "白山",
    "白城",
    "大庆",
    "克拉玛依",
    "乌海",
    "阳泉",
    "朔州",
    "铜川",
    "攀枝花",
    "金昌",
    "嘉峪关",
}

FIELDNAMES = [
    "city_key",
    "city_name",
    "province",
    "city_tier_v1",
    "tier_rank",
    "tier_basis",
    "tier_confidence",
    "is_first_tier",
    "is_provincial_capital",
    "is_plan_listed_or_sub_provincial",
    "special_city_type",
    "needs_manual_review",
    "review_reason",
    "notes",
]


def classify_city(row: dict[str, str]) -> dict[str, str]:
    city = row["city_name"]
    notes: list[str] = []

    if city in FIRST_TIER:
        tier = "一线"
        rank = "1"
        basis = "固定种子：北京、上海、广州、深圳"
        confidence = "high"
    elif city in NEW_FIRST_OR_STRONG_SECOND:
        tier = "新一线与强二线"
        rank = "2"
        basis = "固定种子：资源吸附、产业或交易活跃度较强的核心城市"
        confidence = "medium"
    elif (
        city in PROVINCIAL_CAPITALS
        or city in PLAN_LISTED_OR_SUB_PROVINCIAL
        or city in REGIONAL_SECOND_TIER_CANDIDATES
    ):
        tier = "普通二线"
        rank = "3"
        basis = "规则种子：省会、计划单列/副省级城市或区域中心候选"
        confidence = "low"
    else:
        tier = "三四线"
        rank = "4"
        basis = "默认种子：不在核心城市、省会或区域中心候选集合"
        confidence = "low"

    special_types: list[str] = []
    if city in RESOURCE_OR_SHRINKAGE_CANDIDATES:
        special_types.append("资源型或收缩型候选")
        notes.append("资源型或收缩型候选需用人口、产业、财政和成交流动性数据验证")
    if row["admin_status"] != "normal":
        special_types.append(row["admin_status"])
        notes.append(row["review_reason"])
    if row["coverage_status"] != "complete":
        notes.append("购买地级市房地产指标覆盖不完整")

    return {
        "city_key": row["city_key"],
        "city_name": city,
        "province": row["province"],
        "city_tier_v1": tier,
        "tier_rank": rank,
        "tier_basis": basis,
        "tier_confidence": confidence,
        "is_first_tier": "yes" if city in FIRST_TIER else "no",
        "is_provincial_capital": "yes" if city in PROVINCIAL_CAPITALS else "no",
        "is_plan_listed_or_sub_provincial": "yes" if city in PLAN_LISTED_OR_SUB_PROVINCIAL else "no",
        "special_city_type": ";".join(special_types) if special_types else "normal",
        "needs_manual_review": "yes" if special_types or row["needs_manual_review"] == "yes" else "no",
        "review_reason": "；".join(item for item in notes if item),
        "notes": "第一版人工规则种子，后续需用人口、产业、库存、成交和租金数据校正",
    }


def build_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))
    return [classify_city(row) for row in source_rows]


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="城市主键表")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出城市层级种子表")
    args = parser.parse_args()

    rows = build_rows(args.input.resolve())
    write_csv(rows, args.output.resolve())
    print(f"wrote {len(rows)} rows to {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
