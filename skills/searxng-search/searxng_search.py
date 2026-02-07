#!/usr/bin/env python3
"""
综合搜索引擎
使用多个备用源获取搜索结果
"""
import json
import time
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error

# 备用搜索 API
SEARCH_APIS = {
    "ddg": {
        "url": "https://api.duckduckgo.com/",
        "params": {"format": "json"},
    },
    "searx": [
        "https://searx.be",
        "https://search.bus-hit.me",
    ],
}

# 学术搜索源
ACADEMIC_SOURCES = [
    ("arXiv", "http://export.arxiv.org/api/query"),
    ("Semantic Scholar", "https://api.semanticscholar.org/graph/v1/paper/search"),
]

# 财经数据源
FINANCE_SOURCES = {
    "akshare": True,  # 已安装
    "baostock": True,  # 已安装
}


def search_duckduckgo(query):
    """DuckDuckGo 搜索"""
    try:
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        url = f"{SEARCH_APIS['ddg']['url']}?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "DeepSeeker/1.0"})
        
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for item in data.get("RelatedTopics", []):
                if "FirstURL" in item:
                    results.append({
                        "title": item.get("Text", "").split(" - ")[0] if " - " in item.get("Text", "") else item.get("Text", ""),
                        "url": item.get("FirstURL", ""),
                        "content": item.get("Text", ""),
                        "engine": "duckduckgo",
                    })
            
            return results
    except Exception as e:
        return None


def search_arxiv(query, limit=10):
    """arXiv 学术搜索"""
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={limit}"
        
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # 简单解析 XML
            import re
            entries = re.findall(r'<entry>(.*?)</entry>', result.stdout, re.DOTALL)
            
            results = []
            for entry in entries[:limit]:
                title = re.search(r'<title>(.*?)</title>', entry)
                summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                link = re.search(r'<id>(.*?)</id>', entry)
                
                results.append({
                    "title": title.group(1).strip() if title else "Unknown",
                    "url": link.group(1).strip() if link else "",
                    "content": summary.group(1).strip()[:200] if summary else "",
                    "engine": "arxiv",
                })
            
            return results
    except Exception as e:
        pass
    
    return []


def academic_search(query):
    """学术搜索"""
    print("=" * 60)
    print(f"📚 学术搜索: {query}")
    print("=" * 60)
    
    # arXiv 搜索
    print("🔍 搜索 arXiv...")
    results = search_arxiv(query)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 条 arXiv 结果:\n")
        
        for i, r in enumerate(results[:10], 1):
            print(f"{i}. {r['title'][:70]}...")
            print(f"   {r['url']}")
            print()
        
        return results
    
    print("未找到结果")
    return []


def general_search(query, limit=10):
    """综合搜索"""
    print("=" * 60)
    print(f"🔍 综合搜索: {query}")
    print("=" * 60)
    
    # DuckDuckGo 搜索
    print("🔍 搜索 DuckDuckGo...")
    results = search_duckduckgo(query)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 条结果:\n")
        
        for i, r in enumerate(results[:limit], 1):
            print(f"{i}. {r['title'][:60]}")
            print(f"   {r['url'][:60]}...")
            print()
        
        return results
    
    print("未找到结果")
    return []


def finance_search(query):
    """财经搜索"""
    print("=" * 60)
    print(f"💰 财经搜索: {query}")
    print("=" * 60)
    
    # 使用 DuckDuckGo 搜索财经新闻
    finance_query = f"{query} stock market financial news"
    results = search_duckduckgo(finance_query)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 条结果:\n")
        
        for i, r in enumerate(results[:10], 1):
            print(f"{i}. {r['title']}")
            print(f"   {r['url'][:60]}...")
            print()
        
        return results
    
    print("未找到结果")
    return []


def save_results(query, results, search_type="general"):
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
    
    parser = argparse.ArgumentParser(description="综合搜索引擎")
    parser.add_argument("--query", "-q", type=str, help="搜索查询")
    parser.add_argument("--academic", "-a", action="store_true", help="学术搜索")
    parser.add_argument("--finance", "-f", action="store_true", help="财经搜索")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    parser.add_argument("--save", "-s", action="store_true", help="保存结果")
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: python3 searxng_search.py --query '关键词'")
        print("选项: --academic (学术) --finance (财经) --json --save")
        return
    
    # 选择搜索类型
    if args.academic:
        results = academic_search(args.query)
        search_type = "academic"
    elif args.finance:
        results = finance_search(args.query)
        search_type = "finance"
    else:
        results = general_search(args.query)
        search_type = "general"
    
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
