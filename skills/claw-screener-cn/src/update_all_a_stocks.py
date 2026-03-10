#!/usr/bin/env python3
"""
A股全量数据获取器 - 混合数据源
K线: Sina/EastMoney (可用)
财务: akshare (可用)
"""
import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
import json
import time
import random

STOCKS_DIR = Path("/home/liujerry/金融数据/stocks")
FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
FINANCIAL_A_FILE = FINANCIAL_DIR / "profit.csv"


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


def fetch_kline_sina(symbol: str) -> pd.DataFrame:
    """使用新浪API获取K线数据"""
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


def update_all_a_stocks(batch_size: int = 50):
    """批量更新全量A股数据"""
    
    print("=" * 60)
    print("📈 A股全量数据更新 (混合数据源)")
    print("   K线: Sina API")
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
    
    for i, (code, name) in enumerate(stocks[:batch_size]):
        print(f"\n[{i+1}/{min(batch_size, total)}] {code} {name}...")
        
        # 获取K线 (Sina)
        try:
            df = fetch_kline_sina(code)
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
        
        # 避免请求过快
        time.sleep(random.uniform(0.3, 0.6))
        
        if (i + 1) % 10 == 0:
            print(f"\n   📊 进度: {i+1}/{min(batch_size, total)}")
    
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
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    update_all_a_stocks(batch_size=batch)
