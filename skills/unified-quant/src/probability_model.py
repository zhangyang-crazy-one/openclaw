"""
短线获胜概率模型
功能: 基于历史数据计算买入/卖出时机获胜概率
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class WinProbabilityModel:
    """短线获胜概率模型"""
    
    def __init__(self):
        self.historical_data = {}
        self.strategies = {}
        
    def load_historical_data(self, stock_code: str, df: pd.DataFrame):
        """加载历史数据"""
        self.historical_data[stock_code] = df
        
    def calculate_entry_probability(self, stock_code: str, 
                                   signal_type: str = "breakout") -> Dict:
        """
        计算买入时机获胜概率
        
        Args:
            stock_code: 股票代码
            signal_type: 信号类型 (breakout/momentum/reversal)
        
        Returns:
            概率结果字典
        """
        if stock_code not in self.historical_data:
            return {"error": "No data available"}
        
        df = self.historical_data[stock_code]
        
        # 根据信号类型计算概率
        if signal_type == "breakout":
            # 突破策略: 收盘价突破20日高点
            df['high_20'] = df['close'].rolling(20).max()
            df['breakout_signal'] = df['close'] > df['high_20'].shift(1)
            
            # 计算突破后N天收益
            N = 5  # 5天后收益
            df['future_return'] = df['close'].shift(-N) / df['close'] - 1
            
            # 筛选突破信号
            signals = df[df['breakout_signal']].dropna()
            
        elif signal_type == "momentum":
            # 动量策略: 5日均线>20日均线
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            df['momentum_signal'] = df['ma5'] > df['ma20']
            
            signals = df[df['momentum_signal']].dropna()
            
        elif signal_type == "reversal":
            # 反转策略: 超卖后反弹
            df['low_20'] = df['close'].rolling(20).min()
            df['reversal_signal'] = df['close'] < df['low_20'] * 1.05
            
            signals = df[df['reversal_signal']].dropna()
        
        # 计算获胜概率
        if len(signals) == 0:
            return {"error": "No signals found"}
        
        future_returns = signals['future_return'].dropna()
        
        # 统计
        total = len(future_returns)
        wins = (future_returns > 0).sum()
        losses = (future_returns < 0).sum()
        breaks = total - wins - losses
        
        win_rate = wins / total * 100 if total > 0 else 0
        avg_return = future_returns.mean() * 100 if len(future_returns) > 0 else 0
        median_return = future_returns.median() * 100 if len(future_returns) > 0 else 0
        
        # 置信区间 (95%)
        std = future_returns.std() * 100 if len(future_returns) > 1 else 0
        ci_lower = win_rate - 1.96 * np.sqrt(win_rate * (100 - win_rate) / total) if total > 0 else 0
        ci_upper = win_rate + 1.96 * np.sqrt(win_rate * (100 - win_rate) / total) if total > 0 else 100
        
        return {
            "strategy": signal_type,
            "stock_code": stock_code,
            "sample_size": total,
            "win_rate": round(win_rate, 2),
            "loss_rate": round(losses / total * 100, 2) if total > 0 else 0,
            "avg_return_pct": round(avg_return, 2),
            "median_return_pct": round(median_return, 2),
            "confidence_interval_95": [round(ci_lower, 2), round(ci_upper, 2)],
            "best_case_pct": round(future_returns.max() * 100, 2) if len(future_returns) > 0 else 0,
            "worst_case_pct": round(future_returns.min() * 100, 2) if len(future_returns) > 0 else 0,
        }
    
    def calculate_exit_probability(self, stock_code: str,
                                   hold_days: int = 5) -> Dict:
        """计算卖出时机获胜概率"""
        if stock_code not in self.historical_data:
            return {"error": "No data available"}
        
        df = self.historical_data[stock_code]
        
        # 模拟不同持有期的收益分布
        if len(df) < hold_days + 10:
            return {"error": "Insufficient data"}
        
        returns = []
        for i in range(len(df) - hold_days):
            ret = (df['close'].iloc[i + hold_days] / df['close'].iloc[i] - 1) * 100
            returns.append(ret)
        
        returns = np.array(returns)
        
        return {
            "hold_days": hold_days,
            "sample_size": len(returns),
            "win_rate": round((returns > 0).sum() / len(returns) * 100, 2),
            "avg_return_pct": round(returns.mean(), 2),
            "median_return_pct": round(np.median(returns), 2),
            "std_pct": round(returns.std(), 2),
            "profit_factor": round(returns[returns > 0].sum() / abs(returns[returns < 0].sum()), 2) if (returns < 0).sum() > 0 else 0,
        }
    
    def get_optimal_strategy(self, stock_code: str) -> Dict:
        """获取最优策略推荐"""
        results = {}
        
        # 测试所有策略
        for strategy in ["breakout", "momentum", "reversal"]:
            try:
                result = self.calculate_entry_probability(stock_code, strategy)
                if "error" not in result:
                    results[strategy] = result
            except:
                continue
        
        if not results:
            return {"error": "No valid strategy found"}
        
        # 选择最佳策略 (基于获胜概率和平均收益)
        best = max(results.values(), 
                   key=lambda x: x['win_rate'] * 0.6 + min(x['avg_return_pct'] + 5, 10) * 0.4)
        
        return {
            "recommended": best,
            "all_strategies": results
        }
    
    def generate_signal(self, stock_code: str) -> Dict:
        """生成买入/卖出信号"""
        # 获取最优策略
        optimal = self.get_optimal_strategy(stock_code)
        
        if "error" in optimal:
            return optimal
        
        best = optimal["recommended"]
        
        # 根据获胜概率生成信号
        if best['win_rate'] >= 60:
            signal = "BUY"
            reason = f"策略{best['strategy']}获胜概率{best['win_rate']}%"
        elif best['win_rate'] <= 40:
            signal = "SELL"
            reason = f"策略{best['strategy']}获胜概率较低"
        else:
            signal = "HOLD"
            reason = f"策略{best['strategy']}获胜概率{best['win_rate']}%，建议观望"
        
        return {
            "signal": signal,
            "reason": reason,
            "probability": best['win_rate'],
            "strategy": best['strategy'],
            "expected_return": best['avg_return_pct'],
            "confidence_interval": best['confidence_interval_95'],
        }


if __name__ == "__main__":
    model = WinProbabilityModel()
    print("模型已创建，可用于计算获胜概率")
