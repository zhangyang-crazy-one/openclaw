#!/usr/bin/env python3
"""
自动知识提取脚本
从 OpenClaw 对话中提取知识，更新知识图谱
"""
import json
import glob
import re
from datetime import datetime
from pathlib import Path
from dateutil.parser import parse as parse_date

# 知识图谱数据库路径
KNOWLEDGE_DB = Path.home() / ".config" / "deepseeker" / "knowledge.json"

# 知识模式
CONCEPT_PATTERNS = [
    r"(AI|人工智能|AGI|LLM|大语言模型)",
    r"(数据治理|Data Governance|元数据|Data Quality)",
    r"(OpenClaw|插件|channel|extension)",
    r"(Moltbook|知识图谱|Knowledge Graph)",
    r"(股票|ETF|金融|投资)",
    r"(学术研究|论文|arXiv)",
    r"(cron|定时任务|调度)",
]

RELATION_PATTERNS = [
    (r"使用|调用|invokes", "uses"),
    (r"创建|生成|creates", "creates"),
    (r"分析|分析", "analyzes"),
    (r"保存|saves", "saves"),
    (r"依赖|depends on", "depends_on"),
]

def load_db():
    """加载知识图谱"""
    if KNOWLEDGE_DB.exists():
        with open(KNOWLEDGE_DB, 'r') as f:
            return json.load(f)
    return {
        "concepts": {},
        "relationships": {},
        "episodes": [],
        "stats": {"concepts": 0, "relationships": 0, "episodes": 0}
    }

def save_db(db):
    """保存知识图谱"""
    KNOWLEDGE_DB.parent.mkdir(parents=True, exist_ok=True)
    db["stats"]["concepts"] = len(db["concepts"])
    db["stats"]["relationships"] = len(db["relationships"])
    db["stats"]["episodes"] = len(db["episodes"])
    with open(KNOWLEDGE_DB, 'w') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def extract_concepts(text):
    """从文本中提取概念"""
    concepts = set()
    for pattern in CONCEPT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            concepts.add(match.title())
    return list(concepts)

def get_latest_session_file():
    """获取最新的 session 文件"""
    session_dir = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
    if not session_dir.exists():
        # 尝试其他可能路径
        session_dir = Path.home() / ".openclaw" / "sessions"
        if not session_dir.exists():
            return None
    
    sessions = list(session_dir.glob("*.jsonl"))
    if not sessions:
        return None
    
    latest = max(sessions, key=lambda x: x.stat().st_mtime)
    return latest

def extract_knowledge():
    """提取知识主函数"""
    timestamp = datetime.now().isoformat()
    
    print("=" * 60)
    print(f"🧠 自动知识提取与添加")
    print(f"⏰ {timestamp}")
    print("=" * 60)
    
    db = load_db()
    
    # 获取最新对话
    session_file = get_latest_session_file()
    
    if not session_file:
        print("⚠️ 未找到对话文件")
        return {"status": "error", "message": "No session file"}
    
    print(f"\n📂 读取: {session_file}")
    
    # 读取对话
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = ""
    
    if not content:
        print("⚠️ 对话内容为空")
        return {"status": "error", "message": "Empty content"}
    
    # 提取概念
    print("\n🔍 提取概念...")
    concepts = extract_concepts(content)
    
    # 添加到知识图谱
    added_concepts = []
    for concept in concepts:
        if concept not in db["concepts"]:
            db["concepts"][concept] = {
                "name": concept,
                "source": "conversation",
                "confidence": 0.5,
                "created_at": timestamp
            }
            added_concepts.append(concept)
    
    print(f"  📚 发现 {len(concepts)} 个概念，添加 {len(added_concepts)} 个新概念")
    
    # 记录事件
    db["episodes"].append({
        "type": "knowledge_extraction",
        "timestamp": timestamp,
        "session_file": str(session_file),
        "concepts_found": len(concepts),
        "concepts_added": len(added_concepts)
    })
    
    save_db(db)
    
    # 输出
    print(f"\n📊 知识图谱统计:")
    print(f"  概念: {db['stats']['concepts']}")
    print(f"  关系: {db['stats']['relationships']}")
    print(f"  事件: {db['stats']['episodes']}")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "extracted_concepts": len(concepts),
        "added_concepts": len(added_concepts),
        "concepts": concepts,
        "stats": db["stats"],
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")
    
    return result

if __name__ == "__main__":
    import sys
    if "--latest" in sys.argv:
        extract_knowledge()
    else:
        print("Usage: python3 auto_extract_knowledge.py --latest")
