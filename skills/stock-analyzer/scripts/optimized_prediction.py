#!/usr/bin/env python3
"""
A股智能选股与价格预测模型 - 优化版
基于多因子模型、模型集成和动态参数优化
"""
import os
import sys
import json
import warnings
import random
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# 配置
DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
MODEL_DIR = Path("/home/liujerry/金融数据/models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def load_stock_data(code):
    """加载股票数据"""
    filepath = DATA_DIR / f"{code}.csv"
    if not filepath.exists():
        return None
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        n_cols = df.shape[1]
        
        if n_cols == 2:
            df.columns = ['date', 'close']
            df['volume'] = 1.0
        elif n_cols == 6:
            pass
        elif n_cols == 12:
            df.columns = ['date', 'code', 'open', 'close', 'high', 'low', 
                         'volume', 'amount', 'amplitude', 'pct_change', 
                         'change', 'turnover']
            df = df[['date', 'open', 'close', 'high', 'low', 'volume']]
        else:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['open', 'close', 'high', 'low']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'volume' in df.columns:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        else:
            df['volume'] = 1.0
        
        return df.dropna()
    except Exception as e:
        return None

def calculate_advanced_features(df):
    """计算高级技术特征"""
    df = df.copy()
    
    # 确保high, low, volume存在
    if 'high' not in df.columns:
        df['high'] = df['close'] * 1.02
        df['low'] = df['close'] * 0.98
    if 'volume' not in df.columns:
        df['volume'] = df['close'] * 1000000
    
    # === 基础收益率特征 ===
    df['return_1'] = df['close'].pct_change(1)
    df['return_3'] = df['close'].pct_change(3)
    df['return_5'] = df['close'].pct_change(5)
    df['return_10'] = df['close'].pct_change(10)
    df['return_20'] = df['close'].pct_change(20)
    
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # === 移动平均特征 ===
    for window in [5, 10, 20, 60]:
        df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
        df[f'ma_ratio_{window}'] = df['close'] / df[f'ma_{window}']
        df[f'ma_trend_{window}'] = df[f'ma_{window}'] / df[f'ma_{window}'].shift(window)
    
    # === 波动率特征 ===
    for window in [5, 10, 20]:
        df[f'volatility_{window}'] = df['return_1'].rolling(window=window).std()
        df[f'atr_{window}'] = (df['high'] - df['low']).rolling(window=window).mean()
    
    # === RSI特征（多周期）===
    for period in [7, 14, 21]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        df[f'rsi_oversold_{period}'] = (df[f'rsi_{period}'] < 30).astype(int)
        df[f'rsi_overbought_{period}'] = (df[f'rsi_{period}'] > 70).astype(int)
    
    # === MACD特征 ===
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_golden_cross'] = ((df['macd'] > df['macd_signal']).astype(int) - (df['macd'].shift(1) > df['macd_signal'].shift(1)).astype(int))
    
    # === 布林带特征 ===
    for period in [20]:
        df[f'bb_mid_{period}'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df[f'bb_upper_{period}'] = df[f'bb_mid_{period}'] + 2 * bb_std
        df[f'bb_lower_{period}'] = df[f'bb_mid_{period}'] - 2 * bb_std
        df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / df[f'bb_mid_{period}']
        df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'] + 1e-10)
        df[f'bb_squeeze_{period}'] = (df[f'bb_width_{period}'] < df[f'bb_width_{period}'].rolling(50).mean()).astype(int)
    
    # === 成交量特征 ===
    df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
    df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma_20']
    df['volume_trend'] = df['volume_ma_5'] / df['volume_ma_20']
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
    df['obv_ma'] = df['obv'].rolling(window=10).mean()
    
    # === 动量特征 ===
    for period in [5, 10, 20, 60]:
        df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
        df[f'momentum_accel_{period}'] = df[f'momentum_{period}'] - df[f'momentum_{period}'].shift(period)
    
    # === 价格位置特征 ===
    df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / (df['high'].rolling(20).max() - df['low'].rolling(20).min() + 1e-10)
    df['high_20_ratio'] = df['close'] / df['high'].rolling(20).max()
    df['low_20_ratio'] = df['close'] / df['low'].rolling(20).min()
    
    # === 趋势强度（简化版ADX）===
    df['adx'] = np.nan
    for i in range(20, len(df)):
        start_idx = max(0, i - 20)
        high = df['high'].iloc[start_idx:i].values
        low = df['low'].iloc[start_idx:i].values
        close = df['close'].iloc[start_idx:i].values
        
        if len(high) < 5:
            df.iloc[i, df.columns.get_loc('adx')] = 50.0
            continue
        
        high_diff = np.diff(high)
        low_diff = np.diff(low)
        
        plus_di = np.mean(high_diff.clip(0)) / (np.mean(high_diff.clip(0)) + np.mean((-low_diff).clip(0)) + 1e-10) * 100
        minus_di = np.mean((-low_diff).clip(0)) / (np.mean(high_diff.clip(0)) + np.mean((-low_diff).clip(0)) + 1e-10) * 100
        
        adx_val = abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10) * 100
        df.iloc[i, df.columns.get_loc('adx')] = min(adx_val, 100)
    
    df['adx'] = df['adx'].fillna(50.0)
    
    return df

def prepare_features(df, feature_cols):
    """准备特征"""
    df_clean = df.dropna(subset=feature_cols).copy()
    return df_clean

def train_ensemble_model(X_train, y_train, stock_type='normal'):
    """
    训练集成模型
    根据股票类型选择不同参数
    """
    models = {}
    
    # === 随机森林 ===
    if stock_type == 'blue_chip':
        rf_params = {'n_estimators': 150, 'max_depth': 20, 'min_samples_split': 5, 'random_state': 42}
    elif stock_type == 'small_cap':
        rf_params = {'n_estimators': 100, 'max_depth': 10, 'min_samples_split': 10, 'random_state': 42}
    else:
        rf_params = {'n_estimators': 120, 'max_depth': 15, 'min_samples_split': 5, 'random_state': 42}
    
    rf = RandomForestRegressor(**rf_params, n_jobs=-1)
    rf.fit(X_train, y_train)
    models['rf'] = rf
    
    # === 梯度提升 ===
    if stock_type == 'blue_chip':
        gb_params = {'n_estimators': 100, 'max_depth': 8, 'learning_rate': 0.05, 'random_state': 42}
    else:
        gb_params = {'n_estimators': 80, 'max_depth': 6, 'learning_rate': 0.1, 'random_state': 42}
    
    gb = GradientBoostingRegressor(**gb_params)
    gb.fit(X_train, y_train)
    models['gb'] = gb
    
    return models

def ensemble_predict(models, X_test, weights=None):
    """集成预测"""
    if weights is None:
        weights = {'rf': 0.6, 'gb': 0.4}
    
    predictions = {}
    for name, model in models.items():
        predictions[name] = model.predict(X_test)
    
    # 加权平均
    final_pred = np.zeros(len(X_test))
    for name, pred in predictions.items():
        final_pred += weights.get(name, 1/len(models)) * pred
    
    return final_pred

def optimize_weights(models, X_val, y_val):
    """优化集成权重"""
    from scipy.optimize import minimize
    
    def objective(w):
        w = np.array(w)
        w = w / w.sum()  # 归一化
        pred = sum(w[i] * list(models.values())[i].predict(X_val) for i in range(len(w)))
        return mean_squared_error(y_val, pred)
    
    # 约束：权重和为1，都大于0
    constraints = {'type': 'eq', 'fun': lambda w: sum(w) - 1}
    bounds = [(0.0, 1.0) for _ in range(len(models))]
    
    # 初始权重
    x0 = [1/len(models)] * len(models)
    
    result = minimize(objective, x0, bounds=bounds, constraints=constraints, method='SLSQP')
    optimal_weights = result.x / result.x.sum()
    
    return dict(zip(models.keys(), optimal_weights))

def evaluate_prediction(actual, predicted):
    """评估预测"""
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    
    # 方向准确率
    if len(actual) > 1:
        actual_dir = np.sign(np.diff(actual))
        pred_dir = np.sign(np.diff(predicted))
        direction_acc = np.mean(actual_dir == pred_dir) * 100
    else:
        direction_acc = 50.0
    
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'direction_accuracy': direction_acc}

