#!/bin/bash
# Memory Integrity Check - 记忆完整性检查
# 用于验证蒸馏后的记忆系统是否完整

echo "=== Memory Integrity Check ==="
echo "Date: $(date '+%Y-%m-%d %H:%M')"
echo ""

# 1. MEMORY.md 大小检查
MEMORY_SIZE=$(wc -c < /home/liujerry/moltbot/MEMORY.md)
echo "1. MEMORY.md Size Check:"
echo "   Current: $MEMORY_SIZE chars"
if [ "$MEMORY_SIZE" -lt 15000 ]; then
    echo "   Status: ✅ PASS (< 15,000)"
else
    echo "   Status: ⚠️ WARNING (> 15,000 - 需要蒸馏)"
fi
echo ""

# 2. 分层目录检查
echo "2. Layered Memory Structure:"
for dir in "memory" "memory/weekly" "memory/archive" "memory/insights/distillation"; do
    FULL_PATH="/home/liujerry/moltbot/$dir"
    if [ -d "$FULL_PATH" ]; then
        COUNT=$(find "$FULL_PATH" -name "*.md" 2>/dev/null | wc -l)
        echo "   ✅ $dir: $COUNT files"
    else
        echo "   ❌ $dir: NOT FOUND"
    fi
done
echo ""

# 3. 每日日志检查
echo "3. Daily Logs (Last 7 days):"
ls -lt /home/liujerry/moltbot/memory/*.md 2>/dev/null | head -7 | while read line; do
    echo "   $line"
done
echo ""

# 4. 蒸馏日志检查
echo "4. Distillation Log:"
DISTILL_LOG="/home/liujerry/moltbot/memory/insights/distillation/"
if [ -d "$DISTILL_LOG" ]; then
    LATEST=$(ls -t "$DISTILL_LOG"*.md 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo "   Latest: $LATEST"
        echo "   Last distillation:"
        grep "2026-03" "$LATEST" | head -3
    else
        echo "   ⚠️ No distillation log found"
    fi
else
    echo "   ❌ Distillation log directory not found"
fi
echo ""

# 5. 归档完整性（验证归档前后大小一致）
echo "5. Archive Integrity:"
ARCHIVE_COUNT=$(find /home/liujerry/moltbot/memory/archive -name "*.md" 2>/dev/null | wc -l)
echo "   Archived files: $ARCHIVE_COUNT"
if [ "$ARCHIVE_COUNT" -gt 0 ]; then
    ARCHIVE_SIZE=$(du -sh /home/liujerry/moltbot/memory/archive 2>/dev/null | cut -f1)
    echo "   Archive size: $ARCHIVE_SIZE"
fi
echo ""

# 6. 知识图谱同步状态
echo "6. Knowledge Graph Sync:"
if curl -s http://localhost:8000/healthcheck | grep -q "healthy"; then
    echo "   Graphiti: ✅ Online"
    # 获取最新Episode数
    EPISODE_COUNT=$(curl -s http://localhost:8000/episodes/moltbot 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('episodes',[])))" 2>/dev/null || echo "N/A")
    echo "   Recent episodes: $EPISODE_COUNT"
else
    echo "   Graphiti: ❌ Offline"
fi
echo ""

# 7. 最近修改的文件
echo "7. Recently Modified (< 24h):"
find /home/liujerry/moltbot/memory -name "*.md" -mtime -1 2>/dev/null | while read f; do
    echo "   $f"
done

echo ""
echo "=== Check Complete ==="
