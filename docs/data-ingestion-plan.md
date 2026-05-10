# 数据接入计划

本文件定义第二阶段的数据接入顺序。目标不是马上建模，而是把本地数据和公开数据变成可审计、可复现、可交叉验证的资产。

## 当前优先级

1. 盘点本地购买数据：确认文件数量、类型、大小、所属数据源和 Git 策略。
2. 建立目录级元数据：每个购买数据目录保留 `DATA_SOURCE.md`，原始数据继续留在本地。
3. 做字段级验真：抽样读取 Excel、压缩包和年鉴文件，记录表名、年份、城市口径、单位和缺失情况。
4. 和外部来源交叉验证：优先对比统计年鉴、地方统计局、国家统计局和平台数据。
5. 生成清洗后数据：只把可复现的脚本和小型元数据提交到 Git，大型中间数据继续忽略。

## 购买数据接入规则

- `data/purchased-data-inventory.csv` 由 `src/inventory_purchased_data.py` 生成，只记录元数据，不包含原始数据内容。
- `data/raw/purchased/*/DATA_SOURCE.md` 是目录说明文件，可以提交。
- 除 `DATA_SOURCE.md` 外，`data/raw/purchased/` 下的文件不得提交。
- 含线性插值或 ARIMA 填补的数据，必须在后续字段清单里标注原始值和填补值。

## 第二阶段产物

- 数据资产清单：`data/purchased-data-inventory.csv`。
- 数据接入脚本：`src/inventory_purchased_data.py`。
- 字段级清单：后续新增 `data/purchased-field-registry.csv`。
- 质量检查报告：后续新增 `reports/data-quality-notes.md`。

## 验收标准

- 任何进入分析的数据源，都能追溯到 `source-registry.csv`。
- 任何进入模型或报告的变量，都能追溯到 `variable-registry.csv`。
- 购买数据必须先通过文件级盘点，再进入字段级验真。
- 所有原始购买文件保持 ignored，不进入 Git。
