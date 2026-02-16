#!/usr/bin/env python3
"""
创业板财务数据采集 - 极速版v2
获取2025Q3或2024Q4数据
"""
import baostock as bs
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = '/home/liujerry/金融数据/fundamentals/chuangye_full'
BATCH_SIZE = 300  # 每批300只

def get_existing_codes():
    profit_file = f'{OUTPUT_DIR}/profit.csv'
    if os.path.exists(profit_file):
        df = pd.read_csv(profit_file)
        return set(df['code'].unique()) if 'code' in df.columns else set()
    return set()

def main():
    lg = bs.login()
    print(f'[{datetime.now()}] 登录成功')
    
    chuangye = pd.read_csv('/home/liujerry/金融数据/fundamentals/chuangye_stock_list.csv')
    all_codes = chuangye['code'].tolist()
    
    existing = get_existing_codes()
    print(f'已获取: {len(existing)}只')
    
    # 获取尚未获取的股票
    remaining = [c for c in all_codes if c not in existing]
    print(f'剩余: {len(remaining)}只')
    
    if not remaining:
        print('已完成!')
        bs.logout()
        return
    
    # 本批获取
    batch = remaining[:BATCH_SIZE]
    print(f'本批: {len(batch)}只')
    
    # 尝试2025Q3，没有则尝试2024Q4
    all_profit = []
    
    for idx, code in enumerate(batch):
        # 2025Q3
        rs = bs.query_profit_data(code=code, year='2025', quarter='3')
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        
        # 如果没有2025Q3数据，尝试2024Q4
        if not data:
            rs = bs.query_profit_data(code=code, year='2024', quarter='4')
            while rs.error_code == '0' and rs.next():
                data.append(rs.get_row_data())
        
        all_profit.extend(data)
        
        if (idx + 1) % 100 == 0:
            print(f'进度: {idx+1}/{len(batch)}')
        
        time.sleep(0.003)
    
    print(f'获取: {len(all_profit)}条')
    
    # 保存
    if all_profit:
        profit_cols = ['code','pubDate','statDate','roeAvg','npMargin','gpMargin','netProfit','epsTTM','MBRevenue','totalShare','liqaShare']
        new_df = pd.DataFrame(all_profit, columns=profit_cols)
        
        if os.path.exists(f'{OUTPUT_DIR}/profit.csv'):
            existing_df = pd.read_csv(f'{OUTPUT_DIR}/profit.csv')
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            # 去重
            combined = combined.drop_duplicates(subset=['code', 'statDate'], keep='last')
        else:
            combined = new_df
        
        combined.to_csv(f'{OUTPUT_DIR}/profit.csv', index=False)
        print(f'总计: {combined["code"].nunique()}只')
    
    bs.logout()
    print(f'[{datetime.now()}] 完成!')

if __name__ == '__main__':
    main()
