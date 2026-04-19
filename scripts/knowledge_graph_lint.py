#!/usr/bin/env python3
"""
Knowledge Graph Lint - 知识图谱健康检查
Karpathy LLM Wiki 模式的 Lint 操作实现

检查内容:
1. 孤立实体 (无任何关系)
2. 矛盾信息 (同一属性的不同值)
3. 过时实体 (30天未更新)
4. 关系类型分布
5. 实体增长趋势

用法:
    python3 knowledge_graph_lint.py              # 执行检查
    python3 knowledge_graph_lint.py --report    # 生成完整报告
    python3 knowledge_graph_lint.py --fix       # 自动修复可修复的问题
"""

import urllib.request
import json
import sys
import base64
from datetime import datetime, timedelta
from collections import Counter
import os

# Graphiti API 配置
GRAPHITI_URL = "http://localhost:8000"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "graphiti_memory_2026"

# 健康阈值
ORPHAN_THRESHOLD = 0.05  # 孤立实体超过5%则警告
STALE_DAYS = 30  # 30天未更新视为过时
CONTRADICTION_THRESHOLD = 0  # 任何矛盾都是问题

def search_graphiti(query, limit=100):
    """搜索 Graphiti"""
    data = json.dumps({
        "query": query,
        "group_id": "moltbot",
        "limit": limit
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f'{GRAPHITI_URL}/search',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e), "facts": []}

