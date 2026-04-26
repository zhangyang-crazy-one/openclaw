"""
安全边际计算模块
包含多种估值方法：DCF、EPV、格雷厄姆公式
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class SafetyMarginAnalyzer:
    """
    安全边际分析器
    
    估值方法：
    1. DCF (现金流折现)
    2. EPV (盈利功率价值)
    3. 格雷厄姆公式
    """
    
    def __init__(self):
        self.valuation_methods = {}
    
    def analyze(self, stock_code: str, price_data: Dict, financial_data: Dict) -> Dict:
        """
        计算安全边际
        
        Args:
            stock_code: 股票代码
            price_data: 股价数据 {'price': float}
            financial_data: 财务数据
            
        Returns:
            安全边际分析结果
        """
        current_price = price_data.get('price', 0)
        
        result = {
            'stock_code': stock_code,
            'current_price': current_price,
            'dcf_value': 0,
            'epv_value': 0,
            'graham_value': 0,
            'avg_value': 0,
            'safety_margin': 0,
            'recommendation': '',
            'position_size': '',
            'details': {}
        }
        
        if not current_price:
            return result
        
        # 1. DCF估值
        dcf_value = self._calculate_dcf(financial_data, stock_code)
        result['dcf_value'] = dcf_value
        result['details']['DCF'] = f"内在价值 = {dcf_value:.2f}元"
        
        # 2. EPV (盈利功率价值)
        epv_value = self._calculate_epv(financial_data)
        result['epv_value'] = epv_value
        result['details']['EPV'] = f"盈利功率价值 = {epv_value:.2f}元"
        
        # 3. 格雷厄姆公式
        graham_value = self._calculate_graham(financial_data)
        result['graham_value'] = graham_value
        result['details']['格雷厄姆'] = f"估算价值 = {graham_value:.2f}元"
        
        # 计算平均内在价值 (加权平均)
        # DCF权重最高，EPV次之，格雷厄姆作为参考
        if dcf_value > 0 and epv_value > 0 and graham_value > 0:
            result['avg_value'] = (dcf_value * 0.5 + epv_value * 0.35 + graham_value * 0.15)
        elif dcf_value > 0 and epv_value > 0:
            result['avg_value'] = (dcf_value * 0.6 + epv_value * 0.4)
        elif dcf_value > 0:
            result['avg_value'] = dcf_value
        else:
            result['avg_value'] = epv_value if epv_value > 0 else graham_value
        
        # 计算安全边际
        if result['avg_value'] > 0:
            result['safety_margin'] = (result['avg_value'] - current_price) / result['avg_value'] * 100
        
        # 建议
        result['recommendation'] = self._get_recommendation(result['safety_margin'])
        result['position_size'] = self._get_position_size(result['safety_margin'])
        
        return result
    
    def _get_buffett_real_data(self, stock_code: str) -> Dict:
        """从buffett_supplementary.csv获取真实财务数据"""
        try:
            import os
            buffett_file = '/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv'
            if not os.path.exists(buffett_file):
                return {}
            
            df = pd.read_csv(buffett_file)
            rows = df[df['code'].astype(str) == stock_code]
            
            if rows.empty:
                return {}
            
            b = rows.iloc[-1]
            
            # 获取经营现金流
            operating_cf = b['operating_cash_flow'] if pd.notna(b['operating_cash_flow']) else 0
            # 处理单位：如果值小于100，认为是亿元单位，转为元
            if 0 < operating_cf < 100:
                operating_cf *= 1e8
            
            net_income = b['net_income'] if pd.notna(b['net_income']) else 0
            
            # 计算真实FCF：经营现金流 * 0.8 (简化)
            real_fcf = operating_cf * 0.8 if operating_cf > 0 else net_income * 0.8
            
            return {
                'free_cash_flow': real_fcf,
                'net_income': net_income,
                'revenue': b['revenue'] if pd.notna(b['revenue']) else 0,
                'equity': b['equity'] if pd.notna(b['equity']) else 0,
                'total_assets': b['total_assets'] if pd.notna(b['total_assets']) else 0,
                'operating_profit': b['operating_profit'] if pd.notna(b['operating_profit']) else 0,
            }
        except:
            return {}

    def _calculate_dcf(self, data: Dict, stock_code: str = None) -> float:
        """
        DCF现金流折现估值
        
        参数:
        - WACC: 加权平均资本成本 (默认10%)
        - 永续增长率: 2.5%
        - 预测期: 5年
        """
        wacc = data.get('wacc', 0.10)  # 默认10%
        g = data.get('perpetual_growth', 0.025)  # 2.5%
        
        # 使用自由现金流或从buffett数据获取
        fcff = data.get('free_cash_flow', 0)
        if not fcff and stock_code:
            # 尝试从buffett_supplementary.csv获取真实数据
            buffett_data = self._get_buffett_real_data(stock_code)
            if buffett_data:
                fcff = buffett_data.get('free_cash_flow', 0)
        
        if not fcff:
            net_income = data.get('net_income', 0)
            # 简化估算FCF = 净利润 * 0.8
            fcff = net_income * 0.8 if net_income else 0
        
        if not fcff or fcff <= 0:
            return 0
        
        # 获取增长率
        growth_rate = data.get('growth_rate', 0.10)  # 默认10%
        
        # 预测未来5年现金流
        projections = []
        for year in range(1, 6):
            projected_fcf = fcff * (1 + growth_rate) ** year
            # 折现
            discounted_fcf = projected_fcf / (1 + wacc) ** year
            projections.append(discounted_fcf)
        
        # 终值 (第5年)
        terminal_value = (fcff * (1 + growth_rate) ** 5 * (1 + g)) / (wacc - g)
        discounted_terminal = terminal_value / (1 + wacc) ** 5
        
        # 企业价值
        enterprise_value = sum(projections) + discounted_terminal
        
        # 每股价值 (假设流通股)
        shares = data.get('shares_outstanding', 1)
        if shares and shares > 0:
            per_share_value = enterprise_value / shares
            return per_share_value
        
        return enterprise_value
    
    def _calculate_epv(self, data: Dict) -> float:
        """
        EPV (盈利功率价值)
        
        公式: EPV = 调整后盈利 / WACC
        假设企业未来零增长，只看现有资产产生盈利的能力
        """
        wacc = data.get('wacc', 0.10)
        
        # 调整后盈利 (使用5年平均净利润)
        avg_net_income = data.get('avg_net_income_5y', 0)
        
        if not avg_net_income or avg_net_income <= 0:
            # 尝试使用当前净利润
            avg_net_income = data.get('net_income', 0)
        
        if not avg_net_income or avg_net_income <= 0:
            return 0
        
        # EPV = 调整后盈利 / WACC
        epv = avg_net_income / wacc
        
        # 每股价值
        shares = data.get('shares_outstanding', 1)
        if shares and shares > 0:
            return epv / shares
        
        return epv
    
    def _calculate_graham(self, data: Dict) -> float:
        """
        格雷厄姆公式
        
        公式: V = [EPS × (8.5 + 2g) × 4.4] / Y
        
        其中:
        - EPS: 每股收益
        - g: 预期增长率 (7-10年)
        - Y: 当前AAA级企业债券收益率
        """
        eps = data.get('eps', 0)
        if not eps or eps <= 0:
            return 0
        
        # 预期增长率
        growth_rate = data.get('growth_rate', 0.07) * 100  # 转换为百分比
        g = growth_rate
        
        # AAA级债券收益率 (当前约4.4%)
        y = data.get('aaa_bond_yield', 4.4)
        
        # 格雷厄姆公式
        value = eps * (8.5 + 2 * g) * 4.4 / y
        
        return value
    
    def _get_recommendation(self, safety_margin: float) -> str:
        """根据安全边际获取建议"""
        if safety_margin > 50:
            return "强烈推荐买入 ✅"
        elif safety_margin > 30:
            return "推荐买入 👍"
        elif safety_margin > 10:
            return "可以考虑买入 👌"
        elif safety_margin > -10:
            return "估值合理 🤔"
        elif safety_margin > -30:
            return "估值偏高 😕"
        else:
            return "估值过高 建议观望 📉"
    
    def _get_position_size(self, safety_margin: float) -> str:
        """根据安全边际获取仓位建议"""
        if safety_margin > 50:
            return "3-5% (重仓)"
        elif safety_margin > 30:
            return "2-3% (中仓)"
        elif safety_margin > 20:
            return "1-2% (轻仓)"
        elif safety_margin > 10:
            return "0.5-1% (试探)"
        else:
            return "0% (观望)"


def calculate_safety_margin(stock_code: str, price_data: Dict, financial_data: Dict) -> Dict:
    """计算安全边际主函数"""
    analyzer = SafetyMarginAnalyzer()
    return analyzer.analyze(stock_code, price_data, financial_data)


if __name__ == "__main__":
    # 测试数据
    price_data = {'price': 29.09}
    
    financial_data = {
        'net_income': 6.27e8,  # 6.27亿
        'free_cash_flow': 5e8,  # 5亿
        'shares_outstanding': 4.34e8,  # 4.34亿股
        'eps': 1.42,
        'wacc': 0.10,
        'perpetual_growth': 0.025,
        'growth_rate': 0.10,
        'avg_net_income_5y': 4.5e8,
    }
    
    result = calculate_safety_margin('300926', price_data, financial_data)
    print(f"股票代码: {result['stock_code']}")
    print(f"当前价格: {result['current_price']:.2f}元")
    print(f"DCF估值: {result['dcf_value']:.2f}元")
    print(f"EPV估值: {result['epv_value']:.2f}元")
    print(f"格雷厄姆: {result['graham_value']:.2f}元")
    print(f"综合价值: {result['avg_value']:.2f}元")
    print(f"安全边际: {result['safety_margin']:.1f}%")
    print(f"建议: {result['recommendation']}")
    print(f"仓位: {result['position_size']}")
