#!/bin/bash
# OpenClaw Gateway + Graphiti 健康检查脚本
# 只在异常时重启

LOG_FILE="/tmp/gateway_health_check.log"
GATEWAY_PID=$(pgrep -f "openclaw-gateway" | head -1)
GATEWAY_PORT=18789

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> $LOG_FILE

ISSUES=""

# 检查1: Gateway进程是否存在
if [ -z "$GATEWAY_PID" ]; then
    echo "❌ Gateway进程不存在，尝试启动..." >> $LOG_FILE
    
    pkill -9 -f openclaw-gateway 2>/dev/null || true
    sleep 1
    
    cd /home/liujerry/moltbot
    nohup pnpm openclaw gateway run --bind loopback --port $GATEWAY_PORT --force > /tmp/openclaw-gateway.log 2>&1 &
    
    sleep 5
    
    if pgrep -f "openclaw-gateway" > /dev/null; then
        echo "✅ Gateway已重新启动" >> $LOG_FILE
    else
        echo "❌ Gateway启动失败" >> $LOG_FILE
        ISSUES="$ISSUES;Gateway启动失败"
    fi
fi

# 检查2: Gateway端口是否响应
if ! ss -ltnp 2>/dev/null | grep -q ":$GATEWAY_PORT " && ! netstat -ltnp 2>/dev/null | grep -q ":$GATEWAY_PORT "; then
    echo "⚠️ Gateway进程存在但端口无响应，尝试重启..." >> $LOG_FILE
    
    pkill -9 -f openclaw-gateway 2>/dev/null || true
    sleep 2
    
    cd /home/liujerry/moltbot
    nohup pnpm openclaw gateway run --bind loopback --port $GATEWAY_PORT --force > /tmp/openclaw-gateway.log 2>&1 &
    
    sleep 5
    
    if pgrep -f "openclaw-gateway" > /dev/null; then
        echo "✅ Gateway已重新启动" >> $LOG_FILE
    else
        echo "❌ Gateway启动失败" >> $LOG_FILE
        ISSUES="$ISSUES;Gateway端口无响应"
    fi
fi

# 检查3: Gateway健康检查API
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$GATEWAY_PORT/health 2>/dev/null || echo "000")
if [ "$HEALTH" != "200" ]; then
    echo "⚠️ Gateway健康检查失败(HTTP $HEALTH)" >> $LOG_FILE
    ISSUES="$ISSUES;Gateway健康检查失败(HTTP $HEALTH)"
fi

# 检查4: Graphiti API
GRAPHITI=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthcheck 2>/dev/null || echo "000")
if [ "$GRAPHITI" != "200" ]; then
    echo "⚠️ Graphiti API异常(HTTP $GRAPHITI)" >> $LOG_FILE
    ISSUES="$ISSUES;Graphiti异常(HTTP $GRAPHITI)"
    
    # 尝试重启 Graphiti worker
    pkill -f 'graph_service/main.py' 2>/dev/null || true
    sleep 1
    cd /home/liujerry/graphiti && nohup /usr/bin/python3 server/graph_service/main.py > /tmp/graphiti.log 2>&1 &
    sleep 3
fi

# 检查5: Neo4j
NEO4J=$(docker ps --filter "name=neo4j" --filter "status=running" -q 2>/dev/null)
if [ -z "$NEO4J" ]; then
    echo "⚠️ Neo4j未运行" >> $LOG_FILE
    ISSUES="$ISSUES;Neo4j未运行"
    
    # 尝试启动 Neo4j
    docker start neo4j 2>/dev/null || true
    sleep 5
fi

# 输出状态
GATEWAY_STATUS="✅"
if [ -n "$ISSUES" ]; then
    echo "⚠️ 发现问题:$ISSUES" >> $LOG_FILE
    GATEWAY_STATUS="⚠️"
fi

echo "✅ Gateway运行正常 (PID: $GATEWAY_PID)" >> $LOG_FILE
echo "✅ Graphiti: HTTP $GRAPHITI" >> $LOG_FILE
echo "✅ Neo4j: $([ -n "$NEO4J" ] && echo '运行中' || echo '未运行')" >> $LOG_FILE

# 输出简洁状态
if [ -n "$ISSUES" ]; then
    echo "⚠️ 发现问题:$ISSUES"
else
    echo "✅ Gateway+Graphiti 运行正常"
fi
