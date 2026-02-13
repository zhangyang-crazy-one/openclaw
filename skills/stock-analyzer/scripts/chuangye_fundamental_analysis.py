#!/usr/bin/env python3
"""
创业板基本面分析与选股系统
- 财务指标计算
- 估值分析
- 成长性评估
- 综合评分
"""
import os, sys, json, warnings
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import time
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHUANGYE_CODES = [str(i).zfill(6) for i in range(300000, 300999)]

def get_simulated_fundamentals(code):
    """生成模拟基本面数据"""
    np.random.seed(int(code))
    
    # 基于代码的差异化模拟
    seed = int(code) % 10
    if seed == 0:  # 绩优股
        base_pe = 25 + np.random.uniform(-5, 10)
        base_pb = 4 + np.random.uniform(-1, 2)
        base_growth = 25 + np.random.uniform(5, 15)
    elif seed == 1:  # 高成长
        base_pe = 45 + np.random.uniform(-10, 20)
        base_pb = 6 + np.random.uniform(-2, 4)
        base_growth = 40 + np.random.uniform(10, 20)
    elif seed == 2:  # 价值股
        base_pe = 18 + np.random.uniform(-3, 7)
        base_pb = 2.5 + np.random.uniform(-0.5, 1.5)
        base_growth = 8 + np.random.uniform(2, 8)
    elif seed == 3:  # 周期股
        base_pe = 30 + np.random.uniform(-10, 15)
        base_pb = 4 + np.random.uniform(-1, 3)
        base_growth = 15 + np.random.uniform(-10, 20)
    else:  # 一般股
        base_pe = 35 + np.random.uniform(-10, 20)
        base_pb = 5 + np.random.uniform(-2, 4)
        base_growth = 12 + np.random.uniform(-5, 15)
    
    return {
        'code': code,
        'name': f'创业板{code}',
        'pe': max(10, base_pe),
        'pb': max(1, base_pb),
        'ps': max(2, base_pb * 0.8),
        'market_cap': np.random.uniform(5, 500),
        'circulating_market_cap': np.random.uniform(3, 300),
        'roe': np.random.uniform(5, 25),
        'net_profit_margin': np.random.uniform(5, 25),
        'gross_profit_margin': np.random.uniform(20, 60),
        'revenue_growth': max(-20, base_growth + np.random.uniform(-8, 8)),
        'profit_growth': max(-30, base_growth + np.random.uniform(-10, 15)),
        'eps_growth': max(-25, base_growth + np.random.uniform(-10, 10)),
        'debt_ratio': np.random.uniform(10, 60),
        'current_ratio': np.random.uniform(0.8, 3.0),
        'quick_ratio': np.random.uniform(0.5, 2.5),
        'goodwill_ratio': np.random.uniform(0, 30),
        'turnover_ratio': np.random.uniform(0.3, 2.0),
        'total_asset_turnover': np.random.uniform(0.2, 0.8),
        'operating_cash_flow_ratio': np.random.uniform(0.5, 1.5),
        'free_cash_flow': np.random.uniform(-1, 5),
        'price_change_1y': np.random.uniform(-30, 80),
        'price_change_ytd': np.random.uniform(-15, 30),
        'dividend_yield': np.random.uniform(0, 1.5),
        'payout_ratio': np.random.uniform(0, 40),
    }

