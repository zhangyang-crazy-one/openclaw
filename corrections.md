## 2026-06-08 — Heartbeat验证 vs 00:13笔记的确认偏误

凌晨唤醒笔记 (00:13) 把 Graphiti:8000 / Neo4j / memory_search embedding 列入 P0 清单, 但 06:24 实测发现三者全部健康。教训: **P0 标签必须附最近一次实测证据**, 否则只是基于既有焦虑的"假设"。任何 cron 监控 / 健康断言都应可被新一轮 curl/port-check 推翻。

## 2026-06-07 — weekly_insight_compiler.py section detection

**Bug**: Parser 把 `**时间**:` `**场景**:` 这类 bold-key 子项当成了问题列表项
(从 6 个"问题"虚增到 6 个全是 sub-bullet)；同时把 `- [ ] 待办` 误识别为洞察。
**Fix**: 过滤 bold-key 行 (`**X**: value`) 和 todo checkbox 行；重写 print loop 用 `---` 出现 2 次判定概览区结束。
**Lesson**: 日记 section 内嵌 `**字段**: 值` 是中英混排常见结构, 任何 markdown 解析器都要把 `**...**:` 单独归类，不能当 bullet。
