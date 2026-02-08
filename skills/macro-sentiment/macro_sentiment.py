#!/usr/bin/env python3
"""
宏观与情绪分析技能
洞察市场情绪、经济周期与政策影响
"""
import json
import re
import subprocess
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

# ==========================================
# 研究分类查询模板
# ==========================================
QUERY_TEMPLATES = {
    # 宏观经济
    "macro": [
        "monetary policy transmission",
        "interest rate hiking cycle",
        "inflation expectations",
        "GDP growth forecasting",
        "fiscal stimulus impact",
    ],
    # 市场情绪
    "sentiment": [
        "investor sentiment market returns",
        "volatility index VIX predictive",
        "put call ratio analysis",
        "option market sentiment",
        "crowd behavior finance",
    ],
    # 美联储与央行
    "policy": [
        "Federal Reserve policy",
        "quantitative easing effects",
        "forward guidance communication",
        "yield curve signaling",
    ],
    # 经济周期
    "cycle": [
        "business cycle turning points",
        "recession prediction",
        "yield curve recession predictor",
    ],
    # 行为金融
    "behavior": [
        "herd behavior markets",
        "overconfidence trading",
        "loss aversion investing",
        "behavioral asset pricing",
    ],
}


def search_arxiv(query, limit=10):
    """搜索 arXiv"""
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query.replace(' ', '+')}&max_results={limit}"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "20", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            entries = re.findall(r'<entry>(.*?)</entry>', result.stdout, re.DOTALL)
            
            results = []
            for entry in entries[:limit]:
                title = re.search(r'<title>(.*?)</title>', entry)
                summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                link = re.search(r'<id>(.*?)</id>', entry)
                published = re.search(r'<published>(.*?)</published>', entry)
                
                if title and link:
                    results.append({
                        "title": title.group(1).strip().replace('\n', ' ')[:80],
                        "url": link.group(1).strip(),
                        "abstract": (summary.group(1).strip().replace('\n', ' ')[:300] if summary else ""),
                        "year": published.group(1)[:4] if published else "",
                        "source": "arXiv",
                    })
            
            return results, "arXiv"
    except Exception as e:
        print(f"   Error: {e}")
    return [], "arXiv"


def search_crossref(query, limit=10):
    """搜索 Crossref"""
    try:
        url = f"https://api.crossref.org/works?query={query.replace(' ', '+')}&rows={limit}"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            results = []
            
            for item in data.get("message", {}).get("items", []):
                year = item.get("published-print", {}).get("date-parts", [[None]])[0]
                results.append({
                    "title": item.get("title", [""])[0][:80] if item.get("title") else "",
                    "url": item.get("URL", ""),
                    "year": str(year[0]) if year else "",
                    "authors": [a.get("family", "") for a in item.get("author", [])[:2]],
                    "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                    "source": "Crossref",
                })
            
            return results, "Crossref"
    except Exception as e:
        print(f"   Error: {e}")
    return [], "Crossref"


def search_semantic_scholar(query, limit=10):
    """搜索 Semantic Scholar"""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query.replace(' ', '+')}&fields=title,abstract,authors,year,url,citationCount&limit={limit}"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "20", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            results = []
            
            for paper in data.get("data", []):
                results.append({
                    "title": paper.get("title", "")[:80],
                    "url": paper.get("url", ""),
                    "abstract": paper.get("abstract", "")[:300],
                    "year": str(paper.get("year", "")),
                    "authors": [a.get("name", "") for a in paper.get("authors", [])[:2]],
                    "source": "Semantic Scholar",
                    "citations": paper.get("citationCount", 0),
                })
            
            return results, "Semantic Scholar"
    except Exception as e:
        print(f"   Error: {e}")
    return [], "Semantic Scholar"


def search_google_scholar(query, limit=10):
    """通过 SerpAPI 搜索 Google Scholar (备用)"""
    api_key = ""  # 需要设置 SERPAPI_KEY
    
    if not api_key:
        return [], "Google Scholar"
    
    try:
        url = f"https://serpapi.com/search.json?engine=google_scholar&q={query.replace(' ', '+')}&api_key={api_key}"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            results = []
            
            for item in data.get("organic_results", [])[:limit]:
                results.append({
                    "title": item.get("title", "")[:80],
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")[:200],
                    "source": "Google Scholar",
                })
            
            return results, "Google Scholar"
    except Exception as e:
        print(f"   Error: {e}")
    return [], "Google Scholar"


