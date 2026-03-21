#!/usr/bin/env python3
"""Sync insights JSON files to graphiti knowledge graph via HTTP API."""

import json
from datetime import datetime
from pathlib import Path
import requests

GRAPHITI_API = "http://localhost:8000"
DEFAULT_GROUP_ID = "moltbot"

def create_entity_node(name, summary, group_id=DEFAULT_GROUP_ID):
    """Create entity node via HTTP API."""
    import uuid
    entity_data = {
        "uuid": str(uuid.uuid4()),
        "group_id": group_id,
        "name": name,
        "summary": summary[:500] if summary else "",
    }
    try:
        response = requests.post(f"{GRAPHITI_API}/entity-node", json=entity_data, timeout=30)
        return response.status_code in (200, 201, 202)
    except Exception as e:
        return False

def create_episode_messages(topic, content, timestamp, group_id=DEFAULT_GROUP_ID):
    """Create episode via HTTP API."""
    messages = []
    messages.append({
        "content": f"探索主题: {topic}",
        "role_type": "system",
        "role": "metadata",
        "timestamp": timestamp or datetime.now().isoformat(),
        "source_description": "insight:research_results"
    })
    messages.append({
        "content": content[:5000],
        "role_type": "user",
        "role": "insight",
        "timestamp": timestamp or datetime.now().isoformat(),
        "source_description": "insight:research_results"
    })
    message_data = {
        "group_id": group_id,
        "messages": messages
    }
    try:
        response = requests.post(f"{GRAPHITI_API}/messages", json=message_data, timeout=30)
        return response.status_code == 202
    except Exception as e:
        return False

def sync_insights():
    insights_dir = Path(__file__).parent.parent / "memory" / "insights"
    json_files = sorted(insights_dir.glob("*.json"))
    
    print(f"=== 同步探索结果 ({len(json_files)} 个文件) ===")
    
    synced = 0
    errors = 0
    for f in json_files:
        try:
            with open(f) as fp:
                data = json.load(fp)
            
            topic = data.get("topic", f.stem)
            timestamp = data.get("timestamp", datetime.now().isoformat())
            results = data.get("results", [])
            
            # Build summary from results
            summary = f"探索主题: {topic}\n"
            if results:
                titles = [r.get("title", "") for r in results[:10] if r.get("title")]
                summary += f"发现 ({len(results)}项): " + ", ".join(titles[:5])
                if len(results) > 5:
                    summary += f" 等{len(results)}项"
            
            # Create entity
            create_entity_node(topic, summary)
            
            # Create episode
            create_episode_messages(topic, summary, timestamp)
            
            synced += 1
            if synced % 50 == 0:
                print(f"  已同步 {synced} 个文件...")
                
        except Exception as e:
            errors += 1
    
    print(f"✅ 成功同步 {synced} 个探索结果 (失败 {errors} 个)")
    return synced

if __name__ == "__main__":
    sync_insights()