def select_stocks_ranking():
    """
    基于多因子模型进行股票排名选股
    """
    print("=" * 80)
    print("📊 智能选股模型 - 多因子评分系统")
    print("=" * 80)
    
    feature_cols = [
        'return_5', 'return_20', 'ma_ratio_20', 'volatility_20',
        'rsi_14', 'rsi_oversold_14', 'macd_hist', 'bb_position_20',
        'volume_ratio', 'momentum_20', 'price_position', 'adx'
    ]
    
    # 获取所有股票
    all_stocks = []
    for f in DATA_DIR.glob("*.csv"):
        code = f.stem
        if code.isdigit() and len(code) == 6:
            all_stocks.append(code)
    
    print(f"\n📈 分析股票数量: {len(all_stocks)}")
    
    stock_scores = []
    
    for code in all_stocks:
        df = load_stock_data(code)
        if df is None or len(df) < 200:
            continue
        
        df = calculate_advanced_features(df)
        df = prepare_features(df, feature_cols)
        
        if len(df) < 100:
            continue
        
        latest = df.iloc[-1]
        
        # === 多因子评分 ===
        score = 0
        factors = {}
        
        # 1. 动量因子 (30%)
        momentum = latest.get('momentum_20', 0)
        if momentum > 0.05:
            score += 30
            factors['momentum'] = '强'
        elif momentum > 0:
            score += 15
            factors['momentum'] = '中'
        else:
            score += 0
            factors['momentum'] = '弱'
        
        # 2. 趋势因子 (25%)
        ma_ratio = latest.get('ma_ratio_20', 1)
        if ma_ratio > 1.02:
            score += 25
            factors['trend'] = '多头'
        elif ma_ratio > 0.98:
            score += 12
            factors['trend'] = '震荡'
        else:
            score += 0
            factors['trend'] = '空头'
        
        # 3. 波动率因子 (15%) - 低波动更好
        volatility = latest.get('volatility_20', 0.05)
        if volatility < 0.02:
            score += 15
            factors['volatility'] = '低'
        elif volatility < 0.04:
            score += 8
            factors['volatility'] = '中'
        else:
            score += 0
            factors['volatility'] = '高'
        
        # 4. RSI因子 (15%)
        rsi = latest.get('rsi_14', 50)
        if 40 < rsi < 60:
            score += 15
            factors['rsi'] = '正常'
        elif rsi < 30:
            score += 5
            factors['rsi'] = '超卖'
        elif rsi > 70:
            score += 5
            factors['rsi'] = '超买'
        else:
            score += 8
            factors['rsi'] = '中性'
        
        # 5. 成交量因子 (15%)
        volume_ratio = latest.get('volume_ratio', 1)
        if 0.8 < volume_ratio < 2.0:
            score += 15
            factors['volume'] = '正常'
        elif volume_ratio >= 2:
            score += 10
            factors['volume'] = '放量'
        else:
            score += 5
            factors['volume'] = '缩量'
        
        stock_scores.append({
            'code': code,
            'score': score,
            'momentum': factors['momentum'],
            'trend': factors['trend'],
            'volatility': factors['volatility'],
            'rsi': factors['rsi'],
            'volume': factors['volume'],
            'close': latest['close'],
            'rsi_value': rsi,
            'momentum_value': momentum
        })
    
    # 按分数排序
    stock_scores = sorted(stock_scores, key=lambda x: x['score'], reverse=True)
    
    # 输出TOP 20
    print("\n🏆 TOP 20 精选股票:")
    print("-" * 100)
    print(f"{'排名':<4} {'代码':<10} {'得分':<6} {'动量':<6} {'趋势':<6} {'波动':<6} {'RSI':<6} {'量能':<6} {'收盘价':<10}")
    print("-" * 100)
    
    for i, s in enumerate(stock_scores[:20], 1):
        print(f"{i:<4} {s['code']:<10} {s['score']:<6} {s['momentum']:<6} {s['trend']:<6} {s['volatility']:<6} {s['rsi']:<6} {s['volume']:<6} {s['close']:.2f}")
    
    return stock_scores[:20]

