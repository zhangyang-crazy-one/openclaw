#!/usr/bin/env python3
"""
创业板综合选股系统 v3.0
- 复用优化模型参数
- 集成更多因子（技术+基本面）
- 波动率分层建模
"""
import os, sys, json, warnings
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FUNDAMENTAL_FILE = OUTPUT_DIR / "chuangye_fundamental_results.json"

OPTIMIZED_FEATURE_COLS = [
    'return_3', 'return_5', 'return_10',
    'volatility_5', 'volatility_10', 'volatility_20',
    'turnover_rate', 'volume_trend',
    'rsi_7', 'rsi_14',
    'macd_hist',
    'bb_position', 'bb_width',
    'momentum_5', 'momentum_10',
    'ma_ratio_5', 'ma_ratio_10', 'ma_ratio_20',
    'atr',
    'obv_trend'
]

VOLATILITY_PARAMS = {
    'high': {'rf': {'n_estimators': 80, 'max_depth': 8, 'min_samples_split': 15, 'min_samples_leaf': 10, 'random_state': 42},
             'gb': {'n_estimators': 60, 'max_depth': 4, 'learning_rate': 0.08, 'random_state': 42}},
    'normal': {'rf': {'n_estimators': 100, 'max_depth': 12, 'min_samples_split': 10, 'min_samples_leaf': 5, 'random_state': 42},
               'gb': {'n_estimators': 80, 'max_depth': 6, 'learning_rate': 0.1, 'random_state': 42}},
    'low': {'rf': {'n_estimators': 120, 'max_depth': 15, 'min_samples_split': 5, 'min_samples_leaf': 3, 'random_state': 42},
            'gb': {'n_estimators': 100, 'max_depth': 8, 'learning_rate': 0.12, 'random_state': 42}}
}

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
            df['high'] = df['close'] * 1.02
            df['low'] = df['close'] * 0.98
        else:
            cols = ['date', 'open', 'close', 'high', 'low', 'volume'][:n_cols]
            df.columns = cols + [f'col{i}' for i in range(n_cols-6)] if n_cols > 6 else cols
            df['volume'] = pd.to_numeric(df.get('volume', 1), errors='coerce')
            df['high'] = pd.to_numeric(df.get('high', df['close'] * 1.02), errors='coerce')
            df['low'] = pd.to_numeric(df.get('low', df['close'] * 0.98), errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        for col in ['close', 'high', 'low', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna()
    except:
        return None

def calculate_all_features(df):
    df = df.copy()
    for p in [1, 3, 5, 10]:
        df[f'return_{p}'] = df['close'].pct_change(p)
    for p in [5, 10, 20]:
        df[f'volatility_{p}'] = df['return_1'].rolling(p).std()
    df['volume_ma_5'] = df['volume'].rolling(5).mean()
    df['volume_ma_20'] = df['volume'].rolling(20).mean()
    df['turnover_rate'] = df['volume'] / (df['volume_ma_20'] + 1)
    df['volume_trend'] = df['volume_ma_5'] / (df['volume_ma_20'] + 1)
    for p in [7, 14]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(p).mean()
        rs = gain / (loss + 1e-10)
        df[f'rsi_{p}'] = 100 - (100 / (1 + rs))
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    bb_mid = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = bb_mid + 2 * bb_std
    df['bb_lower'] = bb_mid - 2 * bb_std
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / bb_mid
    for p in [5, 10, 20]:
        df[f'momentum_{p}'] = df['close'] / df['close'].shift(p) - 1
    for p in [5, 10, 20]:
        df[f'ma_{p}'] = df['close'].rolling(p).mean()
        df[f'ma_ratio_{p}'] = df['close'] / (df[f'ma_{p}'] + 1e-10)
    tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift(1)).abs(), (df['low'] - df['close'].shift(1)).abs()], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean() / df['close']
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
    df['obv_ma'] = df['obv'].rolling(10).mean()
    df['obv_trend'] = df['obv'] / (df['obv_ma'] + 1)
    return df

def get_volatility_level(train_df):
    vol = train_df['volatility_20'].iloc[-30:].mean()
    if vol > 0.04:
        return 'high'
    elif vol < 0.025:
        return 'low'
    return 'normal'

