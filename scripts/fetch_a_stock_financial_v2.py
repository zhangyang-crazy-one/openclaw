#!/usr/bin/env python3
"""
A股财务数据采集脚本 v2
使用akshare的stock_financial_abstract_ths接口
"""

import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"

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
            # 使用杜邦分析数据
            df = ak.stock_financial_abstract_ths(symbol=code)
            
            if df is not None and not df.empty:
                # 只取最新一期数据
                df = df.head(1).copy()
                df['code'] = code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success_count += 1
            else:
                empty_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(stock_codes)}")
            
            time.sleep(0.3)  # 避免请求过快
            
        except Exception as e:
            fail_count += 1
            if fail_count <= 5:  # 只打印前5个错误
                print(f"  {code} 失败: {str(e)[:40]}")
    
    print(f"本批完成: 有数据 {success_count}, 无数据 {empty_count}, 错误 {fail_count}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

def main():
    print("=" * 50)
    print("A股财务数据采集开始")
    print("=" * 50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取股票列表
    all_stocks = get_stock_list()
    
    # 分批采集，每批100只
    batch_size = 100
    total_batches = (len(all_stocks) + batch_size - 1) // batch_size
    
    # 从第1批开始
    start_batch = 1
    
    total_success = 0
    total_empty = 0
    total_fail = 0
    
    # 只采集前5批（500只）作为测试
    max_batches = 5
    
    for batch_num in range(start_batch, min(start_batch + max_batches, total_batches + 1)):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(batch_num * batch_size, len(all_stocks))
        batch_stocks = all_stocks[start_idx:end_idx]
        
        print(f"\n{'='*50}")
        print(f"采集第 {batch_num}/{total_batches} 批 (股票 {start_idx+1}-{end_idx})")
        print(f"{'='*50}")
        
        data = fetch_financial_batch(batch_stocks, batch_num)
        
        if data is not None and not data.empty:
            # 保存到文件
            output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
            data.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"已保存到: {output_file}")
            print(f"数据列: {data.columns.tolist()[:5]}...")
            total_success += len(data)
        
        # 批次间休息
        if batch_num < min(start_batch + max_batches, total_batches):
            print("\n休息3秒...")
            time.sleep(3)
    
    print("\n" + "=" * 50)
    print(f"采集完成!")
    print(f"总计: 有数据 {total_success} 只")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
