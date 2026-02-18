#!/usr/bin/env python3
"""
行为金融学市场情绪分析
基于行为金融学理论，使用真实市场数据分析投资者行为偏差
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_market_sentiment():
    """获取真实市场情绪数据"""
    # 1. 主力资金流向
    fund_flow = ak.stock_market_fund_flow()
    latest = fund_flow.iloc[-1]
    
    # 2. 涨跌停数据
    date_str = datetime.now().strftime('%Y%m%d')
    try:
        zt_pool = ak.stock_zt_pool_em(date=date_str)
        zt_count = len(zt_pool)
    except:
        zt_count = 0
    
    return {
        'date': latest['日期'],
        'sh_change': float(latest['上证-涨跌幅']),
        'sz_change': float(latest['深证-涨跌幅']),
        'main_money': float(latest['主力净流入-净额']),
        'main_ratio': float(latest['主力净流入-净占比']),
        'zt_count': zt_count
    }

def calculate_sentiment_score(data):
    """计算情绪评分"""
    # 资金情绪 (30%)
    main_ratio = data['main_ratio']
    if main_ratio > 5:
        money_score = 80
    elif main_ratio > 0:
        money_score = 60
    elif main_ratio > -3:
        money_score = 40
    else:
        money_score = 20
    
    # 涨跌情绪 (30%)
    change = data['sh_change']
    if change > 2:
        price_score = 80
    elif change > 0:
        price_score = 60
    elif change > -2:
        price_score = 40
    else:
        price_score = 20
    
    # 涨停情绪 (20%)
    zt = data['zt_count']
    if zt > 50:
        zt_score = 80
    elif zt > 20:
        zt_score = 60
    elif zt > 10:
        zt_score = 40
    else:
        zt_score = 20
    
    # 波动情绪 (20%)
    volatility = abs(change)
    if volatility > 3:
        vol_score = 80
    elif volatility > 1.5:
        vol_score = 50
    else:
        vol_score = 30
    
    total = money_score * 0.3 + price_score * 0.3 + zt_score * 0.2 + vol_score * 0.2
    return total, money_score, price_score, zt_score, vol_score

def get_sentiment_label(score):
    """获取情绪标签"""
    if score < 25:
        return "极度恐惧", "分批建仓机会"
    elif score < 45:
        return "恐惧", "保持谨慎"
    elif score < 55:
        return "中性", "均衡配置"
    elif score < 75:
        return "贪婪", "逐步减仓"
    else:
        return "极度贪婪", "清仓观望"

def main():
    print(f"\n{'='*70}")
    print(f"行为金融学市场情绪分析 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")
    
    # 获取真实市场数据
    data = get_market_sentiment()
    
    # 计算情绪评分
    score, money_score, price_score, zt_score, vol_score = calculate_sentiment_score(data)
    
    # 获取情绪标签
    if score < 25:
        label, advice = "极度恐惧", "分批建仓，逆向投资机会"
    elif score < 45:
        label, advice = "恐惧", "保持谨慎，观望为主"
    elif score < 55:
        label, advice = "中性", "均衡配置"
    elif score < 75:
        label, advice = "贪婪", "逐步减仓，锁定利润"
    else:
        label, advice = "极度贪婪", "清仓观望，风险极大"
    
    print(f"\n📊 真实市场数据:")
    print(f"  日期: {data['date']}")
    print(f"  上证: {data['sh_change']:+.2f}%")
    print(f"  深证: {data['sz_change']:+.2f}%")
    print(f"  主力净流入: {data['main_money']/1e8:.1f}亿 ({data['main_ratio']:.2f}%)")
    print(f"  涨停家数: {data['zt_count']}")
    
    print(f"\n📈 情绪评分:")
    print(f"  资金情绪: {money_score}/100 (权重30%)")
    print(f"  涨跌情绪: {price_score}/100 (权重30%)")
    print(f"  涨停情绪: {zt_score}/100 (权重20%)")
    print(f"  波动情绪: {vol_score}/100 (权重20%)")
    
    print(f"\n{'='*50}")
    print(f"【综合情绪评分】: {score:.0f}/100")
    print(f"【情绪状态】: {label}")
    print(f"【投资建议】: {advice}")
    
    # 行为偏差检测
    print(f"\n🔍 行为偏差检测:")
    if data['main_ratio'] < -3:
        print(f"  ⚠️ 主力资金大幅流出 - 存在羊群效应")
    if data['sh_change'] < -3:
        print(f"  ⚠️ 恐慌性下跌 - 可能触发损失厌恶")
    if data['zt_count'] > 50 and data['sh_change'] > 2:
        print(f"  ⚠️ 放量涨停+过热 - 追高风险")
    
    print(f"\n{'='*70}")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'score': score,
        'label': label,
        'advice': advice,
        'data': data
    }

if __name__ == "__main__":
    main()
