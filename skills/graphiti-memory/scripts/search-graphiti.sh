#!/bin/bash
# 搜索 Graphiti 记忆

set -e

QUERY="$1"
GROUP="${2:-openclaw-main}"
PORT="${3:-8001}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 <搜索词> [group_id] [port]"
    echo "示例: $0 'DeepSeeker personality'"
    exit 1
fi

echo "🔍 搜索: $QUERY"
echo ""

curl -s -X POST "http://localhost:$PORT/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"group_ids\": [\"$GROUP\"]}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    facts = data.get('facts', [])
    print(f'找到 {len(facts)} 条结果:')
    for i, f in enumerate(facts[:5], 1):
        fact = f.get('fact', '')[:100]
        print(f'{i}. {fact}...')
except Exception as e:
    print(f'解析失败: {e}')
    print(sys.stdin.read()[:500])
"
