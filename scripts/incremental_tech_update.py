#!/usr/bin/env python3
"""
增量更新技术指标 - 仅重新计算有新数据的股票
"""
import os
import glob
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

STOCK_DIR = Path('/home/liujerry/金融数据/stocks')
TECH_DIR  = Path('/home/liujerry/金融数据/technical_indicators')
OUT_DIR   = TECH_DIR
PYTHON    = '/home/liujerry/moltbot/openclaw_py/bin/python'
WORKERS   = 4

# ── 列名兼容 (000300.csv 用中文列名) ──────────────────────────────────────
_COLS = ['date','open','high','low','close','volume']
_COLS_CN = ['日期','开盘','最高','最低','收盘','成交量']

def read_stock(path):
    df = pd.read_csv(path)
    # 统一列名
    col_map = dict(zip(df.columns[:6], _COLS[:len(df.columns)]))
    df.rename(columns=col_map, inplace=True)
    if 'date' not in df.columns:
        raise ValueError(f"No date col in {path}: {df.columns.tolist()}")
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# ── 技术指标计算 ────────────────────────────────────────────────────────────
def calc_ma(df, w):
    return df['close'].rolling(w).mean()

def calc_ema(df, span):
    return df['close'].ewm(span=span).mean()

def calc_macd(df):
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    dif   = ema12 - ema26
    dea   = dif.ewm(span=9).mean()
    hist  = (dif - dea) * 2
    return dif, dea, hist

def calc_rsi(df, n=14):
    diff = df['close'].diff()
    gain = diff.clip(lower=0)
    loss = (-diff).clip(lower=0)
    avg_gain = gain.ewm(com=n-1, min_periods=n).mean()
    avg_loss = loss.ewm(com=n-1, min_periods=n).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    return rsi

def calc_kdj(df, n=9):
    low_n  = df['low'].rolling(n).min()
    high_n = df['high'].rolling(n).max()
    rsv    = (df['close'] - low_n) / (high_n - low_n + 1e-10) * 100
    K = pd.Series(index=df.index, dtype=float)
    D = pd.Series(index=df.index, dtype=float)
    K.iloc[0] = 50
    D.iloc[0] = 50
    for i in range(1, len(df)):
        K.iloc[i] = 2/3 * K.iloc[i-1] + 1/3 * rsv.iloc[i]
        D.iloc[i] = 2/3 * D.iloc[i-1] + 1/3 * K.iloc[i]
    J = 3 * K - 2 * D
    return K, D, J

def calc_boll(df, w=20):
    mid  = df['close'].rolling(w).mean()
    std  = df['close'].rolling(w).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return upper, mid, lower

def calc_atr(df, n=14):
    h   = df['high']
    l   = df['low']
    pc  = df['close'].shift(1)
    tr  = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=n, min_periods=n).mean()
    return atr

def calc_obv(df):
    diff = df['close'].diff()
    sign = np.sign(diff)
    obv  = (sign * df['volume']).cumsum()
    return obv

def compute_indicators(df):
    close = df['close']
    n = len(df)

    out = pd.DataFrame({'date': df['date']})

    # MA5/10/20/30
    for w in [5, 10, 20, 30]:
        out[f'ma{w}'] = calc_ma(df, w)

    # EMA12/26
    out['ema12'] = calc_ema(df, 12)
    out['ema26'] = calc_ema(df, 26)

    # MACD
    dif, dea, hist = calc_macd(df)
    out['macd_dif']  = dif
    out['macd_dea']  = dea
    out['macd_hist'] = hist

    # RSI
    out['rsi'] = calc_rsi(df)

    # KDJ
    K, D, J = calc_kdj(df)
    out['kdj_K'] = K
    out['kdj_D'] = D
    out['kdj_J'] = J

    # Bollinger
    upper, mid, lower = calc_boll(df)
    out['boll_upper'] = upper
    out['boll_mid']   = mid
    out['boll_lower'] = lower

    # ATR
    out['atr'] = calc_atr(df)

    # OBV
    out['obv'] = calc_obv(df)

    # 补充原始价量
    out['open']   = df['open']
    out['high']   = df['high']
    out['low']    = df['low']
    out['close']  = close
    out['volume'] = df['volume']

    out.dropna(how='all', inplace=True)
    return out

# ── 单只股票处理 ─────────────────────────────────────────────────────────────
def process_one(code):
    stock_file  = STOCK_DIR / f'{code}.csv'
    tech_file   = OUT_DIR  / f'{code}.csv'

    try:
        df_stock = read_stock(stock_file)
    except Exception as e:
        return code, False, f'read error: {e}'

    latest_stock_date = df_stock['date'].max()

    need_update = False
    if not tech_file.exists():
        need_update = True
    else:
        try:
            df_tech = pd.read_csv(tech_file, usecols=['date'])
            tech_dates = pd.to_datetime(df_tech['date'])
            latest_tech_date = tech_dates.max()
            if latest_stock_date > latest_tech_date:
                need_update = True
        except Exception:
            need_update = True

    if not need_update:
        return code, False, 'up-to-date'

    try:
        df_indicators = compute_indicators(df_stock)
        df_indicators.to_csv(tech_file, index=False)
        return code, True, f'updated ({len(df_indicators)} rows)'
    except Exception as e:
        return code, False, f'calc error: {e}'

# ── 主流程 ───────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    stock_files = sorted(STOCK_DIR.glob('*.csv'))
    codes = [f.stem for f in stock_files]

    print(f'[*] 发现 {len(codes)} 只股票，使用 {WORKERS} 个 worker')

    updated  = []
    skipped  = []
    errors   = []

    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(process_one, code): code for code in codes}
        done = 0
        for future in as_completed(futures):
            code, ok, msg = future.result()
            done += 1
            if ok:
                updated.append(code)
                print(f'  [U] {code}: {msg}')
            elif msg == 'up-to-date':
                skipped.append(code)
            else:
                errors.append((code, msg))
                print(f'  [E] {code}: {msg}')
            if done % 500 == 0:
                print(f'  ... 已处理 {done}/{len(codes)}')

    print(f'\n✅ 更新: {len(updated)}  |  跳过: {len(skipped)}  |  错误: {len(errors)}')
    if errors:
        for code, e in errors:
            print(f'   [{code}] {e}')

if __name__ == '__main__':
    main()
