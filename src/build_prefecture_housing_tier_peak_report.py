#!/usr/bin/env python3
"""基于本地分层趋势 CSV 生成峰值回撤观察报告。"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "processed" / "purchased" / "prefecture-housing-tier-trends.csv"
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "prefecture-housing-tier-peak-drawdown.md"

TIER_ORDER = ["一线", "新一线与强二线", "普通二线", "三四线"]
METRIC_ORDER = [
    "地级市房价",
    "商品房销售面积",
    "商品房销售额",
    "住宅销售面积",
    "住宅销售额",
    "房地产开发投资额",
    "住宅开发投资额",
]


def pct(value: float) -> str:
    return f"{value:.1f}%"


def num(value: float) -> str:
    if abs(value) >= 100000:
        return f"{value:,.0f}"
    if abs(value) >= 1000:
        return f"{value:,.1f}"
    return f"{value:.2f}"


def evidence_note(latest_coverage: float, drawdown_pct: float) -> str:
    if latest_coverage < 0.30:
        return "弱证据：末期覆盖率低"
    if latest_coverage < 0.50:
        return "谨慎使用：末期覆盖率偏低"
    if drawdown_pct <= -30:
        return "强回落信号"
    if drawdown_pct <= -10:
        return "中等回落信号"
    if drawdown_pct < 0:
        return "轻微回落"
    return "未见峰值回撤"


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"缺少趋势 CSV，请先运行 src/build_prefecture_housing_tier_trends.py: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        rows = [row for row in csv.DictReader(f) if row["mean_value"]]
    if not rows:
        raise ValueError(f"趋势 CSV 没有可用记录: {path}")
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["metric_name"], row["city_tier_v1"])].append(row)

    summary: dict[tuple[str, str], dict[str, object]] = {}
    for key, series in grouped.items():
        ordered = sorted(series, key=lambda row: int(row["year"]))
        start = ordered[0]
        latest = ordered[-1]
        peak = max(ordered, key=lambda row: float(row["mean_value"]))

        start_value = float(start["mean_value"])
        latest_value = float(latest["mean_value"])
        peak_value = float(peak["mean_value"])
        latest_coverage = float(latest["coverage_rate"])
        change_from_start = (latest_value / start_value - 1) * 100 if start_value else 0.0
        drawdown = (latest_value / peak_value - 1) * 100 if peak_value else 0.0

        summary[key] = {
            "start_year": start["year"],
            "start_value": start_value,
            "peak_year": peak["year"],
            "peak_value": peak_value,
            "latest_year": latest["year"],
            "latest_value": latest_value,
            "change_from_start": change_from_start,
            "drawdown": drawdown,
            "latest_coverage": latest_coverage,
            "unit": latest["unit"],
            "note": evidence_note(latest_coverage, drawdown),
        }
    return summary


def table_for_metric(metric: str, summary: dict[tuple[str, str], dict[str, object]]) -> list[str]:
    lines = [
        f"### {metric}",
        "",
        "| 城市层级 | 起点 | 峰值 | 最新 | 较起点变化 | 较峰值回撤 | 最新覆盖率 | 证据备注 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for tier in TIER_ORDER:
        item = summary.get((metric, tier))
        if not item:
            continue
        unit = item["unit"]
        lines.append(
            "| {tier} | {start_year} {start_value} | {peak_year} {peak_value} | {latest_year} {latest_value} | {change} | {drawdown} | {coverage} | {note} |".format(
                tier=tier,
                start_year=item["start_year"],
                start_value=f"{num(item['start_value'])} {unit}",
                peak_year=item["peak_year"],
                peak_value=f"{num(item['peak_value'])} {unit}",
                latest_year=item["latest_year"],
                latest_value=f"{num(item['latest_value'])} {unit}",
                change=pct(item["change_from_start"]),
                drawdown=pct(item["drawdown"]),
                coverage=pct(item["latest_coverage"] * 100),
                note=item["note"],
            )
        )
    lines.append("")
    return lines


def strongest_drawdowns(summary: dict[tuple[str, str], dict[str, object]]) -> list[tuple[str, str, dict[str, object]]]:
    items = [(metric, tier, item) for (metric, tier), item in summary.items()]
    return sorted(items, key=lambda row: row[2]["drawdown"])[:8]


def build_report(rows: list[dict[str, str]]) -> str:
    summary = summarize(rows)
    lines = [
        "# 地级市房地产指标分层峰值回撤摘要",
        "",
        "本报告由本地趋势 CSV 生成，用于补充趋势图阅读。它只反映购买数据衍生的城市层级均值，不是预测结论。",
        "",
        "生成脚本：`src/build_prefecture_housing_tier_peak_report.py`",
        "",
        "上游趋势脚本：`src/build_prefecture_housing_tier_trends.py`",
        "",
        "本地趋势 CSV：`data/processed/purchased/prefecture-housing-tier-trends.csv`",
        "",
        "## Reference",
        "",
        "- 数据来源：购买数据-地级市房地产指标 2000-2024，见 `data/raw/purchased/prefecture-real-estate-indicators-2000-2024/DATA_SOURCE.md`。",
        "- 来源登记：`data/source-registry.csv` 中的 `SRC_CN_PURCHASED_PREF_RE_INDICATORS`。",
        "- 城市层级：`data/city-tier-seed-v1.csv`。",
        "- 趋势图：`reports/prefecture-housing-tier-trend-observations.md`。",
        "",
        "## 最大回撤组合",
        "",
        "| 指标 | 城市层级 | 峰值年份 | 最新年份 | 较峰值回撤 | 最新覆盖率 | 证据备注 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]

    for metric, tier, item in strongest_drawdowns(summary):
        lines.append(
            f"| {metric} | {tier} | {item['peak_year']} | {item['latest_year']} | {pct(item['drawdown'])} | {pct(item['latest_coverage'] * 100)} | {item['note']} |"
        )

    lines.extend(
        [
            "",
            "## 分指标摘要",
            "",
        ]
    )
    for metric in METRIC_ORDER:
        lines.extend(table_for_metric(metric, summary))

    lines.extend(
        [
            "## 使用限制",
            "",
            "- 当前摘要基于城市层级均值，不能替代单城、板块或小区层面的判断。",
            "- 2024 年部分指标覆盖率偏低，尤其是住宅销售额、住宅开发投资额等指标。",
            "- 城市层级来自第一版人工规则种子表，后续需要用人口、产业、库存、成交和租金数据校正。",
            "- 该摘要只描述历史回撤，不直接预测 2026 年之后的价格方向。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="本地趋势 CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 Markdown 报告")
    args = parser.parse_args()

    rows = load_rows(args.input.resolve())
    report = build_report(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"wrote {args.output.resolve().relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
