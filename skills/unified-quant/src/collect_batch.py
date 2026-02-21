#!/usr/bin/env python3
"""
A股财务数据采集脚本 - 改进版
"""
import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"
BATCH_SIZE = 100

def main():
    print("="*60)
    print("A股财务数据采集")
    print("="*60)
    
    # 获取股票列表
    print("\n[1] 获取股票列表...")
    stock_info_a_code_name = ak.stock_info_a_code_name()
    all_codes = stock_info_a_code_name['code'].tolist()
    total = len(all_codes)
    print(f"A股总数: {total}")
    
    # 统计已有批次
    existing = []
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("a_stock_financial_batch") and f.endswith(".csv"):
            batch_num = int(f.replace("a_stock_financial_batch", "").replace(".csv", ""))
            existing.append(batch_num)
    
    if existing:
        max_batch = max(existing)
        start_idx = max_batch * BATCH_SIZE
        print(f"已有批次: {max_batch}, 从索引 {start_idx} 开始")
    else:
        start_idx = 0
        print("从头开始采集")
    
    # 采集下一批
    if start_idx >= total:
        print("全部采集完成!")
        return
    
    end_idx = min(start_idx + BATCH_SIZE, total)
    batch_codes = all_codes[start_idx:end_idx]
    batch_num = max_batch + 1 if existing else 1
    
    print(f"\n[2] 批次{batch_num}: 采集 {len(batch_codes)} 只 ({start_idx+1}-{end_idx})")
    
    all_data = []
    success = 0
    fail = 0
    
    for i, code in enumerate(batch_codes):
        try:
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df is not None and len(df) > 0:
                df['code'] = code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
        
        if (i + 1) % 20 == 0:
            print(f"  进度: {i+1}/{len(batch_codes)}")
        
        time.sleep(0.2)  # 避免请求过快
    
    # 保存
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n[3] 完成!")
        print(f"成功: {success}, 失败: {fail}")
        print(f"记录数: {len(result)}")
        print(f"保存到: {output_file}")
    else:
        print("\n无数据!")

if __name__ == "__main__":
    main()
