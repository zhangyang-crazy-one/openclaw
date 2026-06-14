# Corrections Log — Template

> This file is created in `~/self-improving/corrections.md` when you first use the skill.
> Keeps the last 50 corrections. Older entries are evaluated for promotion or archived.

## Entries

### 2026-06-11 00:13 — 夜间唤醒-加载记忆模式

- **Context**: Cron `dc180475-acd3-4ecf-8e58-3a4d5f087cdd` 触发,需读取 4 类核心记忆
- **Pattern**: 读 MEMORY.md + W\_周报 + 3个 insights + 今日/昨日日志,合并写入今日 daily journal
- **Action**: 写入 `memory/2026-06-11.md`,含 (a) 加载清单 (b) 用户偏好 (c) 本周探索成果 (d) KG/数据快照 (e) 自我检查 (f) 端午假期目标
- **Lesson**: self-improving `memory.md` 是模板文件,真实累积在 `corrections.md` + `reflections.md` + `MEMORY.md`,不要被模板格式误导
- **Count**: 1 (新模式,待观察是否复用)

## Example Entries (Template)

```markdown
## 2026-02-19

### 14:32 — Code style

- **Correction:** "Use 2-space indentation, not 4"
- **Context:** Editing TypeScript file
- **Count:** 1 (first occurrence)

### 16:15 — Communication

- **Correction:** "Don't start responses with 'Great question!'"
- **Context:** Chat response
- **Count:** 3 → **PROMOTED to memory.md**

## 2026-02-18

### 09:00 — Project: website

- **Correction:** "For this project, always use Tailwind"
- **Context:** CSS discussion
- **Action:** Added to projects/website.md
```

## Log Format

Each entry includes:

- **Timestamp** — When the correction happened
- **Correction** — What the user said
- **Context** — What triggered it
- **Count** — How many times (for promotion tracking)
- **Action** — Where it was stored (if promoted)
