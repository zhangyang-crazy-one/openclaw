---
name: acp-claude-code
description: 通过 acpx 调用 Claude Code 进行复杂任务，支持 Skill-Driven 工作流（分析→分解→技能匹配→执行→验证）。核心：先检查可用技能，再决定执行策略。触发词：Claude Code 生成PPT、acp调用claude、Claude Code 任务。
user-invocable: true
---

# ACP Claude Code 技能

通过 acpx 协议调用 Claude Code，支持 Skill-Driven 开发流程。

---

## 📚 技能与插件索引

### MiniMax Skills (pptx-plugin)

路径: `~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/`

| 技能                    | 文件                           | 用途                                    |
| ----------------------- | ------------------------------ | --------------------------------------- |
| **ppt-orchestra-skill** | `ppt-orchestra-skill/SKILL.md` | PPT整体规划、结构设计、布局规划         |
| **slide-making-skill**  | `slide-making-skill/SKILL.md`  | 单页幻灯片实现、PptxGenJS代码生成       |
| **color-font-skill**    | `color-font-skill/SKILL.md`    | 配色方案、字体搭配选择                  |
| **design-style-skill**  | `design-style-skill/SKILL.md`  | 视觉风格设计（Sharp/Soft/Rounded/Pill） |
| **ppt-editing-skill**   | `ppt-editing-skill/SKILL.md`   | 编辑现有PPT模板、XML安全工作流          |

### Claude Code 内置技能

路径: `~/.claude/skills/`

#### 开发类

| 技能                   | 用途            |
| ---------------------- | --------------- |
| **ship**               | 快速交付功能    |
| **plan-ceo-review**    | CEO视角审查计划 |
| **plan-design-review** | 设计审查        |
| **plan-eng-review**    | 工程审查        |

#### 代码类

| 技能                    | 用途     |
| ----------------------- | -------- |
| **review**              | 代码审查 |
| **qa**                  | QA测试   |
| **qa-only**             | 仅QA     |
| **design-consultation** | 设计咨询 |
| **design-review**       | 设计审查 |

#### 研究类

| 技能                         | 用途     |
| ---------------------------- | -------- |
| **academic-research-skills** | 学术研究 |
| **investigate**              | 深度调查 |

#### 部署类

| 技能                      | 用途             |
| ------------------------- | ---------------- |
| **land-and-deploy**       | 部署上线         |
| **setup-deploy**          | 部署配置         |
| **setup-browser-cookies** | 浏览器Cookie设置 |

#### 实验性

| 技能                 | 用途         |
| -------------------- | ------------ |
| **autoplan**         | 自动规划     |
| **gstack**           | GStack集成   |
| **gstack-upgrade**   | GStack升级   |
| **benchmark**        | 性能基准测试 |
| **canary**           | 金丝雀发布   |
| **codex**            | Codex集成    |
| **careful**          | 谨慎模式     |
| **document-release** | 文档发布     |
| **freeze**           | 冻结         |
| **guard**            | 防护         |
| **office-hours**     | 办公时间     |
| **retro**            | 回顾         |
| **unfreeze**         | 解冻         |

### Claude Code 官方插件

路径: `~/.claude/settings.json` 中的 `enabledPlugins`

| 插件                   | 用途              |
| ---------------------- | ----------------- |
| **code-review**        | 代码审查          |
| **code-simplifier**    | 代码简化          |
| **commit-commands**    | Git提交命令       |
| **context7**           | Context7集成      |
| **feature-dev**        | 功能开发          |
| **frontend-design**    | 前端设计          |
| **github**             | GitHub集成        |
| **hookify**            | Hook管理          |
| **huggingface-skills** | HuggingFace技能   |
| **plugin-dev**         | 插件开发          |
| **pyright-lsp**        | Pyright LSP       |
| **ralph-loop**         | Ralph循环         |
| **rust-analyzer-lsp**  | Rust Analyzer LSP |
| **slack**              | Slack集成         |
| **typescript-lsp**     | TypeScript LSP    |

---

