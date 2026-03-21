"""
增强筛选因子模块
基于NotebookLM建议的筛选因子优化
包含: ROE稳定性、FCF、动量因子、低波动因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import akshare as ak


class EnhancedScreener:
    """
    增强型选股器
    
    新增筛选因子:
    1. ROE稳定性 (10年平均ROE ≥ 15%)
    2. 自由现金流 (FCF连续3-5年为正)
    3. 动量因子 (6个月涨幅)
    4. 低波动因子
    5. 盈利能力因子
    6. 投资模式因子
    """
    
    def __init__(self):
        self.params = {
            # ROE参数
            'min_avg_roe': 15.0,  # 最低10年平均ROE %
            'min_roe_single_year': 10.0,  # 单一年份最低ROE %
            
            # FCF参数
            'min_fcf_years': 3,  # FCF正增长年数
            
            # 动量参数
            'momentum_period': 6,  # 动量周期 (月)
            
            # 波动率参数
            'volatility_period': 20,  # 波动率计算周期 (交易日)
            'max_volatility': 0.5,  # 最高波动率
            
            # 估值参数
            'max_pe': 30,  # 最高PE
            'max_pb': 5,  # 最高PB
        }
    
    def screen(self, stock_codes: List[str]) -> List[Dict]:
        """
        增强筛选
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            符合条件的股票列表
        """
        results = []
        
        for code in stock_codes:
            try:
                result = self.analyze_stock(code)
                if result['pass_screening']:
                    results.append(result)
            except Exception as e:
                print(f"分析 {code} 出错: {e}")
        
        # 按综合评分排序
        results.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        return results
    
    def analyze_stock(self, stock_code: str) -> Dict:
        """分析单只股票"""
        result = {
            'stock_code': stock_code,
            'name': '',
            'price': 0,
            'roe_stability': {},  # ROE稳定性
            'fcf_status': {},     # FCF状态
            'momentum': {},        # 动量
            'volatility': {},      # 波动率
            'valuation': {},       # 估值
            'total_score': 0,
            'pass_screening': False,
        }
        
        try:
            # 1. 获取数据
            data = self._fetch_data(stock_code)
            if not data:
                return result
            
            result['name'] = data.get('name', '')
            result['price'] = data.get('price', 0)
            
            # 2. 计算各因子
            result['roe_stability'] = self._check_roe_stability(data)
            result['fcf_status'] = self._check_fcf(data)
            result['momentum'] = self._calculate_momentum(data)
            result['volatility'] = self._calculate_volatility(data)
            result['valuation'] = self._check_valuation(data)
            
            # 3. 计算综合评分
            result['total_score'] = self._calculate_score(result)
            
            # 4. 判断是否通过筛选
            result['pass_screening'] = self._pass_filter(result)
            
        except Exception as e:
            print(f"分析 {stock_code} 失败: {e}")
        
        return result
    
    def _fetch_data(self, stock_code: str) -> Optional[Dict]:
        """获取股票数据"""
        data = {}
        
        try:
            # 获取财务摘要
            df_financial = ak.stock_financial_abstract_ths(symbol=stock_code)
            if df_financial is None or df_financial.empty:
                return None
            
            data['financial'] = df_financial
            
            # 获取实时行情
            df_quote = ak.stock_zh_a_spot_em()
            row = df_quote[df_quote['代码'] == stock_code]
            if not row.empty:
                data['price'] = row['最新价'].values[0]
                data['name'] = row['名称'].values[0]
                data['pe'] = row['市盈率-动态'].values[0] if '市盈率-动态' in row.columns else 0
                data['pb'] = row['市净率'].values[0] if '市净率' in row.columns else 0
                
            # 获取历史行情 (用于动量和波动率)
            try:
                df_history = ak.stock_zh_a_hist(
                    symbol=stock_code, 
                    period="monthly",
                    start_date="20250101",
                    adjust="qfq"
                )
                data['history'] = df_history
            except:
                pass
                
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
        
        return data if data.get('financial') is not None else None
    
    def _check_roe_stability(self, data: Dict) -> Dict:
        """检查ROE稳定性"""
        result = {
            'avg_roe': 0,
            'min_roe': 0,
            'years_above_15': 0,
            'pass': False,
            'score': 0,
        }
        
        try:
            df = data.get('financial', pd.DataFrame())
            if df.empty:
                return result
            
            # 提取ROE数据
            roe_col = None
            for col in df.columns:
                if '净资产收益率' in col or 'ROE' in col:
                    roe_col = col
                    break
            
            if roe_col is None:
                return result
            
            roe_values = []
            for val in df[roe_col].head(10):  # 最近10年
                if isinstance(val, (int, float)):
                    roe_values.append(val)
                elif isinstance(val, str):
                    try:
                        roe_values.append(float(val.replace('%', '')))
                    except:
                        pass
            
            if not roe_values:
                return result
            
            # 计算指标
            result['avg_roe'] = np.mean(roe_values)
            result['min_roe'] = min(roe_values)
            result['years_above_15'] = sum(1 for r in roe_values if r >= 15)
            
            # 评分
            if result['avg_roe'] >= 20:
                result['score'] = 5
            elif result['avg_roe'] >= 15:
                result['score'] = 3
            elif result['avg_roe'] >= 10:
                result['score'] = 1
            
            # 通过条件
            if (result['avg_roe'] >= self.params['min_avg_roe'] and 
                result['min_roe'] >= self.params['min_roe_single_year'] and
                result['years_above_15'] >= 7):
                result['pass'] = True
                
        except Exception as e:
            print(f"ROE检查失败: {e}")
        
        return result
    
    def _check_fcf(self, data: Dict) -> Dict:
        """检查自由现金流"""
        result = {
            'fcf_values': [],
            'positive_years': 0,
            'pass': False,
            'score': 0,
        }
        
        try:
            df = data.get('financial', pd.DataFrame())
            if df.empty:
                return result
            
            # 尝试获取经营现金流或自由现金流
            # 这里简化处理，实际需要更详细的数据
            # 使用净利润+折旧摊销作为FCF近似
            
            net_profit_col = None
            for col in df.columns:
                if '净利润' in col:
                    net_profit_col = col
                    break
            
            if net_profit_col is None:
                return result
            
            fcf_values = []
            for val in df[net_profit_col].head(5):  # 最近5年
                if isinstance(val, (int, float)):
                    fcf_values.append(val)
                elif isinstance(val, str):
                    try:
                        if '亿' in val:
                            fcf_values.append(float(val.replace('亿', '')) * 1e8)
                        elif '万' in val:
                            fcf_values.append(float(val.replace('万', '')) * 1e4)
                    except:
                        pass
            
            if not fcf_values:
                return result
            
            result['fcf_values'] = fcf_values
            result['positive_years'] = sum(1 for v in fcf_values if v > 0)
            
            # 评分
            if result['positive_years'] >= 5:
                result['score'] = 5
            elif result['positive_years'] >= 3:
                result['score'] = 3
            
            # 通过条件
            if result['positive_years'] >= self.params['min_fcf_years']:
                result['pass'] = True
                
        except Exception as e:
            print(f"FCF检查失败: {e}")
        
        return result
    
    def _calculate_momentum(self, data: Dict) -> Dict:
        """计算动量因子"""
        result = {
            'momentum_1m': 0,
            'momentum_3m': 0,
            'momentum_6m': 0,
            'pass': False,
            'score': 0,
        }
        
        try:
            df = data.get('history')
            if df is None or df.empty:
                return result
            
            # 计算各周期涨幅
            if len(df) >= 2:
                result['momentum_1m'] = (df['收盘'].iloc[-1] / df['收盘'].iloc[-2] - 1) * 100
            if len(df) >= 4:
                result['momentum_3m'] = (df['收盘'].iloc[-1] / df['收盘'].iloc[-4] - 1) * 100
            if len(df) >= 7:
                result['momentum_6m'] = (df['收盘'].iloc[-1] / df['收盘'].iloc[-7] - 1) * 100
            
            # 评分: 动量适中最好 (避免追涨杀跌)
            # 6个月涨幅在0-30%之间为最佳
            mom = result['momentum_6m']
            if 0 <= mom <= 30:
                result['score'] = 5
            elif -10 <= mom < 0:
                result['score'] = 3
            elif 30 < mom <= 50:
                result['score'] = 2
            else:
                result['score'] = 1
            
            # 通过条件: 6个月涨幅为正但不超过50%
            if 0 <= mom <= 50:
                result['pass'] = True
                
        except Exception as e:
            print(f"动量计算失败: {e}")
        
        return result
    
    def _calculate_volatility(self, data: Dict) -> Dict:
        """计算波动率因子"""
        result = {
            'volatility': 0,
            'pass': False,
            'score': 0,
        }
        
        try:
            df = data.get('history')
            if df is None or df.empty or len(df) < 5:
                return result
            
            # 计算日收益率标准差 (年化)
            returns = df['收盘'].pct_change().dropna()
            if len(returns) > 0:
                daily_vol = returns.std()
                annual_vol = daily_vol * np.sqrt(252)  # 年化
                result['volatility'] = annual_vol
            
            # 评分: 波动率越低越好
            if result['volatility'] < 0.2:
                result['score'] = 5
            elif result['volatility'] < 0.3:
                result['score'] = 3
            elif result['volatility'] < 0.5:
                result['score'] = 1
            
            # 通过条件
            if result['volatility'] < self.params['max_volatility']:
                result['pass'] = True
                
        except Exception as e:
            print(f"波动率计算失败: {e}")
        
        return result
    
    def _check_valuation(self, data: Dict) -> Dict:
        """检查估值"""
        result = {
            'pe': 0,
            'pb': 0,
            'pass': False,
            'score': 0,
        }
        
        try:
            result['pe'] = data.get('pe', 0)
            result['pb'] = data.get('pb', 0)
            
            # 评分
            if 0 < result['pe'] < 15:
                result['score'] = 5
            elif 15 <= result['pe'] < 25:
                result['score'] = 3
            elif 25 <= result['pe'] < 30:
                result['score'] = 1
            
            # 通过条件
            if (0 < result['pe'] < self.params['max_pe'] and 
                0 < result['pb'] < self.params['max_pb']):
                result['pass'] = True
                
        except Exception as e:
            print(f"估值检查失败: {e}")
        
        return result
    
    def _calculate_score(self, result: Dict) -> float:
        """计算综合评分"""
        score = 0
        
        # 各因子评分加总
        score += result['roe_stability'].get('score', 0)
        score += result['fcf_status'].get('score', 0)
        score += result['momentum'].get('score', 0)
        score += result['volatility'].get('score', 0)
        score += result['valuation'].get('score', 0)
        
        return score
    
    def _pass_filter(self, result: Dict) -> bool:
        """判断是否通过筛选"""
        # 必须通过ROE稳定性筛选
        if not result['roe_stability'].get('pass', False):
            return False
        
        # 至少再通过一个因子
        passed = 0
        if result['fcf_status'].get('pass', False):
            passed += 1
        if result['momentum'].get('pass', False):
            passed += 1
        if result['volatility'].get('pass', False):
            passed += 1
        if result['valuation'].get('pass', False):
            passed += 1
        
        return passed >= 1
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成筛选报告"""
        if not results:
            return "没有找到符合条件的股票"
        
        report = []
        report.append("=" * 80)
        report.append("📊 增强筛选报告 (ROE稳定性 + FCF + 动量 + 低波动)")
        report.append("=" * 80)
        report.append("")
        
        for i, r in enumerate(results, 1):
            report.append(f"## {i}. {r['name']} ({r['stock_code']})")
            report.append(f"   价格: {r['price']:.2f}元")
            report.append(f"   综合评分: {r['total_score']}/25")
            
            # ROE
            roe = r['roe_stability']
            report.append(f"   📈 ROE稳定性: {roe.get('avg_roe', 0):.1f}% (通过: {roe.get('pass', False)})")
            
            # FCF
            fcf = r['fcf_status']
            report.append(f"   💰 FCF: {fcf.get('positive_years', 0)}年正 (通过: {fcf.get('pass', False)})")
            
            # 动量
            mom = r['momentum']
            report.append(f"   📊 动量(6M): {mom.get('momentum_6m', 0):.1f}% (通过: {mom.get('pass', False)})")
            
            # 波动率
            vol = r['volatility']
            report.append(f"   📉 波动率: {vol.get('volatility', 0)*100:.1f}% (通过: {vol.get('pass', False)})")
            
            # 估值
            val = r['valuation']
            report.append(f"   💵 PE: {val.get('pe', 0):.1f} | PB: {val.get('pb', 0):.1f}")
            
            report.append("")
        
        return "\n".join(report)


def enhanced_screen(stock_codes: List[str]) -> List[Dict]:
    """增强筛选主函数"""
    screener = EnhancedScreener()
    return screener.screen(stock_codes)


if __name__ == "__main__":
    # 测试
    codes = ['300502', '300926', '300308']
    screener = EnhancedScreener()
    results = screener.screen(codes)
    print(screener.generate_report(results))
