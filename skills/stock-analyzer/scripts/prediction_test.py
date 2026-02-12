#!/usr/bin/env python3
"""
A股预测模型验证测试
使用历史数据训练模型，预测2026年2月交易数据，并与真实数据比对
"""
import os
import sys
import json
import warnings
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# 配置
DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 测试股票列表（选择不同板块）
TEST_STOCKS = [
    ("600519", "贵州茅台"),  # 沪市蓝筹
    ("601398", "工商银行"),  # 银行
    ("600030", "中信证券"),  # 券商
    ("000002", "万  科Ａ"),  # 深市地产
    ("300750", "宁德时代"),  # 创业板新能源
    ("002594", "比亚迪"),    # 整车
    ("600028", "中国石化"),  # 石油
    ("000651", "格力电器"),  # 家电
    ("300760", "迈为股份"),  # 医疗
    ("603986", "兆易创新"),  # 芯片
    ("600036", "招商银行"),  # 银行
    ("000001", "平安银行"),  # 银行
]

def load_stock_data(code):
    """加载股票数据"""
    filepath = DATA_DIR / f"{code}.csv"
    if not filepath.exists():
        return None
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        
        # 根据列数判断格式
        n_cols = df.shape[1]
        
        if n_cols == 2:
            # 简化格式: date, open -> date, close
            df.columns = ['date', 'close']
        elif n_cols == 6:
            # 沪市格式: date,open,high,low,close,volume
            pass  # 列名已经正确
        elif n_cols == 12:
            # 完整历史格式
            df.columns = ['date', 'code', 'open', 'close', 'high', 'low', 
                         'volume', 'amount', 'amplitude', 'pct_change', 
                         'change', 'turnover']
            df = df[['date', 'open', 'close', 'high', 'low', 'volume']]
        else:
            print(f"  ⚠️ 未知格式: {n_cols} 列")
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 确保数值列是数值类型
        for col in ['open', 'close', 'high', 'low']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'volume' in df.columns:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # 如果没有volume列，创建默认值
        if 'volume' not in df.columns:
            df['volume'] = 1.0
        
        return df
    except Exception as e:
        print(f"加载 {code} 数据失败: {e}")
        return None

def calculate_technical_features(df):
    """计算技术指标特征"""
    df = df.copy()
    
    # 价格特征
    df['return'] = df['close'].pct_change()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # 移动平均
    for window in [5, 10, 20, 60]:
        df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
        df[f'ma_ratio_{window}'] = df['close'] / df[f'ma_{window}']
    
    # 波动率
    df['volatility_5'] = df['return'].rolling(window=5).std()
    df['volatility_20'] = df['return'].rolling(window=20).std()
    
    # RSI
    for period in [7, 14, 21]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 布林带
    for period in [20]:
        df[f'bb_mid_{period}'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df[f'bb_upper_{period}'] = df[f'bb_mid_{period}'] + 2 * bb_std
        df[f'bb_lower_{period}'] = df[f'bb_mid_{period}'] - 2 * bb_std
        df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / df[f'bb_mid_{period}']
        df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])
    
    # 成交量特征
    df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma_5']
    
    # 动量
    for period in [5, 10, 20]:
        df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
    
    return df

def prepare_features(df, feature_cols):
    """准备特征矩阵"""
    df_clean = df.dropna(subset=feature_cols).copy()
    return df_clean

def train_lstm_model(X_train, y_train):
    """简单LSTM模型（使用sklearn的MLP替代）"""
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1
    )
    model.fit(X_scaled, y_train)
    
    return model, scaler

def train_xgboost_model(X_train, y_train):
    """XGBoost模型"""
    try:
        import xgboost as xgb
        
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        return model
    except (ImportError, ModuleNotFoundError):
        print("  ⚠️ XGBoost未安装，使用随机森林替代")
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        return model

def predict_next_day(model, scaler, last_features, model_type='lstm'):
    """预测下一天价格"""
    if model_type == 'lstm':
        X = scaler.transform(last_features.reshape(1, -1))
    else:
        X = last_features.reshape(1, -1)
    
    pred = model.predict(X)[0]
    return pred

def evaluate_prediction(actual, predicted):
    """评估预测准确性"""
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    # 计算各种误差指标
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    
    # 方向准确率
    actual_dir = np.sign(np.diff(actual))
    pred_dir = np.sign(np.diff(predicted))
    direction_acc = np.mean(actual_dir == pred_dir) * 100
    
    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape,
        'direction_accuracy': direction_acc
    }

