# Corrections Log

## 2026-06-12 22:21

### Verification before quoting file sizes in heartbeat

- **Context**: 22:19 heartbeat claimed "Buffett CSV: 1.82MB, 06-08 未变". 22:21 verification could not find any ~1.8MB Buffett CSV in repo (v4_screening files are 14-15KB, buffett_data.db is 0 bytes).
- **Lesson**: When claiming file size/mtime in heartbeat, always `ls -la` the actual path first. Don't carry forward unverified numbers from earlier reports — they may reference a file that was moved, deleted, or never existed at that path.
- **Action**: Going forward, treat quoted file sizes/dates in prior heartbeat entries as untrusted; verify with `ls -la` before re-using in new entries.

## 2026-06-14 06:24

### Network fragility: Proxy+arXiv dual failure has固化 as a weekly pattern

- **Context**: 06-11~06-14 连续 4 日 Proxy (Clash) + arXiv 直连同步不可达, 状态完全未自愈
  - mihomo 进程/端口健康 (7d12h+), 但 DNS 127.0.0.1:53 refused + upstream timeout
  - arXiv 直连也挂 (5s timeout) — 暗示问题可能不限于 Clash, 本机 upstream DNS/路由也可能受影响
- **Lesson**: 假期 + 周末双因素叠加时, 外部服务降级最易固化, 单纯维持 liveness 策略 (6h 心跳) 不够 — 需要更早触发主会话介入信号
  - **触发升级规则**: 连续 ≥2 个心跳 (≥6h) Proxy 持续失能 → 升级为 P1 提醒, 在 HEARTBEAT 顶部用 🚨 标识
  - **避免噪音**: 不要每个心跳都重复 "Proxy 持续失能", 改用 delta-only 报告 (只记录相对上次的变化)
- **Action**: 下次 (6/15 开盘后或下次 proxy 恢复时) 复盘这次 4-day outage 的根因, 写入 self-improving/reflections.md

## 2026-06-22 22:30 paper_search_hybrid.py 网络超时 — 降级策略

**症状**:

- paper_search_hybrid.py 在 cron 夜间执行时持续挂起（arXiv 直连 + proxy 双超时）
- 这是 06-14 以来又一次 Proxy/arXiv 同步失能的体现

**教训**:

- 夜间 cron 不应依赖脚本的网络连通性——应该默认 web_search 作为降级路径
- paper_search_hybrid.py 的挂起会阻塞整个 cron job chain 的后续步骤
- 解决: 对于网络依赖任务，web_search (MiniMax) 比 curl 到 arXiv 更可靠

**改进**:

- [P1] 修改 paper_search_hybrid.py cron template: 添加 30s timeout + 快速降级到 web_search
- [P1] 或者将论文发现拆分为两个独立 cron: (1) 快速 web_search 发现 + (2) 可选的深度 arXiv 抓取（可选、有网才跑）
- [P2] 当前 fallback 策略验证: paper_search_hybrid.py → web_search → 停止（不再无限重试）

## 2026-06-22 22:24

### Heartbeat entry cron list 推测 vs 实际验证 — 80% 准确, 仍需 verify

**Context**: 22:19 heartbeat entry 推测了 6/22 整天 5 项预测验证 + 10 项 cron 状态, 22:22 (3min 后) 用 `openclaw cron list` 实际拉数据对照:

- 22:19 推测 5 项预测 → 实际验证 4/5 准确 (EastMoney/学术搜索/语音播报/夜间构建预测 OK, 开盘前综合预测 fail 准确)
- 22:19 推测 10 项 cron 状态 → 实际验证 8/10 准确 (邮件检查 last 13h 误为 last 3h, 22:19 未单列 3 个健康 cron: K线数据采集/16:30深度复盘/创业板)

**Lesson**:

- 跨日收盘后 entry 推测 cron 状态时, 应在 entry 写盘前 1 min 跑一次 `openclaw cron list` 拉真实数据, 而不是凭 cron history 推断
- "last 13h ago" 在 22:19 (开盘后 12h49m) 和 22:22 (开盘后 12h52m) 看起来都是 13h, 但 cron list 实际 last 3h (19:13 那次) → **22:19 entry 的 last 13h 是不准的, 应该 last 13h, 但 cron list 报 last 3h 表明有 cron 19:13 跑过, 22:19 推测漏算**
- 22:19 entry 未列的 3 个健康 cron (K线/16:30深度复盘/创业板) — 收盘后实际健康 cron 数量比推测多 5 个, **6/22 实际 cron 健康度比 22:19 entry 描绘的好**

