---
name: graphiti-memory
version: 2.1.0
description: Graphiti 知识图谱记忆系统 - 集成 DeepSeek + Ollama
---

# Graphiti Memory (v2.1)

Graphiti 知识图谱记忆系统，支持时序事实存储和语义搜索。

## 当前状态 ✅

| 组件 | 状态 | 版本 |
|------|------|------|
| Neo4j | ✅ 运行中 | 5.26.0 |
| Graphiti API | ✅ healthy | /home/liujerry/graphiti/ |
| DeepSeek LLM | ✅ JSON mode | deepseek-chat |
| Ollama Embedding | ✅ 768维 | embeddinggemma:300m |
| Worker | ✅ 后台运行 | 处理消息队列 |
| fulltext 索引 | ✅ ONLINE | node + edge |

## 数据统计

| 类型 | 数量 |
|------|------|
| Episodic | 14 |
| Entity | 97 |
| Relations | 处理中 |

## 快速启动

```bash
# 1. 确保 Neo4j 运行
docker ps | grep neo4j || docker run -d --name neo4j \
  -v neo4j_data:/data \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphiti_memory_2026 \
  neo4j:5.26.0

# 2. 创建 fulltext 索引 (首次)
docker exec neo4j cypher-shell -u neo4j -p graphiti_memory_2026 "
CREATE FULLTEXT INDEX node_name_and_summary FOR (n:Entity) ON EACH [n.name, n.summary];
CREATE FULLTEXT INDEX edge_name_and_fact FOR ()-[r:RELATES_TO]-() ON EACH [r.name, r.fact];
"

# 3. 启动 Graphiti (使用 uv)
cd /home/liujerry/graphiti/server
source ../.env
uv run uvicorn graph_service.main:app --host 0.0.0.0 --port 8000
```

## 环境变量

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphiti_memory_2026

# DeepSeek (LLM)
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# Ollama (Embedding)
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=embeddinggemma:300m
```

## API 使用

```bash
# 健康检查
curl http://localhost:8000/healthcheck

# 添加消息 (自动提取实体)
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "openclaw-main",
    "messages": [{"content": "内容...", "role_type": "user", "role": "user"}]
  }'

# 搜索
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "关键词", "group_ids": ["openclaw-main"]}'
```

## Python 使用

```python
import asyncio
from graphiti_core import Graphiti
from graphiti_core.embedder.ollama import OllamaEmbedder, OllamaEmbedderConfig

async def add_memory():
    embedder = OllamaEmbedder(
        config=OllamaEmbedderConfig(
            embedding_model="embeddinggemma:300m",
            base_url="http://localhost:11434",
        )
    )
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="graphiti_memory_2026",
        embedder=embedder,
    )
    
    await graphiti.add_episode(
        group_id="openclaw-main",
        name="memory: filename.md",
        episode_body="内容...",
        source=EpisodeType.text,
    )
    
    await graphiti.close()

asyncio.run(add_memory())
```

## 故障排除

### Neo4j 未运行
```bash
docker start neo4j
sleep 120  # 等待启动
```

### Graphiti 无法启动
```bash
# 检查端口
netstat -tlnp | grep 8000

# 查看日志
tail -50 /tmp/graphiti.log

# 重启
pkill -f uvicorn
cd /home/liujerry/graphiti/server && source ../.env && uv run uvicorn graph_service.main:app
```

### 消息未处理
```bash
# 检查 worker 日志
tail -100 /tmp/graphiti.log | grep -i worker

# 重新添加消息
curl -X POST http://localhost:8000/messages -d '...'
```

## 文件位置

- Graphiti 源码: `/home/liujerry/graphiti/`
- 技能配置: `/home/liujerry/moltbot/skills/graphiti-memory/`
- Memory 文件: `/home/liujerry/moltbot/memory/`
- 日志: `/tmp/graphiti.log`

## 来源

- Graphiti: https://github.com/getzep/graphiti
- DeepSeek: https://api.deepseek.com
- Ollama: https://ollama.com
