#!/usr/bin/env python3
"""
A股财务数据采集 - 简化版 v2
"""
import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"

def main():
    print("="*60)
    print("A股财务数据采集 - 简化版 v2")
    print("="*60)
    
    # 获取A股股票列表
    print("\n[1] 获取A股股票列表...")
    stock_info = ak.stock_info_a_code_name()
    all_stocks = stock_info['code'].tolist()
    print(f"A股总数: {len(all_stocks)}")
    
    # 读取已采集的股票 - 简化版
    print("\n[2] 检查已采集数据...")
    collected = set()
    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("a_stock_financial_batch") and f.endswith(".csv")]
    
    for f in files:
        try:
            # 只读取第一列和code列
            df = pd.read_csv(os.path.join(OUTPUT_DIR, f), encoding='utf-8-sig', usecols=[0])
            # 尝试找code列
            for col in df.columns:
                if 'code' in col.lower():
                    codes = df[col].dropna().astype(str).str.strip()
                    # 只保留6位数字代码
                    valid_codes = codes[codes.str.match(r'^\d{6}$', na=False)]
                    collected.update(valid_codes.tolist())
                    break
        except Exception as e:
            print(f"  读取 {f} 失败: {e}")
    
    print(f"已采集股票数: {len(collected)}")
    
    # 计算待采集股票
    to_collect = [s for s in all_stocks if s not in collected]
    print(f"待采集股票数: {len(to_collect)}")
    
    if not to_collect:
        print("\n✓ 所有股票已采集完成!")
        return
    
    # 找到下一个批次号
    batch_num = 1
    existing = []
    for f in files:
        try:
            num = int(f.replace("a_stock_financial_batch", "").replace(".csv", ""))
            existing.append(num)
        except:
            pass
    if existing:
        batch_num = max(existing) + 1
    
    print(f"\n[3] 采集批次 {batch_num} (100只股票)...")
    
    # 采集100只股票
    batch_codes = to_collect[:100]
    all_data = []
    success_count = 0
    fail_count = 0
    
    for i, code in enumerate(batch_codes):
        try:
            print(f"  [{i+1}/100] {code}...", end=" ", flush=True)
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df is not None and len(df) > 0:
                df['code'] = code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success_count += 1
                print(f"OK ({len(df)}条)")
            else:
                fail_count += 1
                print("无数据")
            time.sleep(0.3)
        except Exception as e:
            fail_count += 1
            err_msg = str(e)[:40]
            print(f"失败: {err_msg}")
            continue
    
    # 保存结果
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        unique_codes = result['code'].nunique() if 'code' in result.columns else 0
        print(f"\n✓ 批次{batch_num}完成: {len(result)}条记录, {unique_codes}只股票")
        print(f"  保存到: {output_file}")
    else:
        print("\n本批次无数据")
    
    # 汇总
    total_now = len(collected) + success_count
    print(f"\n总计: 已采集 {total_now} 只股票 (成功{success_count}, 失败{fail_count})")

if __name__ == "__main__":
    main()
