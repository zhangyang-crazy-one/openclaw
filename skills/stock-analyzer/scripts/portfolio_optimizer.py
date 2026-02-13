#!/usr/bin/env python3
"""
Portfolio Optimization System for ChiNext Stocks
- Kelly Criterion Optimization
- Risk Parity Strategy
- Maximum Drawdown Limit
"""
import os, sys, json, warnings
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHUANGYE_POOL = [
    "300750", "300014", "300017", "300408", "300251",
    "300015", "300529", "300383", "300285", "300298",
    "300274", "300124", "300212", "300676", "300760"
]

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
        else:
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
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna()
    except:
        return None

def calc_features(df):
    df = df.copy()
    for p in [1, 3, 5, 10]:
        df[f'return_{p}'] = df['close'].pct_change(p)
    for p in [5, 10, 20]:
        df[f'volatility_{p}'] = df['return_1'].rolling(p).std()
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['turnover_rate'] = df['volume'] / df['volume_ma']
    for p in [7, 14]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(p).mean()
        rs = gain / (loss + 1e-10)
        df[f'rsi_{p}'] = 100 - (100 / (1 + rs))
    df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    for p in [5, 10, 20]:
        df[f'momentum_{p}'] = df['close'] / df['close'].shift(p) - 1
    for p in [5, 10, 20]:
        df[f'ma_{p}'] = df['close'].rolling(p).mean()
        df[f'ma_ratio_{p}'] = df['close'] / df[f'ma_{p}']
    return df

def kelly_position(win_rate, avg_win, avg_loss, confidence=0.5):
    if avg_loss == 0:
        return 0.2
    kelly = win_rate - (1 - win_rate) / (avg_win / abs(avg_loss))
    adj_kelly = kelly * confidence
    half_kelly = adj_kelly / 2
    return max(0.05, min(0.4, half_kelly))

def risk_parity(returns_df):
    n = returns_df.shape[1]
    cov = returns_df.cov()
    
    def rc(w):
        pv = np.sqrt(np.dot(w.T, np.dot(cov.values, w)))
        mc = np.dot(cov.values, w)
        return w * mc / (pv + 1e-10)
    
    def obj(w):
        target = np.ones(n) / n
        return np.sum((rc(w) - target) ** 2)
    
    cons = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    bnds = [(0.05, 0.5) for _ in range(n)]
    w0 = np.ones(n) / n
    
    res = minimize(obj, w0, method='SLSQP', bounds=bnds, constraints=cons)
    return res.x / res.x.sum() if res.success else w0

def calc_optimal_position(stock_metrics, risk_aversion=0.5):
    positions = []
    for stock in stock_metrics:
        vol = stock['volatility']
        vol_pen = np.sqrt(vol) * 2
        win_rate = stock.get('win_rate', 0.5)
        dir_acc = stock.get('direction_accuracy', 0.5)
        mape = stock.get('mape', 0.3)
        mape_pen = max(0, mape - 0.1) * 3
        
        base = 0.25
        adj = (1 - vol_pen) * risk_aversion + (win_rate - 0.5) * 0.2 + (dir_acc - 0.5) * 0.3 + (1 - mape_pen) * (1 - risk_aversion)
        pos = base * max(0.3, min(1.5, 1 + adj))
        positions.append({'code': stock['code'], 'position': max(0.05, min(0.4, pos))})
    return positions

def backtest(positions, returns_df):
    weights = np.array([p['position'] for p in positions])
    weights = weights / weights.sum()
    port_ret = (returns_df * weights).sum(axis=1)
    
    tot = (1 + port_ret).prod() - 1
    ann = tot / len(port_ret) * 252
    vol = port_ret.std() * np.sqrt(252)
    sharpe = ann / (vol + 1e-10)
    
    cum = (1 + port_ret).cumprod()
    max_dd = -(cum.cummax() - cum).min()
    
    return {
        'total_return': tot,
        'annualized_return': ann,
        'volatility': vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'weights': dict(zip([p['code'] for p in positions], weights.tolist()))
    }

