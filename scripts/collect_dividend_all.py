#!/usr/bin/env python3
"""
全部A股分红数据采集脚本
- 数据源：akshare stock_dividend_cninfo
- 防封策略：每请求间隔3秒
- 断点续传：保存进度，Ctrl+C后可继续
"""

import akshare as ak
import pandas as pd
import csv
import time
import json
import sys
from pathlib import Path
from datetime import datetime

# 配置
PROGRESS_FILE = Path("/home/liujerry/金融数据/fundamentals/chuangye_full/dividend_progress.json")
OUTPUT_FILE = Path("/home/liujerry/金融数据/fundamentals/chuangye_full/dividend_all.csv")
MAIN_DATA = Path("/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv")
DELAY = 3.0  # 每请求间隔秒数

def load_stock_list():
    """从a_stock_codes.csv获取股票列表"""
    codes = set()
    stock_file = Path("/home/liujerry/金融数据/a_stock_codes.csv")
    with open(stock_file, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('code', '')
            if code and len(code) == 6:  # 只取6位完整代码
                codes.add(code)
    return sorted(codes)

def load_progress():
    """加载进度"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_index": 0}

def save_progress(progress):
    """保存进度"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, ensure_ascii=False)

def fetch_dividend(code, retries=2):
    """获取单只股票分红数据"""
    for attempt in range(retries):
        try:
            df = ak.stock_dividend_cninfo(symbol=code)
            if df is not None and len(df) > 0:
                # 添加股票代码列
                df = df.copy()
                df['code'] = code
                return df
            return None
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"  ⚠️ {code} 第{attempt+1}次失败，{wait}秒后重试: {e}")
                time.sleep(wait)
            else:
                return None
    return None

def append_to_csv(df, first_write=False):
    """追加数据到CSV"""
    mode = 'w' if first_write else 'a'
    with open(OUTPUT_FILE, mode, encoding='utf-8-sig', newline='') as f:
        if first_write:
            df.to_csv(f, index=False, header=True)
        else:
            df.to_csv(f, index=False, header=False)

def main():
    print(f"=== A股分红数据采集 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载股票列表
    stocks = load_stock_list()
    print(f"股票总数: {len(stocks)}")
    
    # 加载进度
    progress = load_progress()
    completed = set(progress["completed"])
    failed = set(progress["failed"])
    
    # 过滤已完成
    remaining = [s for s in stocks if s not in completed and s not in failed]
    print(f"待采集: {len(remaining)}")
    print(f"已完成: {len(completed)}")
    print(f"已失败: {len(failed)}")
    print(f"请求间隔: {DELAY}秒")
    print()
    
    if not remaining:
        print("全部股票已采集完成！")
        return
    
    # 检查CSV是否存在
    first_write = not OUTPUT_FILE.exists()
    
    try:
        for i, code in enumerate(remaining, 1):
            start = time.time()
            
            # 采集
            df = fetch_dividend(code)
            
            elapsed = time.time() - start
            if df is not None and len(df) > 0:
                append_to_csv(df, first_write=first_write)
                first_write = False
                completed.add(code)
                print(f"[{i}/{len(remaining)}] ✅ {code}: {len(df)}条 (耗时{elapsed:.1f}秒)")
            else:
                failed.add(code)
                print(f"[{i}/{len(remaining)}] ❌ {code}: 无数据 (耗时{elapsed:.1f}秒)")
            
            # 保存进度
            progress["completed"] = list(completed)
            progress["failed"] = list(failed)
            save_progress(progress)
            
            # 间隔
            if i < len(remaining):
                sleep_time = max(0, DELAY - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print(f"\n\n⏸ 中断已保存进度")
        print(f"已完成: {len(completed)}/{len(stocks)}")
        print(f"重启脚本继续采集")

    # 最终统计
    print(f"\n=== 采集完成 ===")
    print(f"总股票: {len(stocks)}")
    print(f"成功: {len(completed)}")
    print(f"失败: {len(failed)}")
    if failed:
        print(f"失败列表: {list(failed)[:20]}...")

if __name__ == "__main__":
    main()
