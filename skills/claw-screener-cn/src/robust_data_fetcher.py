#!/usr/bin/env python3
"""
多数据源股票数据获取器 - 完整版
获取: K线数据、财务数据、实时行情、交易数据
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import time
import random
import json

DATA_DIR = Path("/home/liujerry/金融数据/stocks_backup")
FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")


class DataSource:
    """数据源基类"""
    def get_kline(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        raise NotImplementedError
    
    def get_realtime(self, symbol: str) -> Optional[dict]:
        raise NotImplementedError
    
    def get_financial(self, symbol: str) -> Optional[dict]:
        raise NotImplementedError
    
    def get_trading(self, symbol: str) -> Optional[dict]:
        raise NotImplementedError
    
    def name(self) -> str:
        raise NotImplementedError


class SinaSource(DataSource):
    """新浪财经数据源"""
    def name(self) -> str:
        return "sina"
    
    def get_kline(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            import requests
            url = f"https://quotes.sina.cn/cn/api/jsonp.php/var%20_{symbol}=/CN_MarketDataService.getKLineData"
            params = {
                "symbol": f"sz{symbol}" if symbol.startswith('3') else f"sh{symbol}",
                "scale": "240",
                "ma": "no",
                "datalen": "1024"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            text = response.text
            start = text.find('[')
            end = text.rfind(']') + 1
            if start == -1:
                return None
            
            data = json.loads(text[start:end])
            if not data:
                return None
            
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'day': 'date', 'open': 'open', 'high': 'high', 
                'low': 'low', 'close': 'close', 'volume': 'volume'
            })
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            return df
        except Exception as e:
            return None
    
    def get_realtime(self, symbol: str) -> Optional[dict]:
        try:
            import requests
            exchange = "sz" if symbol.startswith('3') else "sh"
            url = f"https://hq.sinajs.cn/list={exchange}{symbol}"
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None
            
            text = response.text
            if '=' not in text:
                return None
            
            parts = text.split('=')[1].split(',')
            if len(parts) < 32:
                return None
            
            return {
                'name': parts[0],
                'open': float(parts[1]) if parts[1] else None,
                'high': float(parts[2]) if parts[2] else None,
                'low': float(parts[3]) if parts[3] else None,
                'close': float(parts[4]) if parts[4] else None,
                'volume': float(parts[5]) if parts[5] else None,
                'amount': float(parts[6]) if parts[6] else None,
                'bid1': float(parts[11]) if len(parts) > 11 and parts[11] else None,
                'ask1': float(parts[13]) if len(parts) > 13 and parts[13] else None,
                'turnover': float(parts[38]) if len(parts) > 38 and parts[38] else None,
            }
        except:
            return None
    
    def get_financial(self, symbol: str) -> Optional[dict]:
        # 新浪财务数据
        try:
            import requests
            exchange = "sz" if symbol.startswith('3') else "sh"
            url = f"https://finance.sina.com.cn/realstock/company/{exchange}{symbol}/nc.shtml"
            # 简化版本，返回空
            return {}
        except:
            return None
    
    def get_trading(self, symbol: str) -> Optional[dict]:
        # 新浪资金流向
        try:
            import requests
            url = f"https://money6.sina.cn/lm/zhangban/data/{symbol}.js"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                text = response.text
                # 解析资金数据
                return {'source': 'sina', 'raw': text[:500]}
            return {}
        except:
            return {}


class EastMoneySource(DataSource):
    """东方财富数据源"""
    def name(self) -> str:
        return "eastmoney"
    
    def get_kline(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            import requests
            
            secid = f"1.{symbol}" if symbol.startswith('6') else f"0.{symbol}"
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": "101",
                "fqt": "1",
                "beg": start_date.replace('-', ''),
                "end": end_date.replace('-', ''),
                "lmt": "1000000"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get('data') is None:
                return None
            
            klines = data['data']['klines']
            if not klines:
                return None
            
            records = []
            for line in klines:
                parts = line.split(',')
                records.append({
                    'date': parts[0],
                    'open': parts[1],
                    'high': parts[2],
                    'low': parts[3],
                    'close': parts[4],
                    'volume': parts[5],
                    'amount': parts[6] if len(parts) > 6 else None,
                })
            
            return pd.DataFrame(records)
        except Exception as e:
            return None
    
    def get_realtime(self, symbol: str) -> Optional[dict]:
        try:
            import requests
            
            secid = f"1.{symbol}" if symbol.startswith('6') else f"0.{symbol}"
            url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                "fltt": "2",
                "invt": "2",
                "fields": "f2,f3,f4,f5,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f30,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f62,f115,f117,f128,f140,f141",
                "secids": secid
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get('data'):
                return None
            
            item = data['data']['diff'][0]
            return {
                'name': item.get('f14'),
                'close': item.get('f2'),
                'change': item.get('f3'),
                'change_pct': item.get('f4'),
                'volume': item.get('f5'),
                'amount': item.get('f6'),
                'open': item.get('f17'),
                'high': item.get('f15'),
                'low': item.get('f16'),
                'turnover': item.get('f38'),  # 换手率
                'pe': item.get('f162'),  # 市盈率
                'pb': item.get('f167'),  # 市净率
            }
        except:
            return None
    
    def get_financial(self, symbol: str) -> Optional[dict]:
        """获取财务指标"""
        try:
            import requests
            
            secid = f"1.{symbol}" if symbol.startswith('6') else f"0.{symbol}"
            url = "https://emweb.securities.eastmoney.com/PC_HSF10/FinancialAnalysis/MainTargetAjax"
            params = {"code": secid}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return {}
            
            data = response.json()
            return data if data else {}
        except:
            return {}
    
    def get_trading(self, symbol: str) -> Optional[dict]:
        """获取资金流向"""
        try:
            import requests
            
            secid = f"1.{symbol}" if symbol.startswith('6') else f"0.{symbol}"
            url = "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get"
            params = {
                "lmt": "30",
                "fields1": "f1,f2,f3,f4,f7",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
                "secid": secid
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                return {}
            
            data = response.json()
            if not data.get('data'):
                return {}
            
            klines = data['data']['klines']
            records = []
            for line in klines:
                parts = line.split(',')
                records.append({
                    'date': parts[0],
                    'main_inflow': parts[1],   # 主力净流入
                    'small_inflow': parts[2],   # 小单净流入
                    'medium_inflow': parts[3],  # 中单净流入
                    'large_inflow': parts[4],   # 大单净流入
                })
            
            return {'capital_flow': records}
        except:
            return {}


class XueqiuSource(DataSource):
    """雪球数据源"""
    def name(self) -> str:
        return "xueqiu"
    
    def get_kline(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            import requests
            
            url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
            headers = {'Cookie': 'xq_a_token=test', 'User-Agent': 'Mozilla/5.0'}
            
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
            
            params = {
                "symbol": f"SH{symbol}" if symbol.startswith('6') else f"SZ{symbol}",
                "begin": end_ts,
                "period": "day",
                "type": "before",
                "count": "-180",
                "indicator": "kline"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if 'data' not in data:
                return None
            
            klines = data['data'].get('klines', [])
            if not klines:
                return None
            
            records = []
            for line in klines:
                parts = line.split(',')
                records.append({
                    'date': parts[0],
                    'open': parts[1],
                    'high': parts[2],
                    'low': parts[3],
                    'close': parts[4],
                    'volume': parts[5],
                })
            
            return pd.DataFrame(records)
        except Exception as e:
            return None
    
    def get_realtime(self, symbol: str) -> Optional[dict]:
        return None
    
    def get_financial(self, symbol: str) -> Optional[dict]:
        return {}
    
    def get_trading(self, symbol: str) -> Optional[dict]:
        return {}


class RobustDataFetcher:
    """多数据源鲁棒获取器"""
    
    def __init__(self):
        self.sources = [
            EastMoneySource(),
            SinaSource(),
            XueqiuSource(),
        ]
    
    def get_kline(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        for source in self.sources:
            try:
                df = source.get_kline(symbol, start_date, end_date)
                if df is not None and len(df) > 0:
                    return df
            except:
                continue
        return None
    
    def get_realtime(self, symbol: str) -> Optional[dict]:
        for source in self.sources:
            try:
                data = source.get_realtime(symbol)
                if data:
                    data['source'] = source.name()
                    return data
            except:
                continue
        return None
    
    def get_financial(self, symbol: str) -> Optional[dict]:
        for source in self.sources:
            try:
                data = source.get_financial(symbol)
                if data:
                    return data
            except:
                continue
        return {}
    
    def get_trading(self, symbol: str) -> Optional[dict]:
        for source in self.sources:
            try:
                data = source.get_trading(symbol)
                if data:
                    return data
            except:
                continue
        return {}


def fetch_all_data(symbol: str, days: int = 90) -> dict:
    """获取股票所有数据"""
    from datetime import timedelta
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days+30)).strftime("%Y-%m-%d")
    
    fetcher = RobustDataFetcher()
    results = {'symbol': symbol, 'update_time': datetime.now().isoformat()}
    
    print(f"\n📊 {symbol} 数据获取")
    print("-" * 40)
    
    # 1. K线数据
    print("  📈 K线数据...", end=" ")
    df = fetcher.get_kline(symbol, start_date, end_date)
    if df is not None:
        kline_path = DATA_DIR / f"{symbol}.csv"
        df.to_csv(kline_path, index=False)
        results['kline'] = {'status': 'success', 'records': len(df), 'path': str(kline_path)}
        print(f"✅ {len(df)} 条")
    else:
        results['kline'] = {'status': 'failed'}
        print("❌")
    
    time.sleep(random.uniform(0.3, 0.8))
    
    # 2. 实时行情
    print("  💰 实时行情...", end=" ")
    realtime = fetcher.get_realtime(symbol)
    if realtime:
        results['realtime'] = realtime
        print(f"✅ {realtime.get('close', 'N/A')}")
    else:
        results['realtime'] = {}
        print("❌")
    
    # 3. 财务数据
    print("  📋 财务数据...", end=" ")
    financial = fetcher.get_financial(symbol)
    if financial:
        results['financial'] = financial
        print("✅")
    else:
        results['financial'] = {}
        print("❌")
    
    # 4. 资金流向
    print("  💵 资金流向...", end=" ")
    trading = fetcher.get_trading(symbol)
    if trading:
        results['trading'] = trading
        print("✅")
    else:
        results['trading'] = {}
        print("❌")
    
    return results


def fetch_watchlist(watchlist: List[str]) -> dict:
    """批量获取自选股数据"""
    print(f"\n🚀 开始批量获取 {len(watchlist)} 只股票完整数据")
    print("=" * 60)
    
    results = {}
    
    for i, symbol in enumerate(watchlist):
        print(f"\n[{i+1}/{len(watchlist)}]")
        result = fetch_all_data(symbol)
        results[symbol] = result
        
        time.sleep(random.uniform(0.5, 1.5))
    
    # 统计
    success = sum(1 for r in results.values() if r.get('kline', {}).get('status') == 'success')
    print("\n" + "=" * 60)
    print(f"📈 K线获取完成: {success}/{len(watchlist)} 成功")
    
    return results


if __name__ == "__main__":
    import sys
    
    WATCHLIST = [
        '300276', '300199', '300502', '300394', '300308',
        '300628', '300533', '300274', '300251', '300604', '300456',
        '300926', '300573'
    ]
    
    if len(sys.argv) > 1:
        # 单只股票
        if sys.argv[1] == '--realtime':
            symbol = sys.argv[2] if len(sys.argv) > 2 else '300502'
            fetcher = RobustDataFetcher()
            data = fetcher.get_realtime(symbol)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            symbol = sys.argv[1]
            fetch_all_data(symbol)
    else:
        # 默认自选股
        fetch_watchlist(WATCHLIST)
