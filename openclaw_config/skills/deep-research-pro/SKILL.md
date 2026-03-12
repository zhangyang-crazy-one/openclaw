---
name: deep-research-pro
version: 1.4.0
description: "Multi-source deep research agent using SearXNG (Docker) and Tavily"
metadata: { "clawdbot": { "emoji": "🔬", "category": "research" } }
---

# Deep Research Pro 🔬

深度研究技能，使用 SearXNG (Docker) 和 Tavily 进行多源搜索。

## 支持的搜索源

### 📚 学术搜索 (SearXNG Docker)

| 源               | 用途        | 命令                         |
| ---------------- | ----------- | ---------------------------- |
| arXiv            | AI/ML预印本 | `--engines arxiv`            |
| Semantic Scholar | 学术论文    | `--engines semantic_scholar` |
| Google Scholar   | 学术搜索    | `--engines google_scholar`   |
| Crossref         | 文献        | `--engines crossref`         |
| PubMed           | 生物医学    | `--engines pubmed`           |
| GitHub           | 代码        | `--engines github`           |

### 🌐 通用搜索 (SearXNG)

| 源        | 用途     |
| --------- | -------- |
| Brave     | 隐私搜索 |
| Wikipedia | 百科     |

### 📰 新闻搜索 (Tavily)

```bash
cd ~/moltbot/skills/tavily-search/scripts
python3 tavily_search.py "关键词" 5
```

## 搜索命令

### 学术论文搜索

```bash
cd /home/liujerry/moltbot/skills/searxng-search/scripts

# AI/ML 论文 (arXiv)
python3 searxng_search.py "transformer attention mechanism" --engines arxiv --max 15

# 学术论文 (Semantic Scholar)
python3 searxng_search.py "large language model reasoning" --engines semantic_scholar --max 10

# Google Scholar
python3 searxng_search.py "artificial intelligence healthcare" --engines google_scholar --max 10

# 代码搜索
python3 searxng_search.py "python machine learning framework" --engines github --max 10
```

### 新闻搜索

```bash
cd /home/liujerry/moltbot/skills/tavily-search/scripts
python3 tavily_search.py "中国重要新闻 2025" 5
python3 tavily_search.py "AI news 2025" 5
```

### 通用搜索

```bash
python3 searxng_search.py "关键词" --max 10
```

## 研究工作流

1. **理解目标** - 确认用户想要什么
2. **规划子问题** - 分解为3-5个研究问题
3. **执行搜索** - 使用合适的搜索源
4. **深度阅读** - 获取关键URL的完整内容
5. **整合报告** - 结构化输出

## 报告格式

```markdown
# [主题]: 深度研究报告

_生成时间: [日期] | 来源: [N]_

## 执行摘要

[关键发现概述]

## 1. [主要主题1]

- 关键点 [来源](url)

## 2. [主要主题2]

- 关键点 [来源](url)

## 关键要点

- 可操作见解

## 来源

1. [标题](url)
```

## 质量规则

1. 每个断言需要来源
2. 交叉验证多个来源
3. 优先选择新近来源（12个月内）
4. 承认信息缺口
5. 不幻觉
