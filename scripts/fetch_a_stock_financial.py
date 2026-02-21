#!/usr/bin/env python3
"""
A股财务数据采集脚本
使用akshare每次采集100只股票
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
    
    # 获取沪深京A股股票列表
    try:
        # 沪深A股
        df_sh = ak.stock_info_a_code_name()
        print(f"获取到 {len(df_sh)} 只股票")
        
        # 标记市场
        df_sh['market'] = df_sh['code'].apply(
            lambda x: 'sh' if x.startswith('6') else ('bj' if x.startswith('8') or x.startswith('4') else 'sz')
        )
        
        return df_sh
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None

def fetch_financial_data(stock_codes, batch_num):
    """采集财务数据"""
    print(f"\n=== 采集第 {batch_num} 批 (共 {len(stock_codes)} 只) ===")
    
    all_data = []
    success_count = 0
    fail_count = 0
    
    for i, code in enumerate(stock_codes):
        try:
            # 判断市场
            if code.startswith('6'):
                full_code = f"sh{code}"
            elif code.startswith('8') or code.startswith('4'):
                full_code = f"bj{code}"
            else:
                full_code = f"sz{code}"
            
            # 使用杜邦分析数据
            df = ak.stock_financial_abstract_ths(symbol=code)
            
            if df is not None and not df.empty:
                df['code'] = full_code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success_count += 1
                print(f"  [{i+1}/{len(stock_codes)}] {code} OK")
            else:
                fail_count += 1
                print(f"  [{i+1}/{len(stock_codes)}] {code} 无数据")
            
            # 避免请求过快
            time.sleep(0.5)
            
        except Exception as e:
            fail_count += 1
            print(f"  [{i+1}/{len(stock_codes)}] {code} 失败: {str(e)[:50]}")
            time.sleep(0.3)
    
    print(f"\n本批完成: 成功 {success_count}, 失败 {fail_count}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

def fetch_profit_data(stock_codes, batch_num):
    """采集利润表数据"""
    print(f"\n=== 采集第 {batch_num} 批利润表 (共 {len(stock_codes)} 只) ===")
    
    all_data = []
    success_count = 0
    fail_count = 0
    
    for i, code in enumerate(stock_codes):
        try:
            # 判断市场
            if code.startswith('6'):
                full_code = f"sh{code}"
            elif code.startswith('8') or code.startswith('4'):
                full_code = f"bj{code}"
            else:
                full_code = f"sz{code}"
            
            # 使用利润表数据
            df = ak.stock_financial_analysis_indicator(symbol=code)
            
            if df is not None and not df.empty:
                df['code'] = full_code
                df['fetch_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_data.append(df)
                success_count += 1
                print(f"  [{i+1}/{len(stock_codes)}] {code} OK")
            else:
                fail_count += 1
                print(f"  [{i+1}/{len(stock_codes)}] {code} 无数据")
            
            time.sleep(0.5)
            
        except Exception as e:
            fail_count += 1
            print(f"  [{i+1}/{len(stock_codes)}] {code} 失败: {str(e)[:50]}")
            time.sleep(0.3)
    
    print(f"\n本批完成: 成功 {success_count}, 失败 {fail_count}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

def main():
    print("=" * 50)
    print("A股财务数据采集开始")
    print("=" * 50)
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取股票列表
    stock_df = get_stock_list()
    if stock_df is None:
        print("无法获取股票列表，退出")
        return
    
    all_stocks = stock_df['code'].tolist()
    print(f"总共 {len(all_stocks)} 只股票")
    
    # 分批采集，每批100只
    batch_size = 100
    total_batches = (len(all_stocks) + batch_size - 1) // batch_size
    
    # 从第1批开始
    start_batch = 1
    
    all_financial_data = []
    total_success = 0
    total_fail = 0
    
    for batch_num in range(start_batch, total_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(batch_num * batch_size, len(all_stocks))
        batch_stocks = all_stocks[start_idx:end_idx]
        
        print(f"\n{'='*50}")
        print(f"采集第 {batch_num}/{total_batches} 批")
        print(f"{'='*50}")
        
        # 采集财务摘要
        data = fetch_profit_data(batch_stocks, batch_num)
        
        if data is not None and not data.empty:
            all_financial_data.append(data)
            total_success += len(batch_stocks) - (data.groupby('code').ngroups if 'code' in data.columns else 0)
        
        # 每批完成后保存
        if all_financial_data:
            combined = pd.concat(all_financial_data, ignore_index=True)
            output_file = os.path.join(OUTPUT_DIR, f"a_stock_profit_batch{batch_num}.csv")
            combined.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n已保存到: {output_file}")
        
        # 批次间休息
        if batch_num < total_batches:
            print("\n休息5秒...")
            time.sleep(5)
    
    print("\n" + "=" * 50)
    print("采集完成!")
    print(f"总计: 成功 {total_success}, 失败 {total_fail}")
    print("=" * 50)

if __name__ == "__main__":
    main()
