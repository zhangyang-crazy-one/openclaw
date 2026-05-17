#!/usr/bin/env python3
"""
技术指标增量更新脚本
- 遍历所有股票日线数据
- 仅对有新增数据的股票重新计算技术指标
- 使用4个worker并行处理
"""

import os
import glob
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial
import warnings
warnings.filterwarnings('ignore')

# 路径配置
STOCKS_DIR = "/home/liujerry/金融数据/stocks"
TECH_DIR = "/home/liujerry/金融数据/technical_indicators"
PYTHON_BIN = "/home/liujerry/moltbot/openclaw_py/bin/python"

# 技术指标列名
TECH_COLS = [
    'date', 'close', 'high', 'low', 'volume',
    'ma5', 'ma10', 'ma20', 'ma30', 'ma60',
    'ema12', 'ema26', 'dif', 'dea', 'macd',
    'rsi6', 'rsi12', 'rsi24',
    'kdj_k', 'kdj_d', 'kdj_j',
    'bb_upper', 'bb_middle', 'bb_lower',
    'atr', 'obv', 'williams_r'
]


def calc_ma(df, windows=[5, 10, 20, 30, 60]):
    """计算移动平均线"""
    for w in windows:
        df[f'ma{w}'] = df['close'].rolling(window=w).mean()
    return df


def calc_ema(df, spans=[12, 26]):
    """计算指数移动平均线"""
    for span in spans:
        df[f'ema{span}'] = df['close'].ewm(span=span, adjust=False).mean()
    return df


def calc_macd(df):
    """计算MACD: dif=EMA12-EMA26, dea=EMA(dif,9), hist=(dif-dea)*2"""
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = (dif - dea) * 2
    df['dif'] = dif
    df['dea'] = dea
    df['macd'] = macd
    return df


def calc_rsi(df, periods=[6, 12, 24]):
    """计算RSI"""
    for period in periods:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df[f'rsi{period}'] = 100 - (100 / (rs + 1))
    return df


def calc_kdj(df, n=9):
    """计算KDJ"""
    low_n = df['low'].rolling(window=n, min_periods=1).min()
    high_n = df['high'].rolling(window=n, min_periods=1).max()
    rsv = (df['close'] - low_n) / (high_n - low_n + 1e-9) * 100
    
    k = np.zeros(len(df))
    d = np.zeros(len(df))
    j = np.zeros(len(df))
    
    k[0] = 50.0
    d[0] = 50.0
    
    for i in range(1, len(df)):
        k[i] = 2/3 * k[i-1] + 1/3 * rsv.iloc[i]
        d[i] = 2/3 * d[i-1] + 1/3 * k[i]
        j[i] = 3 * k[i] - 2 * d[i]
    
    df['kdj_k'] = k
    df['kdj_d'] = d
    df['kdj_j'] = j
    return df


def calc_bollinger(df, window=20):
    """计算布林带"""
    df['bb_middle'] = df['close'].rolling(window=window).mean()
    df['bb_std'] = df['close'].rolling(window=window).std()
    df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
    df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
    df.drop('bb_std', axis=1, inplace=True)
    return df


def calc_atr(df, period=14):
    """计算ATR"""
    high = df['high']
    low = df['low']
    prev_close = df['close'].shift(1)
    tr = np.maximum(high - low, np.maximum(
        np.abs(high - prev_close),
        np.abs(low - prev_close)
    ))
    df['atr'] = tr.ewm(span=period, adjust=False).mean()
    return df


def calc_obv(df):
    """计算OBV"""
    diff = df['close'].diff()
    sign = np.sign(diff)
    df['obv'] = (sign * df['volume']).cumsum()
    return df


def calc_williams_r(df, period=14):
    """计算Williams %R"""
    high_n = df['high'].rolling(window=period, min_periods=1).max()
    low_n = df['low'].rolling(window=period, min_periods=1).min()
    df['williams_r'] = -100 * (high_n - df['close']) / (high_n - low_n + 1e-9)
    return df


def calculate_all_indicators(df):
    """计算所有技术指标"""
    df = calc_ma(df)
    df = calc_ema(df)
    df = calc_macd(df)
    df = calc_rsi(df)
    df = calc_kdj(df)
    df = calc_bollinger(df)
    df = calc_atr(df)
    df = calc_obv(df)
    df = calc_williams_r(df)
    
    # 保留原始列 + 指标列
    keep_cols = ['date', 'close', 'high', 'low', 'volume',
                 'ma5', 'ma10', 'ma20', 'ma30', 'ma60',
                 'ema12', 'ema26', 'dif', 'dea', 'macd',
                 'rsi6', 'rsi12', 'rsi24',
                 'kdj_k', 'kdj_d', 'kdj_j',
                 'bb_upper', 'bb_middle', 'bb_lower',
                 'atr', 'obv', 'williams_r']
    
    # 确保所有列存在
    for col in keep_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    return df[keep_cols]


