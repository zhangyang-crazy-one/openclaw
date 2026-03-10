"""
高级分析模块 - Carlson 质量评分 + DCF 估值
与巴菲特10大公式 (formulas.py) 配合使用
"""
from typing import Dict, List, Optional
import math

# 从 formulas.py 导入
from formulas import FormulaEngine, FinancialData, FormulaStatus


class CarlsonQualityScore:
    """
    Carlson 质量评分 - 复利机器核心
    
    对应原版 TypeScript: computeCarlsonScore()
    
    评分维度:
    - 营收增长 (Revenue Growth): 20分
    - 净利润增长 (Net Income Growth): 20分
    - EPS增长 (EPS Growth): 10分
    - ROIC: 20分
    - 自由现金流: 10分
    - 回购 (Buyback): 10分
    - 营业利润率: 10分
    """
    
    def __init__(self, financial_data: Dict, price_data: Dict = None):
        """
        初始化 Carlson 评分
        
        Args:
            financial_data: 财务数据字典
            price_data: 价格数据字典
        """
        self.data = financial_data
        self.price = price_data or {}
    
    def _get(self, key: str, default: float = 0) -> float:
        """安全获取数值"""
        value = self.data.get(key, default)
        if value is None:
            return default
        if isinstance(value, dict):
            return float(value.get('value', default))
        return float(value) if isinstance(value, (int, float)) else default
    
    def _growth_score(self, values: List[float], weight: float) -> float:
        """
        计算增长评分 - 对应 TypeScript: normalizedGrowthScore()
        
        Args:
            values: 历史数据列表
            weight: 权重
        
        Returns:
            评分
        """
        if len(values) < 2:
            return 0
        
        intervals = len(values) - 1
        positive_count = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        
        return (positive_count / intervals) * weight
    
    def compute_revenue_growth_score(self) -> float:
        """营收增长评分 (权重20)"""
        revenues = self.data.get('revenue_history', [])
        if isinstance(revenues, list) and len(revenues) >= 2:
            return self._growth_score(revenues, 20)
        
        # 尝试从单年数据估算
        revenue = self._get('revenue', 0)
        if revenue > 0:
            return 10  # 给定基础分
        return 0
    
    def compute_net_income_growth_score(self) -> float:
        """净利润增长评分 (权重20)"""
        incomes = self.data.get('net_income_history', [])
        if isinstance(incomes, list) and len(incomes) >= 2:
            return self._growth_score(incomes, 20)
        
        net_income = self._get('net_income', 0)
        if net_income > 0:
            return 10
        return 0
    
    def compute_eps_growth_score(self) -> float:
        """EPS增长评分 (权重10)"""
        eps_list = self.data.get('eps_history', [])
        if isinstance(eps_list, list) and len(eps_list) >= 2:
            return self._growth_score(eps_list, 10)
        
        return 5  # 默认给分
    
    def compute_roic_score(self) -> float:
        """
        ROIC评分 (权重20) - 对应 TypeScript:
        score += clamp((input.roicPercent - 5) / 20, 0, 1) * 20
        """
        roic = self._get('roic')
        
        if roic is None or roic == 0:
            return 0
        
        # (roic - 5) / 20, 限制在 0-1 之间
        score = (roic - 5) / 20
        score = max(0, min(1, score)) * 20
        
        return score
    
    def compute_fcf_score(self) -> float:
        """
        自由现金流评分 (权重10)
        - 有正现金流: +5分
        - 增长率为正: +5分
        """
        score = 0
        
        fcf = self._get('free_cash_flow')
        if fcf > 0:
            score += 5
        
        # 增长率
        fcf_growth = self.data.get('fcf_growth', 0)
        if fcf_growth:
            # (-5% ~ 20%) 映射到 0-5
            growth_score = (fcf_growth + 5) / 20
            growth_score = max(0, min(1, growth_score)) * 5
            score += growth_score
        
        return score
    
    def compute_buyback_score(self) -> float:
        """
        回购评分 (权重10) - 对应 TypeScript:
        score += clamp((-sharesChange3YPercent) / 8, 0, 1) * 10
        """
        shares_change = self._get('shares_change_3y')
        
        if shares_change is None or shares_change == 0:
            return 0
        
        # 负值表示回购 (流通股减少)
        # (-sharesChange / 8), 限制在 0-1 之间
        score = (-shares_change) / 8
        score = max(0, min(1, score)) * 10
        
        return score
    
    def compute_operating_margin_score(self) -> float:
        """
        营业利润率评分 (权重10) - 对应 TypeScript:
        score += clamp((operatingMarginPercent - 10) / 20, 0, 1) * 10
        """
        margin = self._get('operating_margin')
        
        if margin is None or margin == 0:
            return 0
        
        # (margin - 10) / 20, 限制在 0-1 之间
        score = (margin - 10) / 20
        score = max(0, min(1, score)) * 10
        
        return score
    
    def compute_total_score(self) -> int:
        """
        计算总评分 - 对应 TypeScript: computeCarlsonScore()
        
        Returns:
            总分 (0-100)
        """
        score = 0
        score += self.compute_revenue_growth_score()
        score += self.compute_net_income_growth_score()
        score += self.compute_eps_growth_score()
        score += self.compute_roic_score()
        score += self.compute_fcf_score()
        score += self.compute_buyback_score()
        score += self.compute_operating_margin_score()
        
        # 限制范围
        return min(100, int(round(score)))
    
    def get_rating(self) -> str:
        """获取评级"""
        score = self.compute_total_score()
        if score >= 80:
            return "A+ (优秀)"
        elif score >= 60:
            return "A (良好)"
        elif score >= 40:
            return "B (一般)"
        elif score >= 20:
            return "C (较差)"
        else:
            return "D (差)"


