#!/usr/bin/env python3
"""
Paper Reader - 论文阅读助手
支持专业论文报告格式
"""
import argparse
import json
import os
import sys
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# 配置
CACHE_DIR = Path(os.environ.get('PAPER_READER_CACHE_DIR', Path.home() / '.cache' / 'paper-reader')
CACHE_TTL_DAYS = 7

API_KEY = os.environ.get('MINIMAX_API_KEY', '')
BASE_URL = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimaxi.com/anthropic/v1')
MODEL = os.environ.get('MINIMAX_MODEL', 'MiniMax-M2.5')


def get_cache_key(topic, source='arxiv'):
    return hashlib.md5(f"{topic}:{source}".encode()).hexdigest()


def load_cache(topic, source='arxiv'):
    cache_file = CACHE_DIR / f"{get_cache_key(topic, source)}.json"
    if cache_file.exists():
        import time
        mtime = cache_file.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        if age_days < CACHE_TTL_DAYS:
            with open(cache_file) as f:
                return json.load(f)
    return None


def save_cache(topic, source, data):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{get_cache_key(topic, source)}.json"
    with open(cache_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_arxiv(topic, limit=3):
    """从 arXiv 获取论文"""
    import urllib.parse
    query = f"all:{topic}"
    url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    papers = []
    
    for entry in root.findall('atom:entry', ns)[:limit]:
        paper = {
            'id': entry.find('atom:id', ns).text,
            'title': entry.find('atom:title', ns).text.replace('\n', ' ').strip(),
            'summary': entry.find('atom:summary', ns).text.replace('\n', ' ').strip()[:2000],
            'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
            'published': entry.find('atom:published', ns).text[:10],
            'source': 'arxiv',
        }
        if '/abs/' in paper['id']:
            paper['arxiv_id'] = paper['id'].split('/')[-1]
        papers.append(paper)
    
    return papers


def summarize_paper(paper):
    """AI 总结"""
    if not API_KEY:
        return {'summary': paper.get('summary', '')[:500], 'key_points': [], 'tags': [], 'contributions': []}
    
    prompt = """分析以下论文，提取结构化信息。中文回复。
格式：
摘要: 2-3句话
关键要点: 3-5点
标签: 2-4个标签
核心贡献: 2-3点
    """
    
    content = f"标题: {paper.get('title', '')}\n作者: {', '.join(paper.get('authors', [])[:3])}\n摘要: {paper.get('summary', '')}"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": MODEL,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": f"{prompt}\n\n{content}"}]
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/messages", headers=headers, json=data, timeout=60)
        result = resp.json()
        
        if 'content' in result:
            for c in result['content']:
                if c.get('type') == 'text':
                    return parse_ai_response(c['text'])
    except Exception as e:
        print(f"AI 总结失败: {e}")
    
    return {'summary': paper.get('summary', '')[:500], 'key_points': [], 'tags': [], 'contributions': []}


def parse_ai_response(text):
    """解析 AI 响应"""
    lines = text.strip().split('\n')
    result = {'summary': '', 'key_points': [], 'tags': [], 'contributions': []}
    key = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('摘要:'):
            result['summary'] = line.replace('摘要:', '').strip()
            key = None
        elif line.startswith('关键要点:'):
            result['summary'] = line.replace('关键要点:', '').strip()
            key = 'key_points'
        elif line.startswith('标签:'):
            result['tags'] = [t.strip() for t in line.replace('标签:', '').split(',')]
            key = None
        elif line.startswith('核心贡献:'):
            result['contributions'].append(line.replace('核心贡献:', '').strip())
            key = 'contributions'
        elif line and key and line[0].isdigit() or line.startswith('•') or line.startswith('-'):
            result[key].append(line.lstrip('•-0123456789. ').strip())
    
    return result


def generate_markdown(paper, summary):
    """生成 Markdown 格式"""
    arxiv_id = paper.get('arxiv_id', '')
    
    md = f"""# {paper.get('title', '')[:80]}

> **摘要**  
> {summary.get('summary', paper.get('summary', '')[:200])}

---

## 核心贡献
{chr(10).join([f'{i+1}. {c}' for i, c in enumerate(summary.get('contributions', [])]) if summary.get('contributions') else '无'}

## 关键要点
{chr(10).join([f'- {p}' for p in summary.get('key_points', [])]) if summary.get('key_points') else '无'}

## 标签
{', '.join([f'#{t}' for t in summary.get('tags', ['paper'])])}

---

**来源**: {paper.get('source', '').upper()}: {arxiv_id or paper.get('id', '')}

---
*获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    return md


def main():
    parser = argparse.ArgumentParser(description='Paper Reader - 论文阅读助手')
    parser.add_argument('--topic', '-t', default='AI', help='论文主题')
    parser.add_argument('--source', '-s', default='arxiv', choices=['arxiv', 'semantic'])
    parser.add_argument('--limit', '-l', type=int, default=3)
    parser.add_argument('--format', '-f', default='markdown', choices=['markdown', 'obsidian', 'text'])
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--output', '-o')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("📚 Paper Reader - 论文阅读助手")
    print("=" * 50)
    print(f"主题: {args.topic}")
    print(f"数据源: {args.source}")
    print(f"数量: {args.limit}")
    
    # 检查缓存
    if not args.no_cache:
        cached = load_cache(args.topic, args.source)
        papers = cached if cached else None
    else:
        papers = None
    
    # 获取论文
    if papers is None:
        print(f"从 {args.source} 获取论文...")
        try:
            if args.source == 'arxiv':
                papers = fetch_arxiv(args.topic, args.limit)
            save_cache(args.topic, args.source, papers)
            print(f"获取 {len(papers)} 篇论文")
        except Exception as e:
            print(f"获取失败: {e}")
            return
    
    # 处理论文
    output_dir = Path(args.output) if args.output else CACHE_DIR / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, paper in enumerate(papers):
        print(f"\n[{i+1}/{len(papers)}] {paper.get('title', '')[:50]}...")
        
        summary = summarize_paper(paper)
        print(f"  摘要: {summary.get('summary', '')[:50]}...")
        
        if args.format == 'markdown':
            md = generate_markdown(paper, summary)
            safe_title = ''.join(c for c in paper.get('title', 'untitled')[:30] if c.isalnum() or c in ' -')
            filename = output_dir / f"{safe_title}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"  已保存: {filename.name}")
    
    print("\n完成!")


if __name__ == "__main__":
    main()
