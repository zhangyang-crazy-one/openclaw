#!/usr/bin/env python3
"""
创业板批量筛选工具 - 并行优化版
使用多线程并行处理，加速API调用
"""

import os
import pandas as pd
import baostock as bs
import akshare as ak
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

STOCK_DIR = "/home/liujerry/金融数据/stocks"
OUTPUT_DIR = "/home/liujerry/金融数据/screening_results"

def get_chi_next_stocks():
    stocks = []
    for f in os.listdir(STOCK_DIR):
        if f.startswith('3') and f.endswith('.csv'):
            code = f.replace('.csv', '')
            stocks.append(code)
    return sorted(stocks)

def get_financial_data(code):
    """获取财务数据"""
    try:
        fin_df = ak.stock_financial_abstract_ths(symbol=code)
        if fin_df is None or fin_df.empty:
            return None
        
        latest = fin_df.iloc[-1]
        roe_str = str(latest.get('净资产收益率', '0'))
        roe = 0
        if roe_str and roe_str not in ['nan', 'None', '']:
            try:
                roe = float(roe_str.replace('%', ''))
            except:
                pass
        
        return {'code': code, 'roe': roe}
    except:
        return None

def get_price_momentum(code):
    """获取价格和动量"""
    try:
        bs_code = f"sz.{code}"
        lg = bs.login()
        rs = bs.query_history_k_data_plus(
            bs_code, "date,close",
            start_date="2025-01-01", frequency="d"
        )
        
        prices = []
        while rs.next():
            prices.append(rs.get_row_data())
        
        bs.logout()
        
        if not prices or len(prices) < 20:
            return None
        
        price_now = float(prices[-1][1])
        price_then = float(prices[-20][1])
        momentum = (price_now / price_then - 1) * 100
        
        return {'code': code, 'price': price_now, 'momentum': momentum}
    except:
        return None

def main():
    print("=" * 60)
    print("🎯 创业板全量筛选 (并行优化版)")
    print("=" * 60)
    
    stocks = get_chi_next_stocks()
    print(f"\n📊 创业板股票总数: {len(stocks)}")
    
    # 阶段1: ROE筛选 (并行)
    print("\n🔍 阶段1: 神奇公式筛选 (ROE >= 15%)...")
    
    magic_results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_financial_data, code): code for code in stocks}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"  已处理 {completed}/{len(stocks)}...")
            
            result = future.result()
            if result and result.get('roe', 0) >= 15:
                magic_results.append(result)
    
    print(f"  ✅ ROE>=15%: {len(magic_results)} 只")
    
    if not magic_results:
        print("\n❌ 没有股票通过ROE筛选")
        return
    
    # 阶段2: 价格数据 (并行)
    print("\n🔍 阶段2: 获取价格数据...")
    
    ff_results = []
    codes_to_check = [r['code'] for r in magic_results]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_price_momentum, code): code for code in codes_to_check}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            
            price_data = future.result()
            code = futures[future]
            
            # 找到对应的ROE
            for r in magic_results:
                if r['code'] == code:
                    if price_data:
                        ff_results.append({
                            'code': code,
                            'roe': r['roe'],
                            'price': price_data['price'],
                            'momentum': price_data['momentum'],
                        })
                    break
    
    print(f"  ✅ 获取价格数据: {len(ff_results)} 只")
    
    # 按ROE排序
    ff_results.sort(key=lambda x: x['roe'], reverse=True)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📊 最终筛选结果 (按ROE排序)")
    print("=" * 60)
    
    print(f"\n{'排名':<4} {'代码':<10} {'ROE':<10} {'价格':<10} {'6M动量':<10}")
    print("-" * 55)
    
    for i, r in enumerate(ff_results[:50], 1):
        print(f"{i:<4} {r['code']:<10} {r['roe']:<10.1f}% {r['price']:<10.2f} {r['momentum']:<10.1f}%")
    
    # 保存结果
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, "screening_results_2026-03-16.csv")
    
    df = pd.DataFrame(ff_results)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 结果已保存: {output_file}")
    print(f"   共 {len(ff_results)} 只股票通过筛选")

if __name__ == "__main__":
    main()
