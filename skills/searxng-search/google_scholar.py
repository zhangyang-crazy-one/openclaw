#!/usr/bin/env python3
"""
Google Scholar 学术搜索
使用 scholarly 包（本地爬取）或 SerpApi
"""
import json
import time
import warnings
from datetime import datetime
from pathlib import Path

# SerpApi 配置
SERPAPI_KEY = ""  # 从环境变量读取


def search_scholarly(query, limit=10, timeout=30):
    """使用 scholarly 包搜索 Google Scholar"""
    try:
        from scholarly import scholarly
        warnings.filterwarnings('ignore')
        
        # 搜索出版物
        results = []
        search_gen = scholarly.search_pubs(query, citations=False)
        
        for i, paper in enumerate(search_gen):
            if i >= limit:
                break
            
            bib = paper.get('bib', {})
            
            result = {
                "title": bib.get('title', ''),
                "url": paper.get('pub_url', ''),
                "authors": bib.get('author', []),
                "year": bib.get('year', ''),
                "venue": bib.get('venue', ''),
                "abstract": bib.get('abstract', '')[:500],
                "citations": paper.get('citedby', 0),
                "engine": "Google Scholar (scholarly)",
            }
            results.append(result)
            
            if (i + 1) % 3 == 0:
                print(f"   📄 已获取 {i+1} 篇...")
        
        return results, "Google Scholar"
        
    except Exception as e:
        return None, str(e)


def search_serpapi_google_scholar(query, limit=10):
    """使用 SerpApi 搜索 Google Scholar"""
    global SERPAPI_KEY
    
    if not SERPAPI_KEY:
        SERPAPI_KEY = __import__('os').environ.get("SERPAPI_KEY", "")
    
    if not SERPAPI_KEY:
        return None, "需要 SERPAPI_KEY"
    
    try:
        import urllib.request
        import urllib.parse
        
        params = {
            "engine": "google_scholar",
            "q": query,
            "num": limit,
            "api_key": SERPAPI_KEY,
        }
        
        url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "DeepSeeker/1.0"})
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "authors": item.get("publication_info", {}).get("authors", []),
                    "year": item.get("publication_info", {}).get("year", ""),
                    "citations": item.get("cited_by", {}).get("value", 0),
                    "engine": "Google Scholar (SerpApi)",
                })
            
            return results, "Google Scholar (SerpApi)"
    
    except Exception as e:
        return None, str(e)


def google_scholar_search(query, use_scholarly=True, use_serpapi=False, limit=10):
    """Google Scholar 搜索主函数"""
    print("=" * 70)
    print(f"🎓 Google Scholar 搜索: {query}")
    print("=" * 70)
    
    all_results = []
    sources_tried = []
    
    # 方法1: scholarly 包
    if use_scholarly:
        print("🔍 使用 scholarly (Google Scholar 本地爬取)...")
        print("   ⚠️ 速度较慢，需要 10-30 秒...")
        
        start = time.time()
        results, source = search_scholarly(query, limit=limit)
        elapsed = int(time.time() - start)
        
        if results:
            all_results.extend(results)
            sources_tried.append(f"scholarly: {len(results)} 篇 ({elapsed}s)")
            print(f"   ✅ 成功! 找到 {len(results)} 篇 ({elapsed}s)")
        else:
            sources_tried.append(f"scholarly: {source}")
            print(f"   ⚠️ 不可用: {source}")
        
        time.sleep(2)  # 避免请求过快
    
    # 方法2: SerpApi
    if use_serpapi:
        print("🔍 使用 SerpApi...")
        results, source = search_serpapi_google_scholar(query, limit)
        
        if results:
            all_results.extend(results)
            sources_tried.append(f"SerpApi: {len(results)} 篇")
            print(f"   ✅ 找到 {len(results)} 篇")
        else:
            sources_tried.append(f"SerpApi: {source}")
            print(f"   ⚠️ {source}")
    
    # 去重
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)
    
    print(f"\n📊 搜索统计:")
    for s in sources_tried:
        print(f"   • {s}")
    print(f"   去重后: {len(unique_results)} 篇")
    
    return unique_results


def display_results(results):
    """显示搜索结果"""
    if not results:
        print("\n未找到结果")
        return
    
    print(f"\n{'=' * 70}")
    print("搜索结果")
    print(f"{'=' * 70}")
    
    for i, r in enumerate(results[:10], 1):
        print(f"\n{i}. {r.get('title', 'Unknown')[:65]}...")
        
        authors = r.get('authors', [])
        if isinstance(authors, list):
            authors = ", ".join(authors[:3])
        if authors:
            print(f"   作者: {authors}")
        
        if r.get('year'):
            print(f"   年份: {r.get('year')}")
        
        if r.get('citations'):
            print(f"   引用: {r.get('citations')}")
        
        if r.get('venue'):
            print(f"   期刊: {r.get('venue')}")
        
        print(f"   来源: {r.get('engine', 'unknown')}")
        
        if r.get('url'):
            print(f"   链接: {r.get('url')[:60]}...")
    
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Google Scholar 学术搜索")
    parser.add_argument("--query", "-q", type=str, help="搜索查询")
    parser.add_argument("--limit", "-l", type=int, default=10, help="结果数量")
    parser.add_argument("--serpapi", "-s", action="store_true", help="使用 SerpApi")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: python3 google_scholar.py --query '关键词'")
        print("选项:")
        print("  --limit, -l  结果数量 (默认 10)")
        print("  --serpapi, -s  使用 SerpApi (需要 API Key)")
        print("  --json, -j   JSON 输出")
        print()
        print("示例:")
        print("  python3 google_scholar.py --query 'transformer attention'")
        print("  python3 google_scholar.py --query 'AI' --limit 5")
        print()
        print("SerpApi 配置:")
        print("  export SERPAPI_KEY='your_key'")
        print("  python3 google_scholar.py --query 'ML' --serpapi")
        return
    
    results = google_scholar_search(
        args.query,
        use_scholarly=True,
        use_serpapi=args.serpapi,
        limit=args.limit
    )
    
    if results:
        display_results(results)
        
        if args.json:
            print("\n---OUTPUT_START---")
            print(json.dumps(results, ensure_ascii=False, indent=2))
            print("---OUTPUT_END---")


if __name__ == "__main__":
    main()
