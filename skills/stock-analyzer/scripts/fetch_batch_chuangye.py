#!/usr/bin/env python3
"""
获取创业板股票历史数据
创业板代码: 300xxx
"""
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

END_DATE = datetime(2026, 2, 6)
START_DATE = END_DATE - timedelta(days=1825)

PROGRESS_FILE = Path.home() / ".config" / "deepseeker" / "chuangye_progress.json"


def get_chuangye_stocks_from_baostock():
    """获取创业板股票列表"""
    import baostock as bs
    
    print("📋 获取创业板列表...")
    chuangye_stocks = []
    
    lg = bs.login()
    if lg.error_code != '0':
        print("   ❌ baostock 登录失败")
        return []
    
    rs = bs.query_stock_industry()
    
    while (rs.error_code == '0') and rs.next():
        row = rs.get_row_data()
        code = row[1]  # sh.600000 / sz.300001
        name = row[2]
        
        # 提取纯代码
        pure_code = code.split('.')[-1]
        
        # 筛选创业板: 300xxx
        if pure_code and name and pure_code.startswith('300'):
            chuangye_stocks.append((pure_code, name))
    
    bs.logout()
    
    print(f"   ✅ 共获取 {len(chuangye_stocks)} 只创业板股票")
    return chuangye_stocks


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_stocks": 0,
        "completed": [],
        "failed": [],
        "batch_index": 0,
        "total_fetched": 0,
        "last_run": None,
        "data_range": {
            "start": START_DATE.strftime("%Y-%m-%d"),
            "end": END_DATE.strftime("%Y-%m-%d")
        }
    }


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)


def fetch_history_baostock(symbol, name):
    """获取历史数据"""
    try:
        import baostock as bs
        
        lg = bs.login()
        if lg.error_code != '0':
            return None, None
        
        bs_symbol = f"sz.{symbol}"  # 创业板都是深圳
        
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


def save_to_csv(df, symbol):
    output_dir = Path("/home/liujerry/金融数据/stocks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{symbol}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    return output_file


def batch_fetch(batch_index, batch_size=10):
    """批量获取"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print("📈 获取创业板历史数据")
    print(f"⏰ {timestamp}")
    print(f"📅 范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")
    print(f"📦 批次: {batch_index}, 每批: {batch_size}只")
    print("=" * 80)
    
    progress = load_progress()
    
    if 'chuangye_stocks' not in progress:
        stocks = get_chuangye_stocks_from_baostock()
        if not stocks:
            print("❌ 无法获取创业板列表")
            return
        progress['chuangye_stocks'] = stocks
        progress['total_stocks'] = len(stocks)
        save_progress(progress)
    else:
        stocks = progress['chuangye_stocks']
    
    total_stocks = len(stocks)
    
    completed = set(progress.get('completed', []))
    failed = set(progress.get('failed', []))
    
    start_idx = batch_index * batch_size
    end_idx = min(start_idx + batch_size, total_stocks)
    
    if start_idx >= total_stocks:
        print(f"\n✅ 创业板批次已完成！")
        print(f"📊 总进度: {len(completed)}/{total_stocks}")
        return
    
    batch_stocks = stocks[start_idx:end_idx]
    
    print(f"\n📊 进度: {start_idx}/{total_stocks} ({start_idx/total_stocks*100:.1f}%)")
    print(f"   本批次: {start_idx}~{end_idx}")
    
    success = failed_count = 0
    qualified = 0
    
    for i, (symbol, name) in enumerate(batch_stocks, 1):
        current = start_idx + i
        
        if symbol in completed:
            print(f"[{current}/{total_stocks}] {symbol} ({name})... ⏭️ 已完成")
            continue
        
        print(f"[{current}/{total_stocks}] {symbol} ({name})...", end=" ", flush=True)
        
        df, source = fetch_history_baostock(symbol, name)
        
        if df is not None and not df.empty:
            save_to_csv(df, symbol)
            records = len(df)
            latest = df['date'].iloc[-1].strftime("%Y-%m-%d")
            
            if records >= 1000:
                print(f"✓ ({source}, {latest}, {records}条) ✅")
                qualified += 1
            else:
                print(f"✓ ({source}, {latest}, {records}条) ⚠️")
            
            success += 1
            completed.add(symbol)
            if symbol in failed:
                failed.discard(symbol)
        else:
            print("✗")
            failed_count += 1
            failed.add(symbol)
        
        time.sleep(0.2)
    
    progress['completed'] = list(completed)
    progress['failed'] = list(failed)
    progress['batch_index'] = batch_index
    progress['total_fetched'] = len(completed)
    progress['last_run'] = timestamp
    save_progress(progress)
    
    pct = len(completed) / total_stocks * 100 if total_stocks > 0 else 0
    
    print(f"\n" + "=" * 80)
    print(f"📊 批次完成: {success}, 失败: {failed_count}")
    print(f"📈 达标股票: {qualified}/{success}")
    print(f"📊 总体进度: {len(completed)}/{total_stocks} ({pct:.2f}%)")
    print("=" * 80)
    
    remaining = total_stocks - len(completed)
    batches_left = (remaining + batch_size - 1) // batch_size
    print(f"📅 预计还需 {batches_left} 批次完成全部")
    
    print("\n---OUTPUT_START---")
    result = {
        "status": "batch_complete",
        "batch_index": batch_index,
        "success": success,
        "failed": failed_count,
        "qualified": qualified,
        "total_completed": len(completed),
        "total_stocks": total_stocks,
        "progress_pct": round(pct, 2),
        "batches_left": batches_left,
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")


def show_summary():
    progress = load_progress()
    
    print("\n" + "=" * 80)
    print("📊 创业板历史数据获取进度")
    print("=" * 80)
    
    total = progress.get('total_stocks', 0)
    completed = len(progress.get('completed', []))
    batch_idx = progress.get('batch_index', 0)
    last_run = progress.get('last_run', '未知')
    
    pct = completed / total * 100 if total > 0 else 0
    
    print(f"\n📅 数据范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")
    print(f"📦 当前批次: {batch_idx}")
    print(f"⏰ 最后运行: {last_run}")
    print(f"\n📊 完成: {completed}/{total} ({pct:.2f}%)")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            show_summary()
        elif sys.argv[1] == "--reset":
            if PROGRESS_FILE.exists():
                PROGRESS_FILE.unlink()
            print("✅ 进度已重置")
        elif sys.argv[1] == "--full":
            stocks = get_chuangye_stocks_from_baostock()
            if stocks:
                total = len(stocks)
                batch_size = 10
                for i in range((total + batch_size - 1) // batch_size):
                    if i > 0:
                        time.sleep(3)
                    batch_fetch(i, batch_size)
        else:
            try:
                batch_index = int(sys.argv[1])
                batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
                batch_fetch(batch_index, batch_size)
            except:
                batch_fetch(0, 10)
    else:
        show_summary()
