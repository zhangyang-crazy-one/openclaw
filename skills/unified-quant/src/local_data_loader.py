"""
本地数据加载模块
功能: 复用已有的本地数据进行量化分析
"""
import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# 数据目录
DATA_DIR = Path("/home/liujerry/金融数据")
PREDICTIONS_DIR = DATA_DIR / "predictions"
FUNDAMENTALS_DIR = DATA_DIR / "fundamentals"


class LocalDataLoader:
    """本地数据加载器"""
    
    def __init__(self):
        self.cache = {}
        self._load_stock_list()
    
    def _load_stock_list(self):
        """加载股票列表"""
        # 尝试从多个数据源加载
        candidates = [
            FUNDAMENTALS_DIR / "chuangye_stock_list.csv",
            FUNDAMENTALS_DIR / "chuangye_names.json",
        ]
        
        for f in candidates:
            if f.exists():
                if f.suffix == '.json':
                    with open(f) as fp:
                        self.cache['stock_list'] = json.load(fp)
                else:
                    # CSV格式
                    stocks = []
                    with open(f) as fp:
                        reader = csv.DictReader(fp)
                        for row in reader:
                            stocks.append(row)
                    self.cache['stock_list'] = stocks
                return
    
    def load_top_stocks(self, n: int = 20) -> List[Dict]:
        """加载TOP评分股票"""
        # 优先使用最新的分析结果
        candidates = [
            PREDICTIONS_DIR / "chuangye_final_top20.json",
            PREDICTIONS_DIR / "top20_final_ranking.json",
        ]
        
        for f in candidates:
            if f.exists():
                with open(f) as fp:
                    data = json.load(fp)
                top = data.get('top_by_score', [])
                return top[:n] if isinstance(top, list) else []
        
        return []
    
    def load_stock_fundamentals(self, stock_code: str) -> Optional[Dict]:
        """加载单只股票的基本面数据"""
        # 搜索所有数据文件
        search_codes = [
            stock_code.replace('sz.', ''),
            stock_code.replace('sz.3', '3'),
            stock_code,
        ]
        
        # 从chuangye_final_top20.json搜索
        top_file = PREDICTIONS_DIR / "chuangye_final_top20.json"
        if top_file.exists():
            with open(top_file) as fp:
                data = json.load(fp)
            
            for stock in data.get('top_by_score', []):
                code = stock.get('code', '')
                if code in search_codes:
                    return stock
        
        return None
    
    def get_analysis_summary(self) -> Dict:
        """获取分析摘要"""
        summary = {
            "total_stocks": 0,
            "last_analysis_date": None,
            "top_stocks": [],
        }
        
        # 从股票列表获取总数
        if 'stock_list' in self.cache:
            summary['total_stocks'] = len(self.cache['stock_list'])
        
        # 从预测结果获取最新日期
        top_file = PREDICTIONS_DIR / "chuangye_final_top20.json"
        if top_file.exists():
            with open(top_file) as fp:
                data = json.load(fp)
            summary['last_analysis_date'] = data.get('date', '')
            summary['top_stocks'] = [
                {"code": s['code'], "score": s.get('composite_score', 0)}
                for s in data.get('top_by_score', [])[:10]
            ]
        
        return summary
    
    def load_financial_data(self, stock_code: str) -> Optional[Dict]:
        """加载财务数据"""
        # 简化：从推荐基本面数据中查找
        file = FUNDAMENTALS_DIR / "recommended_fundamentals.json"
        if file.exists():
            with open(file) as fp:
                data = json.load(fp)
            
            # 搜索匹配的股票
            code = stock_code.replace('sz.', '')
            for item in data:
                if item.get('code') == code or item.get('股票代码') == code:
                    return item
        
        return None


def load_chuangye_top20() -> List[Dict]:
    """便捷函数: 加载创业板TOP20股票"""
    loader = LocalDataLoader()
    return loader.load_top_stocks(20)


def get_stock_info(stock_code: str) -> Dict:
    """便捷函数: 获取股票信息"""
    loader = LocalDataLoader()
    
    # 尝试多个数据源
    data = loader.load_stock_fundamentals(stock_code)
    if not data:
        data = loader.load_financial_data(stock_code)
    
    return data or {}


if __name__ == "__main__":
    loader = LocalDataLoader()
    
    print("=== 本地数据分析系统 ===\n")
    
    # 摘要
    summary = loader.get_analysis_summary()
    print(f"📊 分析股票数: {summary['total_stocks']}")
    print(f"📅 最新分析: {summary['last_analysis_date']}")
    
    # TOP10
    print(f"\n🏆 TOP10 股票:")
    for i, s in enumerate(summary['top_stocks'][:10], 1):
        print(f"   {i}. {s['code']} (评分: {s['score']:.1f})")
