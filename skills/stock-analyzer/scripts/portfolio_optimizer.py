#!/usr/bin/env python3
"""
投资组合优化脚本
黄金ETF + 创业板股票组合分析
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PortfolioOptimizer:
    def __init__(self):
        self.assets = {}
        self.returns = pd.DataFrame()
        
    def fetch_data(self, symbols, start_date="20250101"):
        """获取多只股票数据"""
        print("📥 获取数据...")
        
        for symbol in symbols:
            try:
                # 创业板股票
                if symbol.startswith("30"):
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                            start_date=start_date, adjust="qfq")
                else:
                    # ETF
                    df = ak.fund_etf_hist_em(symbol=symbol, period="daily",
                                             start_date=start_date)
                
                if df is not None and len(df) > 0:
                    df['日期'] = pd.to_datetime(df['日期'])
                    df = df.sort_values('日期')
                    df = df.set_index('日期')
                    
                    # 计算日收益率
                    close = df['收盘'].astype(float)
                    daily_return = close.pct_change().dropna()
                    
                    self.returns[symbol] = daily_return
                    self.assets[symbol] = len(df)
                    print(f"  ✅ {symbol}: {len(df)}条")
                else:
                    print(f"  ❌ {symbol}: 无数据")
            except Exception as e:
                print(f"  ❌ {symbol}: {str(e)[:30]}")
                
        return self
    
    def calculate_metrics(self):
        """计算组合指标"""
        # 年化收益率
        annual_return = self.returns.mean() * 252
        
        # 年化波动率 (标准差)
        annual_volatility = self.returns.std() * np.sqrt(252)
        
        # 夏普比率 (假设无风险利率 3%)
        risk_free_rate = 0.03
        sharpe = (annual_return - risk_free_rate) / annual_volatility
        
        # 相关性矩阵
        correlation = self.returns.corr()
        
        metrics = {
            'annual_return': annual_return,
            'volatility': annual_volatility,
            'sharpe': sharpe,
            'correlation': correlation
        }
        
        self.metrics = metrics
        return self
    
    def optimize_portfolio(self, target_volatility=None):
        """优化组合权重"""
        n = len(self.returns.columns)
        
        if n < 2:
            return None
            
        # 计算协方差矩阵
        cov_matrix = self.returns.cov() * 252
        
        # 平均分配权重
        weights = np.array([1/n] * n)
        
        # 计算组合收益和风险
        portfolio_return = np.dot(weights, self.metrics['annual_return'])
        portfolio_volatility = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        # 夏普比率
        risk_free = 0.03
        portfolio_sharpe = (portfolio_return - risk_free) / portfolio_volatility
        
        # 蒙特卡洛模拟优化
        best_sharpe = portfolio_sharpe
        best_weights = weights
        best_return = portfolio_return
        best_vol = portfolio_volatility
        
        print("\n🔄 蒙特卡洛模拟优化...")
        
        for _ in range(5000):
            # 随机权重
            weights = np.random.random(n)
            weights = weights / weights.sum()
            
            # 组合收益
            ret = np.dot(weights, self.metrics['annual_return'])
            
            # 组合风险
            vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            
            # 夏普比率
            sharpe = (ret - risk_free) / vol
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights
                best_return = ret
                best_vol = vol
        
        return {
            'weights': dict(zip(self.returns.columns, best_weights)),
            'return': best_return,
            'volatility': best_vol,
            'sharpe': best_sharpe
        }
    
    def generate_report(self):
        """生成报告"""
        print("\n" + "="*70)
        print("【投资组合优化报告】")
        print("="*70)
        
        # 单资产指标
        print("\n📊 【单资产指标】")
        print(f"{'代码':<12} {'年化收益':<12} {'年化波动':<12} {'夏普比率':<12}")
        print("-" * 50)
        
        for col in self.returns.columns:
            ret = self.metrics['annual_return'][col] * 100
            vol = self.metrics['volatility'][col] * 100
            sharpe = self.metrics['sharpe'][col]
            print(f"{col:<12} {ret:>+8.2f}%   {vol:>8.2f}%   {sharpe:>8.2f}")
        
        # 优化组合
        result = self.optimize_portfolio()
        
        if result:
            print("\n" + "="*70)
            print("【最优组合】")
            print("="*70)
            
            print("\n权重分配:")
            for code, weight in sorted(result['weights'].items(), key=lambda x: -x[1]):
                if weight > 0.01:
                    print(f"  {code}: {weight*100:.1f}%")
            
            print(f"\n预期收益: {result['return']*100:+.2f}%")
            print(f"波动率(风险): {result['volatility']*100:.2f}%")
            print(f"夏普比率: {result['sharpe']:.2f}")
            
            # 风险分析
            print("\n⚠️ 风险提示:")
            if result['volatility'] > 0.3:
                print("  - 组合波动率较高，风险较大")
            if result['return'] < 0:
                print("  - 预期收益为负，需谨慎")
                
            # 建议
            print("\n💡 建议:")
            gold_weight = result['weights'].get('518880', 0)
            if gold_weight > 0.3:
                print(f"  - 黄金ETF占比{gold_weight*100:.0f}%，防御性强")
            elif gold_weight > 0.1:
                print(f"  - 黄金ETF占比{gold_weight*100:.0f}%，平衡配置")
            else:
                print("  - 黄金ETF占比低，进攻性较强")
        
        return result


def main():
    # 创业板低价股TOP5 + 黄金ETF
    stocks = [
        "518880",  # 黄金ETF
        "300251",  # 光线传媒
        "300967",  # 晓鸣股份
        "300749",  # 佳士科技
        "300017",  # 网宿科技
        "300191",  # 中国荣昌
    ]
    
    optimizer = PortfolioOptimizer()
    optimizer.fetch_data(stocks, start_date="20250101")
    
    if len(optimizer.returns.columns) < 2:
        print("❌ 数据不足，无法分析")
        return
    
    optimizer.calculate_metrics()
    optimizer.generate_report()


if __name__ == "__main__":
    main()
