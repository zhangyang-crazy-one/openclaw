#!/usr/bin/env python3
"""
A股财务数据采集 - 每次100只
"""

import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"

def main():
    print("=" * 50)
    print("A股财务数据采集 (每次100只)")
    print("=" * 50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取当前批次编号
    existing_batches = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith('a_stock_financial_batch') and f.endswith('.csv'):
            try:
                num = int(f.replace('a_stock_financial_batch', '').replace('.csv', ''))
                existing_batches.add(num)
            except:
                pass
    
    next_batch = max(existing_batches, default=0) + 1
    print(f"将从第 {next_batch} 批开始")
    
    # 获取股票列表
    print("\n获取股票列表...")
    stock_df = ak.stock_info_a_code_name()
    all_stocks = stock_df['code'].tolist()
    total_stocks = len(all_stocks)
    print(f"A股总数: {total_stocks}")
    
    # 采集1批100只
    batch_size = 100
    start_idx = (next_batch - 1) * batch_size
    
    if start_idx >= total_stocks:
        print(f"索引 {start_idx} 超出范围，采集完成!")
        return
    
    end_idx = min(start_idx + batch_size, total_stocks)
    batch_stocks = all_stocks[start_idx:end_idx]
    
    print(f"\n=== 采集第 {next_batch} 批 ({start_idx+1}-{end_idx}) ===")
    
    all_data = []
    success = 0
    fail = 0
    empty = 0
    
    for i, code in enumerate(batch_stocks):
        try:
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df is not None and not df.empty:
                df = df.head(1).copy()
                df['code'] = code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success += 1
            else:
                empty += 1
            if (i + 1) % 20 == 0:
                print(f"  进度: {i+1}/{len(batch_stocks)}")
            time.sleep(0.3)
        except Exception as e:
            fail += 1
            if fail <= 5:
                print(f"  {code} 失败: {str(e)[:40]}")
    
    print(f"\n本批完成: 成功 {success}, 无数据 {empty}, 错误 {fail}")
    
    if all_data:
        data = pd.concat(all_data, ignore_index=True)
        output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{next_batch}.csv")
        data.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"已保存: {output_file}")
    
    # 统计
    total = 0
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith('a_stock_financial_batch') and f.endswith('.csv'):
            try:
                df = pd.read_csv(os.path.join(OUTPUT_DIR, f), usecols=['code'])
                total += len(df['code'].dropna().unique())
            except:
                pass
    
    print(f"\n总唯一股票: {total} 只")
    print("=" * 50)

if __name__ == "__main__":
    main()
