#!/usr/bin/env python3
"""快速选股和预测测试"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data(code):
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
        elif n_cols >= 5:
            cols = ['date', 'open', 'close', 'high', 'low', 'volume'][:n_cols]
            df.columns = cols + [f'col{i}' for i in range(n_cols-6)] if n_cols > 6 else cols
            if 'volume' not in df.columns:
                df['volume'] = 1.0
            if 'high' not in df.columns:
                df['high'] = df['close'] * 1.02
                df['low'] = df['close'] * 0.98
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        for col in ['close', 'high', 'low', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna()
    except:
        return None

def calc_features(df):
    df = df.copy()
    df['return_5'] = df['close'].pct_change(5)
    df['return_20'] = df['close'].pct_change(20)
    df['ma_ratio_20'] = df['close'] / df['close'].rolling(20).mean()
    df['volatility_20'] = df['return_5'].rolling(5).std()
    df['rsi_14'] = 50  # 简化RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    df['macd_hist'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['macd_hist'] = df['macd_hist'] - df['macd_hist'].ewm(span=9).mean()
    df['bb_position_20'] = (df['close'] - df['close'].rolling(20).min()) / (df['close'].rolling(20).max() - df['close'].rolling(20).min() + 1e-10)
    df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
    return df

def main():
    print("="*60)
    print("快速选股与预测测试")
    print("="*60)
    
    # 获取股票列表
    stocks = [f.stem for f in DATA_DIR.glob("*.csv") if f.stem.isdigit() and len(f.stem) == 6]
    print(f"总股票数: {len(stocks)}")
    
    # 选股评分
    feature_cols = ['return_5', 'return_20', 'ma_ratio_20', 'volatility_20', 'rsi_14', 'bb_position_20', 'volume_ratio', 'momentum_20']
    
    scores = []
    for code in stocks[:500]:  # 快速测试500只
        df = load_data(code)
        if df is None or len(df) < 200:
            continue
        df = calc_features(df)
        latest = df.iloc[-1]
        
        score = 0
        score += 30 if latest['momentum_20'] > 0.05 else (15 if latest['momentum_20'] > 0 else 0)
        score += 25 if latest['ma_ratio_20'] > 1.02 else (12 if latest['ma_ratio_20'] > 0.98 else 0)
        score += 15 if latest['volatility_20'] < 0.03 else (8 if latest['volatility_20'] < 0.05 else 0)
        score += 15 if 40 < latest['rsi_14'] < 60 else (5 if latest['rsi_14'] < 30 or latest['rsi_14'] > 70 else 8)
        score += 15 if 0.5 < latest['volume_ratio'] < 2.0 else 5
        
        scores.append({'code': code, 'score': score, 'close': latest['close']})
    
    # 排序
    scores = sorted(scores, key=lambda x: x['score'], reverse=True)
    
    print(f"\n🏆 TOP 20 精选股票:")
    print("-"*60)
    for i, s in enumerate(scores[:20], 1):
        print(f"{i:2}. {s['code']:<10} 得分:{s['score']:<3} 收盘:{s['close']:.2f}")
    
    # 预测TOP 10
    print(f"\n🤖 价格预测 (TOP 10):")
    print("-"*60)
    
    results = []
    for s in scores[:10]:
        code = s['code']
        df = load_data(code)
        if df is None:
            continue
        df = calc_features(df)
        
        train_df = df[df['date'] < '2026-02-01'].dropna(subset=feature_cols)
        test_df = df[(df['date'] >= '2026-02-01') & (df['date'] <= '2026-02-06')]
        
        if len(train_df) < 100 or len(test_df) < 2:
            continue
        
        X_train = train_df[feature_cols].values
        y_train = train_df['close'].values
        
        # 随机森林
        rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        
        preds, actuals = [], []
        for _, row in test_df.iterrows():
            X = row[feature_cols].values.reshape(1, -1)
            pred = rf.predict(X)[0]
            preds.append(pred)
            actuals.append(row['close'])
        
        if len(preds) > 1:
            mape = np.mean(np.abs(np.array(preds) - np.array(actuals)) / np.array(actuals)) * 100
            results.append({'code': code, 'mape': mape, 'actual': actuals[-1], 'pred': preds[-1]})
    
    results = sorted(results, key=lambda x: x['mape'])
    for r in results[:10]:
        print(f"{r['code']:<10} 实际:{r['actual']:.2f} 预测:{r['pred']:.2f} 误差:{r['mape']:.2f}%")
    
    # 汇总
    if results:
        avg_mape = np.mean([r['mape'] for r in results])
        print(f"\n📊 汇总:")
        print(f"   预测成功: {len(results)} 只")
        print(f"   平均MAPE: {avg_mape:.2f}%")
        excellent = len([r for r in results if r['mape'] < 5])
        print(f"   优秀(MAPE<5%): {excellent} 只 ({excellent/len(results)*100:.1f}%)")
    
    # 保存
    output_file = OUTPUT_DIR / "quick_prediction_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'top20': scores[:20],
            'predictions': results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {output_file}")

if __name__ == "__main__":
    main()
