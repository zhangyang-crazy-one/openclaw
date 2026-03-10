#!/usr/bin/env python3
"""
A股股票筛选器 - 使用本地数据
分析用户13只自选股
"""
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# 自选股列表
WATCHLIST = [
    ('300276', '三丰智能'),
    ('300199', '翰宇药业'),
    ('301381', '待确认'),
    ('300502', '新易盛'),
    ('300394', '天孚通信'),
    ('300308', '中际旭创'),
    ('300628', '亿联网络'),
    ('300573', '兴齐眼药'),
    ('300533', '冰川网络'),
    ('300274', '阳光电源'),
    ('300251', '光线传媒'),
    ('300604', '长川科技'),
    ('300456', '赛微电子'),
]

DATA_DIR = Path("/home/liujerry/金融数据/stocks_clean")


def calculate_williams_r(high, low, close, period=14):
    """计算 Williams %R"""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    diff = highest_high - lowest_low
    diff = diff.replace(0, pd.NA)
    wr = ((highest_high - close) / diff) * -100
    return wr


def calculate_rsi(prices, period=14):
    """计算 RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(prices, period=20, std_dev=2.0):
    """计算布林带"""
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return middle, upper, lower


def analyze_stock(code, name):
    """分析单只股票"""
    file_path = DATA_DIR / f"{code}.csv"
    
    if not file_path.exists():
        return {
            'code': code,
            'name': name,
            'error': '数据不存在'
        }
    
    try:
        df = pd.read_csv(file_path)
        
        # 确保有必要的列
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            return {
                'code': code,
                'name': name,
                'error': '数据格式错误'
            }
        
        # 转换日期
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 转换数值
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 只取最近90天数据
        df = df.tail(90)
        
        if len(df) < 30:
            return {
                'code': code,
                'name': name,
                'error': f'数据不足，仅{len(df)}天'
            }
        
        # 计算技术指标
        df['williams_r'] = calculate_williams_r(df['high'], df['low'], df['close'])
        df['rsi'] = calculate_rsi(df['close'])
        df['bb_middle'], df['bb_upper'], df['bb_lower'] = calculate_bollinger_bands(df['close'])
        
        # 获取最新数据
        latest = df.iloc[-1]
        
        price = latest['close']
        wr = latest['williams_r']
        rsi_val = latest['rsi']
        bb_lower = latest['bb_lower']
        
        # 判断信号
        signals = []
        score = 0
        
        # Williams %R 信号
        if pd.notna(wr):
            if wr <= -80:
                signals.append(("Williams %R", "超卖", "⭐⭐⭐买入信号"))
                score += 3
            elif wr <= -70:
                signals.append(("Williams %R", "接近超卖", "⭐⭐关注"))
                score += 1
            elif wr >= -20:
                signals.append(("Williams %R", "超买", "⚠️风险"))
        
        # RSI 信号
        if pd.notna(rsi_val):
            if rsi_val <= 30:
                signals.append(("RSI", "超卖", "⭐关注"))
            elif rsi_val >= 70:
                signals.append(("RSI", "超买", "⚠️风险"))
        
        # 布林带信号
        if pd.notna(bb_lower) and pd.notna(price):
            if price <= bb_lower * 1.03:
                signals.append(("布林带", "触及下轨", "⭐支撑位"))
                score += 1
            elif price <= bb_lower * 1.05:
                signals.append(("布林带", "接近下轨", "关注"))
        
        # 综合建议
        if score >= 4:
            recommendation = "🚀 强烈推荐买入"
        elif score >= 2:
            recommendation = "⭐ 建议关注"
        elif score >= 1:
            recommendation = "👀 观察"
        else:
            recommendation = "➡️ 观望"
        
        return {
            'code': code,
            'name': name,
            'price': round(price, 2) if pd.notna(price) else None,
            'williams_r': round(wr, 2) if pd.notna(wr) else None,
            'rsi': round(rsi_val, 2) if pd.notna(rsi_val) else None,
            'bb_lower': round(bb_lower, 2) if pd.notna(bb_lower) else None,
            'data_days': len(df),
            'signals': signals,
            'score': score,
            'recommendation': recommendation
        }
        
    except Exception as e:
        return {
            'code': code,
            'name': name,
            'error': str(e)
        }


def main():
    print("=" * 70)
    print("📊 A股自选股分析报告")
    print(f"   分析日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    results = []
    
    for code, name in WATCHLIST:
        result = analyze_stock(code, name)
        results.append(result)
    
    # 按分数排序
    results_with_score = [r for r in results if 'score' in r]
    results_with_score.sort(key=lambda x: x['score'], reverse=True)
    
    results_with_error = [r for r in results if 'error' in r]
    
    # 打印结果
    print("\n📈 符合买入条件的股票:")
    print("-" * 70)
    
    buy_candidates = [r for r in results_with_score if r['score'] >= 2]
    
    if buy_candidates:
        for r in buy_candidates:
            print(f"\n{r['code']} {r['name']}")
            print(f"   价格: {r['price']} | WR: {r['williams_r']} | RSI: {r['rsi']}")
            print(f"   布林下轨: {r['bb_lower']}")
            print(f"   分数: {r['score']}/5")
            print(f"   信号: {', '.join([s[2] for s in r['signals']])}")
            print(f"   ➡️ {r['recommendation']}")
    else:
        print("   无")
    
    print("\n\n📊 全部股票状态:")
    print("-" * 70)
    
    # 按分数排序显示
    for r in results_with_score:
        status = "✅" if r['score'] >= 2 else "➖"
        print(f"{status} {r['code']} {r['name']:8} | "
              f"价格:{r['price']:7} | WR:{r['williams_r']:6} | RSI:{r['rsi']:5} | "
              f"评分:{r['score']}")
    
    # 显示错误
    for r in results_with_error:
        print(f"❌ {r['code']} {r['name']}: {r['error']}")
    
    # 统计
    total = len(results)
    has_data = len(results_with_score)
    errors = len(results_with_error)
    buy_signals = len([r for r in results_with_score if r['score'] >= 2])
    
    print("\n" + "=" * 70)
    print("📈 统计:")
    print(f"   自选股总数: {total}")
    print(f"   有效数据: {has_data}")
    print(f"   缺失数据: {errors}")
    print(f"   买入信号: {buy_signals}")
    print("=" * 70)
    
    # 返回结果
    return results


if __name__ == "__main__":
    main()
