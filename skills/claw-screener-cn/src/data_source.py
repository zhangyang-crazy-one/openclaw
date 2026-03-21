"""
多通道数据获取模块
支持akshare和baostock自动切换，带重试机制
"""

import akshare as ak
import baostock as bs
import pandas as pd
import time
from typing import Optional, Dict, List


class DataSource:
    """
    多通道数据获取器
    
    自动重试 + 通道切换:
    1. 首先尝试 akshare (东财接口)
    2. 如果失败, 重试3次
    3. 如果仍然失败, 切换到 baostock
    4. 如果都失败, 返回缓存数据
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache = {}  # 简单缓存
        
    def _retry_with_backoff(self, func, *args, **kwargs):
        """带退避的重试机制"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                return result, 'success'
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 递增延迟
                    print(f"  重试 {attempt + 1}/{self.max_retries}...")
        
        return None, str(last_error)
    
    # ========== 实时行情 ==========
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情 (多通道)"""
        # 通道1: akshare
        result, status = self._retry_with_backoff(
            self._get_quote_akshare, stock_code
        )
        
        if result is not None:
            return result
        
        print(f"  akshare失败, 尝试备用通道...")
        
        # 通道2: baostock (获取收盘价作为近似)
        result, status = self._retry_with_backoff(
            self._get_quote_baostock, stock_code
        )
        
        if result is not None:
            return result
        
        # 通道3: 使用缓存
        return self.cache.get(f'quote_{stock_code}')
    
    def _get_quote_akshare(self, stock_code: str) -> Dict:
        """akshare获取实时行情"""
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == stock_code]
        
        if row.empty:
            raise ValueError(f"股票 {stock_code} 不存在")
        
        return {
            'code': stock_code,
            'name': row['名称'].values[0],
            'price': row['最新价'].values[0],
            'change_pct': row['涨跌幅'].values[0],
            'volume': row['成交量'].values[0],
            'amount': row['成交额'].values[0],
            'pe': row.get('市盈率-动态', [0]).values[0],
            'pb': row.get('市净率', [0]).values[0],
            'source': 'akshare'
        }
    
    def _get_quote_baostock(self, stock_code: str) -> Dict:
        """baostock获取最新收盘价"""
        # 转换为baostock格式
        bs_code = self._to_baostock_code(stock_code)
        
        lg = bs.login()
        if lg.error_code != '0':
            raise Exception(lg.error_msg)
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            'date,open,high,low,close,volume,amount',
            start_date='2025-01-01',
            frequency='d',
            fields='date,open,high,low,close,volume,amount'
        )
        
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if not data_list:
            raise ValueError(f"无数据: {stock_code}")
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        latest = df.iloc[-1]
        
        return {
            'code': stock_code,
            'name': stock_code,
            'price': float(latest['close']),
            'change_pct': 0,  # baostock不直接提供涨跌幅
            'volume': int(latest['volume']),
            'amount': float(latest['amount']),
            'pe': 0,
            'pb': 0,
            'source': 'baostock'
        }
    
    # ========== 历史数据 ==========
    
    def get_historical_data(self, stock_code: str, days: int = 250) -> Optional[pd.DataFrame]:
        """获取历史数据 (多通道)"""
        # 通道1: akshare
        result, status = self._retry_with_backoff(
            self._get_history_akshare, stock_code, days
        )
        
        if result is not None and not result.empty:
            return result
        
        print(f"  akshare历史数据失败, 尝试baostock...")
        
        # 通道2: baostock
        result, status = self._retry_with_backoff(
            self._get_history_baostock, stock_code, days
        )
        
        if result is not None and not result.empty:
            return result
        
        # 通道3: 缓存
        cache_key = f'history_{stock_code}_{days}'
        return self.cache.get(cache_key)
    
    def _get_history_akshare(self, stock_code: str, days: int) -> pd.DataFrame:
        """akshare获取历史数据"""
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        return df.tail(days) if len(df) > days else df
    
    def _get_history_baostock(self, stock_code: str, days: int) -> pd.DataFrame:
        """baostock获取历史数据"""
        from datetime import datetime, timedelta
        
        bs_code = self._to_baostock_code(stock_code)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y-%m-%d')
        
        lg = bs.login()
        if lg.error_code != '0':
            raise Exception(lg.error_msg)
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            'date,open,high,low,close,volume,amount',
            start_date=start_date,
            end_date=end_date,
            frequency='d',
            fields='date,open,high,low,close,volume,amount'
        )
        
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if not data_list:
            raise ValueError(f"无历史数据: {stock_code}")
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 转换数值类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.tail(days) if len(df) > days else df
    
    # ========== 财务数据 ==========
    
    def get_financial_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取财务数据 (akshare财务接口稳定)"""
        result, status = self._retry_with_backoff(
            self._get_financial_akshare, stock_code
        )
        
        if result is not None:
            return result
        
        return None
    
    def _get_financial_akshare(self, stock_code: str) -> pd.DataFrame:
        """akshare获取财务数据"""
        df = ak.stock_financial_abstract_ths(symbol=stock_code)
        
        # 缓存结果
        self.cache[f'financial_{stock_code}'] = df
        
        return df
    
    # ========== 辅助方法 ==========
    
    def _to_baostock_code(self, stock_code: str) -> str:
        """转换为baostock格式"""
        if stock_code.startswith('6'):
            return f'sh.{stock_code}'
        elif stock_code.startswith(('3', '0')):
            return f'sz.{stock_code}'
        else:
            return f'sz.{stock_code}'
    
    def cache_data(self, key: str, data: any):
        """缓存数据"""
        self.cache[key] = data
    
    def get_cached(self, key: str) -> any:
        """获取缓存"""
        return self.cache.get(key)


# 全局实例
_data_source = None

def get_data_source() -> DataSource:
    """获取数据源实例"""
    global _data_source
    if _data_source is None:
        _data_source = DataSource(max_retries=3, retry_delay=1.0)
    return _data_source


if __name__ == "__main__":
    # 测试
    ds = get_data_source()
    
    print("=" * 50)
    print("测试多通道数据获取")
    print("=" * 50)
    
    stocks = ['300502', '300926', '300308']
    
    for code in stocks:
        print(f"\n获取 {code} 数据...")
        
        # 实时行情
        quote = ds.get_realtime_quote(code)
        if quote:
            print(f"  行情: {quote.get('name')} - {quote.get('price')} (来源: {quote.get('source')})")
        
        # 历史数据
        hist = ds.get_historical_data(code, days=30)
        if hist is not None:
            print(f"  历史: {len(hist)} 条数据")
        
        # 财务数据
        fin = ds.get_financial_data(code)
        if fin is not None:
            print(f"  财务: {len(fin)} 条数据")
    
    print("\n测试完成!")
