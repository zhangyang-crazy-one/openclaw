#!/usr/bin/env python3
"""
创业板智能选股与价格预测模型
特点：高波动性、散户主导、成长性强、小市值
"""
import os
import sys
import json
import warnings
import random
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# 配置
DATA_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据/predictions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 创业板股票池（选取不同行业代表）
CHUANGYE_POOL = [
    # 新能源
    "300750",  # 宁德时代
    "300014",  # 亿纬锂能
    "300274",  # 阳光电源
    # 医药
    "300015",  # 爱尔眼科
    "300003",  # 乐普医疗
    "300529",  # 健帆生物
    # 科技
    "300059",  # 东方财富
    "300212",  # 易华录
    "300017",  # 网宿科技
    # 制造业
    "300124",  # 汇川技术
    "300285",  # 国瓷材料
    "300383",  # 光环新网
    # 消费
    "300146",  # 中科创达
    "300251",  # 光线传媒
    "300298",  # 三诺生物
    # 创业板50权重
    "300760",  # 迈为股份
    "300676",  # 华为技术
    "300618",  # 寒锐钴业
    "300433",  # 蓝思科技
    "300408",  # 艾比森
]

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
        else:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['close', 'high', 'low', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna()
    except:
        return None

def calculate_chuangye_features(df):
    """
    计算创业板专用因子
    创业板特点：高波动、高换手、成长性强
    """
    df = df.copy()
    
    # === 收益率因子（创业板波动大，用多周期）===
    df['return_1'] = df['close'].pct_change(1)
    df['return_3'] = df['close'].pct_change(3)
    df['return_5'] = df['close'].pct_change(5)
    df['return_10'] = df['close'].pct_change(10)
    
    # === 波动率因子（创业板需要更敏感的波动率）===
    for window in [3, 5, 10, 20]:
        df[f'volatility_{window}'] = df['return_1'].rolling(window=window).std()
        df[f'atr_{window}'] = (df['high'] - df['low']).rolling(window=window).mean() / df['close']
    
    # === 换手率因子（创业板换手率高）===
    df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
    df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
    df['turnover_rate'] = df['volume'] / df['volume_ma_20']  # 换手率倍数
    df['volume_trend'] = df['volume_ma_5'] / df['volume_ma_20']
    
    # === RSI因子（创业板RSI更敏感）===
    for period in [7, 14]:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
    
    # === MACD因子 ===
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # === 布林带因子（创业板波动大，布林带更宽）===
    for period in [20]:
        df[f'bb_mid_{period}'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df[f'bb_upper_{period}'] = df[f'bb_mid_{period}'] + 2 * bb_std
        df[f'bb_lower_{period}'] = df[f'bb_mid_{period}'] - 2 * bb_std
        df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'] + 1e-10)
        df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / df[f'bb_mid_{period}']
    
    # === 动量因子（创业板动量效应强）===
    for period in [5, 10, 20]:
        df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
    
    # === 移动平均因子 ===
    for window in [5, 10, 20]:
        df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
        df[f'ma_ratio_{window}'] = df['close'] / df[f'ma_{window}']
    
    # === 成交量确认因子 ===
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
    df['obv_ma'] = df['obv'].rolling(window=10).mean()
    
    # === 价格位置（创业板弹性大）===
    df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / (df['high'].rolling(20).max() - df['low'].rolling(20).min() + 1e-10)
    
    return df

def select_chuangye_stocks():
    """
    创业板选股模型
    考虑因素：动量、波动率、换手率、RSI
    """
    print("="*70)
    print("🚀 创业板智能选股系统")
    print("="*70)
    print(f"分析创业板特点: 高波动、高换手、成长性强")
    print()
    
    feature_cols = [
        'return_5', 'return_10', 'volatility_5', 'volatility_20',
        'turnover_rate', 'rsi_7', 'rsi_14', 'macd_hist',
        'bb_position_20', 'momentum_5', 'momentum_10',
        'ma_ratio_20', 'price_position', 'volume_trend'
    ]
    
    stock_scores = []
    
    for code in CHUANGYE_POOL:
        df = load_stock_data(code)
        if df is None or len(df) < 200:
            continue
        
        df = calculate_chuangye_features(df)
        latest = df.iloc[-1]
        
        # === 创业板多因子评分 ===
        score = 0
        factors = {}
        
        # 1. 动量因子 (25%) - 创业板动量效应强
        mom = latest.get('momentum_5', 0)
        if mom > 0.03:
            score += 25
            factors['momentum'] = '强'
        elif mom > 0:
            score += 15
            factors['momentum'] = '中'
        else:
            score += 0
            factors['momentum'] = '弱'
        
        # 2. 波动率因子 (15%) - 适度波动
        vol = latest.get('volatility_20', 0.03)
        if 0.02 < vol < 0.05:
            score += 15
            factors['volatility'] = '适中'
        elif vol < 0.02:
            score += 10
            factors['volatility'] = '低'
        else:
            score += 5
            factors['volatility'] = '高'
        
        # 3. 换手率因子 (15%) - 活跃度
        turnover = latest.get('turnover_rate', 1)
        if 1.0 < turnover < 2.5:
            score += 15
            factors['turnover'] = '活跃'
        elif turnover >= 2.5:
            score += 10
            factors['turnover'] = '高换手'
        else:
            score += 5
            factors['turnover'] = '正常'
        
        # 4. RSI因子 (15%) - 不超买超卖
        rsi = latest.get('rsi_14', 50)
        if 40 < rsi < 60:
            score += 15
            factors['rsi'] = '正常'
        elif rsi < 30:
            score += 8
            factors['rsi'] = '超卖'
        elif rsi > 70:
            score += 5
            factors['rsi'] = '超买'
        else:
            score += 10
            factors['rsi'] = '中性'
        
        # 5. 趋势因子 (15%) - 均线确认
        ma_ratio = latest.get('ma_ratio_20', 1)
        if ma_ratio > 1.02:
            score += 15
            factors['trend'] = '多头'
        elif ma_ratio > 0.98:
            score += 8
            factors['trend'] = '震荡'
        else:
            score += 0
            factors['trend'] = '空头'
        
        # 6. 量能确认 (15%)
        vol_trend = latest.get('volume_trend', 1)
        if vol_trend > 1.1:
            score += 15
            factors['volume'] = '放量'
        elif vol_trend > 0.9:
            score += 8
            factors['volume'] = '稳定'
        else:
            score += 3
            factors['volume'] = '缩量'
        
        stock_scores.append({
            'code': code,
            'score': score,
            'momentum': factors['momentum'],
            'volatility': factors['volatility'],
            'turnover': factors['turnover'],
            'rsi': factors['rsi'],
            'trend': factors['trend'],
            'volume': factors['volume'],
            'close': latest['close'],
            'momentum_value': mom,
            'rsi_value': rsi
        })
    
    # 按分数排序
    stock_scores = sorted(stock_scores, key=lambda x: x['score'], reverse=True)
    
    print("🏆 TOP 10 精选创业板股票:")
    print("-"*70)
    print(f"{'排名':<4} {'代码':<10} {'得分':<6} {'动量':<6} {'波动':<6} {'换手':<6} {'RSI':<6} {'趋势':<6} {'收盘价':<10}")
    print("-"*70)
    
    for i, s in enumerate(stock_scores[:10], 1):
        print(f"{i:<4} {s['code']:<10} {s['score']:<6} {s['momentum']:<6} {s['volatility']:<6} {s['turnover']:<6} {s['rsi']:<6} {s['trend']:<6} {s['close']:.2f}")
    
    return stock_scores[:10]

def optimize_prediction_model(stock_list):
    """
    针对创业板优化预测模型
    创业板特点需要调整的参数
    """
    print("\n" + "="*70)
    print("🤖 创业板预测模型优化")
    print("="*70)
    print("模型特点: 适配高波动、小市值股票")
    print()
    
    # 创业板专用特征
    feature_cols = [
        'return_3', 'return_5', 'volatility_5', 'volatility_20',
        'turnover_rate', 'rsi_7', 'macd_hist',
        'bb_position_20', 'momentum_5', 'ma_ratio_20', 'volume_trend'
    ]
    
    results = []
    
    for s in stock_list:
        code = s['code']
        
        df = load_stock_data(code)
        if df is None:
            continue
        
        df = calculate_chuangye_features(df)
        
        train_df = df[df['date'] < '2026-02-01'].dropna(subset=feature_cols)
        test_df = df[(df['date'] >= '2026-02-01') & (df['date'] <= '2026-02-06')]
        
        if len(train_df) < 100 or len(test_df) < 2:
            continue
        
        X_train = train_df[feature_cols].values
        y_train = train_df['close'].values
        
        # 随机森林（创业板用较浅的树，防止过拟合）
        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,  # 创业板用较浅的树
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        
        # 梯度提升（创业板用更高的学习率）
        gb = GradientBoostingRegressor(
            n_estimators=80,
            max_depth=6,
            learning_rate=0.15,  # 创业板用更高的学习率
            random_state=42
        )
        gb.fit(X_train, y_train)
        
        # 预测
        preds, actuals = [], []
        
        for _, row in test_df.iterrows():
            features = row[feature_cols].values.astype(float)
            if not np.any(np.isnan(features)):
                # 集成预测
                pred_rf = rf.predict(features.reshape(1, -1))[0]
                pred_gb = gb.predict(features.reshape(1, -1))[0]
                pred = 0.5 * pred_rf + 0.5 * pred_gb
                
                preds.append(pred)
                actuals.append(row['close'])
        
        if len(preds) > 1:
            mape = np.mean(np.abs(np.array(preds) - np.array(actuals)) / np.array(actuals)) * 100
            
            # 方向准确率
            actual_dir = np.sign(np.diff(actuals))
            pred_dir = np.sign(np.diff(preds))
            direction_acc = np.mean(actual_dir == pred_dir) * 100 if len(actual_dir) > 0 else 50
            
            results.append({
                'code': code,
                'actual_last': actuals[-1],
                'predicted_last': preds[-1],
                'mape': mape,
                'direction_acc': direction_acc
            })
            
            print(f"  {code}: MAPE={mape:.2f}%, 方向准确率={direction_acc:.1f}%")
    
    return results

def analyze_and_report(top_stocks, predictions):
    """生成分析报告"""
    print("\n" + "="*70)
    print("📊 创业板分析报告")
    print("="*70)
    
    if not predictions:
        print("❌ 无有效预测结果")
        return
    
    predictions = sorted(predictions, key=lambda x: x['mape'])
    
    total_mape = np.mean([r['mape'] for r in predictions])
    total_dir = np.mean([r['direction_acc'] for r in predictions])
    
    print(f"\n✅ 预测统计:")
    print(f"   测试股票: {len(predictions)} 只")
    print(f"   平均MAPE: {total_mape:.2f}%")
    print(f"   平均方向准确率: {total_dir:.1f}%")
    
    # 分类
    excellent = [r for r in predictions if r['mape'] < 5]
    good = [r for r in predictions if 5 <= r['mape'] < 10]
    fair = [r for r in predictions if 10 <= r['mape'] < 20]
    poor = [r for r in predictions if r['mape'] >= 20]
    
    print(f"\n📈 预测准确性分布:")
    print(f"  🟢 优秀 (MAPE<5%): {len(excellent)} 只")
    print(f"  🟡 良好 (5-10%): {len(good)} 只")
    print(f"  🟠 一般 (10-20%): {len(fair)} 只")
    print(f"  🔴 较差 (>20%): {len(poor)} 只")
    
    print(f"\n🏆 TOP 5 预测结果:")
    print("-"*70)
    print(f"{'代码':<10} {'实际价格':<12} {'预测价格':<12} {'MAPE':<10} {'评级':<6}")
    print("-"*70)
    
    for r in predictions[:5]:
        if r['mape'] < 5:
            rating = '优秀'
        elif r['mape'] < 10:
            rating = '良好'
        elif r['mape'] < 20:
            rating = '一般'
        else:
            rating = '较差'
        
        print(f"{r['code']:<10} {r['actual_last']:<12.2f} {r['predicted_last']:<12.2f} {r['mape']:<10.2f}% {rating}")
    
    # 保存结果
    output_file = OUTPUT_DIR / "chuangye_prediction_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'top_stocks': top_stocks,
            'predictions': predictions,
            'summary': {
                'total_mape': total_mape,
                'total_direction': total_dir
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存: {output_file}")

def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 创业板智能选股与价格预测系统")
    print("="*70)
    print("创业板特点分析:")
    print("  • 高波动性: 日内波动大")
    print("  • 高换手率: 交易活跃")
    print("  • 成长性强: 科技创新企业集中")
    print("  • 小市值: 盘子小，易被操纵")
    print()
    
    # 1. 选股
    top_stocks = select_chuangye_stocks()
    
    if len(top_stocks) < 5:
        print("❌ 有效股票不足，无法继续")
        return
    
    # 2. 预测
    predictions = optimize_prediction_model(top_stocks)
    
    # 3. 报告
    analyze_and_report(top_stocks, predictions)

if __name__ == "__main__":
    main()
