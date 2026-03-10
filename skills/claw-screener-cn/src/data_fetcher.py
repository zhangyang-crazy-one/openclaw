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
    """A股数据获取器"""
    
    def __init__(self):
        self._login_baostock()
    
    def _login_baostock(self):
        """登录Baostock"""
        self._lg = bs.login()
    
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
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """
        获取实时行情
        
        Args:
            stock_code: 股票代码，如 'sh600000' 或 '600000'
        
        Returns:
            dict with price data
        """
        try:
            # 格式化代码
            code = stock_code.replace('.', '')
            
            # 使用 Akshare 获取实时数据
            df = ak.stock_zh_a_spot_em()
            
            # 过滤
            row = df[df['代码'] == code]
            if row.empty:
                return None
            
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
            }
        except Exception as e:
            print(f"Error fetching realtime quote: {e}")
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
            # 利润表
            profit_df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            
            # 资产负债表
            balance_df = ak.stock_financial_balance_sheet_ths(symbol=code, indicator="按报告期")
            
            # 财务指标
            indicator_df = ak.stock_financial_indicator_ths(symbol=code)
            
            if profit_df is None or profit_df.empty:
                return None
            
            # 获取最新数据
            latest = profit_df.iloc[0] if len(profit_df) > 0 else None
            
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
                ind = indicator_df.iloc[0]
                result.update({
                    'eps': ind.get('基本每股收益', 0),
                    'bps': ind.get('每股净资产', 0),
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
