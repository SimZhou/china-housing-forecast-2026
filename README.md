# 2026 年后中国房价走势研究

本仓库用于调研、建模和展示 2026 年之后中国房价走势。研究目标不是复述单一统计口径或社交媒体观点，而是从人口、收入、就业、信贷、土地、库存、迁徙、租金收益率、社会文化变化、国际经验等变量出发，建立可复核的数据链和判断框架。

最终目标是回答两类问题：在房价已大幅下跌、并可能阶段性企稳的情景下，远期房价是会回暖、横盘还是继续下跌；对任意给定城市、区域和房屋属性，是否值得购买，还是更适合租房。

## 研究原则

1. 遵从第一性原理，优先分析影响房价的直接和间接因素。
2. 不把单一官方数据源当作事实本身，国家统计局数据仅作为参考口径之一。
3. 尽量使用可交叉验证的数据：出生人口、就业、工资、居民杠杆、地方财政、土地成交、库存、租金、迁徙、搜索指数等。
4. 纳入代际价值观、婚育观念、家庭责任和个人生活方式变化，避免只用经济变量解释房价。
5. 对照其他国家和地区的历史房地产周期，提取可比较变量，而不是机械类比结论。
6. 所有关键结论必须保留来源、口径、更新时间和不确定性说明。

## 目录

```text
.
├── data/
│   ├── raw/             # 原始数据，仅做归档，不直接手工修改
│   ├── processed/       # 清洗后的中间数据
│   ├── source-registry.csv
│   └── variable-registry.csv
├── docs/                # 研究方法、数据源、变量定义
├── notebooks/           # 探索性分析
├── reports/             # 调研报告、文章草稿和图表输出
├── src/                 # 数据抓取、清洗、建模代码
└── web/                 # 后续前端展示页面
```

## 当前阶段

- 已完成研究框架、变量体系、预测目标和本地购买数据第一轮结构化。
- 正在核对地级市房地产指标的低覆盖组合、城市细分有效性和 2024 年缺失原因。
- 下一步优先接入中国城市数据库 v202603 的人口、就业、收入、财政和产业变量，用于验证成交回撤是否有基本面支撑。

## 第一阶段成果

- `docs/variable-taxonomy.md`：房价相关变量体系。
- `docs/evidence-protocol.md`：证据分级、偏差处理和反证要求。
- `docs/city-tier-framework.md`：城市层级研究框架。
- `docs/prediction-targets.md`：宏观、城市地段和单套房决策的预测目标。
- `data/source-registry.csv`：候选数据源、口径、可信度和下一步动作。
- `data/variable-registry.csv`：候选变量、代理指标、适用城市层级和混杂因素。
- `data/model-target-registry.csv`：模型预测目标、最小粒度、输入和评估方式。
- `data/property-feature-registry.csv`：单套房决策所需的位置、房屋、流动性、租金和买方约束特征。
- `data/purchased-data-inventory.csv`：本地购买数据文件级元数据清单，不含原始数据内容。

## 第二阶段成果

