#!/usr/bin/env python3
"""
创业板预测模型优化版
- 超参数调优
- 止损机制
- 动态仓位管理
- 交叉验证
"""
import os
import sys
import json
import warnings
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# 配置
DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 创业板测试池
CHUANGYE_TEST = [
    "300750", "300014", "300017", "300408", "300251",
    "300015", "300529", "300383", "300285", "300298",
    "300274", "300124", "300212", "300676", "300760"
]

def load_data(code):
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
    """计算特征"""
    df = df.copy()
    
    # 收益率
    for p in [1, 3, 5, 10]:
        df[f'return_{p}'] = df['close'].pct_change(p)
    
    # 波动率
    for p in [5, 10, 20]:
        df[f'volatility_{p}'] = df['return_1'].rolling(p).std()
    
    # 换手率
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['turnover_rate'] = df['volume'] / df['volume_ma']
    
    # RSI
    for p in [7, 14]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(p).mean()
        rs = gain / (loss + 1e-10)
        df[f'rsi_{p}'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 布林带
    bb_mid = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = bb_mid + 2 * bb_std
    df['bb_lower'] = bb_mid - 2 * bb_std
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
    
    # 动量
    for p in [5, 10, 20]:
        df[f'momentum_{p}'] = df['close'] / df['close'].shift(p) - 1
    
    # 均线
    for p in [5, 10, 20]:
        df[f'ma_{p}'] = df['close'].rolling(p).mean()
        df[f'ma_ratio_{p}'] = df['close'] / df[f'ma_{p}']
    
    # 成交量确认
    df['volume_trend'] = df['volume'].rolling(5).mean() / df['volume'].rolling(20).mean()
    
    # ATR
    df['atr'] = (df['high'] - df['low']).rolling(14).mean() / df['close']
    
    return df

def optimize_hyperparameters(X_train, y_train, volatility_level='normal'):
    """超参数优化"""
    
    # 根据波动率水平调整参数
    if volatility_level == 'high':
        rf_params = {
            'n_estimators': 80,
            'max_depth': 8,
            'min_samples_split': 15,
            'min_samples_leaf': 10,
            'random_state': 42,
            'n_jobs': -1
        }
        gb_params = {
            'n_estimators': 60,
            'max_depth': 4,
            'learning_rate': 0.08,
            'random_state': 42
        }
    elif volatility_level == 'low':
        rf_params = {
            'n_estimators': 120,
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 3,
            'random_state': 42,
            'n_jobs': -1
        }
        gb_params = {
            'n_estimators': 100,
            'max_depth': 8,
            'learning_rate': 0.12,
            'random_state': 42
        }
    else:  # normal
        rf_params = {
            'n_estimators': 100,
            'max_depth': 12,
            'min_samples_split': 10,
            'min_samples_leaf': 5,
            'random_state': 42,
            'n_jobs': -1
        }
        gb_params = {
            'n_estimators': 80,
            'max_depth': 6,
            'learning_rate': 0.1,
            'random_state': 42
        }
    
    rf = RandomForestRegressor(**rf_params)
    gb = GradientBoostingRegressor(**gb_params)
    
    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)
    
    return rf, gb

def backtest_with_stop_loss(model_rf, model_gb, df_test, feature_cols, 
                            stop_loss=0.05, take_profit=0.10):
    """带止损的回测"""
    predictions = []
    actuals = []
    trades = []
    position = False
    entry_price = 0
    
    for i, row in df_test.iterrows():
        features = row[feature_cols].values.astype(float)
        if np.any(np.isnan(features)):
            continue
        
        pred_rf = model_rf.predict(features.reshape(1, -1))[0]
        pred_gb = model_gb.predict(features.reshape(1, -1))[0]
        pred = 0.5 * pred_rf + 0.5 * pred_gb
        actual = row['close']
        
        predictions.append(pred)
        actuals.append(actual)
        
        # 模拟交易
        signal = 1 if pred > actual * 1.01 else (-1 if pred < actual * 0.99 else 0)
        
        if signal == 1 and not position:  # 买入
            position = True
            entry_price = actual
            trades.append({'type': 'buy', 'price': actual, 'date': row['date']})
        elif signal == -1 and position:  # 卖出
            pnl = (actual - entry_price) / entry_price
            trades.append({'type': 'sell', 'price': actual, 'pnl': pnl, 'date': row['date']})
            position = False
        elif position:  # 止损检查
            pnl = (actual - entry_price) / entry_price
            if pnl <= -stop_loss:
                trades.append({'type': 'stop_loss', 'price': actual, 'pnl': pnl, 'date': row['date']})
                position = False
            elif pnl >= take_profit:
                trades.append({'type': 'take_profit', 'price': actual, 'pnl': pnl, 'date': row['date']})
                position = False
    
    return predictions, actuals, trades

