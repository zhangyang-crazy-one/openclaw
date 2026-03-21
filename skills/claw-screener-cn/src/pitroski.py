"""
Piotroski F-Score 价值陷阱检测模块
基于Joseph Piotroski的研究，用于识别优质价值股
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class PiotroskiAnalyzer:
    """
    Piotroski F-Score 分析器
    
    F-Score是一个9分制评分系统，用于评估公司的财务实力：
    - 盈利能力 (4项)
    - 财务杠杆、流动性、源泉 (3项)
    - 运营效率 (2项)
    
    得分 >= 7: 优质公司
    得分 4-6: 中等
    得分 <= 3: 财务状况不佳
    """
    
    def __init__(self):
        self.criteria = {}
    
    def analyze(self, stock_code: str, financial_data: Dict) -> Dict:
        """
        计算 Piotroski F-Score
        
        Args:
            stock_code: 股票代码
            financial_data: 财务数据字典
            
        Returns:
            F-Score分析结果
        """
        result = {
            'stock_code': stock_code,
            'f_score': 0,
            'rating': '',
            'profitability_score': 0,
            'leverage_score': 0,
            'efficiency_score': 0,
            'details': {}
        }
        
        # ===== 盈利能力指标 (4项) =====
        
        # 1. ROE > 0 (资产回报率)
        roe = financial_data.get('roe', 0)
        if roe and roe > 0:
            result['f_score'] += 1
            result['profitability_score'] += 1
            result['details']['ROE > 0'] = f"✓ ROE = {roe:.2f}%"
        else:
            result['details']['ROE > 0'] = f"✗ ROE = {roe:.2f}%"
        
        # 2. ROA > 0 (资产回报率)
        roa = financial_data.get('roa', 0)
        if roa and roa > 0:
            result['f_score'] += 1
            result['profitability_score'] += 1
            result['details']['ROA > 0'] = f"✓ ROA = {roa:.2f}%"
        else:
            result['details']['ROA > 0'] = f"✗ ROA = {roa:.2f}%"
        
        # 3. 营业利润率 > 0
        op_margin = financial_data.get('operating_margin', 0)
        if op_margin and op_margin > 0:
            result['f_score'] += 1
            result['profitability_score'] += 1
            result['details']['营业利润率 > 0'] = f"✓ 营业利润率 = {op_margin:.2f}%"
        else:
            result['details']['营业利润率 > 0'] = f"✗ 营业利润率 = {op_margin:.2f}%"
        
        # 4. 现金流 > 0
        # 使用经营现金流/营业收入
        cfo = financial_data.get('cfo_ratio', 0)
        if cfo and cfo > 0:
            result['f_score'] += 1
            result['profitability_score'] += 1
            result['details']['经营现金流 > 0'] = f"✓ CFO比率 = {cfo:.2f}%"
        else:
            result['details']['经营现金流 > 0'] = f"✗ CFO比率 = {cfo:.2f}%"
        
        # ===== 财务杠杆、流动性、源泉 (3项) =====
        
        # 5. 负债权益比下降
        current_de_ratio = financial_data.get('debt_to_equity_current', 100)
        prev_de_ratio = financial_data.get('debt_to_equity_prev', 100)
        if current_de_ratio and prev_de_ratio and current_de_ratio < prev_de_ratio:
            result['f_score'] += 1
            result['leverage_score'] += 1
            result['details']['负债率下降'] = f"✓ {prev_de_ratio:.2f}% → {current_de_ratio:.2f}%"
        else:
            result['details']['负债率下降'] = f"✗ {prev_de_ratio:.2f}% → {current_de_ratio:.2f}%"
        
        # 6. 流动比率上升
        current_cr = financial_data.get('current_ratio_current', 1)
        prev_cr = financial_data.get('current_ratio_prev', 1)
        if current_cr and current_cr > prev_cr:
            result['f_score'] += 1
            result['leverage_score'] += 1
            result['details']['流动比率上升'] = f"✓ {prev_cr:.2f} → {current_cr:.2f}"
        else:
            result['details']['流动比率上升'] = f"✗ {prev_cr:.2f} → {current_cr:.2f}"
        
        # 7. 股东权益增长 (无稀释)
        # 避免发行新股导致的权益增长
        shares_change = financial_data.get('shares_change', 0)
        if shares_change and shares_change <= 0:
            result['f_score'] += 1
            result['leverage_score'] += 1
            result['details']['无稀释'] = f"✓ 股本无增长"
        else:
            result['details']['无稀释'] = f"✗ 股本增长 {shares_change:.1f}%"
        
        # ===== 运营效率 (2项) =====
        
        # 8. 毛利率上升
        current_gm = financial_data.get('gross_margin_current', 0)
        prev_gm = financial_data.get('gross_margin_prev', 0)
        if current_gm and prev_gm and current_gm > prev_gm:
            result['f_score'] += 1
            result['efficiency_score'] += 1
            result['details']['毛利率上升'] = f"✓ {prev_gm:.2f}% → {current_gm:.2f}%"
        else:
            result['details']['毛利率上升'] = f"✗ {prev_gm:.2f}% → {current_gm:.2f}%"
        
        # 9. 资产周转率上升
        current_at = financial_data.get('asset_turnover_current', 0)
        prev_at = financial_data.get('asset_turnover_prev', 0)
        if current_at and prev_at and current_at > prev_at:
            result['f_score'] += 1
            result['efficiency_score'] += 1
            result['details']['周转率上升'] = f"✓ {prev_at:.2f} → {current_at:.2f}"
        else:
            result['details']['周转率上升'] = f"✗ {prev_at:.2f} → {current_at:.2f}"
        
        # 评级
        if result['f_score'] >= 7:
            result['rating'] = '优质 (买入)'
        elif result['f_score'] >= 5:
            result['rating'] = '中等 (观望)'
        else:
            result['rating'] = '弱势 (卖出)'
        
        return result
    
    def get_value_trap_warning(self, result: Dict) -> List[str]:
        """获取价值陷阱警告"""
        warnings = []
        
        if result['f_score'] <= 4:
            warnings.append("⚠️ Piotroski F-Score较低，财务状况可能不佳")
        
        if result['profitability_score'] < 2:
            warnings.append("⚠️ 盈利能力不足")
        
        if result['leverage_score'] < 2:
            warnings.append("⚠️ 财务杠杆可能有问题")
        
        if result['efficiency_score'] < 1:
            warnings.append("⚠️ 运营效率下降")
        
        return warnings


def calculate_piotroski_f_score(stock_code: str, financial_data: Dict) -> Dict:
    """计算 Piotroski F-Score 主函数"""
    analyzer = PiotroskiAnalyzer()
    result = analyzer.analyze(stock_code, financial_data)
    result['warnings'] = analyzer.get_value_trap_warning(result)
    return result


if __name__ == "__main__":
    # 测试数据
    test_data = {
        'roe': 15.5,
        'roa': 8.2,
        'operating_margin': 12.3,
        'cfo_ratio': 15.0,
        'debt_to_equity_current': 0.5,
        'debt_to_equity_prev': 0.8,
        'current_ratio_current': 1.5,
        'current_ratio_prev': 1.2,
        'shares_change': 0,
        'gross_margin_current': 35.0,
        'gross_margin_prev': 30.0,
        'asset_turnover_current': 1.2,
        'asset_turnover_prev': 1.1,
    }
    
    result = calculate_piotroski_f_score('000001', test_data)
    print(f"Piotroski F-Score: {result['f_score']}/9")
    print(f"评级: {result['rating']}")
    print(f"详细: {result['details']}")
