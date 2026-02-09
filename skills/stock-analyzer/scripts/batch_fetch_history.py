#!/usr/bin/env python3
"""
批量获取所有A股历史数据
目标：每只股票至少1000条数据（4年历史）
截止日期：2026年2月6日
"""
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 截止日期
END_DATE = datetime(2026, 2, 6)
START_DATE = END_DATE - timedelta(days=1825)  # 5年 (约1250交易日)

# A股所有股票列表（测试用）
TEST_STOCKS = [
    # 沪深300
    ("600519", "贵州茅台"),
    ("601398", "工商银行"),
    ("600036", "招商银行"),
    ("601288", "农业银行"),
    ("601988", "中国银行"),
    ("601939", "建设银行"),
    ("600030", "中信证券"),
    ("600028", "中国石化"),
    ("601857", "中国石油"),
    ("600016", "民生银行"),
    # 中证500
    ("000338", "潍柴动力"),
    ("002032", "苏泊尔"),
    ("002594", "比亚迪"),
    ("002415", "海康威视"),
    ("002466", "中环股份"),
    ("002371", "北方华创"),
    ("002475", "富安娜"),
    ("002511", "中顺洁柔"),
    # 创业板
    ("300001", "特锐德"),
    ("300002", "神州泰岳"),
    ("300003", "乐普医疗"),
    ("300004", "南风股份"),
    ("300005", "探路者"),
    ("300006", "莱美药业"),
    ("300007", "汉威科技"),
    ("300008", "上海佳豪"),
    ("300009", "安科生物"),
    ("300010", "鼎龙股份"),
    ("300012", "华测检测"),
    ("300015", "爱尔眼科"),
    ("300016", "智飞生物"),
    ("300017", "网宿科技"),
    ("300018", "中科曙光"),
    ("300019", "硅宝科技"),
    ("300020", "银江股份"),
]

PROGRESS_FILE = Path.home() / ".config" / "deepseeker" / "stock_fetch_progress.json"


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "batch_index": 0, "total_fetched": 0}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)


def fetch_history_akshare(symbol, name):
    """akshare 获取历史数据"""
    try:
        import akshare as ak
        
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=START_DATE.strftime("%Y%m%d"),
            end_date=END_DATE.strftime("%Y%m%d"),
            adjust="qfq"
        )
        
        if df is not None and not df.empty:
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            })
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df[['date', 'open', 'close', 'high', 'low', 'volume']], "akshare"
    
    except Exception as e:
        pass
    
    return None, None


def fetch_history_baostock(symbol, name):
    """baostock 获取历史数据"""
    try:
        import baostock as bs
        
        lg = bs.login()
        if lg.error_code != '0':
            return None, None
        
        bs_symbol = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
        
        rs = bs.query_history_k_data_plus(
            bs_symbol,
            "date,open,high,low,close,volume",
            start_date=START_DATE.strftime("%Y-%m-%d"),
            end_date=END_DATE.strftime("%Y-%m-%d"),
            frequency="d",
            adjustflag="2"
        )
        
        data_list = []
        while (rs.error_code == '0') and rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if data_list:
            df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df, "baostock"
    
    except Exception as e:
        pass
    
    return None, None


def fetch_stock_history(symbol, name):
    """获取单只股票历史数据"""
    # 优先 akshare
    df, source = fetch_history_akshare(symbol, name)
    if df is not None:
        return df, source
    
    # 备用 baostock
    time.sleep(0.3)
    df, source = fetch_history_baostock(symbol, name)
    if df is not None:
        return df, source
    
    return None, None