def train_optimized_model(df, feature_cols):
    df_feat = calculate_all_features(df)
    train_df = df_feat[df_feat['date'] < '2026-02-01'].dropna(subset=feature_cols)
    if len(train_df) < 200:
        return None, None, None
    vol_level = get_volatility_level(train_df)
    params = VOLATILITY_PARAMS[vol_level]
    X_train = train_df[feature_cols].values
    y_train = train_df['close'].values
    rf = RandomForestRegressor(**params['rf'])
    gb = GradientBoostingRegressor(**params['gb'])
    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)
    return rf, gb, vol_level

def predict_optimized(rf, gb, df, feature_cols):
    df_feat = calculate_all_features(df)
    latest = df_feat.iloc[-1]
    features = latest[feature_cols].values.astype(float)
    if np.any(np.isnan(features)):
        return None
    pred_rf = rf.predict(features.reshape(1, -1))[0]
    pred_gb = gb.predict(features.reshape(1, -1))[0]
    return 0.5 * pred_rf + 0.5 * pred_gb

def calculate_fundamental_score(fund):
    score = 0
    pe = fund.get('pe', 50)
    pb = fund.get('pb', 5)
    pe_score = 100 if pe <= 20 else (80 if pe <= 30 else (60 if pe <= 50 else (40 if pe <= 70 else 20)))
    pb_score = 100 if pb <= 3 else (70 if pb <= 5 else (50 if pb <= 8 else 30))
    score += (pe_score * 0.6 + pb_score * 0.4) * 0.25
    growth = (fund.get('revenue_growth', 0) + fund.get('profit_growth', 0)) / 2
    growth_score = 100 if growth >= 30 else (75 if growth >= 15 else (50 if growth >= 0 else 25))
    score += growth_score * 0.30
    roe = fund.get('roe', 10)
    net_marg = fund.get('net_profit_margin', 10)
    gross_marg = fund.get('gross_profit_margin', 30)
    profit_score = 0
    profit_score += 40 if roe >= 15 else (30 if roe >= 10 else 20)
    profit_score += 30 if net_marg >= 15 else (20 if net_marg >= 8 else 10)
    profit_score += 30 if gross_marg >= 40 else (25 if gross_marg >= 25 else 15)
    score += profit_score * 0.25
    debt = fund.get('debt_ratio', 30)
    curr = fund.get('current_ratio', 1.5)
    risk_score = 0
    risk_score += 40 if debt < 30 else (30 if debt < 50 else 20)
    risk_score += 30 if curr >= 1.5 else (20 if curr >= 1.0 else 10)
    risk_score += 30 if debt < 50 else 10
    score += risk_score * 0.20
    return score

def calculate_technical_score(df):
    if df is None or len(df) < 50:
        return None, None
    latest = df.iloc[-1]
    close = latest['close']
    mom = df['close'].pct_change(20).iloc[-1]
    mom_score = 30 if mom > 0.1 else (25 if mom > 0.05 else (20 if mom > 0 else 10))
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    trend_score = 25 if close > ma20 * 1.05 else (20 if close > ma20 else (15 if close > ma20 * 0.95 else 10))
    vol = df['close'].pct_change().std()
    vol_score = 20 if vol < 0.025 else (15 if vol < 0.04 else (10 if vol < 0.06 else 5))
    vol_ma = df['volume'].rolling(20).mean().iloc[-1]
    turnover = df['volume'].iloc[-1] / vol_ma
    vol_score_adj = 15 if 1 < turnover < 3 else (10 if turnover >= 3 else 5)
    price_dir = close > df['close'].iloc[-2]
    vol_dir = df['volume'].iloc[-1] > df['volume'].iloc[-2]
    coop_score = 10 if (price_dir and vol_dir) else (5 if price_dir else 0)
    total_score = mom_score + trend_score + vol_score + vol_score_adj + coop_score
    return total_score, {'momentum': mom * 100, 'ma_ratio': close / ma20, 'volatility': vol * 100, 'turnover': turnover}

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
    return '一般型'

