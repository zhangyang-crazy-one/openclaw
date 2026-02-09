#!/usr/bin/env python3
"""
综合学术搜索引擎
聚合多个高质量学术数据源和搜索引擎
"""
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

# ==========================================
# 学术数据源配置
# ==========================================
ACADEMIC_SOURCES = {
    # arXiv - 预印本
    "arxiv": {
        "url": "http://export.arxiv.org/api/query",
        "enabled": True,
        "weight": 2,
    },
    # Semantic Scholar - AI 专用
    "semantic_scholar": {
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "enabled": True,
        "weight": 3,
        "params": {"fields": "title,abstract,authors,year,url,citationCount", "limit": 10},
    },
    # Crossref - 期刊论文
    "crossref": {
        "url": "https://api.crossref.org/works",
        "enabled": True,
        "weight": 2,
    },
    # PubMed - 生物医学
    "pubmed": {
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        "enabled": True,
        "weight": 2,
    },
    # OpenAlex - 开放学术
    "openalex": {
        "url": "https://api.openalex.org/works",
        "enabled": True,
        "weight": 2,
    },
    # Microsoft Academic (已退役，改用 OpenAlex)
    # ar5iv - arXiv 论文全文
    "ar5iv": {
        "url": "https://ar5iv.org/abs",
        "enabled": True,
        "weight": 1,
    },
}

# ==========================================
# 通用搜索引擎配置
# ==========================================
SEARCH_ENGINES = {
    # DuckDuckGo - 隐私搜索
    "duckduckgo": {
        "url": "https://api.duckduckgo.com/",
        "enabled": True,
        "weight": 1,
    },
    # Brave Search - 高质量
    "brave": {
        "url": "https://api.search.brave.com/res/v1/search",
        "enabled": False,  # 需要 API Key
        "weight": 3,
    },
    # Startpage - 隐私
    "startpage": {
        "url": "https://www.startpage.com/do/search",
        "enabled": False,
        "weight": 1,
    },
    # Bing (via SearXNG)
    "bing": {
        "url": "https://searx.be/search",
        "enabled": True,
        "weight": 2,
    },
}

# ==========================================
# 搜索分类模板
# ==========================================
QUERY_TEMPLATES = {
    "ai_research": [
        "artificial intelligence research 2024",
        "large language model optimization",
        "AI governance ethics safety",
        "neural network architecture",
        "transformer model training",
    ],
    "machine_learning": [
        "machine learning survey 2024",
        "deep learning reinforcement learning",
        "unsupervised learning clustering",
        "natural language processing",
        "computer vision transformer",
    ],
    "data_science": [
        "data governance framework",
        "metadata management quality",
        "knowledge graph construction",
        "data pipeline automation",
    ],
    "finance": [
        "stock market prediction AI",
        "cryptocurrency analysis blockchain",
        "algorithmic trading ML",
        "financial risk assessment",
    ],
}


def search_arxiv(query, limit=10):
    """搜索 arXiv 预印本"""
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={limit}"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            import re
            entries = re.findall(r'<entry>(.*?)</entry>', result.stdout, re.DOTALL)
            
            results = []
            for entry in entries[:limit]:
                title = re.search(r'<title>(.*?)</title>', entry)
                summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                link = re.search(r'<id>(.*?)</id>', entry)
                published = re.search(r'<published>(.*?)</published>', entry)
                authors = re.findall(r'<name>(.*?)</name>', entry)
                
                results.append({
                    "title": title.group(1).strip().replace('\n', ' ') if title else "Unknown",
                    "url": link.group(1).strip() if link else "",
                    "abstract": summary.group(1).strip().replace('\n', ' ')[:500] if summary else "",
                    "authors": authors[:3],
                    "year": published.group(1)[:4] if published else "",
                    "engine": "arXiv",
                    "citations": 0,
                })
            
            return results, "arXiv"
    except Exception as e:
        pass
    return [], "arXiv"