## 核心流程

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: 分析与分解                                    │
│  - 分析任务类型和复杂度                                  │
│  - 分解为子任务                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 2: 技能发现 (必须在此阶段检查!)                   │
│  - 列出可用技能和插件                                    │
│  - 阅读技能文档                                         │
│  - 匹配技能到子任务                                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: 执行策略决策                                   │
│  - 判断：单 Claude Code vs Agent Team                   │
│  - 确定调用方式                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 4: 执行与监控                                     │
│  - 调用 acpx                                            │
│  - 监控进度                                             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 5: 验证                                          │
│  - 验证产物                                             │
│  - 检查质量                                             │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: 分析与分解

### 1.1 分析任务类型

| 任务类型     | 特征                   | 示例                   |
| ------------ | ---------------------- | ---------------------- |
| **简单任务** | 单一步骤，不需要多技能 | 问答题、简单代码片段   |
| **复杂任务** | 多步骤，需要多技能协调 | PPT生成、项目架构设计  |
| **批量任务** | 大量相似子任务         | 批量文件转换、数据处理 |
| **研究任务** | 需要深度调研           | 竞品分析、技术调研     |

### 1.2 分解任务

将任务分解为独立的子任务，每个子任务需要：

- 明确的输入/输出
- 需要的技能
- 依赖关系

**输出**: 任务分解表

| 子任务 | 输入     | 输出         | 需要技能            | 依赖 |
| ------ | -------- | ------------ | ------------------- | ---- |
| T1     | 需求文档 | PPT结构规划  | ppt-orchestra-skill | 无   |
| T2     | PPT结构  | 幻灯片JS文件 | slide-making-skill  | T1   |
| T3     | JS文件   | 编译PPTX     | pptxgenjs           | T2   |

---

## Phase 2: 技能发现（必须执行）

**在调用 Claude Code 之前，必须先检查可用技能！**

### 2.1 检查可用技能

```bash
# 列出所有可用插件
ls ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/

# 列出特定插件的技能
ls ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/

# 列出 Claude Code 内置技能
ls ~/.claude/skills/
```

### 2.2 阅读技能文档

对于每个可能用到的技能，阅读其 SKILL.md：

```bash
# 示例：阅读 ppt-orchestra-skill
cat ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/ppt-orchestra-skill/SKILL.md

# 示例：阅读 slide-making-skill
cat ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/slide-making-skill/SKILL.md
```

### 2.3 技能匹配表

根据任务分解，将技能匹配到子任务：

| 子任务          | 技能                | 技能路径                | 用途                 |
| --------------- | ------------------- | ----------------------- | -------------------- |
| T1: PPT结构规划 | ppt-orchestra-skill | .../pptx-plugin/skills/ | 规划幻灯片类型和布局 |
| T2: 生成幻灯片  | slide-making-skill  | .../pptx-plugin/skills/ | 生成单页幻灯片代码   |
| T3: 编译PPTX    | pptxgenjs           | npm全局/本地            | 编译JS为PPTX         |

### 2.4 常用技能速查

#### PPT 相关

```
ppt-orchestra-skill     → 规划整个PPT结构
slide-making-skill      → 生成单页幻灯片
color-font-skill        → 配色和字体选择
design-style-skill      → 视觉风格设计
pptxgenjs               → 编译最终PPTX
```

#### Word 文档相关

```
docx-orchestra-skill    → 规划文档结构
slide-making-skill      → 生成章节内容
docxgenjs               → 编译最终DOCX
```

---

## Phase 3: 执行策略决策

### 3.1 判断标准

```
是否使用 Agent Team？
├── 子任务是否相互独立？
│   ├── 是 → 可并行 → 考虑 Agent Team
│   └── 否 → 必须串行 → 单 Claude Code
├── 任务复杂度？
│   ├── 高（需要多种技能）→ Agent Team
│   └── 低（单一技能）→ 单 Claude Code
└── 时间要求？
    ├── 紧急 → 单 Claude Code（启动快）
    └── 不紧急 → Agent Team（并行快）
```

### 3.2 策略选择

| 策略                         | 适用场景                | 调用方式                           |
| ---------------------------- | ----------------------- | ---------------------------------- |
| **单 Claude Code**           | 简单任务、串行依赖任务  | `acpx claude exec`                 |
| **Claude Code + 内置技能**   | 中等复杂度、需1-2种技能 | `acpx claude --session` + 技能路径 |
| **Claude Code + Agent Team** | 复杂任务、多技能并行    | Claude Code 内部 spawn subagents   |

