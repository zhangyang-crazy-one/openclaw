#!/bin/bash
# Direct sync to Graphiti via curl - no python interpreter complexity
GRAPHITI_API="http://localhost:8000"
GROUP="moltbot"

sync_entity() {
    local name="$1"
    local summary="$2"
    local uuid=$(uuidgen 2>/dev/null || echo "$(date +%s)-$RANDOM")
    curl -s -X POST "$GRAPHITI_API/entity-node" \
        -H "Content-Type: application/json" \
        -d "{\"uuid\":\"$uuid\",\"group_id\":\"$GROUP\",\"name\":\"$name\",\"summary\":\"${summary:0:500}\"}" > /dev/null 2>&1
}

sync_messages() {
    local name="$1"
    local category="$2"
    local content="$3"
    local timestamp=$(date -Iseconds)
    
    # Create metadata + content as messages
    curl -s -X POST "$GRAPHITI_API/messages" \
        -H "Content-Type: application/json" \
        -d "{
            \"group_id\":\"$GROUP\",
            \"messages\":[
                {\"content\":\"file:$name\",\"role_type\":\"system\",\"role\":\"metadata\",\"timestamp\":\"$timestamp\",\"source_description\":\"file:$category\"},
                {\"content\":\"${content:0:4000}\",\"role_type\":\"user\",\"role\":\"memory\",\"timestamp\":\"$timestamp\",\"source_description\":\"file:$category\"}
            ]
        }" > /dev/null 2>&1
}

echo "=== Syncing to Knowledge Graph ==="
echo "Graphiti: $GRAPHITI_API"
echo ""

# Sync main memory files
for f in MEMORY.md SOUL.md IDENTITY.md USER.md HEARTBEAT.md AGENTS.md; do
    if [ -f "/home/liujerry/moltbot/$f" ]; then
        content=$(cat "/home/liujerry/moltbot/$f" | head -c 4000)
        sync_entity "$f" "$content"
        sync_messages "$f" "memory" "$content"
        echo "  ✅ $f"
    fi
done

# Sync daily memory (recent ones)
count=0
for f in /home/liujerry/moltbot/memory/2026-05-*.md; do
    if [ -f "$f" ]; then
        name=$(basename "$f")
        content=$(cat "$f" | head -c 3000)
        sync_entity "$name" "$content"
        sync_messages "$name" "daily" "$content"
        echo "  ✅ $name"
        count=$((count + 1))
    fi
done
echo "  → $count daily files synced"

# Sync weekly
for f in /home/liujerry/moltbot/memory/weekly/W20_2026.md; do
    if [ -f "$f" ]; then
        name=$(basename "$f")
        content=$(cat "$f" | head -c 3000)
        sync_entity "$name" "$content"
        sync_messages "$name" "weekly" "$content"
        echo "  ✅ $name"
    fi
done

# Sync self-improving key files
for name in memory.md corrections.md reflections.md; do
    f="/home/liujerry/self-improving/$name"
    if [ -f "$f" ]; then
        content=$(cat "$f" | head -c 3000)
        sync_entity "$name" "$content"
        sync_messages "$name" "self_improving" "$content"
        echo "  ✅ self-improving/$name"
    fi
done

# Sync latest insights (skip extraction_*.json - too many)
for f in /home/liujerry/moltbot/memory/insights/daily_review_2026-05-13.md \
         /home/liujerry/moltbot/memory/insights/daily_review_2026-05-12.md \
         /home/liujerry/moltbot/memory/insights/daily_review_2026-05-11.md \
         /home/liujerry/moltbot/memory/insights/weekly_2026-W19.md \
         /home/liujerry/moltbot/memory/insights/weekly_2026-W20.md \
         /home/liujerry/moltbot/memory/insights/weekend_deep_dive_2026-05-09.md; do
    if [ -f "$f" ]; then
        name=$(basename "$f")
        content=$(cat "$f" | head -c 3000)
        sync_entity "$name" "$content"
        sync_messages "$name" "insights" "$content"
        echo "  ✅ insights/$name"
    fi
done

echo ""
echo "=== Verifying ==="
docker exec neo4j cypher-shell -u neo4j -p graphiti_memory_2026 "MATCH (n) RETURN count(n) as total" 2>/dev/null
echo ""
echo "Done!"