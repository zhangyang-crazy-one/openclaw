#!/usr/bin/env python3
"""
财务数据获取器 - 使用 akshare
更新 profit.csv 财务数据
"""
import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
PROFIT_FILE = FINANCIAL_DIR / "profit.csv"


def get_financial_abstract(symbol: str) -> dict:
    """获取财务摘要数据"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator='按报告期')
        
        if df is None or df.empty:
            return {}
        
        # 取最新报告期数据
        latest = df.iloc[-1]
        
        # 解析净利润 (如 "63.27亿" -> 63.27)
        def parse_value(val):
            if pd.isna(val):
                return 0
            if isinstance(val, (int, float)):
                return float(val)
            val = str(val)
            if '亿' in val:
                return float(val.replace('亿', '')) * 100000000
            if '万' in val:
                return float(val.replace('万', '')) * 10000
            try:
                return float(val)
            except:
                return 0
        
        # 解析百分比 (如 "55.20%" -> 0.5520)
        def parse_pct(val):
            if pd.isna(val):
                return 0
            if isinstance(val, (int, float)):
                return float(val) / 100 if abs(float(val)) > 1 else float(val)
            val = str(val).replace('%', '')
            try:
                return float(val) / 100
            except:
                return 0
        
        # 直接使用 akshare 提供的 ROE
        roe = parse_pct(latest.get('净资产收益率', 0))
        
        record = {
            'code': f"sz.{symbol}" if symbol.startswith('3') else f"sh.{symbol}",
            'pubDate': datetime.now().strftime("%Y-%m-%d"),
            'statDate': str(latest.get('报告期', '')),
            'roeAvg': roe,
            'npMargin': parse_pct(latest.get('销售净利率', 0)),
            'gpMargin': parse_pct(latest.get('销售毛利率', 0)),
            'netProfit': parse_value(latest.get('净利润', 0)),
            'epsTTM': parse_value(latest.get('基本每股收益', 0)),
            'MBRevenue': parse_value(latest.get('营业总收入', 0)),
            'totalShare': 0,
            'liqaShare': 0,
        }
        
        return record
        
    except Exception as e:
        print(f"  获取失败: {e}")
        return {}


def update_financial_data(symbols: list) -> dict:
    """批量更新财务数据"""
    
    print(f"\n📋 开始更新财务数据 (akshare): {len(symbols)} 只股票")
    print("=" * 50)
    
    # 读取现有数据
    existing_data = {}
    if PROFIT_FILE.exists():
        try:
            df = pd.read_csv(PROFIT_FILE)
            for _, row in df.iterrows():
                code = row.get('code', '')
                if code:
                    existing_data[code] = row.to_dict()
            print(f"已读取 {len(existing_data)} 条现有记录")
        except Exception as e:
            print(f"读取现有数据失败: {e}")
    
    # 更新
    updated = 0
    failed = []
    
    for i, symbol in enumerate(symbols):
        print(f"[{i+1}/{len(symbols)}] {symbol}...", end=" ")
        
        record = get_financial_abstract(symbol)
        
        if record:
            existing_data[record['code']] = record
            updated += 1
            print(f"✅ ROE={record.get('roeAvg', 0):.1%}")
        else:
            failed.append(symbol)
            print("❌")
        
        time.sleep(0.5)  # 避免请求过快
    
    # 保存
    if existing_data:
        df = pd.DataFrame(list(existing_data.values()))
        df.to_csv(PROFIT_FILE, index=False)
        print(f"\n✅ 已保存 {len(existing_data)} 条记录")
    
    return {'updated': updated, 'failed': failed}


if __name__ == "__main__":
    WATCHLIST = [
        '300276', '300199', '300502', '300394', '300308',
        '300628', '300533', '300274', '300251', '300604', '300456'
    ]
    
    import sys
    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
    else:
        symbols = WATCHLIST
    
    update_financial_data(symbols)
