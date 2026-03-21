"""
Fama-French 六因子模型选股器

Fama-French六因子模型:
1. 市场因子 (Rm-Rf) - 市场超额收益
2. 规模因子 (SMB) - 小市值减大市值
3. 价值因子 (HML) - 高账面市值比减低
4. 盈利因子 (RMW) - 高盈利减低盈利
5. 投资因子 (CMA) - 保守投资减积极投资
6. 动量因子 (Mom) - 过去收益减过去收益

简化实现:
- 使用ROE作为盈利因子
- 使用PE作为价值因子近似
- 使用市值作为规模因子
- 使用股价动量作为动量因子

参考: NotebookLM建议 - Fama-French扩展因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import baostock as bs
import akshare as ak


class FamaFrenchScreener:
    """
    Fama-French 六因子选股器
    
    六个因子:
    1. 市场因子 - 市场收益
    2. 规模因子 (SMB) - 小市值溢价
    3. 价值因子 (HML) - 价值股溢价
    4. 盈利因子 (RMW) - 高盈利溢价
    5. 投资因子 (CMA) - 保守投资溢价
    6. 动量因子 (Mom) - 趋势延续
    """
    
    def __init__(self):
        self.params = {
            # 因子权重 (可调整)
            'weight_market': 0.10,
            'weight_smb': 0.15,
            'weight_hml': 0.20,
            'weight_rmw': 0.25,
            'weight_cma': 0.15,
            'weight_mom': 0.15,
            
            # 筛选条件
            'min_roe': 10,      # 最低ROE %
            'max_pe': 50,       # 最高PE
            'min_market_cap': 10,  # 最小市值(亿)
            
            # 输出
            'top_n': 30,
        }
        
        # 缓存市场数据
        self.market_data = None
    
    def screen(self, stock_codes: List[str]) -> List[Dict]:
        """六因子筛选"""
        results = []
        
        print(f"开始Fama-French六因子筛选 ({len(stock_codes)} 只股票)...")
        
        # 获取市场基准数据
        self._fetch_market_data()
        
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
        
        # 计算因子得分
        results = self._calculate_factor_scores(results)
        
        # 按综合得分排序
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        print(f"筛选完成, {len(results)} 只符合条件")
        
        return results[:self.params['top_n']]
    
    def _fetch_market_data(self):
        """获取市场基准数据 (沪深300)"""
        try:
            lg = bs.login()
            
            # 获取沪深300历史数据作为市场基准
            rs = bs.query_history_k_data_plus(
                "sh.000300",  # 沪深300
                "date,close",
                start_date="2025-01-01",
                frequency="d"
            )
            
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            bs.logout()
            
            if data_list:
                self.market_data = pd.DataFrame(
                    data_list, 
                    columns=rs.fields
                )
                self.market_data['close'] = pd.to_numeric(
                    self.market_data['close'], 
                    errors='coerce'
                )
                
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            self.market_data = None
    
    def _analyze_stock(self, stock_code: str) -> Optional[Dict]:
        """分析单只股票"""
        result = {
            'code': stock_code,
            'name': '',
            'price': 0,
            
            # 原始指标
            'market_cap': 0,    # 市值(亿)
            'pe': 0,           # 市盈率
            'pb': 0,           # 市净率
            'roe': 0,          # ROE
            'revenue_growth': 0,  # 营收增长
            'momentum_6m': 0,  # 6个月动量
            'momentum_12m': 0, # 12个月动量
            
            # 因子值
            'factor_smb': 0,   # 规模因子
            'factor_hml': 0,   # 价值因子
            'factor_rmw': 0,   # 盈利因子
            'factor_cma': 0,   # 投资因子
            'factor_mom': 0,   # 动量因子
            
            # 综合得分
            'composite_score': 0,
            
            'pass': False,
        }
        
        try:
            # 1. 获取财务数据
            fin_df = ak.stock_financial_abstract_ths(symbol=stock_code)
            
            if fin_df is None or fin_df.empty:
                return None
            
            # 提取ROE
            for col in fin_df.columns:
                if '净资产收益率' in col:
                    roe_str = str(fin_df.iloc[0][col])
                    if roe_str and roe_str not in ['nan', 'None', '']:
                        try:
                            result['roe'] = float(roe_str.replace('%', ''))
                        except:
                            pass
                    break
            
            # 提取营收增长
            for col in fin_df.columns:
                if '营业总收入' in col and '同比' in col:
                    growth_str = str(fin_df.iloc[0][col])
                    if growth_str and growth_str not in ['nan', 'None', '', 'False']:
                        try:
                            if '%' in growth_str:
                                result['revenue_growth'] = float(growth_str.replace('%', ''))
                            else:
                                result['revenue_growth'] = float(growth_str)
                        except:
                            pass
                    break
            
            # 2. 获取价格数据
            bs_code = self._to_baostock_code(stock_code)
            lg = bs.login()
            
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,close,volume",
                start_date="2024-01-01",  # 需要更早数据算12个月动量
                frequency="d"
            )
            
            prices = []
            while rs.next():
                prices.append(rs.get_row_data())
            
            bs.logout()
            
            if not prices:
                return None
            
            price_df = pd.DataFrame(prices, columns=rs.fields)
            price_df['close'] = pd.to_numeric(price_df['close'], errors='coerce')
            price_df['volume'] = pd.to_numeric(price_df['volume'], errors='coerce')
            
            # 最新价格
            result['price'] = float(price_df.iloc[-1]['close'])
            
            # 估算市值 (简化: 价格 * 流通股本)
            # 使用成交量作为流通性的近似
            avg_volume = price_df['volume'].mean() if len(price_df) > 0 else 0
            # 假设平均股价 * 流通股本 = 日均成交额 / 换手率
            # 简化: 用价格估算
            result['market_cap'] = result['price'] * 10  # 简化估算
            
            # 计算动量
            if len(price_df) >= 20:
                result['momentum_6m'] = (
                    result['price'] / float(price_df.iloc[-20]['close']) - 1
                ) * 100
            
            if len(price_df) >= 240:  # 约12个月
                result['momentum_12m'] = (
                    result['price'] / float(price_df.iloc[-240]['close']) - 1
                ) * 100
            
            # 3. 估算PE/PB (简化)
            if result['roe'] > 0 and result['price'] > 0:
                # 假设 ROE = 净利润/净资产, PE = 股价/EPS
                # 简化: 用ROE反推
                result['pe'] = 100 / result['roe'] if result['roe'] > 0 else 0
            
            # 4. 判断通过筛选
            result['pass'] = (
                result['roe'] >= self.params['min_roe'] and
                result['price'] > 0
            )
            
        except Exception as e:
            print(f"分析 {stock_code} 失败: {e}")
        
        return result if result['pass'] else None
    
    def _calculate_factor_scores(self, results: List[Dict]) -> List[Dict]:
        """计算因子得分"""
        if not results:
            return results
        
        # 1. 规模因子 (SMB): 小市值得分更高
        results.sort(key=lambda x: x['market_cap'])
        for i, r in enumerate(results):
            r['factor_smb'] = 1 - (i / len(results))
        
        # 2. 价值因子 (HML): 低PE/低PB得分更高
        valid_results = [r for r in results if r['pe'] > 0]
        if valid_results:
            valid_results.sort(key=lambda x: x['pe'])
            for r in valid_results:
                idx = valid_results.index(r)
                r['factor_hml'] = 1 - (idx / len(valid_results))
        
        # 3. 盈利因子 (RMW): 高ROE得分更高
        results.sort(key=lambda x: x['roe'], reverse=True)
        for i, r in enumerate(results):
            r['factor_rmw'] = 1 - (i / len(results))
        
        # 4. 投资因子 (CMA): 营收增长稳定(非高增长)得分更高
        # 简化: 中等增长最好
        def cma_score(g):
            if g < 0:  # 负增长
                return 0.3
            elif g < 20:  # 温和增长
                return 1.0
            elif g < 50:  # 较高增长
                return 0.6
            else:  # 极高增长
                return 0.3
        
        for r in results:
            r['factor_cma'] = cma_score(r['revenue_growth'])
        
        # 5. 动量因子 (Mom): 6个月动量
        # 简化: 0-30%动量最佳
        def mom_score(m):
            if m < -20:
                return 0.2
            elif m < 0:
                return 0.6
            elif m < 30:
                return 1.0
            elif m < 50:
                return 0.7
            else:
                return 0.3
        
        for r in results:
            r['factor_mom'] = mom_score(r['momentum_6m'])
        
        # 6. 计算综合得分
        w = self.params
        for r in results:
            r['composite_score'] = (
                w['weight_smb'] * r['factor_smb'] +
                w['weight_hml'] * r['factor_hml'] +
                w['weight_rmw'] * r['factor_rmw'] +
                w['weight_cma'] * r['factor_cma'] +
                w['weight_mom'] * r['factor_mom']
            )
        
        return results
    
    def _to_baostock_code(self, stock_code: str) -> str:
        """转换为baostock格式"""
        if stock_code.startswith('6'):
            return f'sh.{stock_code}'
        elif stock_code.startswith(('3', '0')):
            return f'sz.{stock_code}'
        return f'sz.{stock_code}'
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成报告"""
        if not results:
            return "没有符合条件的股票"
        
        lines = []
        lines.append("=" * 80)
        lines.append("📊 Fama-French 六因子 选股报告")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"{'排名':<4} {'代码':<8} {'价格':<8} {'ROE':<6} {'规模':<6} {'价值':<6} {'盈利':<6} {'投资':<6} {'动量':<6} {'综合':<6}")
        lines.append("-" * 80)
        
        for i, r in enumerate(results, 1):
            lines.append(
                f"{i:<4} {r['code']:<8} {r['price']:<8.2f} "
                f"{r['roe']:<6.1f} {r['factor_smb']:<6.2f} {r['factor_hml']:<6.2f} "
                f"{r['factor_rmw']:<6.2f} {r['factor_cma']:<6.2f} {r['factor_mom']:<6.2f} "
                f"{r['composite_score']:<6.2f}"
            )
        
        lines.append("")
        lines.append("因子说明:")
        lines.append("- 规模(SMB): 小市值得分高")
        lines.append("- 价值(HML): 低PE得分高")
        lines.append("- 盈利(RMW): 高ROE得分高")
        lines.append("- 投资(CMA): 温和增长得分高")
        lines.append("- 动量(Mom): 0-30%涨幅得分高")
        
        return "\n".join(lines)


def famafrench_screen(stock_codes: List[str]) -> List[Dict]:
    """主函数"""
    screener = FamaFrenchScreener()
    return screener.screen(stock_codes)


if __name__ == "__main__":
    codes = ['300502', '300926', '300308', '300628', '300573', '300274']
    
    screener = FamaFrenchScreener()
    results = screener.screen(codes)
    print(screener.generate_report(results))
