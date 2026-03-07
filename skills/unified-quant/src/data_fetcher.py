#!/usr/bin/env python3
"""
高效数据获取模块 - 使用 Baostock
替代 Akshare，提升数据获取速度
"""
import baostock as bs
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


class StockDataFetcher:
    """高效股票数据获取器"""
    
    def __init__(self):
        self._logged_in = False
    
    def login(self):
        if not self._logged_in:
            lg = bs.login()
            if lg.error_code != '0':
                raise Exception(f"登录失败: {lg.error_msg}")
            self._logged_in = True
    
    def logout(self):
        if self._logged_in:
            bs.logout()
            self._logged_in = False
    
    def __enter__(self):
        self.login()
        return self
    
    def __exit__(self, *args):
        self.logout()
    
    def get_stock_data(self, code: str, days: int = 300) -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据
        
        Args:
            code: 股票代码 (如 'sz.300276')
            days: 获取天数
        
        Returns:
            DataFrame 或 None
        """
        # 计算日期范围
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        rs = bs.query_history_k_data_plus(
            code,
            'date,code,open,high,low,close,volume,amount,turn',
            start_date='2024-01-01',
            end_date=end_date,
            frequency='d',
            adjustflag='3'
        )
        
        if rs.error_code != '0':
            return None
        
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        
        if not data:
            return None
        
        df = pd.DataFrame(data, columns=['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turn'])
        
        # 转换为数值类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.tail(days)
    
    def get_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """
        计算技术指标
        
        Returns:
            dict: RSI, 布林带, MACD, MA 等
        """
        close = df['close']
        
        # RSI(6) 和 RSI(14)
        def calc_rsi(p, n):
            d = p.diff()
            g = d.where(d > 0, 0).rolling(n).mean()
            l = (-d.where(d < 0, 0)).rolling(n).mean()
            return 100 - (100 / (1 + g / l))
        
        rsi6 = calc_rsi(close, 6)
        rsi14 = calc_rsi(close, 14)
        
        # 布林带
        ma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        
        # MA
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()
        
        # 成交量均线
        vol_ma5 = df['volume'].rolling(5).mean()
        
        price = close.iloc[-1]
        
        return {
            'close': round(price, 2),
            'rsi6': round(rsi6.iloc[-1], 1) if not pd.isna(rsi6.iloc[-1]) else 50,
            'rsi14': round(rsi14.iloc[-1], 1) if not pd.isna(rsi14.iloc[-1]) else 50,
            'upper_band': round(upper.iloc[-1], 2) if not pd.isna(upper.iloc[-1]) else price,
            'lower_band': round(lower.iloc[-1], 2) if not pd.isna(lower.iloc[-1]) else price,
            'ma5': round(ma5.iloc[-1], 2) if not pd.isna(ma5.iloc[-1]) else price,
            'ma10': round(ma10.iloc[-1], 2) if not pd.isna(ma10.iloc[-1]) else price,
            'ma20': round(ma20.iloc[-1], 2) if not pd.isna(ma20.iloc[-1]) else price,
            'macd': round(macd.iloc[-1], 2) if not pd.isna(macd.iloc[-1]) else 0,
            'signal_line': round(signal.iloc[-1], 2) if not pd.isna(signal.iloc[-1]) else 0,
            'volume': int(df['volume'].iloc[-1]),
            'volume_ma5': round(vol_ma5.iloc[-1], 0) if not pd.isna(vol_ma5.iloc[-1]) else 0,
            'near_lower_band': price <= lower.iloc[-1] * 1.05 if not pd.isna(lower.iloc[-1]) else False,
            'near_upper_band': price >= upper.iloc[-1] * 0.95 if not pd.isna(upper.iloc[-1]) else False,
        }
    
    def analyze_stock(self, code: str) -> Optional[Dict]:
        """
        分析单只股票
        
        Returns:
            dict: 包含基本数据和技术指标
        """
        df = self.get_stock_data(code)
        if df is None or len(df) < 20:
            return None
        
        indicators = self.get_technical_indicators(df)
        
        return {
            'code': code,
            'date': df['date'].iloc[-1],
            **indicators
        }
    
    def batch_analyze(self, codes: List[str]) -> List[Dict]:
        """
        批量分析多只股票
        
        Args:
            codes: 股票代码列表
        
        Returns:
            list: 分析结果列表
        """
        results = []
        for code in codes:
            try:
                result = self.analyze_stock(code)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"分析 {code} 失败: {e}")
                continue
        
        return results
    
    def generate_signals(self, stocks: List[Dict]) -> List[Dict]:
        """
        基于技术指标生成交易信号
        
        保守策略:
        - RSI(14) < 20: 超卖
        - 价格触及布林带下轨: 买入信号
        - RSI(14) < 30: 关注
        """
        signals = []
        
        for stock in stocks:
            rsi14 = stock.get('rsi14', 50)
            rsi6 = stock.get('rsi6', 50)
            price = stock.get('close', 0)
            lower = stock.get('lower_band', price)
            
            # 保守策略判断
            if rsi14 < 20 and price <= lower * 1.05:
                signal = '买入'
                reason = f'RSI14={rsi14}<20, 价格触及布林下轨'
            elif rsi14 < 20:
                signal = '关注'
                reason = f'RSI14={rsi14}<20 超卖'
            elif rsi6 < 20:
                signal = '关注'
                reason = f'RSI6={rsi6}<20 短期超卖'
            elif rsi14 < 30:
                signal = '关注'
                reason = f'RSI14={rsi14}<30 接近超卖'
            else:
                signal = '观望'
                reason = f'RSI14={rsi14} 正常区间'
            
            signals.append({
                **stock,
                'signal': signal,
                'reason': reason
            })
        
        return signals


# 测试
if __name__ == '__main__':
    with StockDataFetcher() as fetcher:
        codes = ['sz.300276', 'sz.300199', 'sz.300502', 'sz.300274', 'sz.300308']
        
        print("=" * 60)
        print("🚀 高效股票分析 (Baostock)")
        print("=" * 60)
        
        # 批量分析
        import time
        start = time.time()
        
        stocks = fetcher.batch_analyze(codes)
        signals = fetcher.generate_signals(stocks)
        
        print(f"\n分析 {len(signals)} 只股票，耗时 {time.time()-start:.2f}秒")
        
        # 输出结果
        print(f"\n{'代码':<12} {'收盘':<10} {'RSI14':<8} {'布林下轨':<10} {'信号':<8} {'原因'}")
        print("-" * 70)
        
        for s in sorted(signals, key=lambda x: x['rsi14']):
            print(f"{s['code']:<12} {s['close']:<10} {s['rsi14']:<8} {s['lower_band']:<10} {s['signal']:<8} {s['reason']}")
        
        # 统计
        buy = [s for s in signals if s['signal'] == '买入']
        watch = [s for s in signals if s['signal'] == '关注']
        print(f"\n📈 买入: {len(buy)} | 👀 关注: {len(watch)} | 🏷️ 观望: {len(signals)-len(buy)-len(watch)}")
