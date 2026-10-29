# 结构化数据说明

本目录存放可被表格/脚本复用的结构化基准数据。所有价格均为 **2026年10月深圳市场参考区间**，不是报价承诺。

## `spec-tiers.csv`

四档婚礼规格的边界条件。

| 字段 | 含义 |
|---|---|
| `tier` | 档位中文名 |
| `code` | S1–S4 |
| `guests` | 建议宾客人数区间 |
| `tables` | 建议桌数区间（10人/桌） |
| `table_price_low/high` | 每桌餐标参考区间（元/桌） |
| `budget_low/high_wan` | 婚礼执行预算区间（万元，不含婚房/购车/彩礼） |
| `venue` | 场地类型 |
| `planning` | 婚策/统筹模式 |
| `best_for` | 适合家庭 |
| `risk` | 主要风险 |

## `cost-benchmarks-2026.csv`

费用基准。`economy/quality/high/flagship` 对应经济/品质/高端/旗舰四档。

| 字段 | 含义 |
|---|---|
| `category` | 费用大类 |
| `item` | 费用项 |
| `economy/quality/high/flagship` | 四档参考值 |
| `unit` | 单位（元、元/桌、比例） |
| `note` | 口径说明 |
| `source` | 来源/依据 |

> 部分行的“旗舰”值为该档位的**起点**（如婚策 30 万），不是上限；正文中以“30–80万+”表述。

## `timeline.csv`

T-12 到 T+30 的任务清单。

| 字段 | 含义 |
|---|---|
| `phase` | 阶段 |
| `window` | 时间窗口 |
| `task` | 任务 |
| `owner` | 主责人 |
| `output` | 交付物 |
| `gate` | 对应决策门（G1–G6） |

## 使用建议

- 用 `spec-tiers.csv` 做档位选择/预算初筛。
- 用 `cost-benchmarks-2026.csv` 填充预算表，但必须用实际书面报价替换。
- 用 `timeline.csv` 导入飞书/Notion/Excel，生成项目任务。
- 修改数据后，同步更新 `docs/03-预算模型与费用基准.md` 与 `docs/04-筹备时间线与责任分工.md`。
