#!/usr/bin/env python3
"""
学术论文搜索脚本 - 快速版
只搜索arXiv，优化速度
"""
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

# 搜索关键词
SEARCH_QUERIES = [
    "AI governance 2024",
    "data governance LLM 2024",
    "large language model AI regulation",
    "knowledge graph",
    "LLM reasoning",
]

# 配置
DISCOVERY_DIR = Path.home() / ".config" / "deepseeker" / "discoveries"

def generate_summary(paper):
    """生成论文摘要 - 简单提取式"""
    
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")[:800]
    
    # 简单提取摘要前150字作为概括
    summary = abstract[:150].strip()
    if len(abstract) > 150:
        summary += "..."
    
    # 添加研究领域标签
    title_lower = title.lower()
    if "governance" in title_lower or "regulation" in title_lower:
        category = "[AI治理]"
    elif "knowledge graph" in title_lower:
        category = "[知识图谱]"
    elif "reasoning" in title_lower or "llm" in title_lower:
        category = "[LLM]"
    elif "data" in title_lower:
        category = "[数据科学]"
    else:
        category = "[AI研究]"
    
    return f"{category} {summary}"

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

def search_arxiv(query, max_results=10):
    """搜索 arXiv - 快速版"""
    try:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", url],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def parse_arxiv_results(xml_content):
    """解析 arXiv 结果"""
    import re
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
        
        papers.append({
            "title": title_text,
            "authors": authors,
            "year": year,
            "abstract": summary_text,
            "url": link.group(1) if link else "",
            "source": "arXiv",
            "citations": 0,
            "influential_citations": 0,
            "score": 0
        })
    
    return papers

def academic_search():
    """学术搜索主函数 - 快速版"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 60)
    print(f"📚 DeepSeeker Academic Search (Fast Mode)")
    print(f"{today_str} {timestamp.split()[1]}")
    print("=" * 60)
    
    all_papers = []
    source_counts = {}
    year_2024_plus = 0
    
    for query in SEARCH_QUERIES:
        print(f"\n📌 {query}")
        
        # 只搜索 arXiv
        arxiv_result = search_arxiv(query, 10)
        if "Error" not in arxiv_result:
            arxiv_papers = parse_arxiv_results(arxiv_result)
            all_papers.extend(arxiv_papers)
            source_counts["arXiv"] = source_counts.get("arXiv", 0) + len(arxiv_papers)
            print(f"  ✅ arXiv: {len(arxiv_papers)}")
        
        time.sleep(0.3)
    
    # 统计 2024+ 论文
    for paper in all_papers:
        try:
            year = int(paper.get("year", 0))
            if year >= 2024:
                year_2024_plus += 1
        except:
            pass
    
    # 去重
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        title_lower = paper["title"].lower().strip()
        if title_lower and title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)
    
    total = len(unique_papers)
    
    # 生成论文摘要
    print(f"\n📝 正在生成论文摘要...")
    for i, paper in enumerate(unique_papers[:5], 1):
        print(f"   [{i}/{min(5, total)}] {paper['title'][:35]}...")
        summary = generate_summary(paper)
        paper["summary"] = summary
        time.sleep(0.5)
    
    print(f"\n📊 总计: {total} 篇论文")
    print(f"📚 来源: {source_counts}")
    print(f"🆕 2024+: {year_2024_plus} 篇")
    
    # 显示Top论文
    print(f"\n🔥 Top论文:")
    for i, paper in enumerate(unique_papers[:3], 1):
        title = paper["title"][:50] + "..." if len(paper["title"]) > 50 else paper["title"]
        year = paper["year"]
        source = paper["source"]
        print(f"  {i}. {title} [{source}] {year}")
    
    # 保存
    discoveries_dir = Path.home() / ".config" / "deepseeker" / "discoveries"
    discoveries_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = discoveries_dir / f"papers_{today_str}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "papers": unique_papers,
            "stats": {
                "total": total,
                "sources": source_counts,
                "year_2024_plus": year_2024_plus
            },
            "timestamp": timestamp
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 论文已保存至: {output_file}")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "total_papers": total,
        "sources": source_counts,
        "year_2024_plus": year_2024_plus,
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")
    
    return result

if __name__ == "__main__":
    academic_search()
