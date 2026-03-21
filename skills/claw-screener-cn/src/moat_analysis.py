"""
护城河分析模块
基于晨星(Morningstar)框架，识别五大护城河来源
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MoatAnalyzer:
    """护城河分析器"""
    
    # 护城河五大来源
    MOAT_SOURCES = {
        'intangible_assets': '无形资产 (品牌、专利、监管特许权)',
        'switching_costs': '转换成本',
        'network_effect': '网络效应',
        'cost_advantage': '成本优势',
        'efficient_scale': '有效规模'
    }
    
    def __init__(self):
        self.moat_indicators = {}
    
    def analyze(self, stock_code: str, fundamentals: Dict) -> Dict:
        """
        分析护城河
        
        Args:
            stock_code: 股票代码
            fundamentals: 基本面数据字典
            
        Returns:
            护城河分析结果
        """
        result = {
            'stock_code': stock_code,
            'moat_sources': [],
            'moat_rating': '无护城河',  # 宽护城河/窄护城河/无护城河
            'moat_score': 0,
            'details': {}
        }
        
        # 1. 检查无形资产 (品牌、专利)
        if self._check_intangible_assets(fundamentals):
            result['moat_sources'].append('intangible_assets')
            result['details']['无形资产'] = '存在品牌优势或专利'
        
        # 2. 检查转换成本
        if self._check_switching_costs(fundamentals):
            result['moat_sources'].append('switching_costs')
            result['details']['转换成本'] = '客户粘性高'
        
        # 3. 检查网络效应
        if self._check_network_effect(fundamentals):
            result['moat_sources'].append('network_effect')
            result['details']['网络效应'] = '具有平台特性'
        
        # 4. 检查成本优势
        if self._check_cost_advantage(fundamentals):
            result['moat_sources'].append('cost_advantage')
            result['details']['成本优势'] = '规模效应或独特资源'
        
        # 5. 检查有效规模
        if self._check_efficient_scale(fundamentals):
            result['moat_sources'].append('efficient_scale')
            result['details']['有效规模'] = '市场地位稳固'
        
        # 计算护城河评分
        result['moat_score'] = len(result['moat_sources'])
        
        # 护城河评级
        if result['moat_score'] >= 3:
            result['moat_rating'] = '宽护城河'
        elif result['moat_score'] >= 1:
            result['moat_rating'] = '窄护城河'
        else:
            result['moat_rating'] = '无护城河'
        
        return result
    
    def _check_intangible_assets(self, fundamentals: Dict) -> bool:
        """检查无形资产"""
        # 毛利率高 (>40%) 通常表示有品牌或定价权
        gross_margin = fundamentals.get('gross_margin', 0)
        if gross_margin and gross_margin > 40:
            return True
        
        # 专利或品牌相关行业
        industry = fundamentals.get('industry', '')
        brand_industries = ['食品饮料', '医药生物', '化妆品', '奢侈品', '软件']
        for ind in brand_industries:
            if ind in industry:
                return True
        
        return False
    
    def _check_switching_costs(self, fundamentals: Dict) -> bool:
        """检查转换成本"""
        # 高客户粘性指标
        # 订阅制、SaaS、重复购买高的行业
        industry = fundamentals.get('industry', '')
        high_switch_cost_industries = [
            '软件', 'IT服务', '互联网', '医疗服务',
            '金融', '电信', '公用事业'
        ]
        
        for ind in high_switch_cost_industries:
            if ind in industry:
                return True
        
        # 客户分散度低通常表示转换成本高
        if fundamentals.get('customer_concentration', 0) < 30:
            return True
        
        return False
    
    def _check_network_effect(self, fundamentals: Dict) -> bool:
        """检查网络效应"""
        industry = fundamentals.get('industry', '')
        
        # 平台型、社交型、支付型行业
        network_industries = [
            '互联网', '电子商务', '社交', '支付',
            '云计算', '平台', '游戏'
        ]
        
        for ind in network_industries:
            if ind in industry:
                return True
        
        # 用户规模大
        if fundamentals.get('user_count', 0) > 10000000:  # 1000万用户
            return True
        
        return False
    
    def _check_cost_advantage(self, fundamentals: Dict) -> bool:
        """检查成本优势"""
        # 规模效应明显的行业
        industry = fundamentals.get('industry', '')
        scale_industries = [
            '零售', '物流', '制造', '钢铁', '煤炭',
            '电力', '房地产', '家电', '汽车'
        ]
        
        for ind in scale_industries:
            if ind in industry:
                return True
        
        # 低毛利率 + 高周转 = 成本优势
        if (fundamentals.get('gross_margin', 0) < 30 and 
            fundamentals.get('asset_turnover', 0) > 1):
            return True
        
        return False
    
    def _check_efficient_scale(self, fundamentals: Dict) -> bool:
        """检查有效规模"""
        # 市场份额高
        market_share = fundamentals.get('market_share', 0)
        if market_share and market_share > 20:
            return True
        
        # 进入壁垒高的行业
        industry = fundamentals.get('industry', '')
        barrier_industries = [
            '电力', '电信', '铁路', '航空', '银行',
            '保险', '公用事业', '烟草'
        ]
        
        for ind in barrier_industries:
            if ind in industry:
                return True
        
        return False
    
    def get_moat_summary(self, result: Dict) -> str:
        """获取护城河摘要"""
        if not result['moat_sources']:
            return "无明显护城河"
        
        names = [self.MOAT_SOURCES.get(s, s) for s in result['moat_sources']]
        return ", ".join(names)


def analyze_moat(stock_code: str, fundamentals: Dict) -> Dict:
    """护城河分析主函数"""
    analyzer = MoatAnalyzer()
    return analyzer.analyze(stock_code, fundamentals)


if __name__ == "__main__":
    # 测试
    test_data = {
        'industry': '食品饮料',
        'gross_margin': 45.0,
        'market_share': 15,
        'asset_turnover': 1.2,
        'customer_concentration': 20
    }
    
    result = analyze_moat('000001', test_data)
    print(f"护城河分析结果: {result}")
