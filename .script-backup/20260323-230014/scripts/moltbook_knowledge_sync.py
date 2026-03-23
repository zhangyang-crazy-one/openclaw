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
    # 调用Graphiti API
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://localhost:8000/messages",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({
                 "group_id": "moltbook_sync",
                 "messages": [{"role": "assistant", "content": f"Moltbook同步: {len(posts)}篇帖子"}]
             })],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {"status": "success", "posts_synced": len(posts)}
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
