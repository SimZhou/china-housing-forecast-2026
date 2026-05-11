# 数据接入计划

本文件定义第二阶段的数据接入顺序。目标不是马上建模，而是把本地数据和公开数据变成可审计、可复现、可交叉验证的资产。

## 当前优先级

1. 回查地级市房地产指标中 2024 年覆盖率低于 50% 的组合，区分真实缺失、口径变化和整理缺失。
2. 抽样对照地方统计局、统计年鉴或平台数据，验证购买数据中的销售面积、销售额和开发投资口径。
3. 为中国城市数据库 v202603 识别原始版、线性插值版和 ARIMA 填补版，避免把填补值当作观测值。
4. 接入人口、就业、收入、财政和产业变量，验证城市层级与城市细分种子表。
5. 补充租金、挂牌、网签或平台成交数据，用于连接城市均值、地段流动性和单套房判断。
6. 继续只提交可复现脚本、小型元数据、报告和 SVG 图表；原始数据和购买数据衍生数值表保持 ignored。

## 购买数据接入规则

- `data/purchased-data-inventory.csv` 由 `src/inventory_purchased_data.py` 生成，只记录元数据，不包含原始数据内容。
- `data/raw/purchased/*/DATA_SOURCE.md` 是目录说明文件，可以提交。
- 除 `DATA_SOURCE.md` 外，`data/raw/purchased/` 下的文件不得提交。
- 含线性插值或 ARIMA 填补的数据，必须在后续字段清单里标注原始值和填补值。

## 第二阶段产物

- 数据资产清单：`data/purchased-data-inventory.csv`。
- 数据接入脚本：`src/inventory_purchased_data.py`。
- 字段级清单：`data/purchased-field-registry.csv`。
- 字段检查脚本：`src/inspect_purchased_spreadsheets.py`。
- 城市覆盖核对表：`data/prefecture-city-coverage-audit.csv`。
- 城市主键表：`data/city-registry.csv`。
- 城市主键脚本：`src/build_city_registry.py`。
- 城市层级种子表：`data/city-tier-seed-v1.csv`。
- 城市层级种子脚本：`src/build_city_tier_seed.py`。
- 城市细分种子表：`data/city-segment-seed-v1.csv`。
- 城市细分种子脚本：`src/build_city_segment_seed.py`。
- 本地长表转换脚本：`src/normalize_prefecture_housing_data.py`。
- 聚合质量摘要：`data/prefecture-housing-quality-summary.csv`。
- 质量摘要脚本：`src/summarize_prefecture_housing_data.py`。
- 城市层级覆盖摘要：`data/prefecture-housing-tier-coverage-summary.csv`。
- 城市层级覆盖摘要脚本：`src/summarize_prefecture_housing_by_tier.py`。
- 城市细分覆盖摘要：`data/prefecture-housing-segment-coverage-summary.csv`。
- 城市细分覆盖摘要脚本：`src/summarize_prefecture_housing_by_segment.py`。
- 本地探索性趋势脚本：`src/build_prefecture_housing_tier_trends.py`。
- 分层峰值回撤报告脚本：`src/build_prefecture_housing_tier_peak_report.py`。
- 城市细分趋势脚本：`src/build_prefecture_housing_segment_trends.py`。
- 城市细分峰值回撤报告脚本：`src/build_prefecture_housing_segment_peak_report.py`。
- 质量检查报告：`reports/data-quality-notes.md`。
- 预测目标登记表：`data/model-target-registry.csv`。
- 单套房特征登记表：`data/property-feature-registry.csv`。

## 验收标准

- 任何进入分析的数据源，都能追溯到 `source-registry.csv`。
- 任何进入模型或报告的变量，都能追溯到 `variable-registry.csv`。
- 任何模型输出，都能追溯到 `model-target-registry.csv`，且不得超过当前数据支持的最小粒度。
- 单套房模型输入必须能追溯到 `property-feature-registry.csv`，并注明来源粒度和缺失处理。
- 购买数据必须先通过文件级盘点，再进入字段级验真。
- 跨数据源合并必须优先使用 `city_key`，中文城市名只能作为展示字段或辅助核对字段。
- 城市层级种子表只能作为初始切片工具，不能作为最终城市分层结论。
- 城市细分种子表只能作为初始切片工具，尤其不能把都市圈外围候选直接当作已被验证的承接城市。
- 购买数据衍生的数值长表只允许保存在 `data/processed/`，不提交到 Git。
- 购买数据衍生的趋势 CSV 只允许保存在 ignored 路径；分层和城市细分 SVG 图表可以提交到 `reports/figures/purchased/` 作为报告展示材料。
- 可提交的质量摘要只能包含指标级或城市层级聚合质量指标，不得包含逐城市逐年原始数值。
- 所有原始购买文件保持 ignored，不进入 Git。
