# 地级市房地产指标分层趋势观察

本笔记基于本地购买数据生成的城市层级聚合趋势图。它只用于形成待验证观察，不是预测结论，也不能替代后续与统计年鉴、地方统计局、网签、租金和平台成交数据的交叉验证。

生成脚本：`src/build_prefecture_housing_tier_trends.py`

本地趋势 CSV：`data/processed/purchased/prefecture-housing-tier-trends.csv`

图表目录：`reports/figures/purchased/prefecture-housing-tier-trends/`

## 图表索引

- [地级市房价](figures/purchased/prefecture-housing-tier-trends/prefecture_price.svg)
- [商品房销售面积](figures/purchased/prefecture-housing-tier-trends/commercial_housing_sales_area.svg)
- [商品房销售额](figures/purchased/prefecture-housing-tier-trends/commercial_housing_sales_value.svg)
- [住宅销售面积](figures/purchased/prefecture-housing-tier-trends/residential_sales_area.svg)
- [住宅销售额](figures/purchased/prefecture-housing-tier-trends/residential_sales_value.svg)
- [房地产开发投资额](figures/purchased/prefecture-housing-tier-trends/real_estate_development_investment.svg)
- [住宅开发投资额](figures/purchased/prefecture-housing-tier-trends/residential_development_investment.svg)

## 初步观察

### 1. 房价层级差距长期扩大

地级市房价数据覆盖 2000-2022 年。从分层均值看，一线城市价格水平始终显著高于其他层级，新一线与强二线、普通二线、三四线依次降低。

到 2021-2022 年附近，普通二线和三四线的均值已出现从峰值回落的迹象。一线城市 2022 年样本覆盖率只有 75%，因此不能仅凭 2022 年均值判断一线已企稳。

### 2. 销售面积比销售额更早显示压力

商品房销售面积和住宅销售面积在多数城市层级中都已从峰值明显回落。相较销售额，销售面积更接近真实成交量压力，受价格上涨抬高金额的影响较小。

从峰值到 2024 年，商品房销售面积在各层级均出现较大幅度回落。三四线回落更明显，但 2024 年覆盖率仍需结合缺失情况判断。

### 3. 销售额在高层级城市中更容易被价格支撑

销售额同时受成交面积和价格影响。一线城市在 2024 年的销售额均值仍高，但 2024 年一线样本覆盖率只有 50%，不能直接解释为强恢复。

新一线与强二线、普通二线、三四线的销售额从 2020-2021 年附近高点回落更明显，提示成交量和价格共同承压的可能性。

### 4. 开发投资回落集中在非一线层级

房地产开发投资额和住宅开发投资额在新一线与强二线、普通二线、三四线中从 2021 年附近高点明显回落。三四线住宅开发投资额同时存在较高缺失率，相关判断只能作为弱证据。

一线城市投资额 2024 年仍较高，但样本数量小，且 2024 年覆盖率不足，不适合单独推出趋势结论。

### 5. 三四线均值需要拆解

三四线层级包含 227 个城市，并包含全部 24 个需人工复核或特殊标记城市。该层级内部差异很大，均值容易掩盖资源型城市、收缩型城市、都市圈外围城市和普通地级市之间的差异。

后续分析三四线时，应至少拆分：

- 都市圈外围承接型城市。
- 资源型或收缩型城市。
- 人口净流出但财政和产业尚稳定城市。
- 县域需求和棚改后遗留库存压力较大的城市。

## 证据限制

- 图表来自购买数据衍生聚合结果，尚未与公开统计年鉴、地方统计局和平台成交数据逐项交叉验证。
- 2023-2024 年部分指标覆盖率偏低，尤其是住宅销售额、住宅开发投资额等指标。
- 当前城市层级来自人工规则种子表，不是最终分层结果。
- 均值趋势不能替代中位数、分位数和单城趋势；后续需要补充分布视角。
- 图表只做到城市层级，不包含核心与非核心地段差异。

## 下一步

- 对房价、销售面积、销售额和开发投资分别生成峰值年份、峰值回撤和覆盖率摘要。
- 把三四线拆分为资源型或收缩型候选、都市圈外围和普通地级市。
- 抽样核对 2021-2024 年关键城市的销售面积和销售额数据来源。
- 接入人口、收入、就业、租金和库存数据后，检查“价格回落”和“成交萎缩”是否同向。
