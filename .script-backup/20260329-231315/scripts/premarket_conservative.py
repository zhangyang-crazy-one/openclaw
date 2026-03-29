#!/usr/bin/env python3
"""
开盘前保守策略分析 - RSI14 + 布林带下轨
分析用户自选股，生成买入/关注信号
"""

import baostock as bs
import pandas as pd
import json
import sys
from datetime import datetime

# 自选股列表
WATCHLIST = [
    ('300276', 'sz', '三丰智能'),
    ('300199', 'sz', '翰宇药业'),
    ('301381', 'sz', '待确认'),
    ('300502', 'sz', '新易盛'),
    ('300394', 'sz', '天孚通信'),
    ('300308', 'sz', '中际旭创'),
    ('300628', 'sz', '亿联网络'),
    ('300573', 'sz', '兴齐眼药'),
    ('300533', 'sz', '冰川网络'),
    ('300274', 'sz', '阳光电源'),
    ('300251', 'sz', '光线传媒'),
    ('300604', 'sz', '长川科技'),
    ('300456', 'sz', '赛微电子'),
]

def calc_rsi(prices, period=14):
    """计算RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_bollinger(prices, period=20):
    """计算布林带"""
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    return sma, sma + 2*std, sma - 2*std

def analyze_stock(code, exchange, name):
    """分析单只股票"""
    full_code = f'{exchange}.{code}'
    
    rs = bs.query_history_k_data_plus(
        full_code,
        'date,close',
        start_date='2025-01-01',
        end_date=datetime.now().strftime('%Y-%m-%d'),
        frequency='d',
        adjustflag='3'
    )
    
    if rs is None:
        return None
    
    data = []
    while rs.next():
        data.append(rs.get_row_data())
    
    if len(data) < 50:
        return None
    
    df = pd.DataFrame(data, columns=['date', 'close'])
    df['close'] = pd.to_numeric(df['close'], errors='coerce').dropna()
    
    if len(df) < 20:
        return None
    
    # 计算指标
    rsi = calc_rsi(df['close'])
    rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    sma, upper, lower = calc_bollinger(df['close'])
    price = df['close'].iloc[-1]
    lower_val = lower.iloc[-1] if not pd.isna(lower.iloc[-1]) else price
    
    # 保守策略判断
    signal = '观望'
    if rsi_val < 20 and price <= lower_val * 1.05:
        signal = '买入'
    elif rsi_val < 20:
        signal = '关注-接近下轨'
    elif rsi_val < 30:
        signal = '关注-超卖'
    
    return {
        'name': name,
        'code': code,
        'rsi14': round(rsi_val, 1),
        'price': round(price, 2),
        'lower': round(lower_val, 2),
        'signal': signal
    }

def main():
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        sys.exit(1)
    
    results = []
    for code, exchange, name in WATCHLIST:
        result = analyze_stock(code, exchange, name)
        if result:
            results.append(result)
    
    bs.logout()
    
    # 排序输出
    results.sort(key=lambda x: x['rsi14'])
    
    # 统计
    buy = [r for r in results if r['signal'] == '买入']
    watch = [r for r in results if '关注' in r['signal']]
    
    # 输出
    print("=" * 65)
    print("用户自选股保守策略分析 (RSI14 + 布林带)")
    print("=" * 65)
    print(f"{'股票':<10} {'代码':<8} {'RSI14':<8} {'价格':<10} {'布林下轨':<10} {'信号'}")
    print('-' * 65)
    for r in results:
        print(f"{r['name']:<10} {r['code']:<8} {r['rsi14']:<8} {r['price']:<10} {r['lower']:<10} {r['signal']}")
    
    print(f"\n📈 买入(RSI<20+布林下轨): {len(buy)}只")
    for r in buy:
        print(f"  ✅ {r['name']} RSI14={r['rsi14']}")
    
    print(f"\n👀 关注(RSI<30): {len(watch)}只")
    for r in watch:
        print(f"  ⚠️ {r['name']} RSI14={r['rsi14']} - {r['signal']}")
    
    if not buy and not watch:
        print("\n🏷️ 保守策略今日无信号，等待买入时机")
    
    # 保存JSON报告
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'strategy': '保守策略: RSI14<20 + 布林带下轨',
        'results': results,
        'summary': {'buy': len(buy), 'watch': len(watch)}
    }
    
    filename = f'/home/liujerry/金融数据/reports/premarket_conservative_{datetime.now().strftime("%Y%m%d")}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {filename}")
    return report

if __name__ == '__main__':
    main()
