"""
学术论文引用模块
功能: 从arXiv/SSRN/Google Scholar获取权威论文，支持自动引用
"""
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class PaperCitation:
    """学术论文引用器"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "papers"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.papers_cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        cache_file = self.cache_dir / "papers_cache.json"
        if cache_file.exists():
            with open(cache_file) as f:
                self.papers_cache = json.load(f)
    
    def _save_cache(self):
        """保存缓存"""
        cache_file = self.cache_dir / "papers_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self.papers_cache, f, ensure_ascii=False, indent=2)
    
    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """搜索arXiv论文"""
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            # 简单解析XML响应
            entries = []
            # 这里应该用XML解析器，为了简化先用字符串处理
            # 实际使用可以用 feedparser 库
            return entries
        except Exception as e:
            print(f"arXiv搜索失败: {e}")
            return []
    
    def search_searxng(self, query: str, max_results: int = 5) -> List[Dict]:
        """使用SearXNG搜索学术论文"""
        # 这里可以调用本地SearXNG服务
        # 返回搜索结果
        return []
    
    def get_paper_info(self, title: str, year: int = None) -> Optional[Dict]:
        """获取论文信息"""
        # 先检查缓存
        cache_key = f"{title}_{year}"
        if cache_key in self.papers_cache:
            return self.papers_cache[cache_key]
        
        # 搜索论文
        results = self.search_arxiv(title, max_results=3)
        
        # 找到匹配的论文
        for r in results:
            if year and r.get('year') == year:
                self.papers_cache[cache_key] = r
                self._save_cache()
                return r
        
        # 如果没找到精确匹配的，返回第一个
        if results:
            self.papers_cache[cache_key] = results[0]
            self._save_cache()
            return results[0]
        
        return None
    
    def format_citation(self, paper: Dict, style: str = "academic") -> str:
        """格式化引用"""
        if not paper:
            return "[无引用]"
        
        if style == "academic":
            # 学术格式: Authors (Year). Title. Journal.
            authors = paper.get('authors', ['Unknown'])
            if isinstance(authors, list) and len(authors) > 2:
                authors = f"{authors[0]} et al."
            year = paper.get('year', 'n.d.')
            title = paper.get('title', 'Unknown')
            journal = paper.get('journal', '')
            
            if journal:
                return f"{authors} ({year}). {title}. {journal}."
            else:
                return f"{authors} ({year}). {title}."
        
        elif style == "compact":
            # 简洁格式: [Authors, Year]
            authors = paper.get('authors', ['Unknown'])
            if isinstance(authors, list) and len(authors) > 2:
                authors = f"{authors[0]} et al."
            year = paper.get('year', 'n.d.')
            return f"[{authors}, {year}]"
        
        return str(paper)
    
    def add_citation_to_analysis(self, analysis_text: str, claim: str, paper_topic: str) -> str:
        """为分析添加论文引用"""
        paper = self.get_paper_info(paper_topic)
        citation = self.format_citation(paper, "compact")
        
        # 在分析文本中添加引用
        # 格式: "结论X [citation]"
        return f"{analysis_text}\n\n**引用**: {citation}"


# 预定义的研究主题和经典论文
RESEARCH_TOPICS = {
    "stock_prediction": [
        {"topic": "LSTM stock prediction", "paper": " Hochreiter & Schmidhuber, 1997"},
        {"topic": "attention mechanism stock", "paper": "Vaswani et al., 2017"},
    ],
    "sentiment_trading": [
        {"topic": "sentiment analysis financial", "paper": "Bollen et al., 2011"},
    ],
    "portfolio_optimization": [
        {"topic": "modern portfolio theory", "paper": "Markowitz, 1952"},
    ],
    "factor_investing": [
        {"topic": " Fama-French three factor", "paper": "Fama & French, 1992"},
    ],
}


if __name__ == "__main__":
    citation = PaperCitation()
    paper = citation.get_paper_info("LSTM stock prediction")
    print(citation.format_citation(paper))