### 3.3 Agent Team 使用条件

以下情况使用 Agent Team：

- 子任务可以并行执行
- 需要多种不同的技能
- 总任务量大，需要分工

**Claude Code Agent Team 结构**：

```
Claude Code (主控)
├── Agent 1: ppt-orchestra-skill → 规划PPT结构
├── Agent 2: slide-making-skill → 生成幻灯片 1-10
├── Agent 3: slide-making-skill → 生成幻灯片 11-20
├── Agent 4: slide-making-skill → 生成幻灯片 21-30
├── Agent 5: slide-making-skill → 生成幻灯片 31-40
└── 主控: 编译最终PPTX
```

---

## Phase 4: 执行与监控

### 4.1 调用模板

**关键：命令选项顺序**

```
acpx [全局选项] claude [子命令选项] [prompt]

全局选项（在 claude 之前）：
  --format json          # 输出格式
  --json-strict          # 严格JSON模式
  --cwd <dir>            # 工作目录
  --approve-all          # 自动批准所有权限
  --non-interactive-permissions deny  # 权限策略

子命令选项（claude 之后）：
  --session <name>       # 会话名称
  --no-wait              # 异步执行
  exec                   # 一次性执行
  prompt                 # 发送提示（默认）
```

#### 单 Claude Code（简单任务）

```bash
acpx claude exec "<任务描述>"
```

#### 单 Claude Code + 技能（中等任务）

```bash
SESSION="<project>-$(date +%Y%m%d%H%M)"
acpx claude sessions new --name $SESSION

acpx --cwd /home/liujerry/moltbot --approve-all --non-interactive-permissions deny claude --session $SESSION "
任务：<任务描述>

可用技能：
- <技能1路径>: <用途>
- <技能2路径>: <用途>

请使用上述技能完成任务。
"
```

#### Claude Code + Agent Team（复杂任务）

```bash
SESSION="<project>-$(date +%Y%m%d%H%M)"
acpx claude sessions new --name $SESSION

acpx --cwd /home/liujerry/moltbot --approve-all --non-interactive-permissions deny claude --session $SESSION "
任务：<复杂任务>

## 任务分解
- T1: <子任务1> → 使用 <技能A>
- T2: <子任务2> → 使用 <技能B>
- T3: <子任务3> → 使用 <技能C>

## 执行策略
使用 Agent Team并行执行：
1. 主控 Agent 规划整体结构
2. Subagents 并行生成各部分
3. 主控 Agent 编译最终产物

## 技能路径
- 技能A: <路径>
- 技能B: <路径>
- 技能C: <路径>

请使用 Agent Team 模式执行。
"
```

### 4.2 进度监控

```bash
# 检查进程
ps aux | grep acpx | grep $SESSION

# 检查产物
ls -la <output-dir>/ | tail -10

# 检查子任务进度
ls <output-dir>/*.js | wc -l
```

### 4.3 继续对话

```bash
acpx --cwd /home/liujerry/moltbot --approve-all --non-interactive-permissions deny claude --session $SESSION "<后续指令>"
```

### 4.4 关闭会话

```bash
acpx claude sessions close $SESSION
```

---

## Phase 5: 验证

### 5.1 产物验证

```bash
# 检查文件存在
[ -f "<output-file>" ] && echo "✅ 文件存在" || echo "❌ 文件不存在"

# 检查大小
FILE_SIZE=$(stat -c%s "<output-file>" 2>/dev/null || stat -f%z "<output-file>" 2>/dev/null)
[ $FILE_SIZE -gt 100000 ] && echo "✅ 大小正常 ($FILE_SIZE bytes)" || echo "⚠️ 文件过小"

# 检查数量
EXPECTED=40
ACTUAL=$(ls <output-dir>/*.js 2>/dev/null | wc -l)
[ $ACTUAL -ge $EXPECTED ] && echo "✅ 数量符合 ($ACTUAL/$EXPECTED)" || echo "⚠️ 数量不足"
```

### 5.2 质量验证