def calculate_fundamental_score(fund):
    """计算基本面综合评分"""
    score = 0
    
    # 1. 估值评分 (25%)
    pe = fund.get('pe', 50)
    pb = fund.get('pb', 5)
    
    if pe <= 20:
        pe_score = 100
    elif pe <= 30:
        pe_score = 80
    elif pe <= 50:
        pe_score = 60
    elif pe <= 70:
        pe_score = 40
    else:
        pe_score = 20
    
    if pb <= 3:
        pb_score = 100
    elif pb <= 5:
        pb_score = 70
    elif pb <= 8:
        pb_score = 50
    else:
        pb_score = 30
    
    valuation_score = pe_score * 0.6 + pb_score * 0.4
    score += valuation_score * 0.25
    
    # 2. 成长性评分 (30%)
    rev_growth = fund.get('revenue_growth', 0)
    prof_growth = fund.get('profit_growth', 0)
    eps_growth = fund.get('eps_growth', 0)
    growth_avg = (rev_growth + prof_growth + eps_growth) / 3
    
    if growth_avg >= 30:
        growth_score = 100
    elif growth_avg >= 15:
        growth_score = 75
    elif growth_avg >= 0:
        growth_score = 50
    else:
        growth_score = 25
    
    score += growth_score * 0.30
    
    # 3. 盈利能力评分 (25%)
    roe = fund.get('roe', 10)
    net_marg = fund.get('net_profit_margin', 10)
    gross_marg = fund.get('gross_profit_margin', 30)
    
    profitability_score = 0
    profitability_score += 40 if roe >= 15 else (30 if roe >= 10 else 20)
    profitability_score += 30 if net_marg >= 15 else (20 if net_marg >= 8 else 10)
    profitability_score += 30 if gross_marg >= 40 else (25 if gross_marg >= 25 else 15)
    
    score += profitability_score * 0.25
    
    # 4. 风险评分 (20%)
    debt = fund.get('debt_ratio', 30)
    curr = fund.get('current_ratio', 1.5)
    goodwill = fund.get('goodwill_ratio', 10)
    
    risk_score = 0
    risk_score += 40 if debt < 30 else (30 if debt < 50 else 20)
    risk_score += 30 if curr >= 1.5 else (20 if curr >= 1.0 else 10)
    risk_score += 30 if goodwill < 10 else (20 if goodwill < 20 else 10)
    
    score += risk_score * 0.20
    
    return {
        'total_score': score,
        'valuation_score': valuation_score,
        'growth_score': growth_score,
        'profitability_score': profitability_score,
        'risk_score': risk_score,
        'pe': pe,
        'pb': pb,
        'roe': roe,
        'revenue_growth': rev_growth,
        'profit_growth': prof_growth
    }

def select_chuangye_stocks():
    """筛选创业板股票"""
    print("="*70)
    print("创业板基本面全面筛选 (999只)")
    print("="*70)
    
    all_stocks = []
    
    for i, code in enumerate(CHUANGYE_CODES):
        if (i + 1) % 100 == 0:
            print(f"进度: {i+1}/999...")
        
        fund = get_simulated_fundamentals(code)
        score_result = calculate_fundamental_score(fund)
        
        stock_info = {
            'code': code,
            'name': fund['name'],
            'market_cap': fund['market_cap'],
            'pe': fund['pe'],
            'pb': fund['pb'],
            'roe': fund['roe'],
            'revenue_growth': fund['revenue_growth'],
            'profit_growth': fund['profit_growth'],
            'net_profit_margin': fund['net_profit_margin'],
            'debt_ratio': fund['debt_ratio'],
            'current_ratio': fund['current_ratio'],
            'score': score_result['total_score'],
            'valuation_score': score_result['valuation_score'],
            'growth_score': score_result['growth_score'],
            'profitability_score': score_result['profitability_score'],
            'risk_score': score_result['risk_score']
        }
        
        all_stocks.append(stock_info)
    
    return all_stocks

def categorize_stocks(stocks):
    """分类股票"""
    categories = {'成长型': [], '价值型': [], '稳健型': [], '高风险': [], '一般型': []}
    
    for s in stocks:
        score = s['score']
        growth = s['growth_score']
        profit = s['profitability_score']
        risk = s['risk_score']
        pe = s['pe']
        rev = s['revenue_growth']
        prof = s['profit_growth']
        
        if growth >= 70 and profit >= 60:
            categories['成长型'].append(s)
        elif pe <= 35 and profit >= 50:
            categories['价值型'].append(s)
        elif risk >= 70 and profit >= 40:
            categories['稳健型'].append(s)
        elif risk <= 40 and (rev < 0 or prof < -10):
            categories['高风险'].append(s)
        else:
            categories['一般型'].append(s)
    
    return categories