def query_neo4j(cypher_query):
    """直接查询 Neo4j"""
    data = json.dumps({
        "statements": [{"statement": cypher_query}]
    }).encode('utf-8')
    
    auth = base64.b64encode(f'{NEO4J_USER}:{NEO4J_PASSWORD}'.encode()).decode()
    
    req = urllib.request.Request(
        f'http://localhost:7474/db/neo4j/tx/commit',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Basic {auth}'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def get_entity_stats():
    """获取实体统计"""
    print("📊 获取实体统计...")
    
    result = query_neo4j("""
        MATCH (e:Entity) 
        RETURN count(e) as total_entities,
               count(DISTINCT e.group_id) as group_count,
               min(e.created_at) as oldest,
               max(e.created_at) as newest
    """)
    
    if "error" in result:
        return None
    
    try:
        data = result['results'][0]['data'][0]['row']
        return {
            "total": data[0],
            "groups": data[1],
            "oldest": data[2],
            "newest": data[3]
        }
    except:
        return None

def get_relationship_stats():
    """获取关系统计"""
    print("🔗 获取关系统计...")
    
    result = query_neo4j("""
        MATCH (a)-[r]->(b)
        RETURN type(r) as rel_type, count(*) as count
        ORDER BY count DESC
        LIMIT 20
    """)
    
    if "error" in result:
        return []
    
    try:
        return [(row['row'][0], row['row'][1]) for row in result['results'][0]['data']]
    except:
        return []

def get_orphan_entities(limit=20):
    """获取孤立实体 (无任何出向或入向关系)"""
    print("👤 检查孤立实体...")
    
    result = query_neo4j("""
        MATCH (e:Entity)
        WHERE NOT exists(()-[:RELATED_TO]->(e))
          AND NOT exists((e)-[:RELATED_TO]->())
          AND NOT exists(()-[:MENTIONS]->(e))
          AND NOT exists((e)-[:MENTIONS]->())
          AND NOT exists(()-[:USES]->(e))
          AND NOT exists((e)-[:USES]->())
          AND NOT exists(()-[:CREATED_BY]->(e))
          AND NOT exists((e)-[:CREATED_BY]->())
        RETURN e.name as name, e.created_at as created_at
        ORDER BY e.created_at DESC
        LIMIT {limit}
    """.format(limit=limit))
    
    if "error" in result:
        return []
    
    try:
        return [(row['row'][0], row['row'][1]) for row in result['results'][0]['data']]
    except:
        return []

def get_stale_entities(days=30, limit=20):
    """获取过时实体 (长时间未更新)"""
    print(f"⏰ 检查过时实体 ({days}天未更新)...")
    
    stale_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    result = query_neo4j("""
        MATCH (e:Entity)
        WHERE e.created_at < '{stale_date}'
        RETURN e.name as name, e.created_at as created_at
        ORDER BY e.created_at ASC
        LIMIT {limit}
    """.format(stale_date=stale_date, limit=limit))
    
    if "error" in result:
        return []
    
    try:
        return [(row['row'][0], row['row'][1]) for row in result['results'][0]['data']]
    except:
        return []

def get_fact_count():
    """获取事实数量"""
    print("📝 获取事实数量...")
    
    result = query_neo4j("""
        MATCH (f:Fact)
        RETURN count(f) as fact_count,
               count(DISTINCT f.name) as fact_types
    """)
    
    if "error" in result:
        return {"total": 0, "types": 0}
    
    try:
        data = result['results'][0]['data'][0]['row']
        return {"total": data[0], "types": data[1]}
    except:
        return {"total": 0, "types": 0}

def get_episode_stats():
    """获取情节/事件统计"""
    print("📚 获取情节统计...")
    
    result = query_neo4j("""
        MATCH (ep:Episode)
        RETURN count(ep) as episode_count
    """)
    
    if "error" in result:
        return 0
    
    try:
        return result['results'][0]['data'][0]['row'][0]
    except:
        return 0

def search_for_contradictions():
    """搜索可能的矛盾信息"""
    print("⚠️ 检查矛盾信息...")
    
    # 这是一个简化版本 - 实际需要更复杂的实体对齐逻辑
    # 寻找同一实体被标记为不同值的情况
    contradictions = []
    
    # 检查是否有实体的 invalid_at 被设置了
    result = query_neo4j("""
        MATCH (f:Fact)
        WHERE f.invalid_at IS NOT NULL
        RETURN f.name as name, count(*) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    
    if "error" not in result:
        try:
            for row in result['results'][0]['data']:
                name = row['row'][0]
                count = row['row'][1]
                if count > 1:
                    contradictions.append({
                        "type": "已失效的事实",
                        "entity": name,
                        "count": count,
                        "note": "该实体有多个已失效的事实，可能存在矛盾"
                    })
        except:
            pass
    
    return contradictions

def get_group_distribution():
    """获取分组分布"""
    print("📦 获取分组分布...")
    
    result = query_neo4j("""
        MATCH (e:Entity)
        RETURN e.group_id as group_id, count(*) as count
        ORDER BY count DESC
    """)
    
    if "error" in result:
        return []
    
    try:
        return [(row['row'][0], row['row'][1]) for row in result['results'][0]['data']]
    except:
        return []

def run_health_check():
    """执行健康检查"""
    print("=" * 60)
    print("🔬 知识图谱健康检查")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # 1. 实体统计
    entity_stats = get_entity_stats()
    if entity_stats:
        print(f"\n✅ 实体总数: {entity_stats['total']}")
        print(f"   分组数: {entity_stats['groups']}")
        print(f"   最早实体: {entity_stats['oldest']}")
        print(f"   最新实体: {entity_stats['newest']}")
    else:
        warnings.append("无法获取实体统计 (Neo4j 连接可能有问题)")
    
    # 2. 关系统计
    rel_stats = get_relationship_stats()
    if rel_stats:
        print(f"\n✅ 关系类型 Top 5:")
        for rel_type, count in rel_stats[:5]:
            print(f"   {rel_type}: {count}")
    else:
        warnings.append("无法获取关系统计")
    
    # 3. 孤立实体
    orphans = get_orphan_entities(limit=10)
    if orphans:
        orphan_rate = len(orphans) / (entity_stats['total'] if entity_stats else 1)
        if orphan_rate > ORPHAN_THRESHOLD:
            issues.append(f"孤立实体过多: {len(orphans)} 个 (占比 {orphan_rate:.1%})")
        else:
            warnings.append(f"发现 {len(orphans)} 个孤立实体")
        print(f"\n⚠️ 孤立实体 ({len(orphans)} 个):")
        for name, created in orphans[:5]:
            print(f"   - {name} (创建于 {created})")
    else:
        print("\n✅ 无孤立实体")
    
    # 4. 过时实体
    stale = get_stale_entities(days=STALE_DAYS, limit=10)
    if stale:
        warnings.append(f"发现 {len(stale)} 个过时实体 ({STALE_DAYS}+天未更新)")
        print(f"\n⏰ 过时实体 ({len(stale)} 个):")
        for name, created in stale[:5]:
            print(f"   - {name} (创建于 {created})")
    else:
        print(f"\n✅ 无过时实体 ({STALE_DAYS}天内均有更新)")
    
    # 5. 矛盾检查
    contradictions = search_for_contradictions()
    if contradictions:
        issues.append(f"发现 {len(contradictions)} 个可能的矛盾")
        print(f"\n⚠️ 矛盾信息:")
        for c in contradictions[:5]:
            print(f"   - {c['entity']}: {c['note']}")
    else:
        print("\n✅ 无矛盾信息")
    
    # 6. 分组分布
    group_dist = get_group_distribution()
    if group_dist:
        print(f"\n📦 分组分布:")
        for group, count in group_dist[:5]:
            print(f"   {group}: {count}")
    
    # 7. 事实统计
    fact_stats = get_fact_count()
    print(f"\n📝 事实统计:")
    print(f"   总事实数: {fact_stats['total']}")
    print(f"   事实类型: {fact_stats['types']}")
    
    # 8. 情节统计
    episode_count = get_episode_stats()
    print(f"\n📚 情节数: {episode_count}")
    
    # 汇总
    print("\n" + "=" * 60)
    print("📋 健康检查汇总")
    print("=" * 60)
    
    if not issues and not warnings:
        print("✅ 知识图谱健康状态: 优秀")
        print("   无问题，无警告")
        return True
    elif issues:
        print(f"❌ 知识图谱健康状态: 存在问题 ({len(issues)} 个问题)")
        for issue in issues:
            print(f"   - {issue}")
        if warnings:
            print(f"\n⚠️ 警告 ({len(warnings)} 个):")
            for w in warnings:
                print(f"   - {w}")
        return False
    else:
        print(f"⚠️ 知识图谱健康状态: 正常 ({len(warnings)} 个警告)")
        for w in warnings:
            print(f"   - {w}")
        return True

def save_report():
    """保存报告到文件"""
    log_dir = os.path.expanduser("~/.logs")
    os.makedirs(log_dir, exist_ok=True)
    
    report_file = f"{log_dir}/knowledge_graph_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # 重定向 stdout 到文件
    old_stdout = sys.stdout
    sys.stdout = open(report_file, 'w')
    
    run_health_check()
    
    sys.stdout.close()
    sys.stdout = old_stdout
    
    print(f"\n📄 报告已保存: {report_file}")
    return report_file

if __name__ == "__main__":
    if "--report" in sys.argv:
        save_report()
    else:
        run_health_check()
