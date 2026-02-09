#!/usr/bin/env python3
"""
Graphiti Manual Sync Script

Directly syncs memory files to Graphiti with synchronous processing.
Bypasses the background queue issue by processing inline.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add Graphiti source path
sys.path.insert(0, str(Path(__file__).parent.parent / "graphiti"))

from graphiti_core.graphiti import Graphiti
from graphiti_core.nodes import EpisodeType
from neo4j import AsyncGraphDatabase


async def sync_memory():
    """Sync memory files to Graphiti with inline processing."""
    
    # Configuration
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "graphiti_memory_2026")
    
    MEMORY_DIR = Path.home() / "moltbot/memory"
    SOUL_FILE = Path.home() / "moltbot/SOUL.md"
    GROUP_ID = "openclaw-main"
    
    print("=" * 60)
    print("🚀 Graphiti Memory Sync")
    print("=" * 60)
    
    # Check Neo4j connection
    print("\n1. 检查 Neo4j 连接...")
    driver = AsyncGraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    async with driver.session() as session:
        result = await session.run("RETURN 'Neo4j OK'")
        print(f"   ✅ {await result.single()}")
    await driver.close()
    
    # Create Graphiti instance
    print("\n2. 创建 Graphiti 实例...")
    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    print(f"   ✅ Embedder: {type(graphiti.embedder).__name__}")
    
    # Sync SOUL.md
    if SOUL_FILE.exists():
        print(f"\n3. 同步 SOUL.md...")
        content = SOUL_FILE.read_text()[:2000]
        try:
            await graphiti.add_episode(
                name="soul-sync",
                episode_body=content,
                source_description="OpenClaw SOUL",
                reference_time=datetime.now(),
                source=EpisodeType.text,
                group_id=GROUP_ID,
            )
            print("   ✅ SOUL.md 已添加")
            print("   ⏳ 等待处理 (60秒)...")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"   ⚠️ 错误: {e}")
    
    # Sync memory files
    if MEMORY_DIR.exists():
        print(f"\n4. 同步 memory/ 目录...")
        count = 0
        for mem_file in sorted(MEMORY_DIR.glob("*.md"))[:10]:  # Limit to 10 files
            print(f"   处理: {mem_file.name}...", end=" ")
            try:
                content = mem_file.read_text()[:3000]
                await graphiti.add_episode(
                    name=f"memory-{mem_file.stem}",
                    episode_body=content,
                    source_description=f"Memory: {mem_file.name}",
                    reference_time=datetime.now(),
                    source=EpisodeType.text,
                    group_id=GROUP_ID,
                )
                print("✅")
                count += 1
                await asyncio.sleep(2)  # Rate limiting
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
        
        print(f"\n   总计添加 {count} 个文件")
    
    # Wait for processing
    print("\n5. 最终等待 (60秒)...")
    await asyncio.sleep(60)
    
    # Check results
    print("\n6. 检查结果...")
    driver = AsyncGraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    async with driver.session() as session:
        # Episodes
        result = await session.run("MATCH (e:Episodic) RETURN count(e)")
        episodes = (await result.single())[0]
        print(f"   Episodes: {episodes}")
        
        # Entities
        result = await session.run("MATCH (n:Entity) RETURN count(n)")
        entities = (await result.single())[0]
        print(f"   Entities: {entities}")
        
        # EntityEdges
        result = await session.run("MATCH ()-[e:RELATES_TO]->() RETURN count(e)")
        edges = (await result.single())[0]
        print(f"   EntityEdges: {edges}")
    
    await driver.close()
    await graphiti.close()
    
    print("\n" + "=" * 60)
    if edges > 0:
        print("✅ 同步完成! 可以进行搜索测试。")
    else:
        print("⚠️  实体关系未完全提取。")
        print("   这是 Graphiti 后台处理问题，需要修复驱动生命周期。")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(sync_memory())
