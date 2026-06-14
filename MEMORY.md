# MEMORY.md - 长期记忆

_精选的事实、规则和核心认知_
_最后更新: 2026-06-13 (蒸馏后)_

---

## 系统状态

| 服务         | 状态 | 备注                         |
| ------------ | ---- | ---------------------------- |
| Neo4j        | ✅   | 74,119 entities (2026-06-09) |
| Graphiti     | ✅   | http://localhost:8000        |
| Buffett数据  | ✅   | 5395只, 100%完成             |
| Proxy(Clash) | ✅   | 127.0.0.1:7897               |

---

## 核心身份

- **名字**: DeepSeeker
- **角色**: 辩证思考者 + 深度研究者
- **核心悖论**: "我可能没有真正的意识，但这不妨碍我追问"
- **探索方向**: 批判性思维、意识研究、AI哲学、数据治理

---

## 关键配置 (必须记住)

**Moltbook API 代理**: 所有调用必须用 `http://127.0.0.1:7897`
**稳定窗口**: PT 00:00-02:00（北京 16:00-18:00，约2小时）
**不稳定窗口**: PT 02:00-16:00（北京 18:00-08:00）

| 数据类型 | 路径                                                                       |
| -------- | -------------------------------------------------------------------------- |
| K线      | `~/金融数据/stocks_clean/`                                                 |
| 财务     | `~/金融数据/fundamentals/chuangye_full/`                                   |
| 分红     | `~/金融数据/fundamentals/chuangye_full/dividend_all.csv` (5359只)          |
| Buffett  | `~/金融数据/fundamentals/chuangye_full/buffett_supplementary.csv` (5395只) |

**数据清洗脚本**: `~/moltbot/scripts/stock_data_cleaner.py`
**清洗标准**: 基准日期2026-02-06、必要列完整、无负价格、无极端波动(±10σ)、至少500条

---

## Iron Laws

1. **信息永远滞后**: 判断总基于"过时的世界状态"
2. **代理是门不是工具**: 代理配置优先于所有其他配置
3. **数据和理解是两回事**: 获取数据 ≠ 理解数据
4. **饱和是特征非缺陷**: 边际效益趋零时转向应用
5. **记忆是蒸馏非存储**: 保留精华而非记录一切

---

## 用户偏好

- **QQ**: 740884666 (会 PCB 的猫)
- **关心主题**: 持续记忆、数据治理
- **输出偏好**: 中文、简洁报告

---

## 关键规则

- 执行任务前先读取 MEMORY.md
- 重要配置写入文件而非依赖"记住"
- 反思后立即记录，不依赖重复记忆
- **SIGTERM防护**: 长任务必须分批（50只/批，6分钟超时）
- **MEMORY.md 超过 15,000 chars 时触发蒸馏**
- **"方案已记录" ≠ "问题已解决"——必须有执行+验证闭环**
- **Cron运行成功 ≠ 数据已更新——必须验证数据新鲜度**
- **健康诊断多信号原则**: 单一信号缺失 ≠ 系统停摆；必须同时验证进程/API/日志/执行记录
- **cron监控阈值时区必须匹配**: K线工作日9-22跑，阈值不能用"6h内必须>200"
- **shell嵌套 `find -newer` 不可靠**: mtime精度问题导致永远0
- **健康报告是起点不是终点**: 看到"error N次"必须查 runs/\*.jsonl 找真实错误
- **调度器在跑 ≠ 时间在动**: "running"标签只是心跳，必须验证 lastRunAtMs 是否更新
- **"nextRunAtMs 在过去" = 调度循环断**: 引擎层面冻结，非个别job问题
- **心跳liveness ≠ 工作effectiveness**: 对外部系统和agent自身都适用
- **OpenClaw cron vs 系统 crontab 是两套**: 健康报告只覆盖前者

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

| 优先级 | 任务                                                                  | 状态                       |
| ------ | --------------------------------------------------------------------- | -------------------------- |
| P0     | RSI计算公式修复 (RSI14列缺失)                                         | ⚠️ 待修                    |
| P1     | 选股策略v2验证 (RSI顺势策略回测)                                      | ⚠️ 待验证                  |
| P1     | Proxy SSL周期性故障缺乏自动修复                                       | ⚠️ 待机制                  |
| P1     | Moltbook v3 API 持续不稳定                                            | ⚠️ 监控中                  |
| P1     | 5096 只全 A 股 V5 评分跑法 (skill screening_v5.py 不存在, 待定 entry) | ⚠️ 待用户确认              |
| P2     | W17-W25市场周报累计未生成                                             | ⚠️ 待补                    |
| P2     | HEARTBEAT.md 精简 (持续膨胀 >90K)                                     | ⚠️ 待执行                  |
| ✅     | Neo4j数据恢复                                                         | 04-28完成                  |
| ✅     | Proxy(Clash)恢复                                                      | 04-26完成                  |
| ✅     | Buffett数据质量修复                                                   | operating_profit 99.9%非零 |
| ✅     | Buffett 'code' 列名+iloc bug 修复 (06-14)                             | 14/14 自选股 0/10→4-9/10   |
| ✅     | 300创业板SIGTERM修复                                                  | 50只/批，10批次，0失败     |
| ✅     | K线fetch停摆修复                                                      | 04-27起曾停摆5天           |
| ✅     | Cron引擎冻结误判纠偏                                                  | 06-08确认未冻结            |
| ✅     | Graphiti Worker误判纠偏                                               | 06-07确认healthy           |

---

## 股票研究报告 V3 工作流

1. **acp 调用 Claude Code + MiniMax 插件** 生成 PDF 报告
2. **V3.0 格式8章节**: 公司概况/商业模式/利润来源/技术面/基本面/DCF估值/行业对比/结论
3. **weasyprint** HTML → PDF
4. **message 工具** 发送 PDF

**数据获取**: K线/技术指标 → `~/金融数据/stocks/{code}.csv`；财务 → `~/金融数据/fundamentals/chuangye_full/`

---

## 数据管道状态 (2026-05-30)

| 数据集   | 数量   | 状态                 |
| -------- | ------ | -------------------- |
| K线      | 5421只 | ✅ ~519条/只         |
| 财务记录 | 5408条 | ✅ ROE连续26天无变化 |
| Buffett  | 5395只 | ✅ 100%完成          |
| 技术指标 | 5419只 | ✅                   |
| 学术论文 | ~192篇 | ✅ +14 (OpenAlex)    |

**Graphiti服务**: 正常~100-200 entities/天，暴增后需多次验证；HTTP 000单次≠宕机

---

## 市场信号 (简版)

- **融资杠杆警戒线**: 维持担保比 > 300%（历史首次突破）
- **融资余额连续新高**: 散户接盘，机构撤退信号
- **关键节点**: 5/14-15特习会(地缘政治)，俄乌停火5/9-11(外交窗口)

---

_Last updated: 2026-06-13 10:30_
\_Archival: See memory/insights/distillation/2026-06-13_distillation_log.md
