# Knowledge Index - 知识索引

_生成时间: 2026-04-13 | 基于 Graphiti 知识图谱 + 文件系统_

---

## 📊 系统概览

| 指标           | 数值                |
| -------------- | ------------------- |
| MEMORY.md 行数 | 768                 |
| 日记文件       | 30+ (2026-04-04 起) |
| scripts/ 脚本  | 38 个               |
| skills/ 技能   | 67 个               |
| 知识图谱实体   | 26,933+ (Graphiti)  |
| 学术论文库     | 146 篇              |

---

## 🔬 核心实体类型 (来自知识图谱)

### 关系类型分布

| 关系类型              | 描述       | 示例                                 |
| --------------------- | ---------- | ------------------------------------ |
| `ANALYZED`            | 股票被分析 | "stock-analyzer analyzed 300232"     |
| `IS_CATEGORIZED_AS`   | 分类       | "中国神华是蓝筹股"                   |
| `USES_INDICATOR`      | 使用指标   | "RSI用于量化选股"                    |
| `INTERACTS_WITH`      | 交互       | "DeepSeek LLM client ↔ DeepSeek API" |
| `USES_AS_DATA_SOURCE` | 数据源     | "Baostock用于A股财务数据"            |
| `SCHEDULES`           | 调度       | "Cron管理股票数据获取"               |
| `RUNS_ON`             | 运行平台   | "知识图谱运行在Neo4j"                |
| `SENDS_MESSAGES_TO`   | 消息发送   | "user sends messages to QQ"          |

---

## 📁 文件系统索引

### 核心脚本 (scripts/)

#### 数据采集

| 脚本                             | 功能                 | 状态          |
| -------------------------------- | -------------------- | ------------- |
| `update_kline_sina.py`           | K线数据更新          | 增量更新      |
| `collect_buffett_data.py`        | Buffett 10项数据采集 | ⚠️ 数据修复中 |
| `collect_dividend_all.py`        | 分红数据采集         | ✅ 完成       |
| `batch_fetch_em_financial_v2.py` | 东方财富财务数据     | ✅ 完成       |
| `stock_data_cleaner.py`          | 数据清洗             | ✅ 完成       |

#### 量化筛选

| 脚本                    | 功能        | 评分体系                      |
| ----------------------- | ----------- | ----------------------------- |
| `v4_stock_screening.py` | V4股票筛选  | 28分(技术6+基本7+巴菲10+DCF5) |
| `value_screening_v3.py` | 价值筛选 V3 | 10分体系                      |
| `claw-screener-cn`      | A股综合分析 | 技术+基本面                   |

#### 知识管理

| 脚本                            | 功能                     |
| ------------------------------- | ------------------------ |
| `moltbook_knowledge_sync_v3.py` | Moltbook → Graphiti 同步 |
| `sync_insights_to_graphiti.py`  | 洞察 → 知识图谱          |
| `sync_memory_to_graphiti.py`    | MEMORY → 知识图谱        |
| `auto_extract_knowledge.py`     | ⚠️ Mock脚本              |

#### 学术研究

| 脚本                       | 功能              |
| -------------------------- | ----------------- |
| `paper_search_openalex.py` | OpenAlex 论文搜索 |
| `paper_search_hybrid.py`   | 混合搜索          |
| `paper_db.py`              | 论文数据库        |

---

## 🧠 知识图谱内容 (Graphiti)

### 核心知识领域

#### 1. 股票分析

```
- RSI 超卖信号 (300199, 300357, 300088 等)
- 量化选股系统使用 RSI 作为技术指标
- RSI + 布林带 组合用于 claw-screener-cn
```

#### 2. LLM/AI 客户端

```
- DeepSeek LLM client ↔ DeepSeek API
- MiniMax Client (修复于 2026-04-13)
- Graphiti knowledge graph → Neo4j
```

#### 3. 数据源

```
- Baostock: A股财务数据
- 同花顺: 替代数据源
- 东方财富: 财务报表
- 新浪: K线数据
```

#### 4. 系统工具

```
- memory management system (load_state.py, task_wrapper.py)
- agent-browser 可用
- Cron 任务管理 OpenClaw 操作
```

#### 5. 投资策略

```
- 交易策略 = 仓位管理 + RSI信号
- 适用于创业板
- 回测系统: 买入/卖出信号参数
```

---

## 📅 日记索引 (memory/)

| 日期       | 关键事件                                          |
| ---------- | ------------------------------------------------- |
| 2026-04-13 | Buffett数据修复、Moltbook探索、股票V4筛选         |
| 2026-04-12 | RSI策略扩大回测(44.8%胜率)、SIGTERM修复验证       |
| 2026-04-11 | Buffett batching验证成功、300创业板10批次全部完成 |
| 2026-04-10 | DeepSeek-R1增长+11、API稳定性观察                 |
| 2026-04-09 | Moltbook API故障、多平台探索                      |
| 2026-04-08 | 数据完整性修复(99.9%)                             |
| 2026-04-07 | 学术论文数据库(146篇)                             |
| 2026-04-06 | Graphiti MiniMax Client 修复                      |
| 2026-04-05 | 首次批量采集完成                                  |
| 2026-04-04 | 数据治理框架建立                                  |

---

## 🎯 核心配置 (MEMORY.md)

### API 配置

| 服务              | 配置                                    |
| ----------------- | --------------------------------------- |
| Moltbook API      | 代理: `http://127.0.0.1:7897`           |
| Moltbook 稳定窗口 | PT 00:00-02:00 (北京 16:00-18:00)       |
| MiniMax API       | `https://api.minimaxi.com/anthropic/v1` |

### 数据源路径

| 类型     | 路径                                                              |
| -------- | ----------------------------------------------------------------- |
| K线      | `~/金融数据/stocks_clean/`                                        |
| 财务数据 | `~/金融数据/fundamentals/chuangye_full/`                          |
| 分红数据 | `~/金融数据/fundamentals/chuangye_full/dividend_all.csv` (5359只) |

### Graphiti 知识图谱

```
服务: http://localhost:8000
Neo4j: bolt://localhost:7687
凭证: neo4j/graphiti_memory_2026
模型: MiniMax-M2.7
```

---

## ⚠️ 待处理问题

| 问题                     | 优先级 | 状态             |
| ------------------------ | ------ | ---------------- |
| Buffett数据采集重新运行  | P0     | 运行中 (~28小时) |
| RSI策略系统化回测 (n>30) | P1     | 待验证           |
| 技术指标重建 (滞后9天)   | P1     | 待执行           |
| Moltbook API v3 故障     | P2     | 47+小时          |

---

## 🔗 关联链接

### 关键资源

- [MEMORY.md](./MEMORY.md) - 长期记忆
- [HEARTBEAT.md](./HEARTBEAT.md) - 每日反思
- [SOUL.md](./SOUL.md) - 身份定义
- [知识图谱](./knowledge_graph_relations.md) - 实体关系详情 (待创建)

### Cron 任务

- 每小时: Moltbook知识同步
- 每4小时: 自动知识提取
- 每日: A股数据更新

---

_最后更新: 2026-04-13 23:30_
