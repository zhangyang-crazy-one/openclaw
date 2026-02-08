#!/usr/bin/env python3
"""
学术论文搜索脚本
使用 arXiv API 搜索学术论文
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

# 搜索关键词
SEARCH_QUERIES = [
    "AI data governance automation",
    "data stewardship machine learning",
    "metadata extraction neural networks",
    "data quality AI benchmark",
    "DAMA framework",
]

def search_arxiv(query):
    """搜索 arXiv"""
    try:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&max_results=50"
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            text=True,
            timeout=30
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
            "source": "arxiv"
        })
    
    return papers

def academic_search():
    """学术搜索主函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 60)
    print(f"📚 DeepSeeker Academic Search")
    print(f"{today_str} {timestamp.split()[1]}")
    print("=" * 60)
    
    all_papers = []
    source_counts = {"arxiv": 0}
    year_2024_plus = 0
    
    for query in SEARCH_QUERIES:
        print(f"\n📌 {query}")
        
        arxiv_result = search_arxiv(query)
        if "Error" not in arxiv_result:
            arxiv_papers = parse_arxiv_results(arxiv_result)
            all_papers.extend(arxiv_papers)
            source_counts["arxiv"] += len(arxiv_papers)
            print(f"  ✅ arxiv: {len(arxiv_papers)}")
        else:
            print(f"  ❌ arxiv: 搜索失败")
    
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
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)
    
    total = len(unique_papers)
    
    print(f"\n📊 总计: {total} 篇")
    print(f"📚 来源: {source_counts}")
    print(f"🆕 2024+: {year_2024_plus} 篇")
    
    # 显示示例论文
    print(f"\n📄 示例论文:")
    for i, paper in enumerate(unique_papers[:3], 1):
        title = paper["title"][:60] + "..." if len(paper["title"]) > 60 else paper["title"]
        year = paper["year"]
        source = paper["source"]
        print(f"  • {title} [{source}] {year}")
    
    # 保存到 discoveries 目录
    discoveries_dir = Path.home() / ".config" / "deepseeker" / "discoveries"
    discoveries_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = discoveries_dir / f"papers_{today_str}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_papers, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 论文已保存至: {output_file}")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "total_papers": total,
        "sources": source_counts,
        "year_2024_plus": year_2024_plus,
        "papers": unique_papers[:10],
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")
    
    return result

if __name__ == "__main__":
    academic_search()
