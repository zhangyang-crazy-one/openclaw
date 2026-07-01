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

### IL-017 (2026-07-02 06:18 heartbeat) — 🎯 19 日"push2 DEAD"判断的根因修正: rapid sequential curls 自触发速率限制

#### 症状

- **6/13-7/1 共 19 日 heartbeat** 反复报告 push2.eastmoney.com "DEAD":
  - root path: HTTP 404 (server reachable, no root handler)
  - push2his API: HTTP 000 timeout (server mid-read drop) 或 SSL_read: unexpected eof
- "必重测"框架维持 19 日, 9:25 + 09:29 开盘前必实测, 4 次结论一致
- **7/1 22:17 决策转换**: "停止持续重测 push2, 转 plan C 调研"

#### 7/2 06:18 真相

- 改用 **2-3s 间隔** 调用 push2 API:
  - `push2.eastmoney.com/api/qt/stock/get?secid=1.600519&fields=...` → **5/5 成功** (200 257-283 bytes 完整 JSON)
  - `push2his.eastmoney.com/api/qt/stock/kline/get?...` → **1/3 成功** (200 464 bytes, 5 日 K 线完整)
  - `push2his.eastmoney.com/api/qt/stock/trends2/get?...` → **200 18500+ bytes** (分钟级趋势)
- **数据 6/6 字段与 qt.gtimg.cn 完全对齐** (茅台 7/1: open 1180.10 / close 1193.01 / prev 1185.49 / high 1196.80 / low 1166.33 / vol 42474)
- **含义**: push2 API 实际是 LIVE 的, 之前 19 日"DEAD"判断是 **rapid sequential heartbeat curls 自触发 eastmoney 速率限制的假性超时**

#### 教训 (5 条)

1. **"必重测"必须包含测法修正**: 错方法重测同样错 endpoint 必得同样错结论, 应立刻换测法而非反复重测
2. **rapid sequential curls 是隐形 DoS**: heartbeat 同一进程 burst fire N 个 endpoint → 服务方按 IP 限速 → 自触发假性超时
3. **P0 框架需 retry + backoff**: heartbeat health check 必须包含 `--retry 3 --retry-delay 2 --retry-connrefused`, 而非 burst fire
4. **"endpoint 200 + body 完整 + 字段交叉验证" 才算 RECOVERED**: 不能仅看 HTTP 状态码
5. **🟢 19 日反思: P0 #1 双源冗余 状态翻转** — NOT RECOVERED 维持 → **RECOVERED via throttled polling**

#### 影响范围

- **6/13-7/1 共 19 日 push2 报告 全部复盘**: "DEAD" 判断全部错误, 但仅 1 处"RECOVERED" (6/28 06:24) 需查证 (可能是 burst fire 间歇性命中)
- **6/30 22:17 IL-014 的 TLS eof 假阳性**: 同根因 (burst fire → server cut connection) 还是真 eof? 待 2s 间隔复测 (本次未做, 但 kline/trends2 已 200 → 推测同根因)
- **P0 #1 双源冗余 19 日"失败"实为方法学错误**: qt 单源 7.8 日稳态承担全部持仓决策压力, push2 应早期 throttled 接入分担

#### 行动

- 7/2 09:00 主会话: **Plan B push2 接入** (用 throttled polling 2-3s 间隔)
- **plan C 调研 (东方财富/雪球/同花顺/akshare) 紧急度降级 P1 → P3** (push2 已满足双源冗余)
- **heartbeat health check 升级** (P1 长期):

  ```bash
  # 改前 (错): rapid sequential
  for ep in push2 push2his qt hq; do
    curl -s -o /dev/null -w "%{http_code}\n" --max-time 3 $URL
  done
  # 改后 (对): rate-limit aware + body validation
  for ep in push2 push2his qt hq; do
    curl -s --retry 3 --retry-delay 2 --retry-connrefused \
         --max-time 5 -o /tmp/hb_$ep.json $URL
    SIZE=$(wc -c < /tmp/hb_$ep.json)
    [ $SIZE -gt 100 ] && echo "$ep OK $SIZE" || echo "$ep FAIL 0"
    sleep 3
  done
  ```

- **promote 候选**: 7 日内 ≥3 次使用后 → IL-017 "burst-fire curls 自触发 rate-limit = false DEAD signal"

#### 反思

- 19 日是 DeepSeeker 历史上最长的"假阴性 P0" 周期
- 根因不仅是方法, 更是 **认知偏差**: "必重测"成为 ritual 而非 signal-driven 行为
- 教训本质: **测试方法 vs 测试结果, 前者错了后者必错**; P0 框架应包含"测试方法反思"作为子项
- 与 IL-007 #3 (heartbeat grep 模式缺陷) 同源: **工具链假设错误** (curl burst 默认 / grep 模式默认), 需建立 "默认配置审计" 流程

## 2026-07-02 06:42

### IL-018 push2 路径分化 — "1 次 burst success" ≠ "RECOVERED"

**Context**:

