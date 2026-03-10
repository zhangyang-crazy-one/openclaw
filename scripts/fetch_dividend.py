#!/usr/bin/env python3
"""
分红数据获取脚本
使用 akshare 获取股票分红送转数据
"""
import akshare as ak
import pandas as pd
from pathlib import Path
import sys

DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")

def get_dividend(stock_code):
    """获取单只股票分红数据"""
    try:
        # 转换为 akshare 需要的格式
        code = stock_code.replace("sz.", "").replace("sh.", "")
        df = ak.stock_dividend_cninfo(symbol=code)
        if df is not None and len(df) > 0:
            df['code'] = stock_code
            return df
    except Exception as e:
        print(f"获取 {stock_code} 分红数据失败: {e}")
    return None

def fetch_chuangye_dividend():
    """获取创业板股票分红数据"""
    # 读取创业板股票列表
    stock_list = DATA_DIR / "chuangye_full" / "profit.csv"
    if not stock_list.exists():
        print(f"股票列表文件不存在: {stock_list}")
        return
    
    df = pd.read_csv(stock_list)
    codes = df['code'].unique()
    
    all_dividends = []
    batch_size = 50
    
    for i, code in enumerate(codes):
        print(f"获取分红数据: {code} ({i+1}/{len(codes)})")
        div = get_dividend(code)
        if div is not None:
            all_dividends.append(div)
        
        # 每批次保存一次
        if (i + 1) % batch_size == 0:
            save_dividends(all_dividends, f"chuangye_dividend_batch{(i//batch_size)+1}.csv")
            all_dividends = []
    
    # 保存剩余数据
    if all_dividends:
        save_dividends(all_dividends, "chuangye_dividend.csv")

def save_dividends(dividend_list, filename):
    """保存分红数据"""
    if not dividend_list:
        return
    df = pd.concat(dividend_list, ignore_index=True)
    output_path = DATA_DIR / filename
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"已保存 {len(df)} 条分红数据到 {output_path}")

if __name__ == "__main__":
    # 测试单只股票
    if len(sys.argv) > 1:
        code = sys.argv[1]
        div = get_dividend(code)
        if div is not None:
            print(div)
    else:
        fetch_chuangye_dividend()
