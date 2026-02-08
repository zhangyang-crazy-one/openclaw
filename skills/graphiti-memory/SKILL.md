---
name: graphiti-memory
version: 1.0.1
description: Graphiti 知识图谱记忆系统 - 集成 DeepSeek + Ollama
---

# Graphiti Memory

Graphiti 知识图谱记忆系统，支持时序事实存储和语义搜索。

## ✅ 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| Neo4j | ✅ 运行中 | localhost:7687 |
| Graphiti API | ✅ 运行中 | localhost:8001 |
| DeepSeek LLM | ✅ 使用中 | JSON mode + schema |
| Ollama Embedding | ✅ 使用中 | embeddinggemma:300m |
| Episodes | ✅ 9 | 消息已存储 |
| Entities | ✅ 6 | 实体已提取 |
| Relations | ✅ 1 | 关系已创建 (DeepSeeker USES_FOR_PERSONALITY) |

## 🔧 已修复问题

### 1. DeepSeek LLM 客户端 (`deepseek_client.py`)
- 使用 `response_format={"type": "json_object"}` 确保 JSON 输出
- 添加 JSON schema 到 system prompt
- 返回格式兼容 `_handle_structured_response`

### 2. Ollama Embedder (`ollama_embedder.py`)
- 正确处理 Ollama API 格式: `{"embeddings": [[...]]}`
- `create_batch()` 返回完整 embeddings 列表

### 3. API 服务 (`zep_graphiti.py`)
- 正确创建 DeepSeekClient（基于 base_url/model 检测）
- Ollama embedder 使用 `embeddinggemma:300m` 模型

### 4. 驱动生命周期 (`neo4j_driver.py`)
- 禁用自动索引创建（后台任务导致 Driver closed 错误）
- 索引改为按需创建

## 快速启动

```bash
# 启动 Graphiti API
./scripts/start-graphiti.sh

# 检查状态
./scripts/status.sh

# 直接同步（推荐）
python3 scripts/graphiti-sync-direct.py
```

## 架构

```
OpenClaw Memory → Graphiti API → Neo4j
                        ↑
                   DeepSeek LLM (JSON mode)
                   Ollama Embedding (768维)
```

## 文件结构

```
scripts/
├── start-graphiti.sh      # 启动 Graphiti API
├── status.sh             # 检查状态和快速测试
├── sync-memory.py        # 同步 memory 目录
└── graphiti-sync-direct.py  # 直接同步（修复版）
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
# 添加消息到处理队列
curl -X POST http://localhost:8001/messages \
  -H "Content-Type: application/json" \
  -d '{"group_id": "my-group", "messages": [{"content": "...", "role_type": "user", "role": "assistant"}]}'

# 搜索
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "关键词", "group_ids": ["my-group"]}'
```

## 故障排除

### 搜索返回空结果
```bash
# 检查 EntityEdges 是否存在
curl "http://localhost:7474/db/neo4j/query/v2" \
  -H "Content-Type: application/json" \
  -u "neo4j:graphiti_memory_2026" \
  -d '{"statement": "MATCH ()-[e:RELATES_TO]->() RETURN count(e)"}'

# 如果为 0，尝试添加更多数据并等待处理
```

### Graphiti 无法启动
```bash
# 检查端口
netstat -tlnp | grep 8001

# 查看日志
tail -50 /tmp/graphiti-api.log
```

## 来源

- Graphiti: https://github.com/getzep/graphiti
- DeepSeek: https://api.deepseek.com
- Ollama: https://ollama.com
