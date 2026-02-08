#!/usr/bin/env python3
"""
股票数据获取脚本
使用 akshare + baostock 获取 A 股股票历史数据
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 股票列表
STOCKS = [
    ("159866", "日经ETF"),
    ("159321", "黄金股票ETF"),
    ("159501", "纳指ETF"),
    ("159502", "标普生物ETF"),
    ("601398", "工商银行"),
    ("601288", "农业银行"),
    ("601939", "建设银行"),
    ("601988", "中国银行"),
    ("000001", "平安银行"),
    ("600030", "中信证券"),
    ("600028", "中国石化"),
    ("600519", "贵州茅台"),
    ("000338", "潍柴动力"),
    ("002032", "苏泊尔"),
    ("300251", "光线传媒"),
    ("300766", "每日互动"),
    ("300229", "拓尔思"),
    ("300007", "汉威科技"),
    ("300276", "三丰智能"),
    ("300545", "联得装备"),
    ("300418", "昆仑万维"),
    ("300661", "圣邦股份"),
    ("301330", "熵基科技"),
    ("002594", "比亚迪"),
    ("300763", "锦浪科技"),
    ("300639", "凯普生物"),
    ("603986", "兆易创新"),
    ("603195", "公牛集团"),
    ("399001", "深证成指"),
    ("399006", "创业板指"),
    ("000300", "沪深300"),
]

def get_date_range():
    today = datetime.now()
    return (today - timedelta(days=30)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

def fetch_akshare(symbol, name):
    """akshare 数据源"""
    import akshare as ak
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=get_date_range()[0].replace("-", ""),
            end_date=get_date_range()[1].replace("-", ""),
            adjust="qfq"
        )
        if df is not None and not df.empty:
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            })
            return df[['date', 'open', 'close', 'high', 'low', 'volume']], "akshare"
    except:
        pass
    return None, None

def fetch_baostock(symbol, name):
    """baostock 备用数据源"""
    import baostock as bs
    start_date, end_date = get_date_range()
    
    try:
        lg = bs.login()
        if lg.error_code != '0':
            return None, None
        
        # 转换股票代码格式
        bs_symbol = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
        
        rs = bs.query_history_k_data_plus(
            bs_symbol,
            "date,open,high,low,close,volume",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2"
        )
        
        data_list = []
        while (rs.error_code == '0') and rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if data_list:
            import pandas as pd
            df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df, "baostock"
    except Exception as e:
        pass
    
    return None, None

def fetch_stock_data(symbol, name):
    """获取股票数据（多数据源）"""
    # 优先 akshare
    df, source = fetch_akshare(symbol, name)
    if df is not None:
        return df, source
    
    # 备用 baostock
    time.sleep(0.3)
    df, source = fetch_baostock(symbol, name)
    if df is not None:
        return df, source
    
    return None, None

def save_to_csv(df, symbol):
    output_dir = Path("/home/liujerry/金融数据/stocks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{symbol}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    return output_file

def fetch_all_stocks():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 60)
    print(f"📈 股票数据获取（akshare + baostock）")
    print(f"⏰ {timestamp}")
    print("=" * 60)
    
    success = failed = 0
    source_counts = {"akshare": 0, "baostock": 0}
    
    for i, (symbol, name) in enumerate(STOCKS, 1):
        print(f"[{i}/{len(STOCKS)}] {symbol} ({name})...", end=" ")
        
        df, source = fetch_stock_data(symbol, name)
        
        if df is not None:
            save_to_csv(df, symbol)
            latest_date = df['date'].iloc[-1]
            latest_close = df['close'].iloc[-1]
            print(f"✓ ({source}, {latest_date}, {latest_close:.2f})")
            success += 1
            source_counts[source] = source_counts.get(source, 0) + 1
        else:
            print("✗")
            failed += 1
    
    print(f"\n📊 完成: {success} ({source_counts}), 失败: {failed}")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "success",
        "success": success,
        "failed": failed,
        "sources": source_counts,
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        name_map = {code: name for code, name in STOCKS}
        name = name_map.get(symbol, symbol)
        df, source = fetch_stock_data(symbol, name)
        if df is not None:
            save_to_csv(df, symbol)
            print(f"✅ {symbol} ({name}) from {source}")
        else:
            print(f"❌ {symbol} ({name}) failed")
    else:
        fetch_all_stocks()
