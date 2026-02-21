#!/usr/bin/env python3
"""
A股财务数据采集脚本 - 使用baostock
每次采集100只股票，保存到指定目录
"""
import baostock as bs
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = "/home/liujerry/金融数据/fundamentals/chuangye_full"

def get_stock_list():
    """获取创业板股票列表"""
    stock_list_file = "/home/liujerry/金融数据/fundamentals/chuangye_stock_list.csv"
    if os.path.exists(stock_list_file):
        df = pd.read_csv(stock_list_file)
        if 'code' in df.columns:
            return df['code'].tolist()
        elif '股票代码' in df.columns:
            return df['股票代码'].tolist()
    return []

def get_collected_codes():
    """获取已采集的股票代码"""
    collected = set()
    files = [
        f"{OUTPUT_DIR}/profit.csv",
        f"{OUTPUT_DIR}/profit_100.csv",
        f"{OUTPUT_DIR}/profit_baostock.csv"
    ]
    for f in files:
        if os.path.exists(f):
            try:
                df = pd.read_csv(f)
                if 'code' in df.columns:
                    collected.update(df['code'].unique())
            except:
                pass
    return collected

def fetch_financial_data_baostock(stock_codes, year=2024, quarter=4):
    """使用baostock批量获取财务数据"""
    # 登录
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return None
    
    print(f"已登录Baostock")
    
    all_data = []
    total = len(stock_codes)
    success = 0
    failed = 0
    
    for i, code in enumerate(stock_codes):
        # 股票代码格式: sz.300001 (已经是正确格式)
        bs_code = code  # 直接使用
        
        if (i + 1) % 10 == 0:
            print(f"  进度: {i+1}/{total}...", end=" ")
        
        try:
            rs = bs.query_profit_data(code=bs_code, year=year, quarter=quarter)
            
            if rs.error_code == '0':
                data_list = []
                while rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df = pd.DataFrame(data_list, columns=rs.fields)
                    df['code'] = code
                    all_data.append(df)
                    success += 1
                else:
                    failed += 1
            else:
                failed += 1
                
        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"\n错误 {code}: {e}")
        
        # 避免请求过快
        time.sleep(0.15)
    
    bs.logout()
    print(f"\nBaostock登出")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined
    return None

def main():
    print("=" * 60)
    print("A股财务数据采集开始 (Baostock)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 获取股票列表
    stock_list = get_stock_list()
    print(f"\n股票列表总数: {len(stock_list)}")
    
    # 获取已采集的股票
    collected = get_collected_codes()
    print(f"已采集股票数: {len(collected)}")
    
    # 过滤未采集的股票
    uncollected = [s for s in stock_list if s not in collected]
    print(f"待采集股票数: {len(uncollected)}")
    
    if not uncollected:
        print("\n所有股票已采集完成！")
        return
    
    # 采集前100只
    to_collect = uncollected[:100]
    print(f"\n本次将采集 {len(to_collect)} 只股票")
    
    # 执行采集
    result = fetch_financial_data_baostock(to_collect)
    
    if result is not None and len(result) > 0:
        # 保存结果
        output_file = f"{OUTPUT_DIR}/profit_baostock.csv"
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n" + "=" * 60)
        print(f"采集完成!")
        print(f"成功获取: {len(result)} 条记录")
        print(f"保存到: {output_file}")
        print("=" * 60)
        
        # 统计信息
        print(f"\n数据统计:")
        print(f"  - 采集股票数: {len(to_collect)}")
        print(f"  - 有效记录: {len(result)}")
        print(f"  - 字段: {result.columns.tolist()}")
    else:
        print("\n未获取到任何数据")

if __name__ == "__main__":
    main()