def run_prediction_test():
    """运行预测测试"""
    print("=" * 80)
    print("🤖 A股预测模型验证测试")
    print("=" * 80)
    print(f"\n📅 测试日期范围: 2026-02-01 ~ 2026-02-06")
    print(f"📊 测试股票数量: {len(TEST_STOCKS)}")
    
    # 特征列
    feature_cols = [
        'return', 'log_return', 'ma_ratio_5', 'ma_ratio_10', 'ma_ratio_20',
        'volatility_5', 'volatility_20', 'rsi_14', 'macd', 'macd_signal',
        'macd_hist', 'bb_position_20', 'volume_ratio', 'momentum_5', 'momentum_10'
    ]
    
    results = []
    
    for code, name in TEST_STOCKS:
        print(f"\n{'='*60}")
        print(f"📈 测试 {code} ({name})")
        print(f"{'='*60}")
        
        # 加载数据
        df = load_stock_data(code)
        if df is None or len(df) < 100:
            print(f"  ❌ 数据不足，跳过")
            continue
        
        # 计算特征
        df = calculate_technical_features(df)
        
        # 分离训练数据和测试数据
        # 训练: 2021-01-01 ~ 2026-01-31
        # 测试: 2026-02-01 ~ 2026-02-06
        train_df = df[df['date'] < '2026-02-01'].copy()
        test_df = df[(df['date'] >= '2026-02-01') & (df['date'] <= '2026-02-06')].copy()
        
        if len(test_df) < 3:
            print(f"  ❌ 测试数据不足，跳过")
            continue
        
        train_df = prepare_features(train_df, feature_cols)
        
        if len(train_df) < 50:
            print(f"  ❌ 训练数据不足，跳过")
            continue
        
        # 准备训练数据
        X_train = train_df[feature_cols].values
        y_train = train_df['close'].values
        
        # 训练模型
        print(f"  📊 训练数据: {len(train_df)} 条")
        print(f"  📊 测试数据: {len(test_df)} 条")
        
        # XGBoost模型
        xgb_model = train_xgboost_model(X_train, y_train)
        
        # 预测
        predictions = []
        actuals = []
        dates = []
        
        for idx, row in test_df.iterrows():
            features = row[feature_cols].values.astype(float)
            
            if not np.any(np.isnan(features)):
                pred = xgb_model.predict(features.reshape(1, -1))[0]
                predictions.append(pred)
                actuals.append(row['close'])
                dates.append(row['date'])
        
        if len(predictions) < 2:
            print(f"  ❌ 预测结果不足，跳过")
            continue
        
        # 评估
        metrics = evaluate_prediction(actuals, predictions)
        
        print(f"\n  📊 预测结果:")
        print(f"     预测天数: {len(predictions)}")
        print(f"     MAE: {metrics['MAE']:.2f}")
        print(f"     RMSE: {metrics['RMSE']:.2f}")
        print(f"     MAPE: {metrics['MAPE']:.2f}%")
        print(f"     方向准确率: {metrics['direction_accuracy']:.1f}%")
        
        print(f"\n  📈 价格对比:")
        for i, (date, actual, pred) in enumerate(zip(dates[:5], actuals[:5], predictions[:5])):
            error_pct = (pred - actual) / actual * 100
            direction = "✓" if np.sign(pred - actuals[i-1]) == np.sign(actual - actuals[i-1]) else "✗" if i > 0 else "-"
            print(f"     {date.strftime('%Y-%m-%d')}: 实际={actual:.2f}, 预测={pred:.2f}, 误差={error_pct:+.1f}% {direction}")
        
        results.append({
            'code': code,
            'name': name,
            'actual_last': actuals[-1],
            'predicted_last': predictions[-1],
            'mape': metrics['MAPE'],
            'direction_acc': metrics['direction_accuracy'],
            'predictions': predictions,
            'actuals': actuals,
            'dates': [str(d) for d in dates]
        })
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 预测结果汇总")
    print("=" * 80)
    
    if not results:
        print("❌ 没有有效的测试结果")
        return
    
    # 计算总体指标
    total_mape = np.mean([r['mape'] for r in results])
    total_dir_acc = np.mean([r['direction_acc'] for r in results])
    
    print(f"\n✅ 成功测试 {len(results)} 只股票")
    print(f"📊 平均MAPE: {total_mape:.2f}%")
    print(f"📊 平均方向准确率: {total_dir_acc:.1f}%")
    
    print(f"\n📋 详细结果:")
    print("-" * 80)
    print(f"{'代码':<10} {'名称':<10} {'实际收盘':<12} {'预测收盘':<12} {'MAPE':<10} {'方向准确率':<10}")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['mape']):
        print(f"{r['code']:<10} {r['name']:<10} {r['actual_last']:<12.2f} {r['predicted_last']:<12.2f} {r['mape']:<10.2f}% {r['direction_acc']:<10.1f}%")
    
    # 保存结果
    output_file = OUTPUT_DIR / "prediction_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'stocks_tested': len(results),
            'total_mape': total_mape,
            'total_direction_accuracy': total_dir_acc,
            'results': results
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 结果已保存至: {output_file}")
    
    return results

if __name__ == "__main__":
    run_prediction_test()
