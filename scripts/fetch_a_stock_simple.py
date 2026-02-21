#!/usr/bin/env python3
"""
A股财务数据增量采集 - 简化版
"""

import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"

def get_collected_codes():
    """获取已采集的股票代码"""
    collected = set()
    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('a_stock_financial_batch') and f.endswith('.csv')]
    
    for f in files:
        try:
            df = pd.read_csv(os.path.join(OUTPUT_DIR, f), usecols=['code'])
            collected.update(df['code'].dropna().astype(str).unique())
        except Exception as e:
            print(f"读取{f}失败: {e}")
    
    print(f"已采集股票: {len(collected)} 只")
    return collected

def main():
    print("=" * 50)
    print("A股财务数据增量采集 (简化版)")
    print("=" * 50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取已采集的股票
    collected = get_collected_codes()
    
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
    print(f"将从第 {next_batch} 批开始采集")
    
    # 直接从东方财富获取股票列表
    print("\n获取股票列表...")
    stock_df = ak.stock_info_a_code_name()
    all_stocks = stock_df['code'].tolist()
    print(f"A股总数: {len(all_stocks)}")
    
    # 过滤未采集的
    remaining = [s for s in all_stocks if str(s) not in collected]
    print(f"剩余待采集: {len(remaining)}")
    
    if not remaining:
        print("全部采集完成!")
        return
    
    # 采集3批，每批100只
    batch_size = 100
    total_success = 0
    
    for batch_num in range(next_batch, min(next_batch + 3, (len(remaining) // batch_size) + 2)):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(remaining))
        
        if start_idx >= len(remaining):
            break
            
        batch_stocks = remaining[start_idx:end_idx]
        print(f"\n=== 采集第 {batch_num} 批 ({start_idx+1}-{end_idx}) ===")
        
        all_data = []
        success = 0
        fail = 0
        
        for i, code in enumerate(batch_stocks):
            try:
                df = ak.stock_financial_abstract_ths(symbol=code)
                if df is not None and not df.empty:
                    df = df.head(1).copy()
                    df['code'] = code
                    df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    all_data.append(df)
                    success += 1
                if (i + 1) % 20 == 0:
                    print(f"  进度: {i+1}/{len(batch_stocks)}")
                time.sleep(0.3)
            except Exception as e:
                fail += 1
                if fail <= 3:
                    print(f"  {code} 失败")
        
        print(f"  本批完成: 成功 {success}, 失败 {fail}")
        
        if all_data:
            data = pd.concat(all_data, ignore_index=True)
            output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
            data.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"  已保存: {output_file}")
            total_success += len(data)
        
        if batch_num < next_batch + 2:
            time.sleep(3)
    
    # 最终统计
    final_collected = get_collected_codes()
    
    print("\n" + "=" * 50)
    print(f"采集完成!")
    print(f"本轮新增: {total_success} 条")
    print(f"累计总数: {len(final_collected)} 只")
    print("=" * 50)

if __name__ == "__main__":
    main()
