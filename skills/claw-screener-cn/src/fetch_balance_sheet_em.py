#!/usr/bin/env python3
"""
A股财务数据补全脚本 - EastMoney版
使用 EastMoney API 获取三大报表核心指标

覆盖: 资产负债表 + 现金流量表 + 利润表 的核心指标
字段: EPS, 每股净资产, 毛利率, ROE, 资产负债率, 现金流比率 等 160+ 字段

用法:
  python fetch_balance_sheet_em.py [并发数] [批次大小]
"""
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import random
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
OUTPUT_FILE = FINANCIAL_DIR / "financial_main_em.csv"
PROGRESS_FILE = FINANCIAL_DIR / "financial_main_progress.json"
STOCK_LIST_FILE = Path("/home/liujerry/金融数据/fundamentals/chuangye_stock_list.csv")

API_BASE = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
API_REPORT = "RPT_F10_FINANCE_MAINFINADATA"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://emweb.securities.eastmoney.com/",
    "Accept": "application/json",
}


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


def code_to_em(code: str) -> str:
    """6位码转EastMoney格式"""
    code = code.zfill(6)
    return f"{code}.SH" if code.startswith('6') else f"{code}.SZ"


def fetch_financial_em(symbol: str, max_retries: int = 2) -> pd.DataFrame | None:
    """获取EastMoney主要财务指标"""
    em_code = code_to_em(symbol)
    
    for attempt in range(max_retries):
        try:
            params = {
                "reportName": API_REPORT,
                "columns": "ALL",
                "filter": f'(SECUCODE="{em_code}")',
                "pageNumber": "1",
                "pageSize": "200",
                "sortTypes": "-1",
                "sortColumns": "REPORT_DATE",
                "source": "HSF10",
                "client": "PC",
            }
            r = requests.get(
                API_BASE, params=params, headers=HEADERS, timeout=15
            )
            data = r.json()
            
            if data.get("success") and data.get("result") and data["result"].get("data"):
                df = pd.DataFrame(data["result"]["data"])
                df["code"] = symbol
                return df
            else:
                # API正常返回但无数据（非错误）
                if data.get("message") in ("返回数据为空", "报表配置不存在"):
                    return None
        except Exception as e:
            pass
        
        if attempt < max_retries - 1:
            time.sleep(random.uniform(1, 2))
    
    return None


def worker(args):
    symbol, = args
    return symbol, fetch_financial_em(symbol)


def update_financial_em(concurrency: int = 8, batch_size: int = None):
    print("=" * 60)
    print("📋 A股财务数据补全 (EastMoney版)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 读取进度
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
    
    tasks = [(c,) for c in to_fetch]
    
    success = 0
    failed = 0
    all_results = []
    
    print(f"\n开始获取 (并发数: {concurrency})...")
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(worker, t): t for t in tasks}
        
        for future in as_completed(futures):
            symbol, result = future.result()
            
            if result is not None and not result.empty:
                all_results.append(result)
                progress[symbol] = datetime.now().isoformat()
                success += 1
            else:
                failed += 1
            
            total = success + failed
            if total % 100 == 0 or total == len(tasks):
                print(f"[{total}/{len(tasks)}] (成功:{success} 失败:{failed})")
            
            time.sleep(random.uniform(0.05, 0.15))  # EastMoney限制比Sina宽
    
    # 保存进度
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)
    
    # 合并并保存
    if all_results:
        print(f"\n合并 {len(all_results)} 个数据块...")
        new_data = pd.concat(all_results, ignore_index=True)
        
        # 调整列顺序
        priority_cols = ['code', 'REPORT_DATE', 'SECUCODE', 'SECURITY_CODE', 
                         'SECURITY_NAME_ABBR', 'REPORT_DATE_NAME']
        other_cols = [c for c in new_data.columns if c not in priority_cols]
        new_data = new_data[priority_cols + other_cols]
        
        # 追加到现有文件
        if OUTPUT_FILE.exists():
            try:
                existing = pd.read_csv(OUTPUT_FILE)
                combined = pd.concat([existing, new_data], ignore_index=True)
                combined = combined.drop_duplicates(
                    subset=['code', 'REPORT_DATE'], keep='last'
                )
                print(f"合并后总记录: {len(combined)}")
            except:
                combined = new_data
        else:
            combined = new_data
        
        combined.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"✅ 已保存: {OUTPUT_FILE}")
        print(f"   总记录: {len(combined)}")
        print(f"   唯一股票: {combined['code'].nunique()}")
    else:
        print("没有获取到数据")
    
    print("\n" + "=" * 60)
    print(f"📊 本次: 成功 {success}, 失败 {failed}")
    print(f"📊 累计: {len(progress)} 只股票已完成")
    print("=" * 60)
    
    return {'success': success, 'failed': failed}


if __name__ == "__main__":
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    update_financial_em(concurrency=concurrency, batch_size=batch_size)
