#!/usr/bin/env python3
"""
量化金融学术研究技能
为投资决策提供学术支撑
"""
import json
import re
import subprocess
import time
import warnings
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.parse

warnings.filterwarnings('ignore')

# ==========================================
# 搜索查询模板 - 量化金融细分领域
# ==========================================
QUERY_TEMPLATES = {
    # 量化投资策略
    "quant": [
        "quantitative investing factor model",
        "statistical arbitrage strategy",
        "high frequency trading algorithm",
        "momentum factor investing",
        "value factor screening",
        "smart beta ETF construction",
    ],
    # 机器学习量化
    "ml": [
        "LSTM stock prediction",
        "transformer financial forecasting",
        "machine learning asset pricing",
        "deep reinforcement learning trading",
        "neural network volatility forecasting",
        "AI hedge fund strategy",
    ],
    # 风险管理
    "risk": [
        "value at risk VaR modeling",
        "hedging strategies derivatives",
        "tail risk portfolio protection",
        "liquidity risk assessment",
        "systemic risk detection",
        "counterparty risk analysis",
    ],
    # 投资组合优化
    "portfolio": [
        "portfolio optimization machine learning",
        "mean-variance efficient frontier",
        "risk parity strategy",
        "maximum diversification ratio",
        "minimum variance portfolio",
        "factor based allocation",
    ],
    # 资产定价
    "pricing": [
        "CAPM asset pricing anomalies",
        "factor investing equity returns",
        "momentum premium stock",
        "quality factor investing",
        "low volatility anomaly",
        "ETF arbitrage pricing",
    ],
    # 行为金融
    "behavior": [
        "behavioral finance market anomalies",
        "investor sentiment prediction",
        "crowd trading behavior",
        "market microstructure",
        "price discovery mechanism",
        "liquidity provision",
    ],
}

# ==========================================
# 学术数据源
# ==========================================
ACADEMIC_SOURCES = {
    "arxiv": {
        "url": "http://export.arxiv.org/api/query",
        "enabled": True,
        "weight": 2,
        "category": "quantitative finance",
    },
    "semantic_scholar": {
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "enabled": True,
        "weight": 3,
        "category": "Artificial Intelligence",
    },
    "crossref": {
        "url": "https://api.crossref.org/works",
        "enabled": True,
        "weight": 2,
        "category": "Finance",
    },
}

# ==========================================
# 投资因子映射
# ==========================================
INVESTMENT_FACTORS = {
    "momentum": {"name": "动量因子", "description": "过去收益高的资产未来收益也高"},
    "value": {"name": "价值因子", "description": "低估值资产长期表现优于高估值资产"},
    "size": {"name": "规模因子", "description": "小盘股长期收益优于大盘股"},
    "low_vol": {"name": "低波动因子", "description": "低波动资产风险调整后收益更优"},
    "quality": {"name": "质量因子", "description": "高盈利、高增长公司表现更优"},
    "dividend": {"name": "分红因子", "description": "高分红公司更稳定"},
    "liquidity": {"name": "流动性因子", "description": "流动性好的资产更易交易"},
}


def search_arxiv(query, limit=10):
    """搜索 arXiv 量化金融论文"""
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={limit}"
        
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
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
                        "title": title.group(1).strip().replace('\n', ' '),
                        "url": link.group(1).strip(),
                        "abstract": (summary.group(1).strip().replace('\n', ' ')[:300] if summary else ""),
                        "year": published.group(1)[:4] if published else "",
                        "source": "arXiv",
                        "citations": 0,
                        "keywords": extract_keywords(query),
                    })
            
            return results, "arXiv"
    except Exception as e:
        pass
    return [], "arXiv"


