#!/usr/bin/env python3
"""
Paper Reader - 论文阅读助手 v2.0
支持专业论文报告格式 (Markdown/Obsidian/PDF)
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
CACHE_DIR = Path(os.environ.get('PAPER_READER_CACHE_DIR', Path.home() / '.cache' / 'paper-reader'))
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
        return {
            'summary': paper.get('summary', '')[:500],
            'tldr': paper.get('summary', '')[:150],
            'key_points': [],
            'tags': [],
            'contributions': [],
            'method': '',
            'results': {}
        }
    
    prompt = """分析以下论文，提取结构化信息。中文回复。
格式：
TL;DR: 一句话总结（不超过50字）
摘要: 2-3句话
关键要点: 3-5点（每点不超过30字）
标签: 2-4个标签
核心贡献: 2-3点
方法: 用一两句话描述方法
实验结果: 列出主要指标（格式：指标名: 数值）
    """
    
    content = f"标题: {paper.get('title', '')}\n作者: {', '.join(paper.get('authors', [])[:3])}\n摘要: {paper.get('summary', '')}"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": MODEL,
        "max_tokens": 800,
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
    
    return {
        'summary': paper.get('summary', '')[:500],
        'tldr': paper.get('summary', '')[:150],
        'key_points': [],
        'tags': [],
        'contributions': [],
        'method': '',
        'results': {}
    }


def parse_ai_response(text):
    """解析 AI 响应"""
    lines = text.strip().split('\n')
    result = {
        'summary': '',
        'tldr': '',
        'key_points': [],
        'tags': [],
        'contributions': [],
        'method': '',
        'results': {}
    }
    
    current_key = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('TL;DR:'):
            result['tldr'] = line.replace('TL;DR:', '').strip()[:150]
            current_key = None
        elif line.startswith('摘要:'):
            result['summary'] = line.replace('摘要:', '').strip()
            current_key = None
        elif line.startswith('关键要点:'):
            result['summary'] = line.replace('关键要点:', '').strip()
            current_key = 'key_points'
        elif line.startswith('标签:'):
            result['tags'] = [t.strip() for t in line.replace('标签:', '').split(',')]
            current_key = None
        elif line.startswith('核心贡献:'):
            result['contributions'].append(line.replace('核心贡献:', '').strip())
            current_key = 'contributions'
        elif line.startswith('方法:'):
            result['method'] = line.replace('方法:', '').strip()
            current_key = None
        elif ':' in line and current_key == 'results':
            # 解析实验结果: 指标: 数值
            parts = line.split(':', 1)
            if len(parts) == 2:
                result['results'][parts[0].strip()] = parts[1].strip()
        elif line.startswith('实验结果:'):
            current_key = 'results'
        elif current_key and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
            # 添加到当前列表
            item = line.lstrip('•-0123456789. ').strip()
            if current_key in ['key_points', 'contributions']:
                result[current_key].append(item)
    
    return result


def generate_markdown(paper, summary):
    """生成 Markdown 格式"""
    arxiv_id = paper.get('arxiv_id', '')
    
    # 构建实验结果表格
    results_table = ""
    if summary.get('results'):
        rows = []
        for k, v in summary['results'].items():
            rows.append(f"| {k} | {v} |")
        results_table = "\n## 实验结果\n" + "\n".join(["| 指标 | 结果 |", "|-----|------|"] + rows)
    
    md = f"""# {paper.get('title', '')[:80]}

> **TL;DR**  
> {summary.get('tldr', paper.get('summary', '')[:150])}

---

## 摘要
{summary.get('summary', paper.get('summary', '')[:500])}

---

## 核心贡献
{chr(10).join([f'{i+1}. {c}' for i, c in enumerate(summary.get('contributions', []))]) if summary.get('contributions') else '无'}

## 关键要点
{chr(10).join([f'- {p}' for p in summary.get('key_points', [])]) if summary.get('key_points') else '无'}

## 方法论
{summary.get('method', '无')}

{results_table}

## 标签
{', '.join([f'`{t}`' for t in summary.get('tags', ['paper'])])}

---

**来源**: {paper.get('source', '').upper()}: {arxiv_id or paper.get('id', '')}

---
*获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    return md