- `docs/data-ingestion-plan.md`：数据接入顺序、购买数据接入规则和验收标准。
- `src/inventory_purchased_data.py`：扫描 `data/raw/purchased/` 并生成购买数据元数据清单。
- `src/inspect_purchased_spreadsheets.py`：检查已购地级市房地产 Excel 的 sheet、字段、年份、单位和缺失率。
- `src/audit_prefecture_city_coverage.py`：核对地级市房地产指标 7 个 Excel 的城市覆盖差异。
- `src/normalize_prefecture_housing_data.py`：把 7 个宽表转换为本地长表，输出到 ignored 的 `data/processed/`。
- `src/build_city_registry.py`：从城市覆盖核对表生成稳定城市主键表。
- `src/summarize_prefecture_housing_data.py`：基于本地长表生成可提交的聚合质量摘要。
- `src/build_city_tier_seed.py`：基于城市主键表生成第一版城市层级种子表。
- `src/build_city_segment_seed.py`：在城市层级之上生成第一版城市细分种子表。
- `src/summarize_prefecture_housing_by_tier.py`：基于本地长表和城市层级种子表生成分层覆盖质量摘要。
- `src/summarize_prefecture_housing_by_segment.py`：基于本地长表和城市细分种子表生成细分覆盖质量摘要。
- `src/build_prefecture_housing_tier_trends.py`：生成本地探索性趋势 CSV 和可提交的 SVG 图表。
- `src/build_prefecture_housing_tier_peak_report.py`：基于本地趋势 CSV 生成峰值回撤观察报告。
- `src/build_prefecture_housing_segment_trends.py`：生成城市细分组趋势 CSV 和可提交的 SVG 图表。
- `src/build_prefecture_housing_segment_peak_report.py`：基于城市细分趋势 CSV 生成峰值回撤观察报告。
- `data/purchased-data-inventory.csv`：记录购买数据的文件名、大小、类型、来源登记 ID 和 Git 策略。
- `data/purchased-field-registry.csv`：地级市房地产指标 7 个 Excel 的字段级清单。
- `data/prefecture-city-coverage-audit.csv`：城市覆盖核对表，不含原始数值。
- `data/city-registry.csv`：项目城市主键表，后续跨数据源 join 应优先使用 `city_key`。
- `data/city-tier-seed-v1.csv`：第一版城市层级种子表，覆盖 298 个城市，后续需用数据校正。
- `data/city-segment-seed-v1.csv`：第一版城市细分种子表，重点拆分三四线城市。
- `data/prefecture-housing-quality-summary.csv`：地级市房地产指标的聚合质量摘要，不含逐城市逐年数值。
- `data/prefecture-housing-tier-coverage-summary.csv`：按城市层级拆分的地级市房地产指标覆盖质量摘要。
- `data/prefecture-housing-segment-coverage-summary.csv`：按城市细分组拆分的地级市房地产指标覆盖质量摘要。
- `reports/data-quality-notes.md`：购买数据第一版质量检查笔记。
- `reports/prefecture-housing-tier-trend-observations.md`：分层趋势图和方向性观察。
- `reports/prefecture-housing-tier-peak-drawdown.md`：分层峰值年份、回撤幅度和覆盖率摘要。
- `reports/prefecture-housing-segment-trend-observations.md`：城市细分趋势图和三四线内部差异观察。
- `reports/prefecture-housing-segment-peak-drawdown.md`：城市细分峰值年份、回撤幅度和覆盖率摘要。

本地可生成 `data/processed/purchased/prefecture-housing-tier-trends.csv`、`data/processed/purchased/prefecture-housing-segment-trends.csv` 和 `reports/figures/purchased/` 下的趋势图。趋势 CSV 保持 ignored；SVG 图表可提交，用于报告展示。

## 本地购买数据

仓库本地保存了三份购买数据，放在 `data/raw/purchased/` 下：地级市房地产指标 2000-2024、中国房地产统计年鉴 1999-2025、中国城市数据库 v202603。原始文件不提交到 Git，也不公开共享；每个目录只提交 `DATA_SOURCE.md` 说明来源和使用限制。

这些数据可作为相对可信候选来源纳入分析，但不能作为唯一证据。使用时需要核对来源、缺失值、单位、口径、城市编码和插值或预测填补方法，并与公开年鉴、地方统计局、平台数据或其他来源交叉验证。

## 初始问题

- 中国住宅价格是否仍可由收入、人口和信贷扩张解释，还是已经进入资产负债表收缩主导阶段？
- 如果后续数据确认 2026 年出现阶段性企稳，这是否代表长期回暖，还是只是成交和价格下跌后的短期平台？
- 不同城市层级之间的分化是否会超过全国均值本身的解释力？
- 同一城市内核心地段与非核心地段的分化，是否会超过城市之间的分化？
- 给定一套房的城市、地段、价格、租金和房屋属性后，买入是否优于租赁？
- 与日本、韩国、美国、欧洲部分国家的房地产周期相比，中国更接近哪类路径，差异变量是什么？
- 哪些非房价数据能更早反映价格压力，例如租金、挂牌量、成交周期、土地溢价率、搜索热度、招聘与迁徙数据？
- 代际价值观、婚育观念、家庭责任和个人生活方式变化，会怎样改变住房需求、购房优先级和承债意愿？
