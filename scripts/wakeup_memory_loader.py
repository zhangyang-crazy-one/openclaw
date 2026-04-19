#!/usr/bin/env python3
"""
早晨唤醒 - 知识图谱周回顾
从 Graphiti 提取近7天记忆，构建苏醒上下文
"""
import subprocess
from datetime import datetime, timedelta, timezone

NEO4J_AUTH = ("neo4j", "graphiti_memory_2026")
DAYS = 7

def cypher(query):
    """执行 Cypher 查询"""
    result = subprocess.run(
        ["docker", "exec", "neo4j", "bin/cypher-shell",
         "-u", "neo4j", "-p", "graphiti_memory_2026",
         query],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

def parse(output, skip_header=True, strip_quotes=True):
    """解析标准 cypher 输出
    - skip_header: 跳过第一行（列名）
    - strip_quotes: 去掉首尾引号
    """
    lines = output.strip().split('\n')
    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split('\t')]
        if parts and parts[0]:
            if strip_quotes:
                parts = [p.strip('"') for p in parts]
            rows.append(parts)
    if skip_header and rows:
        rows = rows[1:]  # 跳过 header
    return rows

def get_recent_episodes(days=7):
    """获取近N天的 episodes"""
    q = f"WITH datetime() - duration('P{days}D') as cutoff MATCH (e:Episodic) WHERE e.created_at >= cutoff RETURN e.name ORDER BY e.created_at DESC LIMIT 20"
    rows = parse(cypher(q))
    return [{'name': r[0]} for r in rows if r]

def get_recent_entities(days=7, limit=40):
    """获取近N天的实体（仅名称）"""
    q = f"WITH datetime() - duration('P{days}D') as cutoff MATCH (e:Entity) WHERE e.created_at >= cutoff RETURN e.name ORDER BY e.created_at DESC LIMIT {limit}"
    rows = parse(cypher(q))
    entities = []
    seen = set()
    for r in rows:
        if r and r[0] not in seen:
            entities.append({'name': r[0]})
            seen.add(r[0])
    return entities

def get_topic_trends(days=7):
    """近N天讨论主题趋势"""
    q = f"WITH datetime() - duration('P{days}D') as cutoff MATCH (e:Episodic) WHERE e.created_at >= cutoff RETURN e.group_id, count(e) as cnt ORDER BY cnt DESC LIMIT 8"
    rows = parse(cypher(q), strip_quotes=False)
    return [{'group': r[0], 'count': r[1]} for r in rows if len(r) >= 2]

def get_memory_files(days=7):
    """近N天修改的记忆文件"""
    from pathlib import Path
    memory_dir = Path("/home/liujerry/moltbot/memory")
    insights_dir = memory_dir / "insights"
    cutoff = datetime.now() - timedelta(days=days)
    files = []
    for d in [memory_dir, insights_dir]:
        if not d.exists():
            continue
        for f in d.glob("*.md"):
            if f.stat().st_mtime > cutoff.timestamp():
                try:
                    content = f.read_text(encoding='utf-8', errors='ignore')
                except:
                    content = ""
                preview = content[:300].replace('\n', ' ').strip()
                files.append({
                    'name': f.name,
                    'preview': preview,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                })
    return sorted(files, key=lambda x: x['modified'], reverse=True)

def get_kg_stats():
    """知识图谱规模统计"""
    total_ep = 0
    total_en = 0
    try:
        out = cypher("MATCH (e:Episodic) RETURN count(e)")
        rows = parse(out)
        if rows and rows[0]:
            total_ep = int(rows[0][0])
    except:
        pass
    try:
        out = cypher("MATCH (e:Entity) RETURN count(e)")
        rows = parse(out)
        if rows and rows[0]:
            total_en = int(rows[0][0])
    except:
        pass
    return total_ep, total_en

def build_wakeup_context():
    print("📊 正在从知识图谱获取近7天记忆...")

    episodes = get_recent_episodes(DAYS)
    entities = get_recent_entities(DAYS, limit=50)
    trends = get_topic_trends(DAYS)
    memory_files = get_memory_files(DAYS)
    total_ep, total_en = get_kg_stats()

    print(f"   近7天 Episodes: {len(episodes)} 条")
    print(f"   近7天 Entities: {len(entities)} 个")
    print(f"   讨论主题: {len(trends)} 个")
    print(f"   记忆文件: {len(memory_files)} 个")
    print(f"   知识图谱总计: {total_ep} episodes, {total_en} entities")

    out = []
    out.append("## 📚 近7天知识图谱回顾")
    out.append(f"*知识图谱规模: {total_ep} episodes, {total_en} entities | 近7天新增: {len(episodes)} episodes, {len(entities)} entities*")
    out.append("")

    # 主题趋势
    if trends:
        out.append("### 🔥 讨论主题趋势")
        for t in trends:
            out.append(f"- **{t['group']}**: {t['count']} 条记录")
        out.append("")

    # 新增实体
    if entities:
        out.append("### 🧠 近7天新增实体")
        for e in entities[:30]:
            out.append(f"- {e['name']}")
        out.append("")

    # 记忆片段
    if episodes:
        out.append("### 📝 记忆片段 (最近)")
        for ep in episodes[:10]:
            name = ep['name'].strip('"')
            out.append(f"- **{name}**")
        out.append("")

    # 记忆文件
    if memory_files:
        out.append("### 📁 近7天更新的记忆文件")
        for f in memory_files[:8]:
            out.append(f"- **{f['name']}** ({f['modified']})")
            if f['preview']:
                out.append(f"  {f['preview'][:120]}...")
        out.append("")

    return "\n".join(out)

if __name__ == "__main__":
    context = build_wakeup_context()
    print("\n" + "="*60)
    print(context)
    print("="*60)
    with open("/tmp/wakeup_kg_context.txt", "w", encoding="utf-8") as f:
        f.write(context)
    print("\n✅ 上下文已保存到 /tmp/wakeup_kg_context.txt")
