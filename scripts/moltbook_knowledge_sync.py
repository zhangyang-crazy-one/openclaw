#!/usr/bin/env python3
"""
Moltbook知识同步脚本
将Moltbook帖子同步到知识图谱
"""
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path("/home/liujerry/文档/programs/openclaw-private-config")


def sync_to_graphiti(posts: list) -> dict:
    """同步到知识图谱"""
    import requests
    # 调用Graphiti API
    try:
        # 构建消息内容
        content_parts = []
        for i, post in enumerate(posts[:10]):  # 限制10条
            content_parts.append(f"#{i+1}: {post.get('title', 'No title')}")
        content = f"Moltbook帖子同步 ({len(posts)}篇): " + " | ".join(content_parts)
        
        response = requests.post(
            "http://localhost:8000/messages",
            json={
                "group_id": "moltbot",
                "messages": [
                    {
                        "role": "assistant",
                        "role_type": "assistant",
                        "content": content
                    }
                ]
            },
            timeout=30
        )
        if response.status_code in (200, 202):
            return {"status": "success", "posts_synced": len(posts)}
        else:
            return {"status": "error", "code": response.status_code, "body": response.text[:200]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Moltbook知识同步")
    parser.add_argument("--latest", action="store_true", help="同步最新帖子")
    parser.add_argument("--count", type=int, default=10, help="帖子数量")
    
    args = parser.parse_args()
    
    print("📚 Moltbook知识同步")
    print(f"时间: {datetime.now()}")
    print(f"模式: {'最新' if args.latest else '全部'}")
    
    # 模拟同步
    posts = [{"title": f"Post {i}", "score": 100-i*5} for i in range(args.count)]
    
    result = sync_to_graphiti(posts)
    print(f"结果: {result}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
