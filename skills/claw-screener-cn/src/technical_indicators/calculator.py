"""
A股技术指标批量计算脚本
计算: MA, EMA, MACD, RSI, Bollinger Bands, KDJ, Williams %R
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

# 尝试导入tqdm用于进度条
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# 路径配置
STOCKS_DIR = Path.home() / "金融数据" / "stocks"
OUTPUT_DIR = Path.home() / "金融数据" / "technical_indicators"


def calculate_ma(close: pd.Series, period: int) -> pd.Series:
    """计算移动平均线"""
    return close.rolling(window=period, min_periods=1).mean()


def calculate_ema(close: pd.Series, period: int) -> pd.Series:
    """计算指数移动平均线"""
    return close.ewm(span=period, adjust=False, min_periods=1).mean()


def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    计算MACD指标
    Returns: DIF, DEA, HIST
    """
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = calculate_ema(dif, signal)
    hist = 2 * (dif - dea)
    return dif, dea, hist


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """计算RSI相对强弱指标"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=1).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=1).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    # 确保RSI在[0, 100]范围内，防止浮点数边界溢出
    rsi = rsi.clip(lower=0, upper=100)
    # avg_loss为0时rs为nan，填充为100（全是上涨）
    rsi = rsi.fillna(100)
    return rsi


def calculate_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0):
    """
    计算布林带
    Returns: upper, middle, lower
    """
    middle = calculate_ma(close, period)
    std = close.rolling(window=period, min_periods=1).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, 
                   n: int = 9, m1: int = 3, m2: int = 3):
    """
    计算KDJ随机指标
    Returns: K, D, J
    """
    lowest_low = low.rolling(window=n, min_periods=1).min()
    highest_high = high.rolling(window=n, min_periods=1).max()
    
    rsv = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    
    K = pd.Series(index=close.index, dtype=float)
    D = pd.Series(index=close.index, dtype=float)
    
    K.iloc[0] = 50.0
    D.iloc[0] = 50.0
    
    for i in range(1, len(close)):
        K.iloc[i] = (2/3) * K.iloc[i-1] + (1/3) * rsv.iloc[i]
        D.iloc[i] = (2/3) * D.iloc[i-1] + (1/3) * K.iloc[i]
    
    J = 3 * K - 2 * D
    return K, D, J


def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, 
                         period: int = 14) -> pd.Series:
    """
    计算Williams %R威廉指标
    """
    highest_high = high.rolling(window=period, min_periods=1).max()
    lowest_low = low.rolling(window=period, min_periods=1).min()
    
    wr = -100 * (highest_high - close) / (highest_high - lowest_low).replace(0, np.nan)
    return wr


def calculate_psy(close: pd.Series, period: int = 12) -> pd.Series:
    """
    计算PSY心理线指标
    """
    change = close.diff()
    up_count = (change > 0).rolling(window=period, min_periods=1).sum()
    psy = 100 * up_count / period
    return psy


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算OBV能量潮指标
    """
    direction = np.sign(close.diff())
    obv = (direction.fillna(0) * volume).cumsum()
    return obv


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, 
                   period: int = 14) -> pd.Series:
    """
    计算ATR平均真实波幅
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False, min_periods=1).mean()
    return atr


def process_single_stock(filepath: str) -> dict:
    """
    处理单只股票，计算所有技术指标
    Returns: dict with stock_code and status
    """
    try:
        stock_code = Path(filepath).stem
        df = pd.read_csv(filepath)
        
        if len(df) < 5:
            return {"code": stock_code, "status": "skipped", "reason": "数据太少"}
        
        # 确保数据按日期升序排列
        df = df.sort_values('date').reset_index(drop=True)
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # ====== 计算所有技术指标 ======
        
        # 移动平均线
        df['MA5'] = calculate_ma(close, 5)
        df['MA10'] = calculate_ma(close, 10)
        df['MA20'] = calculate_ma(close, 20)
        df['MA60'] = calculate_ma(close, 60)
        df['MA120'] = calculate_ma(close, 120)
        df['MA250'] = calculate_ma(close, 250)
        
        # 指数移动平均线
        df['EMA12'] = calculate_ema(close, 12)
        df['EMA26'] = calculate_ema(close, 26)
        
        # MACD
        df['MACD_DIF'], df['MACD_DEA'], df['MACD_HIST'] = calculate_macd(close)
        
        # RSI
        df['RSI6'] = calculate_rsi(close, 6)
        df['RSI14'] = calculate_rsi(close, 14)
        df['RSI24'] = calculate_rsi(close, 24)
        
        # 布林带
        df['BB_UPPER'], df['BB_MIDDLE'], df['BB_LOWER'] = calculate_bollinger_bands(close)
        df['BB_WIDTH'] = (df['BB_UPPER'] - df['BB_LOWER']) / df['BB_MIDDLE']
        df['BB_POSITION'] = (close - df['BB_LOWER']) / (df['BB_UPPER'] - df['BB_LOWER'])
        
        # KDJ
        df['KDJ_K'], df['KDJ_D'], df['KDJ_J'] = calculate_kdj(high, low, close)
        
        # Williams %R
        df['WR14'] = calculate_williams_r(high, low, close, 14)
        df['WR28'] = calculate_williams_r(high, low, close, 28)
        
        # PSY
        df['PSY12'] = calculate_psy(close, 12)
        df['PSY24'] = calculate_psy(close, 24)
        
        # OBV
        df['OBV'] = calculate_obv(close, volume)
        
        # ATR
        df['ATR14'] = calculate_atr(high, low, close, 14)
        
        # 涨跌停标志
        df['LIMIT_UP'] = ((close / close.shift(1) - 1) * 100).round(2)
        df['IS_LIMIT_UP'] = df['LIMIT_UP'] >= 9.9
        df['IS_LIMIT_DOWN'] = df['LIMIT_UP'] <= -9.9
        
        # 成交量变化
        df['VOL_CHANGE'] = ((volume / volume.shift(1) - 1) * 100).round(2)
        
        # ====== 保存结果 ======
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{stock_code}.csv"
        df.to_csv(output_path, index=False, float_format='%.4f')
        
        return {
            "code": stock_code, 
            "status": "success", 
            "rows": len(df),
            "latest_date": df['date'].iloc[-1]
        }
        
    except Exception as e:
        stock_code = Path(filepath).stem
        return {"code": stock_code, "status": "error", "reason": str(e)}


def batch_process_stocks(max_workers: int = 8, batch_size: int = 1000):
    """
    批量处理所有股票数据
    """
    stock_files = sorted(STOCKS_DIR.glob("*.csv"))
    total = len(stock_files)
    
    print(f"\n{'='*60}")
    print(f"📊 A股技术指标批量计算")
    print(f"{'='*60}")
    print(f"股票数量: {total}")
    print(f"并发数: {max_workers}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'='*60}\n")
    
    results = {"success": 0, "error": 0, "skipped": 0}
    errors = []
    
    if HAS_TQDM:
        iterator = tqdm(stock_files, desc="计算技术指标", unit="只")
    else:
        iterator = stock_files
    
    # 分批处理以避免内存问题
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch_files = stock_files[batch_start:batch_end]
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_stock, str(f)): f for f in batch_files}
            
            for future in as_completed(futures):
                result = future.result()
                if result["status"] == "success":
                    results["success"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["error"] += 1
                    errors.append(result)
        
        if HAS_TQDM:
            print(f"  批次 {batch_start//batch_size + 1}: {batch_end}/{total} 完成")
    
    # 打印结果摘要
    print(f"\n{'='*60}")
    print(f"📋 计算完成!")
    print(f"{'='*60}")
    print(f"✅ 成功: {results['success']} 只")
    print(f"⏭️  跳过: {results['skipped']} 只")
    print(f"❌ 失败: {results['error']} 只")
    
    if errors:
        print(f"\n失败股票 (前10只):")
        for e in errors[:10]:
            print(f"  {e['code']}: {e['reason']}")
    
    # 保存失败列表
    if errors:
        error_log = OUTPUT_DIR / "errors.txt"
        with open(error_log, 'w') as f:
            for e in errors:
                f.write(f"{e['code']}: {e['reason']}\n")
        print(f"\n失败列表已保存: {error_log}")
    
    # 统计指标覆盖
    if OUTPUT_DIR.exists():
        output_files = list(OUTPUT_DIR.glob("*.csv"))
        if output_files:
            sample = pd.read_csv(output_files[0])
            indicators = [col for col in sample.columns if col not in 
                         ['date', 'open', 'high', 'low', 'close', 'volume']]
            print(f"\n📈 计算的指标 ({len(indicators)}个):")
            print(f"   {', '.join(indicators)}")
    
    print(f"\n💾 数据已保存到: {OUTPUT_DIR}")
    return results


def update_single_stock(stock_code: str):
    """
    更新单只股票的技术指标 (用于增量更新)
    """
    filepath = STOCKS_DIR / f"{stock_code}.csv"
    if filepath.exists():
        return process_single_stock(str(filepath))
    return {"code": stock_code, "status": "error", "reason": "文件不存在"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A股技术指标批量计算")
    parser.add_argument("-w", "--workers", type=int, default=8, 
                        help="并发进程数 (默认: 8)")
    parser.add_argument("-b", "--batch-size", type=int, default=1000,
                        help="批处理大小 (默认: 1000)")
    parser.add_argument("-s", "--stock", type=str, default=None,
                        help="单只股票代码 (用于单只更新)")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅检查不计算")
    
    args = parser.parse_args()
    
    if args.dry_run:
        # 干跑模式: 仅检查数据情况
        stock_files = list(STOCKS_DIR.glob("*.csv"))
        print(f"K线数据检查:")
        print(f"  总股票数: {len(stock_files)}")
        
        if stock_files:
            sample = pd.read_csv(stock_files[0])
            print(f"  字段: {', '.join(sample.columns)}")
            print(f"  样本行数: {len(sample)}")
            print(f"  日期范围: {sample['date'].iloc[0]} ~ {sample['date'].iloc[-1]}")
        
        # 检查已有技术指标
        if OUTPUT_DIR.exists():
            tech_files = list(OUTPUT_DIR.glob("*.csv"))
            print(f"\n技术指标数据:")
            print(f"  已计算股票数: {len(tech_files)}")
            if tech_files:
                sample = pd.read_csv(tech_files[0])
                tech_cols = [c for c in sample.columns if c not in 
                            ['date', 'open', 'high', 'low', 'close', 'volume']]
                print(f"  指标字段: {', '.join(tech_cols)}")
        else:
            print(f"\n技术指标数据: 尚未计算")
    else:
        if args.stock:
            # 单只更新
            result = update_single_stock(args.stock)
            print(f"更新结果: {result}")
        else:
            # 全量计算
            batch_process_stocks(max_workers=args.workers, batch_size=args.batch_size)
