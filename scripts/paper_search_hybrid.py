#!/usr/bin/env python3
"""
学术论文搜索脚本 - arXiv + OpenAlex 交叉验证版
策略：arXiv 为主获取全面论文，OpenAlex 补充引用数热点信息
"""
import json
import subprocess
import time
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============ 配置 ============
SEARCH_QUERIES = [
    "LLM reasoning",
    "AI governance", 
    "knowledge graph",
    "large language model",
    "LLM hallucination",
    # 数据治理相关
    "AI data governance",
    "data governance",
    "data management",
    "digital transformation",
    "enterprise digital transformation",
    "data quality",
    "data strategy",
    # DAMA 数据管理
    "DAMA data governance",
    "DAMA data management",
    "DAMA CDMP",
]

# 目标：每天更新10篇论文
TARGET_PAPERS_PER_DAY = 10
MIN_CITATIONS_THRESHOLD = 10  # 最低引用数门槛，低于此值继续搜索

# OpenAlex 热门论文补充（当引用数不达标时使用）
OPENALEX_HOT_QUERIES = [
    "LLM reasoning",
    "AI governance",
    "knowledge graph LLM",
    "AI data governance",
    "digital transformation enterprise",
    "data management AI",
    "data quality AI",
    # DAMA 数据管理
    "DAMA data governance",
    "DAMA CDMP",
]

DISCOVERY_DIR = Path.home() / ".config" / "deepseeker" / "discoveries"
DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)

MAX_RESULTS_PER_QUERY = 15  # arXiv 每查询获取数量
YEAR_RANGE = "2024,2025,2026"  # 年份筛选


def search_arxiv(query, max_results=15):
    """搜索 arXiv"""
    try:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True,
            text=True,
            timeout=20
        )
        return result.stdout
    except Exception as e:
        return f"Error: {e}"


def parse_arxiv_results(xml_content):
    """解析 arXiv 结果"""
    papers = []
    entries = re.findall(r'<entry>(.*?)</entry>', xml_content, re.DOTALL)
    
    for entry in entries:
        title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
        authors = re.findall(r'<name>(.*?)</name>', entry)
        summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
        published = re.search(r'<published>(.*?)</published>', entry)
        link = re.search(r'<id>(.*?)</id>', entry)
        
        title_text = title.group(1).strip().replace('\n', ' ') if title else "Unknown"
        summary_text = summary.group(1).strip().replace('\n', ' ')[:500] if summary else ""
        year = published.group(1)[:4] if published else "Unknown"
        
        # 提取 arXiv ID
        arxiv_id = ""
        if link:
            arxiv_id = link.group(1).replace("http://arxiv.org/abs/", "").strip()
        
        papers.append({
            "title": title_text,
            "authors": authors[:5],
            "abstract": summary_text,
            "year": year,
            "date": published.group(1)[:10] if published else "",
            "arxiv_id": arxiv_id,
            "source": "arXiv",
        })
    
    return papers


