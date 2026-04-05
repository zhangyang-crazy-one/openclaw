#!/usr/bin/env python3
"""
批量补全 EastMoney 现金流量表
使用akshare stock_cash_flow_sheet_by_report_em
"""
import akshare as ak
import pandas as pd
import time
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
OUTPUT_FILE = DATA_DIR / "cashflow_em.csv"

def normalize_code(code):
    """统一格式: sz.300023 -> SZ300023"""
    code = str(code).upper()
    if '.' in code:
        parts = code.split('.')
        if len(parts) == 2:
            prefix = "SH" if parts[0] in ('sh', 'SH', '600', '601', '603', '688') else "SZ"
            return f"{prefix}{parts[1]}"
    return code

def get_all_stocks():
    """从profit.csv获取全部股票列表"""
    profit_file = DATA_DIR / "profit.csv"
    df = pd.read_csv(profit_file, low_memory=False)
    codes = set()
    for code in df['code'].dropna().unique():
        normalized = normalize_code(code)
        if normalized:
            codes.add(normalized)
    return codes

def get_existing_stocks():
    """获取已存在的股票"""
    if not OUTPUT_FILE.exists():
        return set()
    df = pd.read_csv(OUTPUT_FILE, low_memory=False)
    if 'SECUCODE' not in df.columns:
        return set()
    stocks = set()
    for secucode in df['SECUCODE'].dropna().unique():
        code = secucode.replace('.SH', '').replace('.SZ', '')
        prefix = "SH" if secucode.endswith('.SH') else "SZ"
        stocks.add(f"{prefix}{code}")
    return stocks

def fetch_cashflow(symbol):
    """获取现金流量表"""
    try:
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        if df is not None and len(df) > 0:
            return df
    except:
        pass
    return None

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 现金流量表批量采集开始...")
    
    all_stocks = get_all_stocks()
    existing_stocks = get_existing_stocks()
    missing_stocks = [s for s in sorted(all_stocks) if s not in existing_stocks]
    
    print(f"全部股票: {len(all_stocks)}")
    print(f"已存在: {len(existing_stocks)}")
    print(f"缺口: {len(missing_stocks)}")
    
    if not missing_stocks:
        print("没有缺失股票!")
        return
    
    # 分批采集
    all_data = []
    total = len(missing_stocks)
    success_count = 0
    fail_count = 0
    start_time = time.time()
    
    for i, symbol in enumerate(missing_stocks):
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = (i / elapsed) if elapsed > 0 else 1
            remaining = (total - i) / rate if rate > 0 else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 进度: {i}/{total} ({i/total*100:.1f}%) - 成功:{success_count} 失败:{fail_count} - 预计剩余: {remaining/60:.1f}分钟")
        
        df = fetch_cashflow(symbol)
        if df is not None and len(df) > 0:
            all_data.append(df)
            success_count += 1
        else:
            fail_count += 1
        
        # 每100个保存一次
        if (i + 1) % 100 == 0 and all_data:
            df_combined = pd.concat(all_data, ignore_index=True)
            df_combined.to_csv(OUTPUT_FILE, index=False)
            all_data = []
        
        time.sleep(0.2)
    
    # 保存剩余
    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        if OUTPUT_FILE.exists():
            df_existing = pd.read_csv(OUTPUT_FILE, low_memory=False)
            df_combined = pd.concat([df_existing, df_combined], ignore_index=True)
        df_combined.to_csv(OUTPUT_FILE, index=False)
    
    # 最终统计
    df_final = pd.read_csv(OUTPUT_FILE, low_memory=False)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 完成!")
    print(f"总股票: {df_final['SECUCODE'].nunique() if 'SECUCODE' in df_final.columns else 'N/A'}")
    print(f"总行数: {len(df_final)}")
    print(f"本次成功: {success_count}")
    print(f"本次失败: {fail_count}")

if __name__ == '__main__':
    main()