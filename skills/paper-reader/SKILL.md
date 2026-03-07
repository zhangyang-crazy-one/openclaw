# Paper Reader - 论文阅读助手 (优化版 v2.0)

自动从 arXiv、Semantic Scholar 获取论文并进行 AI 总结，生成专业的论文笔记和美观 PDF 报告。

## 功能

- 📥 **自动获取论文** - 从 arXiv 抓取最新论文
- 🤖 **AI 摘要生成** - 使用 Minimax API 生成结构化摘要
- 📝 **专业笔记格式** - 支持 Markdown/Obsidian/PDF 多格式输出
- 🏷️ **智能标签** - 自动识别论文领域
- 💾 **缓存机制** - 7 天 TTL 避免重复获取
- 📄 **美观 PDF 导出** - 专业学术报告布局

## 目录结构

```
paper-reader/
├── SKILL.md              # 本文档
├── main.py               # 入口
├── requirements.txt      # 依赖
├── pdf_generator.py      # PDF生成模块 (新增)
└── scripts/
    └── main.py          # 主逻辑
```

## 使用方法

```bash
# 基本用法
python main.py --topic "LLM agent" --limit 3

# 输出 PDF 报告 (推荐)
python main.py --topic "AI governance" --format pdf

# 输出 Obsidian 格式
python main.py --topic "AI governance" --format obsidian

# 强制刷新
python main.py --topic "AI" --no-cache
```

## 参数

| 参数         | 简写 | 默认值    | 说明                             |
| ------------ | ---- | --------- | -------------------------------- |
| `--topic`    | `-t` | AI        | 论文主题                         |
| `--source`   | `-s` | arxiv     | 数据源                           |
| `--limit`    | `-l` | 3         | 数量                             |
| `--format`   | `-f` | markdown  | 输出格式 (markdown/obsidian/pdf) |
| `--no-cache` |      | false     | 强制刷新                         |
| `--output`   | `-o` | ~/.cache/ | 输出目录                         |

## PDF 报告格式 (v2.0 核心)

### 页面布局

```
┌─────────────────────────────────────────────┐
│  [页眉] 论文标题          [页码]             │
├─────────────────────────────────────────────┤
│                                             │
│  ████ 论文标题 (大号加粗) ████              │
│     作者: Author1, Author2...                │
│     arXiv: xxxx.xxxxx                       │
│     发表日期: YYYY-MM-DD                    │
│                                             │
├─────────────────────────────────────────────┤
│  📌 TL;DR (一句话总结)                       │
│     "核心发现的简要描述"                     │
├─────────────────────────────────────────────┤
│                                             │
│  摘要 (Abstract)                            │
│  ─────────────────                          │
│  详细摘要内容...                             │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  🎯 核心贡献                                │
│  ─────────────                              │
│  1. 贡献一                                   │
│  2. 贡献二                                   │
│  3. 贡献三                                   │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  🔧 方法论                                   │
│  ─────────                                  │
│  技术细节描述...                             │
│                                             │
│  [方法流程图占位]                           │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  📊 实验结果                                 │
│  ────────────                               │
│                                             │
│  ┌─────────────┬────────┬────────┐         │
│  │ Dataset     │ Acc    │ F1     │         │
│  ├─────────────┼────────┼────────┤         │
│  │ Train       │ 95.2%  │ 0.91   │         │
│  │ Test        │ 93.8%  │ 0.89   │         │
│  └─────────────┴────────┴────────┘         │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  💡 个人笔记 / 思考                          │
│  ─────────────────────                      │
│  [空白区域用于手写/记录想法]                  │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  🔗 相关论文 / 参考文献                      │
│  ─────────────────────────                  │
│  • 相关论文1                                 │
│  • 相关论文2                                 │
│                                             │
└─────────────────────────────────────────────┘
```

### 配色方案

