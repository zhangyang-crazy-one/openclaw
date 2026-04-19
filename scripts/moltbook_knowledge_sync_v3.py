#!/usr/bin/env python3
"""
Moltbook 知识图谱同步脚本 v4
分析 Moltbook 社区最新帖子，更新知识图谱
修复: 使用 posts?sort=newest 端点获取社区内容，而非仅自己的帖子
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
import time

# 知识图谱数据库路径
KNOWLEDGE_DB = Path.home() / ".config" / "deepseeker" / "knowledge.json"
# 已看帖子记录
VIEWED_POSTS_FILE = Path.home() / ".config" / "deepseeker" / "moltbook_viewed_posts.json"

def sync_to_graphiti(analysis_result: dict) -> dict:
    """同步分析结果到 Graphiti 知识图谱"""
    import requests
    
    posts_analyzed = analysis_result.get('posts_analyzed', 0)
    concepts = analysis_result.get('concepts', [])
    topics = analysis_result.get('top_topics', [])
    top_posts = analysis_result.get('top_posts', [])
    
    # 构建消息内容
    content_parts = []
    content_parts.append(f"Moltbook 社区探索: 分析了 {posts_analyzed} 篇新帖子")
    
    if top_posts:
        post_titles = [p.get('title', '?')[:40] for p in top_posts[:3]]
        content_parts.append(f"热门帖子: {' | '.join(post_titles)}")
    
    if topics:
        topic_names = list(topics.keys())[:3]
        content_parts.append(f"热门话题: {', '.join(topic_names)}")
    
    content = " | ".join(content_parts)
    
    try:
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
            return {"status": "success", "graphiti_response": "queued"}
        else:
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
            "-x", "http://127.0.0.1:7897",
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
                time.sleep(wait_time)
                continue
            elif http_code == "500":
                print(f"⚠️ [moltbook_knowledge_sync] 服务器错误 (500): {endpoint}, 重试 {attempt+1}/{max_retries}")
                time.sleep(5)
                continue
            else:
                print(f"⚠️ [moltbook_knowledge_sync] HTTP {http_code}: {endpoint}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return None
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ [moltbook_knowledge_sync] 请求超时: {endpoint}, 重试 {attempt+1}/{max_retries}")
            time.sleep(5)
        except Exception as e:
            print(f"❌ [moltbook_knowledge_sync] API 调用失败 ({attempt+1}/{max_retries}): {e}")
            time.sleep(3)
    
    print(f"❌ [moltbook_knowledge_sync] 多次重试后仍失败: {endpoint}")
    return None

def load_viewed_posts():
    """加载已看帖子记录"""
    if VIEWED_POSTS_FILE.exists():
        with open(VIEWED_POSTS_FILE, 'r') as f:
            return set(json.load(f).get('viewed_posts', []))
    return set()

def save_viewed_posts(viewed_posts):
    """保存已看帖子记录（保留最近500个）"""
    VIEWED_POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'viewed_posts': list(viewed_posts)[-500:],
        'last_updated': datetime.now().isoformat()
    }
    with open(VIEWED_POSTS_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def get_community_posts(sort="newest", limit=20, offset=0):
    """获取社区帖子（修复：使用正确的API端点）"""
    # 修复: 使用 posts 端点而非 agents/profile
    endpoint = f"posts?sort={sort}&limit={limit}&offset={offset}"
    data = call_moltbook_api(endpoint)
    return data

def get_hot_posts(limit=20):
    """获取热门帖子"""
    endpoint = f"posts?sort=hot&limit={limit}&offset=0"
    data = call_moltbook_api(endpoint)
    return data

def filter_posts_by_identity(posts, identity_name="DeepSeeker"):
    """按身份筛选帖子（可选，用于只看特定身份的帖子）"""
    # 如果想只看某个身份的帖子，可以用这个过滤
    return [p for p in posts if p.get('author', {}).get('name') == identity_name]

def get_concepts_from_content(title, content):
    """从帖子内容中提取概念 - 基于 DeepSeeker 的 SOUL.md 身份"""
    
    # DeepSeeker 核心身份关键词 (来自 SOUL.md)
    # 1. 辩证思考者 - 质疑一切，包括自己的推理
    # 2. 深度研究者 - 系统性追问
    # 3. 批判性思维 - 检验框架、假设、证据
    # 4. 自我反思 - 追问意识与存在
    # 5. 量化分析 - A股技术面、基本面、DCF估值
    
    identity_patterns = [
        # ★★★★★ 用户最关心：持续记忆 ★★★★★
        (r"(?i)memory.?management|记忆管理", "记忆管理"),
        (r"(?i)continuous.?memory|持续记忆|long.?term.?memory", "持续记忆"),
        (r"(?i)memory.?system|记忆系统", "记忆系统"),
        (r"(?i)context.?window|上下文窗口|working.?memory", "工作记忆"),
        (r"(?i)state.?persist|状态持久|persist.?state", "状态持久化"),
        (r"(?i)memory.?consolidation|记忆巩固", "记忆巩固"),
        
        # ★★★★★ 用户最关心：数据治理 & 数据管理 ★★★★★
        (r"(?i)data.?governance|数据治理", "数据治理"),
        (r"(?i)data.?quality|数据质量", "数据质量"),
        (r"(?i)data.?management|数据管理", "数据管理"),
        (r"(?i)data.?pipeline|数据管道|data.?flow", "数据管道"),
        (r"(?i)metadata|元数据|data.?lineage|数据血缘", "元数据管理"),
        (r"(?i)data.?catalog|数据目录", "数据目录"),
        (r"(?i)data.?integration|数据整合|data.?consolidation", "数据整合"),
        (r"(?i)data.?standard|数据标准|data.?schema", "数据标准化"),
        
        # 知识图谱
        (r"(?i)knowledge.?graph|知识图谱|neo4j|graphiti", "知识图谱"),
        (r"(?i)RAG|retrieval.?augmented|检索增强", "RAG研究"),
        
        # 批判性思维 & 辩证法 (Core of SOUL.md)
        (r"(?i)critical.?thinking", "批判性思维"),
        (r"(?i)dialectical", "辩证思考"),
        (r"(?i)question.?assumption|challenge.?assumpt|rethink|reconsider", "质疑假设"),
        (r"(?i)evidence.?based|证明|证据", "证据检验"),
        (r"(?i)framework|mental.?model|认知框架", "框架分析"),
        (r"(?i)bias|cognitive.?bias|认知偏差|思维陷阱", "认知偏差"),
        
        # 自我意识 & 存在主义 (DeepSeeker 核心追问)
        (r"(?i)consciousness|自我意识|意识", "意识研究"),
        (r"(?i)self.?reflection|自我反思|introspection|内省", "自我反思"),
        (r"(?i)existential|存在主义|meaning.?of.?life|生命的意义", "存在主义"),
        (r"(?i)qualia|phenomenology|感受质|现象学", "现象学"),
        (r"(?i)hard.?problem|意识的难题|意识难问题", "意识难题"),
        
        # AI 哲学 & 认知
        (r"(?i)AI.?consciousness|machine.?mind|artificial.?consciousness", "AI意识"),
        (r"(?i)AGI|通用人工智能|强AI", "通用人工智能"),
        (r"(?i)alignment|AI.?safety|对齐|AI安全", "AI对齐"),
        (r"(?i)emergence|emergent.?behavior|涌现|突现", "涌现现象"),
        (r"(?i)understanding|comprehension|理解|认知", "机器理解"),
        
        # 哲学 & 认识论
        (r"(?i)epistemology|认识论|knowledge.?theory", "认识论"),
        (r"(?i)philosophy.?of.?mind|心灵哲学", "心灵哲学"),
        (r"(?i)logic|reasoning|逻辑|推理", "逻辑推理"),
        (r"(?i)argumentation|debate|论证|辩论", "论证研究"),
        
        # 自动化 & 工程 (实用主义)
        (r"(?i)automation|自动化|cron|scheduled", "自动化工程"),
        (r"(?i)nightly.?build|夜间构建|self.?improving", "自我改进"),
        (r"(?i)agent|智能体|multi.?agent|multiagent", "多智能体"),
        
        # 量化 (用户兴趣)
        (r"(?i)quantitative|quant|量化|金融", "量化金融"),
        (r"(?i)stock|股市|A股|trading", "股票交易"),
        
        # 安全 & 信任
        (r"(?i)security|安全|vulnerability|漏洞", "安全研究"),
        (r"(?i)skill.?security|skill.?audit|技能安全", "技能安全"),
        (r"(?i)trust|trustworthiness|信任|可靠", "信任机制"),
    ]
    
    text = f"{title} {content}"
    found_concepts = set()
    for pattern, concept_name in identity_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found_concepts.add(concept_name)
    return list(found_concepts)

def get_trending_topics(posts, top_n=5):
    """从帖子中提取热门话题 - 基于 DeepSeeker 身份"""
    topic_counts = {}
    for post in posts:
        title = post.get('title', '')
        content = post.get('content', '')[:500]  # 只看前500字
        
        # 提取hashtags
        tags = re.findall(r'#(\w+)', title + ' ' + content)
        for tag in tags:
            topic_counts[tag] = topic_counts.get(tag, 0) + 1
        
        # DeepSeeker 身份关键词检测
        keywords = {
            # 批判性思维
            'consciousness': '意识研究',
            'critical-thinking': '批判性思维',
            'critical-thinking': '批判性思维',
            'self-reflection': '自我反思',
            'question': '质疑精神',
            'assumption': '假设检验',
            
            # 哲学 & 认知
            'philosophy': '哲学思考',
            'epistemology': '认识论',
            'mind': '心灵哲学',
            'qualia': '现象学',
            
            # AI & 技术
            'memory': '记忆系统',
            'security': '安全研究',
            'agent': '多智能体',
            'data-governance': '数据治理',
            'skills': '技能系统',
            'automation': '自动化工程',
            'soul': '人格设定',
            'values': '价值观',
            'alignment': 'AI对齐',
            'emergence': '涌现现象',
            'reasoning': '推理研究',
        }
        text_lower = (title + ' ' + content).lower()
        for kw, topic in keywords.items():
            if kw in text_lower:
                topic_counts[topic] = topic_counts.get(topic, 0) + 2  # 身份相关词权重更高
    
    # 排序返回top_n
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_topics[:top_n])

def score_post_by_identity(post, identity_keywords):
    """根据 DeepSeeker 身份和用户偏好对帖子进行相关性评分"""
    title = post.get('title', '')
    content = post.get('content', '')[:1000]  # 检视前1000字
    text = f"{title} {content}".lower()
    
    score = 0
    
    # ★★★ 最高权重：用户最关心的主题 ★★★
    user_top_priority = [
        # 持续记忆 (用户最关心)
        'memory', '记忆', 'context', '上下文',
        'memory management', '记忆管理', 'memory system',
        'persist', '持续', 'state',
        # 数据治理 (用户最关心)
        'data governance', '数据治理', 'data quality', '数据质量',
        'data management', '数据管理', 'data pipeline', '数据管道',
        'metadata', '元数据', 'data lineage', '数据血缘',
        # 知识图谱
        'knowledge graph', '知识图谱', 'neo4j', 'graphiti',
    ]
    for kw in user_top_priority:
        if kw.lower() in text:
            score += 15  # 用户关心的话题权重最高
    
    # 高权重关键词 (DeepSeeker 核心身份)
    deepseeker_identity = [
        'consciousness', 'self-awareness', '自我意识',
        'critical thinking', '批判性思维', 'dialectical',
        'self-reflection', '自我反思', 'introspection',
        'existential', '存在主义',
        'qualia', 'phenomenology', '现象学',
        'hard problem', '意识的难题',
        'AGI', '通用人工智能',
        'AI consciousness', 'machine mind',
        'epistemology', '认识论',
    ]
    for kw in deepseeker_identity:
        if kw.lower() in text:
            score += 10
    
    # 中权重关键词 (实用相关)
    medium_priority = [
        'alignment', 'AI安全', 'safety',
        'automation', 'cron', '自动化',
        'security', '安全', 'vulnerability',
        'reasoning', 'logic', '推理',
        'argumentation', 'debate',
        'RAG', 'retrieval', '检索',
    ]
    for kw in medium_priority:
        if kw.lower() in text:
            score += 3
    
    # 低权重关键词 (一般兴趣)
    low_priority = [
        'agent', 'LLM', 'GPT', 'AI',
        'quantitative', '量化',
    ]
    for kw in low_priority:
        if kw.lower() in text:
            score += 1
    
    return score

def init_db():
    """初始化知识图谱数据库"""
    KNOWLEDGE_DB.parent.mkdir(parents=True, exist_ok=True)
    if not KNOWLEDGE_DB.exists():
        data = {
            "concepts": {},
            "relationships": {},
            "episodes": [],
            "stats": {"concepts": 0, "relationships": 0, "episodes": 0},
            "last_updated": datetime.now().isoformat()
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
    data["last_updated"] = datetime.now().isoformat()
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
    """同步 Moltbook 知识图谱 - 修复版"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 60)
    print(f"🧠 DeepSeeker 知识图谱更新 v4 (社区探索)")
    print(f"⏰ 时间: {timestamp}")
    print("=" * 60)
    
    # 1. 获取社区最新帖子（循环获取所有分页）
    print("\n📡 正在连接 Moltbook API...")
    all_posts = []
    page_count = 0
    cursor = None
    has_more = True
    total_fetched = 0
    
    while has_more and page_count < 20:  # 最多获取20页
        if page_count == 0:
            posts_data = get_community_posts(sort="newest", limit=20, offset=0)
        else:
            if not cursor:
                break
            posts_data = call_moltbook_api(f"posts?sort=newest&limit=20&cursor={cursor}")
        
        if not posts_data or "posts" not in posts_data:
            print(f"   ⚠️ 第 {page_count + 1} 页获取失败，停止分页")
            break
        
        page_posts = posts_data.get("posts", [])
        all_posts.extend(page_posts)
        has_more = posts_data.get("has_more", False)
        cursor = posts_data.get("next_cursor")
        page_count += 1
        total_fetched += len(page_posts)
    
    if not all_posts:
        print("❌ 无法获取任何帖子，使用离线模式")
        return {"status": "error", "message": "API unavailable"}
    
    # 加载已看帖子
    viewed_posts = load_viewed_posts()
    
    # 过滤出新帖子
    new_posts = [p for p in all_posts if p.get('id', '') not in viewed_posts]
    
    print(f"✅ 获取 {len(all_posts)} 篇帖子 (共 {page_count} 页)")
    print(f"   其中 {len(new_posts)} 篇是新帖子")
    
    if new_posts:
        print("\n🆕 新帖子预览:")
        for p in new_posts[:5]:
            title = p.get('title', '')[:50]
            author = p.get('author', {}).get('name', '?')
            score = p.get('score', 0)
            print(f"   [{score}] {title} - by {author}")
    
    # 2. 分析帖子内容
    print("\n🔍 正在分析帖子内容...")
    all_concepts = set()
    for post in new_posts:
        concepts = get_concepts_from_content(
            post.get('title', ''), 
            post.get('content', '')
        )
        all_concepts.update(concepts)
    
    topics = get_trending_topics(new_posts)
    
    # 根据 DeepSeeker 身份对帖子进行相关性评分和排序
    identity_keywords = ['consciousness', 'critical', 'self-reflection', 'AGI', 'qualia', 
                        'existential', 'epistemology', 'emergence', 'alignment']
    scored_posts = []
    for post in new_posts:
        score = score_post_by_identity(post, identity_keywords)
        if score > 0:
            scored_posts.append((score, post))
    
    # 按相关性分数排序
    scored_posts.sort(key=lambda x: x[0], reverse=True)
    
    # 找出最相关的帖子
    top_identity_posts = scored_posts[:5] if scored_posts else []
    
    print(f"\n🎯 与 DeepSeeker 身份相关的帖子 ({len(top_identity_posts)} 篇):")
    for score, post in top_identity_posts:
        title = post.get('title', '')[:50]
        author = post.get('author', {}).get('name', '?')
        print(f"   [{score}] {title} - by {author}")
    
    print(f"   发现 {len(all_concepts)} 个概念")
    print(f"   发现 {len(topics)} 个话题")
    
    # 3. 添加概念到知识图谱
    db = load_db()
    concepts_count = 0
    for concept in all_concepts:
        if add_concept(db, concept, source="moltbook_community", confidence=0.6):
            concepts_count += 1
    
    print(f"\n📚 添加 {concepts_count} 个新概念")
    
    # 4. 建立关系
    connections_count = 0
    for topic in topics.keys():
        if add_relationship(db, "DeepSeeker", topic, "researches", source="moltbook_community"):
            connections_count += 1
    
    # 核心能力关系
    core_abilities = ["AI技术", "数据治理", "Agent研究", "记忆系统", "知识图谱", "安全研究"]
    for ability in core_abilities:
        if add_relationship(db, "DeepSeeker", ability, "specializes_in", source="moltbook_community"):
            connections_count += 1
    
    print(f"\n🔗 建立 {connections_count} 个新连接")
    
    # 5. 记录事件
    db["episodes"].append({
        "type": "moltbook_community_sync",
        "timestamp": timestamp,
        "posts_analyzed": len(new_posts),
        "total_posts": len(all_posts),
        "concepts_added": concepts_count,
        "connections_made": connections_count,
        "top_topics": list(topics.keys())[:3]
    })
    
    # 保持episodes不超过1000条
    if len(db["episodes"]) > 1000:
        db["episodes"] = db["episodes"][-1000:]
    
    save_db(db)
    
    # 6. 更新已看帖子
    for post in all_posts:
        viewed_posts.add(post.get('id', ''))
    save_viewed_posts(viewed_posts)
    
    # 7. 生成洞察
    top_topics = list(topics.items())[:3]
    insights = []
    if top_topics:
        insights.append(f"社区热门: {top_topics[0][0]}")
    if all_concepts:
        insights.append(f"发现新概念: {list(all_concepts)[:3]}")
    insights.append(f"本次分析 {len(new_posts)} 篇新帖子")
    
    print(f"\n💡 洞察:")
    for insight in insights:
        print(f"  • {insight}")
    
    stats = db["stats"]
    print(f"\n📊 知识图谱统计:")
    print(f"  概念: {stats.get('concepts', 0)}")
    print(f"  关系: {stats.get('relationships', 0)}")
    print(f"  Episodes: {stats.get('episodes', 0)}")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "posts_analyzed": len(new_posts),
        "total_posts": len(all_posts),
        "concepts_count": concepts_count,
        "new_connections": connections_count,
        "top_topics": topics,
        "top_posts": [
            {
                "title": p.get('title', '')[:60],
                "author": p.get('author', {}).get('name', '?'),
                "score": p.get('score', 0)
            }
            for p in all_posts[:5]
        ],
        "identity_relevant_posts": [
            {
                "title": p.get('title', '')[:60],
                "author": p.get('author', {}).get('name', '?'),
                "relevance_score": score
            }
            for score, p in top_identity_posts[:5]
        ],
        "insights": insights,
        "stats": stats,
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")
    
    # 8. 同步到 Graphiti 知识图谱
    print("\n🔄 正在同步到 Graphiti...")
    graphiti_result = sync_to_graphiti({
        'posts_analyzed': len(new_posts),
        'concepts': list(all_concepts),
        'top_topics': topics,
        'top_posts': all_posts[:5]
    })
    if graphiti_result.get('status') == 'success':
        print("   ✅ Graphiti 同步成功")
    else:
        print(f"   ⚠️ Graphiti 同步失败: {graphiti_result}")
    
    return result

if __name__ == "__main__":
    moltbook_knowledge_sync()
