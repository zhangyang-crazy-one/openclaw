#!/usr/bin/env python3
"""
行为金融学 - 多维度舆情分析 v2
包含：市场数据 + 论坛舆情 + 新闻情绪
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
        'sz_change': float(latest['深证-涨跌幅']),
        'main_money': float(latest['主力净流入-净额']),
        'main_ratio': float(latest['主力净流入-净占比']),
        'zt_count': zt_count
    }

def get_news_sentiment():
    """获取财经新闻情绪"""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    news_data = {
        'total': 0,
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'titles': []
    }
    
    try:
        url = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html"
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            titles = re.findall(r'"title":"([^"]+)"', resp.text)
            news_data['total'] = len(titles)
            news_data['titles'] = titles[:20]
            
            # 简单情感分析
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
                    
    except Exception as e:
        print(f"新闻获取失败: {e}")
    
    return news_data

def get_forum_buzz():
    """获取论坛讨论热度"""
    # 这里可以扩展雪球、股吧等API
    # 目前返回占位数据
    return {
        'xueqiu': '需要登录cookie',
        'guba': '需要爬虫',
        'weibo': '需要认证'
    }

def analyze_sentiment(market_data, news_data):
    """综合分析"""
    
    # ===== 1. 资金面 (25%) =====
    mr = market_data['main_ratio']
    if mr > 5: money_score, money_sig = 90, "贪婪"
    elif mr > 0: money_score, money_sig = 65, "中性偏多"
    elif mr > -3: money_score, money_sig = 45, "中性偏空"
    elif mr > -8: money_score, money_sig = 25, "恐惧"
    else: money_score, money_sig = 10, "极度恐惧"
    
    # ===== 2. 涨跌面 (15%) =====
    change = market_data['sh_change']
    if change > 3: price_score, price_sig = 85, "过热"
    elif change > 1: price_score, price_sig = 65, "偏多"
    elif change > -1: price_score, price_sig = 50, "中性"
    elif change > -3: price_score, price_sig = 35, "偏空"
    else: price_score, price_sig = 15, "恐慌"
    
    # ===== 3. 涨停情绪 (15%) =====
    zt = market_data['zt_count']
    if zt > 80: zt_score, zt_sig = 90, "亢奋"
    elif zt > 40: zt_score, zt_sig = 70, "活跃"
    elif zt > 20: zt_score, zt_sig = 50, "中性"
    elif zt > 10: zt_score, zt_sig = 35, "清淡"
    else: zt_score, zt_sig = 20, "冷清"
    
    # ===== 4. 新闻情绪 (25%) =====
    if news_data['total'] > 0:
        pos_ratio = news_data['positive'] / news_data['total']
        neg_ratio = news_data['negative'] / news_data['total']
        
        if pos_ratio > 0.5:
            news_score, news_sig = 80, "偏多"
        elif pos_ratio > neg_ratio:
            news_score, news_sig = 60, "中性偏多"
        elif neg_ratio > pos_ratio:
            news_score, news_sig = 40, "中性偏空"
        else:
            news_score, news_sig = 50, "中性"
    else:
        news_score, news_sig = 50, "未知"
    
    # ===== 5. 行为偏差 (20%) =====
    bias_score = 50
    biases = []
    
    if change < -3:
        bias_score -= 15
        biases.append("⚠️ 大跌可能触发损失厌恶")
    
    if mr > 5 and change > 2:
        bias_score -= 10
        biases.append("⚠️ 放量上涨警惕羊群效应")
    
    biases.append("💡 提醒：勿被成本锚定，以价值为锚")
    
    # ===== 综合 =====
    total = money_score*0.25 + price_score*0.15 + zt_score*0.15 + news_score*0.25 + bias_score*0.20
    
    return {
        'total': total,
        'money': (money_score, money_sig),
        'price': (price_score, price_sig),
        'zt': (zt_score, zt_sig),
        'news': (news_score, news_sig, news_data),
        'bias': (bias_score, biases)
    }

def main():
    print("="*70)
    print("行为金融学 - 多维度舆情分析 v2")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # 获取数据
    print("\n📥 数据采集中...")
    market_data = get_market_data()
    news_data = get_news_sentiment()
    
    print(f"  ✓ 市场数据")
    print(f"  ✓ 财经新闻 {news_data['total']}条")
    
    # 分析
    result = analyze_sentiment(market_data, news_data)
    
    # 输出
    print(f"\n📊 【市场数据】")
    print(f"  上证: {market_data['sh_change']:+.2f}%")
    print(f"  主力净流入: {market_data['main_money']/1e8:.1f}亿 ({market_data['main_ratio']:.2f}%)")
    print(f"  涨停: {market_data['zt_count']}家")
    
    print(f"\n📰 【新闻情绪】")
    print(f"  正面: {news_data['positive']} 负面: {news_data['negative']} 中性: {news_data['neutral']}")
    print(f"  热门标题:")
    for t in news_data['titles'][:5]:
        print(f"    • {t[:40]}")
    
    print(f"\n📈 【情绪分项】")
    print(f"  资金: {result['money'][0]}/100 ({result['money'][1]})")
    print(f"  涨跌: {result['price'][0]}/100 ({result['price'][1]})")
    print(f"  涨停: {result['zt'][0]}/100 ({result['zt'][1]})")
    print(f"  新闻: {result['news'][0]}/100 ({result['news'][1]})")
    
    print(f"\n🔍 【行为偏差】")
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
