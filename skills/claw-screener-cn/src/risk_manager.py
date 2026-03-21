"""
GARCH波动率预测 + VaR风险价值风控模块

功能:
1. GARCH模型预测未来波动率
2. VaR计算最大可能损失
3. 风险过滤 - 剔除高风险股票

参考: NotebookLM建议 - 结合GARCH与VaR的风控过滤模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import baostock as bs
from scipy import stats


class RiskManager:
    """
    风险管理器
    
    功能:
    1. GARCH(1,1)波动率预测
    2. VaR风险价值计算
    3. 风险评级
    """
    
    def __init__(self):
        self.params = {
            # GARCH参数
            'garch_warmup': 30,   # GARCH预热期
            'garch_forecast': 1,   # 预测天数
            
            # VaR参数
            'var_confidence': 0.95,  # 置信水平
            'var_horizon': 1,       # 持有期(天)
            
            # 风控阈值
            'max_volatility': 0.50,   # 最大波动率 (50%)
            'max_var': 0.15,        # 最大VaR (15%)
            'max_loss': 0.20,       # 最大可能损失 (20%)
        }
        
        # 波动率缓存
        self.volatility_cache = {}
        self.var_cache = {}
    
    def analyze_stock(self, stock_code: str, prices: List[float]) -> Dict:
        """
        风险分析
        
        Args:
            stock_code: 股票代码
            prices: 价格序列
            
        Returns:
            风险分析结果
        """
        result = {
            'code': stock_code,
            'current_volatility': 0,    # 当前波动率
            'predicted_volatility': 0,  # 预测波动率
            'var_95': 0,             # 95% VaR
            'var_99': 0,             # 99% VaR
            'max_loss': 0,            # 最大可能损失
            'risk_rating': 'N/A',     # 风险评级
            'pass': False,            # 是否通过风控
        }
        
        try:
            if len(prices) < 30:
                print(f"数据不足: {len(prices)} < 30")
                return result
            
            # 1. 计算收益率
            returns = self._calculate_returns(prices)
            
            # 2. GARCH波动率预测
            result['current_volatility'] = self._calculate_volatility(returns)
            result['predicted_volatility'] = self._garch_forecast(returns)
            
            # 3. VaR计算
            result['var_95'], result['var_99'] = self._calculate_var(returns)
            
            # 4. 最大可能损失
            result['max_loss'] = result['predicted_volatility'] * 1.65  # 近似
            
            # 5. 风险评级
            result['risk_rating'] = self._get_risk_rating(result)
            
            # 6. 判断通过
            result['pass'] = self._check_pass(result)
            
        except Exception as e:
            print(f"风险分析失败 {stock_code}: {e}")
        
        return result
    
    def _calculate_returns(self, prices: List[float]) -> pd.Series:
        """计算收益率"""
        prices = np.array(prices)
        returns = np.diff(prices) / prices[:-1]
        return pd.Series(returns)
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """计算历史波动率 (年化)"""
        if len(returns) < 2:
            return 0
        
        # 日波动率
        daily_vol = returns.std()
        
        # 年化波动率 (假设252交易日)
        annual_vol = daily_vol * np.sqrt(252)
        
        return annual_vol
    
    def _garch_forecast(self, returns: pd.Series, horizon: int = 1) -> float:
        """
        GARCH(1,1)波动率预测
        
        简化实现: 使用EWMA
        r_t = sqrt(lambda * r_{t-1}^2 + (1-lambda) * sigma^2)
        """
        if len(returns) < 10:
            return self._calculate_volatility(returns)
        
        # 简化GARCH: 使用指数加权移动平均 (EWMA)
        # lambda = 0.94 (RiskMetrics标准)
        lam = 0.94
        
        # 从最近30天开始计算
        recent_returns = returns.tail(30)
        
        # 计算方差序列
        variance = recent_returns.var()
        
        for i in range(len(recent_returns) - 1, 0, -1):
            r2 = recent_returns.iloc[i] ** 2
            variance = lam * variance + (1 - lam) * r2
        
        # 预测未来波动率
        forecast_vol = np.sqrt(variance) * np.sqrt(252)  # 年化
        
        return forecast_vol
    
    def _calculate_var(self, returns: pd.Series) -> Tuple[float, float]:
        """
        计算VaR (风险价值)
        
        VaR = mean - z * std
        """
        if len(returns) < 10:
            return 0, 0
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        # 95% VaR
        z_95 = stats.norm.ppf(1 - 0.95)
        var_95 = -(mean_return + z_95 * std_return)
        
        # 99% VaR
        z_99 = stats.norm.ppf(1 - 0.99)
        var_99 = -(mean_return + z_99 * std_return)
        
        return var_95, var_99
    
    def _get_risk_rating(self, result: Dict) -> str:
        """风险评级"""
        vol = result['predicted_volatility']
        var_95 = result['var_95']
        
        # 综合评分
        risk_score = 0
        
        if vol < 0.15:
            risk_score += 3
        elif vol < 0.25:
            risk_score += 2
        elif vol < 0.35:
            risk_score += 1
        else:
            risk_score += 0
        
        if var_95 < 0.03:
            risk_score += 3
        elif var_95 < 0.05:
            risk_score += 2
        elif var_95 < 0.08:
            risk_score += 1
        
        # 评级
        if risk_score >= 5:
            return "🟢 低风险"
        elif risk_score >= 3:
            return "🟡 中等"
        elif risk_score >= 1:
            return "🟠 较高"
        else:
            return "🔴 高风险"
    
    def _check_pass(self, result: Dict) -> bool:
        """判断是否通过风控"""
        if result['predicted_volatility'] > self.params['max_volatility']:
            return False
        
        if result['var_95'] > self.params['max_var']:
            return False
        
        if result['max_loss'] > self.params['max_loss']:
            return False
        
        return True
    
    def filter_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        过滤高风险股票
        
        Args:
            stocks: 股票列表 (需包含price_history字段)
            
        Returns:
            通过风控的股票
        """
        passed = []
        
        for stock in stocks:
            code = stock.get('code', '')
            prices = stock.get('price_history', [])
            
            if not prices:
                # 无价格数据，跳过风控
                passed.append(stock)
                continue
            
            risk = self.analyze_stock(code, prices)
            
            if risk['pass']:
                stock['risk'] = risk
                passed.append(stock)
            else:
                print(f"风控过滤: {code} - {risk['risk_rating']}")
        
        return passed


