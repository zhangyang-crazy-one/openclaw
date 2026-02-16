#!/usr/bin/env python3
"""
创业板财务数据采集脚本 - 分批版本
每小时获取100只，逐步完成全部1431只
"""
import baostock as bs
import pandas as pd
import time
import os
from datetime import datetime

OUTPUT_DIR = '/home/liujerry/金融数据/fundamentals/chuangye_full'
BATCH_SIZE = 100  # 每批100只

def get_previous_count():
    """获取之前已获取的股票数"""
    profit_file = f'{OUTPUT_DIR}/profit.csv'
    if os.path.exists(profit_file):
        df = pd.read_csv(profit_file)
        return df['code'].nunique() if 'code' in df.columns else 0
    return 0

def main():
    lg = bs.login()
    if lg.error_code != '0':
        print(f'登录失败: {lg.error_msg}')
        return
    
    print(f'[{datetime.now()}] 登录成功')
    
    # 读取股票列表
    chuangye = pd.read_csv('/home/liujerry/金融数据/fundamentals/chuangye_stock_list.csv')
    all_codes = chuangye['code'].tolist()
    
    # 获取之前进度
    prev_count = get_previous_count()
    print(f'已获取: {prev_count}只')
    
    # 计算本次获取范围
    start_idx = prev_count
    end_idx = min(start_idx + BATCH_SIZE, len(all_codes))
    
    if start_idx >= len(all_codes):
        print('已完成全部数据获取!')
        bs.logout()
        return
    
    codes = all_codes[start_idx:end_idx]
    print(f'本次获取: {start_idx+1}-{end_idx}只 ({len(codes)}只)')
    
    # 获取2024Q4和2025Q3最新数据
    quarters = [('2025','3'), ('2024','4')]
    
    all_profit = []
    all_dupont = []
    
    for idx, code in enumerate(codes):
        for year, quarter in quarters:
            try:
                rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
                while rs.error_code == '0' and rs.next():
                    all_profit.append(rs.get_row_data())
                
                rs = bs.query_dupont_data(code=code, year=year, quarter=quarter)
                while rs.error_code == '0' and rs.next():
                    all_dupont.append(rs.get_row_data())
            except:
                pass
        
        if (idx + 1) % 50 == 0:
            print(f'进度: {idx+1}/{len(codes)}')
        
        time.sleep(0.01)
    
    print(f'本次获取: 盈利{len(all_profit)}, 杜邦{len(all_dupont)}')
    
    # 读取已有数据并合并
    existing_profit = []
    existing_dupont = []
    
    if os.path.exists(f'{OUTPUT_DIR}/profit.csv'):
        existing_profit = pd.read_csv(f'{OUTPUT_DIR}/profit.csv').values.tolist()
    if os.path.exists(f'{OUTPUT_DIR}/dupont.csv'):
        existing_dupont = pd.read_csv(f'{OUTPUT_DIR}/dupont.csv').values.tolist()
    
    # 添加新数据
    if all_profit:
        profit_cols = ['code','pubDate','statDate','roeAvg','npMargin','gpMargin','netProfit','epsTTM','MBRevenue','totalShare','liqaShare']
        new_profit_df = pd.DataFrame(all_profit, columns=profit_cols)
        existing_profit_df = pd.DataFrame(existing_profit, columns=profit_cols) if existing_profit else pd.DataFrame(columns=profit_cols)
        combined = pd.concat([existing_profit_df, new_profit_df], ignore_index=True)
        combined.to_csv(f'{OUTPUT_DIR}/profit.csv', index=False)
        print(f'盈利数据总计: {combined["code"].nunique()}只')
    
    if all_dupont:
        dupont_cols = ['code','pubDate','statDate','dupontROE','dupontAssetStoEquity','dupontAssetTurn','dupontPnitoni','dupontNitogr','dupontTaxBurden','dupontIntburden','dupontEbittogr']
        new_dupont_df = pd.DataFrame(all_dupont, columns=dupont_cols)
        existing_dupont_df = pd.DataFrame(existing_dupont, columns=dupont_cols) if existing_dupont else pd.DataFrame(columns=dupont_cols)
        combined = pd.concat([existing_dupont_df, new_dupont_df], ignore_index=True)
        combined.to_csv(f'{OUTPUT_DIR}/dupont.csv', index=False)
    
    bs.logout()
    print(f'[{datetime.now()}] 完成!')

if __name__ == '__main__':
    main()
