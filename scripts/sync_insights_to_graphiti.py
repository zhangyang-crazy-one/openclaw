#!/usr/bin/env python3
"""
同步insights JSON文件到知识图谱
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import requests

GRAPHITI_API = "http://localhost:8000"
INSIGHTS_DIR = Path("/home/liujerry/moltbot/memory/insights")

def extract_json_summary(filepath):
    """从JSON文件提取摘要用于实体创建"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取关键词
        keywords = []
        if 'keywords' in data:
            keywords = data['keywords'][:10] if isinstance(data['keywords'], list) else []
        elif 'topic' in data:
            keywords = [data['topic']]
        
        # 提取摘要
        summary = ""
        if 'summary' in data:
            summary = data['summary'][:500]
        elif 'title' in data:
            summary = str(data.get('title', ''))[:500]
        
        return {
            'keywords': keywords,
            'summary': summary,
            'filename': filepath.name
        }
    except Exception as e:
        return {'keywords': [], 'summary': str(filepath), 'filename': filepath.name}

def sync_insights_to_graphiti():
    """同步insights目录下的JSON文件到知识图谱"""
    json_files = list(INSIGHTS_DIR.glob("*.json"))
    print(f"发现 {len(json_files)} 个insights JSON文件")
    
    synced = 0
    skipped = 0
    
    for json_file in json_files:
        # 提取摘要
        info = extract_json_summary(json_file)
        
        # 创建实体节点
        entity_data = {
            "uuid": str(uuid.uuid4()),
            "group_id": "moltbot",
            "name": info['filename'],
            "summary": info['summary'][:500] if info['summary'] else info['filename'],
        }
        
        try:
            response = requests.post(
                f"{GRAPHITI_API}/entity-node",
                json=entity_data,
                timeout=30
            )
            if response.status_code == 201:
                synced += 1
                if synced % 50 == 0:
                    print(f"  已同步 {synced} 个文件...")
            else:
                skipped += 1
        except Exception as e:
            skipped += 1
    
    print(f"✅ Insights同步完成: {synced} 个成功, {skipped} 个跳过")
    return synced

if __name__ == "__main__":
    print(f"=== 同步Insights到知识图谱 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    count = sync_insights_to_graphiti()
    print(f"完成: {count} 个insights文件已同步")