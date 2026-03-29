"""
A股股票数据获取 - 使用 Baostock + Akshare
"""
import baostock as bs
import akshare as ak
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import requests

class AStockDataFetcher:
    """A股数据获取器（多通道 + 缓存）"""
    
    def __init__(self):
        self._login_baostock()
        self._sina_spot_cache = None  # Sina全市场缓存
        self._sina_spot_cache_time = None
        self._sina_spot_cache_ttl = 300  # 缓存5分钟
    
    def _login_baostock(self):
        """登录Baostock"""
        self._lg = bs.login()
    
    def _get_sina_spot_cached(self):
        """获取 Sina 全市场数据（带缓存，避免每次等待40秒）"""
        import time
        now = time.time()
        if self._sina_spot_cache is not None and self._sina_spot_cache_time is not None:
            if now - self._sina_spot_cache_time < self._sina_spot_cache_ttl:
                return self._sina_spot_cache
        
        print("  [data_fetcher] 刷新 Sina 全市场缓存...")
        try:
            df = ak.stock_zh_a_spot()  # ~40秒加载
            self._sina_spot_cache = df
            self._sina_spot_cache_time = now
            return df
        except Exception as e:
            print(f"  [data_fetcher] Sina spot 加载失败: {e}")
            if self._sina_spot_cache is not None:
                print("  [data_fetcher] 使用过期缓存")
                return self._sina_spot_cache
            return None
    
    def get_stock_list(self, market: str = "all") -> List[str]:
        """
        获取股票列表
        
        Args:
            market: "all"(全部), "sh"(沪市), "sz"(深市), "cy"(创业板)
        
        Returns:
            股票代码列表，如 ['sh.600000', 'sz.000001', ...]
        """
        if market == "all":
            rs = bs.query_all_stock()
        elif market == "sh":
            rs = bs.query_sh_stock_list()
        elif market == "sz":
            rs = bs.query_sz_stock_list()
        elif market == "cy":
            rs = bs.query_cy_stock_list()
        else:
            rs = bs.query_all_stock()
        
        stocks = []
        while rs.next():
            stocks.append(rs.get_row_data())
        
        # 返回格式: [code, name, ...]
        return [s[0] for s in stocks]
    
    def get_price_data(self, stock_code: str, days: int = 90) -> Optional[pd.DataFrame]:
        """
        获取股票价格数据
        
        Args:
            stock_code: 股票代码，如 'sh.600000' 或 '600000'
            days: 获取天数
        
        Returns:
            DataFrame with OHLC data
        """
        # 格式化代码
        if '.' not in stock_code:
            # 判断市场
            if stock_code.startswith('6'):
                stock_code = f'sh.{stock_code}'
            else:
                stock_code = f'sz.{stock_code}'
        
        # 计算日期
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y-%m-%d')
        
        rs = bs.query_history_k_data_plus(
            stock_code,
            'date,code,open,high,low,close,volume,amount,turn,pctChg',
            start_date=start_date,
            end_date=end_date,
            frequency='d',
            adjustflag='3'  # 前复权
        )
        
        if rs is None:
            return None
        
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return None
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 转换数据类型
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _get_sina_realtime_via_http(self, code: str) -> Optional[Dict]:
        """通过 Sina HTTP API 获取单只股票实时行情（快，约1秒）"""
        try:
            # 转换代码格式: 600000 -> sh600000, 000001 -> sz000001
            if code.startswith('6') or code.startswith('9'):
                sym = f'sh{code}'
            else:
                sym = f'sz{code}'
            
            url = f'https://hq.sinajs.cn/list={sym}'
            headers = {'Referer': 'http://finance.sina.com.cn', 'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code != 200:
                return None
            
            text = resp.text.strip()
            # 格式: var hq_str_sz000001="平安银行,10.50,10.60,10.55,10.58,10.52,10.55,1000000,..."
            if '=' not in text or '"' not in text:
                return None
            
            data_str = text.split('"')[1]
            fields = data_str.split(',')
            
            if len(fields) < 32:
                return None
            
            # fields: 名称,今开,昨收,最新价,最高,最低,...
            return {
                'code': code,
                'name': fields[0],
                'price': float(fields[3]),
                'open': float(fields[1]),
                'close': float(fields[2]),
                'high': float(fields[4]),
                'low': float(fields[5]),
                'volume': float(fields[8]) if fields[8] else 0,
                'amount': float(fields[9]) if fields[9] else 0,
                'change': (float(fields[3]) - float(fields[2])) / float(fields[2]) * 100 if float(fields[2]) != 0 else 0,
                'amplitude': ((float(fields[4]) - float(fields[5])) / float(fields[2]) * 100) if float(fields[2]) != 0 else 0,
                'source': 'sina-http'
            }
        except Exception as e:
            print(f"  [data_fetcher] Sina HTTP 失败: {e}")
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """
        获取实时行情（多通道 fallback）
        优先级: eastmoney -> sina-http -> sina-cache -> baostock
        
        Args:
            stock_code: 股票代码，如 'sh600000' 或 '600000'
        
        Returns:
            dict with price data
        """
        code = stock_code.replace('.', '')
        
        # 通道1: 东方财富 (eastmoney) - 最快
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == code]
            if not row.empty:
                row = row.iloc[0]
                return {
                    'code': code,
                    'name': row['名称'],
                    'price': row['最新价'],
                    'change': row['涨跌幅'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'amplitude': row['振幅'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'open': row['今开'],
                    'close': row['昨收'],
                    'source': 'eastmoney'
                }
        except Exception as e:
            print(f"  [data_fetcher] eastmoney 失败: {e}")
        
        # 通道2: Sina HTTP 单股查询 - 快（约1秒）
        result = self._get_sina_realtime_via_http(code)
        if result:
            return result
        
        # 通道3: Sina 全量缓存（如果已有缓存则快，否则约40秒）
        df = self._get_sina_spot_cached()
        if df is not None:
            row = df[df['代码'] == code]
            if not row.empty:
                row = row.iloc[0]
                return {
                    'code': code,
                    'name': row['名称'],
                    'price': row['最新价'],
                    'change': row['涨跌幅'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'amplitude': row['振幅'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'open': row['今开'],
                    'close': row['昨收'],
                    'source': 'sina-cache'
                }
        
        # 通道4: Baostock 最新收盘（实时性差一些，但可靠）
        try:
            bs_code = f'sh{code}' if code.startswith('6') else f'sz{code}'
            rs = bs.query_history_k_data_plus(
                bs_code,
                'date,open,high,low,close,volume,amount',
                start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                frequency='d',
            )
            if rs.error_code == '0':
                rows = []
                while rs.next():
                    rows.append(rs.get_row_data())
                if rows:
                    latest = rows[-1]
                    close = float(latest[4])
                    open_p = float(latest[2])
                    high = float(latest[3])
                    low = float(latest[4])
                    prev_close = float(rows[-2][4]) if len(rows) > 1 else close
                    return {
                        'code': code,
                        'name': '',
                        'price': close,
                        'open': open_p,
                        'close': prev_close,
                        'high': high,
                        'low': low,
                        'volume': float(latest[5]),
                        'amount': float(latest[6]),
                        'change': (close - prev_close) / prev_close * 100 if prev_close else 0,
                        'amplitude': (high - low) / prev_close * 100 if prev_close else 0,
                        'source': 'baostock'
                    }
        except Exception as e:
            print(f"  [data_fetcher] baostock 失败: {e}")
        
        return None
    
    def get_financial_data(self, stock_code: str) -> Optional[Dict]:
        """
        获取基本面数据
        
        Args:
            stock_code: 股票代码，如 '600000'
        
        Returns:
            dict with financial metrics
        """
        try:
            # 格式化代码
            code = stock_code.zfill(6)
            
            # 使用 Akshare 获取财务数据
            # 利润表 (同花顺)
            profit_df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            
            # 资产负债表 (同花顺 - 实际是 debt)
            balance_df = None
            try:
                balance_df = ak.stock_financial_debt_ths(symbol=code, indicator="按报告期")
            except Exception as e:
                print(f"  [data_fetcher] 资产负债表获取失败: {e}")
            
            # 财务指标 (同花顺)
            indicator_df = None
            try:
                indicator_df = ak.stock_financial_analysis_indicator(symbol=code, start_year='2024')
            except Exception as e:
                print(f"  [data_fetcher] 财务指标获取失败: {e}")
            
            if profit_df is None or profit_df.empty:
                return None
            
            # 获取最新数据（数据按时间倒序，最新在最后）
            latest = profit_df.iloc[-1] if len(profit_df) > 0 else None
            
            if latest is None:
                return None
            
            # 提取关键指标
            result = {
                'code': code,
                'report_date': str(latest.get('报告日期', '')),
                'revenue': latest.get('营业总收入', 0),
                'net_profit': latest.get('净利润', 0),
                'roe': latest.get('净资产收益率', 0),
                'gross_margin': latest.get('销售毛利率', 0),
                'debt_ratio': latest.get('资产负债率', 0),
            }
            
            # 如果有指标数据，添加更多
            if indicator_df is not None and not indicator_df.empty:
                ind = indicator_df.iloc[-1]  # 取最新一期
                result.update({
                    'eps': ind.get('基本每股收益', 0),
                    'bps': ind.get('每股净资产_调整前', 0),
                    'pe': ind.get('市盈率', 0),
                    'pb': ind.get('市净率', 0),
                })
            
            return result
            
        except Exception as e:
            print(f"Error fetching financial data: {e}")
            return None
    
    def get_index_components(self, index_code: str = "000300") -> List[str]:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码，如 '000300'(沪深300), '399006'(创业板指)
        
        Returns:
            股票代码列表
        """
        try:
            if index_code == "000300":
                # 沪深300
                df = ak.index_stock_cons_csindex(symbol="000300")
            elif index_code == "399006":
                # 创业板指
                df = ak.index_stock_cons_sina(symbol="399006")
            elif index_code == "000852":
                # 中证1000
                df = ak.index_stock_cons_csindex(symbol="000852")
            else:
                return []
            
            if df is None or df.empty:
                return []
            
            return df['成分券代码'].tolist()
            
        except Exception as e:
            print(f"Error fetching index components: {e}")
            return []
    
    def close(self):
        """退出登录"""
        bs.logout()


# 便捷函数
def get_china_stock_list() -> List[str]:
    """获取全部A股列表"""
    fetcher = AStockDataFetcher()
    stocks = fetcher.get_stock_list()
    fetcher.close()
    return stocks


def get_realtime_price(stock_code: str) -> Optional[Dict]:
    """获取实时价格"""
    fetcher = AStockDataFetcher()
    data = fetcher.get_realtime_quote(stock_code)
    fetcher.close()
    return data


if __name__ == "__main__":
    # 测试
    fetcher = AStockDataFetcher()
    
    # 获取沪深300成分股
    print("获取沪深300成分股...")
    stocks = fetcher.get_index_components("000300")
    print(f"沪深300成分股数量: {len(stocks)}")
    print(f"前10只: {stocks[:10]}")
    
    # 获取价格数据
    if stocks:
        print("\n获取价格数据...")
        df = fetcher.get_price_data(stocks[0], 90)
        if df is not None:
            print(df.tail())
    
    fetcher.close()
