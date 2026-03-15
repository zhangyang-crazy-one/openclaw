#!/usr/bin/env python3
"""
全量财务数据获取脚本
包含: 基础财务数据 + 巴菲特10大指标 + 分红数据
"""
import akshare as ak
import pandas as pd
from pathlib import Path
import sys
import time

DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")
STOCK_LIST = DATA_DIR / "chuangye_full" / "profit.csv"

def get_financial_indicators(code):
    """获取财务指标 - 巴菲特10大公式相关"""
    try:
        # 转换为 akshare 格式
        symbol = code.replace("sz.", "").replace("sh.", "")
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df is not None and len(df) > 0:
            df = df.sort_values('报告期', ascending=False)
            df['code'] = code
            return df.head(4)  # 最近4个季度
    except Exception as e:
        pass
    return None

def get_dividend_data(code):
    """获取分红数据"""
    try:
        symbol = code.replace("sz.", "").replace("sh.", "")
        df = ak.stock_dividend_cninfo(symbol=symbol)
        if df is not None and len(df) > 0:
            df['code'] = code
            return df
    except Exception as e:
        pass
    return None

def fetch_all_data():
    """获取全量数据"""
    # 读取股票列表
    if not STOCK_LIST.exists():
        print(f"股票列表不存在: {STOCK_LIST}")
        return
    
    df = pd.read_csv(STOCK_LIST)
    codes = df['code'].unique()
    
    # 清空之前的数据文件（重新开始）
    if DATA_DIR / "chuangye_financial_indicators.csv":
        (DATA_DIR / "chuangye_financial_indicators.csv").unlink(missing_ok=True)
    if DATA_DIR / "chuangye_dividend.csv":
        (DATA_DIR / "chuangye_dividend.csv").unlink(missing_ok=True)
    
    all_financial = []
    all_dividends = []
    first_save = True  # 标记是否是第一次保存
    
    for i, code in enumerate(codes):
        print(f"处理 {code} ({i+1}/{len(codes)})")
        
        # 获取财务指标
        fin = get_financial_indicators(code)
        if fin is not None:
            all_financial.append(fin)
        
        # 获取分红数据
        div = get_dividend_data(code)
        if div is not None:
            all_dividends.append(div)
        
        # 每批次保存（追加模式）
        if (i + 1) % 50 == 0:
            save_data(all_financial, all_dividends, first_save)
            all_financial = []
            all_dividends = []
            first_save = False
            print(f"已处理 {i+1} 只股票")
    
    # 保存剩余数据
    if all_financial or all_dividends:
        save_data(all_financial, all_dividends, first_save)
    
    print(f"完成! 共处理 {len(codes)} 只股票")

def save_data(financial_list, dividend_list, first_save=True):
    """保存数据（追加模式）"""
    if financial_list:
        df = pd.concat(financial_list, ignore_index=True)
        # 第一次保存带表头，之后追加
        df.to_csv(DATA_DIR / "chuangye_financial_indicators.csv", 
                  mode='w' if first_save else 'a', 
                  header=first_save, 
                  index=False, encoding='utf-8-sig')
        print(f"已保存 {len(df)} 条财务指标数据")
    
    if dividend_list:
        df = pd.concat(dividend_list, ignore_index=True)
        df.to_csv(DATA_DIR / "chuangye_dividend.csv", 
                  mode='w' if first_save else 'a', 
                  header=first_save, 
                  index=False, encoding='utf-8-sig')
        print(f"已保存 {len(df)} 条分红数据")

if __name__ == "__main__":
    # 测试单只股票
    if len(sys.argv) > 1:
        code = sys.argv[1]
        print(f"测试: {code}")
        fin = get_financial_indicators(code)
        div = get_dividend_data(code)
        if fin is not None:
            print("财务指标:")
            print(fin.columns.tolist())
        if div is not None:
            print("分红数据:")
            print(div)
    else:
        fetch_all_data()
