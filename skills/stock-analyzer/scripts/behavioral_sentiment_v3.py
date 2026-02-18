#!/usr/bin/env python3
"""
行为金融学 - 多维度舆情分析 v3
包含：市场数据 + 新闻情绪 + 板块舆情
"""
import akshare as ak
import requests
import pandas as pd
from datetime import datetime
import re

def get_market_data():
    """获取市场数据"""
    fund_flow = ak.stock_market_fund_flow()
    latest = fund_flow.iloc[-1]
    
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        zt = ak.stock_zt_pool_em(date=date_str)
        zt_count = len(zt)
    except:
        zt_count = 0
    
    return {
        'date': latest['日期'],
        'sh_change': float(latest['上证-涨跌幅']),
        'main_money': float(latest['主力净流入-净额']),
        'main_ratio': float(latest['主力净流入-净占比']),
        'zt_count': zt_count
    }

def get_board_sentiment():
    """获取板块舆情（反映论坛讨论热点）"""
    concept = ak.stock_board_industry_name_em()
    
    up_count = (concept['涨跌幅'] > 0).sum()
    down_count = (concept['涨跌幅'] < 0).sum()
    total = len(concept)
    
    # 最强/最弱板块
    top_up = concept.nlargest(3, '涨跌幅')
    top_down = concept.nsmallest(3, '涨跌幅')
    
    return {
        'total': total,
        'up': up_count,
        'down': down_count,
        'up_ratio': up_count / total,
        'top_up': top_up[['板块名称', '涨跌幅']].values.tolist(),
        'top_down': top_down[['板块名称', '涨跌幅']].values.tolist()
    }

def get_news_sentiment():
    """获取财经新闻情绪"""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    news_data = {'positive': 0, 'negative': 0, 'neutral': 0, 'titles': []}
    
    try:
        url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            titles = re.findall(r'"title":"([^"]+)"', resp.text)
            news_data['titles'] = titles[:15]
            
            positive_words = ['涨','升','利好','增长','突破','新高','牛市','反弹','看涨','抢眼']
            negative_words = ['跌','降','利空','下滑','暴跌','新低','熊市','跳水','看跌','风险']
            
            for t in titles:
                has_pos = any(w in t for w in positive_words)
                has_neg = any(w in t for w in negative_words)
                
                if has_pos and not has_neg:
                    news_data['positive'] += 1
                elif has_neg and not has_pos:
                    news_data['negative'] += 1
                else:
                    news_data['neutral'] += 1
    except:
        pass
    
    return news_data

def analyze(market, board, news):
    """综合分析"""
    
    # 1. 资金面 (20%)
    mr = market['main_ratio']
    if mr > 5: money = 90, "贪婪"
    elif mr > 0: money = 65, "中性偏多"
    elif mr > -3: money = 45, "中性偏空"
    else: money = 25, "恐惧"
    
    # 2. 涨跌 (15%)
    change = market['sh_change']
    if change > 2: price = 85, "过热"
    elif change > 0: price = 65, "偏多"
    elif change > -2: price = 45, "偏空"
    else: price = 25, "恐慌"
    
    # 3. 涨停 (10%)
    zt = market['zt_count']
    if zt > 50: zt_score = 80, "活跃"
    elif zt > 20: zt_score = 55, "中性"
    else: zt_score = 35, "清淡"
    
    # 4. 板块舆情 (25%) - 反映论坛讨论热点
    up_ratio = board['up_ratio']
    if up_ratio > 0.7: board_s = 85, "亢奋"
    elif up_ratio > 0.5: board_s = 65, "偏多"
    elif up_ratio > 0.3: board_s = 50, "分化"
    elif up_ratio > 0.15: board_s = 40, "偏空"
    else: board_s = 25, "恐慌"
    
    # 5. 新闻情绪 (15%)
    if news['positive'] + news['negative'] > 0:
        pos_ratio = news['positive'] / (news['positive'] + news['negative'])
        if pos_ratio > 0.6: news_s = 75, "偏多"
        elif pos_ratio > 0.4: news_s = 55, "中性"
        elif pos_ratio > 0.3: news_s = 40, "偏空"
        else: news_s = 30, "偏空"
    else:
        news_s = 50, "中性"
    
    # 6. 行为偏差 (15%)
    bias_score = 50
    biases = []
    if change < -2:
        bias_score -= 10
        biases.append("⚠️ 大跌触发损失厌恶")
    if mr < -3 and change < 0:
        bias_score -= 10
        biases.append("⚠️ 主力流出+下跌=羊群效应")
    if up_ratio < 0.2:
        bias_score -= 10
        biases.append("⚠️ 板块普跌，市场情绪低迷")
    biases.append("💡 提醒：以价值为锚，勿被成本锚定")
    
    # 综合
    total = money[0]*0.20 + price[0]*0.15 + zt_score[0]*0.10 + board_s[0]*0.25 + news_s[0]*0.15 + bias_score*0.15
    
    return {
        'total': total,
        'money': money,
        'price': price,
        'zt': zt_score,
        'board': board_s,
        'news': news_s,
        'bias': (bias_score, biases)
    }

def main():
    print("="*70)
    print("行为金融学 - 多维度舆情分析 v3")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    print("\n📥 数据采集中...")
    
    market = get_market_data()
    board = get_board_sentiment()
    news = get_news_sentiment()
    
    print("  ✓ 市场数据")
    print("  ✓ 板块舆情")
    print("  ✓ 财经新闻")
    
    result = analyze(market, board, news)
    
    # 输出
    print(f"\n📊 【市场数据】")
    print(f"  上证: {market['sh_change']:+.2f}%")
    print(f"  主力净流入: {market['main_money']/1e8:.1f}亿 ({market['main_ratio']:.2f}%)")
    print(f"  涨停: {market['zt_count']}家")
    
    print(f"\n📊 【板块舆情】（反映论坛讨论热点）")
    print(f"  上涨板块: {board['up']}个 ({board['up_ratio']*100:.1f}%)")
    print(f"  下跌板块: {board['down']}个 ({(1-board['up_ratio'])*100:.1f}%)")
    print(f"  热点话题:")
    for name, change in board['top_up'][:3]:
        print(f"    🔥 {name}: {change:.2f}%")
    for name, change in board['top_down'][:3]:
        print(f"    ❄️ {name}: {change:.2f}%")
    
    print(f"\n📰 【新闻情绪】")
    print(f"  正面: {news['positive']}  负面: {news['negative']}  中性: {news['neutral']}")
    
    print(f"\n📈 【情绪分项】")
    print(f"  资金: {result['money'][0]}/100 ({result['money'][1]})")
    print(f"  涨跌: {result['price'][0]}/100 ({result['price'][1]})")
    print(f"  涨停: {result['zt'][0]}/100 ({result['zt'][1]})")
    print(f"  板块: {result['board'][0]}/100 ({result['board'][1]})")
    print(f"  新闻: {result['news'][0]}/100 ({result['news'][1]})")
    
    print(f"\n🔍 【行为偏差检测】")
    for b in result['bias'][1]:
        print(f"  {b}")
    
    print(f"\n{'='*50}")
    
    score = result['total']
    if score < 25:
        label, advice = "极度恐惧", "分批建仓"
    elif score < 40:
        label, advice = "恐惧", "保持谨慎"
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

if __name__ == "__main__":
    main()