def run_optimized_prediction(stock_list):
    """运行优化后的预测"""
    print("\n" + "=" * 80)
    print("🤖 优化版价格预测")
    print("=" * 80)
    
    feature_cols = [
        'return_1', 'return_5', 'return_20', 'ma_ratio_5', 'ma_ratio_20',
        'volatility_5', 'volatility_20', 'rsi_14', 'macd_hist', 'bb_position_20',
        'volume_ratio', 'momentum_5', 'momentum_20', 'price_position'
    ]
    
    results = []
    
    for s in stock_list[:20]:  # 预测TOP 20
        code = s['code']
        name = s.get('code', code)
        
        df = load_stock_data(code)
        if df is None or len(df) < 500:
            continue
        
        df = calculate_advanced_features(df)
        train_df = df[df['date'] < '2026-02-01'].copy()
        test_df = df[(df['date'] >= '2026-02-01') & (df['date'] <= '2026-02-06')].copy()
        
        if len(test_df) < 3:
            continue
        
        train_df = prepare_features(train_df, feature_cols)
        
        if len(train_df) < 200:
            continue
        
        X_train = train_df[feature_cols].values
        y_train = train_df['close'].values
        
        # 分离验证集优化权重
        val_size = int(len(X_train) * 0.1)
        X_tr, X_val = X_train[:-val_size], X_train[-val_size:]
        y_tr, y_val = y_train[:-val_size], y_train[-val_size:]
        
        # 训练集成模型
        stock_type = 'blue_chip' if s['score'] > 70 else 'normal'
        models = train_ensemble_model(X_tr, y_tr, stock_type)
        
        # 优化权重
        try:
            weights = optimize_weights(models, X_val, y_val)
        except:
            weights = {'rf': 0.6, 'gb': 0.4}
        
        # 预测
        predictions = []
        actuals = []
        
        for idx, row in test_df.iterrows():
            features = row[feature_cols].values.astype(float)
            if not np.any(np.isnan(features)):
                pred = ensemble_predict(models, features.reshape(1, -1), weights)[0]
                predictions.append(pred)
                actuals.append(row['close'])
        
        if len(predictions) < 2:
            continue
        
        metrics = evaluate_prediction(actuals, predictions)
        
        results.append({
            'code': code,
            'name': name,
            'score': s['score'],
            'actual_last': actuals[-1],
            'predicted_last': predictions[-1],
            'mape': metrics['MAPE'],
            'direction_acc': metrics['direction_accuracy'],
            'weights': weights
        })
        
        print(f"  已完成 {len(results)}/20...")
    
    # 汇总
    print("\n" + "=" * 80)
    print("📊 预测结果汇总")
    print("=" * 80)
    
    if not results:
        print("❌ 无有效结果")
        return
    
    total_mape = np.mean([r['mape'] for r in results])
    total_dir_acc = np.mean([r['direction_acc'] for r in results])
    
    print(f"\n✅ 成功预测 {len(results)} 只股票")
    print(f"📊 平均MAPE: {total_mape:.2f}%")
    print(f"📊 平均方向准确率: {total_dir_acc:.1f}%")
    
    # 分类
    excellent = [r for r in results if r['mape'] < 5]
    good = [r for r in results if 5 <= r['mape'] < 10]
    fair = [r for r in results if 10 <= r['mape'] < 20]
    poor = [r for r in results if r['mape'] >= 20]
    
    print(f"\n📈 预测准确性分布:")
    print(f"  🟢 优秀 (MAPE<5%): {len(excellent)} 只")
    print(f"  🟡 良好 (5-10%): {len(good)} 只")
    print(f"  🟠 一般 (10-20%): {len(fair)} 只")
    print(f"  🔴 较差 (>20%): {len(poor)} 只")
    
    # 保存结果
    output_file = OUTPUT_DIR / "optimized_prediction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'stocks_tested': len(results),
            'total_mape': total_mape,
            'total_direction_accuracy': total_dir_acc,
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存至: {output_file}")
    
    return results

def run_full_pipeline():
    """运行完整流程"""
    print("\n" + "=" * 80)
    print("🚀 A股智能选股与价格预测系统 - 优化版")
    print("=" * 80)
    
    # 1. 选股
    top_stocks = select_stocks_ranking()
    
    # 2. 预测
    results = run_optimized_prediction(top_stocks)
    
    return results

if __name__ == "__main__":
    run_full_pipeline()