def process_stock(code):
    """处理单只股票：检查是否需要更新，如需要则重新计算"""
    stock_file = os.path.join(STOCKS_DIR, f"{code}.csv")
    tech_file = os.path.join(TECH_DIR, f"{code}.csv")
    
    try:
        # 读取股票数据
        stock_df = pd.read_csv(stock_file, parse_dates=['date'])
        if stock_df.empty or 'date' not in stock_df.columns:
            return code, 'skip', 'empty or invalid'
        
        latest_stock_date = stock_df['date'].max()
        
        # 检查技术指标文件
        need_update = True
        if os.path.exists(tech_file):
            try:
                tech_df = pd.read_csv(tech_file, parse_dates=['date'])
                if not tech_df.empty and 'date' in tech_df.columns:
                    latest_tech_date = tech_df['date'].max()
                    if latest_stock_date <= latest_tech_date:
                        need_update = False
            except:
                pass
        
        if not need_update:
            return code, 'skip', 'up-to-date'
        
        # 重新计算所有技术指标
        stock_df = stock_df.sort_values('date').reset_index(drop=True)
        tech_df = calculate_all_indicators(stock_df)
        
        # 保存技术指标
        os.makedirs(TECH_DIR, exist_ok=True)
        tech_df.to_csv(tech_file, index=False)
        
        return code, 'updated', str(latest_stock_date.date())
    
    except Exception as e:
        return code, 'error', str(e)[:100]


def main():
    print(f"=== 技术指标增量更新 ===")
    print(f"时间: {pd.Timestamp.now()}")
    print(f"Workers: 4")
    print()
    
    # 获取所有股票代码
    stock_files = glob.glob(os.path.join(STOCKS_DIR, "*.csv"))
    codes = [os.path.basename(f).replace('.csv', '') for f in stock_files]
    print(f"股票总数: {len(codes)}")
    
    # 快速检查需要更新的股票
    stocks_need_update = []
    stocks_up_to_date = 0
    
    print("快速扫描中...")
    for i, code in enumerate(codes):
        if i % 500 == 0:
            print(f"  扫描进度: {i}/{len(codes)}")
        
        stock_file = os.path.join(STOCKS_DIR, f"{code}.csv")
        tech_file = os.path.join(TECH_DIR, f"{code}.csv")
        
        try:
            stock_df = pd.read_csv(stock_file, parse_dates=['date'])
            latest_stock_date = stock_df['date'].max()
            
            need_update = True
            if os.path.exists(tech_file):
                try:
                    tech_df = pd.read_csv(tech_file, parse_dates=['date'])
                    if not tech_df.empty:
                        latest_tech_date = tech_df['date'].max()
                        if latest_stock_date <= latest_tech_date:
                            need_update = False
                            stocks_up_to_date += 1
                except:
                    pass
            
            if need_update:
                stocks_need_update.append(code)
        except:
            pass
    
    print(f"  扫描完成: {len(codes)}/{len(codes)}")
    print(f"已最新: {stocks_up_to_date}, 需更新: {len(stocks_need_update)}")
    print()
    
    if not stocks_need_update:
        print("所有股票技术指标已是最新的，无需更新。")
        return
    
    print(f"开始并行计算 ({len(stocks_need_update)} 只股票)...")
    
    # 使用4个worker并行处理
    with Pool(processes=4) as pool:
        results = pool.map(process_stock, stocks_need_update)
    
    # 统计结果
    updated = [r for r in results if r[1] == 'updated']
    errors = [r for r in results if r[1] == 'error']
    skipped = [r for r in results if r[1] == 'skip']
    
    print()
    print(f"=== 更新完成 ===")
    print(f"更新成功: {len(updated)}")
    print(f"跳过: {len(skipped)}")
    print(f"错误: {len(errors)}")
    
    if errors:
        print(f"\n错误详情 (前5条):")
        for r in errors[:5]:
            print(f"  {r[0]}: {r[2]}")
    
    print(f"\n已更新的股票代码: {[r[0] for r in updated[:20]]}" + 
          (f"... 共{len(updated)}只" if len(updated) > 20 else ""))


if __name__ == '__main__':
    main()
