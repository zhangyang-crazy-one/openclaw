#!/usr/bin/env python3
"""
A股财务数据增量采集脚本
跳过已采集的股票，继续采集剩余股票
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
            collected.update(df['code'].dropna().unique())
        except Exception as e:
            print(f"读取{f}失败: {e}")
    
    print(f"已采集股票: {len(collected)} 只")
    return collected

def get_stock_list():
    """获取A股股票列表"""
    print("获取A股股票列表...")
    df = ak.stock_info_a_code_name()
    print(f"获取到 {len(df)} 只股票")
    return df['code'].tolist()

def fetch_financial_batch(stock_codes, batch_num):
    """采集财务数据"""
    print(f"\n=== 采集第 {batch_num} 批 (共 {len(stock_codes)} 只) ===")
    
    all_data = []
    success_count = 0
    fail_count = 0
    empty_count = 0
    
    for i, code in enumerate(stock_codes):
        try:
            df = ak.stock_financial_abstract_ths(symbol=code)
            
            if df is not None and not df.empty:
                df = df.head(1).copy()
                df['code'] = code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success_count += 1
            else:
                empty_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(stock_codes)}")
            
            time.sleep(0.3)
            
        except Exception as e:
            fail_count += 1
            if fail_count <= 5:
                print(f"  {code} 失败: {str(e)[:50]}")
    
    print(f"本批完成: 有数据 {success_count}, 无数据 {empty_count}, 错误 {fail_count}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

def main():
    print("=" * 50)
    print("A股财务数据增量采集")
    print("=" * 50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取已采集的股票
    collected = get_collected_codes()
    
    # 获取完整股票列表
    all_stocks = get_stock_list()
    
    # 过滤未采集的股票
    remaining = [s for s in all_stocks if s not in collected]
    print(f"剩余待采集: {len(remaining)} 只")
    
    if not remaining:
        print("所有股票已采集完成!")
        return
    
    # 分批采集，每批100只
    batch_size = 100
    total_batches = (len(remaining) + batch_size - 1) // batch_size
    
    # 找到下一个批次编号
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
    
    total_success = 0
    
    for batch_num in range(next_batch, min(next_batch + 3, total_batches + 1)):  # 每次最多采集3批
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(batch_num * batch_size, len(remaining))
        batch_stocks = remaining[start_idx:end_idx]
        
        print(f"\n{'='*50}")
        print(f"采集第 {batch_num}/{total_batches} 批 (股票 {start_idx+1}-{end_idx})")
        print(f"{'='*50}")
        
        data = fetch_financial_batch(batch_stocks, batch_num)
        
        if data is not None and not data.empty:
            output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
            data.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"已保存到: {output_file}")
            total_success += len(data)
        
        if batch_num < min(next_batch + 3, total_batches):
            print("\n休息3秒...")
            time.sleep(3)
    
    print("\n" + "=" * 50)
    print(f"采集完成!")
    print(f"本轮新增: {total_success} 条")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
