#!/usr/bin/env python3
"""
A股全量数据获取器 - 混合数据源
K线: Sina/EastMoney (可用)
财务: akshare (可用)
"""
import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import requests
import json
import time
import random

STOCKS_DIR = Path("/home/liujerry/金融数据/stocks")
FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
FINANCIAL_A_FILE = FINANCIAL_DIR / "profit.csv"

# EastMoney API headers
EM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.eastmoney.com/"
}


def get_a_stock_codes() -> list:
    """获取A股股票代码列表"""
    try:
        df = ak.stock_info_a_code_name()
        codes = []
        for _, row in df.iterrows():
            code = row['code']
            if code.startswith('6') or code.startswith('0') or code.startswith('3'):
                codes.append((code, row['name']))
        return codes
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return [(f"{i:06d}", f"股票{i}") for i in range(1, 100)]


def fetch_kline_eastmoney(symbol: str) -> pd.DataFrame:
    """使用东方财富API获取K线数据"""
    try:
        # EastMoney: 沪市(6xxxxx)=1, 深市(0/3xxxxx)=0
        market = 1 if symbol.startswith('6') else 0
        
        url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": f"{market}.{symbol}",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",   # 日K线
            "fqt": "1",     # 前复权
            "beg": "0",
            "end": "20500101",
            "lmt": "90"     # 最近90天
        }
        
        response = requests.get(url, params=params, headers=EM_HEADERS, timeout=10)
        if response.status_code != 200:
            return pd.DataFrame()
        
        data = response.json()
        klines = data.get("data", {}).get("klines", [])
        if not klines:
            return pd.DataFrame()
        
        # 解析K线数据: date,open,close,high,low,volume,amount,...
        records = []
        for line in klines:
            parts = line.split(',')
            if len(parts) >= 6:
                records.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': int(parts[5]),
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        # 只保留需要的列
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


