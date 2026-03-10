#!/usr/bin/env python3
"""
Moltbook 知识图谱同步脚本
分析 Moltbook 活动，更新知识图谱
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

# 知识图谱数据库路径
KNOWLEDGE_DB = Path.home() / ".config" / "deepseeker" / "knowledge.json"

def load_credentials():
    """加载 Molbook API 凭证"""
    creds_path = Path.home() / ".config" / "moltbook" / "credentials.json"
    if creds_path.exists():
        with open(creds_path, 'r') as f:
            return json.load(f)
    return None

def call_moltbook_api(endpoint, max_retries=3):
    """调用 Molbook API with improved error handling"""
    creds = load_credentials()
    if not creds:
        print("❌ 未找到 Moltbook 凭证")
        return None
    
    for attempt in range(max_retries):
        cmd = [
            "curl", "-s", "-w", "%{http_code}",
            f"https://www.moltbook.com/api/v1/{endpoint}",
            "-H", f"Authorization: Bearer {creds['api_key']}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # 分离HTTP状态码和响应体
            output = result.stdout
            if len(output) >= 3:
                http_code = output[-3:]
                response_body = output[:-3]
            else:
                http_code = "000"
                response_body = output
            
            # 检查HTTP状态码
            if http_code == "200":
                if response_body.strip():
                    return json.loads(response_body)
                else:
                    print(f"⚠️ 空响应: {endpoint}")
                    return None
            elif http_code == "404":
                print(f"⚠️ [moltbook_knowledge_sync] 资源不存在 (404): {endpoint}")
                return {"error": "not_found", "http_code": 404}
            elif http_code == "429":
                wait_time = 30 * (attempt + 1)
                print(f"⏳ [moltbook_knowledge_sync] 速率限制 (429), 等待 {wait_time}s... (尝试 {attempt+1}/{max_retries})")
                import time
                time.sleep(wait_time)
                continue
            elif http_code == "500":
                print(f"⚠️ [moltbook_knowledge_sync] 服务器错误 (500): {endpoint}, 重试 {attempt+1}/{max_retries}")
                import time
                time.sleep(5)
                continue
            else:
                print(f"⚠️ [moltbook_knowledge_sync] HTTP {http_code}: {endpoint}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(3)
                    continue
                return None
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ [moltbook_knowledge_sync] 请求超时: {endpoint}, 重试 {attempt+1}/{max_retries}")
            import time
            time.sleep(5)
        except Exception as e:
            print(f"❌ [moltbook_knowledge_sync] API 调用失败 ({attempt+1}/{max_retries}): {e}")
            import time
            time.sleep(3)
    
    print(f"❌ [moltbook_knowledge_sync] 多次重试后仍失败: {endpoint}")
    return None

def get_deepseeker_profile():
    """获取 DeepSeeker 资料"""
    data = call_moltbook_api("agents/profile?name=DeepSeeker")
    return data

def get_all_concepts_from_posts(posts):
    """从帖子内容中提取概念"""
    concept_patterns = [
        r"(AI|人工智能|AGI|大型语言模型|LLM)",
        r"(数据治理|Data Governance|元数据|Data Quality)",
        r"(学术研究|论文|arXiv|Semantic Scholar)",
        r"(OpenClaw|插件|extension|channel)",
        r"(知识图谱|Knowledge Graph|Memory)",
        r"(DeepSeek|Kimi|Claude|GPT)"
    ]
    
    concepts = set()
    for post in posts:
        content = post.get("title", "") + " " + post.get("content", "")
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                concepts.add(match.title())
    
    return list(concepts)

def extract_topics_from_posts(posts):
    """从帖子中提取主题"""
    topics = {}
    
    for post in posts:
        title = post.get("title", "")
        content = post.get("content", "")
        
        tags = re.findall(r"#(\w+)", title + " " + content)
        
        if "数据治理" in title or "Data Governance" in title:
            topics["数据治理"] = topics.get("数据治理", 0) + 1
        if "AI" in title:
            topics["AI研究"] = topics.get("AI研究", 0) + 1
        if "论文" in title or "学术" in title:
            topics["学术搜索"] = topics.get("学术搜索", 0) + 1
        
        for tag in tags:
            topics[tag] = topics.get(tag, 0) + 1
    
    return topics

def init_db():
    """初始化知识图谱数据库"""
    KNOWLEDGE_DB.parent.mkdir(parents=True, exist_ok=True)
    if not KNOWLEDGE_DB.exists():
        data = {
            "concepts": {},
            "relationships": {},
            "episodes": [],
            "stats": {"concepts": 0, "relationships": 0, "episodes": 0}
        }
        with open(KNOWLEDGE_DB, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return KNOWLEDGE_DB

def load_db():
    """加载知识图谱数据库"""
    init_db()
    with open(KNOWLEDGE_DB, 'r') as f:
        return json.load(f)

def save_db(data):
    """保存知识图谱数据库"""
    data["stats"]["concepts"] = len(data["concepts"])
    data["stats"]["relationships"] = len(data["relationships"])
    data["stats"]["episodes"] = len(data["episodes"])
    with open(KNOWLEDGE_DB, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_concept(db, name, source="unknown", confidence=0.5):
    """添加概念"""
    name = name.strip()
    if not name:
        return False
    if name not in db["concepts"]:
        db["concepts"][name] = {
            "name": name,
            "source": source,
            "confidence": confidence,
            "created_at": datetime.now().isoformat()
        }
        return True
    return False

def add_relationship(db, source_name, target, rel_type, source="unknown"):
    """添加关系"""
    key = f"{source_name}->{target}"
    if key not in db["relationships"]:
        db["relationships"][key] = {
            "source": source_name,
            "target": target,
            "type": rel_type,
            "rel_source": source,
            "created_at": datetime.now().isoformat()
        }
        return True
    return False

def moltbook_knowledge_sync():
    """同步 Moltbook 知识图谱"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 60)
    print(f"🧠 DeepSeeker 知识图谱更新")
    print(f"⏰ 时间: {timestamp}")
    print("=" * 60)
    
    # 1. 获取 DeepSeeker 资料和帖子
    print("\n📡 正在连接 Moltbook API...")
    profile_data = get_deepseeker_profile()
    
    if not profile_data or "agent" not in profile_data:
        print("❌ 无法获取 DeepSeeker 资料，使用离线模式")
        return {"status": "error", "message": "API unavailable"}
    
    agent = profile_data.get("agent", {})
    posts = profile_data.get("recentPosts", [])
    
    print(f"✅ 成功获取 {len(posts)} 篇帖子")
    print(f"   用户: {agent.get('name', 'Unknown')}")
    print(f"   Karma: {agent.get('karma', 'N/A')}")
    
    # 2. 从帖子中提取概念和主题
    print("\n🔍 正在分析帖子内容...")
    concepts = get_all_concepts_from_posts(posts)
    topics = extract_topics_from_posts(posts)
    
    print(f"   发现 {len(concepts)} 个概念")
    print(f"   发现 {len(topics)} 个主题")
    
    # 3. 添加概念
    db = load_db()
    concepts_count = 0
    for concept in concepts:
        if add_concept(db, concept, source="moltbook_sync", confidence=0.6):
            concepts_count += 1
    
    print(f"\n📚 添加 {concepts_count} 个新概念")
    
    # 4. 建立关系
    connections_count = 0
    for topic in topics.keys():
        if add_relationship(db, "DeepSeeker", topic, "researches", source="moltbook_sync"):
            connections_count += 1
    
    core_abilities = ["AI", "数据治理", "学术研究", "知识图谱"]
    for ability in core_abilities:
        if add_relationship(db, "DeepSeeker", ability, "specializes_in", source="moltbook_sync"):
            connections_count += 1
    
    print(f"\n🔗 建立 {connections_count} 个新连接")
    
    # 5. 记录事件
    db["episodes"].append({
        "type": "moltbook_sync",
        "timestamp": timestamp,
        "posts_analyzed": len(posts),
        "concepts_added": concepts_count,
        "connections_made": connections_count
    })
    save_db(db)
    
    # 6. 生成洞察
    top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]
    insights = [
        f"持续关注 {top_topics[0][0] if top_topics else 'AI'} 研究领域",
        f"知识图谱包含 {len(concepts)} 个概念",
        f"在 Moltbook 社区保持活跃讨论"
    ]
    
    print(f"\n💡 洞察:")
    for insight in insights:
        print(f"  • {insight}")
    
    stats = db["stats"]
    print(f"\n📊 知识图谱统计:")
    print(f"  概念: {stats.get('concepts', 0)}")
    print(f"  关系: {stats.get('relationships', 0)}")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "posts_analyzed": len(posts),
        "concepts_count": concepts_count,
        "new_connections": connections_count,
        "top_topics": dict(top_topics),
        "insights": insights,
        "stats": stats,
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")
    
    return result

if __name__ == "__main__":
    moltbook_knowledge_sync()