def save_to_csv(df, symbol):
    output_dir = Path("/home/liujerry/金融数据/stocks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{symbol}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    return output_file


def get_batch_stocks(batch_index, batch_size=50):
    progress = load_progress()
    
    if 'all_stocks' not in progress:
        stocks = TEST_STOCKS
        progress['all_stocks'] = stocks
        progress['batch_size'] = batch_size
        save_progress(progress)
    else:
        stocks = progress['all_stocks']
    
    start_idx = batch_index * batch_size
    end_idx = min(start_idx + batch_size, len(stocks))
    
    return stocks[start_idx:end_idx]


def batch_fetch_history(batch_index=0, batch_size=50):
    """批量获取历史数据"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 70)
    print("📈 批量获取A股历史数据")
    print(f"⏰ {timestamp}")
    print(f"📅 范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")
    print(f"📦 批次: {batch_index}, 每批: {batch_size}只")
    print("=" * 70)
    
    progress = load_progress()
    completed = set(progress.get('completed', []))
    stocks = get_batch_stocks(batch_index, batch_size)
    
    if not stocks:
        print("✅ 所有批次已完成！")
        print(f"📊 总计获取: {progress.get('total_fetched', 0)} 只股票")
        return
    
    success = failed = 0
    source_counts = {}
    
    for i, (symbol, name) in enumerate(stocks, 1):
        if symbol in completed:
            print(f"[{i}/{len(stocks)}] {symbol} ({name})... ⏭️ 已完成")
            continue
        
        print(f"[{i}/{len(stocks)}] {symbol} ({name})...", end=" ", flush=True)
        
        df, source = fetch_stock_history(symbol, name)
        
        if df is not None and not df.empty:
            save_to_csv(df, symbol)
            latest_date = df['date'].iloc[-1].strftime("%Y-%m-%d")
            records = len(df)
            print(f"✓ ({source}, {latest_date}, {records}条)")
            
            if records >= 1000:
                print(f"   ✅ 达标: {records}条 ≥ 1000条")
            else:
                print(f"   ⚠️ 仅 {records}条 (目标: 1000条)")
            
            success += 1
            source_counts[source] = source_counts.get(source, 0) + 1
            completed.add(symbol)
        else:
            print("✗")
            failed += 1
        
        time.sleep(0.5)
    
    progress['completed'] = list(completed)
    progress['total_fetched'] = progress.get('total_fetched', 0) + success
    progress['batch_index'] = batch_index
    progress['last_run'] = timestamp
    save_progress(progress)
    
    total_stocks = len(progress.get('all_stocks', TEST_STOCKS))
    completed_count = len(completed)
    progress_pct = (completed_count / total_stocks * 100) if total_stocks > 0 else 0
    
    print(f"\n📊 本批次完成: {success}, 失败: {failed}")
    print(f"📈 总体进度: {completed_count}/{total_stocks} ({progress_pct:.1f}%)")
    
    remaining = total_stocks - completed_count
    batches_left = (remaining + batch_size - 1) // batch_size
    
    print(f"📅 预计还需 {batches_left} 批次完成全部")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "batch_complete",
        "batch_index": batch_index,
        "success": success,
        "failed": failed,
        "sources": source_counts,
        "progress": {
            "completed": completed_count,
            "total": total_stocks,
            "percentage": round(progress_pct, 2)
        },
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")


def check_data_quality():
    """检查数据质量"""
    print("\n📊 数据质量检查:")
    progress = load_progress()
    completed = progress.get('completed', [])
    
    qualified = 0
    for symbol in completed:
        file_path = Path(f"/home/liujerry/金融数据/stocks/{symbol}.csv")
        if file_path.exists():
            df = pd.read_csv(file_path)
            records = len(df)
            if records >= 1000:
                qualified += 1
                print(f"   ✅ {symbol}: {records}条")
            else:
                print(f"   ⚠️ {symbol}: {records}条")
    
    print(f"\n📈 达标股票: {qualified}/{len(completed)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            progress = load_progress()
            print(json.dumps(progress, ensure_ascii=False, indent=2))
            check_data_quality()
        elif sys.argv[1] == "--reset":
            if PROGRESS_FILE.exists():
                PROGRESS_FILE.unlink()
            print("✅ 进度已重置")
        elif sys.argv[1] == "--quality":
            check_data_quality()
        else:
            try:
                batch_index = int(sys.argv[1])
                batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
                batch_fetch_history(batch_index, batch_size)
            except:
                batch_fetch_history()
    else:
        batch_fetch_history()