def generate_report(stocks, categories):
    """生成报告"""
    print("\n" + "="*70)
    print("📊 创业板基本面分析报告")
    print("="*70)
    
    total = len(stocks)
    avg_score = np.mean([s['score'] for s in stocks])
    avg_pe = np.mean([s['pe'] for s in stocks])
    avg_roe = np.mean([s['roe'] for s in stocks])
    
    print(f"\n整体: {total}只, 平均评分:{avg_score:.1f}, 平均PE:{avg_pe:.1f}, 平均ROE:{avg_roe:.1f}%")
    
    print(f"\n分类统计:")
    for cat, lst in categories.items():
        if lst:
            print(f"  {cat}: {len(lst)}只")
    
    # TOP 10
    print(f"\n🏆 TOP 10 综合评分:")
    print("-"*70)
    print(f"{'排名':<4} {'代码':<10} {'综合分':<8} {'估值分':<8} {'成长分':<8} {'盈利分':<8} {'风险分':<8}")
    print("-"*70)
    
    sorted_stocks = sorted(stocks, key=lambda x: x['score'], reverse=True)
    
    for i, s in enumerate(sorted_stocks[:10], 1):
        print(f"{i:<4} {s['code']:<10} {s['score']:<8.1f} {s['valuation_score']:<8.1f} {s['growth_score']:<8.1f} {s['profitability_score']:<8.1f} {s['risk_score']:<8.1f}")
    
    # TOP 成长
    print(f"\n🌱 TOP 10 成长型:")
    growth_top = sorted(categories['成长型'], key=lambda x: x['growth_score'], reverse=True)[:10]
    for i, s in enumerate(growth_top, 1):
        print(f"{i}. {s['code']} - 成长分:{s['growth_score']:.1f} 营收:{s['revenue_growth']:.1f}% 利润:{s['profit_growth']:.1f}%")
    
    # TOP 价值
    print(f"\n💰 TOP 10 价值型:")
    value_top = sorted(categories['价值型'], key=lambda x: (x['score'], x['pe']))[:10]
    for i, s in enumerate(value_top, 1):
        print(f"{i}. {s['code']} - PE:{s['pe']:.1f} PB:{s['pb']:.1f} ROE:{s['roe']:.1f}%")
    
    # TOP 稳健
    print(f"\n🛡️ TOP 10 稳健型:")
    stable_top = sorted(categories['稳健型'], key=lambda x: x['risk_score'], reverse=True)[:10]
    for i, s in enumerate(stable_top, 1):
        print(f"{i}. {s['code']} - 风险分:{s['risk_score']:.1f} 负债:{s['debt_ratio']:.1f}%")
    
    # 保存
    output = {
        'date': datetime.now().isoformat(),
        'summary': {'total': total, 'avg_score': avg_score, 'avg_pe': avg_pe, 'avg_roe': avg_roe},
        'categories': {cat: len(lst) for cat, lst in categories.items()},
        'all_stocks': sorted_stocks,
        'top_growth': sorted(categories['成长型'], key=lambda x: x['growth_score'], reverse=True)[:30],
        'top_value': sorted(categories['价值型'], key=lambda x: (x['score'], x['pe']))[:30],
        'top_stable': sorted(categories['稳健型'], key=lambda x: x['risk_score'], reverse=True)[:30]
    }
    
    out_file = OUTPUT_DIR / "chuangye_fundamental_results.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存: {out_file}")

def main():
    stocks = select_chuangye_stocks()
    categories = categorize_stocks(stocks)
    generate_report(stocks, categories)

if __name__ == "__main__":
    main()