```bash
# 检查关键文件
for f in slide-01.js slide-02.js slide-40.js; do
    [ -f "<output-dir>/$f" ] && echo "✅ $f 存在" || echo "❌ $f 缺失"
done

# 检查编译日志
grep -i "error\|fail" <output-dir>/compile.log 2>/dev/null || echo "✅ 无编译错误"
```

---

## 完整工作流示例：GSD PPT

### Step 1: 分析与分解

**任务**: 生成 GSD 项目分析 PPT (40页)

**子任务分解**:

| ID  | 子任务           | 技能                | 依赖  |
| --- | ---------------- | ------------------- | ----- |
| T1  | 规划PPT结构      | ppt-orchestra-skill | 无    |
| T2  | 生成幻灯片 1-20  | slide-making-skill  | T1    |
| T3  | 生成幻灯片 21-40 | slide-making-skill  | T1    |
| T4  | 编译PPTX         | pptxgenjs           | T2+T3 |

### Step 2: 技能发现

```bash
# 检查 pptx-plugin 技能
ls ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/
# 输出: ppt-orchestra-skill/  slide-making-skill/  color-font-skill/  design-style-skill/

# 阅读 ppt-orchestra-skill
cat ~/.claude/.../pptx-plugin/skills/ppt-orchestra-skill/SKILL.md | head -50
```

### Step 3: 决策

**判断**:

- 任务复杂度：高（40页，多技能）
- 子任务独立性：T2和T3可并行
- **结论**: 使用 **Claude Code + Agent Team**

### Step 4: 执行

```bash
SESSION="gsd-ppt-$(date +%Y%m%d%H%M)"
acpx claude sessions new --name $SESSION

acpx --cwd /home/liujerry/moltbot --approve-all --non-interactive-permissions deny claude --session $SESSION "
任务：生成 GSD 项目分析 PPT (40页)

## 任务分解
- T1: 规划PPT结构（5个Section）→ ppt-orchestra-skill
- T2: 生成幻灯片 1-20 → slide-making-skill (Agent A)
- T3: 生成幻灯片 21-40 → slide-making-skill (Agent B)
- T4: 编译最终PPTX → pptxgenjs

## 执行策略
使用 Agent Team 并行：
1. 先用 ppt-orchestra-skill 规划整体结构
2. Spawn 2 个 subagents 并行生成幻灯片
3. 主控编译最终PPTX

## 技能路径
- ppt-orchestra-skill: ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/ppt-orchestra-skill/
- slide-making-skill: ~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/pptx-plugin/skills/slide-making-skill/

## 输出
- 工作目录: /home/liujerry/reports/gsd_pptx/
- 最终文件: /home/liujerry/reports/gsd_pptx_presentation.pptx

## 配色
primary: 22223b, secondary: 4a4e69, accent: 9a8c98 (深色主题)
"
```

### Step 5: 验证

```bash
# 检查PPTX
ls -lh /home/liujerry/reports/gsd_pptx_presentation.pptx

# 检查幻灯片数量
ls /home/liujerry/reports/gsd_pptx/slides/*.js | wc -l
```

---

## 关键规则

1. **Phase 2 不可跳过**: 调用 Claude Code 前必须先检查和匹配技能
2. **技能路径必须提供**: 给 Claude Code 的指令中要包含完整的技能路径
3. **根据复杂度选择策略**: 不要过度使用 Agent Team
4. **验证是最后一步**: 完成任务后必须验证产物

---

## 常用路径速查

| 资源                  | 路径                                                                   |
| --------------------- | ---------------------------------------------------------------------- |
| MiniMax Skills 根目录 | `~/.claude/plugins/cache/minimax-skills/minimax-skills/1.0.0/plugins/` |
| Claude Code 技能目录  | `~/.claude/skills/`                                                    |
| acpx 命令             | `acpx` (全局)                                                          |

| 技能                | 路径                                          |
| ------------------- | --------------------------------------------- |
| ppt-orchestra-skill | `.../pptx-plugin/skills/ppt-orchestra-skill/` |
| slide-making-skill  | `.../pptx-plugin/skills/slide-making-skill/`  |
| color-font-skill    | `.../pptx-plugin/skills/color-font-skill/`    |
| design-style-skill  | `.../pptx-plugin/skills/design-style-skill/`  |
