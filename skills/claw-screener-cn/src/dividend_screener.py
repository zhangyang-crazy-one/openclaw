#!/usr/bin/env python3
"""
分红评分模块 - 将分红因素纳入选股筛选
价值投资核心：分红是硬道理
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from pathlib import Path

DIVIDEND_FILE = Path("/home/liujerry/金融数据/fundamentals/chuangye_full/dividend_all.csv")


class DividendScreener:
    """
    分红评分筛选器
    用于评估股票的分红能力和意愿
    """
    
    def __init__(self):
        self.params = {
            # 股息率参数 (%)
            'min_dividend_yield': 1.0,  # 最低股息率
            'good_dividend_yield': 2.0,  # 良好股息率
            'excellent_dividend_yield': 3.0,  # 优秀股息率
            
            # 连续分红参数
            'min_consecutive_years': 3,  # 最低连续分红年数
            'good_consecutive_years': 5,  # 良好连续分红年数
            'excellent_consecutive_years': 8,  # 优秀连续分红年数
            
            # 分红稳定性参数
            'min_dividend_payout_ratio': 10,  # 最低派息率 (%)
            'max_dividend_payout_ratio': 80,  # 最高派息率 (%) - 过高可能不可持续
        }
    
    def get_dividend_data(self, stock_code: str) -> Dict:
        """
        获取股票分红数据
        
        Args:
            stock_code: 股票代码 (如 '000001' 或 '300308')
            
        Returns:
            分红数据字典
        """
        code_int = int(stock_code)
        
        result = {
            'stock_code': stock_code,
            'has_dividend_history': False,
            'consecutive_years': 0,
            'total_dividends': 0,
            'avg_dividend_per_share': 0,
            'dividend_yield': 0,  # 股息率 %
            'payout_ratio': 0,  # 派息率 %
            'last_dividend': 0,  # 最近一次每股分红
            'last_dividend_year': None,
            'dividend_history': [],
            'dividend_score': 0,
            'pass_screening': False,
        }
        
        try:
            if not DIVIDEND_FILE.exists():
                return result
            
            df = pd.read_csv(DIVIDEND_FILE)
            
            # 筛选该股票的分红记录
            stock_dividends = df[df['code'] == code_int].copy()
            
            if stock_dividends.empty:
                return result
            
            result['has_dividend_history'] = True
            
            # 按日期排序（最新在前）
            stock_dividends['date'] = pd.to_datetime(stock_dividends['实施方案公告日期'])
            stock_dividends = stock_dividends.sort_values('date', ascending=False)
            
            # 计算连续分红年数（从最新年报开始计算）
            consecutive_years = 0
            years_checked = []
            for _, row in stock_dividends.iterrows():
                report_time = str(row.get('报告时间', ''))
                # 只计算年度分红和中期分红
                if '年报' in report_time or '半年报' in report_time or '季报' in report_time:
                    years_checked.append(report_time)
                    consecutive_years += 1
                    if consecutive_years >= 10:  # 最多计算10年
                        break
            
            result['consecutive_years'] = consecutive_years
            
            # 计算总分红和平均每股分红
            # 派息比例单位是"10派X元"
            dividend_sum = 0
            last_div = 0
            count = 0
            
            for _, row in stock_dividends.iterrows():
                payout = row.get('派息比例', 0)
                if pd.notna(payout) and payout > 0:
                    dividend_sum += payout
                    count += 1
                    if last_div == 0:
                        last_div = payout
            
            if count > 0:
                result['avg_dividend_per_share'] = dividend_sum / count
                result['last_dividend'] = last_div
            
            result['total_dividends'] = len(stock_dividends)
            result['dividend_history'] = stock_dividends.head(10).to_dict('records')
            
            # 计算股息率（需要股价和每股派息）
            # 股息率 = 每股派息 / 每股股价
            # 简化计算：使用最新的派息比例作为参考
            result['dividend_yield'] = self._estimate_dividend_yield(
                last_div, stock_code
            )
            
            # 计算分红评分
            result['dividend_score'] = self._calculate_dividend_score(result)
            
            # 判断是否通过筛选
            result['pass_screening'] = self._pass_dividend_filter(result)
            
        except Exception as e:
            print(f"获取分红数据失败 {stock_code}: {e}")
        
        return result
    
    def _estimate_dividend_yield(self, dividend_per_10shares: float, stock_code: str) -> float:
        """
        估算股息率
        
        股息率 = (每股派息 / 股价) * 100%
        假设: 派息比例 / 10 = 每股派息 (元)
        需要获取股价来计算
        """
        if dividend_per_10shares <= 0:
            return 0
        
        try:
            # 尝试从本地技术指标获取最新价格
            tech_file = Path(f"/home/liujerry/金融数据/technical_indicators/{stock_code}.csv")
            if tech_file.exists():
                df = pd.read_csv(tech_file)
                if not df.empty:
                    # 获取最新收盘价
                    latest_price = df['close'].iloc[-1]
                    # 每股派息 = 派息比例 / 10
                    per_share_dividend = dividend_per_10shares / 10
                    # 股息率 = (每股派息 / 股价) * 100%
                    dividend_yield = (per_share_dividend / latest_price) * 100
                    return round(dividend_yield, 2)
        except Exception:
            pass
        
        return 0
    
    def _calculate_dividend_score(self, data: Dict) -> float:
        """
        计算分红评分 (0-10分)
        
        评分标准:
        - 股息率 (0-4分)
        - 连续分红年数 (0-3分)
        - 分红稳定性 (0-3分)
        """
        score = 0
        
        # 1. 股息率评分 (0-4分)
        yield_score = 0
        if data['dividend_yield'] >= self.params['excellent_dividend_yield']:
            yield_score = 4
        elif data['dividend_yield'] >= self.params['good_dividend_yield']:
            yield_score = 3
        elif data['dividend_yield'] >= self.params['min_dividend_yield']:
            yield_score = 2
        elif data['dividend_yield'] > 0:
            yield_score = 1
        score += yield_score
        
        # 2. 连续分红年数评分 (0-3分)
        years_score = 0
        if data['consecutive_years'] >= self.params['excellent_consecutive_years']:
            years_score = 3
        elif data['consecutive_years'] >= self.params['good_consecutive_years']:
            years_score = 2
        elif data['consecutive_years'] >= self.params['min_consecutive_years']:
            years_score = 1
        score += years_score
        
        # 3. 分红稳定性评分 (0-3分)
        stability_score = 0
        if data['total_dividends'] >= 10:
            stability_score = 3
        elif data['total_dividends'] >= 5:
            stability_score = 2
        elif data['total_dividends'] >= 2:
            stability_score = 1
        score += stability_score
        
        return score
    
    def _pass_dividend_filter(self, data: Dict) -> bool:
        """
        判断是否通过分红筛选
        
        通过条件:
        1. 有分红历史
        2. 连续分红 >= 3年
        3. 股息率 >= 1%
        """
        if not data['has_dividend_history']:
            return False
        
        if data['consecutive_years'] < self.params['min_consecutive_years']:
            return False
        
        if data['dividend_yield'] < self.params['min_dividend_yield']:
            return False
        
        return True
    
    def get_dividend_summary(self, stock_code: str) -> str:
        """
        获取分红摘要字符串
        """
        data = self.get_dividend_data(stock_code)
        
        if not data['has_dividend_history']:
            return f"{stock_code}: 无分红记录"
        
        summary = f"{stock_code}: "
        summary += f"连续{data['consecutive_years']}年分红, "
        summary += f"股息率{data['dividend_yield']:.2f}%, "
        summary += f"最近一次10派{data['last_dividend']}元, "
        summary += f"分红评分{data['dividend_score']}/10分"
        
        return summary


# 测试
if __name__ == "__main__":
    screener = DividendScreener()
    
    # 测试几只股票
    test_codes = ['000001', '300308', '300502', '000568']
    
    print("=" * 60)
    print("分红评分测试")
    print("=" * 60)
    
    for code in test_codes:
        result = screener.get_dividend_data(code)
        print(f"\n{code}:")
        print(f"  有分红历史: {result['has_dividend_history']}")
        print(f"  连续分红年数: {result['consecutive_years']}")
        print(f"  股息率: {result['dividend_yield']:.2f}%")
        print(f"  最近一次派息: 10派{result['last_dividend']}元")
        print(f"  分红评分: {result['dividend_score']}/10分")
        print(f"  通过筛选: {result['pass_screening']}")