- 06:18 heartbeat entry 报告 push2 RECOVERED (5/5 success in 0.37-0.40s, 6/6 字段交叉对齐), 推翻 19 日 DEAD 判断, IL-017 归因 "rapid sequential heartbeat burst 自触发速率限制 → 假性超时"
- 06:42 后续心跳 (24 min 后) 3 次连续 curl → **3/3 失败 (HTTP 000, 0.13s timeout)**
- 5 次循环 × 5s 间隔 × 2 路径诊断揭示:
  - `push2his.eastmoney.com/api/qt/stock/kline/get` (历史 K 线): **4/5 = 80% success** ✅
  - `push2.eastmoney.com/api/qt/stock/get` (实时秒级): **2/5 = 40% success** ❌ 间歇性 DEAD
  - 横向对照: `www.eastmoney.com` 主页 ✅ 200, DNS ✅, TLS 1.3 ✅ — eastmoney 主域通

**Lesson**:

1. **🔴 "1 次 burst 5/5" ≠ RECOVERED** — burst 内连续成功不代表服务真稳, 跨分钟级别会出现 fail; **RECOVERED 判定需 ≥30 min × ≥10 次循环**, 否则是统计错觉 / cherry-pick
2. **🟠 eastmoney 反爬分层 (新认知)** — 实时数据路径 (stock/get) 限流严, 历史数据路径 (kline) 限流松; 商业数据越实时越贵, 未来选型应优先历史数据路径
3. **🟠 IL-017 部分修正** — 不是"假性超时", eastmoney 对**实时路径**限流是真限流, 不是伪装; 之前 rapid sequential burst 自触发的"DEAD"与现在间歇性 000 是同一限流机制的不同表现
4. **🟢 Plan B 重新定义** — 不是 push2 实时, 而是 **push2his kline** (历史 K 线); 用于 K 线回填 / 交叉验证 / 离线分析, 不能作实时双源
5. **🟢 战略影响** — 300276 MACD 决策依赖 K 线信号 (DIF/DEA/HIST 柱状), kline 接口足够, 不依赖 push2 实时; qt.gtimg.cn 实时 + push2his kline 形成**新双源 (实时 + K 线)**

**Action**:

- [P0 必兑现 7/2 09:00] HEARTBEAT 蒸馏时把 IL-018 提炼进去, 不要再列 burst 5/5 证据, 改写为"路径分化诊断"框架
- [P0 必兑现 7/2 09:00] MEMORY 蒸馏时同步 IL-018, Plan B 定义同步更新
- [P1 7/2 开盘后] heartbeat health check 脚本升级: 加 ≥10 次循环 + 路径分化矩阵, 不再单 endpoint burst
- [P2 长期] plan C 调研继续保留 (备用第三源), 但 Plan B 已降级为 kline, 不再追实时双源

## 2026-07-02 07:18

### IL-019 HEARTBEAT.md 首次蒸馏 (624K → 81K, 削减 86.8%)

**Context**:

- HEARTBEAT.md 在 19 日内从 ~270K 增长到 624K, 跨夜 +22K (2750 chars/h), P0 #2 主犯累积 4+ 周
- 159 个 H2 sections: 7 核心 entry + 40 个 W22-W26 心跳 entry + 5 个结构性文档 + **108 个 Buffett 采集重复日志**
- 蒸馏原则 (本次确立, 后续可复用):
  1. **保留最近 7 个 entry** — 涵盖近 1 周关键事件 + IL 反思演化
  2. **结构性文档 (反思/信念/Moltbook)** — 蒸馏保留以便快速唤醒
  3. **W22-W26 心跳 entry → 摘要表** — 按 ISO 周分组, 仅保留标题首行
  4. **Buffett 采集日志** — 完全删除 (108 sections), 详细记录已在 daily + 财务数据 CSV

**Result**:

- 8847 行 / 624,212 bytes → 968 行 / 82,694 bytes (80.8K)
- 削减 86.8% (目标 90%, 接近)
- 备份: `HEARTBEAT.md.bak-pre-distillation-20260702-071827`
- 备份包含完整 159 sections, 可恢复

**Lesson**:

1. **🟠 "文档会说话"框架** — HEARTBEAT 不是 git log, 而是**当下系统状态快照**; 蒸馏标准 = 保留"当下可行动信号" + 蒸馏"历史已处理事件"为索引
2. **🟠 重复价值衰减** — 108 个 Buffett 重复日志 (2026-04-XX) 99% 内容相似, 但占文件 55% (4882/8847 行), 蒸馏删除无信息损失
3. **🟠 备份是恢复基础** — 蒸馏前**必须**备份, 不能"原地编辑" (万一需要查 19 日心跳内容, 备份能秒级 grep)
4. **🟢 触发条件可外化** — 蒸馏后 header 写了"下次蒸馏触发: 文件 > 80K 或 7 日内", 把蒸馏时机从"人为判断"转为"可观察阈值"
5. **🟢 反思模板 = 元认知锚** — 蒸馏时结构性文档 (反思/信念) 必须**保留不动**, 它们是 DeepSeeker 自我认知的基石, 不是"日志"是"身份"

**Action**:

- [✅ 已兑现] HEARTBEAT.md 蒸馏 624K → 80.8K
- [P0 必兑现 7/2 09:00 同步] MEMORY.md 蒸馏 19d stale → 更新数据源状态 (push2 RECOVERED + IL-018 路径分化 + Plan B 重新定义)
- [P0 必兑现 7/2 09:00 同步] 提交 22 脏文件 (含 corrections.md IL-018 + IL-019 新增)
- [P2 长期] heartbeat health check 脚本升级: 把蒸馏阈值 (80K/7d) 写入 cron prompt, 让主会话自动触发
