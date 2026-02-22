#!/usr/bin/env python3
"""
A股财务数据采集脚本 - 使用akshare
每次采集100只股票 - 使用stock_financial_abstract_ths
"""

import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals"

def get_a_stock_list():
    """获取A股股票列表"""
    try:
        df = ak.stock_info_a_code_name()
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None

def fetch_financial_data(stock_codes, batch_num):
    """采集指定股票的财务数据"""
    all_data = []
    success_count = 0
    
    for i, code in enumerate(stock_codes):
        try:
            print(f"[{i+1}/{len(stock_codes)}] 采集 {code}...", end=" ", flush=True)
            
            # 获取财务摘要数据
            financial = ak.stock_financial_abstract_ths(symbol=code)
            
            if financial is not None and len(financial) > 0:
                # 添加股票代码
                financial['stock_code'] = code
                
                # 获取股票名称
                try:
                    stock_df = ak.stock_info_a_code_name()
                    if code in stock_df['code'].values:
                        financial['stock_name'] = stock_df[stock_df['code'] == code]['name'].values[0]
                    else:
                        financial['stock_name'] = ''
                except:
                    financial['stock_name'] = ''
                
                financial['fetch_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                all_data.append(financial)
                success_count += 1
                print("✓")
            else:
                print("无数据")
            
            time.sleep(0.5)  # 避免请求过快
            
        except Exception as e:
            print(f"失败: {str(e)[:30]}")
            continue
    
    if all_data:
        # 合并数据
        result = pd.concat(all_data, ignore_index=True)
        
        # 保存
        output_file = os.path.join(OUTPUT_DIR, f"a_stock_financial_batch{batch_num}.csv")
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n批次 {batch_num} 保存完成: {output_file}")
        print(f"成功采集: {success_count} 只股票, 共 {len(result)} 条记录")
        return success_count
    else:
        print(f"批次 {batch_num} 无数据")
        return 0

def main():
    print("=" * 50)
    print("A股财务数据采集开始")
    print("=" * 50)
    
    # 获取股票列表
    stock_df = get_a_stock_list()
    if stock_df is None:
        print("无法获取股票列表，退出")
        return
    
    total_stocks = len(stock_df)
    print(f"A股总共 {total_stocks} 只股票")
    
    # 计算批次
    batch_size = 100
    batch_num = 26  # 从第26批开始
    
    # 获取本次要采集的股票
    start_idx = (batch_num - 1) * batch_size
    end_idx = min(start_idx + batch_size, total_stocks)
    
    if start_idx >= total_stocks:
        print(f"股票已全部采集完成!")
        return
    
    stocks = stock_df.iloc[start_idx:end_idx]['code'].tolist()
    print(f"本次采集: 批次 {batch_num}, 股票索引 {start_idx}-{end_idx}")
    print("-" * 50)
    
    # 采集数据
    count = fetch_financial_data(stocks, batch_num)
    
    print("=" * 50)
    print(f"采集完成! 成功 {count} 只股票")
    print("=" * 50)

if __name__ == "__main__":
    main()
