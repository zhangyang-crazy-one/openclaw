#!/usr/bin/env python3
"""同步insights JSON文件到知识图谱 (使用entity-node和messages API)"""
import json
import uuid
from datetime import datetime
from pathlib import Path
import requests

GRAPHITI_API = "http://localhost:8000"
INSIGHTS_DIR = Path("/home/liujerry/moltbot/memory/insights")
GROUP_ID = "moltbot"

def create_entity(name, entity_type="concept", group_id=GROUP_ID):
    """创建单个实体"""
    data = {
        "uuid": str(uuid.uuid4()),
        "group_id": group_id,
        "name": name,
        "entity_type": entity_type,
        "summary": f"从insights探索结果中提取的概念: {name}",
    }
    try:
        resp = requests.post(f"{GRAPHITI_API}/entity-node", json=data, timeout=15)
        return resp.status_code == 201
    except:
        return False

def create_episode(insight_data, group_id=GROUP_ID):
    """创建Episode记录"""
    source = insight_data.get("source", "unknown")
    timestamp = insight_data.get("timestamp", datetime.now().isoformat())
    concepts = insight_data.get("concepts", [])
    relations = insight_data.get("relations", [])
    
    concept_names = [c.get("name", "") for c in concepts if c.get("name")]
    relation_strs = [f"{r.get('from','')} --{r.get('type','relates_to')}--> {r.get('to','')}" for r in relations]
    
    messages = [{
        "content": f"探索来源: {source}\n时间: {timestamp}\n概念: {', '.join(concept_names)}\n关系: {'; '.join(relation_strs)}",
        "role_type": "user",
        "role": "insight",
        "timestamp": timestamp,
        "source_description": f"insight:{source}"
    }]
    
    data = {"group_id": group_id, "messages": messages}
    try:
        resp = requests.post(f"{GRAPHITI_API}/messages", json=data, timeout=15)
        return resp.status_code == 202
    except:
        return False

files = sorted(INSIGHTS_DIR.glob("*.json"))
print(f"发现 {len(files)} 个insights JSON文件")

entities_created = 0
episodes_created = 0
skipped = 0

for i, f in enumerate(files):
    try:
        data = json.load(open(f))
        if not isinstance(data, dict):
            skipped += 1
            continue
        
        concepts = data.get("concepts", [])
        for c in concepts:
            name = c.get("name", "")
            if name and create_entity(name, c.get("type", "concept")):
                entities_created += 1
        
        if create_episode(data):
            episodes_created += 1
        
        if (i+1) % 50 == 0:
            print(f"  进度: {i+1}/{len(files)} (实体:{entities_created}, Episodes:{episodes_created})")
            
    except Exception as e:
        print(f"  ⚠️ {f.name}: {e}")

print(f"\n✅ insights同步完成:")
print(f"   - 文件处理: {len(files)} 个")
print(f"   - 新增实体: {entities_created} 个")
print(f"   - 新增Episodes: {episodes_created} 个")
print(f"   - 跳过(无效): {skipped} 个")
