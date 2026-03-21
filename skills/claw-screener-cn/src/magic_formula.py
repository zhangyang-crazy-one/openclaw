"""
神奇公式 + 动量模型 (优化版)
基于Joel Greenblatt的神奇公式，结合动量因子

简化实现:
1. 使用ROE替代ROIC (数据更易获取)
2. 使用PE的倒数作为EY近似
3. 使用baostock获取价格数据
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import baostock as bs


class MagicFormulaScreener:
    """
    神奇公式 + 动量选股器
    
    简化版:
    - 使用ROE作为资本回报率近似
    - 使用1/PE作为盈利收益率近似
    """
    
    def __init__(self):
        self.params = {
            # 神奇公式参数 (简化)
            'min_roe': 15,      # 最低ROE (%)
            'min_pe': 0,        # 最低PE (0表示不限制)
            'max_pe': 50,       # 最高PE
            
            # 动量参数
            'momentum_period': 6,   # 6个月
            'max_momentum': 100,    # 最大涨幅
            
            # 排名参数
            'top_n': 30,
        }
    
    def screen(self, stock_codes: List[str]) -> List[Dict]:
        """神奇公式筛选"""
        results = []
        
        print(f"开始筛选 {len(stock_codes)} 只股票...")
        
        for code in stock_codes:
            try:
                result = self._analyze_stock(code)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"分析 {code} 出错: {e}")
        
        if not results:
            print("没有符合条件的股票")
            return []
        
        # 计算排名
        results = self._calculate_ranks(results)
        
        # 按综合得分排序
        results.sort(key=lambda x: x['combined_score'], reverse=False)
        
        print(f"筛选完成, {len(results)} 只符合条件")
        
        return results[:self.params['top_n']]
    
    def _analyze_stock(self, stock_code: str) -> Optional[Dict]:
        """分析单只股票"""
        result = {
            'code': stock_code,
            'name': '',
            'price': 0,
            'roe': 0,           # ROE (替代ROIC)
            'pe': 0,            # 市盈率
            'earnings_yield': 0, # 盈利收益率 (1/PE)
            'momentum_6m': 0,
            'pass': False,
        }
        
        try:
            # 1. 获取财务数据
            import akshare as ak
            fin_df = ak.stock_financial_abstract_ths(symbol=stock_code)
            
            if fin_df is None or fin_df.empty:
                return None
            
            # 提取ROE
            for col in fin_df.columns:
                if '净资产收益率' in col:
                    roe_str = str(fin_df.iloc[0][col])
                    if roe_str and roe_str != 'nan' and roe_str != 'None':
                        try:
                            result['roe'] = float(roe_str.replace('%', ''))
                        except:
                            pass
                    break
            
            # 2. 获取价格数据 (用baostock)
            bs_code = self._to_baostock_code(stock_code)
            lg = bs.login()
            
            # 获取最新收盘价
            rs = bs.query_history_k_data_plus(
                bs_code,
                'date,close',
                start_date='2025-01-01',
                frequency='d'
            )
            
            prices = []
            while rs.next():
                prices.append(rs.get_row_data())
            
            bs.logout()
            
            if prices:
                result['price'] = float(prices[-1][1])
                
                # 获取6个月前价格
                if len(prices) >= 20:
                    result['momentum_6m'] = (result['price'] / float(prices[-20][1]) - 1) * 100
            
            # 3. 计算EY (简化: 用ROE/PE的关系)
            # 如果有价格和EPS,可以计算PE
            # 这里简化: ROE > 15% 即为优质
            
            # 4. 判断通过
            result['pass'] = (
                result['roe'] >= self.params['min_roe'] and
                result['price'] > 0
            )
            
            if result['pass']:
                result['earnings_yield'] = result['roe'] / 100  # 简化EY = ROE/100
            
        except Exception as e:
            print(f"分析 {stock_code} 失败: {e}")
        
        return result if result['pass'] else None
    
    def _to_baostock_code(self, stock_code: str) -> str:
        """转换为baostock格式"""
        if stock_code.startswith('6'):
            return f'sh.{stock_code}'
        elif stock_code.startswith(('3', '0')):
            return f'sz.{stock_code}'
        return f'sz.{stock_code}'
    
    def _calculate_ranks(self, results: List[Dict]) -> List[Dict]:
        """计算综合排名"""
        if not results:
            return results
        
        # ROE排名 (越高越好)
        results.sort(key=lambda x: x['roe'], reverse=True)
        for i, r in enumerate(results):
            r['rank_roe'] = i + 1
        
        # 动量排名 (0-30%最好)
        def momentum_rank(m):
            if m < 0: return 3
            elif m <= 30: return 1
            elif m <= 60: return 2
            else: return 4
        
        results.sort(key=lambda x: momentum_rank(x['momentum_6m']), reverse=False)
        for i, r in enumerate(results):
            r['rank_momentum'] = i + 1
        
        # 综合得分
        for r in results:
            r['combined_score'] = r['rank_roe'] + r['rank_momentum']
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成报告"""
        if not results:
            return "没有符合条件的股票"
        
        lines = []
        lines.append("=" * 70)
        lines.append("📊 神奇公式 + 动量 选股报告")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"{'排名':<4} {'代码':<10} {'价格':<8} {'ROE':<8} {'6M动量':<10} {'综合分':<6}")
        lines.append("-" * 70)
        
        for i, r in enumerate(results, 1):
            lines.append(
                f"{i:<4} {r['code']:<10} {r['price']:<8.2f} "
                f"{r['roe']:<8.1f}% {r['momentum_6m']:<10.1f}% {r['combined_score']:<6}"
            )
        
        lines.append("")
        lines.append("说明: ROE≥15% 为筛选标准, 综合分=ROE排名+动量排名")
        
        return "\n".join(lines)


def magic_formula_screen(stock_codes: List[str]) -> List[Dict]:
    """主函数"""
    screener = MagicFormulaScreener()
    return screener.screen(stock_codes)


if __name__ == "__main__":
    codes = ['300502', '300926', '300308', '300628', '300573', '300274']
    
    screener = MagicFormulaScreener()
    results = screener.screen(codes)
    print(screener.generate_report(results))
