#!/usr/bin/env python3
"""
创业板综合选股系统
结合技术分析 + 基本面分析 + 仓位优化
"""
import os, sys, json, warnings
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FUNDAMENTAL_FILE = OUTPUT_DIR / "chuangye_fundamental_results.json"

def load_fundamental_results():
    if FUNDAMENTAL_FILE.exists():
        with open(FUNDAMENTAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_stock_data(code):
    filepath = DATA_DIR / f"{code}.csv"
    if not filepath.exists():
        return None
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        n_cols = df.shape[1]
        if n_cols == 2:
            df.columns = ['date', 'close']
            df['volume'] = 1.0
        else:
            cols = ['date', 'open', 'close', 'high', 'low', 'volume'][:n_cols]
            df.columns = cols + [f'col{i}' for i in range(n_cols-6)] if n_cols > 6 else cols
            if 'volume' not in df.columns:
                df['volume'] = 1.0
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        for col in ['close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna()
    except:
        return None

def calc_technical_score(df):
    if df is None or len(df) < 50:
        return None, None
    
    latest = df.iloc[-1]
    close = latest['close']
    
    return_5 = df['close'].pct_change(5).iloc[-1]
    return_20 = df['close'].pct_change(20).iloc[-1]
    volatility = df['close'].pct_change().std()
    
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    ma_ratio = close / ma20
    
    volume_ma = df['volume'].rolling(20).mean().iloc[-1]
    turnover = df['volume'].iloc[-1] / volume_ma
    
    # 技术评分
    score = 0
    
    if return_20 > 0.1:
        score += 30
    elif return_20 > 0.05:
        score += 25
    elif return_20 > 0:
        score += 20
    else:
        score += 10
    
    if ma_ratio > 1.05:
        score += 25
    elif ma_ratio > 1.0:
        score += 20
    elif ma_ratio > 0.95:
        score += 15
    else:
        score += 10
    
    if volatility < 0.025:
        score += 20
    elif volatility < 0.04:
        score += 15
    elif volatility < 0.06:
        score += 10
    else:
        score += 5
    
    if 1 < turnover < 3:
        score += 15
    elif turnover >= 3:
        score += 10
    else:
        score += 5
    
    if return_20 > 0 and turnover > 1:
        score += 10
    elif return_20 > 0:
        score += 5
    
    return score, {'return_5': return_5*100, 'return_20': return_20*100, 
                   'volatility': volatility*100, 'ma_ratio': ma_ratio,
                   'momentum': return_20*100, 'turnover': turnover}

def predict_next_return(df):
    if df is None or len(df) < 150:
        return None
    
    df_feat = df.copy()
    for p in [1, 3, 5]:
        df_feat[f'return_{p}'] = df['close'].pct_change(p)
    df_feat['volatility_5'] = df['close'].pct_change().rolling(5).std()
    df_feat['volatility_20'] = df['close'].pct_change().rolling(20).std()
    df_feat['ma_ratio'] = df['close'] / df['close'].rolling(20).mean()
    df_feat['volume_ma'] = df['volume'].rolling(10).mean() / df['volume'].rolling(20).mean()
    
    feature_cols = ['return_3', 'return_5', 'volatility_5', 'volatility_20', 'ma_ratio', 'volume_ma']
    
    # 计算目标变量
    df_feat['target'] = df['close'].pct_change(5).shift(-5)
    df_clean = df_feat.dropna(subset=feature_cols + ['target'])
    
    if len(df_clean) < 50:
        return None
    
    X = df_clean[feature_cols].values
    y = df_clean['target'].values
    
    rf = RandomForestRegressor(n_estimators=30, max_depth=6, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    latest = df_feat[feature_cols].iloc[-1:].values
    return rf.predict(latest)[0]

def categorize_by_type(fund):
    growth = fund.get('growth_score', 50)
    profit = fund.get('profitability_score', 50)
    pe = fund.get('pe', 40)
    
    if growth >= 70 and profit >= 60:
        return '成长型'
    elif pe <= 30 and profit >= 50:
        return '价值型'
    elif profit >= 50 and growth >= 40:
        return '业绩型'
    elif growth >= 50:
        return '高成长'
    else:
        return '一般型'

def run_comprehensive_analysis():
    print("="*70)
    print("创业板综合选股系统")
    print("="*70)
    print("评分: 基本面60% + 技术面40%")
    
    print("\n加载基本面数据...")
    fund_data = load_fundamental_results()
    if fund_data is None:
        print("未找到基本面数据!")
        return
    
    fund_stocks = {s['code']: s for s in fund_data.get('all_stocks', [])}
    print(f"加载 {len(fund_stocks)} 只基本面数据")
    
    all_analysis = []
    
    print("\n分析技术面...")
    total = len(fund_stocks)
    
    for i, (code, fund) in enumerate(fund_stocks.items()):
        if (i + 1) % 200 == 0:
            print(f"  进度: {i+1}/{total}")
        
        df = load_stock_data(code)
        tech_score, tech_details = calc_technical_score(df)
        
        if tech_score is None:
            continue
        
        fund_score = fund.get('score', 50)
        composite = fund_score * 0.6 + tech_score * 0.4
        
        predicted = predict_next_return(df)
        
        analysis = {
            'code': code,
            'name': fund.get('name', code),
            'fundamental_score': fund_score,
            'technical_score': tech_score,
            'composite_score': composite,
            'pe': fund.get('pe', 0),
            'pb': fund.get('pb', 0),
            'roe': fund.get('roe', 0),
            'revenue_growth': fund.get('revenue_growth', 0),
            'profit_growth': fund.get('profit_growth', 0),
            'market_cap': fund.get('market_cap', 0),
            'predicted_return': predicted * 100 if predicted else None,
            'tech_details': tech_details,
            'category': categorize_by_type(fund)
        }
        
        all_analysis.append(analysis)
    
    print(f"\n完成 {len(all_analysis)} 只股票分析")
    
    all_analysis = sorted(all_analysis, key=lambda x: x['composite_score'], reverse=True)
    generate_report(all_analysis)
    optimize_positions(all_analysis)

def generate_report(stocks):
    print("\n" + "="*70)
    print("📊 创业板综合分析报告")
    print("="*70)
    
    total = len(stocks)
    avg_comp = np.mean([s['composite_score'] for s in stocks])
    avg_fund = np.mean([s['fundamental_score'] for s in stocks])
    avg_tech = np.mean([s['technical_score'] for s in stocks])
    
    print(f"\n整体: {total}只, 综合分:{avg_comp:.1f}, 基本面:{avg_fund:.1f}, 技术面:{avg_tech:.1f}")
    
    # TOP 20
    print(f"\n🏆 TOP 20 综合评分股票:")
    print("-"*70)
    print(f"{'排名':<4} {'代码':<10} {'综合分':<8} {'基本面':<8} {'技术面':<8} {'预测收益':<10} {'类型':<10}")
    print("-"*70)
    
    for i, s in enumerate(stocks[:20], 1):
        pred = f"{s['predicted_return']:+.1f}%" if s['predicted_return'] else "N/A"
        print(f"{i:<4} {s['code']:<10} {s['composite_score']:<8.1f} {s['fundamental_score']:<8.1f} {s['technical_score']:<8.1f} {pred:<10} {s['category']:<10}")
    
    # 分类
    cats = {}
    for s in stocks:
        c = s['category']
        cats[c] = cats.get(c, 0) + 1
    
    print(f"\n类型分布:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}只")
    
    # 推荐
    print(f"\n💰 精选推荐:")
    
    high_growth = [s for s in stocks if s['category'] == '成长型' and s['predicted_return'] and s['predicted_return'] > 5]
    print(f"\n🌱 高成长 ({len(high_growth)}只):")
    for s in high_growth[:5]:
        print(f"  {s['code']} - 预测:{s['predicted_return']:+.1f}% 营收:{s['revenue_growth']:.1f}%")
    
    value = [s for s in stocks if s['pe'] < 30 and s['fundamental_score'] > 60]
    print(f"\n💎 价值低估 ({len(value)}只):")
    for s in value[:5]:
        print(f"  {s['code']} - PE:{s['pe']:.1f} ROE:{s['roe']:.1f}%")
    
    # 保存
    out = {
        'date': datetime.now().isoformat(),
        'summary': {'total': total, 'avg_composite': avg_comp, 'avg_fundamental': avg_fund, 'avg_technical': avg_tech},
        'top_50': stocks[:50],
        'all_stocks': stocks
    }
    
    out_file = OUTPUT_DIR / "chuangye_comprehensive_results.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存: {out_file}")

def optimize_positions(stocks):
    print("\n" + "="*70)
    print("💰 仓位优化建议")
    print("="*70)
    
    top_stocks = stocks[:20]
    
    print(f"\n🏆 TOP 20 建议配置:")
    print("-"*50)
    print(f"{'代码':<10} {'综合分':<8} {'预测':<10} {'仓位':<10}")
    print("-"*50)
    
    total_score = sum([s['composite_score'] for s in top_stocks])
    
    recs = []
    for s in top_stocks:
        base = s['composite_score'] / total_score
        adj = 1.0
        if s['predicted_return']:
            if s['predicted_return'] > 10:
                adj = 1.3
            elif s['predicted_return'] > 5:
                adj = 1.1
        pos = base * adj * 100
        
        recs.append({
            'code': s['code'],
            'composite_score': s['composite_score'],
            'predicted_return': s['predicted_return'],
            'position': pos
        })
        
        pred = f"{s['predicted_return']:+.1f}%" if s['predicted_return'] else "N/A"
        print(f"{s['code']:<10} {s['composite_score']:<8.1f} {pred:<10} {pos:<10.1f}%")
    
    out_file = OUTPUT_DIR / "chuangye_position_recommendations.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'date': datetime.now().isoformat(), 'recommendations': recs}, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 仓位建议已保存: {out_file}")

def main():
    run_comprehensive_analysis()

if __name__ == "__main__":
    main()
