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
