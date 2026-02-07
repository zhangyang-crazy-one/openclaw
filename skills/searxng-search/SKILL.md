---
name: searxng-search
version: 2.0.0
description: 综合学术搜索引擎 - 多源聚合高质量数据
---

# 综合学术搜索引擎

聚合多个高质量学术数据源和搜索引擎，获取最全面的研究资料。

## 学术数据源

| 源 | 类型 | 特点 | API |
|---|---|---|---|
| **Semantic Scholar** | AI 学术 | 高引用论文, 被引数, Open Access PDF | ✅ |
| **arXiv** | 预印本 | 最新 AI/ML 论文 | ✅ |
| **Crossref** | 期刊 | 同行评审论文, DOI | ✅ |
| **OpenAlex** | 开放学术 | 开放获取, 机构数据 | ✅ |
| **PubMed** | 生物医学 | 医学/生命科学 | ⚠️ |
| **ar5iv** | 论文全文 | arXiv 论文 HTML 全文 | ✅ |

## 搜索引擎

| 引擎 | 类型 | 特点 |
|---|---|---|
| **DuckDuckGo** | 通用 | 隐私保护, 无追踪 |
| **Bing** | 通用 | 高质量结果 (via SearXNG) |
| **Brave** | 通用 | 需要 API Key |

## 使用方法

```bash
# 默认：学术搜索模式
python3 academic_search.py --query "transformer architecture"

# 指定数据源
python3 academic_search.py --query "AI governance" --sources arxiv,semantic_scholar

# JSON 输出
python3 academic_search.py --query "machine learning" --json --save

# 通用搜索
python3 academic_search.py --query "最新科技新闻"
```

## 数据源说明

### Semantic Scholar (推荐)
- AI 领域最专业的学术搜索
- 提供引用数、被引网络
- 自动标记 Open Access 论文
- 权重: ⭐⭐⭐

### arXiv
- AI/ML 预印本首发平台
- 最新研究成果
- 权重: ⭐⭐

### Crossref
- DOI 注册机构
- 同行评审期刊论文
- 权重: ⭐⭐

### OpenAlex
- 开放学术知识图谱
- 开放获取论文优先
- 权重: ⭐⭐

## 搜索结果排序

结果按以下优先级排序：
1. 数据源权重 (Semantic Scholar > arXiv > Crossref > OpenAlex)
2. 引用数
3. 发表时间

## 配置

### 启用/禁用数据源

编辑脚本中的 `ACADEMIC_SOURCES` 字典：

```python
ACADEMIC_SOURCES = {
    "semantic_scholar": {"enabled": True, "weight": 3},
    "arxiv": {"enabled": True, "weight": 2},
    "crossref": {"enabled": True, "weight": 2},
    "openalex": {"enabled": True, "weight": 2},
}
```

### 启用 Brave Search (需要 API Key)

```python
SEARCH_ENGINES = {
    "brave": {
        "url": "https://api.search.brave.com/res/v1/search",
        "enabled": True,
        "api_key": "YOUR_BRAVE_API_KEY",
    }
}
```

## 输出格式

结果保存至 `~/.config/deepseeker/searches/`

```json
{
  "query": "AI governance",
  "type": "academic",
  "count": 20,
  "results": [
    {
      "title": "论文标题",
      "authors": ["作者1", "作者2"],
      "year": "2024",
      "citations": 150,
      "url": "https://...",
      "engine": "Semantic Scholar",
      "pdf": "https://..."
    }
  ]
}
```