def search_semantic_scholar(query, limit=10):
    """搜索 Semantic Scholar"""
    try:
        params = {
            "query": query,
            "fields": "title,abstract,authors,year,url,citationCount,openAccessPdf",
            "limit": limit,
        }
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DeepSeeker/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for paper in data.get("data", []):
                results.append({
                    "title": paper.get("title", ""),
                    "url": paper.get("url", ""),
                    "abstract": paper.get("abstract", "")[:500],
                    "authors": [a.get("name", "") for a in paper.get("authors", [])[:3]],
                    "year": str(paper.get("year", "")),
                    "engine": "Semantic Scholar",
                    "citations": paper.get("citationCount", 0),
                    "pdf": paper.get("openAccessPdf", {}).get("url", ""),
                })
            
            return results, "Semantic Scholar"
    except Exception as e:
        pass
    return [], "Semantic Scholar"


def search_crossref(query, limit=10):
    """搜索 Crossref 期刊"""
    try:
        params = {
            "query": query,
            "rows": limit,
            "select": "title,author,published-print,URL,container-title",
        }
        url = f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DeepSeeker/1.0 (mailto:research@example.com)"}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for item in data.get("message", {}).get("items", []):
                results.append({
                    "title": item.get("title", [""])[0] if item.get("title") else "",
                    "url": item.get("URL", ""),
                    "abstract": "",  # Crossref 不提供摘要
                    "authors": [a.get("family", "") for a in item.get("author", [])[:3]],
                    "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0] if item.get("published-print") else "",
                    "engine": "Crossref",
                    "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                })
            
            return results, "Crossref"
    except Exception as e:
        pass
    return [], "Crossref"


def search_openalex(query, limit=10):
    """搜索 OpenAlex 开放学术"""
    try:
        params = {
            "search": query,
            "per-page": limit,
            "select": "id,title,abstract,authors,publication_year,host_venue,doi,open_access",
        }
        url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DeepSeeker/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for work in data.get("results", []):
                results.append({
                    "title": work.get("title", ""),
                    "url": work.get("doi", ""),
                    "abstract": work.get("abstract", "")[:500] if work.get("abstract") else "",
                    "authors": [a.get("author_position", "") for a in work.get("authorships", [])[:3]],
                    "year": str(work.get("publication_year", "")),
                    "engine": "OpenAlex",
                    "open_access": work.get("open_access", {}).get("is_oa", False),
                })
            
            return results, "OpenAlex"
    except Exception as e:
        pass
    return [], "OpenAlex"


def search_duckduckgo(query, limit=10):
    """DuckDuckGo 通用搜索"""
    try:
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        url = f"https://api.duckduckgo.com/?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "DeepSeeker/1.0"})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for item in data.get("RelatedTopics", []):
                if "FirstURL" in item:
                    results.append({
                        "title": item.get("Text", "").split(" - ")[0] if " - " in item.get("Text", "") else item.get("Text", ""),
                        "url": item.get("FirstURL", ""),
                        "content": item.get("Text", ""),
                        "engine": "DuckDuckGo",
                    })
            
            return results[:limit], "DuckDuckGo"
    except Exception as e:
        pass
    return [], "DuckDuckGo"


# ==========================================
# 主搜索函数
# ==========================================

def academic_search(query, sources=None, limit_per_source=5):
    """学术搜索 - 多源聚合"""
    print("=" * 70)
    print(f"📚 学术搜索: {query}")
    print("=" * 70)
    
    if sources is None:
        sources = ["semantic_scholar", "arxiv", "crossref", "openalex"]
    
    all_results = []
    source_results = {}
    
    # 搜索各学术源
    search_funcs = {
        "arxiv": lambda q: search_arxiv(q, limit_per_source),
        "semantic_scholar": lambda q: search_semantic_scholar(q, limit_per_source),
        "crossref": lambda q: search_crossref(q, limit_per_source),
        "openalex": lambda q: search_openalex(q, limit_per_source),
    }
    
    for source in sources:
        if source in search_funcs and ACADEMIC_SOURCES.get(source, {}).get("enabled", False):
            print(f"🔍 搜索 {source}...")
            
            results, engine = search_funcs[source](query)
            
            if results:
                source_results[engine] = len(results)
                all_results.extend(results)
                print(f"   ✅ 找到 {len(results)} 篇论文")
            else:
                print(f"   ⚠️ 未找到结果")
            
            time.sleep(0.5)  # 避免请求过快
    
    # 去重（基于标题）
    seen_titles = set()
    unique_results = []
    for r in all_results:
        title_lower = r["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_results.append(r)
    
    # 按引用数/权重排序
    def sort_key(r):
        weight = ACADEMIC_SOURCES.get(r["engine"].lower().replace(" ", "_"), {}).get("weight", 1)
        citations = r.get("citations", 0)
        return (weight, citations)
    
    unique_results.sort(key=sort_key, reverse=True)
    
    print(f"\n📊 搜索统计:")
    for engine, count in source_results.items():
        print(f"   {engine}: {count} 篇")
    print(f"   去重后: {len(unique_results)} 篇")
    
    return unique_results[:limit_per_source * len(sources)]


def general_search(query, engines=None, limit=10):
    """通用搜索"""
    print("=" * 70)
    print(f"🔍 搜索: {query}")
    print("=" * 70)
    
    if engines is None:
        engines = ["duckduckgo"]
    
    all_results = []
    
    for engine in engines:
        if engine in SEARCH_ENGINES and SEARCH_ENGINES[engine].get("enabled", False):
            print(f"🔍 搜索 {engine}...")
            
            if engine == "duckduckgo":
                results, _ = search_duckduckgo(query, limit)
                all_results.extend(results)
                print(f"   ✅ 找到 {len(results)} 条")
            
            time.sleep(0.3)
    
    print(f"\n📊 总计: {len(all_results)} 条结果")
    
    return all_results[:limit]


def display_results(results, title="搜索结果"):
    """显示搜索结果"""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}")
    
    for i, r in enumerate(results[:15], 1):
        print(f"\n{i}. {r.get('title', 'Unknown')[:70]}...")
        
        if r.get("authors"):
            authors = ", ".join(r["authors"][:3])
            print(f"   作者: {authors}")
        
        if r.get("year"):
            print(f"   年份: {r['year']}")
        
        if r.get("citations"):
            print(f"   引用: {r['citations']}")
        
        if r.get("journal"):
            print(f"   期刊: {r['journal']}")
        
        print(f"   来源: {r.get('engine', 'unknown')}")
        
        if r.get("url"):
            print(f"   链接: {r['url'][:60]}...")
    
    print()


def save_results(query, results, search_type="academic"):
    """保存搜索结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_dir = Path.home() / ".config" / "deepseeker" / "searches"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{search_type}_{timestamp}.json"
    output_file = output_dir / filename
    
    data = {
        "query": query,
        "type": search_type,
        "timestamp": timestamp,
        "count": len(results),
        "results": results,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存至: {output_file}")
    return output_file


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="综合学术搜索引擎")
    parser.add_argument("--query", "-q", type=str, help="搜索查询")
    parser.add_argument("--academic", "-a", action="store_true", help="学术搜索模式")
    parser.add_argument("--finance", "-f", action="store_true", help="财经搜索模式")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    parser.add_argument("--save", "-s", action="store_true", help="保存结果")
    parser.add_argument("--sources", "-S", type=str, help="指定数据源 (逗号分隔)")
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: python3 academic_search.py --query '关键词'")
        print("选项:")
        print("  --academic, -a   学术搜索模式")
        print("  --finance, -f    财经搜索模式")
        print("  --json, -j       JSON 输出")
        print("  --save, -s       保存结果")
        print("  --sources, -S    指定数据源: arxiv,semantic_scholar,crossref,openalex")
        return
    
    # 解析数据源
    sources = None
    if args.sources:
        sources = args.sources.split(",")
    
    # 执行搜索
    if args.academic:
        results = academic_search(args.query, sources=sources)
        search_type = "academic"
    elif args.finance:
        # 财经搜索 = 通用搜索 + 财经关键词
        results = academic_search(f"{args.query} finance stock market", sources=sources)
        search_type = "finance"
    else:
        results = general_search(args.query)
        search_type = "general"
    
    # 显示结果
    if results:
        display_results(results, f"搜索结果: {args.query}")
    
    # JSON 输出
    if args.json and results:
        print("\n---OUTPUT_START---")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print("---OUTPUT_END---")
    
    # 保存结果
    if args.save and results:
        save_results(args.query, results, search_type)


if __name__ == "__main__":
    main()