def run_enhanced_analysis():
    print("="*70)
    print("创业板综合选股系统 v3.0 (复用优化模型)")
    print("="*70)
    print(f"特征数量: {len(OPTIMIZED_FEATURE_COLS)} 个")
    print(f"模型: RF+GB集成 (波动率分层)")
    
    print("\n加载基本面数据...")
    fund_data = load_fundamental_results()
    if fund_data is None:
        print("未找到基本面数据!")
        return
    fund_stocks = {s['code']: s for s in fund_data.get('all_stocks', [])}
    print(f"加载 {len(fund_stocks)} 只基本面数据")
    
    all_analysis = []
    model_stats = {'high': 0, 'normal': 0, 'low': 0}
    
    print("\n分析股票（使用优化模型）...")
    total = len(fund_stocks)
    
    for i, (code, fund) in enumerate(fund_stocks.items()):
        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{total}")
        
        df = load_stock_data(code)
        if df is None or len(df) < 200:
            continue
        
        rf, gb, vol_level = train_optimized_model(df, OPTIMIZED_FEATURE_COLS)
        if rf is None:
            continue
        
        model_stats[vol_level] += 1
        predicted_price = predict_optimized(rf, gb, df, OPTIMIZED_FEATURE_COLS)
        actual_price = df['close'].iloc[-1]
        pred_return = (predicted_price - actual_price) / actual_price * 100 if predicted_price else None
        
        fund_score = calculate_fundamental_score(fund)
        tech_score, tech_details = calculate_technical_score(df)
        if tech_score is None:
            continue
        
        composite_score = fund_score * 0.6 + tech_score * 0.4
        
        analysis = {
            'code': code, 'name': fund.get('name', code),
            'fundamental_score': fund_score, 'technical_score': tech_score,
            'composite_score': composite_score, 'volatility_level': vol_level,
            'predicted_return': pred_return, 'predicted_price': predicted_price,
            'actual_price': actual_price, 'pe': fund.get('pe', 0),
            'pb': fund.get('pb', 0), 'roe': fund.get('roe', 0),
            'revenue_growth': fund.get('revenue_growth', 0),
            'profit_growth': fund.get('profit_growth', 0),
            'market_cap': fund.get('market_cap', 0),
            'tech_details': tech_details,
            'category': categorize_by_type(fund)
        }
        all_analysis.append(analysis)
    
    print(f"\n模型分布: 高波动 {model_stats['high']}只, 正常 {model_stats['normal']}只, 低波动 {model_stats['low']}只")
    print(f"完成 {len(all_analysis)} 只股票分析")
    
    all_analysis = sorted(all_analysis, key=lambda x: x['composite_score'], reverse=True)
    generate_enhanced_report(all_analysis)

