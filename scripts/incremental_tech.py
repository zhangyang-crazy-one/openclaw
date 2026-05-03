import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from multiprocessing import Pool, cpu_count

STOCKS_DIR = os.path.expanduser("~/金融数据/stocks")
TECH_DIR = os.path.expanduser("~/金融数据/technical_indicators")

def needs_update(code, stocks_dir, tech_dir):
    stock_file = os.path.join(stocks_dir, f"{code}.csv")
    tech_file = os.path.join(tech_dir, f"{code}.csv")
    
    if not os.path.exists(stock_file):
        return False
    
    try:
        df_stock = pd.read_csv(stock_file)
        if df_stock.empty or 'date' not in df_stock.columns:
            return False
        latest_stock_date = df_stock['date'].iloc[-1]
    except:
        return False
    
    if os.path.exists(tech_file):
        try:
            df_tech = pd.read_csv(tech_file)
            if not df_tech.empty and 'date' in df_tech.columns:
                latest_tech_date = df_tech['date'].iloc[-1]
                if latest_tech_date >= latest_stock_date:
                    return False
        except:
            pass
    
    return True

def calc_indicators(code, stocks_dir):
    stock_file = os.path.join(stocks_dir, f"{code}.csv")
    tech_file = os.path.join(TECH_DIR, f"{code}.csv")
    
    try:
        df = pd.read_csv(stock_file)
        if df.empty or 'close' not in df.columns:
            return code, False
        
        close = df['close'].copy()
        high = df['high'].copy() if 'high' in df.columns else df['close'].copy()
        low = df['low'].copy() if 'low' in df.columns else df['close'].copy()
        volume = df['volume'].copy() if 'volume' in df.columns else pd.Series(0, index=df.index)
        
        ma5 = close.rolling(window=5).mean()
        ma10 = close.rolling(window=10).mean()
        ma20 = close.rolling(window=20).mean()
        ma30 = close.rolling(window=30).mean()
        ma60 = close.rolling(window=60).mean()
        
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        
        dif = ema12 - ema26
        dea = dif.ewm(span=9).mean()
        macd = (dif - dea) * 2
        
        def calc_rsi(series, n):
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = (-delta).where(delta < 0, 0)
            avg_gain = gain.ewm(alpha=1/n, min_periods=n).mean()
            avg_loss = loss.ewm(alpha=1/n, min_periods=n).mean()
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        
        rsi6 = calc_rsi(close, 6)
        rsi12 = calc_rsi(close, 12)
        rsi24 = calc_rsi(close, 24)
        
        def calc_kdj(h, l, c, n=9):
            low_n = l.rolling(window=n).min()
            high_n = h.rolling(window=n).max()
            rsv = (c - low_n) / (high_n - low_n) * 100
            rsv = rsv.fillna(50)
            k = pd.Series(50.0, index=c.index)
            d = pd.Series(50.0, index=c.index)
            j = pd.Series(50.0, index=c.index)
            for i in range(1, len(c)):
                k.iloc[i] = 2/3 * k.iloc[i-1] + 1/3 * rsv.iloc[i]
                d.iloc[i] = 2/3 * d.iloc[i-1] + 1/3 * k.iloc[i]
                j.iloc[i] = 3 * k.iloc[i] - 2 * d.iloc[i]
            return k, d, j
        
        kdj_k, kdj_d, kdj_j = calc_kdj(high, low, close)
        
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std
        
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/14, min_periods=14).mean()
        
        diff_close = close.diff()
        sign = pd.Series(0, index=close.index)
        sign[diff_close > 0] = 1
        sign[diff_close < 0] = -1
        obv = (sign * volume).cumsum()
        
        rolling_high = high.rolling(window=14).max()
        rolling_low = low.rolling(window=14).min()
        williams_r = (rolling_high - close) / (rolling_high - rolling_low) * -100
        
        result = pd.DataFrame({
            'date': df['date'],
            'close': close,
            'high': high,
            'low': low,
            'volume': volume,
            'ma5': ma5, 'ma10': ma10, 'ma20': ma20, 'ma30': ma30, 'ma60': ma60,
            'ema12': ema12, 'ema26': ema26,
            'dif': dif, 'dea': dea, 'macd': macd,
            'rsi6': rsi6, 'rsi12': rsi12, 'rsi24': rsi24,
            'kdj_k': kdj_k, 'kdj_d': kdj_d, 'kdj_j': kdj_j,
            'bb_upper': bb_upper, 'bb_middle': bb_middle, 'bb_lower': bb_lower,
            'atr': atr, 'obv': obv, 'williams_r': williams_r
        })
        
        result.to_csv(tech_file, index=False)
        return code, True
    except Exception as e:
        return code, False

def main():
    print("=== 增量技术指标更新 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    stock_files = glob.glob(os.path.join(STOCKS_DIR, "*.csv"))
    codes = [os.path.basename(f).replace(".csv", "") for f in stock_files]
    print(f"股票总数: {len(codes)}")
    
    to_update = [code for code in codes if needs_update(code, STOCKS_DIR, TECH_DIR)]
    print(f"需要更新的股票: {len(to_update)} 只")
    
    if not to_update:
        print("没有需要更新的股票")
        return
    
    worker_count = 4
    print(f"使用 {worker_count} 个 worker 并行处理...")
    
    with Pool(processes=worker_count) as pool:
        results = pool.starmap(calc_indicators, [(code, STOCKS_DIR) for code in to_update])
    
    success = sum(1 for _, ok in results if ok)
    failed = len(results) - success
    
    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"更新成功: {success} 只")
    print(f"更新失败: {failed} 只")
    
    ti_count = len(glob.glob(os.path.join(TECH_DIR, "*.csv")))
    stock_count = len(glob.glob(os.path.join(STOCKS_DIR, "*.csv")))
    print(f"\n=== 覆盖验证 ===")
    print(f"技术指标文件: {ti_count} 只")
    print(f"K线文件: {stock_count} 只")
    print(f"覆盖率: {ti_count/stock_count*100:.1f}%")
    
    import random
    if to_update:
        sample_code = random.choice(to_update)
        sample_file = os.path.join(TECH_DIR, f"{sample_code}.csv")
        if os.path.exists(sample_file):
            df = pd.read_csv(sample_file)
            if 'rsi6' in df.columns and not df.empty:
                latest = df.iloc[-1]
                print(f"\n抽检 {sample_code}: RSI(6)={latest['rsi6']:.4f}, RSI(12)={latest['rsi12']:.4f}")

if __name__ == "__main__":
    main()
