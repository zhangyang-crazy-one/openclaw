#!/usr/bin/env python3
"""
A股财务数据采集脚本 - 批量版
每次采集100只股票财务数据
"""
import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"

def get_stock_list():
    """获取A股股票列表"""
    stock_info_a_code_name = ak.stock_info_a_code_name()
    return stock_info_a_code_name

def fetch_financial_data(stock_codes, batch_num):
    """采集指定股票的财务数据"""
    all_data = []
    
    for i, code in enumerate(stock_codes):
        try:
            # 获取财务指标
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df is not None and len(df) > 0:
                df['code'] = code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
            time.sleep(0.3)  # 避免请求过快
        except Exception as e:
            print(f"  股票 {code} 采集失败: {e}")
            continue
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"批次{batch_num}完成: {len(result)}条记录 -> {output_file}")
        return len(result)
    return 0

def main():
    print("="*60)
    print("A股财务数据采集 - 批次版")
    print("="*60)
    
    # 获取股票列表
    print("\n[1/3] 获取A股股票列表...")
    stocks = get_stock_list()
    total_stocks = len(stocks)
    print(f"A股总数: {total_stocks}")
    
    # 检查已采集的批次
    existing_batches = []
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("a_stock_financial_batch") and f.endswith(".csv"):
            batch_num = int(f.replace("a_stock_financial_batch", "").replace(".csv", ""))
            existing_batches.append(batch_num)
    
    if existing_batches:
        max_batch = max(existing_batches)
        print(f"已采集到批次{max_batch}, 共{max_batch*100}只股票")
        start_batch = max_batch + 1
    else:
        print("未发现已采集数据，从批次1开始")
        start_batch = 1
    
    # 计算剩余需要采集的数量
    stocks_per_batch = 100
    processed_count = (start_batch - 1) * stocks_per_batch
    remaining_stocks = total_stocks - processed_count
    
    if remaining_stocks <= 0:
        print("所有股票已采集完成!")
        return
    
    print(f"\n[2/3] 开始采集剩余 {remaining_stocks} 只股票...")
    print(f"将从批次 {start_batch} 开始，每次采集 {stocks_per_batch} 只\n")
    
    batch_num = start_batch
    stocks_list = stocks['code'].tolist()
    
    while processed_count < total_stocks and batch_num <= start_batch + 4:  # 每次运行最多采集5批
        end_idx = min(processed_count + stocks_per_batch, total_stocks)
        batch_codes = stocks_list[processed_count:end_idx]
        
        print(f"批次{batch_num}: 采集 {len(batch_codes)} 只股票 ({processed_count+1}-{end_idx})...")
        
        count = fetch_financial_data(batch_codes, batch_num)
        
        processed_count += len(batch_codes)
        batch_num += 1
        time.sleep(2)  # 批次间暂停
    
    print(f"\n[3/3] 采集完成!")
    print(f"本次采集后总计: {processed_count}/{total_stocks} 只股票")
    
    # 统计
    total_files = len([f for f in os.listdir(OUTPUT_DIR) if f.startswith("a_stock_financial_batch")])
    print(f"批次文件总数: {total_files}")

if __name__ == "__main__":
    main()
