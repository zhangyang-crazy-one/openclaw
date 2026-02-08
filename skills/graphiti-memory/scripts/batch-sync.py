#!/usr/bin/env python3
"""
Batch sync memory files to Graphiti knowledge graph.
Uses synchronous processing to ensure data is properly stored.
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from graphiti_core.graphiti import Graphiti
from graphiti_core.nodes import EpisodeType


async def sync_memory_files():
    """Sync all memory files to Graphiti."""
    
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "graphiti_memory_2026"
    
    MEMORY_DIR = Path.home() / "moltbot/memory"
    SOUL_FILE = Path.home() / "moltbot/SOUL.md"
    GROUP_ID = "openclaw-memory"
    
    print("=" * 60)
    print("🚀 批量同步记忆文件到 Graphiti")
    print("=" * 60)
    
    # Create Graphiti instance
    print("\n📦 创建 Graphiti 实例...")
    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    print(f"   Embedder: {type(graphiti.embedder).__name__}")
    print(f"   LLM Client: {type(graphiti.llm_client).__name__}")
    
    sync_count = 0
    
    # Sync SOUL.md first
    if SOUL_FILE.exists():
        print(f"\n📄 同步 SOUL.md...")
        content = SOUL_FILE.read_text()[:3000]
        try:
            await graphiti.add_episode(
                name="SOUL-personality",
                episode_body=content,
                source_description="OpenClaw SOUL - Core Truths and Boundaries",
                reference_time=datetime.now(),
                source=EpisodeType.text,
                group_id=GROUP_ID,
            )
            print("   ✅ SOUL.md 已添加")
            sync_count += 1
        except Exception as e:
            print(f"   ❌ SOUL.md 失败: {e}")
    
    # Sync memory files
    if MEMORY_DIR.exists():
        print(f"\n📁 同步 memory/ 目录 ({len(list(MEMORY_DIR.glob('*.md')))} 个文件)...")
        
        for mem_file in sorted(MEMORY_DIR.glob("*.md")):
            print(f"   处理: {mem_file.name}...", end=" ")
            try:
                content = mem_file.read_text()[:4000]
                await graphiti.add_episode(
                    name=f"memory-{mem_file.stem}",
                    episode_body=content,
                    source_description=f"Memory: {mem_file.name}",
                    reference_time=datetime.now(),
                    source=EpisodeType.text,
                    group_id=GROUP_ID,
                )
                print("✅")
                sync_count += 1
            except Exception as e:
                print(f"❌ {str(e)[:40]}")
            
            # Small delay between requests
            await asyncio.sleep(2)
    
    print(f"\n✅ 总计添加 {sync_count} 个文件")
    print("\n⏳ 等待处理 (90秒)...")
    await asyncio.sleep(90)
    
    # Check results
    print("\n📊 验证结果...")
    from neo4j import AsyncGraphDatabase
    
    driver = AsyncGraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    async with driver.session() as session:
        # Episodes for our group
        result = await session.run(
            "MATCH (e:Episodic {group_id: $gid}) RETURN count(e) as count",
            gid=GROUP_ID
        )
        record = await result.single()
        group_episodes = record['count'] if record else 0
        
        # All Episodes
        result = await session.run("MATCH (e:Episodic) RETURN count(e)")
        record = await result.single()
        total_episodes = record[0]
        
        # Entities
        result = await session.run("MATCH (n:Entity) RETURN count(n)")
        record = await result.single()
        entities = record[0]
        
        # EntityEdges
        result = await session.run("MATCH ()-[e:RELATES_TO]->() RETURN count(e)")
        record = await result.single()
        edges = record[0]
        
        print(f"\n   📈 统计数据:")
        print(f"      Group Episodes: {group_episodes}")
        print(f"      Total Episodes: {total_episodes}")
        print(f"      Entities: {entities}")
        print(f"      EntityEdges: {edges}")
        
        # List entities
        print(f"\n   📋 提取的实体:")
        result = await session.run(
            "MATCH (n:Entity) RETURN n.name, n.summary LIMIT 10"
        )
        async for row in result:
            name = row['n.name']
            summary = row['n.summary'][:50] if row['n.summary'] else 'None'
            print(f"      - {name}: {summary}...")
        
        # List edges
        if edges > 0:
            print(f"\n   🔗 创建的关系:")
            result = await session.run(
                "MATCH ()-[e:RELATES_TO]->() RETURN e.name, e.fact LIMIT 10"
            )
            async for row in result:
                name = row['e.name']
                fact = row['e.fact'][:60] if row['e.fact'] else 'None'
                print(f"      - {name}: {fact}...")
    
    await driver.close()
    await graphiti.close()
    
    print("\n" + "=" * 60)
    if edges > 0:
        print("✅ 同步完成！知识图谱已更新。")
    else:
        print("⚠️  同步完成，但未创建实体关系。")
        print("   检查 DeepSeek LLM 调用是否正常工作。")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(sync_memory_files())
