# 电竞选手与战队奖金数据分析（eSports Earnings Analysis）

> 一份基于公开电竞奖金数据集的端到端数据分析项目，覆盖「数据清洗 → 维表关联 → 多维聚合 → 头部集中度分析 → 可视化」完整链路。

## 1. 项目简介（Overview）

本项目对电竞选手与战队的历年赛事奖金进行结构化分析，回答三类问题：

- **谁赚得最多**：选手榜 / 战队榜 Top10 及其所属项目（Game）；
- **奖金的地域分布**：按国家 / 大洲聚合，验证"电竞奖金的地域格局"；
- **奖金是否过度集中**：用 Top1% / Top50 份额量化奖金分布的头部集中与长尾特征。

数据集原始来源为 **eSportsEarnings.com**（经天池数据集转载下载）。本项目从数据分析师视角出发，重点演示**多表 join、聚合统计与分布集中度分析**的方法与可复现工程实践。

## 2. 数据集说明（Data）

数据为三份 CSV，构成「两张事实表 + 一张维表」的星型结构：

| 文件 | 角色 | 规模 | 说明 |
| --- | --- | --- | --- |
| `highest_earning_players.csv` | 事实表 | 1000 行 × 8 列 | 奖金最高的电竞选手 |
| `highest_earning_teams.csv` | 事实表 | 928 行 × 6 列 | 奖金最高的电竞战队 |
| `country-and-continent-codes-list.csv` | 维表 | 262 行 × 6 列 | 国家 ↔ 大洲编码映射 |

覆盖的游戏包括：Dota 2、Counter-Strike: Global Offensive、Fortnite、League of Legends、Starcraft II、Overwatch、PUBG、Hearthstone、Heroes of the Storm、Arena of Valor。

### 2.1 字段字典

**highest_earning_players.csv（选手表）**

| 字段 | 含义 |
| --- | --- |
| `PlayerId` | 选手唯一 ID |
| `NameFirst` / `NameLast` | 名 / 姓 |
| `CurrentHandle` | 选手 ID / 比赛昵称（如 N0tail、dupreeh），优先作为展示名 |
| `CountryCode` | 两位国家码（如 dk、cn），用于与维表关联 |
| `TotalUSDPrize` | 累计奖金（美元） |
| `Game` | 所属游戏项目 |
| `Genre` | 游戏类型 |

**highest_earning_teams.csv（战队表）**

| 字段 | 含义 |
| --- | --- |
| `TeamId` | 战队唯一 ID |
| `TeamName` | 战队名称 |
| `TotalUSDPrize` | 战队累计奖金（美元） |
| `TotalTournaments` | 参赛数 |
| `Game` / `Genre` | 所属游戏 / 游戏类型 |

> ⚠️ 注意：**战队表本身不含国家字段**，因此国家 / 大洲维度的分析仅基于选手表，战队表只用于榜单与合计统计。

**country-and-continent-codes-list.csv（维表）**

| 字段 | 含义 |
| --- | --- |
| `Continent_Name` / `Continent_Code` | 大洲名称 / 编码 |
| `Country_Name` | 国家名称 |
| `Two_Letter_Country_Code` | 两位国家码，**与选手表 `CountryCode` 关联的关联键** |
| `Three_Letter_Country_Code` / `Country_Number` | 三位国家码 / 数字国家码 |

## 3. 技术栈（Tech Stack）

- **Python 3.11**
- **pandas**：数据清洗、join、聚合
- **matplotlib**：可视化
- 纯脚本实现，无数据库依赖，可在原始 CSV 上直接重跑复现全部指标

## 4. 分析方法（Methodology）

1. **数据清洗**：统一选手 `CountryCode` 为大写并去除空白；选手展示名取 `CurrentHandle`，缺失时回退「名 + 姓」；奖金字段转数值并剔除非正数。
2. **维表关联（join）**：以选手 `CountryCode` 关联维表 `Two_Letter_Country_Code`，补齐国家名与大洲名，关联匹配率 100%。
3. **多维聚合**：分别按选手、战队、国家、大洲聚合累计奖金与占比。
4. **集中度分析**：对选手奖金降序排列，计算 **Top1%** 与 **Top50** 的奖金份额，刻画分布的头部集中与长尾特征。
5. **可视化**：输出 Top10 选手榜、Top10 战队榜、国家奖金 Top、大洲占比 4 张图表。

## 5. 核心结论（Key Findings）

> 以下结论基于上述真实数据集实测。

- **数据规模**：1000 名选手 + 928 支战队，选手与战队累计奖金约 **8.99 亿美元**（≈ $898,837,420）。
- **大洲分布（选手奖金）**：**亚洲 42.6% > 欧洲 39.3% > 北美 14.3%**，亚洲（受中国、韩国电竞奖金拉动）反超欧洲，与"电竞 = 欧洲主导"的常见直觉相反。
- **国家维度**：**中国以约 7,239 万美元**居选手奖金首位（≈ $72,391,879），其后为韩国、美国、丹麦、瑞典。
- **头部集中度**：**奖金前 1% 选手占 13.3%、Top50 选手占 35.0%**，奖金呈明显的幂律 / 长尾分布——少数头部选手占据绝大部分奖金。
- **个人榜首**：Dota 2 选手 **N0tail ≈ 695 万美元**；**战队榜首**：**OG ≈ 3,381 万美元**。

## 6. 项目结构（Project Structure）

```
esports-earnings-analysis/
├── README.md                          # 本说明文档
├── esports_earnings_analysis.py       # 分析脚本
├── data/                              # 三份原始 CSV（自行放入）
│   ├── highest_earning_players.csv
│   ├── highest_earning_teams.csv
│   └── country-and-continent-codes-list.csv
└── output_charts/                     # 脚本生成的 4 张图表
```

## 7. 快速开始（Getting Started）

**环境依赖**

```bash
pip install pandas matplotlib
```

**运行**

将三份 CSV 放入与脚本同目录（或脚本读取的 `data/` 目录）后执行：

```bash
python esports_earnings_analysis.py
```

脚本会在控制台打印关键指标（来源、规模、合计奖金、大洲分布、Top 国家、Top1% / Top50 份额），并将 4 张图表输出到 `output_charts/`。

## 8. 复现说明（Reproducibility）

脚本对原始 CSV 直接计算，不写死任何结果数值；只要在相同数据集上重跑即可复现第 5 节全部指标。图表与指标均由代码产出，可逐行追溯计算口径（如 Top1% 为「奖金降序后前 1% 选手的奖金之和 ÷ 选手总奖金」）。

## 9. 致谢（Acknowledgements）

数据来源：[eSportsEarnings.com](https://esportsearnings.com)（经天池数据集转载）。本项目仅用于数据分析方法学习与求职作品展示。

---

内容由 AI 生成