def macro_sentiment_research(query, research_type="macro", limit_per_source=5):
    """宏观与情绪分析研究"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("=" * 80)
    print("📊 宏观与情绪分析研究")
    print(f"🔍 查询: {query}")
    print(f"📁 类型: {research_type}")
    print(f"⏰ 时间: {timestamp}")
    print("=" * 80)
    
    # 选择搜索查询
    queries = [query]
    if research_type in QUERY_TEMPLATES:
        queries.extend(QUERY_TEMPLATES[research_type])
    queries = list(dict.fromkeys(queries))[:3]
    
    all_results = []
    source_stats = {}
    
    # 搜索函数
    search_funcs = [
        ("arXiv", lambda q: search_arxiv(q, limit_per_source)),
        ("Semantic Scholar", lambda q: search_semantic_scholar(q, limit_per_source)),
        ("Crossref", lambda q: search_crossref(q, limit_per_source)),
    ]
    
    for source, search_func in search_funcs:
        print(f"\n🔍 搜索 {source}...")
        
        source_results = []
        for q in queries:
            results, _ = search_func(q)
            source_results.extend(results)
            time.sleep(0.5)
        
        # 去重
        seen_urls = set()
        unique_results = []
        for r in source_results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)
        
        if unique_results:
            all_results.extend(unique_results)
            source_stats[source] = len(unique_results)
            print(f"   ✅ {source}: {len(unique_results)} 篇")
        
        time.sleep(1)
    
    # 最终去重和排序
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            r["_score"] = r.get("citations", 0)
            unique_results.append(r)
    
    unique_results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    
    print(f"\n📊 搜索统计:")
    for source, count in source_stats.items():
        print(f"   • {source}: {count} 篇")
    print(f"   • 去重后: {len(unique_results)} 篇")
    
    return unique_results


def analyze_market_sentiment(papers):
    """分析市场情绪"""
    if not papers:
        return {"total": 0}
    
    analysis = {
        "total": len(papers),
        "themes": {},
        "findings": [],
    }
    
    theme_count = {"macro": 0, "sentiment": 0, "behavior": 0, "risk": 0}
    
    for paper in papers:
        title = (paper.get("title", "") + paper.get("abstract", "")).lower()
        
        if any(kw in title for kw in ["monetary", "interest", "fed", "policy"]):
            theme_count["macro"] += 1
        if any(kw in title for kw in ["sentiment", "volatility", "vix", "fear"]):
            theme_count["sentiment"] += 1
        if any(kw in title for kw in ["behavior", "herd", "overconfidence", "bias"]):
            theme_count["behavior"] += 1
        if any(kw in title for kw in ["risk", "crisis", "liquidity"]):
            theme_count["risk"] += 1
    
    analysis["themes"] = theme_count
    
    if theme_count["macro"] > 0:
        analysis["findings"].append(f"货币政策研究: {theme_count['macro']} 篇")
    if theme_count["sentiment"] > 0:
        analysis["findings"].append(f"市场情绪研究: {theme_count['sentiment']} 篇")
    if theme_count["behavior"] > 0:
        analysis["findings"].append(f"行为金融研究: {theme_count['behavior']} 篇")
    
    return analysis


def generate_market_analysis(papers, indicators=None):
    """生成市场分析报告"""
    if not papers:
        return {}
    
    analysis = analyze_market_sentiment(papers)
    
    # 情绪指标
    if indicators is None:
        indicators = {
            "VIX": {"value": 18.5, "status": "normal (偏低)"},
            "PCR": {"value": 0.95, "status": "中性"},
            "Margin": {"value": "历史高位", "status": "谨慎"},
        }
    
    analysis["indicators"] = indicators
    
    # 投资含义
    implications = []
    vix = indicators.get("VIX", {}).get("value", 20)
    
    if vix > 30:
        implications.append("⚠️ VIX 高位，市场恐慌，可能存在超卖机会")
    elif vix < 15:
        implications.append("⚠️ VIX 低位，市场自满，警惕回调风险")
    else:
        implications.append("✅ VIX 正常，市场情绪稳定")
    
    pcr = indicators.get("PCR", {}).get("value", 1.0)
    if pcr > 1.5:
        implications.append("📉 PCR 高位，看跌情绪浓厚")
    elif pcr < 0.7:
        implications.append("📈 PCR 低位，看涨情绪偏强")
    
    analysis["implications"] = implications
    
    return analysis


def display_results(papers, show_analysis=True):
    """显示研究结果"""
    if not papers:
        print("\n未找到相关论文")
        return
    
    print(f"\n{'=' * 80}")
    print("📄 论文列表")
    print(f"{'=' * 80}")
    
    for i, paper in enumerate(papers[:15], 1):
        title = paper.get("title", "Unknown")[:75]
        year = paper.get("year", "")
        source = paper.get("source", "")
        citations = paper.get("citations", 0)
        
        print(f"\n{i}. {title}...")
        
        if year:
            print(f"   📅 {year}")
        if citations:
            print(f"   📊 引用: {citations}")
        if paper.get("authors"):
            authors = paper["authors"]
            if isinstance(authors, list):
                authors = ", ".join(authors[:2])
            print(f"   👤 {authors}")
        print(f"   🔗 {source}")
    
    if show_analysis:
        analysis = generate_market_analysis(papers)
        
        print(f"\n{'=' * 80}")
        print("📊 市场情绪分析")
        print(f"{'=' * 80}")
        
        print(f"\n📈 主题分布:")
        for theme, count in analysis.get("themes", {}).items():
            if count > 0:
                names = {"macro": "货币政策", "sentiment": "市场情绪", "behavior": "行为金融", "risk": "风险"}
                print(f"   • {names.get(theme, theme)}: {count} 篇")
        
        print(f"\n😊 当前情绪指标:")
        for ind, data in analysis.get("indicators", {}).items():
            names = {"VIX": "VIX恐慌指数", "PCR": "看跌/看涨比率", "Margin": "保证金债务"}
            print(f"   • {names.get(ind, ind)}: {data.get('status', '')}")
        
        print(f"\n💡 投资含义:")
        for impl in analysis.get("implications", []):
            print(f"   {impl}")


def save_results(query, papers, research_type="macro"):
    """保存结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    output_dir = Path.home() / ".config" / "deepseeker" / "macro_sentiment"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{research_type}_{timestamp}.json"
    output_file = output_dir / filename
    
    data = {
        "query": query,
        "type": research_type,
        "timestamp": timestamp,
        "papers": papers,
        "analysis": generate_market_analysis(papers),
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存至: {output_file}")
    return output_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="宏观与情绪分析")
    parser.add_argument("--query", "-q", type=str, help="搜索查询")
    parser.add_argument("--type", "-t", type=str, default="macro",
                       choices=["macro", "sentiment", "policy", "cycle", "behavior"],
                       help="研究类型")
    parser.add_argument("--limit", "-l", type=int, default=8, help="结果数")
    parser.add_argument("--analyze", "-a", action="store_true", help="显示分析")
    parser.add_argument("--save", "-s", action="store_true", help="保存结果")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: python3 macro_sentiment.py --query '关键词'")
        print("  --type macro/sentiment/policy/cycle/behavior")
        print("  --analyze  显示市场分析")
        print("示例:")
        print("  python3 macro_sentiment.py --query 'investor sentiment' --type sentiment --analyze")
        return
    
    papers = macro_sentiment_research(args.query, args.type, args.limit)
    display_results(papers, show_analysis=args.analyze)
    
    if args.json and papers:
        print("\n---OUTPUT_START---")
        print(json.dumps(papers, ensure_ascii=False, indent=2))
        print("---OUTPUT_END---")
    
    if args.save and papers:
        save_results(args.query, papers, args.type)


if __name__ == "__main__":
    main()