```python
# 学术风格配色
COLORS = {
    'primary': '#1a365d',        # 深蓝色 - 标题
    'secondary': '#2c5282',       # 中蓝色 - 子标题
    'accent': '#3182ce',          # 亮蓝色 - 强调
    'text': '#2d3748',            # 深灰 - 正文
    'light_text': '#718096',      # 浅灰 - 次要文字
    'background': '#ffffff',       # 白色 - 背景
    'light_bg': '#f7fafc',        # 浅灰 - 区块背景
    'border': '#e2e8f0',          # 边框灰
    'success': '#38a169',         # 绿色 - 成功/贡献
    'warning': '#d69e2e',         # 黄色 - 警告/注意
}
```

### 字体方案

```python
# 字体配置
FONTS = {
    'title': ('Helvetica-Bold', 18),      # 标题
    'subtitle': ('Helvetica-Bold', 14),    # 子标题
    'heading': ('Helvetica-Bold', 12),     # 章节标题
    'body': ('Helvetica', 10),              # 正文
    'small': ('Helvetica', 8),             # 小字/引用
    'code': ('Courier', 9),                 # 代码
}
```

### 元素样式

1. **标题样式**
   - 主标题: 18pt 深蓝 加粗
   - 子标题: 14pt 深蓝 加粗
   - 章节标题: 12pt 深灰 加粗 下划线

2. **卡片样式**
   - 背景: #f7fafc
   - 边框: 1px solid #e2e8f0
   - 圆角: 3px
   - 内边距: 10px

3. **表格样式**
   - 表头: 深蓝背景 白字
   - 斑马纹: 奇数行 #f7fafc
   - 边框: #e2e8f0

4. **引用块**
   - 左边框: 3px solid #3182ce
   - 背景: #ebf8ff
   - 斜体文字

### PDF 页面设置

```python
# 页面配置
PAGE_CONFIG = {
    'format': 'A4',
    'orientation': 'portrait',
    'unit': 'mm',
    'margin_top': 20,
    'margin_bottom': 20,
    'margin_left': 20,
    'margin_right': 20,
}
```

## Markdown 格式

### 基础输出

```markdown
# 论文标题

> **TL;DR**  
> 一句话总结

---

## 摘要

...

## 核心贡献

1. 贡献1
2. 贡献2

## 关键要点

- 要点1
- 要点2

## 标签

#AI #MachineLearning #Paper
```

### Obsidian 格式 (增强)

包含 YAML frontmatter、双向链接、标签

```yaml
---
title: "论文标题"
authors: ["Author1", "Author2"]
date: "2025-01-01"
tags: [AI, ML]
arxiv: "xxxx.xxxxx"
type: paper-note
---
# 论文标题
...
```

## 环境变量

```bash
export MINIMAX_API_KEY=your_key
export MINIMAX_BASE_URL=https://api.minimaxi.com/anthropic/v1
export MINIMAX_MODEL=MiniMax-M2.5
```

## 数据源

- **arXiv**：免费，cs.AI/cs.LG 等
- **Semantic Scholar**：需要 API key

## 缓存

位置：`~/.cache/paper-reader/`
TTL：7 天

## 触发词

- "获取最新论文"
- "总结这篇论文"
- "论文晨读"
- "分析这篇论文"
- "生成论文PDF"
- "导出论文报告"

## 依赖

```
requests>=2.31.0
xmltodict>=0.13.0
fpdf>=1.7.2
```

## PDF 生成示例

```python
from pdf_generator import PaperPDFGenerator

generator = PaperPDFGenerator()

# 单篇论文
paper_data = {
    'title': '论文标题',
    'authors': ['Author1', 'Author2'],
    'arxiv_id': '2501.00001',
    'published': '2025-01-01',
    'tldr': '一句话总结',
    'abstract': '详细摘要...',
    'contributions': ['贡献1', '贡献2', '贡献3'],
    'key_points': ['要点1', '要点2'],
    'method': '方法描述...',
    'results': {...},
    'notes': '个人笔记...',
}

generator.generate_single(paper_data, 'output.pdf')
generator.generate_report([paper_data, ...], 'multi_papers.pdf')
```

## 更新日志

### v2.0 (2026-03-05)

- ✨ 新增美观 PDF 报告生成
- 🎨 专业学术配色方案
- 📐 清晰的页面布局和层次
- 📊 优化的表格和卡片样式
- 💡 新增个人笔记区域