def fetch_kline_sina(symbol: str) -> pd.DataFrame:
    """使用新浪API获取K线数据 (备用)"""
    try:
        # 沪市用sh, 深市用sz
        exchange = "sh" if symbol.startswith('6') else "sz"
        
        url = f"https://quotes.sina.cn/cn/api/jsonp.php/var%20_{symbol}=/CN_MarketDataService.getKLineData"
        params = {
            "symbol": f"{exchange}{symbol}",
            "scale": "240",
            "ma": "no",
            "datalen": "500"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return pd.DataFrame()
        
        text = response.text
        start = text.find('[')
        end = text.rfind(']') + 1
        if start == -1:
            return pd.DataFrame()
        
        data = json.loads(text[start:end])
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.rename(columns={
            'day': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        
        # 只保留最近90天
        if len(df) > 90:
            df = df.tail(90)
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


def fetch_kline_tencent(symbol: str, days: int = 90) -> pd.DataFrame:
    """使用腾讯证券API获取K线数据 - akshare stock_zh_a_hist_tx"""
    try:
        # 腾讯证券格式: sz000001 (深市/创业板), sh600000 (沪市/科创板)
        if symbol.startswith('6'):
            tx_symbol = f'sh{symbol}'
        else:
            tx_symbol = f'sz{symbol}'
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist_tx(
            symbol=tx_symbol,
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        # 转换列名以保持兼容 (腾讯接口返回amount而非volume)
        df = df.rename(columns={
            'date': 'date', 
            'open': 'open', 
            'high': 'high', 
            'low': 'low', 
            'close': 'close', 
            'amount': 'volume'
        })
        
        # 只保留需要的列和最近90天
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        if len(df) > days:
            df = df.tail(days)
        
        return df
        
    except Exception as e:
        return pd.DataFrame()


def fetch_financial_akshare(symbol: str) -> dict:
    """使用akshare获取财务数据"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator='按报告期')
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            
            def parse_val(v):
                if pd.isna(v):
                    return 0
                if isinstance(v, (int, float)):
                    return float(v)
                v = str(v)
                if '亿' in v:
                    return float(v.replace('亿', '')) * 1e8
                if '万' in v:
                    return float(v.replace('万', '')) * 1e4
                try:
                    return float(v.replace('%', ''))
                except:
                    return 0
            
            def parse_pct(v):
                if pd.isna(v):
                    return 0
                if isinstance(v, (int, float)):
                    return float(v) / 100 if abs(float(v)) > 1 else float(v)
                try:
                    return float(str(v).replace('%', '')) / 100
                except:
                    return 0
            
            return {
                'code': f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}",
                'pubDate': datetime.now().strftime("%Y-%m-%d"),
                'statDate': str(latest.get('报告期', '')),
                'roeAvg': parse_pct(latest.get('净资产收益率', 0)),
                'npMargin': parse_pct(latest.get('销售净利率', 0)),
                'gpMargin': parse_pct(latest.get('销售毛利率', 0)),
                'netProfit': parse_val(latest.get('净利润', 0)),
                'epsTTM': parse_val(latest.get('基本每股收益', 0)),
                'MBRevenue': parse_val(latest.get('营业总收入', 0)),
                'totalShare': 0,
                'liqaShare': 0,
            }
    except:
        pass
    return {}


def update_all_a_stocks(batch_size: int = 50, start: int = 0):
    """批量更新全量A股数据
    
    Args:
        batch_size: 本次处理的股票数量
        start: 从哪个索引开始（0=从000001开始，1491=从300001开始）
    """
    
    print("=" * 60)
    print("📈 A股全量数据更新 (混合数据源)")
    print("   K线: EastMoney API")
    print("   财务: akshare")
    print("=" * 60)
    
    # 获取股票列表
    print("\n📋 获取A股股票列表...")
    stocks = get_a_stock_codes()
    print(f"   A股总数: {len(stocks)} 只")
    
    # 读取现有财务数据
    existing_financial = {}
    if FINANCIAL_A_FILE.exists():
        try:
            df = pd.read_csv(FINANCIAL_A_FILE)
            for _, row in df.iterrows():
                code = row.get('code', '')
                if code:
                    existing_financial[code] = row.to_dict()
            print(f"   已有财务记录: {len(existing_financial)} 条")
        except:
            pass
    
    # 分批处理
    total = len(stocks)
    success_kline = 0
    success_financial = 0
    failed = []
    
    end = min(start + batch_size, total)
    for i, (code, name) in enumerate(stocks[start:end]):
        idx = start + i
        print(f"\n[{idx+1}/{total}] {code} {name}...")
        
        # 获取K线 (腾讯证券)
        try:
            df = fetch_kline_tencent(code)
            if not df.empty:
                stock_file = STOCKS_DIR / f"{code}.csv"
                df.to_csv(stock_file, index=False)
                success_kline += 1
                print(f"   ✅ K线: {len(df)} 条")
            else:
                print(f"   ❌ K线: 无数据")
        except Exception as e:
            print(f"   ❌ K线失败")
        
        # 获取财务 (akshare)
        try:
            fin = fetch_financial_akshare(code)
            if fin:
                existing_financial[fin['code']] = fin
                success_financial += 1
                print(f"   ✅ 财务: ROE={fin.get('roeAvg', 0)*100:.1f}%")
            else:
                print(f"   ❌ 财务: 无数据")
        except Exception as e:
            print(f"   ❌ 财务失败")
        
        # 避免请求过快 (EastMoney API)
        time.sleep(random.uniform(0.3, 0.6))
        
        if (i + 1) % 10 == 0:
            print(f"\n   📊 进度: {i+1}/{end - start}")
    
    # 保存财务数据
    if existing_financial:
        df_fin = pd.DataFrame(list(existing_financial.values()))
        df_fin.to_csv(FINANCIAL_A_FILE, index=False)
        print(f"\n✅ 财务数据已保存: {len(df_fin)} 条")
    
    print("\n" + "=" * 60)
    print(f"📊 更新完成:")
    print(f"   K线数据: {success_kline} 只")
    print(f"   财务数据: {success_financial} 只")
    print("=" * 60)
    
    return {
        'kline': success_kline,
        'financial': success_financial,
    }


if __name__ == "__main__":
    import sys
    batch = 50
    start = 0
    for arg in sys.argv[1:]:
        if arg.startswith('--start='):
            start = int(arg.split('=')[1])
        else:
            batch = int(arg)
    update_all_a_stocks(batch_size=batch, start=start)