def search_semantic_scholar(query, limit=10):
    """搜索 Semantic Scholar 金融论文"""
    try:
        params = {
            "query": query,
            "fields": "title,abstract,authors,year,url,citationCount,topics",
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
                topics = paper.get("topics", [])
                topic_names = [t.get("topic", "") for t in topics[:3]]
                
                results.append({
                    "title": paper.get("title", ""),
                    "url": paper.get("url", ""),
                    "abstract": paper.get("abstract", "")[:400],
                    "year": str(paper.get("year", "")),
                    "authors": [a.get("name", "") for a in paper.get("authors", [])[:3]],
                    "source": "Semantic Scholar",
                    "citations": paper.get("citationCount", 0),
                    "topics": topic_names,
                    "keywords": extract_keywords(query),
                })
            
            return results, "Semantic Scholar"
    except Exception as e:
        pass
    return [], "Semantic Scholar"


def search_crossref_finance(query, limit=10):
    """搜索 Crossref 金融期刊"""
    try:
        params = {
            "query": query,
            "rows": limit,
            "select": "title,author,published-print,URL,container-title,type",
            "filter": "type:journal-article",
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
                year = item.get("published-print", {}).get("date-parts", [[None]])[0]
                results.append({
                    "title": item.get("title", [""])[0] if item.get("title") else "",
                    "url": item.get("URL", ""),
                    "year": str(year[0]) if year else "",
                    "authors": [a.get("family", "") for a in item.get("author", [])[:3]],
                    "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                    "source": "Crossref",
                    "citations": 0,
                    "keywords": extract_keywords(query),
                })
            
            return results, "Crossref"
    except Exception as e:
        pass
    return [], "Crossref"


def extract_keywords(query):
    """提取关键词"""
    query_lower = query.lower()
    keywords = []
    
    factor_keywords = ["factor", "momentum", "value", "quality", "low volatility", "size"]
    ml_keywords = ["machine learning", "LSTM", "neural", "deep learning", "transformer"]
    quant_keywords = ["quantitative", "trading", "arbitrage", "portfolio", "optimization"]
    
    for kw in factor_keywords:
        if kw in query_lower:
            keywords.append(kw)
    
    for kw in ml_keywords:
        if kw in query_lower:
            keywords.append(kw)
    
    for kw in quant_keywords:
        if kw in query_lower:
            keywords.append(kw)
    
    return keywords if keywords else ["general"]


def quant_research(query, research_type="quant", limit_per_source=5):
    """
    量化金融学术研究主函数
    
    Args:
        query: 搜索查询
        research_type: 研究类型 (quant/ml/risk/portfolio/pricing/behavior)
        limit_per_source: 每个数据源的结果数量
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("=" * 80)
    print("📊 量化金融学术研究")
    print(f"🔍 查询: {query}")
    print(f"📁 类型: {research_type}")
    print(f"⏰ 时间: {timestamp}")
    print("=" * 80)
    
    # 选择搜索查询
    queries = [query]
    if research_type in QUERY_TEMPLATES:
        queries.extend(QUERY_TEMPLATES[research_type])
    
    # 去重查询
    queries = list(dict.fromkeys(queries))[:3]
    
    all_results = []
    source_stats = {}
    
    # 搜索各数据源
    search_funcs = {
        "arXiv": lambda q: search_arxiv(q, limit_per_source),
        "Semantic Scholar": lambda q: search_semantic_scholar(q, limit_per_source),
        "Crossref": lambda q: search_crossref_finance(q, limit_per_source),
    }
    
    for source, search_func in search_funcs.items():
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
            # 按引用数排序
            r["_score"] = r.get("citations", 0)
            unique_results.append(r)
    
    unique_results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    
    # 统计信息
    print(f"\n📊 搜索统计:")
    for source, count in source_stats.items():
        print(f"   • {source}: {count} 篇")
    print(f"   • 去重后: {len(unique_results)} 篇")
    
    return unique_results


def generate_investment_recommendation(papers):
    """基于论文生成投资建议"""
    if not papers:
        return []
    
    recommendations = []
    
    # 分析论文中的因子
    factor_count = {}
    ml_count = 0
    risk_count = 0
    
    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        keywords = paper.get("keywords", [])
        
        # 检测因子
        for factor, info in INVESTMENT_FACTORS.items():
            if factor in title or factor in abstract or factor in keywords:
                factor_count[factor] = factor_count.get(factor, 0) + 1
        
        # 检测 ML/AI
        if any(kw in title or kw in abstract for kw in ["machine learning", "neural", "AI", "deep learning", "LSTM"]):
            ml_count += 1
        
        # 检测风险管理
        if any(kw in title or kw in abstract for kw in ["risk", "volatility", "hedging", "VaR"]):
            risk_count += 1
    
    # 生成建议
    recommendations.append({
        "type": "因子分析",
        "content": f"发现 {len(papers)} 篇相关论文",
        "factors": factor_count,
    })
    
    if ml_count > 0:
        recommendations.append({
            "type": "AI/ML 量化",
            "content": f"{ml_count} 篇使用机器学习的量化策略研究",
            "suggestion": "关注 AI 因子在组合优化中的应用",
        })
    
    if risk_count > 0:
        recommendations.append({
            "type": "风险管理",
            "content": f"{risk_count} 篇关于风险建模的研究",
            "suggestion": "考虑加入波动率因子和尾部风险对冲",
        })
    
    # 热门因子
    if factor_count:
        top_factors = sorted(factor_count.items(), key=lambda x: x[1], reverse=True)[:3]
        recommendations.append({
            "type": "热门因子",
            "content": "研究热点因子排名",
            "top_factors": [{"name": INVESTMENT_FACTORS.get(f, {}).get("name", f), "count": c} for f, c in top_factors],
        })
    
    return recommendations


def display_results(papers, show_recommendations=True):
    """显示搜索结果"""
    if not papers:
        print("\n未找到相关论文")
        return
    
    print(f"\n{'=' * 80}")
    print("📄 论文列表")
    print(f"{'=' * 80}")
    
    for i, paper in enumerate(papers[:15], 1):
        title = paper.get("title", "Unknown")[:70]
        year = paper.get("year", "")
        citations = paper.get("citations", 0)
        source = paper.get("source", "")
        
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
        
        if paper.get("journal"):
            print(f"   📖 {paper['journal']}")
        
        print(f"   🔗 {source}")
        
        # 投资相关关键词
        keywords = paper.get("keywords", [])
        if keywords:
            print(f"   🏷️ 关键词: {', '.join(keywords)}")
    
    # 生成投资建议
    if show_recommendations:
        recommendations = generate_investment_recommendation(papers)
        
        if recommendations:
            print(f"\n{'=' * 80}")
            print("💡 投资建议")
            print(f"{'=' * 80}")
            
            for rec in recommendations:
                print(f"\n📌 {rec['type']}")
                print(f"   {rec['content']}")
                
                if rec.get("suggestion"):
                    print(f"   💎 建议: {rec['suggestion']}")
                
                if rec.get("factors"):
                    print(f"   因子分布:")
                    for f, c in rec.get("factors", {}).items():
                        name = INVESTMENT_FACTORS.get(f, {}).get("name", f)
                        print(f"      • {name}: {c} 篇")
                
                if rec.get("top_factors"):
                    print(f"   热门:")
                    for tf in rec.get("top_factors", []):
                        print(f"      • {tf['name']}: {tf['count']} 篇")


def save_results(query, papers, research_type="quant"):
    """保存搜索结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    output_dir = Path.home() / ".config" / "deepseeker" / "quant_research"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{research_type}_{timestamp}.json"
    output_file = output_dir / filename
    
    recommendations = generate_investment_recommendation(papers)
    
    data = {
        "query": query,
        "type": research_type,
        "timestamp": timestamp,
        "paper_count": len(papers),
        "recommendations": recommendations,
        "papers": papers,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存至: {output_file}")
    return output_file


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="量化金融学术研究")
    parser.add_argument("--query", "-q", type=str, help="搜索查询")
    parser.add_argument("--type", "-t", type=str, default="quant",
                       choices=["quant", "ml", "risk", "portfolio", "pricing", "behavior"],
                       help="研究类型")
    parser.add_argument("--limit", "-l", type=int, default=10, help="每个数据源的结果数")
    parser.add_argument("--recommend", "-r", action="store_true", help="显示投资建议")
    parser.add_argument("--save", "-s", action="store_true", help="保存结果")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: python3 quant_research.py --query '关键词'")
        print()
        print("研究类型:")
        print("  --type quant      量化投资策略 (默认)")
        print("  --type ml         机器学习量化")
        print("  --type risk       风险管理")
        print("  --type portfolio  投资组合优化")
        print("  --type pricing    资产定价")
        print("  --type behavior   行为金融")
        print()
        print("选项:")
        print("  --recommend, -r   显示投资建议")
        print("  --save, -s        保存结果")
        print("  --json, -j         JSON 输出")
        print()
        print("示例:")
        print("  python3 quant_research.py --query 'factor investing'")
        print("  python3 quant_research.py --query 'LSTM' --type ml --recommend")
        print("  python3 quant_research.py --query 'risk parity' --type portfolio --save")
        return
    
    # 执行搜索
    papers = quant_research(args.query, args.type, args.limit)
    
    # 显示结果
    display_results(papers, show_recommendations=args.recommend)
    
    # JSON 输出
    if args.json and papers:
        print("\n---OUTPUT_START---")
        print(json.dumps(papers, ensure_ascii=False, indent=2))
        print("---OUTPUT_END---")
    
    # 保存结果
    if args.save and papers:
        save_results(args.query, papers, args.type)


if __name__ == "__main__":
    main()