class DCFValuation:
    """
    DCF 现金流折现估值 - 对应原版 TypeScript: computeDcf()
    
    假设:
    - 折现率: 10%
    - 终值增长率: 2.5%
    - 预测期: 10年
    """
    
    def __init__(self, financial_data: Dict, price_data: Dict = None):
        self.data = financial_data
        self.price = price_data or {}
    
    def _get(self, key: str, default: float = 0) -> float:
        value = self.data.get(key, default)
        if value is None:
            return default
        if isinstance(value, dict):
            return float(value.get('value', default))
        return float(value) if isinstance(value, (int, float)) else default
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))
    
    def compute_intrinsic_value(self) -> Dict:
        """
        计算内在价值 - 对应 TypeScript: computeDcf()
        
        Returns:
            估值结果字典
        """
        # 获取自由现金流 (单位: 万元 -> 亿元)
        fcf = self._get('free_cash_flow', 0) / 10000
        
        # 获取流通股数 (单位: 股 -> 亿股)
        shares = self._get('shares_outstanding', 1) / 100000000
        
        # 当前股价
        current_price = self.price.get('price', 0) if self.price else 0
        
        # 如果没有FCF，使用净利润估算
        if fcf <= 0 or shares <= 0:
            net_profit = self._get('net_income', 0) / 10000
            if net_profit > 0:
                fcf = net_profit * 0.8  # 假设 FCF 是净利润的 80%
            else:
                return {'error': '数据不足，无法估值'}
        
        # 估算增长率
        fcf_history = self.data.get('fcf_history', [])
        if isinstance(fcf_history, list) and len(fcf_history) >= 2:
            first = fcf_history[0]
            last = fcf_history[-1]
            periods = len(fcf_history) - 1
            if first > 0 and periods > 0:
                growth = (last / first) ** (1 / periods) - 1
            else:
                growth = 0.04
        else:
            growth = 0.04
        
        # 限制增长范围 (-5% ~ 20%)
        growth = self._clamp(growth, -0.05, 0.20)
        
        # 参数
        discount_rate = 0.10
        terminal_growth = 0.025
        
        # 10年现金流折现
        pv = 0
        projected_fcf = fcf
        
        for year in range(1, 11):
            projected_fcf *= (1 + growth)
            pv += projected_fcf / ((1 + discount_rate) ** year)
        
        # 终值
        terminal_value = (projected_fcf * (1 + terminal_growth)) / max(0.0001, discount_rate - terminal_growth)
        discounted_terminal = terminal_value / ((1 + discount_rate) ** 10)
        
        # 内在价值
        intrinsic_equity = pv + discounted_terminal
        intrinsic_per_share = intrinsic_equity / shares if shares > 0 else 0
        
        # 上涨空间
        upside = None
        if current_price and current_price > 0:
            upside = (intrinsic_per_share / current_price - 1) * 100
        
        return {
            'fcf': round(fcf, 2),
            'growth_rate': round(growth * 100, 2),
            'discount_rate': discount_rate * 100,
            'terminal_growth': terminal_growth * 100,
            'intrinsic_value_per_share': round(intrinsic_per_share, 2),
            'current_price': current_price,
            'upside_percent': round(upside, 2) if upside else None,
            'rating': self._rate_upside(upside) if upside else 'N/A'
        }
    
    def _rate_upside(self, upside: float) -> str:
        if upside is None:
            return "N/A"
        if upside >= 50:
            return "🚀 严重低估"
        elif upside >= 20:
            return "⭐ 低估"
        elif upside >= 0:
            return "➡️ 合理"
        elif upside >= -20:
            return "⚠️ 高估"
        else:
            return "🚨 严重高估"