def generate_enhanced_report(stocks):
    print("\n" + "="*70)
    print("📊 创业板综合分析报告 v3.0")
    print("="*70)
    
    total = len(stocks)
    avg_comp = np.mean([s['composite_score'] for s in stocks])
    avg_fund = np.mean([s['fundamental_score'] for s in stocks])
    avg_tech = np.mean([s['technical_score'] for s in stocks])
    avg_pred = np.mean([s['predicted_return'] for s in stocks if s['predicted_return']])
    
    print(f"\n整体统计: {total}只, 综合分:{avg_comp:.1f}, 基本面:{avg_fund:.1f}, 技术面:{avg_tech:.1f}, 预测收益:{avg_pred:.2f}%")
    
    vol_dist = {'high': 0, 'normal': 0, 'low': 0}
    for s in stocks:
        vol_dist[s.get('volatility_level', 'normal')] += 1
    
    print(f"\n波动率分布: 高:{vol_dist['high']}只, 正常:{vol_dist['normal']}只, 低:{vol_dist['low']}只")
    
    print(f"\n🏆 TOP 20 综合评分:")
    print("-"*75)
    print(f"{'排名':<4} {'代码':<10} {'综合分':<8} {'基本面':<8} {'技术面':<8} {'预测收益':<10} {'波动':<6}")
    print("-"*75)
    
    for i, s in enumerate(stocks[:20], 1):
        pred = f"{s['predicted_return']:+.1f}%" if s['predicted_return'] else "N/A"
        vol = s.get('volatility_level', '-')[:3]
        print(f"{i:<4} {s['code']:<10} {s['composite_score']:<8.1f} {s['fundamental_score']:<8.1f} {s['technical_score']:<8.1f} {pred:<10} {vol:<6}")
    
    print(f"\n🌟 TOP 10 预测收益:")
    pred_stocks = [s for s in stocks if s['predicted_return']]
    for i, s in enumerate(sorted(pred_stocks, key=lambda x: x['predicted_return'], reverse=True)[:10], 1):
        print(f"{i}. {s['code']} - 预测:{s['predicted_return']:+.2f}% 当前:{s['actual_price']:.2f}")
    
    cats = {}
    for s in stocks:
        cats[s['category']] = cats.get(s['category'], 0) + 1
    print(f"\n类型分布:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}只")
    
    # 推荐
    rec1 = [s for s in stocks if s['category'] in ['成长型', '高成长'] and s['predicted_return'] and s['predicted_return'] > 3]
    print(f"\n🌱 高成长正收益 ({len(rec1)}只):")
    for s in rec1[:5]:
        print(f"  {s['code']} - 预测:{s['predicted_return']:+.1f}%")
    
    rec2 = [s for s in stocks if s['pe'] < 30 and s['roe'] > 15]
    print(f"\n💎 价值低估高ROE ({len(rec2)}只):")
    for s in sorted(rec2, key=lambda x: x['roe'], reverse=True)[:5]:
        print(f"  {s['code']} - PE:{s['pe']:.1f} ROE:{s['roe']:.1f}%")
    
    # 保存
    out = {
        'date': datetime.now().isoformat(), 'model': 'optimized_v3',
        'features': OPTIMIZED_FEATURE_COLS,
        'summary': {'total_stocks': total, 'avg_composite': avg_comp, 'avg_fundamental': avg_fund, 'avg_technical': avg_tech, 'avg_predicted_return': avg_pred},
        'volatility_distribution': vol_dist, 'categories': cats,
        'top_50': stocks[:50], 'all_stocks': stocks
    }
    out_file = OUTPUT_DIR / "chuangye_enhanced_results.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 结果已保存: {out_file}")
    
    optimize_with_enhanced_model(stocks)

def optimize_with_enhanced_model(stocks):
    print("\n" + "="*70)
    print("💰 仓位优化建议 v3.0")
    print("="*70)
    
    top_stocks = sorted(stocks, key=lambda x: x['composite_score'], reverse=True)[:20]
    
    print(f"\n🏆 TOP 20 建议配置:")
    print("-"*60)
    print(f"{'代码':<10} {'综合分':<8} {'预测收益':<10} {'波动率':<8} {'仓位':<8}")
    print("-"*60)
    
    for s in top_stocks:
        base_pos = s['composite_score'] / 100 * 20
        pred_adj = 1.0
        if s['predicted_return']:
            if s['predicted_return'] > 10:
                pred_adj = 1.4
            elif s['predicted_return'] > 5:
                pred_adj = 1.2
            elif s['predicted_return'] > 0:
                pred_adj = 1.0
            else:
                pred_adj = 0.7
        vol = s.get('volatility_level', 'normal')
        vol_adj = 0.7 if vol == 'high' else (1.1 if vol == 'low' else 1.0)
        position = base_pos * pred_adj * vol_adj
        position = max(2, min(15, position))
        pred_str = f"{s['predicted_return']:+.1f}%" if s['predicted_return'] else "N/A"
        print(f"{s['code']:<10} {s['composite_score']:<8.1f} {pred_str:<10} {vol:<8} {position:<8.1f}%")
    
    out_file = OUTPUT_DIR / "chuangye_enhanced_positions.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'date': datetime.now().isoformat(), 'model': 'enhanced_v3', 'recommendations': [
            {'code': s['code'], 'composite_score': s['composite_score'], 'predicted_return': s['predicted_return'],
             'volatility_level': s.get('volatility_level')} for s in top_stocks]}, f, ensure_ascii=False, indent=2)
    print(f"\n💾 仓位建议已保存: {out_file}")

def main():
    run_enhanced_analysis()

if __name__ == "__main__":
    main()