def generate_obsidian(paper, summary):
    """生成 Obsidian 格式"""
    arxiv_id = paper.get('arxiv_id', '')
    date_str = datetime.now().strftime('%Y-%m-%d')
    tags_str = ', '.join([f'"{t}"' for t in summary.get('tags', ['paper'])])
    
    yaml = f"""---
title: "{paper.get('title', '')[:60]}"
authors: {json.dumps(paper.get('authors', [])[:3])}
date: "{date_str}"
tags: [{tags_str}]
arxiv: "{arxiv_id}"
type: paper-note
---

# {paper.get('title', '')[:80]}

> **TL;DR** {summary.get('tldr', '')}

## 摘要
{summary.get('summary', paper.get('summary', '')[:500])}

## 核心贡献
{chr(10).join([f'1. {c}' for c in summary.get('contributions', [])]) if summary.get('contributions') else '无'}

## 关键要点
{chr(10).join([f'- {p}' for p in summary.get('key_points', [])]) if summary.get('key_points') else '无'}

## 方法
{summary.get('method', '无')}

## 实验结果
| 指标 | 结果 |
|-----|------|
{chr(10).join([f'| {k} | {v} |' for k, v in summary.get('results', {}).items()])}

---

**来源**: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})

---
*笔记创建于: {date_str}*
"""
    return yaml


def generate_pdf(paper, summary, output_path):
    """生成 PDF 格式"""
    try:
        from pdf_generator import PaperPDFGenerator
        
        # 合并论文数据和摘要
        paper_data = {
            'title': paper.get('title', ''),
            'authors': paper.get('authors', []),
            'arxiv_id': paper.get('arxiv_id', ''),
            'published': paper.get('published', ''),
            'tldr': summary.get('tldr', paper.get('summary', '')[:150]),
            'abstract': summary.get('summary', paper.get('summary', '')[:800]),
            'contributions': summary.get('contributions', []),
            'key_points': summary.get('key_points', []),
            'method': summary.get('method', ''),
            'results': summary.get('results', {}),
            'references': []
        }
        
        pdf = PaperPDFGenerator()
        return pdf.generate_single(paper_data, output_path)
    except ImportError:
        print("错误: 请安装 fpdf 库 (pip install fpdf)")
        return None
    except Exception as e:
        print(f"PDF 生成失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Paper Reader - 论文阅读助手 v2.0')
    parser.add_argument('--topic', '-t', default='AI', help='论文主题')
    parser.add_argument('--source', '-s', default='arxiv', choices=['arxiv', 'semantic'])
    parser.add_argument('--limit', '-l', type=int, default=3, help='获取论文数量')
    parser.add_argument('--format', '-f', default='markdown', 
                       choices=['markdown', 'obsidian', 'pdf', 'all'],
                       help='输出格式')
    parser.add_argument('--no-cache', action='store_true', help='强制刷新缓存')
    parser.add_argument('--output', '-o', help='输出目录')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📚 Paper Reader - 论文阅读助手 v2.0")
    print("=" * 60)
    print(f"主题: {args.topic}")
    print(f"数据源: {args.source}")
    print(f"数量: {args.limit}")
    print(f"格式: {args.format}")
    
    # 检查缓存
    if not args.no_cache:
        cached = load_cache(args.topic, args.source)
        papers = cached if cached else None
    else:
        papers = None
    
    # 获取论文
    if papers is None:
        print(f"\n从 {args.source} 获取论文...")
        try:
            if args.source == 'arxiv':
                papers = fetch_arxiv(args.topic, args.limit)
            save_cache(args.topic, args.source, papers)
            print(f"✅ 获取 {len(papers)} 篇论文")
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            return
    
    # 输出目录
    output_dir = Path(args.output) if args.output else CACHE_DIR / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理论文
    print(f"\n{'='*60}")
    print("📝 生成报告...")
    print("=" * 60)
    
    all_papers = []
    
    for i, paper in enumerate(papers):
        print(f"\n[{i+1}/{len(papers)}] {paper.get('title', '')[:50]}...")
        
        # AI 总结
        summary = summarize_paper(paper)
        print(f"   TL;DR: {summary.get('tldr', '')[:40]}...")
        
        # 安全文件名
        safe_title = ''.join(c for c in paper.get('title', f'paper_{i}')[:30] 
                           if c.isalnum() or c in ' -')
        
        # 生成各格式
        if args.format in ['markdown', 'all']:
            md = generate_markdown(paper, summary)
            md_path = output_dir / f"{safe_title}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"   ✅ Markdown: {md_path.name}")
        
        if args.format in ['obsidian', 'all']:
            obs = generate_obsidian(paper, summary)
            obs_path = output_dir / f"{safe_title}_obsidian.md"
            with open(obs_path, 'w', encoding='utf-8') as f:
                f.write(obs)
            print(f"   ✅ Obsidian: {obs_path.name}")
        
        if args.format in ['pdf', 'all']:
            pdf_path = output_dir / f"{safe_title}.pdf"
            pdf_result = generate_pdf(paper, summary, str(pdf_path))
            if pdf_result:
                print(f"   ✅ PDF: {pdf_path.name}")
            else:
                print(f"   ❌ PDF 生成失败")
        
        # 保存摘要数据供后续使用
        all_papers.append({
            'paper': paper,
            'summary': summary
        })
    
    print(f"\n{'='*60}")
    print(f"✅ 完成! 共处理 {len(papers)} 篇论文")
    print(f"📂 输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
