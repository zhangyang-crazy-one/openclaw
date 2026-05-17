#!/usr/bin/env python3
"""
知识图谱全面同步脚本
同步记忆文件、探索结果、自我进化文件到Graphiti
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import requests

GRAPHITI_API = "http://localhost:8000"
MOLTBOT_DIR = Path("/home/liujerry/moltbot")
MEMORY_DIR = MOLTBOT_DIR / "memory"
SELF_IMPROVING_DIR = Path.home() / "self-improving"
INSIGHTS_DIR = MEMORY_DIR / "insights"

def get_file_info(file_path):
    if not file_path.exists():
        return None
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "name": file_path.name,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "size": stat.st_size,
    }

def extract_content(file_path, max_chars=3000):
    if not file_path.exists():
        return ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(max_chars)
    except:
        return ""

def create_entity(name, summary, group_id="moltbot", category="memory"):
    """创建Entity节点"""
    entity_data = {
        "uuid": str(uuid.uuid4()),
        "group_id": group_id,
        "name": name,
        "summary": summary[:500] if summary else "",
    }
    try:
        response = requests.post(f"{GRAPHITI_API}/entity-node", json=entity_data, timeout=30)
        return response.status_code == 201
    except Exception as e:
        print(f"    ⚠️ Entity错误: {e}")
        return False

def create_messages(file_info, content, category, group_id="moltbot"):
    """创建Episode消息"""
    messages = [
        {
            "content": f"文件: {file_info['name']}, 类型: {category}, 修改: {file_info['modified']}, 大小: {file_info['size']} bytes",
            "role_type": "system",
            "role": "metadata",
            "timestamp": datetime.now().isoformat(),
            "source_description": f"file:{file_info['path']}"
        },
        {
            "content": content[:5000],
            "role_type": "user",
            "role": "memory",
            "timestamp": datetime.now().isoformat(),
            "source_description": f"file:{file_info['path']}"
        }
    ]
    try:
        response = requests.post(f"{GRAPHITI_API}/messages", json={"group_id": group_id, "messages": messages}, timeout=30)
        return response.status_code == 202
    except Exception as e:
        print(f"    ⚠️ Messages错误: {e}")
        return False

def sync_file(file_path, category, count_dict):
    """同步单个文件"""
    info = get_file_info(file_path)
    content = extract_content(file_path)
    if info and content:
        create_entity(file_path.name, content, "moltbot", category)
        create_messages(info, content, category)
        print(f"  ✅ {file_path.name}")
        return True
    return False

def main():
    print(f"知识图谱全面同步 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    counts = {"memory_files": 0, "insights": 0, "self_improving": 0}
    
    # 1. 同步每日记忆文件
    print("\n=== 同步每日记忆文件 ===")
    if MEMORY_DIR.exists():
        for md_file in sorted(MEMORY_DIR.glob("*.md")):
            if md_file.name in ["README.md"]:
                continue
            if sync_file(md_file, "daily_memory", counts):
                counts["memory_files"] += 1
    
    # 2. 同步探索结果 (insights/*.json)
    print("\n=== 同步探索结果 ===")
    if INSIGHTS_DIR.exists():
        for json_file in sorted(INSIGHTS_DIR.glob("*.json")):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                info = get_file_info(json_file)
                # 提取关键词和摘要
                summary = json.dumps(data)[:500] if data else ""
                create_entity(json_file.name, summary, "moltbot", "insights")
                create_messages(info, json.dumps(data)[:5000], "insights")
                print(f"  ✅ {json_file.name}")
                counts["insights"] += 1
            except Exception as e:
                print(f"  ⚠️ {json_file.name}: {e}")
    
    # 3. 同步自我进化文件
    print("\n=== 同步自我进化文件 ===")
    for name in ["memory.md", "corrections.md", "reflections.md"]:
        file_path = SELF_IMPROVING_DIR / name
        if file_path.exists():
            if sync_file(file_path, "self_improving", counts):
                counts["self_improving"] += 1
    
    print(f"\n✅ 全部记忆已同步到知识图谱，包含：")
    print(f"   - {counts['memory_files']}个记忆文件")
    print(f"   - {counts['insights']}个探索结果")
    print(f"   - {counts['self_improving']}个自我进化文件")

if __name__ == "__main__":
    main()