def analyze_fundamental(financial_data: Dict, price_data: Dict = None) -> Dict:
    """
    综合基本面分析
    
    结合巴菲特10大公式、Carlson评分和DCF估值
    
    Args:
        financial_data: 财务数据
        price_data: 价格数据
    
    Returns:
        分析结果字典
    """
    # 巴菲特公式分析
    try:
        financial_data_formatted = {}
        for key, value in financial_data.items():
            if isinstance(value, (int, float)):
                financial_data_formatted[key] = {
                    'value': float(value),
                    'end_date': '2024-12-31',
                    'form': '10-K'
                }
            elif isinstance(value, dict):
                financial_data_formatted[key] = value
        
        fd = FinancialData(financial_data_formatted)
        buffett_engine = FormulaEngine(fd)
        buffett_results = buffett_engine.evaluate_all()
        buffett_score = buffett_engine.get_score()
    except Exception as e:
        buffett_results = []
        buffett_score = 0
    
    # Carlson 评分
    carlson = CarlsonQualityScore(financial_data, price_data)
    carlson_score = carlson.compute_total_score()
    carlson_rating = carlson.get_rating()
    
    # DCF 估值
    dcf = DCFValuation(financial_data, price_data)
    dcf_result = dcf.compute_intrinsic_value()
    
    # 综合评级
    total_score = (buffett_score * 10 + carlson_score) / 2
    
    if total_score >= 80:
        recommendation = "🚀 强烈推荐"
    elif total_score >= 60:
        recommendation = "⭐ 建议买入"
    elif total_score >= 40:
        recommendation = "➡️ 观望"
    else:
        recommendation = "⚠️ 建议回避"
    
    return {
        'buffett_score': buffett_score,
        'buffett_rating': "优秀" if buffett_score >= 8 else "良好" if buffett_score >= 6 else "一般",
        'buffett_results': buffett_results,
        'carlson_score': carlson_score,
        'carlson_rating': carlson_rating,
        'dcf': dcf_result,
        'total_score': round(total_score, 1),
        'recommendation': recommendation
    }


if __name__ == "__main__":
    # 测试
    test_data = {
        'CashAndCashEquivalentsAtCarryingValue': 50000000000,
        'ShortTermDebt': 15000000000,
        'LongTermDebt': 10000000000,
        'Liabilities': 29000000000,
        'StockholdersEquity': 62000000000,
        'NetIncomeLoss': 9700000000,
        'Revenues': 38300000000,
        'OperatingIncomeLoss': 11400000000,
        'Assets': 40000000000,
        'CurrentAssets': 13500000000,
        'CurrentLiabilities': 8000000000,
        'InterestExpense': 290000000,
        'CashFlowFromContinuingOperatingActivities': 11000000000,
        # Carlson 扩展数据
        'revenue_history': [15, 16, 17, 18, 19, 20],
        'net_income_history': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
        'eps_history': [1.0, 1.1, 1.15, 1.2, 1.25, 1.3],
        'roic': 18,
        'free_cash_flow': 1500000000,
        'fcf_growth': 5,
        'shares_change_3y': -5,
        'operating_margin': 15,
        'shares_outstanding': 1000000000,
    }
    
    price_data = {'price': 25.0}
    
    result = analyze_fundamental(test_data, price_data)
    
    print("=" * 60)
    print("基本面综合分析")
    print("=" * 60)
    print(f"\n巴菲特10大公式:")
    for r in result['buffett_results']:
        symbol = "✅" if r.status == FormulaStatus.PASS else "❌"
        print(f"  {symbol} {r.name}: {r.message}")
    
    print(f"\n巴菲特评分: {result['buffett_score']}/10 ({result['buffett_rating']})")
    print(f"Carlson评分: {result['carlson_score']} ({result['carlson_rating']})")
    print(f"DCF估值: {result['dcf']}")
    print(f"\n综合评分: {result['total_score']}")
    print(f"建议: {result['recommendation']}")
