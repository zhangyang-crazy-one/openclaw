#!/usr/bin/env python3
"""
论文关键词搜索脚本
根据关键词快速检索本地存储的学术论文
"""
import json
import sys
from pathlib import Path

DISCOVERY_DIR = Path.home() / ".config" / "deepseeker" / "discoveries"
INDEX_FILE = DISCOVERY_DIR / "keyword_index.json"

def load_index():
    """加载索引"""
    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

def load_papers():
    """加载所有论文"""
    papers = {}
    for pf in sorted(DISCOVERY_DIR.glob("papers_*.json")):
        try:
            with open(pf, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'papers' in data:
                for p in data['papers']:
                    if 'title' in p:
                        pid = len(papers)
                        papers[pid] = p
                        p['_source_file'] = pf.name
            elif isinstance(data, list):
                for p in data:
                    if 'title' in p:
                        pid = len(papers)
                        papers[pid] = p
                        p['_source_file'] = pf.name
        except Exception as e:
            continue
    return papers

def search_by_keyword(keyword, index_data, papers, top_n=10):
    """搜索包含关键词的论文"""
    kw = keyword.lower()
    keyword_to_papers = index_data['keyword_to_papers']
    
    # 精确匹配
    if kw in keyword_to_papers:
        paper_ids = keyword_to_papers[kw]
        match_type = "exact"
    # 2-gram匹配
    elif len(kw.split()) == 2:
        kw_underscore = kw.replace(' ', '_')
        if kw_underscore in keyword_to_papers:
            paper_ids = keyword_to_papers[kw_underscore]
            match_type = "2-gram"
        else:
            paper_ids = []
            match_type = "none"
    else:
        paper_ids = []
        match_type = "none"
    
    # 如果没有精确匹配，尝试模糊匹配
    if not paper_ids and match_type == "none":
        for k, v in keyword_to_papers.items():
            if kw in k:
                paper_ids.extend(v)
        paper_ids = list(set(paper_ids))
        match_type = "partial" if paper_ids else "none"
    
    total = len(paper_ids)
    paper_ids = paper_ids[:top_n]
    
    results = []
    for pid in paper_ids:
        if pid in papers:
            p = papers[pid]
            results.append({
                'title': p.get('title', ''),
                'authors': p.get('authors', [])[:3],
                'year': p.get('year', ''),
                'citations': p.get('citations', 0),
                'source': p.get('source', ''),
                'url': p.get('url', '')
            })
    
    return results, total, match_type

def main():
    if len(sys.argv) < 2:
        print("用法: python paper_keyword_search.py <关键词> [数量]")
        print("示例: python paper_keyword_search.py llm 20")
        sys.exit(1)
    
    keyword = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print(f"🔍 搜索关键词: '{keyword}'\n")
    
    # 加载数据
    index_data = load_index()
    papers = load_papers()
    
    # 搜索
    results, total, match_type = search_by_keyword(keyword, index_data, papers, top_n)
    
    print(f"找到 {total} 篇论文 (匹配类型: {match_type})\n")
    print("=" * 80)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   作者: {', '.join(r['authors'])}")
        print(f"   年份: {r['year']} | 引用: {r['citations']} | 来源: {r['source']}")
        print(f"   链接: {r['url']}")
    
    print("\n" + "=" * 80)
    print(f"\n索引统计: {index_data['paper_count']} 篇论文, {index_data['keywords_count']} 个关键词")

if __name__ == "__main__":
    main()
