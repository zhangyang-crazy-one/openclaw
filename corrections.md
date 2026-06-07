## 2026-06-07 — weekly_insight_compiler.py section detection

**Bug**: Parser 把 `**时间**:` `**场景**:` 这类 bold-key 子项当成了问题列表项
(从 6 个"问题"虚增到 6 个全是 sub-bullet)；同时把 `- [ ] 待办` 误识别为洞察。
**Fix**: 过滤 bold-key 行 (`**X**: value`) 和 todo checkbox 行；重写 print loop 用 `---` 出现 2 次判定概览区结束。
**Lesson**: 日记 section 内嵌 `**字段**: 值` 是中英混排常见结构, 任何 markdown 解析器都要把 `**...**:` 单独归类，不能当 bullet。
