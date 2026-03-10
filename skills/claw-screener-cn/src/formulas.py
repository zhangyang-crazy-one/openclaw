"""
巴菲特10大公式选股系统
完全对照原版 TypeScript 实现

参考: https://github.com/rsoutar/claw-screener/blob/main/src/formulas.ts
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math


class FormulaStatus(Enum):
    """公式评估状态"""
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "N/A"


@dataclass
class FormulaResult:
    """单条公式评估结果"""
    name: str
    status: FormulaStatus
    value: float
    target: str
    message: str


class FinancialData:
    """
    财务数据结构 - 对应 TypeScript 的 Financials 接口
    
    字段说明:
    - 所有数值单位应为"元" (原版使用美元，这里使用人民币)
    - 日期格式: YYYY-MM-DD
    - 表单类型: 10-K, 10-Q 等
    """
    
    def __init__(self, data: Dict[str, Dict[str, Any]]):
        """
        Args:
            data: 财务数据字典，格式如:
            {
                "CashAndCashEquivalentsAtCarryingValue": {"value": 50000000000, "end_date": "2024-09-28", "form": "10-K"},
                "ShortTermDebt": {"value": 15000000000, "end_date": "2024-09-28", "form": "10-K"},
                ...
            }
        """
        self.data = data
    
    def get_value(self, key: str, default_value: float = 0) -> float:
        """
        获取财务指标值 - 对应 TypeScript: getValue()
        
        Args:
            key: 财务指标名称
            default_value: 默认值
        
        Returns:
            指标数值
        """
        if key in self.data:
            return float(self.data[key].get('value', default_value))
        return default_value
    
    def get_date(self, key: str) -> Optional[str]:
        """获取财务指标日期"""
        if key in self.data:
            return self.data[key].get('end_date')
        return None
    
    def get_form(self, key: str) -> Optional[str]:
        """获取财务指标表单类型"""
        if key in self.data:
            return self.data[key].get('form')
        return None


class FormulaEngine:
    """
    巴菲特10大公式引擎 - 对应 TypeScript 的 FormulaEngine 类
    
    评估维度:
    1. 现金测试 (Cash Test)
    2. 负债权益比 (Debt-to-Equity)
    3. 净资产收益率 (ROE)
    4. 流动比率 (Current Ratio)
    5. 营业利润率 (Operating Margin)
    6. 资产周转率 (Asset Turnover)
    7. 利息保障倍数 (Interest Coverage)
    8. 盈利稳定性 (Earnings Stability)
    9. 自由现金流 (Free Cash Flow)
    10. 资本配置 (Capital Allocation) - 同ROE
    """
    
    def __init__(self, financials: FinancialData):
        """
        初始化公式引擎
        
        Args:
            financials: 财务数据对象
        """
        self.financials = financials
    
    def cash_test(self) -> FormulaResult:
        """
        现金测试 - 对应 TypeScript: cashTest()
        
        公式: 现金及现金等价物 > 总负债
        目标: 现金能够覆盖所有负债
        
        Returns:
            现金测试结果
        """
        # 获取现金及现金等价物
        cash = self.financials.get_value("CashAndCashEquivalentsAtCarryingValue")
        
        # 获取短期负债
        short_term_debt = self.financials.get_value("ShortTermDebt")
        
        # 获取长期负债
        long_term_debt = self.financials.get_value("LongTermDebt")
        
        # 计算总负债
        total_debt = short_term_debt + long_term_debt
        
        # 如果没有负债，则通过
        if total_debt == 0:
            return FormulaResult(
                name="现金测试 (Cash Test)",
                status=FormulaStatus.PASS,
                value=cash,
                target="> 总负债",
                message="无负债 (通过)"
            )
        
        # 计算现金覆盖率
        ratio = cash / total_debt
        
        # 判断是否通过
        status = FormulaStatus.PASS if ratio > 1.0 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="现金测试 (Cash Test)",
            status=status,
            value=ratio,
            target="> 1.0x",
            message=f"现金/负债: {ratio:.2f}x"
        )
    
    def debt_to_equity(self) -> FormulaResult:
        """
        负债权益比 - 对应 TypeScript: debtToEquity()
        
        公式: 总负债 / 所有者权益 < 0.5
        目标: 负债不应超过所有者权益的一半
        
        Returns:
            负债权益比结果
        """
        # 获取总负债 (Liabilities)
        liabilities = self.financials.get_value("Liabilities")
        
        # 获取所有者权益 (StockholdersEquity)
        equity = self.financials.get_value("StockholdersEquity")
        
        # 如果没有权益数据，则失败
        if equity == 0:
            return FormulaResult(
                name="负债权益比 (Debt-to-Equity)",
                status=FormulaStatus.FAIL,
                value=999,
                target="< 0.5",
                message="无所有者权益数据"
            )
        
        # 计算负债权益比
        ratio = liabilities / equity
        
        # 判断是否通过 (小于0.5通过)
        status = FormulaStatus.PASS if ratio < 0.5 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="负债权益比 (Debt-to-Equity)",
            status=status,
            value=ratio,
            target="< 0.5",
            message=f"负债/权益: {ratio:.2f}"
        )
    
    def return_on_equity(self) -> FormulaResult:
        """
        净资产收益率 (ROE) - 对应 TypeScript: returnOnEquity()
        
        公式: 净利润 / 所有者权益 * 100%
        目标: ROE > 15%
        
        Returns:
            ROE结果
        """
        # 获取净利润
        net_income = self.financials.get_value("NetIncomeLoss")
        
        # 获取所有者权益
        equity = self.financials.get_value("StockholdersEquity")
        
        # 数据不足则失败
        if equity == 0 or net_income == 0:
            return FormulaResult(
                name="净资产收益率 (ROE)",
                status=FormulaStatus.FAIL,
                value=0,
                target="> 15%",
                message="数据不足"
            )
        
        # 计算ROE
        roe = (net_income / equity) * 100
        
        # 判断是否通过 (大于15%通过)
        status = FormulaStatus.PASS if roe > 15 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="净资产收益率 (ROE)",
            status=status,
            value=roe,
            target="> 15%",
            message=f"ROE: {roe:.1f}%"
        )
    
    def current_ratio(self) -> FormulaResult:
        """
        流动比率 - 对应 TypeScript: currentRatio()
        
        公式: 流动资产 / 流动负债
        目标: > 1.5
        
        Returns:
            流动比率结果
        """
        # 获取流动资产
        current_assets = self.financials.get_value("CurrentAssets")
        
        # 获取流动负债
        current_liabilities = self.financials.get_value("CurrentLiabilities")
        
        # 如果没有流动负债，则通过
        if current_liabilities == 0:
            return FormulaResult(
                name="流动比率 (Current Ratio)",
                status=FormulaStatus.PASS,
                value=999,
                target="> 1.5",
                message="无流动负债 (通过)"
            )
        
        # 计算流动比率
        ratio = current_assets / current_liabilities
        
        # 判断是否通过
        status = FormulaStatus.PASS if ratio > 1.5 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="流动比率 (Current Ratio)",
            status=status,
            value=ratio,
            target="> 1.5",
            message=f"流动比率: {ratio:.2f}"
        )
    
    def operating_margin(self) -> FormulaResult:
        """
        营业利润率 - 对应 TypeScript: operatingMargin()
        
        公式: 营业利润 / 营业收入 * 100%
        目标: > 12%
        
        Returns:
            营业利润率结果
        """
        # 获取营业利润
        operating_income = self.financials.get_value("OperatingIncomeLoss")
        
        # 获取营业收入
        revenue = self.financials.get_value("Revenues")
        
        # 如果没有营收数据，则失败
        if revenue == 0:
            return FormulaResult(
                name="营业利润率 (Operating Margin)",
                status=FormulaStatus.FAIL,
                value=0,
                target="> 12%",
                message="无营业收入数据"
            )
        
        # 计算营业利润率
        margin = (operating_income / revenue) * 100
        
        # 判断是否通过
        status = FormulaStatus.PASS if margin > 12 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="营业利润率 (Operating Margin)",
            status=status,
            value=margin,
            target="> 12%",
            message=f"营业利润率: {margin:.1f}%"
        )
    
    def asset_turnover(self) -> FormulaResult:
        """
        资产周转率 - 对应 TypeScript: assetTurnover()
        
        公式: 营业收入 / 总资产
        目标: > 0.5
        
        Returns:
            资产周转率结果
        """
        # 获取营业收入
        revenue = self.financials.get_value("Revenues")
        
        # 获取总资产
        assets = self.financials.get_value("Assets")
        
        # 如果没有资产数据，则失败
        if assets == 0:
            return FormulaResult(
                name="资产周转率 (Asset Turnover)",
                status=FormulaStatus.FAIL,
                value=0,
                target="> 0.5",
                message="无资产数据"
            )
        
        # 计算资产周转率
        turnover = revenue / assets
        
        # 判断是否通过
        status = FormulaStatus.PASS if turnover > 0.5 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="资产周转率 (Asset Turnover)",
            status=status,
            value=turnover,
            target="> 0.5",
            message=f"周转率: {turnover:.2f}"
        )
    
    def interest_coverage(self) -> FormulaResult:
        """
        利息保障倍数 - 对应 TypeScript: interestCoverage()
        
        公式: 营业利润 / 利息费用
        目标: > 3x
        
        Returns:
            利息保障倍数结果
        """
        # 获取营业利润
        operating_income = self.financials.get_value("OperatingIncomeLoss")
        
        # 获取利息费用 (通常为负数)
        interest_expense = self.financials.get_value("InterestExpense")
        
        # 如果没有利息支出，则通过
        if interest_expense == 0:
            return FormulaResult(
                name="利息保障倍数 (Interest Coverage)",
                status=FormulaStatus.PASS,
                value=999,
                target="> 3x",
                message="无利息支出 (通过)"
            )
        
        # 计算利息保障倍数 (注意利息费用可能为负)
        coverage = operating_income / abs(interest_expense)
        
        # 判断是否通过
        status = FormulaStatus.PASS if coverage > 3 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="利息保障倍数 (Interest Coverage)",
            status=status,
            value=coverage,
            target="> 3x",
            message=f"利息保障倍数: {coverage:.1f}x"
        )
    
    def earnings_stability(self) -> FormulaResult:
        """
        盈利稳定性 - 对应 TypeScript: earningsStability()
        
        公式: 净利润 > 0
        目标: 最近N年盈利
        
        Note: 原版使用最新一年数据作为代理
        
        Returns:
            盈利稳定性结果
        """
        # 获取净利润
        net_income = self.financials.get_value("NetIncomeLoss")
        
        # 判断是否盈利
        status = FormulaStatus.PASS if net_income > 0 else FormulaStatus.FAIL
        
        return FormulaResult(
            name="盈利稳定性 (Earnings Stability)",
            status=status,
            value=1 if net_income > 0 else 0,
            target="8+/10年盈利",
            message="基于最新一年数据 (完整历史需要更多数据)"
        )
    
    def free_cash_flow(self) -> FormulaResult:
        """
        自由现金流 - 对应 TypeScript: freeCashFlow()
        
        公式: 自由现金流 > 0
        目标: 经营现金流为正
        
        Note: 原版优先使用 FreeCashFlow，若为0则使用 OperatingCashFlow
        
        Returns:
            自由现金流结果
        """
        # 优先获取自由现金流
        fcf = self.financials.get_value("FreeCashFlow")
        
        # 如果为0，尝试使用经营现金流
        if fcf == 0:
            fcf = self.financials.get_value("CashFlowFromContinuingOperatingActivities")
        
        # 判断是否为正
        status = FormulaStatus.PASS if fcf > 0 else FormulaStatus.FAIL
        
        # 格式化金额显示
        if abs(fcf) >= 1_000_000_000:
            message = f"¥{fcf / 1_000_000_000:.2f}十亿"
        elif abs(fcf) >= 1_000_000:
            message = f"¥{fcf / 1_000_000:.0f}百万"
        else:
            message = f"¥{fcf:,.0f}"
        
        return FormulaResult(
            name="自由现金流 (Free Cash Flow)",
            status=status,
            value=fcf,
            target="> 0",
            message=message
        )
    
    def capital_allocation(self) -> FormulaResult:
        """
        资本配置 - 对应 TypeScript: capitalAllocation()
        
        公式: ROE > 15% (同ROE公式)
        目标: 管理层能有效配置资本创造回报
        
        Note: 实际上就是ROE的复现
        
        Returns:
            资本配置结果
        """
        # 复用ROE计算结果
        roe_result = self.return_on_equity()
        
        return FormulaResult(
            name="资本配置 (Capital Allocation)",
            status=roe_result.status,
            value=roe_result.value,
            target="> 15%",
            message=f"ROE: {roe_result.message}"
        )
    
    def evaluate_all(self) -> List[FormulaResult]:
        """
        评估所有10大公式 - 对应 TypeScript: evaluateAll()
        
        Returns:
            所有公式评估结果列表
        """
        return [
            self.cash_test(),
            self.debt_to_equity(),
            self.return_on_equity(),
            self.current_ratio(),
            self.operating_margin(),
            self.asset_turnover(),
            self.interest_coverage(),
            self.earnings_stability(),
            self.free_cash_flow(),
            self.capital_allocation(),
        ]
    
    def get_score(self) -> int:
        """
        获取通过数量 - 对应 TypeScript: getScore()
        
        Returns:
            通过的公式数量 (0-10)
        """
        results = self.evaluate_all()
        return sum(1 for r in results if r.status == FormulaStatus.PASS)


def format_financial_data(raw_data: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """
    将简单财务数据格式转换为 FormulaEngine 需要的格式
    
    Args:
        raw_data: 简单格式，如 {"CashAndCashEquivalentsAtCarryingValue": 50000000000, ...}
    
    Returns:
        转换后的格式
    """
    result = {}
    for key, value in raw_data.items():
        result[key] = {
            "value": value,
            "end_date": "2024-12-31",
            "form": "10-K"
        }
    return result


# 测试代码 - 对应 TypeScript 的 import.meta.main
if __name__ == "__main__":
    # 创建测试数据 - 与原版 TypeScript 完全相同
    dummy_financials_data = {
        "CashAndCashEquivalentsAtCarryingValue": {"value": 50000000000, "end_date": "2024-09-28", "form": "10-K"},
        "ShortTermDebt": {"value": 15000000000, "end_date": "2024-09-28", "form": "10-K"},
        "LongTermDebt": {"value": 100000000000, "end_date": "2024-09-28", "form": "10-K"},
        "Liabilities": {"value": 290000000000, "end_date": "2024-09-28", "form": "10-K"},
        "StockholdersEquity": {"value": 62000000000, "end_date": "2024-09-28", "form": "10-K"},
        "NetIncomeLoss": {"value": 97000000000, "end_date": "2024-09-28", "form": "10-K"},
        "Revenues": {"value": 383000000000, "end_date": "2024-09-28", "form": "10-K"},
        "OperatingIncomeLoss": {"value": 114000000000, "end_date": "2024-09-28", "form": "10-K"},
        "Assets": {"value": 400000000000, "end_date": "2024-09-28", "form": "10-K"},
        "CurrentAssets": {"value": 135000000000, "end_date": "2024-09-28", "form": "10-K"},
        "CurrentLiabilities": {"value": 153000000000, "end_date": "2024-09-28", "form": "10-K"},
        "InterestExpense": {"value": -2900000000, "end_date": "2024-09-28", "form": "10-K"},
        "CashFlowFromContinuingOperatingActivities": {"value": 110000000000, "end_date": "2024-09-28", "form": "10-K"},
    }
    
    # 创建公式引擎
    financials = FinancialData(dummy_financials_data)
    engine = FormulaEngine(financials)
    
    # 评估所有公式
    results = engine.evaluate_all()
    
    # 输出结果
    print("=" * 60)
    print("巴菲特10大公式评估结果 (Buffett Formula Results)")
    print("=" * 60)
    print(f"\n总分 (Score): {engine.get_score()}/10\n")
    
    for result in results:
        symbol = "✅" if result.status == FormulaStatus.PASS else "❌"
        print(f"{symbol} {result.name}")
        print(f"   结果: {result.message} (目标: {result.target})")
        print()
