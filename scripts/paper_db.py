#!/usr/bin/env python3
"""
论文数据库 - 记录每日搜索的论文，避免重复
"""
import json
import csv
from datetime import datetime
from pathlib import Path

PAPER_DB_PATH = Path.home() / ".config" / "deepseeker" / "paper_database.csv"

# CSV 表头
FIELDNAMES = [
    "title",           # 论文标题
    "year",            # 发表年份
    "authors",        # 作者
    "cited_by",       # 引用数
    "arxiv_id",       # arXiv ID
    "doi",            # DOI
    "journal",        # 期刊
    "source",         # 来源 (arXiv/OpenAlex)
    "search_date",    # 搜索日期
    "category",       # 领域分类
    "oa_status",      # OA 状态
]


def init_db():
    """初始化数据库文件"""
    if not PAPER_DB_PATH.exists():
        PAPER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PAPER_DB_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def add_papers(papers):
    """添加论文到数据库"""
    init_db()
    
    # 读取已存在的标题
    existing_titles = set()
    with open(PAPER_DB_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_titles.add(row["title"][:50].lower())
    
    # 添加新论文
    new_count = 0
    today = datetime.now().strftime("%Y-%m-%d")
    
    with open(PAPER_DB_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        
        for paper in papers:
            title_key = paper.get("title", "")[:50].lower()
            
            # 跳过已存在的
            if title_key in existing_titles:
                continue
            
            row = {
                "title": paper.get("title", ""),
                "year": paper.get("year", ""),
                "authors": ", ".join(paper.get("authors", [])[:3]),
                "cited_by": paper.get("cited_by", 0),
                "arxiv_id": paper.get("arxiv_id", ""),
                "doi": paper.get("doi", ""),
                "journal": paper.get("journal", ""),
                "source": paper.get("source", "Unknown"),
                "search_date": today,
                "category": paper.get("category", ""),
                "oa_status": paper.get("oa_status", ""),
            }
            
            writer.writerow(row)
            existing_titles.add(title_key)
            new_count += 1
    
    return new_count


def get_papers(limit=50, year_filter=None, category_filter=None):
    """查询论文"""
    init_db()
    
    results = []
    with open(PAPER_DB_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if year_filter and row["year"] != str(year_filter):
                continue
            if category_filter and row["category"] != category_filter:
                continue
            results.append(row)
    
    # 按引用数排序
    results.sort(key=lambda x: int(x.get("cited_by", 0)), reverse=True)
    
    return results[:limit]


def check_duplicate(title):
    """检查论文是否已存在"""
    init_db()
    
    title_key = title[:50].lower()
    with open(PAPER_DB_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["title"][:50].lower() == title_key:
                return True
    return False


def get_stats():
    """获取数据库统计"""
    init_db()
    
    stats = {
        "total": 0,
        "by_year": {},
        "by_category": {},
        "by_source": {},
        "top_cited": [],
    }
    
    with open(PAPER_DB_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total"] += 1
            
            # by year
            year = row["year"]
            stats["by_year"][year] = stats["by_year"].get(year, 0) + 1
            
            # by category
            cat = row["category"]
            if cat:
                stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            
            # by source
            src = row["source"]
            stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
    
    return stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python paper_db.py add <json_file>  - 添加论文")
        print("  python paper_db.py stats            - 查看统计")
        print("  python paper_db.py list             - 列出最近论文")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "add":
        # 从 JSON 文件添加论文
        if len(sys.argv) < 3:
            print("Usage: python paper_db.py add <json_file>")
            sys.exit(1)
        
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        papers = data.get("papers", [])
        count = add_papers(papers)
        print(f"✅ 添加了 {count} 篇新论文")
    
    elif cmd == "stats":
        stats = get_stats()
        print(f"📊 论文数据库统计")
        print(f"总论文数: {stats['total']}")
        print(f"\n按年份:")
        for year, count in sorted(stats["by_year"].items(), reverse=True):
            print(f"  {year}: {count}")
        print(f"\n按分类:")
        for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print(f"\n按来源:")
        for src, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
            print(f"  {src}: {count}")
    
    elif cmd == "list":
        papers = get_papers(20)
        print(f"📚 最近论文 (按引用数):")
        for i, p in enumerate(papers, 1):
            cited = p.get("cited_by", 0)
            print(f"{i}. [{p['year']}] {p['title'][:50]}...")
            print(f"   🔥 {cited} citations | {p['category']}")
    
    else:
        print(f"Unknown command: {cmd}")
