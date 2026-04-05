#!/usr/bin/env python3
"""
A股现金流量表补全脚本
使用 Sina API 获取现金流量表数据

用法:
  python fetch_cashflow.py [并发数] [批次大小]
  python fetch_cashflow.py 8      # 8并发，无限批次
  python fetch_cashflow.py 8 1000 # 8并发，每次最多1000只

进度文件: cashflow_progress.json（自动记录已完成的股票）
"""
import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import random
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
CASHFLOW_FILE = FINANCIAL_DIR / "cashflow.csv"
PROGRESS_FILE = FINANCIAL_DIR / "cashflow_progress.json"
STOCK_LIST_FILE = Path("/home/liujerry/金融数据/fundamentals/chuangye_stock_list.csv")


def get_all_a_codes() -> list:
    stocks_dir = Path("/home/liujerry/金融数据/stocks")
    codes = []
    for f in stocks_dir.glob("*.csv"):
        code = f.stem
        if code.isdigit() and len(code) == 6:
            codes.append(code)
    if not codes and STOCK_LIST_FILE.exists():
        try:
            df = pd.read_csv(STOCK_LIST_FILE)
            codes = df['code'].astype(str).str.zfill(6).tolist()
        except:
            pass
    return sorted(set(codes))


def code_to_sina(code: str) -> str:
    code = code.zfill(6)
    return f"sh{code}" if code.startswith('6') else f"sz{code}"


def fetch_cashflow_sheet(symbol: str) -> pd.DataFrame | None:
    try:
        df = ak.stock_financial_report_sina(stock=symbol, symbol='现金流量表')
        if df is not None and not df.empty:
            raw_code = symbol.replace('sh', '').replace('sz', '')
            df['code'] = raw_code
            if '报告日' in df.columns:
                df = df.rename(columns={'报告日': 'report_date'})
            return df
    except:
        pass
    return None


def fetch_with_retry(symbol: str, max_retries: int = 2) -> pd.DataFrame | None:
    for attempt in range(max_retries):
        result = fetch_cashflow_sheet(symbol)
        if result is not None:
            return result
        if attempt < max_retries - 1:
            time.sleep(random.uniform(1, 2))
    return None


def worker(args):
    symbol, code = args
    return code, fetch_with_retry(symbol)


def update_cashflow(concurrency: int = 8, batch_size: int = None):
    print("=" * 60)
    print("📋 A股现金流量表补全")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    progress = {}
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE) as f:
                progress = json.load(f)
            print(f"已有进度记录: {len(progress)} 只股票")
        except:
            progress = {}
    
    all_codes = get_all_a_codes()
    print(f"A股总数: {len(all_codes)}")
    
    to_fetch = [c for c in all_codes if c not in progress]
    print(f"待获取: {len(to_fetch)} 只")
    
    if not to_fetch:
        print("✅ 全部完成!")
        return
    
    if batch_size:
        to_fetch = to_fetch[:batch_size]
        print(f"本次批次: {len(to_fetch)} 只")
    
    tasks = [(code_to_sina(c), c) for c in to_fetch]
    
    success = 0
    failed = 0
    all_results = []
    
    print(f"\n开始获取 (并发数: {concurrency})...")
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(worker, t): t for t in tasks}
        
        for future in as_completed(futures):
            code, result = future.result()
            
            if result is not None:
                all_results.append(result)
                progress[code] = datetime.now().isoformat()
                success += 1
            else:
                failed += 1
            
            total = success + failed
            if total % 100 == 0 or total == len(tasks):
                print(f"[{total}/{len(tasks)}] (成功:{success} 失败:{failed})")
            
            time.sleep(random.uniform(0.1, 0.3))
    
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)
    
    if all_results:
        print(f"\n合并 {len(all_results)} 个数据块...")
        new_data = pd.concat(all_results, ignore_index=True)
        
        cols = ['code', 'report_date'] + [c for c in new_data.columns if c not in ['code', 'report_date']]
        new_data = new_data[cols]
        
        if CASHFLOW_FILE.exists():
            try:
                existing = pd.read_csv(CASHFLOW_FILE)
                combined = pd.concat([existing, new_data], ignore_index=True)
                combined = combined.drop_duplicates(subset=['code', 'report_date'], keep='last')
                print(f"合并后总记录: {len(combined)}")
            except:
                combined = new_data
        else:
            combined = new_data
        
        combined.to_csv(CASHFLOW_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ 已保存: {CASHFLOW_FILE}")
        print(f"   总记录: {len(combined)}")
        print(f"   唯一股票: {combined['code'].nunique()}")
    
    print("\n" + "=" * 60)
    print(f"📊 本次: 成功 {success}, 失败 {failed}")
    print(f"📊 累计: {len(progress)} 只股票已完成")
    print("=" * 60)
    
    return {'success': success, 'failed': failed}


if __name__ == "__main__":
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    update_cashflow(concurrency=concurrency, batch_size=batch_size)
