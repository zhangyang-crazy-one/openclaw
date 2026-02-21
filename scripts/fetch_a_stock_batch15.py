#!/usr/bin/env python3
"""
A股财务数据采集脚本 - Batch 15 (简化版)
"""

import pandas as pd
import akshare as ak
import time
from datetime import datetime
import os

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"
BATCH_NUM = 15

# 从已采集数据分析，下一批代码从 2311 开始（跳过已采集的）
# 已有: batch1-5 各100只, batch6 397, batch7 93, batch8 8659, batch9 8049, batch10 7554, batch11 100, batch12 100, batch13 5104, batch14 4306
# 约1167只唯一股票

def main():
    print(f"=== A股财务数据采集 - Batch {BATCH_NUM} ===")
    print(f"开始时间: {datetime.now()}")
    
    # 简化处理：直接获取未采集的代码
    # 已采集到约2310附近（根据之前分析），所以从2311开始采集100只
    start_code = 2311
    batch_codes = [f"{i:06d}" for i in range(start_code, start_code + 100)]
    
    print(f"待采集: {len(batch_codes)} 只")
    print(f"代码范围: {batch_codes[0]} - {batch_codes[-1]}")
    
    # 采集数据
    all_data = []
    success_count = 0
    fail_count = 0
    
    print("\n开始采集财务数据...")
    for i, code in enumerate(batch_codes):
        try:
            df = ak.stock_financial_abstract_ths(symbol=code)
            
            if df is not None and not df.empty:
                # 格式化code
                if code.startswith('6'):
                    full_code = f"sh.{code}"
                elif code.startswith('8') or code.startswith('4'):
                    full_code = f"bj.{code}"
                else:
                    full_code = f"sz.{code}"
                
                df['code'] = full_code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success_count += 1
                print(f"[{i+1}/{len(batch_codes)}] ✓ {code}: {len(df)}条")
            else:
                fail_count += 1
                print(f"[{i+1}/{len(batch_codes)}] ✗ {code}: 无数据")
            
            time.sleep(0.3)
            
        except Exception as e:
            fail_count += 1
            print(f"[{i+1}/{len(batch_codes)}] ✗ {code}: {str(e)[:30]}")
            time.sleep(0.5)
    
    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        output_file = f"{OUTPUT_DIR}/a_stock_financial_batch{BATCH_NUM}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n=== 采集完成 ===")
        print(f"成功: {success_count} 只")
        print(f"失败: {fail_count} 只")
        print(f"数据行数: {len(df)}")
        print(f"保存位置: {output_file}")
    else:
        print("\n未获取到任何数据")

if __name__ == "__main__":
    main()