def get_price_history(stock_code: str, days: int = 250) -> List[float]:
    """获取价格历史"""
    try:
        # 转换代码
        if stock_code.startswith('6'):
            bs_code = f'sh.{stock_code}'
        else:
            bs_code = f'sz.{stock_code}'
        
        lg = bs.login()
        
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,close",
            start_date="2024-01-01",
            frequency="d"
        )
        
        prices = []
        while rs.next():
            row = rs.get_row_data()
            try:
                prices.append(float(row[1]))
            except:
                pass
        
        bs.logout()
        
        return prices[-days:] if len(prices) > days else prices
        
    except Exception as e:
        print(f"获取价格失败 {stock_code}: {e}")
        return []


def risk_filter(stocks: List[str]) -> List[Dict]:
    """
    风险过滤主函数
    
    Args:
        stocks: 股票代码列表
        
    Returns:
        带风险数据的股票列表
    """
    manager = RiskManager()
    results = []
    
    print(f"开始风险分析 ({len(stocks)} 只股票)...")
    
    for code in stocks:
        prices = get_price_history(code)
        
        if not prices:
            continue
        
        risk = manager.analyze_stock(code, prices)
        
        results.append({
            'code': code,
            'prices': prices,
            'risk': risk,
        })
    
    # 过滤
    passed = [r for r in results if r['risk']['pass']]
    
    print(f"风控完成: {len(passed)}/{len(results)} 只通过")
    
    return passed


def generate_risk_report(results: List[Dict]) -> str:
    """生成风险报告"""
    lines = []
    lines.append("=" * 80)
    lines.append("📊 风险分析报告 (GARCH + VaR)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'代码':<10} {'当前波动':<12} {'预测波动':<12} {'VaR(95%)':<12} {'风险评级':<10} {'通过'}")
    lines.append("-" * 80)
    
    for r in results:
        risk = r['risk']
        lines.append(
            f"{r['code']:<10} "
            f"{risk['current_volatility']*100:<11.1f}% "
            f"{risk['predicted_volatility']*100:<11.1f}% "
            f"{risk['var_95']*100:<11.1f}% "
            f"{risk['risk_rating']:<10} "
            f"{'✅' if risk['pass'] else '❌'}"
        )
    
    lines.append("")
    lines.append("说明:")
    lines.append("- 波动率: 年化波动率 (GARCH预测)")
    lines.append("- VaR(95%): 95%置信度下单日最大可能损失")
    lines.append("- 通过条件: 波动率<50%, VaR<15%, 最大损失<20%")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    stocks = ['300502', '300926', '300308', '300628']
    results = risk_filter(stocks)
    print(generate_risk_report(results))
