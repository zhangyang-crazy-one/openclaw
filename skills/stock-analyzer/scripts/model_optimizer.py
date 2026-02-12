#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学术级A股量化分析系统 - 超参数优化器
使用时间序列交叉验证进行超参数调优

作者: OpenClaw Quant Team
版本: 1.0.0
"""

import numpy as np
import pandas as pd
import sys
sys.path.append('/home/liujerry/moltbot/skills/stock-analyzer/scripts')
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# 导入高级分析模块
import sys
sys.path.append('/home/liujerry/moltbot/skills/stock-analyzer/scripts')
import sys
sys.path.append('/home/liujerry/moltbot/skills/stock-analyzer/scripts')
from advanced_analysis import (
    AcademicStockAnalyzer, TechnicalIndicator, FeatureEngineer,
    MomentumStrategy, MeanReversionStrategy, MLPredictor, RiskEvaluator
)

# ============================================
# 超参数搜索空间
# ============================================

@dataclass
class HyperparameterSpace:
    """超参数搜索空间"""
    
    # 回溯期参数
    lookback_periods: List[int] = field(default_factory=lambda: [5, 10, 20, 60])
    
    # RSI参数
    rsi_periods: List[int] = field(default_factory=lambda: [7, 14, 21])
    rsi_oversold: List[float] = field(default_factory=lambda: [20, 25, 30])
    rsi_overbought: List[float] = field(default_factory=lambda: [70, 75, 80])
    
    # MACD参数 (fast, slow, signal)
    macd_fast: List[int] = field(default_factory=lambda: [8, 12])
    macd_slow: List[int] = field(default_factory=lambda: [17, 26])
    macd_signal: List[int] = field(default_factory=lambda: [7, 9])
    
    # 策略阈值
    momentum_thresholds: List[float] = field(default_factory=lambda: [0.02, 0.05, 0.10])
    mean_reversion_thresholds: List[float] = field(default_factory=lambda: [1.5, 2.0, 2.5])
    
    # ML模型参数
    rf_n_estimators: List[int] = field(default_factory=lambda: [50, 100, 200])
    rf_max_depth: List[int] = field(default_factory=lambda: [5, 10, 15, None])
    gb_learning_rate: List[float] = field(default_factory=lambda: [0.05, 0.1, 0.2])
    gb_n_estimators: List[int] = field(default_factory=lambda: [50, 100, 150])
    
    # 交易阈值
    ml_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.55, 0.6, 0.65])


class TimeSeriesCVOptimizer:
    """
    时间序列交叉验证优化器
    
    使用TimeSeriesSplit确保不发生数据泄露，
    保持时间序列的顺序性
    """
    
    def __init__(self, n_splits: int = 5, test_size: int = 20):
        """
        初始化
        
        Args:
            n_splits: 交叉验证折数
            test_size: 每折测试集大小
        """
        self.n_splits = n_splits
        self.test_size = test_size
        self.best_params = None
        self.best_score = float('-inf')
        self.cv_results = []
        
    def optimize_momentum(self, data: pd.DataFrame, param_space: HyperparameterSpace) -> Dict[str, Any]:
        """
        优化动量策略参数
        
        Returns:
            最优参数和交叉验证结果
        """
        best_params = {}
        best_score = float('-inf')
        results = []
        
        # 生成参数组合
        param_combinations = list(product(
            param_space.lookback_periods,
            param_space.momentum_thresholds
        ))
        
        for lookback, threshold in param_combinations:
            # 时间序列CV
            tscv = TimeSeriesSplit(n_splits=self.n_splits)
            scores = []
            
            for train_idx, val_idx in tscv.split(data):
                train_data = data.iloc[train_idx]
                val_data = data.iloc[val_idx]
                
                if len(train_data) < 60 or len(val_data) < 10:
                    continue
                
                # 计算动量
                momentum = train_data['close'].pct_change(lookback).iloc[-len(val_data):]
                val_momentum = val_data['close'].pct_change(lookback)
                
                # 计算收益
                strategy_returns = np.zeros(len(val_data) - 1)
                for i in range(1, len(val_data)):
                    if momentum.iloc[i-1] > threshold:
                        strategy_returns[i-1] = (val_data['close'].iloc[i] - val_data['close'].iloc[i-1]) / val_data['close'].iloc[i-1]
                    elif momentum.iloc[i-1] < -threshold:
                        strategy_returns[i-1] = -(val_data['close'].iloc[i] - val_data['close'].iloc[i-1]) / val_data['close'].iloc[i-1]
                
                # 使用夏普比率作为评分
                sharpe = RiskEvaluator.calculate_sharpe_ratio(strategy_returns)
                if np.isnan(sharpe) or np.isinf(sharpe):
                    sharpe = 0
                scores.append(sharpe)
            
            avg_score = np.mean(scores) if scores else 0
            
            results.append({
                'lookback': lookback,
                'threshold': threshold,
                'cv_score': avg_score
            })
            
            if avg_score > best_score:
                best_score = avg_score
                best_params = {'lookback': lookback, 'threshold': threshold}
        
        self.best_params = best_params
        self.best_score = best_score
        self.cv_results = results
        
        return {'best_params': best_params, 'best_score': best_score, 'all_results': results}
    
    def optimize_mean_reversion(self, data: pd.DataFrame, param_space: HyperparameterSpace) -> Dict[str, Any]:
        """
        优化均值回归策略参数
        """
        best_params = {}
        best_score = float('-inf')
        results = []
        
        param_combinations = list(product(
            param_space.lookback_periods,
            param_space.mean_reversion_thresholds
        ))
        
        for lookback, threshold in param_combinations:
            tscv = TimeSeriesSplit(n_splits=self.n_splits)
            scores = []
            
            for train_idx, val_idx in tscv.split(data):
                train_data = data.iloc[train_idx]
                val_data = data.iloc[val_idx]
                
                if len(train_data) < 60 or len(val_data) < 10:
                    continue
                
                # 计算Z分数
                rolling_mean = train_data['close'].rolling(lookback).mean()
                rolling_std = train_data['close'].rolling(lookback).std()
                
                val_mean = val_data['close'].rolling(lookback).mean()
                val_std = val_data['close'].rolling(lookback).std()
                z_score = (val_data['close'] - val_mean) / (val_std + 1e-10)
                
                strategy_returns = np.zeros(len(val_data) - 1)
                for i in range(1, len(val_data)):
                    if i < len(z_score):
                        if z_score.iloc[i] > threshold:
                            strategy_returns[i-1] = -(val_data['close'].iloc[i] - val_data['close'].iloc[i-1]) / val_data['close'].iloc[i-1]
                        elif z_score.iloc[i] < -threshold:
                            strategy_returns[i-1] = (val_data['close'].iloc[i] - val_data['close'].iloc[i-1]) / val_data['close'].iloc[i-1]
                
                sharpe = RiskEvaluator.calculate_sharpe_ratio(strategy_returns)
                if np.isnan(sharpe) or np.isinf(sharpe):
                    sharpe = 0
                scores.append(sharpe)
            
            avg_score = np.mean(scores) if scores else 0
            
            results.append({
                'lookback': lookback,
                'threshold': threshold,
                'cv_score': avg_score
            })
            
            if avg_score > best_score:
                best_score = avg_score
                best_params = {'lookback': lookback, 'threshold': threshold}
        
        self.best_params = best_params
        self.best_score = best_score
        self.cv_results = results
        
        return {'best_params': best_params, 'best_score': best_score, 'all_results': results}
    
    def optimize_rsi_params(self, data: pd.DataFrame, param_space: HyperparameterSpace) -> Dict[str, Any]:
        """
        优化RSI参数
        """
        best_params = {}
        best_score = float('-inf')
        results = []
        
        param_combinations = list(product(
            param_space.rsi_periods,
            param_space.rsi_oversold,
            param_space.rsi_overbought
        ))
        
        for period, oversold, overbought in param_combinations:
            tscv = TimeSeriesSplit(n_splits=self.n_splits)
            scores = []
            
            for train_idx, val_idx in tscv.split(data):
                train_data = data.iloc[train_idx]
                val_data = data.iloc[val_idx]
                
                if len(train_data) < period + 10 or len(val_data) < 10:
                    continue
                
                # 计算RSI
                close = train_data['close'].values
                rsi = TechnicalIndicator.calculate_rsi(close, period)
                
                val_close = val_data['close'].values
                val_rsi = TechnicalIndicator.calculate_rsi(val_close, period)
                
                strategy_returns = np.zeros(len(val_data) - 1)
                for i in range(1, len(val_data)):
                    if i < len(val_rsi):
                        if val_rsi[i] < oversold:
                            strategy_returns[i-1] = (val_close[i] - val_close[i-1]) / val_close[i-1]
                        elif val_rsi[i] > overbought:
                            strategy_returns[i-1] = -(val_close[i] - val_close[i-1]) / val_close[i-1]
                
                sharpe = RiskEvaluator.calculate_sharpe_ratio(strategy_returns)
                if np.isnan(sharpe) or np.isinf(sharpe):
                    sharpe = 0
                scores.append(sharpe)
            
            avg_score = np.mean(scores) if scores else 0
            
            results.append({
                'period': period,
                'oversold': oversold,
                'overbought': overbought,
                'cv_score': avg_score
            })
            
            if avg_score > best_score:
                best_score = avg_score
                best_params = {'period': period, 'oversold': oversold, 'overbought': overbought}
        
        return {'best_params': best_params, 'best_score': best_score, 'all_results': results}
    
    def optimize_macd_params(self, data: pd.DataFrame, param_space: HyperparameterSpace) -> Dict[str, Any]:
        """
        优化MACD参数
        """
        best_params = {}
        best_score = float('-inf')
        results = []
        
        param_combinations = list(product(
            param_space.macd_fast,
            param_space.macd_slow,
            param_space.macd_signal
        ))
        
        for fast, slow, signal in param_combinations:
            if fast >= slow:
                continue
                
            tscv = TimeSeriesSplit(n_splits=self.n_splits)
            scores = []
            
            for train_idx, val_idx in tscv.split(data):
                train_data = data.iloc[train_idx]
                val_data = data.iloc[val_idx]
                
                if len(train_data) < slow + 10 or len(val_data) < 10:
                    continue
                
                # 计算MACD
                close = train_data['close'].values
                macd, macd_signal, hist = TechnicalIndicator.calculate_macd(close, fast, slow, signal)
                
                val_close = val_data['close'].values
                val_macd, val_signal, _ = TechnicalIndicator.calculate_macd(val_close, fast, slow, signal)
                
                strategy_returns = np.zeros(len(val_data) - 1)
                prev_cross = 0
                for i in range(1, len(val_data)):
                    if i < len(val_macd) and i < len(val_signal):
                        cross = val_macd[i] - val_signal[i]
                        prev_val = val_macd[i-1] - val_signal[i-1] if i > 0 else 0
                        
                        if prev_val < 0 and cross > 0:
                            strategy_returns[i-1] = (val_close[i] - val_close[i-1]) / val_close[i-1]
                        elif prev_val > 0 and cross < 0:
                            strategy_returns[i-1] = -(val_close[i] - val_close[i-1]) / val_close[i-1]
                
                sharpe = RiskEvaluator.calculate_sharpe_ratio(strategy_returns)
                if np.isnan(sharpe) or np.isinf(sharpe):
                    sharpe = 0
                scores.append(sharpe)
            
            avg_score = np.mean(scores) if scores else 0
            
            results.append({
                'fast': fast,
                'slow': slow,
                'signal': signal,
                'cv_score': avg_score
            })
            
            if avg_score > best_score:
                best_score = avg_score
                best_params = {'fast': fast, 'slow': slow, 'signal': signal}
        
        return {'best_params': best_params, 'best_score': best_score, 'all_results': results}
    
    def optimize_ml_model(self, X: np.ndarray, y: np.ndarray, 
                         model_type: str = 'random_forest') -> Dict[str, Any]:
        """
        优化ML模型超参数
        """
        param_space = HyperparameterSpace()
        best_params = {}
        best_score = float('-inf')
        results = []
        
        if model_type == 'random_forest':
            param_combinations = list(product(
                param_space.rf_n_estimators,
                param_space.rf_max_depth
            ))
            
            for n_est, depth in param_combinations:
                tscv = TimeSeriesSplit(n_splits=self.n_splits)
                scores = []
                
                for train_idx, val_idx in tscv.split(X):
                    X_train, X_val = X[train_idx], X[val_idx]
                    y_train, y_val = y[train_idx], y[val_idx]
                    
                    if len(np.unique(y_train)) < 2:
                        continue
                    
                    model = RandomForestClassifier(n_estimators=n_est, max_depth=depth, random_state=42, n_jobs=-1)
                    model.fit(X_train, y_train)
                    
                    y_pred = model.predict(X_val)
                    y_proba = model.predict_proba(X_val)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                    
                    if len(np.unique(y_val)) > 1:
                        auc = roc_auc_score(y_val, y_proba)
                    else:
                        auc = accuracy_score(y_val, y_pred)
                    
                    scores.append(auc)
                
                avg_score = np.mean(scores) if scores else 0
                
                results.append({
                    'n_estimators': n_est,
                    'max_depth': depth,
                    'cv_score': avg_score
                })
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_params = {'n_estimators': n_est, 'max_depth': depth}
        
        elif model_type == 'gradient_boosting':
            param_combinations = list(product(
                param_space.gb_learning_rate,
                param_space.gb_n_estimators
            ))
            
            for lr, n_est in param_combinations:
                tscv = TimeSeriesSplit(n_splits=self.n_splits)
                scores = []
                
                for train_idx, val_idx in tscv.split(X):
                    X_train, X_val = X[train_idx], X[val_idx]
                    y_train, y_val = y[train_idx], y[val_idx]
                    
                    if len(np.unique(y_train)) < 2:
                        continue
                    
                    model = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, random_state=42)
                    model.fit(X_train, y_train)
                    
                    y_pred = model.predict(X_val)
                    y_proba = model.predict_proba(X_val)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                    
                    if len(np.unique(y_val)) > 1:
                        auc = roc_auc_score(y_val, y_proba)
                    else:
                        auc = accuracy_score(y_val, y_pred)
                    
                    scores.append(auc)
                
                avg_score = np.mean(scores) if scores else 0
                
                results.append({
                    'learning_rate': lr,
                    'n_estimators': n_est,
                    'cv_score': avg_score
                })
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_params = {'learning_rate': lr, 'n_estimators': n_est}
        
        return {'best_params': best_params, 'best_score': best_score, 'all_results': results}


class ComprehensiveOptimizer:
    """
    综合优化器 - 同时优化多个参数组合
    """
    
    def __init__(self, data_path: str = "/home/liujerry/金融数据/stocks/"):
        self.data_path = data_path
        self.param_space = HyperparameterSpace()
        self.analyzer = AcademicStockAnalyzer(data_path)
        self.recommendations = {}
        
    def full_optimization(self, stock_codes: List[str] = None, 
                          sample_size: int = 10) -> Dict[str, Any]:
        """
        执行完整优化流程
        
        Args:
            stock_codes: 股票列表，如果为None则自动选择
            sample_size: 采样股票数量
            
        Returns:
            优化后的参数推荐
        """
        if stock_codes is None:
            stock_codes = self._select_sample_stocks(sample_size)
        
        # 加载第一只股票进行参数优化
        if not stock_codes:
            return {'error': '无可用股票数据'}
        
        df = self.analyzer.load_stock_data(stock_codes[0])
        if df.empty or len(df) < 200:
            return {'error': '数据不足'}
        
        optimizer = TimeSeriesCVOptimizer(n_splits=5, test_size=20)
        
        print("=" * 60)
        print("开始超参数优化...")
        print("=" * 60)
        
        # 优化各参数
        momentum_result = optimizer.optimize_momentum(df, self.param_space)
        print(f"\n动量策略最优参数: {momentum_result['best_params']}")
        print(f"交叉验证分数: {momentum_result['best_score']:.4f}")
        
        mean_reversion_result = optimizer.optimize_mean_reversion(df, self.param_space)
        print(f"\n均值回归策略最优参数: {mean_reversion_result['best_params']}")
        print(f"交叉验证分数: {mean_reversion_result['best_score']:.4f}")
        
        rsi_result = optimizer.optimize_rsi_params(df, self.param_space)
        print(f"\nRSI最优参数: {rsi_result['best_params']}")
        print(f"交叉验证分数: {rsi_result['best_score']:.4f}")
        
        macd_result = optimizer.optimize_macd_params(df, self.param_space)
        print(f"\nMACD最优参数: {macd_result['best_params']}")
        print(f"交叉验证分数: {macd_result['best_score']:.4f}")
        
        # 生成综合推荐
        self.recommendations = {
            'momentum': {
                'lookback': momentum_result['best_params']['lookback'],
                'threshold': momentum_result['best_params']['threshold'],
                'cv_score': momentum_result['best_score']
            },
            'mean_reversion': {
                'lookback': mean_reversion_result['best_params']['lookback'],
                'threshold': mean_reversion_result['best_params']['threshold'],
                'cv_score': mean_reversion_result['best_score']
            },
            'rsi': {
                'period': rsi_result['best_params']['period'],
                'oversold': rsi_result['best_params']['oversold'],
                'overbought': rsi_result['best_params']['overbought'],
                'cv_score': rsi_result['best_score']
            },
            'macd': {
                'fast': macd_result['best_params']['fast'],
                'slow': macd_result['best_params']['slow'],
                'signal': macd_result['best_params']['signal'],
                'cv_score': macd_result['best_score']
            },
            'stocks_analyzed': stock_codes[:sample_size]
        }
        
        return self.recommendations
    
    def _select_sample_stocks(self, n: int) -> List[str]:
        """选择样本股票"""
        import os
        files = [f.replace('.csv', '') for f in os.listdir(self.data_path) if f.endswith('.csv')]
        return files[:n]
    
    def get_recommended_params(self) -> Dict[str, Any]:
        """获取推荐参数"""
        if not self.recommendations:
            return self.default_params()
        return self.recommendations
    
    def default_params(self) -> Dict[str, Any]:
        """默认参数"""
        return {
            'momentum': {'lookback': 20, 'threshold': 0.05},
            'mean_reversion': {'lookback': 20, 'threshold': 2.0},
            'rsi': {'period': 14, 'oversold': 30, 'overbought': 70},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'ml': {'n_estimators': 100, 'max_depth': 10, 'threshold': 0.6}
        }


def run_optimization():
    """运行优化示例"""
    print("=" * 60)
    print("学术级A股量化分析 - 超参数优化")
    print("=" * 60)
    
    optimizer = ComprehensiveOptimizer()
    results = optimizer.full_optimization(sample_size=5)
    
    if 'error' not in results:
        print("\n" + "=" * 60)
        print("优化完成！推荐参数:")
        print("=" * 60)
        for strategy, params in results.items():
            print(f"\n{strategy}:")
            for k, v in params.items():
                print(f"  {k}: {v}")
    else:
        print(f"优化失败: {results['error']}")
    
    return results


if __name__ == "__main__":
    run_optimization()
