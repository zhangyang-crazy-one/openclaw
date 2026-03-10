#!/usr/bin/env python3
"""
知识图谱记忆同步脚本
将记忆文件同步到Graphiti知识图谱
"""
import os
import json
from datetime import datetime
from pathlib import Path
import requests

# 配置
GRAPHITI_API = "http://localhost:8000"
MOLTBOT_DIR = Path("/home/liujerry/moltbot")
MEMORY_FILES = [
    MOLTBOT_DIR / "MEMORY.md",
    MOLTBOT_DIR / "SOUL.md",
    MOLTBOT_DIR / "IDENTITY.md",
    MOLTBOT_DIR / "USER.md",
    MOLTBOT_DIR / "HEARTBEAT.md",
]

# 记忆目录
MEMORY_DIR = MOLTBOT_DIR / "memory"

# self-improving目录
SELF_IMPROVING_DIR = Path.home() / ".self-improving"


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


def extract_content_preview(file_path, max_chars=500):
    """提取文件内容预览"""
    if not file_path.exists():
        return ""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
            return content.replace('\n', ' ')[:max_chars]
    except:
        return ""


def create_episode(file_info, content_preview, category):
    """在Graphiti中创建Episode"""
    episode_data = {
        "episodes": [
            {
                "entity_names": [file_info["name"]],
                "fact": f"[{category}] {file_info['name']}: {content_preview}",
                "source_link": str(file_info["path"]),
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{GRAPHITI_API}/episodes",
            json=episode_data,
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error creating episode: {e}")
        return False


def create_entity(file_info, category):
    """在Graphiti中创建Entity"""
    entity_data = {
        "entities": [
            {
                "name": file_info["name"],
                "entity_type": category,
                "description": f"修改时间: {file_info['modified']}, 大小: {file_info['size']} bytes",
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{GRAPHITI_API}/entities",
            json=entity_data,
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error creating entity: {e}")
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
    }
    
    for file_path in MEMORY_FILES:
        if not file_path.exists():
            print(f"  跳过: {file_path} (不存在)")
            continue
        
        info = get_file_info(file_path)
        category = categories.get(file_path.name, "other")
        preview = extract_content_preview(file_path)
        
        # 创建实体
        create_entity(info, category)
        
        # 创建Episode记录
        create_episode(info, preview, category)
        
        print(f"  ✅ {file_path.name}")


def sync_daily_memory():
    """同步每日记忆"""
    print("\n=== 同步每日记忆 ===")
    
    if not MEMORY_DIR.exists():
        print("  memory目录不存在")
        return
    
    for md_file in sorted(MEMORY_DIR.glob("*.md")):
        if md_file.name == "README.md":
            continue
        
        info = get_file_info(md_file)
        preview = extract_content_preview(md_file, 300)
        
        # 创建Episode记录
        create_episode(info, preview, "daily_memory")
        
        print(f"  ✅ {md_file.name}")


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
    
    for name in key_files:
        file_path = SELF_IMPROVING_DIR / name
        if not file_path.exists():
            continue
        
        info = get_file_info(file_path)
        preview = extract_content_preview(file_path, 300)
        
        # 创建实体和Episode
        create_entity(info, "self_improving")
        create_episode(info, preview, "self_improving")
        
        print(f"  ✅ {name}")


def main():
    print(f"知识图谱记忆同步 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Graphiti API: {GRAPHITI_API}")
    
    # 同步各类型文件
    sync_memory_files()
    sync_daily_memory()
    sync_self_improving()
    
    print("\n同步完成!")


if __name__ == "__main__":
    main()