def main():
    print("="*70)
    print("PORTFOLIO OPTIMIZATION FOR CHINEXT STOCKS")
    print("="*70)
    
    feat_cols = ['return_3', 'return_5', 'volatility_5', 'volatility_20', 
                 'turnover_rate', 'rsi_7', 'macd_hist', 'momentum_5', 'ma_ratio_20']
    
    stock_metrics = []
    rets_list = []
    
    for code in CHUANGYE_POOL:
        print(f"Processing {code}...")
        df = load_data(code)
        if df is None or len(df) < 300:
            continue
        
        df = calc_features(df)
        train_df = df[df['date'] < '2026-02-01']
        test_df = df[(df['date'] >= '2026-02-01') & (df['date'] <= '2026-02-06')]
        
        if len(train_df) < 200 or len(test_df) < 5:
            continue
        
        X_train = train_df[feat_cols].dropna().values
        y_train = train_df.dropna(subset=feat_cols)['close'].values
        
        if len(X_train) < 100:
            continue
        
        rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        
        preds, acts = [], []
        for _, row in test_df.iterrows():
            f = row[feat_cols].values.astype(float)
            if not np.any(np.isnan(f)):
                preds.append(rf.predict(f.reshape(1, -1))[0])
                acts.append(row['close'])
        
        if len(preds) < 5:
            continue
        
        mape = np.mean(np.abs(np.array(preds) - np.array(acts)) / np.array(acts))
        vol_20 = train_df['return_1'].rolling(20).std().iloc[-1]
        dirs = np.sign(np.diff(acts))
        pdirs = np.sign(np.diff(preds))
        dir_acc = np.mean(dirs == pdirs) if len(dirs) > 0 else 0.5
        rets = np.diff(acts) / acts[:-1]
        
        wins = rets[rets > 0]
        losses = rets[rets < 0]
        win_rate = len(wins) / (len(wins) + len(losses) + 1e-10)
        
        stock_metrics.append({
            'code': code, 'mape': mape, 'volatility': vol_20,
            'direction_accuracy': dir_acc, 'win_rate': win_rate, 'returns': rets
        })
        rets_list.append(pd.DataFrame({code: rets}))
        
        print(f"  MAPE={mape*100:.2f}%, Vol={vol_20*100:.2f}%, Dir={dir_acc*100:.1f}%")
    
    if len(stock_metrics) < 5:
        print("Not enough valid stocks!")
        return
    
    rets_df = pd.concat(rets_list, axis=1).dropna()
    
    print("\n" + "="*70)
    print("OPTIMIZATION RESULTS")
    print("="*70)
    
    # Kelly
    print("\n1. Kelly Criterion:")
    kelly_pos = []
    for s in stock_metrics:
        wins = s['returns'][s['returns'] > 0]
        losses = s['returns'][s['returns'] < 0]
        wr = len(wins) / (len(wins) + len(losses) + 1e-10)
        aw = wins.mean() if len(wins) > 0 else 0.05
        al = abs(losses.mean()) if len(losses) > 0 else 0.03
        conf = max(0.3, min(0.9, 1 - s['mape']))
        pos = kelly_position(wr, aw, al, conf)
        kelly_pos.append({'code': s['code'], 'position': pos, 'win_rate': wr, 'confidence': conf})
        print(f"  {s['code']}: {pos*100:.0f}% (win={wr*100:.0f}%, conf={conf*100:.0f}%)")
    
    # Optimal
    print("\n2. Optimal Position:")
    opt_pos = calc_optimal_position(stock_metrics, 0.5)
    for p in opt_pos:
        print(f"  {p['code']}: {p['position']*100:.0f}%")
    
    # Risk Parity
    print("\n3. Risk Parity:")
    try:
        rp_w = risk_parity(rets_df)
        rp_pos = [{'code': s['code'], 'position': rp_w[i]} for i, s in enumerate(stock_metrics)]
        for i, s in enumerate(stock_metrics):
            print(f"  {s['code']}: {rp_w[i]*100:.0f}%")
    except:
        rp_pos = [{'code': s['code'], 'position': 1/len(stock_metrics)} for s in stock_metrics]
        print("  Risk parity failed, using equal weight")
    
    # Equal Weight
    eq_pos = [{'code': s['code'], 'position': 1/len(stock_metrics)} for s in stock_metrics]
    
    # Backtest
    print("\n" + "="*70)
    print("BACKTEST RESULTS")
    print("="*70)
    
    strategies = {
        'Kelly': kelly_pos,
        'Optimal': opt_pos,
        'RiskParity': rp_pos,
        'EqualWeight': eq_pos
    }
    
    best_name = None
    best_sharpe = -999
    
    for name, pos_list in strategies.items():
        r = backtest(pos_list, rets_df)
        print(f"\n{name}:")
        print(f"  Total Return: {r['total_return']*100:.2f}%")
        print(f"  Annualized: {r['annualized_return']*100:.2f}%")
        print(f"  Volatility: {r['volatility']*100:.2f}%")
        print(f"  Sharpe: {r['sharpe']:.3f}")
        print(f"  Max Drawdown: {r['max_drawdown']*100:.2f}%")
        
        if r['sharpe'] > best_sharpe:
            best_sharpe = r['sharpe']
            best_name = name
    
    print(f"\nBEST STRATEGY: {best_name} (Sharpe={best_sharpe:.3f})")
    
    # Save
    output = {
        'date': datetime.now().isoformat(),
        'best_strategy': best_name,
        'strategies': {k: {'metrics': v, 'positions': [{'code': p['code'], 'position': p['position']} for p in strategies[k]]} for k in strategies},
        'backtest': {k: backtest(strategies[k], rets_df) for k in strategies}
    }
    
    out_file = OUTPUT_DIR / "portfolio_optimization_results.json"
    with open(out_file, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to: {out_file}")
    
    print("\n" + "="*70)
    print("RECOMMENDED POSITIONS")
    print("="*70)
    print(f"\nUsing {best_name} strategy:")
    for p in strategies[best_name]:
        print(f"  {p['code']}: {p['position']*100:.1f}%")

if __name__ == "__main__":
    main()
