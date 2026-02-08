#!/bin/bash
# Graphiti Memory Status & Quick Test
# ====================================

echo "========================================"
echo "🔍 Graphiti Memory System Status"
echo "========================================"

# Check services
echo ""
echo "1. 服务状态:"
echo "   Neo4j:    $(curl -s http://localhost:7474 > /dev/null && echo '✅ 运行中' || echo '❌ 停止')"
echo "   Graphiti: $(curl -s http://localhost:8001/healthcheck > /dev/null && echo '✅ 运行中' || echo '❌ 停止')"

# Query Neo4j
echo ""
echo "2. 数据统计:"
episodes=$(curl -s "http://localhost:7474/db/neo4j/query/v2" \
  -H "Content-Type: application/json" \
  -u "neo4j:graphiti_memory_2026" \
  -d '{"statement": "MATCH (e:Episodic) RETURN count(e)"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('values',[[0]])[0][0])" 2>/dev/null || echo "0")
entities=$(curl -s "http://localhost:7474/db/neo4j/query/v2" \
  -H "Content-Type: application/json" \
  -u "neo4j:graphiti_memory_2026" \
  -d '{"statement": "MATCH (n:Entity) RETURN count(n)"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('values',[[0]])[0][0])" 2>/dev/null || echo "0")
edges=$(curl -s "http://localhost:7474/db/neo4j/query/v2" \
  -H "Content-Type: application/json" \
  -u "neo4j:graphiti_memory_2026" \
  -d '{"statement": "MATCH ()-[e:RELATES_TO]->() RETURN count(e)"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('values',[[0]])[0][0])" 2>/dev/null || echo "0")

echo "   Episodes:   $episodes"
echo "   Entities:  $entities"
echo "   Relations: $edges"

# Quick search test
echo ""
echo "3. 搜索测试:"
result=$(curl -s -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SOUL helpful", "group_ids": ["t"]}' 2>/dev/null)
facts=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('facts',[])))" 2>/dev/null || echo "0")
echo "   搜索结果: $facts 条 facts"

echo ""
echo "========================================"
echo "📊 系统状态: $edges EntityEdges"
if [ "$edges" -gt "0" ]; then
    echo "✅ 搜索功能应该可用"
else
    echo "⚠️  实体关系提取失败，搜索不可用"
    echo ""
    echo "💡 解决方案:"
    echo "   1. 重启 Graphiti: ~/moltbot/skills/graphiti-memory/scripts/start-graphiti.sh"
    echo "   2. 手动同步: python3 scripts/graphiti-sync-direct.py"
    echo ""
    echo "🔧 根本原因:"
    echo "   Graphiti 后台处理驱动生命周期问题"
    echo "   需要修复 neo4j 异步驱动复用逻辑"
fi
echo "========================================"
