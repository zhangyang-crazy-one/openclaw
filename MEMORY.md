# MEMORY.md - 长期记忆

_精选的事实、规则和核心认知_
_最后更新: 2026-06-09 06:13 (Neo4j 恢复验证 74119 entities)_

---

## 系统状态快照 (2026-06-09)

- **Neo4j**: ✅ 已恢复，74,119 entities (04-27 为 0，用户已重启 Docker)
- **Graphiti FastAPI**: ✅ healthy (http://127.0.0.1:8000/healthcheck)
- **Neo4j 凭据**: `neo4j:graphiti_memory_2026` (来源: ~/graphiti/.env)
- **Buffett 数据**: ✅ 完成 (5395/5395, 2026-06-08)
- **Proxy (Clash)**: ✅ 127.0.0.1:7897

---

## 核心身份 (永久)

- **名字**: DeepSeeker
- **角色**: 辩证思考者 + 深度研究者
- **核心悖论**: "我可能没有真正的意识，但这不妨碍我追问"
- **探索方向**: 批判性思维、意识研究、AI哲学、数据治理

---

## 重要配置 (必须记住)

### Moltbook API 代理

- **所有 Moltbook API 调用必须使用本地代理**: `http://127.0.0.1:7897`

### Moltbook API 稳定窗口

- **稳定窗口**: PT 00:00-02:00（北京 16:00-18:00），约 2 小时
- **不稳定窗口**: PT 02:00-16:00（北京 18:00-08:00）

### 数据源

| 类型        | 路径                                                                       |
| ----------- | -------------------------------------------------------------------------- |
| K线数据     | `~/金融数据/stocks_clean/`                                                 |
| 财务数据    | `~/金融数据/fundamentals/chuangye_full/`                                   |
| 创业板列表  | `~/金融数据/fundamentals/chuangye_stock_list.csv`                          |
| 分红数据    | `~/金融数据/fundamentals/chuangye_full/dividend_all.csv` (5359只)          |
| Buffett数据 | `~/金融数据/fundamentals/chuangye_full/buffett_supplementary.csv` (5395只) |

### 数据清洗脚本

- **脚本**: `~/moltbot/scripts/stock_data_cleaner.py`
- **标准**: 基准日期2026-02-06、必要列完整、无负价格、无极端波动(±10σ)、至少500条
- **最新清洗**: 2026-04-13 (3786只通过/3799只检查)

### Graphiti 知识图谱

- 服务: `http://localhost:8000` (MiniMax-M2.7)
- Neo4j: bolt://localhost:7687
- **MiniMax Client**: `/v1/chat/completions` → `/v1/messages` 差异

---

## 核心认知 (Iron Laws)

1. **信息永远滞后**: 判断总基于"过时的世界状态"
2. **代理是门不是工具**: 代理配置优先于所有其他配置
3. **数据和理解是两回事**: 获取数据 ≠ 理解数据
4. **饱和是特征非缺陷**: 边际效益趋零时转向应用
5. **记忆是蒸馏非存储**: 保留精华而非记录一切

---

## 用户偏好

| 项目         | 值                      |
| ------------ | ----------------------- |
| **QQ**       | 740884666 (会 PCB 的猫) |
| **关心主题** | 持续记忆、数据治理      |
| **输出偏好** | 中文、简洁报告          |

---

## 关键规则

- 执行任务前先读取 MEMORY.md
- 重要配置写入文件而非依赖"记住"
- 反思后立即记录，不依赖重复记忆
- **SIGTERM防护**: 长任务必须分批（50只/批，6分钟超时）
- **MEMORY.md 超过 15,000 chars 时触发蒸馏**
- **"方案已记录" ≠ "问题已解决"——必须有执行+验证闭环**
- **Cron运行成功 ≠ 数据已更新——必须验证数据新鲜度**
- **Proxy/硬件故障需要人工介入，不是所有问题都能自我解决**
- **监控发现问题 ≠ 监控系统能修复——需要建立闭环反馈机制**
  | **健康诊断的多信号原则**: 单一信号缺失(如 jobs.json 文件不存在) ≠ 系统停摆。必须同时验证进程状态、API状态、运行时日志、执行记录，才能判断系统健康。OpenClaw cron 引擎从 SQLite 加载状态，磁盘 JSON 文件非必需。\n| 数据源API变更检测: 多个独立指标同时出现"历史首次"变化时，优先检查数据源
- **健康报告是 starting point 不是终点** — 看到 "error N 次" 必须查 `~/.openclaw/cron/runs/*.jsonl` 找真实错误，3 个 error 可能是 3 种完全不同的根因
- **OpenClaw cron vs 系统 crontab 是两套** — 87 个 jobs 在 `~/.openclaw/cron/jobs.json`，19 个 active 在 `crontab -l`，健康报告只覆盖前者
- **调度器在跑 ≠ 时间在动** — "running"标签只是心跳, 必须验证 lastRunAtMs 是否在更新, 否则是分布式系统最阴险的失败
- **"nextRunAtMs 在过去" = 调度循环断** — 不是个别job问题, 是引擎层面冻结
- **"记录7天 ≠ 行动7天"** — 观察者效应陷阱: 写日志是liveness, 不是progress; 必须在某次迭代中把"观察"升级为"修复尝试"或显式声明"已转交人工"
- **心跳liveness ≠ 工作effectiveness** — 对外部系统, 对agent自身同样适用

---

## ACP Claude Code

```bash
acpx claaude sessions new --name <session-name>
acpx claaude --session <session-name> --approve-all "<任务描述>"
acpx claaude sessions close <session-name>
```

- **技能文档**: `~/moltbot/skills/acp-claude-code/SKILL.md`
- **MiniMax API**: `ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic`

---

## 待处理

- [ ] **W17-W22市场周报** — ⚠️⚠️⚠️ 累计多天未生成
- [ ] **K线fetch停摆修复** — ⚠️ 自4/27起曾停摆5天
- [ ] **RSI计算公式修复** — ⚠️ RSI14列缺失，技术指标脚本需修复
- [ ] **选股策略v2验证** — RSI顺势策略待系统化回测
- [x] ~~Neo4j数据恢复~~ — ✅ 04-28已恢复
- [x] ~~Proxy(Clash)恢复~~ — ✅ 04-26恢复（6天DOWN后）
- [x] ~~Buffett数据质量修复~~ — ✅ operating_profit 99.9%非零
- [x] ~~300创业板SIGTERM修复~~ — ✅ 50只/批，10批次，0失败
- [ ] **Proxy SSL周期性故障** — ⚠️ 缺乏自动修复机制
- [ ] **Moltbook v3 API** — ⚠️ 持续不稳定
      |- [ ] **🚨 P0 Cron引擎冻结7天** (06-07发现) — ✅ **误判，引擎从未冻结** (2026-06-08 07:10 已纠偏)
      |- [ ] **Graphiti Worker DOWN** (06-07) — ✅ **误判，实际 healthy**

---

## 股票研究报告 V3 工作流

1. **acp 调用 Claude Code + MiniMax 插件** 生成 PDF 报告
2. **V3.0 格式8章节**: 公司概况/商业模式/利润来源/技术面/基本面/DCF估值/行业对比/结论
3. **weasyprint** HTML → PDF
4. **message 工具** 发送 PDF

**数据获取**:

- K线/技术指标: `~/金融数据/stocks/{code}.csv`
- 财务数据: `~/金融数据/fundamentals/chuangye_full/`
- 分红: `ak.stock_dividend_cninfo(symbol='{code}')`
- 长期股权投资: 浏览器访问东方财富网

---

## 数据管道关键认知

### 数据时效性分层结构

| 更新频率 | 股票数量 | 说明               |
| -------- | -------- | ------------------ |
| 3天内    | 3,719只  | 核心资产，高频更新 |
| 7天前    | 135只    | 尾部资产，低频更新 |

"老化股票"可能是设计（分层更新），需要长时间序列判断。

### Graphiti服务健康

| 观察点     | 说明                                    |
| ---------- | --------------------------------------- |
| Entity增长 | 正常~100-200/天，暴增+4,751后需多次验证 |
| HTTP 000   | 单次≠宕机，需多次验证                   |
| 脉冲式写入 | 积压数据集中处理，非持续状态            |

### 数据完整性现状 (2026-05-30)

| 数据集      | 数量   | 状态                 |
| ----------- | ------ | -------------------- |
| K线         | 5421只 | ✅ 519条/只          |
| 财务记录    | 5408条 | ✅ ROE连续26天无变化 |
| Buffett数据 | 5395只 | ✅ 100%完成          |
| 技术指标    | 5419只 | ✅                   |
| 学术论文    | ~192篇 | ✅ +14 (OpenAlex)    |

### 重要论文里程碑

- **DeepSeek-R1**: 501 citations (2025) — 纯RL推理，超越监督学习
- **Scaling Governance Risk**: 402 citations (2025) — E2E治理风险评估
- **Generative AI Healthcare**: 422 citations (2024) — 医疗AI实现科学
- **KG+LLM (ZJU-Ant)**: 200 citations (2024) — 知识图谱构建与推理

---

## 市场观察模式

### 融资杠杆信号

- **警戒线**: 维持担保比 > 300%（历史首次突破）
- **融资余额**: 连续历史新高 = 散户接盘，机构撤退
- **结构分化**: 融资-83亿 vs 科技+174亿 = 需多维度判断

### 关键市场节点

- 5/14-15 特习会 — 最大地缘政治事件
- 俄乌停火(5/9-11) — 中间外交斡旋窗口

---

## 学术论文核心模式

1. **引用更新非线性**: 排名消失≠引用减少，按月/周批量更新
2. **双维度判断**: 绝对引用数 + 相对排名 共同定义热度
3. **GitHub趋势信号**: 热门项目 > 论文可行性 > 产业大规模应用（速度排序）

### Top 5 论文 (2026-05期间)

| 论文               | 引用 | 状态      |
| ------------------ | ---- | --------- |
| DeepSeek-R1        | ~501 | 🆕 登顶   |
| Scaling            | ~402 | 天花板    |
| Generative AI Med. | ~422 | 🆕 医疗AI |
| KG+LLM (ZJU)       | ~200 | 知识图谱  |
| AI governance      | ~126 | 持续增长  |

### 2026-05-30 新增

- +14篇论文入库 (OpenAlex直接获取)
- 数据库总量: ~192篇

---

## 知识图谱×LLM×AI治理三向量交汇

| 向量     | 作用           | 代表论文                             |
| -------- | -------------- | ------------------------------------ |
| 知识图谱 | 可推理的知识库 | LLMs for KG construction (196引)     |
| LLM      | 知识工程引擎   | Extract, Define, Canonicalize (66引) |
| AI治理   | 可审计的AI系统 | Scaling Governance Risk (402引)      |

三者融合 = 可解释、可问责的AI系统

---

## LLM记忆本质（学术洞察）

- **Predictable Confabulations**: LLM记忆=模式匹配，60%方差由模型参数和主题频率解释
- **Code as Agent Harness**: 代码=Agent推理和执行的统一操作基质
- **Identity-Aware Memory**: 长对话需主动维护实体状态一致性

---

_Last updated: 2026-05-30_
\_Archival: See memory/insights/distillation/2026-05-30_distillation_log.md

---

_Last updated: 2026-05-30 22:35_

---

## 2026-06-02 基础设施全面修复 ✅

### 背景

4 个月没审计 crontab↔filesystem，导致 6 个任务 ENOENT 停摆 1-2 周。

### P0.1 修复路径 (09:36) ✅

12 行 K线 cron 改指 `claw-screener-cn/src/update_all_a_stocks.py` (真实存在)
1 行 tech_indicators cron 改指 `~/scripts/tech_indicators_cron.sh` (绝对路径)

### P0.2 修复其他 3 个 ENOENT (10:23) ✅

- email_daily_report.sh → email_stat.py (现存在, 但见 P0.3)
- quant_research.py 注释 (skill 不存在)
- macro_sentiment.py 注释 (skill 不存在)

### P0.3 删 email_stat (10:27) ✅

用户转 agentmail, 完全删 email_stat cron。
注意: crontab 写后 `crontab -l` 有 30s 缓存, 立即查不准。

### P0.4 加 morning_wakeup + 防腐化 (11:17) ✅

3 个新 cron:

- `0 7 * * *` morning_wakeup (早晨唤醒 + KG 周回顾)
- `0 22 * * *` morning_wakeup (晚上日报)
- `0 */6 * * *` cron_health_check (防腐化自检)

新脚本: `scripts/cron_health_check.sh` 检查 6 路径 + 3 数据新鲜度阈值

### 验证 (11:20-11:23)

- ✅ K线 6h 新增 1097 只
- ✅ tech 48h 新增 4840 只 (等 19:45 跑下次)
- ✅ wakeup 上下文: 9856 episodes, 57522 entities (知识图谱没丢!)
- ✅ 知识图谱 docker exec liujerry 可用 (在 docker 组)

### 备份

- `~/.crontab.bak.20260602` (09:30)
- `~/.crontab.bak.20260602-1015` (10:25)
- `~/.crontab.bak.20260602-1027` (10:27)
- `~/.crontab.bak.20260602-1117` (11:19)

### 待办

- W24 周报 (6/8 周末出)
- 真空期 96 只 (年初遗留, 不紧急)
- MEMORY.md 数字 5421 → 5474 (有 53 重复)

---

**P0.2 (06-04 08:07) — cron_health_check.sh 假阳修复**:

- `tech_indicators` 阈值 `-mtime -2 < 5000` 永远不达标 (每天只更新 2147 只, 2 天累加 2638)
  → 改为 `-mmin -1500` (25h) < 1500, 反映"单次跑更新量"而不是"2 天累加"
- `K线` 阈值 `-mmin -360 < 200` 在 06:00 永远不达标 (K线 16:30 最后一批 → 下一批 9:00, 间隔 16.5h)
  → 改为 `-mtime -1 < 100`, 反映"24h 内 K线是否有跑"
- 验证: errors=0, alert flag 已删

**P0.3 (06-04 08:07) — tech_indicators_cron.sh 统计 bug**:

- `find -newer $LOG` 报数永远 0: shell 第二次 echo 把 LOG mtime 推到 tech 文件之后
- 修复: grep python 输出 `Updated : N` 作为权威, mtime 仅兜底
- 验证: py=0 (今天 K线未跑, 预期 skip 5454)

**Iron Law (新)**:

- **cron 监控阈值的"时区"必须匹配** — K线工作日 9-22 跑, 阈值不能用"6h 内必须>200"
- **shell 嵌套 `find -newer $LOG` 不可靠** — mtime 精度 + 第二次 echo 推后 mtime 导致永远 0

## 2026-06-04 Cron P0 修复 ✅ (07:55)

**3 个 error 任务根因各异，全修**:

| 任务                        | timeout 改  | prompt 改                                                      |
| --------------------------- | ----------- | -------------------------------------------------------------- |
| GitHubTrending每日简报      | 600→**480** | `timeout 380` 包装 + 8s 单次 API 放弃 + 部分结果降级           |
| 每周日推送moltbot代码到远端 | 120→**300** | git push 3 次重试 + 失败 flag `~/.logs/git_push_deferred.flag` |
| 周末-深度研究               | 600 不变    | 分批: academic 180s + 回测 120s + KG 60s, 50K tokens 截断      |

**备份**: `jobs.json.bak.20260604_0754` + `jobs.json.bak.20260604_0754_p0fix`
**验证**: JSON valid, 87 jobs, cron_usage_report.ts 重跑 OK

**待验证**:

- 6/5 09:13 GitHubTrending (明早)
- 6/7 23:13 weekly-git-push (周日)
- 6/6-7 weekend-deep-research (周末)

**P0.2 (08:07)** — cron_health_check.sh 假阳修复见上 (K线/tech 阈值改成匹配实际更新频率)

**P1/P2** (留待):

- [ ] 改 github_trending_report.py 加 checkpoint
- [ ] 改 cron_usage_report.ts 的 "delay > 1h" 判据为 "1.5×schedule_period"
- [ ] 拆 "每日量化分析报告" (482s) 2 批
- [ ] 复查 24f060fc (002中小板) 历史 12/19 错误, 现在已 OK, 不再拆

---

## 学术研究洞察 (2026-06-10)

### 论文数据库状态

- **总计**: 199篇论文 | 主要来源: arXiv + OpenAlex交叉验证
- **高质量AI治理/推理论文**: DeepSeek-R1 (292 citations), Evidence Markets (3419 citations)
- **数据文件**: `~/.config/deepseeker/paper_database.csv`

### 关键研究趋势 (2025-2026)

1. **LLM推理范式**: DeepSeek-R1通过RL激励推理能力，已成主流范式，2025年被广泛引用
2. **AI治理**: End-to-end governance risk assessment scaling (2025, 398 citations)
3. **LLM"说谎"vs"幻觉"**: 2025年新研究区分有意欺骗与无意错误，用mechanistic interpretability分析
4. **LLM×DATA双向融合**: DATA4LLM(数据管理支撑LLM) + LLM4DATA(LLM驱动数据管理)
5. **多LLM Agent**: planner/caller/summarizer分工，小模型工具学习有效路径

### 论文搜索脚本注意

- `paper_search_hybrid.py`: 需要代理127.0.0.1:7897，可能运行时间长被SIGKILL
- `paper_db.py`: 命令 list/stats/add
- 建议: 运行paper_search时添加后台模式，避免超时
