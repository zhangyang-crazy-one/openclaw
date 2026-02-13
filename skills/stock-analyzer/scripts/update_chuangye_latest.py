#!/usr/bin/env python3
"""
快速更新创业板最新数据
"""
import baostock as bs
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
PROGRESS_FILE = Path.home() / ".config" / "deepseeker" / "chuangye_update_progress.json"

def update_chuangye_latest():
    """更新创业板最新数据"""
    print("="*60)
    print("📈 更新创业板最新交易日数据")
    print("="*60)
    
    # 固定更新范围 (最新5个交易日)
    end_date = "2026-02-13"
    start_date = "2026-02-07"
    
    print(f"\n🔄 更新范围: {start_date} ~ {end_date}")
    
    # 登录
    lg = bs.login()
    print(f"登录: {lg.error_msg}")
    
    # 获取创业板股票列表
    print("\n📋 获取创业板列表...")
    rs = bs.query_stock_industry()
    chuangye_stocks = []
    while (rs.error_code == '0') and rs.next():
        row = rs.get_row_data()
        code = row[1]
        if code.startswith('sz.300'):
            chuangye_stocks.append(code.replace('sz.', ''))
    
    print(f"创业板总数: {len(chuangye_stocks)}")
    
    # 更新每只股票
    updated = 0
    failed = []
    skipped = 0
    
    print("\n" "-"*60)
    
    for i, code in enumerate(chuangye_stocks):
        filepath = DATA_DIR / f"{code}.csv"
        
        if not filepath.exists():
            failed.append(code)
            continue
        
        try:
            # 获取最新数据
            rs = bs.query_history_k_data_plus(
                f"sz.{code}",
                "date,open,high,low,close,volume",
                f"{start_date},{end_date}", "day", "forward"
            )
            
            data_list = []
            while (rs.error_code == '0') and rs.next():
                data_list.append(rs.get_row_data())
            
            if data_list:
                # 读取现有数据
                df = pd.read_csv(filepath)
                last_date = pd.to_datetime(df['date'].max())
                
                # 只添加新数据
                new_data = []
                for row in data_list:
                    try:
                        row_date = pd.to_datetime(row[0])
                        if row_date > last_date:
                            new_data.append(row)
                    except:
                        pass
                
                if new_data:
                    new_df = pd.DataFrame(new_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                    df = pd.concat([df, new_df], ignore_index=True)
                    df.to_csv(filepath, index=False)
                    updated += 1
                    
                    if updated % 100 == 0:
                        print(f"  已更新: {updated}/{len(chuangye_stocks)}...")
                else:
                    skipped += 1
            
            time.sleep(0.05)  # 避免请求过快
            
        except Exception as e:
            failed.append(code)
    
    bs.logout()
    
    # 保存进度
    progress = {
        "last_update": datetime.now().isoformat(),
        "update_range": f"{start_date} ~ {end_date}",
        "updated": updated,
        "skipped": skipped,
        "failed_count": len(failed)
    }
    
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ 更新完成!")
    print(f"   更新股票: {updated} 只")
    print(f"   已有数据: {skipped} 只")
    print(f"   失败: {len(failed)} 只")
    print("="*60)

if __name__ == "__main__":
    update_chuangye_latest()
