#!/usr/bin/env python3
"""
行为金融学 - 真实舆情分析
基于多维度数据源的真实市场情绪分析
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def get_sentiment_data():
    """获取多维度舆情数据"""
    
    # 1. 主力资金流向
    fund_flow = ak.stock_market_fund_flow()
    latest = fund_flow.iloc[-1]
    
    # 2. 概念板块涨跌
    concept = ak.stock_board_industry_name_em()
    
    # 3. 涨跌停
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        zt = ak.stock_zt_pool_em(date=date_str)
        zt_count = len(zt)
    except:
        zt_count = 0
    
    return {
        'date': latest['日期'],
        'sh_change': float(latest['上证-涨跌幅']),
        'sz_change': float(latest['深证-涨跌幅']),
        'main_money': float(latest['主力净流入-净额']),
        'main_ratio': float(latest['主力净流入-净占比']),
        'zt_count': zt_count,
        'concept_data': concept
    }

def analyze_sentiment(data):
    """综合分析市场情绪"""
    
    # ===== 1. 资金面分析 (25%) =====
    main_ratio = data['main_ratio']
    if main_ratio > 5:
        money_score = 90
        money_signal = "贪婪"
    elif main_ratio > 0:
        money_score = 65
        money_signal = "中性偏多"
    elif main_ratio > -3:
        money_score = 45
        money_signal = "中性偏空"
    elif main_ratio > -8:
        money_score = 25
        money_signal = "恐惧"
    else:
        money_score = 10
        money_signal = "极度恐惧"
    
    # ===== 2. 涨跌面分析 (20%) =====
    change = data['sh_change']
    if change > 3:
        price_score = 85
        price_signal = "过热"
    elif change > 1:
        price_score = 65
        price_signal = "偏多"
    elif change > -1:
        price_score = 50
        price_signal = "中性"
    elif change > -3:
        price_score = 35
        price_signal = "偏空"
    else:
        price_score = 15
        price_signal = "恐慌"
    
    # ===== 3. 涨停情绪 (15%) =====
    zt = data['zt_count']
    if zt > 80:
        zt_score = 90
        zt_signal = "极度亢奋"
    elif zt > 40:
        zt_score = 70
        zt_signal = "活跃"
    elif zt > 20:
        zt_score = 50
        zt_signal = "中性"
    elif zt > 10:
        zt_score = 35
        zt_signal = "清淡"
    else:
        zt_score = 20
        zt_signal = "冷清"
    
    # ===== 4. 板块情绪 (20%) =====
    concept = data['concept_data']
    if '涨跌幅' in concept.columns:
        avg_change = concept['涨跌幅'].mean()
        up_ratio = (concept['涨跌幅'] > 0).sum() / len(concept)
        
        if avg_change > 2 and up_ratio > 0.7:
            board_score = 85
            board_signal = "普涨"
        elif avg_change > 0.5 and up_ratio > 0.5:
            board_score = 65
            board_signal = "偏多"
        elif avg_change > -0.5:
            board_score = 50
            board_signal = "分化"
        elif avg_change > -2:
            board_score = 35
            board_signal = "偏空"
        else:
            board_score = 20
            board_signal = "普跌"
    else:
        board_score = 50
        board_signal = "未知"
    
    # ===== 5. 行为偏差检测 (20%) =====
    bias_score = 50
    biases = []
    
    # 处置效应检测 (大跌后不愿卖出)
    if change < -3:
        bias_score -= 20
        biases.append("⚠️ 大跌可能触发损失厌恶 - 投资者倾向于持有亏损股")
    
    # 羊群效应检测 (放量上涨时追高)
    if data['main_ratio'] > 5 and change > 2:
        bias_score -= 15
        biases.append("⚠️ 放量上涨存在羊群效应 - 谨慎追高")
    
    # 过度反应检测 (暴涨暴跌)
    if abs(change) > 4:
        bias_score -= 10
        biases.append("⚠️ 波动剧烈 - 警惕过度反应")
    
    # 锚定效应提醒
    biases.append("💡 提醒：勿被买入成本锚定，应以价值为锚")
    
    # ===== 综合评分 =====
    total_score = (
        money_score * 0.25 + 
        price_score * 0.20 + 
        zt_score * 0.15 + 
        board_score * 0.20 +
        bias_score * 0.20
    )
    
    return {
        'total': total_score,
        'money': (money_score, money_signal),
        'price': (price_score, price_signal),
        'zt': (zt_score, zt_signal),
        'board': (board_score, board_signal),
        'bias': (bias_score, biases)
    }

def main():
    print("="*70)
    print("行为金融学 - 多维度舆情分析")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # 获取数据
    data = get_sentiment_data()
    result = analyze_sentiment(data)
    
    # 输出结果
    print(f"\n📊 【市场数据】")
    print(f"  日期: {data['date']}")
    print(f"  上证: {data['sh_change']:+.2f}%")
    print(f"  深证: {data['sz_change']:+.2f}%")
    print(f"  主力净流入: {data['main_money']/1e8:.1f}亿 ({data['main_ratio']:.2f}%)")
    print(f"  涨停家数: {data['zt_count']}")
    
    print(f"\n📈 【情绪分项】")
    print(f"  资金情绪 ({result['money'][0]}/100): {result['money'][1]}")
    print(f"  涨跌情绪 ({result['price'][0]}/100): {result['price'][1]}")
    print(f"  涨停情绪 ({result['zt'][0]}/100): {result['zt'][1]}")
    print(f"  板块情绪 ({result['board'][0]}/100): {result['board'][1]}")
    
    print(f"\n🔍 【行为偏差】")
    for b in result['bias'][1]:
        print(f"  {b}")
    
    print(f"\n{'='*50}")
    
    # 总体评价
    score = result['total']
    if score < 25:
        label, advice = "极度恐惧", "分批建仓，逆向投资"
    elif score < 40:
        label, advice = "恐惧", "保持谨慎，观望为主"
    elif score < 55:
        label, advice = "中性", "均衡配置"
    elif score < 75:
        label, advice = "贪婪", "逐步减仓"
    else:
        label, advice = "极度贪婪", "清仓观望"
    
    print(f"【综合评分】: {score:.0f}/100")
    print(f"【情绪状态】: {label}")
    print(f"【投资建议】: {advice}")
    print("="*70)
    
    return result

if __name__ == "__main__":
    main()
