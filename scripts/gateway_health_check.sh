#!/bin/bash
# OpenClaw Gateway 健康检查脚本
# 只在 Gateway 停止时重启，不无故重启

LOG_FILE="/tmp/gateway_health_check.log"
GATEWAY_PID=$(pgrep -f "openclaw-gateway" | head -1)
GATEWAY_PORT=18789

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> $LOG_FILE

# 检查1: Gateway进程是否存在
if [ -z "$GATEWAY_PID" ]; then
    echo "❌ Gateway进程不存在，尝试启动..." >> $LOG_FILE
    
    # 尝试启动 Gateway
    pkill -9 -f openclaw-gateway 2>/dev/null || true
    sleep 1
    
    cd /home/liujerry/moltbot
    nohup pnpm openclaw gateway run --bind loopback --port $GATEWAY_PORT --force > /tmp/openclaw-gateway.log 2>&1 &
    
    sleep 5
    
    # 验证是否启动成功
    if pgrep -f "openclaw-gateway" > /dev/null; then
        echo "✅ Gateway已重新启动" >> $LOG_FILE
    else
        echo "❌ Gateway启动失败" >> $LOG_FILE
    fi
    exit 0
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
    fi
    exit 0
fi

# 检查3: Gateway健康检查API
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$GATEWAY_PORT/health 2>/dev/null || echo "000")
if [ "$HEALTH" != "200" ]; then
    echo "⚠️ Gateway健康检查失败(HTTP $HEALTH)，尝试重启..." >> $LOG_FILE
    
    pkill -9 -f openclaw-gateway 2>/dev/null || true
    sleep 2
    
    cd /home/liujerry/moltbot
    nohup pnpm openclaw gateway run --bind loopback --port $GATEWAY_PORT --force > /tmp/openclaw-gateway.log 2>&1 &
    
    sleep 5
    
    if pgrep -f "openclaw-gateway" > /dev/null; then
        echo "✅ Gateway已重新启动" >> $LOG_FILE
    else
        echo "❌ Gateway启动失败" >> $LOG_FILE
    fi
    exit 0
fi

echo "✅ Gateway运行正常 (PID: $GATEWAY_PID)" >> $LOG_FILE
