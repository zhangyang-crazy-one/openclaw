#!/usr/bin/env python3
"""
GitHub Trending 简报生成脚本
直接从 GitHub API 获取热门项目数据
"""

import json
import urllib.request
import sys

def get_github_trending(days=30, limit=10):
    """获取 GitHub 热门项目"""
    # 近30天创建的项目，按星数排序
    url = f"https://api.github.com/search/repositories?q=created:>2026-02-01&sort=stars&order=desc&per_page={limit}"
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('items', [])[:limit]
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []

def format_report():
    """生成简报"""
    repos = get_github_trending()
    
    if not repos:
        return "⚠️ 无法获取 GitHub 数据"
    
    report = ["🐙 **GitHub 热门项目简报**", ""]
    
    categories = {
        "AI/Agent": [],
        "开发工具": [],
        "其他": []
    }
    
    for repo in repos:
        lang = repo.get('language', '') or ''
        name = repo['full_name']
        stars = repo['stargazers_count']
        desc = (repo.get('description') or '暂无描述')[:60]
        
        item = {
            'name': name,
            'stars': f"⭐ {stars:,}",
            'lang': f"🔹{lang}" if lang else "",
            'desc': desc
        }
        
        # 简单分类
        name_lower = name.lower()
        if any(k in name_lower for k in ['agent', 'llm', 'ai', 'claw', 'model']):
            categories["AI/Agent"].append(item)
        elif any(k in name_lower for k in ['cli', 'tool', 'dev', 'code']):
            categories["开发工具"].append(item)
        else:
            categories["其他"].append(item)
    
    # 输出分类简报
    for cat, items in categories.items():
        if items:
            report.append(f"**{cat}**")
            for item in items[:3]:  # 每类最多3个
                stars_str = f"⭐{item['stars']}" if '⭐' not in item['stars'] else item['stars']
                report.append(f"- **{item['name']}** {item['stars']} {item['lang']}")
                report.append(f"  {item['desc']}")
            report.append("")
    
    return "\n".join(report)

if __name__ == "__main__":
    print(format_report())
