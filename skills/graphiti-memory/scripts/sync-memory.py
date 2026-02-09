#!/usr/bin/env python3
"""
同步 OpenClaw memory 到 Graphiti 知识图谱
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加 Graphiti 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "graphiti"))

from graphiti_core.graphiti import Graphiti
from graphiti_core.nodes import EpisodeType

# 配置
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "graphiti_memory_2026")

OPENCLAW_MEMORY_DIR = Path.home() / "moltbot/memory"
OPENCLAW_SOUL_FILE = Path.home() / "moltbot/SOUL.md"
DEFAULT_GROUP_ID = "openclaw-main"


async def sync_memory_file(graphiti: Graphiti, file_path: Path, group_id: str):
    """同步单个 memory 文件"""
    if not file_path.exists():
        return 0
    
    content = file_path.read_text()
    
    try:
        await graphiti.add_episode(
            name=f"memory-{file_path.stem}",
            episode_body=content[:3000],
            source_description=f"OpenClaw memory: {file_path.name}",
            reference_time=datetime.now(),
            source=EpisodeType.text,
            group_id=group_id,
        )
        print(f"  ✅ {file_path.name}")
        return 1
    except Exception as e:
        print(f"  ❌ {file_path.name}: {e}")
        return 0


async def sync_soul_file(graphiti: Graphiti, file_path: Path, group_id: str):
    """同步 SOUL.md"""
    if not file_path.exists():
        return 0
    
    content = file_path.read_text()
    
    try:
        await graphiti.add_episode(
            name="soul-md",
            episode_body=content[:2000],
            source_description="OpenClaw personality definition",
            reference_time=datetime.now(),
            source=EpisodeType.text,
            group_id=group_id,
        )
        print(f"  ✅ SOUL.md")
        return 1
    except Exception as e:
        print(f"  ❌ SOUL.md: {e}")
        return 0


async def sync_all(group_id: str = DEFAULT_GROUP_ID):
    """同步所有 memory 文件"""
    print(f"\n🚀 开始同步 OpenClaw Memory → Graphiti")
    print(f"   Group ID: {group_id}")
    print("-" * 50)
    
    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    
    total = 0
    
    # 同步 memory/ 目录
    memory_dir = OPENCLAW_MEMORY_DIR
    if memory_dir.exists():
        print(f"\n📁 同步 memory/ 目录:")
        for mem_file in sorted(memory_dir.glob("*.md")):
            count = await sync_memory_file(graphiti, mem_file, group_id)
            total += count
    
    # 同步 SOUL.md
    print(f"\n📄 同步 SOUL.md:")
    count = await sync_soul_file(graphiti, OPENCLAW_SOUL_FILE, group_id)
    total += count
    
    print(f"\n✅ 共同步 {total} 个文件")
    
    await graphiti.close()
    return total


async def search_memory(query: str, group_id: str = DEFAULT_GROUP_ID, limit: int = 10):
    """搜索记忆"""
    print(f"\n🔍 搜索: '{query}'")
    
    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    
    try:
        results = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=limit,
        )
        
        print(f"   找到 {len(results.results)} 条结果:")
        for i, r in enumerate(results.results[:5], 1):
            fact = r.fact[:100] + "..." if len(r.fact) > 100 else r.fact
            print(f"   {i}. {fact}")
        
        return results
    except Exception as e:
        print(f"   ❌ 搜索失败: {e}")
        return None
    finally:
        await graphiti.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw Memory → Graphiti Sync")
    parser.add_argument("--sync", action="store_true", help="Sync all memory files")
    parser.add_argument("--search", type=str, help="Search memory")
    parser.add_argument("--group", type=str, default=DEFAULT_GROUP_ID, help="Group ID")
    
    args = parser.parse_args()
    
    if args.sync:
        asyncio.run(sync_all(args.group))
    elif args.search:
        asyncio.run(search_memory(args.search, args.group))
    else:
        parser.print_help()