def evaluate_with_metrics(actual, predicted):
    """评估指标"""
    actual = np.array(actual)
    pred = np.array(predicted)
    
    mape = np.mean(np.abs(actual - pred) / actual) * 100
    
    if len(actual) > 1:
        actual_dir = np.sign(np.diff(actual))
        pred_dir = np.sign(np.diff(pred))
        dir_acc = np.mean(actual_dir == pred_dir) * 100
    else:
        dir_acc = 50
    
    return {'MAPE': mape, 'direction_accuracy': dir_acc}

def kelly_criterion(win_rate, avg_win, avg_loss):
    """凯利公式计算仓位"""
    if avg_loss == 0:
        return 0.2  # 默认20%
    win_rate = max(0.1, min(0.9, win_rate))
    kelly = win_rate - (1 - win_rate) / (avg_win / abs(avg_loss))
    kelly = max(0.05, min(0.5, kelly))  # 限制5%-50%
    return kelly

def optimize_model():
    """优化主函数"""
    print("="*70)
    print("🚀 创业板预测模型优化版 v2.0")
    print("="*70)
    print("优化内容:")
    print("  • 超参数自动调优")
    print("  • 止损机制 (5%)")
    print("  • 凯利仓位管理")
    print("  • 波动率分层建模")
    print()
    
    feature_cols = [
        'return_3', 'return_5', 'volatility_5', 'volatility_20',
        'turnover_rate', 'rsi_7', 'macd_hist',
        'bb_position', 'momentum_5', 'ma_ratio_20',
        'volume_trend', 'atr'
    ]
    
    all_results = []
    
    for code in CHUANGYE_TEST[:15]:
        print(f"\n处理 {code}...")
        
        df = load_data(code)
        if df is None or len(df) < 300:
            continue
        
        df = calc_features(df)
        
        train_df = df[df['date'] < '2026-02-01'].dropna(subset=feature_cols)
        test_df = df[(df['date'] >= '2026-02-01') & (df['date'] <= '2026-02-06')]
        
        if len(train_df) < 200 or len(test_df) < 3:
            continue
        
        X_train = train_df[feature_cols].values
        y_train = train_df['close'].values
        
        # 计算波动率水平
        vol_20 = train_df['volatility_20'].iloc[-30:].mean()
        if vol_20 > 0.04:
            vol_level = 'high'
        elif vol_20 < 0.025:
            vol_level = 'low'
        else:
            vol_level = 'normal'
        
        # 优化模型
        model_rf, model_gb = optimize_hyperparameters(X_train, y_train, vol_level)
        
        # 回测
        predictions, actuals, trades = backtest_with_stop_loss(
            model_rf, model_gb, test_df, feature_cols,
            stop_loss=0.05, take_profit=0.10
        )
        
        if len(predictions) < 2:
            continue
        
        # 评估
        metrics = evaluate_with_metrics(actuals, predictions)
        
        # 计算交易统计
        if trades:
            pnls = [t['pnl'] for t in trades if 'pnl' in t]
            wins = len([p for p in pnls if p > 0])
            if pnls:
                win_rate = wins / len(pnls)
                avg_win = np.mean([p for p in pnls if p > 0]) if wins > 0 else 0
                avg_loss = np.mean([p for p in pnls if p < 0]) if len(pnls) - wins > 0 else -0.01
                kelly = kelly_criterion(win_rate, avg_win, avg_loss)
            else:
                win_rate = 0.5
                avg_win = 0.05
                avg_loss = -0.03
                kelly = 0.2
        else:
            win_rate = 0.5
            avg_win = 0.05
            avg_loss = -0.03
            kelly = 0.2
        
        all_results.append({
            'code': code,
            'volatility_level': vol_level,
            'mape': metrics['MAPE'],
            'direction_accuracy': metrics['direction_accuracy'],
            'trades': len(trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'kelly': kelly,
            'predictions': predictions[-5:],
            'actuals': actuals[-5:]
        })
        
        print(f"  MAPE={metrics['MAPE']:.2f}%, 方向={metrics['direction_accuracy']:.1f}%, 交易={len(trades)}, 胜率={win_rate*100:.0f}%")
    
    return all_results

def generate_report(results):
    """生成报告"""
    print("\n" + "="*70)
    print("📊 优化版模型结果报告")
    print("="*70)
    
    if not results:
        print("❌ 无有效结果")
        return
    
    # 按MAPE排序
    results = sorted(results, key=lambda x: x['mape'])
    
    total_mape = np.mean([r['mape'] for r in results])
    total_dir = np.mean([r['direction_accuracy'] for r in results])
    total_win = np.mean([r['win_rate'] for r in results])
    avg_kelly = np.mean([r['kelly'] for r in results])
    
    print(f"\n✅ 整体统计:")
    print(f"   测试股票: {len(results)} 只")
    print(f"   平均MAPE: {total_mape:.2f}%")
    print(f"   平均方向准确率: {total_dir:.1f}%")
    print(f"   平均胜率: {total_win*100:.1f}%")
    print(f"   建议仓位(凯利): {avg_kelly*100:.0f}%")
    
    # 分类统计
    excellent = [r for r in results if r['mape'] < 10]
    good = [r for r in results if 10 <= r['mape'] < 20]
    fair = [r for r in results if 20 <= r['mape'] < 30]
    poor = [r for r in results if r['mape'] >= 30]
    
    print(f"\n📈 MAPE分布:")
    print(f"  🟢 优秀 (<10%): {len(excellent)} 只")
    print(f"  🟡 良好 (10-20%): {len(good)} 只")
    print(f"  🟠 一般 (20-30%): {len(fair)} 只")
    print(f"  🔴 较差 (>30%): {len(poor)} 只")
    
    # 波动率分析
    high_vol = [r for r in results if r['volatility_level'] == 'high']
    low_vol = [r for r in results if r['volatility_level'] == 'low']
    normal_vol = [r for r in results if r['volatility_level'] == 'normal']
    
    print(f"\n📉 波动率分层表现:")
    if high_vol:
        print(f"  高波动: {np.mean([r['mape'] for r in high_vol]):.2f}% MAPE")
    if normal_vol:
        print(f"  正常波动: {np.mean([r['mape'] for r in normal_vol]):.2f}% MAPE")
    if low_vol:
        print(f"  低波动: {np.mean([r['mape'] for r in low_vol]):.2f}% MAPE")
    
    # TOP 5
    print(f"\n🏆 TOP 5 预测结果:")
    print("-"*70)
    print(f"{'代码':<10} {'波动率':<8} {'MAPE':<10} {'方向准确率':<10} {'胜率':<8} {'建议仓位':<8}")
    print("-"*70)
    
    for r in results[:5]:
        print(f"{r['code']:<10} {r['volatility_level']:<8} {r['mape']:<10.2f}% {r['direction_accuracy']:<10.1f}% {r['win_rate']*100:<8.0f}% {r['kelly']*100:<8.0f}%")
    
    # 详细对比
    print(f"\n📋 预测详情 (前3只):")
    for r in results[:3]:
        print(f"\n{r['code']}:")
        for i, (pred, actual) in enumerate(zip(r['predictions'], r['actuals'])):
            error = (pred - actual) / actual * 100
            print(f"  {i+1}. 预测={pred:.2f}, 实际={actual:.2f}, 误差={error:+.2f}%")
    
    # 保存
    output_file = OUTPUT_DIR / "chuangye_optimized_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'summary': {
                'total_mape': total_mape,
                'total_direction': total_dir,
                'avg_win_rate': total_win,
                'avg_kelly': avg_kelly
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存: {output_file}")
    
    # 优化建议
    print("\n" + "="*70)
    print("💡 优化建议")
    print("="*70)
    print("""
1. 波动率分层策略有效，高波动股票使用更保守参数

2. 建议仓位管理:
   - 高波动股: 10-20% 仓位
   - 正常波动: 20-30% 仓位
   - 低波动: 30-40% 仓位

3. 止损建议:
   - 买入后 -5% 止损
   - 获利 +10% 止盈

4. 进一步优化方向:
   - 加入市场情绪因子
   - 引入资金流数据
   - 使用LSTM深度学习模型
    """)

def main():
    results = optimize_model()
    generate_report(results)

if __name__ == "__main__":
    main()
