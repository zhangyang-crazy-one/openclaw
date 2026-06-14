#!/usr/bin/env python3
"""
知识图谱记忆同步脚本
将记忆文件同步到Graphiti知识图谱
修复版 - 使用新API端点
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import requests

# 配置
GRAPHITI_API = "http://localhost:8000"
NEO4J_AUTH = ("neo4j", "graphiti_memory_2026")
MOLTBOT_DIR = Path("/home/liujerry/moltbot")
MEMORY_FILES = [
    MOLTBOT_DIR / "MEMORY.md",
    MOLTBOT_DIR / "SOUL.md",
    MOLTBOT_DIR / "IDENTITY.md",
    MOLTBOT_DIR / "USER.md",
    MOLTBOT_DIR / "HEARTBEAT.md",
    MOLTBOT_DIR / "AGENTS.md",
]

# Workspace目录
WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
PLANNING_DIR = WORKSPACE_DIR / "planning"

# 记忆目录
MEMORY_DIR = MOLTBOT_DIR / "memory"

# self-improving目录
SELF_IMPROVING_DIR = Path.home() / "self-improving"

# 默认group_id
DEFAULT_GROUP_ID = "moltbot"


def get_knowledge_graph_stats():
    """获取知识图谱统计信息"""
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "neo4j", "cypher-shell", "-u", "neo4j", "-p", "graphiti_memory_2026",
             "MATCH (n) RETURN count(n)"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            count = int(lines[1].strip())
            return {"entities": count, "episodes": count}
        return {"entities": 0, "episodes": 0}
    except Exception as e:
        print(f"  ⚠️ 统计获取失败: {e}")
        return {"entities": 0, "episodes": 0}


def get_file_info(file_path):
    """获取文件信息"""
    if not file_path.exists():
        return None

    stat = file_path.stat()
    return {
        "path": str(file_path),
        "name": file_path.name,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "size": stat.st_size,
    }


def extract_content_preview(file_path, max_chars=2000):
    """提取文件内容预览"""
    if not file_path.exists():
        return ""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
            return content[:max_chars]
    except:
        return ""


def create_entity_node(name, summary, group_id=DEFAULT_GROUP_ID):
    """在Graphiti中创建Entity节点 (新API)"""
    entity_data = {
        "uuid": str(uuid.uuid4()),
        "group_id": group_id,
        "name": name,
        "summary": summary,
    }

    try:
        response = requests.post(
            f"{GRAPHITI_API}/entity-node",
            json=entity_data,
            timeout=30
        )
        if response.status_code == 201:
            return True
        else:
            print(f"    ⚠️ Entity创建失败: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"    ❌ Entity创建错误: {e}")
        return False


def create_episode_messages(file_info, content, category, group_id=DEFAULT_GROUP_ID):
    """在Graphiti中创建Episode消息 (新API)"""
    # 将内容分段,每段作为一条消息
    messages = []

    # 添加文件元数据作为system消息
    messages.append({
        "content": f"文件: {file_info['name']}, 类型: {category}, 修改: {file_info['modified']}, 大小: {file_info['size']} bytes",
        "role_type": "system",
        "role": "metadata",
        "timestamp": datetime.now().isoformat(),
        "source_description": f"file:{file_info['path']}"
    })

    # 添加内容作为user消息
    messages.append({
        "content": content[:5000],  # 限制长度
        "role_type": "user",
        "role": "memory",
        "timestamp": datetime.now().isoformat(),
        "source_description": f"file:{file_info['path']}"
    })

    message_data = {
        "group_id": group_id,
        "messages": messages
    }

    try:
        response = requests.post(
            f"{GRAPHITI_API}/messages",
            json=message_data,
            timeout=30
        )
        if response.status_code == 202:
            return True
        else:
            print(f"    ⚠️ Messages创建失败: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"    ❌ Messages创建错误: {e}")
        return False


def sync_memory_files():
    """同步主要记忆文件"""
    print("=== 同步主要记忆文件 ===")

    categories = {
        "MEMORY.md": "memory",
        "SOUL.md": "soul",
        "IDENTITY.md": "identity",
        "USER.md": "user",
        "HEARTBEAT.md": "heartbeat",
        "AGENTS.md": "agents",
    }

    for file_path in MEMORY_FILES:
        if not file_path.exists():
            print(f"  跳过: {file_path} (不存在)")
            continue

        info = get_file_info(file_path)
        category = categories.get(file_path.name, "other")
        content = extract_content_preview(file_path)

        # 创建实体节点
        create_entity_node(file_path.name, content[:500], category)

        # 创建Episode消息
        create_episode_messages(info, content, category)

        print(f"  ✅ {file_path.name}")


def sync_daily_memory():
    """同步每日记忆"""
    print("\n=== 同步每日记忆 ===")

    if not MEMORY_DIR.exists():
        print("  memory目录不存在")
        return

    count = 0
    for md_file in sorted(MEMORY_DIR.glob("*.md")):
        if md_file.name == "README.md":
            continue

        info = get_file_info(md_file)
        content = extract_content_preview(md_file, 3000)

        # 创建实体节点
        create_entity_node(md_file.name, content[:500], "daily")

        # 创建Episode消息
        create_episode_messages(info, content, "daily_memory")

        print(f"  ✅ {md_file.name}")
        count += 1

    if count == 0:
        print("  无每日记忆文件")


def sync_self_improving():
    """同步self-improving文件"""
    print("\n=== 同步self-improving文件 ===")

    if not SELF_IMPROVING_DIR.exists():
        print("  self-improving目录不存在")
        return

    key_files = [
        "memory.md",
        "corrections.md",
        "reflections.md",
    ]

    count = 0
    for name in key_files:
        file_path = SELF_IMPROVING_DIR / name
        if not file_path.exists():
            continue

        info = get_file_info(file_path)
        content = extract_content_preview(file_path, 3000)

        # 创建实体节点
        create_entity_node(name, content[:500], "self_improving")

        # 创建Episode消息
        create_episode_messages(info, content, "self_improving")

        print(f"  ✅ {name}")
        count += 1

    if count == 0:
        print("  无self-improving文件")


def sync_insights_files():
    """同步memory/insights下的探索结果JSON文件 (批量)"""
    print("\n=== 同步insights探索结果 ===", flush=True)

    insights_dir = MEMORY_DIR / "insights"
    if not insights_dir.exists():
        print("  insights目录不存在", flush=True)
        return

    json_files = sorted(insights_dir.glob("*.json"))
    if not json_files:
        print("  无insights JSON文件", flush=True)
        return

    BATCH_SIZE = 10
    synced = 0
    batch = []

    def flush_batch(batch):
        if not batch:
            return 0
        messages = []
        for item in batch:
            messages.append({
                "content": f"[Insights:{item['name']}] {item['summary']}",
                "role_type": "system",
                "role": "metadata",
                "timestamp": datetime.now().isoformat(),
                "source_description": f"file:{item['path']}"
            })
            messages.append({
                "content": item["content"][:3000],
                "role_type": "user",
                "role": "memory",
                "timestamp": datetime.now().isoformat(),
                "source_description": f"file:{item['path']}"
            })
        message_data = {"group_id": DEFAULT_GROUP_ID, "messages": messages}
        try:
            response = requests.post(
                f"{GRAPHITI_API}/messages",
                json=message_data,
                timeout=60
            )
            if response.status_code == 202:
                return len(batch)
            else:
                print(f"    ⚠️ 批量messages失败: {response.status_code}", flush=True)
                return 0
        except Exception as e:
            print(f"    ❌ 批量messages错误: {e}", flush=True)
            return 0

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue

        # 提取关键词和摘要
        topic = data.get("topic", data.get("title", json_file.stem))
        summary_parts = [f"探索主题: {topic}"]
        if "results" in data:
            titles = [r.get("title", "") for r in data.get("results", [])[:5] if r.get("title")]
            if titles:
                summary_parts.append(f"关键结果: {'; '.join(titles)}")
        if "findings" in data:
            findings = data["findings"]
            if isinstance(findings, dict):
                keys = list(findings.keys())[:5]
                summary_parts.append(f"发现领域: {', '.join(keys)}")
        if "key_points" in data and isinstance(data["key_points"], list):
            summary_parts.append(f"要点: {'; '.join(str(p) for p in data['key_points'][:3])}")
        if "query" in data:
            summary_parts.append(f"查询: {data['query']}")
        if "summary" in data:
            summary_parts.append(f"摘要: {str(data['summary'])[:200]}")

        summary = " | ".join(summary_parts)[:500]
        content_str = json.dumps(data, ensure_ascii=False)

        batch.append({
            "name": json_file.stem,
            "summary": summary,
            "content": content_str,
            "path": str(json_file)
        })

        if len(batch) >= BATCH_SIZE:
            count = flush_batch(batch)
            synced += count
            batch = []
            if synced % 100 == 0:
                print(f"  ...已同步 {synced} 个insights文件", flush=True)

    if batch:
        count = flush_batch(batch)
        synced += count

    print(f"  ✅ 共同步 {synced} 个insights探索结果", flush=True)


def sync_planning_files():
    """同步planning文件夹"""
    print("\n=== 同步planning文件 ===")

    if not PLANNING_DIR.exists():
        print("  planning目录不存在")
        return

    planning_files = list(PLANNING_DIR.glob("*.md"))

    if not planning_files:
        print("  无planning文件")
        return

    for md_file in planning_files:
        info = get_file_info(md_file)
        content = extract_content_preview(md_file, 3000)

        # 创建实体节点
        create_entity_node(md_file.name, content[:500], "planning")

        # 创建Episode消息
        create_episode_messages(info, content, "planning")

        print(f"  ✅ {md_file.name}")


def main():
    print(f"知识图谱记忆同步 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"Graphiti API: {GRAPHITI_API}", flush=True)

    # 同步前统计
    print("\n=== 同步前统计 ===", flush=True)
    stats_before = get_knowledge_graph_stats()
    print(f"  📊 实体: {stats_before.get('entities', 0)}", flush=True)
    print(f"  📝 Episodes: {stats_before.get('episodes', 0)}", flush=True)

    # 同步各类型文件
    sync_memory_files()
    sync_daily_memory()
    sync_self_improving()
    sync_insights_files()
    sync_planning_files()

    # 同步后统计
    print("\n=== 同步后统计 ===", flush=True)
    stats_after = get_knowledge_graph_stats()
    print(f"  📊 实体: {stats_after.get('entities', 0)}", flush=True)
    print(f"  📝 Episodes: {stats_after.get('episodes', 0)}", flush=True)

    # 计算新增
    new_entities = stats_after.get('entities', 0) - stats_before.get('entities', 0)
    new_episodes = stats_after.get('episodes', 0) - stats_before.get('episodes', 0)

    if new_entities > 0 or new_episodes > 0:
        print(f"\n  ✨ 本次新增: 实体 {new_entities}, Episodes {new_episodes}", flush=True)

    print("\n同步完成!", flush=True)


if __name__ == "__main__":
    main()
