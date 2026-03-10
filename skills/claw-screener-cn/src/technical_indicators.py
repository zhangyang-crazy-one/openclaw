"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional


def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 Williams %R
    
    Formula: WR = (Highest High - Close) / (Highest High - Lowest Low) * -100
    
    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 计算周期
    
    Returns:
        Williams %R 值序列
    """
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    diff = highest_high - lowest_low
    diff = diff.replace(0, np.nan)  # 避免除零
    
    wr = ((highest_high - close) / diff) * -100
    
    return wr


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI (相对强弱指数)
    
    Formula: RSI = 100 - (100 / (1 + RS))
    RS = 平均涨幅 / 平均跌幅
    
    Args:
        prices: 价格序列
        period: 计算周期
    
    Returns:
        RSI 值序列
    """
    delta = prices.diff()
    
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算布林带
    
    Args:
        prices: 价格序列
        period: 移动平均周期
        std_dev: 标准差倍数
    
    Returns:
        (中轨, 上轨, 下轨)
    """
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return middle, upper, lower


def calculate_ma(prices: pd.Series, period: int = 5) -> pd.Series:
    """计算移动平均线"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int = 12) -> pd.Series:
    """计算指数移动平均线"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算 MACD
    
    Args:
        prices: 价格序列
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    
    Returns:
        (DIF, DEA, MACD柱)
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2
    
    return dif, dea, macd


def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算 KDJ 指标
    
    Args:
        high: 最高价
        low: 最低价
        close: 收盘价
        period: 周期
    
    Returns:
        (K, D, J)
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    rsv = rsv.fillna(50)
    
    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = 3 * k - 2 * d
    
    return k, d, j


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算 OBV (能量潮)
    
    Args:
        close: 收盘价
        volume: 成交量
    
    Returns:
        OBV 值序列
    """
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def interpret_williams_r(value: float) -> str:
    """
    解读 Williams %R
    
    Args:
        value: Williams %R 值
    
    Returns:
        解读字符串
    """
    if pd.isna(value):
        return "无信号"
    elif value <= -80:
        return "超卖 - 可能反弹"
    elif value >= -20:
        return "超买 - 可能回调"
    else:
        return "中性"


def interpret_rsi(value: float) -> str:
    """
    解读 RSI
    
    Args:
        value: RSI 值
    
    Returns:
        解读字符串
    """
    if pd.isna(value):
        return "无信号"
    elif value >= 70:
        return "超买 - 风险较高"
    elif value <= 30:
        return "超卖 - 可能反弹"
    elif value >= 50:
        return "偏强"
    else:
        return "偏弱"


def get_oversold_stocks(df: pd.DataFrame, threshold: float = -80) -> bool:
    """
    判断是否超卖
    
    Args:
        df: 包含 williams_r 列的 DataFrame
        threshold: 超卖阈值
    
    Returns:
        True if oversold
    """
    if 'williams_r' not in df.columns:
        return False
    
    latest_wr = df['williams_r'].iloc[-1]
    return pd.notna(latest_wr) and latest_wr <= threshold


if __name__ == "__main__":
    # 测试
    import pandas as pd
    
    # 模拟数据
    np.random.seed(42)
    n = 100
    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(n) * 2)
    high = prices + np.random.rand(n) * 5
    low = prices - np.random.rand(n) * 5
    
    df = pd.DataFrame({
        'close': prices,
        'high': high,
        'low': low,
    })
    
    # 计算指标
    df['williams_r'] = calculate_williams_r(df['high'], df['low'], df['close'])
    df['rsi'] = calculate_rsi(df['close'])
    df['ma5'] = calculate_ma(df['close'], 5)
    df['ma20'] = calculate_ma(df['close'], 20)
    df['upper'], df['middle'], df['lower'] = calculate_bollinger_bands(df['close'])
    
    print(df.tail(10))
    print(f"\n最新 Williams %R: {df['williams_r'].iloc[-1]:.2f}")
    print(f"最新 RSI: {df['rsi'].iloc[-1]:.2f}")
    print(f"解读: {interpret_williams_r(df['williams_r'].iloc[-1])}")
