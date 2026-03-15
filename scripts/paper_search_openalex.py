#!/usr/bin/env python3
"""
学术论文搜索脚本 - OpenAlex 版
支持：引用数筛选、热点排序、年份筛选、无需API Key
"""
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

# ============ 配置 ============
SEARCH_QUERIES = [
    "LLM reasoning",
    "AI governance",
    "knowledge graph",
    "large language model",
    "LLM hallucination",
]

# 输出目录
DISCOVERY_DIR = Path.home() / ".config" / "deepseeker" / "discoveries"
DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)

# 搜索参数
MAX_RESULTS_PER_QUERY = 10
MIN_CITATIONS = 0  # 最小引用数，0=不限制
YEAR_RANGE = "2024|2025|2026"  # 年份筛选


def search_openalex(query, max_results=10, min_citations=0, year_range=None):
    """使用 OpenAlex API 搜索论文"""
    try:
        # 构建过滤条件
        filters = [f"title.search:{quote_plus(query)}"]
        
        if year_range:
            filters.append(f"publication_year:{year_range}")
        
        if min_citations > 0:
            filters.append(f"cited_by_count:>{min_citations}")
        
        filter_str = ",".join(filters)
        url = f"https://api.openalex.org/works?filter={filter_str}&per_page={max_results}&sort=cited_by_count:desc"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", url],
            capture_output=True,
            text=True,
            timeout=35
        )
        
        if result.returncode != 0:
            return {"error": f"curl failed: {result.stderr}"}
        
        return json.loads(result.stdout)
        
    except Exception as e:
        return {"error": str(e)}


def parse_openalex_results(data):
    """解析 OpenAlex 结果"""
    papers = []
    
    if "error" in data:
        return papers
    
    results = data.get("results", [])
    
    for item in results:
        # 提取作者
        authors = []
        for auth in item.get("authorships", [])[:5]:  # 只取前5个作者
            author_info = auth.get("author", {})
            name = author_info.get("display_name", "Unknown")
            authors.append(name)
        
        # 提取引用数
        cited_by = item.get("cited_by_count", 0)
        
        # 提取发表信息
        year = item.get("publication_year", "N/A")
        date = item.get("publication_date", "")
        
        # 提取期刊/来源
        primary_loc = item.get("primary_location", {})
        source = primary_loc.get("source") or {}
        landing_url = primary_loc.get("landing_page_url", "")
        journal = source.get("display_name", "arXiv" if "arxiv" in landing_url.lower() else "Unknown") if source else "Unknown"
        
        # 提取链接
        doi = item.get("doi", "")
        pdf_url = primary_loc.get("pdf_url", "")
        
        # OA 状态
        oa_status = item.get("open_access", {}).get("oa_status", "unknown")
        
        papers.append({
            "title": item.get("title", "Untitled"),
            "authors": authors,
            "year": year,
            "date": date,
            "journal": journal,
            "cited_by": cited_by,
            "doi": doi,
            "pdf_url": pdf_url,
            "oa_status": oa_status,
            "openalex_id": item.get("id", ""),
        })
    
    return papers


def generate_summary(paper):
    """生成论文摘要"""
    title = paper.get("title", "")
    cited = paper.get("cited_by", 0)
    year = paper.get("year", "N/A")
    journal = paper.get("journal", "Unknown")
    oa = paper.get("oa_status", "unknown")
    
    # 热点标签
    if cited >= 100:
        hot = "🔥🔥🔥"
    elif cited >= 50:
        hot = "🔥🔥"
    elif cited >= 10:
        hot = "🔥"
    else:
        hot = "📄"
    
    # OA 标签
    oa_icon = "🔓" if oa in ["gold", "hybrid", "green"] else "🔒"
    
    # 领域标签
    title_lower = title.lower()
    if "governance" in title_lower or "regulation" in title_lower:
        category = "[AI治理]"
    elif "knowledge graph" in title_lower:
        category = "[知识图谱]"
    elif "reasoning" in title_lower or "chain" in title_lower:
        category = "[推理]"
    elif "hallucination" in title_lower or "truthful" in title_lower:
        category = "[诚实性]"
    elif "embedd" in title_lower:
        category = "[嵌入]"
    else:
        category = "[AI]"
    
    return f"{category} {hot}{oa_icon} {year} | {cited} citations | {journal[:30]}"


def load_existing_papers():
    """加载已保存的论文标题，避免重复"""
    existing = set()
    if DISCOVERY_DIR.exists():
        for f in DISCOVERY_DIR.glob("papers_*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    for p in data.get("papers", []):
                        key = f"{p.get('title', '')[:50]}_{p.get('year', '')}"
                        existing.add(key)
            except:
                pass
    return existing


def main():
    print("=" * 60)
    print("📚 学术论文搜索 - OpenAlex 版")
    print("=" * 60)
    
    # 加载已存在的论文
    existing = load_existing_papers()
    print(f"\n📋 已存在 {len(existing)} 篇论文，将跳过重复项")
    
    all_papers = []
    source_counts = {}
    
    for query in SEARCH_QUERIES:
        print(f"\n🔍 搜索: {query}")
        
        data = search_openalex(
            query, 
            max_results=MAX_RESULTS_PER_QUERY,
            min_citations=MIN_CITATIONS,
            year_range=YEAR_RANGE
        )
        
        if "error" in data:
            print(f"  ❌ 错误: {data['error']}")
            continue
        
        papers = parse_openalex_results(data)
        
        # 过滤已存在的
        new_papers = []
        for p in papers:
            key = f"{p['title'][:50]}_{p['year']}"
            if key not in existing:
                new_papers.append(p)
                existing.add(key)
        
        all_papers.extend(new_papers)
        source_counts[query] = len(new_papers)
        
        print(f"  ✅ 获取 {len(papers)} 篇，新增 {len(new_papers)} 篇")
        
        # 礼貌性延迟
        time.sleep(0.5)
    
    # 按引用数排序
    all_papers.sort(key=lambda x: x.get("cited_by", 0), reverse=True)
    
    # 统计
    total = len(all_papers)
    print(f"\n📊 总计: {total} 篇论文")
    
    # 显示 Top 10
    print(f"\n🔥 Top 10 论文 (按引用数):")
    for i, paper in enumerate(all_papers[:10], 1):
        summary = generate_summary(paper)
        print(f"  {i}. {summary}")
        print(f"     {paper['title'][:60]}...")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = DISCOVERY_DIR / f"papers_{timestamp}.json"
    
    output_data = {
        "timestamp": timestamp,
        "source": "OpenAlex",
        "queries": SEARCH_QUERIES,
        "total": total,
        "papers": all_papers
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 论文已保存至: {output_file}")
    
    # 输出摘要用于消息发送
    summary_msg = f"📚 学术论文搜索完成\n"
    summary_msg += f"来源: OpenAlex (无需API)\n"
    summary_msg += f"关键词: {', '.join(SEARCH_QUERIES)}\n"
    summary_msg += f"总计: {total} 篇\n\n"
    summary_msg += "🔥 Top 5:\n"
    
    for i, paper in enumerate(all_papers[:5], 1):
        summary = generate_summary(paper)
        summary_msg += f"{i}. {summary}\n"
        summary_msg += f"   {paper['title'][:50]}...\n"
    
    print("\n" + "=" * 60)
    print(summary_msg)


if __name__ == "__main__":
    main()