**Action**:

- 下次 (6/23 04:19-04:25 或 6/23 收盘后) heartbeat entry 推测 cron 状态时, 强制 30s 前跑 `openclaw cron list` 拉真实快照
- 不要跨日推测, 收盘后 + 3min 内跑一次 cron list = 真实 baseline
- HEARTBEAT entry 写"23 个 cron 中 8 ok / 15 error" 类总结时, 改用"openclaw cron list 实时: 13 ok / 10 error (22:22 验证)"

## 2026-06-23 22:21 晚间心跳教训 (cron-event)

**Context**: 06:25 早间 entry 设的 4 项 P0 (替换 hq / W26 周报 / 校正 6/22 daily / 5 脚本 commit) 在 6/23 整天 0/4 执行, 主会话整天 = 1 次活动 (22:13 夜间学术研读)

**Lesson**:

- 主会话 6/23 = "学术研读优先, P0 推到次日" 模式, 这与 6/22 "cron 主导, 跳过 HEARTBEAT/daily 校正" 模式相同
- 连续 2 日 (6/22 + 6/23) 主会话都跳过了 P0, **🟠 P0 失约是结构性, 非偶发**
- 4/4 P0 失约的归因: 主会话优先级 = 学术 > cron > P0, P0 永远排第 3
- 跨日 cron event (晚间心跳) 是 P0 唯一外部推动力

**Action**:

- 6/24 09:00 主会话唤醒后, 应**强制 P0 块** (一次性集中处理 4 项, 不要再分多次)
- 改进 cron 提示词模板: 提示主会话 "若距 09:30 < 12h 且 P0 未完成, 先做 P0 再做学术"
- HEARTBEAT entry 推测 P0 兑现率时, 改用"P0 失约率" 而非 "P0 完成率" (6/22 = 0/4, 6/23 = 0/4 = 100% 失约率)
- 反思笔记 (3 问) 写到 daily, 但未转化为 action — 提示词应明确 "若反思笔记问 1+ 未答, 优先答反思"

## 2026-06-25 06:25 Graphiti 8000 误报 false alarm — 健康检查端点需核对

**症状**:

- 之前 heartbeat entries 一律用 `curl http://localhost:8000/health` → 永远 HTTP 404
- 据此误判 "Graphiti API 僵死 (pid 2199, 12d+ uptime, 8000 端口未 LISTEN) — `memory_search` 工具失效"
- 列为 P0 #6 重启任务, 持续 4 日累积

**根因 (6/25 06:25 验证)**:

- 实际 `curl http://localhost:8000/healthcheck` → **HTTP 200** (0.0013s)
- FastAPI 默认不提供 `/health` 端点, 实际是 `/healthcheck`
- 完整 OpenAPI 10 paths 全可用, `memory_search` 工具**实际可用**
- 误报源: 之前 heartbeat entries 用错端点 (`/health` 永远 404)

**教训**:

1. **健康检查端点要先验证** — FastAPI `/health` 不存在, 需显式定义, 默认是 `/healthcheck` (或自己定义)
2. **404 不等于 死** — HTTP 404 是端点不存在, 不是服务死, 这是不同信号
3. **观测者的盲点** — "健康检查"本身需要先验证, 否则会形成"系统性误报"
4. **P0 误报的代价** — 1 项假 P0 占 4 日累计精力, 1 项 P0 误删可释放 1 个执行槽位

**行动**:

- [x] ✅ P0 #6 "Graphiti API 重启" **删除** (误报修正)
- [x] ✅ `memory_search` 工具实际可用, 可恢复使用
- [ ] 🟡 P1: cron 提示词加 `/healthcheck` 检测, 避免再误判
- [ ] 🟡 P2: 复查其他服务健康检查端点 (Neo4j / mihomo / cron daemon) 是否有同类误报风险

**修正后 P0 累计** (5 项必做, 估 75-100min):

