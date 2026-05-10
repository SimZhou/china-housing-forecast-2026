# Agent 工作准则

本文件只面向 AI agent，不作为对外说明文档。给人阅读的项目介绍写在 `README.md`，研究细节写在 `docs/` 和 `reports/`。

## 语言与风格

- 文档、注释、报告草稿优先使用中文。
- 增量更新要合并到已有结构中，不写流水账，不追加会话记录。
- 结论必须克制：没有数据或来源支撑时，只能写假设、待验证问题或研究计划。

## 命令与工具

- Shell 命令默认加 `rtk` 前缀，例如 `rtk git status`、`rtk npm run build`。
- `rtk` 不支持的复杂命令可直接使用原生命令，例如带复杂谓词的 `find`。
- 涉及库、框架、SDK、API、CLI 或云服务文档时，先按上级指令使用 `ctx7` 获取当前文档。

## 研究红线

- 不把国家统计局、地方统计或任何单一机构数据当作事实本身；必须记录口径、偏差可能和交叉验证方式。
- 不引用社交媒体帖子、媒体观点、专家发言作为核心证据；这类材料只能用于发现问题或生成待验证假设。
- 使用论文、国际机构报告、政府数据、交易平台数据时，必须记录来源、发布时间、获取日期、指标口径和时间范围。
- 不做“全国均值直接推出所有城市”的结论；涉及价格判断时优先区分城市层级、区域、住房类型和新房/二手房。
- 不做“城市均值直接推出具体房产”的结论；单套房判断必须补充地段、楼龄、户型、租金、成交流动性和持有成本。
- 不把国际经验机械套用到中国；只能比较变量和约束条件。
- 不只用经济变量解释房价；社会文化、代际价值观、婚育观念、家庭责任和个人生活方式变化也要进入候选解释变量。
- 预测目标包括宏观长期方向、城市和地段分化、单套房价格方向、买房与租房比较；新增模型或报告前先对照 `docs/prediction-targets.md` 和 `data/model-target-registry.csv`。

## 数据约定

- `data/raw/` 保存原始数据归档，不手工改写。
- `data/processed/` 保存清洗后的中间数据，需能由代码或 notebook 复现。
- `data/source-registry.csv` 是候选数据源登记表；新增数据源前先补来源、口径、可信度、偏差风险和下一步动作。
- `data/variable-registry.csv` 是变量登记表；变量进入报告、模型或前端前，必须先登记定义、代理指标、适用城市层级和混杂因素。
- `data/model-target-registry.csv` 是预测目标登记表；模型输出、报告结论和前端页面不得超出已登记目标的粒度。
- `data/property-feature-registry.csv` 是单套房特征登记表；单套房模型输入必须先在此登记，不得临时拼字段。
- `data/purchased-data-inventory.csv` 由 `src/inventory_purchased_data.py` 生成；购买数据目录变化后先重新生成清单，再提交元数据。
- `data/purchased-field-registry.csv` 由 `src/inspect_purchased_spreadsheets.py` 生成；字段清单只记录结构和质量指标，不提交原始数据。
- `data/prefecture-city-coverage-audit.csv` 由 `src/audit_prefecture_city_coverage.py` 生成；只记录城市覆盖差异，不包含原始数值。
- `data/city-registry.csv` 由 `src/build_city_registry.py` 生成；跨数据源 join 优先使用 `city_key`，不要直接用中文城市名。
- `data/city-tier-seed-v1.csv` 由 `src/build_city_tier_seed.py` 生成；这是人工规则种子，不是最终城市分层，建模前必须用人口、产业、库存、成交和租金数据校正。
- `data/city-segment-seed-v1.csv` 由 `src/build_city_segment_seed.py` 生成；这是城市细分人工规则种子，重点拆分三四线，不是最终分组。
- `data/prefecture-housing-quality-summary.csv` 由 `src/summarize_prefecture_housing_data.py` 基于 ignored 本地长表生成；只允许包含聚合质量指标。
- `data/prefecture-housing-tier-coverage-summary.csv` 由 `src/summarize_prefecture_housing_by_tier.py` 生成；只允许包含按城市层级聚合的覆盖质量指标，不得包含逐城市逐年数值。
- `data/prefecture-housing-segment-coverage-summary.csv` 由 `src/summarize_prefecture_housing_by_segment.py` 生成；只允许包含按城市细分组聚合的覆盖质量指标，不得包含逐城市逐年数值。
- `src/build_prefecture_housing_tier_trends.py` 生成的趋势 CSV 包含购买数据衍生聚合数值，必须保存在 ignored 路径；SVG 图表可提交到 `reports/figures/purchased/`，用于报告展示。
- `reports/prefecture-housing-tier-peak-drawdown.md` 由 `src/build_prefecture_housing_tier_peak_report.py` 基于本地趋势 CSV 生成；这是报告材料，可以提交，但不得写成预测结论。
- `src/normalize_prefecture_housing_data.py` 生成的长表写入 `data/processed/`，属于购买数据衍生数值数据，不得提交。
- `data/raw/purchased/*/` 只提交 `DATA_SOURCE.md`；购买数据原文件不得入 Git，也不得公开转载。
- 大文件、付费数据、不可再分发数据不要提交到 Git；只提交获取方式、字段说明和处理脚本。
- 数据处理代码应保留输入、输出、口径转换和缺失值处理说明。

## 目录职责

- `docs/`：方法论、数据源、变量定义、技术方案。
- `reports/`：调研报告、文章草稿、图表结论。
- `notebooks/`：探索性分析，不承载长期稳定逻辑。
- `src/`：可复用的数据抓取、清洗、建模和评估代码。
- `web/`：后续前端展示页，展示预测值、真实值、误差和数据来源。
- `docs/variable-taxonomy.md`、`docs/evidence-protocol.md`、`docs/city-tier-framework.md`、`docs/prediction-targets.md` 是第一阶段研究底座，扩展研究范围时优先更新这些文件。
- `docs/data-ingestion-plan.md` 是第二阶段数据接入计划，新增数据接入脚本或清单时同步更新。

## 输出要求

- 每个关键判断至少包含：数据源、时间范围、核心假设、反证可能、不确定性。
- 预测页面或报告中出现的指标，必须能追溯到原始来源或生成脚本。
- 预测值与真实值比较时，要明确真实值来源和发布日期，不能混用不同口径。

## Git 约定

- 提交前检查 `git status --short`，只提交与当前任务相关的文件。
- 不提交 `.env`、本地缓存、原始大数据和临时下载文件。
- 不回滚用户已有改动；如果发现无关改动，保持原样。
