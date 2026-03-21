"""
价值投资筛选模块
整合护城河分析、安全边际计算、Piotroski F-Score
"""

import pandas as pd
import numpy as np
import os
from typing import List, Dict, Tuple
from moat_analysis import MoatAnalyzer
from safety_margin import SafetyMarginAnalyzer
from pitroski import PiotroskiAnalyzer


class ValueScreener:
    """
    价值投资筛选器
    
    基于五阶段选股模型：
    1. 界定能力圈
    2. 质量指标初筛 (ROE, 财务健康)
    3. 护城河分析
    4. 安全边际计算
    5. Piotroski F-Score风险审核
    """
    
    def __init__(self, data_dir: str = '/home/liujerry/金融数据/stocks_clean'):
        self.data_dir = data_dir
        self.moat_analyzer = MoatAnalyzer()
        self.safety_analyzer = SafetyMarginAnalyzer()
        self.piotroski_analyzer = PiotroskiAnalyzer()
        
        # 筛选参数
        self.params = {
            'min_roe': 15,  # 最低ROE (%)
            'min_roe_years': 10,  # ROE要求年数
            'max_debt_ratio': 0.5,  # 最高负债权益比
            'min_safety_margin': 10,  # 最低安全边际 (%)
            'min_piotroski_score': 5,  # 最低Piotroski分数
        }
    
    def load_stock_data(self, stock_code: str) -> Dict:
        """加载股票数据"""
        data = {'price': 0, 'financial': {}}
        
        # 加载价格数据
        csv_path = os.path.join(self.data_dir, f'{stock_code}.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                data['price'] = df.iloc[-1]['close']
        
        return data
    
    def screen(self, stock_codes: List[str]) -> List[Dict]:
        """
        筛选符合条件的股票
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            符合条件的股票列表
        """
        results = []
        
        for code in stock_codes:
            try:
                result = self.analyze_stock(code)
                if self._pass_screening(result):
                    results.append(result)
            except Exception as e:
                print(f"分析 {code} 时出错: {e}")
        
        # 按安全边际排序
        results.sort(key=lambda x: x.get('safety_margin', 0), reverse=True)
        
        return results
    
    def analyze_stock(self, stock_code: str) -> Dict:
        """分析单只股票"""
        data = self.load_stock_data(stock_code)
        current_price = data.get('price', 0)
        
        # 模拟财务数据 (实际应从API获取)
        financial_data = self._get_financial_data(stock_code)
        
        result = {
            'stock_code': stock_code,
            'name': self._get_stock_name(stock_code),
            'price': current_price,
            'roe': financial_data.get('roe', 0),
            'debt_ratio': financial_data.get('debt_ratio', 0),
            'moat': {},
            'safety_margin': {},
            'piotroski': {},
            'pass_screening': False,
        }
        
        # 1. 护城河分析
        moat_result = self.moat_analyzer.analyze(stock_code, financial_data)
        result['moat'] = moat_result
        
        # 2. 安全边际计算
        safety_result = self.safety_analyzer.analyze(
            stock_code,
            {'price': current_price},
            financial_data
        )
        result['safety_margin'] = safety_result
        
        # 3. Piotroski F-Score
        piotroski_result = self.piotroski_analyzer.analyze(stock_code, financial_data)
        result['piotroski'] = piotroski_result
        
        # 综合评分
        result['total_score'] = self._calculate_total_score(result)
        
        return result
    
    def _get_financial_data(self, stock_code: str) -> Dict:
        """获取财务数据 (简化版，实际应从API获取)"""
        # 这里应该调用 akshare 获取真实数据
        # 简化返回测试数据
        return {
            'roe': 22.58,
            'net_income': 6.27e8,
            'free_cash_flow': 5e8,
            'shares_outstanding': 4.34e8,
            'eps': 1.42,
            'gross_margin': 26.99,
            'operating_margin': 15.38,
            'debt_ratio': 0.5,
            'industry': '汽车零部件',
            'wacc': 0.10,
            'growth_rate': 0.10,
        }
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        # 简化处理
        return f"股票{stock_code}"
    
    def _pass_screening(self, result: Dict) -> bool:
        """判断是否通过筛选"""
        # ROE检查
        if result.get('roe', 0) < self.params['min_roe']:
            return False
        
        # 安全边际检查
        sm = result.get('safety_margin', {})
        if sm.get('safety_margin', -100) < self.params['min_safety_margin']:
            return False
        
        # Piotroski检查
        pit = result.get('piotroski', {})
        if pit.get('f_score', 0) < self.params['min_piotroski_score']:
            return False
        
        result['pass_screening'] = True
        return True
    
    def _calculate_total_score(self, result: Dict) -> float:
        """计算综合评分"""
        score = 0
        
        # 护城河 (0-5)
        score += result.get('moat', {}).get('moat_score', 0)
        
        # 安全边际 (0-5)
        sm = result.get('safety_margin', {}).get('safety_margin', 0)
        if sm > 50:
            score += 5
        elif sm > 30:
            score += 4
        elif sm > 10:
            score += 3
        elif sm > 0:
            score += 2
        else:
            score += 1
        
        # Piotroski (0-9)
        score += result.get('piotroski', {}).get('f_score', 0)
        
        # ROE (0-2)
        roe = result.get('roe', 0)
        if roe > 20:
            score += 2
        elif roe > 15:
            score += 1
        
        return score
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成筛选报告"""
        if not results:
            return "没有找到符合条件的股票"
        
        report = []
        report.append("=" * 80)
        report.append("📊 价值投资筛选报告")
        report.append("=" * 80)
        report.append("")
        
        for i, r in enumerate(results, 1):
            report.append(f"## {i}. {r['name']} ({r['stock_code']})")
            report.append(f"   价格: {r['price']:.2f}元")
            report.append(f"   ROE: {r['roe']:.2f}%")
            report.append(f"   护城河: {r['moat'].get('moat_rating', '无')}")
            report.append(f"   安全边际: {r['safety_margin'].get('safety_margin', 0):.1f}%")
            report.append(f"   Piotroski F-Score: {r['piotroski'].get('f_score', 0)}/9")
            report.append(f"   建议仓位: {r['safety_margin'].get('position_size', 'N/A')}")
            report.append(f"   综合评分: {r['total_score']}/21")
            report.append("")
        
        return "\n".join(report)


def screen_value_stocks(stock_codes: List[str]) -> List[Dict]:
    """价值投资筛选主函数"""
    screener = ValueScreener()
    results = screener.screen(stock_codes)
    return results


if __name__ == "__main__":
    # 测试
    codes = ['300926', '300502', '600519']
    screener = ValueScreener()
    results = screener.screen(codes)
    print(screener.generate_report(results))