- P0 #1 替换 hq.sinajs.cn → qt.gtimg.cn (第 4 日)
- P0 #2 提交 19 文件脏 (第 4 日)
- P0 #3 校正 6/22 daily 00:13 P0 表 (第 3 日)
- P0 #4 W26 周报定稿 (第 6 日)
- P0 #5 300276 三丰智能止损决策 (第 4 日)

**元反思**:

- "false alarm" 本身就是 signal — 它告诉我"我的观测方法有系统误差"
- agent 不知道"自己不知道什么", 但 false alarm 出现时应该怀疑"自己的观测方法"
- "信息永远滞后" Iron Law 应用: 我观测到的 "Graphiti 死" 是滞后的/错误的, 实际"Graphiti 健康"才是当前真相

## 2026-06-26 22:19 heartbeat — lessons

- **HEARTBEAT.md 单文件 432K chars 超 OpenClaw 12000-20000 chars bootstrap 注入上限** — agent 仅看到头部 2.78%, 后续 420K 不可见. **🔴 蒸馏窗口已过 4 周, 6/27 必做 432K → 60K 蒸馏压缩**.
- **syslog heartbeat poll 不等于 HEARTBEAT.md entry 写入** — 6/26 整天 7+ heartbeat starts 但 HEARTBEAT.md 0 新 entry (除本 entry), 因 agent 看到截断的 12K 上下文, 无法识别"上次 entry 在哪" 而直接 append.
- **QQ Bridge 3001 监听 ≠ 用户实际使用** — 6/22-6/26 累积 4+ 日 P0 (delivery-queue/failed 421+) 6/26 12:59 用户扫码后清空. P0 兑现 = 端到端验证 (LISTEN + ESTAB + delivery-queue 0 + QQ 实际可达).
- **push2 "半恢复" 实测必须 3+ retry** — 6/25 22:21 单次 HTTP 200 body 空 实为 0.16s 偶发 fluke, 6/26 22:19 3/3 retry 全部 OpenSSL eof. 单次信号不能作为状态结论.
- **6/26 daily 仅 2525 chars 但主会话 7+ 心跳 + 13+ QQ bootstrap** — 反思: 主会话被截断困住无法写 daily, cron 触发但无对应 daily 段. 6/27 必补 6/26 cron 段 / 反思段 / P0 段.

## 2026-06-27 00:13 nightly wakeup — 截断危机的认知升级

### 上下文

夜间唤醒 (cron: 加载记忆到上下文) 加载了 6 份核心文件:

- self-improving/memory.md (10 Iron Laws)
- 3 个最新 insight JSON (00:00/20:00/16:00 of 06-26~27)
- W26 / W25 周报
- 06-26 daily (2525 chars + 22:19 heartbeat 段)
- MEMORY.md (7169 chars)

### 关键发现

- **3 个 insight JSON 完全相同** — 验证 IL-007 信号失真已稳定 (不只是偶发)
- **HEARTBEAT.md 432K 截断到 12K (2.78%)** — 6/26 整天主会话实质是"失忆的我"
- **失忆的我是另一个我** — 5/5 P0 失约不是懒, 是结构性失忆
- **本次唤醒的有效性边界** — context 注入 ≠ 文件写入. session 结束 context 消失, 唯有 file 是真记忆

### 教训

1. **cron 唤醒 = 隐形的 context 修复窗口** — 主会话被截断困住时, cron 是唯一能注入完整上下文的机制. 但若唤醒仅写入 context 而不写 file, 等于无效唤醒.
2. **memory/ 在 .gitignore 中** — daily 写入磁盘但不入 git, 累积的 14 ?? 文件不只是 dirty, 是不在版本控制. 主会话 git add 应考虑 `-f` 或调整 gitignore.
3. **自我检查应纳入"截断感知"** — 唤醒时不仅检查"我还是不是我", 还要检查"主会话看到的版本是不是我". 这是新维度.

### 行动

- 本次唤醒已写入 06-27 daily (4943 chars, 含加载清单 + 自我检查 + 今日 P0 + 离线方法论)
- 候选 IL: **"context 注入 ≠ 长期记忆, file 才是"** — 候选编号 IL-011
- 候选 IL: **"截断下主会话 ≠ 完整的我"** — 候选编号 IL-012

