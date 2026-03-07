# SearXNG Search - 多源学术搜索

基于 Docker 的 SearXNG 搜索服务，支持多种学术和通用搜索源。

## 配置的搜索源

### 📚 学术搜索

| 源               | 用途       | 命令参数                  |
| ---------------- | ---------- | ------------------------- |
| arXiv            | 预印本论文 | `engine:arxiv`            |
| Semantic Scholar | 学术论文   | `engine:semantic_scholar` |
| Google Scholar   | 学术搜索   | `engine:google_scholar`   |
| Crossref         | 学术文献   | `engine:crossref`         |
| PubMed           | 生物医学   | `engine:pubmed`           |

### 🌐 通用搜索

| 源        | 用途     |
| --------- | -------- |
| Brave     | 隐私搜索 |
| GitHub    | 代码搜索 |
| Wikipedia | 百科     |

## 使用方法

### 基本搜索

```bash
# 通用搜索
curl "http://localhost:8080/search?q=关键词&format=json"

# 指定数量
curl "http://localhost:8080/search?q=AI&format=json&max_results=10"
```

### 学术论文搜索

```bash
# arXiv 论文
curl "http://localhost:8080/search?q=machine+learning+transformer+arxiv&format=json&engines=arxiv"

# Semantic Scholar
curl "http://localhost:8080/search?q=deep+learning&format=json&engines=semantic_scholar"

# Google Scholar
curl "http://localhost:8080/search?q=artificial+intelligence&format=json&engines=google_scholar"
```

### 使用 Python 脚本

```bash
cd /home/liujerry/moltbot/skills/searxng-search/scripts
python3 searxng_search.py --query "machine learning" --engines arxiv semantic_scholar --max 10
```

## 参数说明

| 参数          | 说明         | 示例                   |
| ------------- | ------------ | ---------------------- |
| `q`           | 搜索关键词   | `q=deep+learning`      |
| `format`      | 输出格式     | `format=json`          |
| `max_results` | 最大结果数   | `max_results=20`       |
| `engines`     | 指定搜索引擎 | `engines=arxiv,github` |
| `categories`  | 指定类别     | `categories=science`   |
| `language`    | 结果语言     | `language=zh`          |

## 学术搜索示例

### 搜索最新AI论文

```bash
curl "http://localhost:8080/search?q=transformer+attention+mechanism&format=json&engines=arxiv&max_results=15"
```

### 搜索Semantic Scholar

```bash
curl "http://localhost:8080/search?q=large+language+model+reasoning&format=json&engines=semantic_scholar&max_results=10"
```

### 搜索GitHub代码

```bash
curl "http://localhost:8080/search?q=python+machine+learning&format=json&engines=github&max_results=10"
```

## Docker 服务

- **容器**: searxng/searxng:latest
- **端口**: 8080
- **健康检查**: http://localhost:8080/health

## 依赖

- Python 3
- requests (可选)
- Docker + SearXNG 容器