def get_citations_from_openalex(doi_or_title, max_retries=2):
    """从 OpenAlex 获取论文引用数"""
    for attempt in range(max_retries):
        try:
            # 尝试用 DOI 查询
            if doi_or_title.startswith("10."):
                url = f"https://api.openalex.org/works?filter=doi:https://doi.org/{quote_plus(doi_or_title)}&per_page=1"
            else:
                # 用标题查询
                url = f"https://api.openalex.org/works?filter=title.search:{quote_plus(doi_or_title[:50])}&per_page=1"
            
            result = subprocess.run(
                ["curl", "-s", "--max-time", "10", url],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("results"):
                    return data["results"][0].get("cited_by_count", 0)
                    
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
    return 0


def enrich_with_openalex(papers, dois=None):
    """批量从 OpenAlex 获取引用数"""
    print(f"  🌐 OpenAlex 交叉验证中...")
    
    # 先用 DOI 查询
    citation_map = {}
    
    for doi in dois:
        if doi:
            citations = get_citations_from_openalex(doi)
            if citations > 0:
                citation_map[doi] = citations
            time.sleep(0.3)  # 速率限制
    
    # 匹配并填充引用数
    enriched = []
    for paper in papers:
        citations = 0
        
        # 尝试匹配 DOI
        title_key = paper["title"][:30].lower()
        for doi, cit in citation_map.items():
            if doi.lower() in title_key or title_key in doi.lower():
                citations = cit
                break
        
        paper["cited_by"] = citations
        enriched.append(paper)
    
    return enriched


def search_openalex_hot(query, max_results=5):
    """直接从 OpenAlex 获取热门高引论文"""
    try:
        url = f"https://api.openalex.org/works?filter=title.search:{quote_plus(query)},publication_year:2023|2024|2025|2026&per_page={max_results}&sort=cited_by_count:desc"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            papers = []
            for item in data.get("results", []):
                # 检查是否已有 arXiv 版本
                locations = item.get("locations", [])
                arxiv_url = ""
                for loc in locations:
                    if "arxiv.org" in loc.get("landing_page_url", ""):
                        arxiv_url = loc.get("landing_page_url", "").replace("http://arxiv.org/abs/", "").replace("https://arxiv.org/abs/", "")
                        break
                
                authors = []
                for auth in item.get("authorships", [])[:3]:
                    name = auth.get("author", {}).get("display_name", "")
                    if name:
                        authors.append(name)
                
                papers.append({
                    "title": item.get("title", "Untitled"),
                    "authors": authors,
                    "abstract": item.get("abstract", "")[:300],
                    "year": item.get("publication_year", "N/A"),
                    "date": item.get("publication_date", ""),
                    "cited_by": item.get("cited_by_count", 0),
                    "arxiv_id": arxiv_url,
                    "doi": item.get("doi", "").replace("https://doi.org/", ""),
                    "source": "OpenAlex",
                })
            return papers
    except Exception as e:
        print(f"    ⚠️ OpenAlex 查询失败: {e}")
    return []


def generate_summary(paper):
    """生成论文摘要"""
    title = paper.get("title", "")
    cited = paper.get("cited_by", 0)
    year = paper.get("year", "N/A")
    arxiv_id = paper.get("arxiv_id", "")
    
    # 热点标签
    if cited >= 500:
        hot = "🔥🔥🔥"
    elif cited >= 100:
        hot = "🔥🔥"
    elif cited >= 20:
        hot = "🔥"
    else:
        hot = "📄"
    
    # 来源标签
    source = "arXiv" if arxiv_id else "Unknown"
    
    # 领域标签
    title_lower = title.lower()
    if "governance" in title_lower or "regulation" in title_lower:
        category = "[AI治理]"
    elif "knowledge graph" in title_lower:
        category = "[知识图谱]"
    elif "reasoning" in title_lower or "chain" in title_lower or "reasoning" in title_lower:
        category = "[推理]"
    elif "hallucination" in title_lower or "truthful" in title_lower:
        category = "[诚实性]"
    elif "agent" in title_lower or "autonomous" in title_lower:
        category = "[Agent]"
    elif "embedd" in title_lower:
        category = "[嵌入]"
    else:
        category = "[AI]"
    
    return f"{category} {hot} {year} | {cited} citations"


def load_existing_papers():
    """加载已保存的论文标题"""
    existing = set()
    if DISCOVERY_DIR.exists():
        for f in DISCOVERY_DIR.glob("papers_*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    for p in data.get("papers", []):
                        # 统一使用40字符key
                        key = f"{p.get('title', '')[:40]}_{p.get('year', '')}"
                        existing.add(key.lower())
            except:
                pass
    
    # 也检查数据库
    db_path = Path.home() / ".config" / "deepseeker" / "paper_database.csv"
    if db_path.exists():
        try:
            import csv
            with open(db_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row.get('title', '')[:40]}_{row.get('year', '')}"
                    existing.add(key.lower())
        except:
            pass
    
    return existing


def main():
    print("=" * 60)
    print("📚 学术论文搜索 - arXiv + OpenAlex 交叉验证版")
    print("新策略: arXiv下载 → OpenAlex验证 → 引用数门槛过滤")
    print("=" * 60)
    
    existing = load_existing_papers()
    print(f"\n📋 已存在 {len(existing)} 篇论文")
    
    # 目标：每天更新TARGET_PAPERS_PER_DAY篇论文
    qualified_papers = []  # 满足引用数门槛的论文
    pending_papers = []   # 待验证的论文
    
    print(f"\n📥 阶段1: arXiv搜索 (目标: {TARGET_PAPERS_PER_DAY}篇)")
    
    # 搜索循环：直到找到足够的论文
    search_count = 0
    for query in SEARCH_QUERIES:
        if len(qualified_papers) >= TARGET_PAPERS_PER_DAY:
            break
            
        print(f"  🔍 {query}")
        
        xml = search_arxiv(query, MAX_RESULTS_PER_QUERY)
        papers = parse_arxiv_results(xml)
        
        for p in papers:
            if len(qualified_papers) >= TARGET_PAPERS_PER_DAY:
                break
                
            key = f"{p['title'][:40]}_{p['year']}"
            if key in existing:
                continue
            
            # 跳过已有
            existing.add(key)
            pending_papers.append(p)
        
        print(f"     获取 {len(papers)} 篇")
        time.sleep(0.3)
        search_count += 1
    
    print(f"\n🌐 阶段2: OpenAlex交叉验证")
    
    # 如果pending_papers为空，说明arXiv论文都已存在，需要从OpenAlex获取
    if len(pending_papers) == 0:
        print("     arXiv无新论文，直接从OpenAlex获取...")
        for query in OPENALEX_HOT_QUERIES:
            if len(qualified_papers) >= TARGET_PAPERS_PER_DAY:
                break
            print(f"     🔥 {query}")
            hot = search_openalex_hot(query, 5)
            for p in hot:
                if len(qualified_papers) >= TARGET_PAPERS_PER_DAY:
                    break
                key = f"{p['title'][:40]}_{p['year']}"
                if key in existing:
                    continue
                existing.add(key)
                qualified_papers.append(p)
                print(f"     ✅ 添加: {p['title'][:40]}... ({p.get('cited_by',0)} citations)")
            time.sleep(0.5)
    else:
        # OpenAlex验证：获取引用数
        for i, paper in enumerate(pending_papers):
            if i % 5 == 0:
                print(f"     进度: {i}/{len(pending_papers)}")
            
            title = paper["title"][:80]
            citations = get_citations_from_openalex(title)
            paper["cited_by"] = citations
            paper["source"] = "arXiv+OpenAlex"
            
            # 检查是否满足引用数门槛
            if citations >= MIN_CITATIONS_THRESHOLD:
                qualified_papers.append(paper)
                print(f"     ✅ 引用数 {citations} >= {MIN_CITATIONS_THRESHOLD}: {paper['title'][:40]}...")
            else:
                print(f"     ❌ 引用数 {citations} < {MIN_CITATIONS_THRESHOLD}: {paper['title'][:40]}...")
            
            time.sleep(0.4)
    
    # 如果引用数不达标，从OpenAlex补充
    if len(qualified_papers) < TARGET_PAPERS_PER_DAY:
        needed = TARGET_PAPERS_PER_DAY - len(qualified_papers)
        print(f"\n🔥 阶段3: OpenAlex补充 (需要: {needed}篇)")
        
        for query in OPENALEX_HOT_QUERIES:
            if len(qualified_papers) >= TARGET_PAPERS_PER_DAY:
                break
            
            print(f"     🔥 {query}")
            hot = search_openalex_hot(query, 5)
            
            for p in hot:
                if len(qualified_papers) >= TARGET_PAPERS_PER_DAY:
                    break
                    
                key = f"{p['title'][:40]}_{p['year']}"
                if key in existing:
                    continue
                    
                existing.add(key)
                qualified_papers.append(p)
                print(f"     ✅ 添加: {p['title'][:40]}... ({p.get('cited_by',0)} citations)")
            
            time.sleep(0.5)
    
    # 使用满足条件的论文
    all_papers = qualified_papers if qualified_papers else []
    
    # 按引用数排序
    all_papers.sort(key=lambda x: x.get("cited_by", 0), reverse=True)
    
    total = len(all_papers)
    qualified_count = sum(1 for p in all_papers if p.get("cited_by", 0) >= MIN_CITATIONS_THRESHOLD)
    
    print(f"\n📊 搜索完成:")
    print(f"  - 满足引用数门槛 (>= {MIN_CITATIONS_THRESHOLD}): {qualified_count}篇")
    print(f"  - OpenAlex补充: {total - qualified_count}篇")
    
    # 显示所有论文
    print(f"\n📚 获取的论文 (按引用数排序):")
    for i, paper in enumerate(all_papers, 1):
        summary = generate_summary(paper)
        arxiv = paper.get("arxiv_id", "")
        source = paper.get("source", "")
        print(f"  {i}. {summary} [{source}]")
        print(f"     {paper['title'][:55]}...")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = DISCOVERY_DIR / f"papers_{timestamp}.json"
    
    output_data = {
        "timestamp": timestamp,
        "source": "arXiv + OpenAlex",
        "queries": SEARCH_QUERIES,
        "total": total,
        "papers": all_papers,
        "qualified": qualified_count
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 论文已保存至: {output_file}")
    
    # 添加到数据库
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from paper_db import add_papers
        db_count = add_papers(all_papers)
        print(f"✅ 数据库更新: 添加 {db_count} 篇新论文")
    except Exception as e:
        print(f"⚠️ 数据库更新失败: {e}")


if __name__ == "__main__":
    main()