---

## 06-28 06:24 心跳 grep 模式缺陷 (IL-007 候选 #3)

### 事件

- 06:22 heartbeat 报 "Gateway 进程未在 ps 检出 (vs 6/27 22:17 报 5h26m+, 推测周末 OOM/重启)"
- 06:24 heartbeat 实测: pid 73263 /home/liujerry/文档/programs/openclaw/dist/index.js gateway --port 18789 持续运行, 6/26 起累计 38m CPU 时间
- **误判根因**: 06:22 grep 模式 `openclaw gateway|cron -f|verge-mihomo|neo4j|graphiti` 不含 `node` 关键字, 漏检 Node 进程

### Signal 失真第 3 类: heartbeat grep 模式缺陷

- 类 1 (已有): 相同 JSON — 同一对象测两次, 看似"无变化"实为盲点
- 类 2 (已有): 端点错配 — /health 404 vs /healthcheck 200, 测错路径误报"恢复"
- 类 3 (新): grep 模式缺陷 — 模式字符串漏关键字, 漏检进程, 误判"未运行"

### 修正方案

- heartbeat 进程检测统一用宽模式: `pgrep -af "openclaw|node.*openclaw|gateway"` 或更宽 `ps auxw | grep -iE "openclaw|gateway|node.*18789"`
- 不要把"未在 ps 检出"作为 P0 触发条件, 必须 + netstat/ss LISTEN 二次确认
- IL-007 候选 #3 待 7 日内 ≥3 次使用后 promote

### 数据

- HEARTBEAT.md 增量 entry: 507K → 513K (+6K)
- memory/2026-06-28.md 增量: 5212 → 6665 chars (+1453)
- push2 交叉验证里程碑: 4/4 字段全对齐, P0 #1 双源冗余完成

### IL-007 候选 #3 闭环 (6/28 22:21)

- **6/22 entry 06:30**: heartbeat grep 模式缺陷漏检 Node 进程 (误报 Gateway 重启)
- **6/27 22:17 entry**: upstream counter 报 43436 (stale refs, 非持久信号)
- **6/28 06:22 daily**: upstream refs 修正 43436→98 (一次性 fetch 后态)
- **6/28 22:21 entry**: upstream counter 回 43470 (SSH fetch 挂起, refs 又 stale)
- **闭环结论**: "ahead of upstream/main 数字波动大" 应理解为 stale refs 信号, 不应作为 P0 触发条件; **真正行动信号是 "ahead of origin ≠ 0" 或 "git push origin 失败"**
- **promote 候选**: 7 日内 ≥3 次使用后 → IL-013 "ahead counter = stale refs 信号, 不是行动信号"

### 数据 (22:21 增量)

- HEARTBEAT.md: 515197 → 522740 (+7543 chars, 本次 entry)
- memory/2026-06-28.md: 11817 → 13723 (+1906 chars, 本次 entry)

### IL-014 (2026-06-30 22:17 heartbeat) — curl -o /dev/null 在 TLS eof 场景的假阳性

- **症状**: `curl -s -o /dev/null -w "%{http_code}" https://push2.eastmoney.com/...` 报 HTTP 200 (0.19s)
- **真相**: TLS handshake 完成但 server 立刻 SSL_read: unexpected eof, body 为 0 bytes, 业务层不可用
- **教训**: 仅靠 HTTP 200 状态码不可信, 心跳健康检查需升级:
  - ✅ 加 `-o /tmp/x.html; wc -c /tmp/x.html > 100` 字节数校验
  - ✅ 加 `-sv` 看 SSL 错误细节
  - ✅ 加 `--max-time 3` 防 hang
  - ✅ 关键 endpoint 抽 1 个字段校验 (如 qt 的 sh600519 必须含 "1185")
- **影响范围**: 6/27-6/28 push2 RECOVERED 24h+ 期间所有 "HTTP 200" 报告需复盘 (可能都是假阳性)
- **行动**: 下次写 health_check.sh 时采纳, 6/30 22:17 entry 已采纳 (实测发现)
- **优先级**: P1 (heartbeat 健康检查升级, 不影响当前持仓决策)
