#!/bin/bash
# 启动 Graphiti API 服务

set -e

GRAPHTI_DIR="${1:-/home/liujerry/graphiti}"
PORT="${2:-8001}"

echo "🚀 启动 Graphiti API..."
echo "   目录: $GRAPHTI_DIR"
echo "   端口: $PORT"

# 停止旧进程
pkill -f "uvicorn.*$PORT" 2>/dev/null || true

# 设置环境变量
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-4fb2a13f0a10417189b1b182f3dffc47}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.deepseek.com/v1}"
export OPENAI_MODEL="${OPENAI_MODEL:-deepseek-chat}"
export OPENAI_EMBEDDING_BASE_URL="${OPENAI_EMBEDDING_BASE_URL:-http://localhost:11434}"
export OPENAI_EMBEDDING_MODEL="${OPENAI_EMBEDDING_MODEL:-embeddinggemma:300m}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-graphiti_memory_2026}"

# 启动
cd "$GRAPHTI_DIR"
source .venv/bin/activate
export PYTHONPATH="$GRAPHTI_DIR/server:$PYTHONPATH"

nohup python3 -m uvicorn graph_service.main:app --host 0.0.0.0 --port $PORT > /tmp/graphiti-api.log 2>&1 &
PID=$!

echo "   PID: $PID"

# 等待启动
sleep 5

# 检查
if curl -s http://localhost:$PORT/healthcheck > /dev/null 2>&1; then
    echo "✅ Graphiti API 启动成功!"
    echo "   URL: http://localhost:$PORT"
else
    echo "❌ 启动失败，检查日志: tail /tmp/graphiti-api.log"
    exit 1
fi
