#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统合量化投资分析系统
====================
整合行为金融学、货币金融学、量化金融学

作者: OpenClaw Quant Team
版本: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


@dataclass
class UnifiedScore:
    """统合评分"""
    code: str
    name: str
    
    # 行为因子
    sentiment_score: float = 50      # 投资者情绪
    money_flow_score: float = 50     # 资金流向
    analyst_sentiment: float = 50     # 分析师情绪
    
    # 宏观因子
    monetary_score: float = 50        # 货币环境
    cycle_score: float = 50           # 经济周期
    policy_score: float = 50          # 政策影响
    
    # 量化因子
    valuation_score: float = 50       # 估值
    growth_score: float = 50          # 成长
    quality_score: float = 50         # 质量
    momentum_score: float = 50        # 动量
    
    # 综合
    behavioral_score: float = 50
    macro_score: float = 50
    quant_score: float = 50
    total_score: float = 50
    recommendation: str = "HOLD"
    risk_level: str = "MEDIUM"


class UnifiedQuantAnalyzer:
    """统合量化分析器"""
    
    def __init__(self):
        self.stock_data = {}
        self.macro_data = {}
        
    def load_data(self, data_dir: Path):
        """加载数据"""
        print("📂 加载数据...")
        
        # 读取基本面数据
        try:
            # 蓝筹股财务数据
            dupont = pd.read_csv(data_dir / "baostock_dupont.csv")
            growth = pd.read_csv(data_dir / "baostock_growth.csv")
            profit = pd.read_csv(data_dir / "baostock_profit.csv")
            
            self.dupont = dupont
            self.growth = growth
            self.profit = profit
            print(f"   ✅ 基本面数据: {len(dupont)} 条")
        except Exception as e:
            print(f"   ⚠️ 基本面数据: {e}")
            self.dupont = pd.DataFrame()
            self.growth = pd.DataFrame()
            self.profit = pd.DataFrame()
        
        # 读取价格数据
        try:
            stock_dir = Path("/home/liujerry/金融数据/stocks")
            if stock_dir.exists():
                for f in stock_dir.glob("*.csv"):
                    code = f.stem
                    df = pd.read_csv(f)
                    df['date'] = pd.to_datetime(df['date'])
                    self.stock_data[code] = df
            print(f"   ✅ 价格数据: {len(self.stock_data)} 只")
        except Exception as e:
            print(f"   ⚠️ 价格数据: {e}")
    
    def calculate_behavioral_factors(self, code: str) -> Dict:
        """计算行为金融因子"""
        scores = {}
        
        # 模拟投资者情绪 (基于价格波动)
        if code in self.stock_data:
            df = self.stock_data[code].tail(20)
            if len(df) > 10:
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)
                
                # 高波动 = 高情绪 (过度自信)
                sentiment = 50 + volatility * 100
                scores['sentiment_score'] = min(100, max(0, sentiment))
                
                # 资金流向 (模拟: 放量上涨=流入)
                vol_ma5 = df['volume'].rolling(5).mean().iloc[-1]
                vol_ma20 = df['volume'].rolling(20).mean().iloc[-1]
                if vol_ma20 > 0:
                    vol_ratio = vol_ma5 / vol_ma20
                    if df['close'].iloc[-1] > df['close'].iloc[-5]:
                        scores['money_flow_score'] = min(100, 50 + (vol_ratio - 1) * 30)
                    else:
                        scores['money_flow_score'] = min(100, max(0, 50 - (vol_ratio - 1) * 30))
                else:
                    scores['money_flow_score'] = 50
                
                # 分析师情绪 (模拟: 近期涨跌幅)
                price_change = (df['close'].iloc[-1] / df['close'].iloc[-20] - 1) * 100
                scores['analyst_sentiment'] = min(100, max(0, 50 + price_change))
            else:
                scores['sentiment_score'] = 50
                scores['money_flow_score'] = 50
                scores['analyst_sentiment'] = 50
        else:
            scores['sentiment_score'] = 50
            scores['money_flow_score'] = 50
            scores['analyst_sentiment'] = 50
        
        # 行为因子综合
        scores['behavioral_score'] = (
            scores['sentiment_score'] * 0.3 +
            scores['money_flow_score'] * 0.3 +
            scores['analyst_sentiment'] * 0.2 +
            50 * 0.2  # 舆情中性
        )
        
        return scores
    
    def calculate_macro_factors(self, code: str) -> Dict:
        """计算宏观因子"""
        scores = {}
        
        # 货币环境 (模拟: 当前宽松周期)
        # 假设当前为宽松周期
        scores['monetary_score'] = 65
        
        # 经济周期 (模拟: 复苏期)
        scores['cycle_score'] = 60
        
        # 行业周期 (基于代码)
        if code.startswith('sh.60'):  # 主板
            scores['policy_score'] = 55
        elif code.startswith('sz.30'):  # 创业板
            scores['policy_score'] = 65  # 政策支持创新
        else:
            scores['policy_score'] = 50
        
        # 宏观因子综合
        scores['macro_score'] = (
            scores['monetary_score'] * 0.33 +
            scores['cycle_score'] * 0.33 +
            scores['policy_score'] * 0.34
        )
        
        return scores
    
    def calculate_quant_factors(self, code: str) -> Dict:
        """计算量化因子"""
        scores = {}
        
        # 估值因子
        val_score = 50
        if not self.dupont.empty and code in self.dupont['code'].values:
            df = self.dupont[self.dupont['code'] == code].sort_values('statDate', ascending=False).head(1)
            if not df.empty and 'dupontROE' in df.columns:
                roe = df['dupontROE'].iloc[0]
                if not pd.isna(roe):
                    val_score = min(100, max(0, 50 + roe * 100 * 2))
        scores['valuation_score'] = val_score
        
        # 成长因子
        growth_score = 50
        if not self.growth.empty and code in self.growth['code'].values:
            df = self.growth[self.growth['code'] == code].sort_values('statDate', ascending=False).head(1)
            if not df.empty and 'YOYAsset' in df.columns:
                yoy = df['YOYAsset'].iloc[0]
                if not pd.isna(yoy):
                    growth_score = min(100, max(0, 50 + yoy * 100))
        scores['growth_score'] = growth_score
        
        # 质量因子
        quality_score = 50
        if not self.profit.empty and code in self.profit['code'].values:
            df = self.profit[self.profit['code'] == code].sort_values('statDate', ascending=False).head(1)
            if not df.empty and 'npMargin' in df.columns:
                margin = df['npMargin'].iloc[0]
                if not pd.isna(margin):
                    quality_score = min(100, max(0, margin * 100 * 2))
        scores['quality_score'] = quality_score
        
        # 动量因子
        momentum_score = 50
        if code in self.stock_data:
            df = self.stock_data[code].tail(60)
            if len(df) > 30:
                mom = (df['close'].iloc[-1] / df['close'].iloc[-30] - 1) * 100
                momentum_score = min(100, max(0, 50 + mom * 2))
        scores['momentum_score'] = momentum_score
        
        # 量化因子综合
        scores['quant_score'] = (
            scores['valuation_score'] * 0.3 +
            scores['growth_score'] * 0.3 +
            scores['quality_score'] * 0.2 +
            scores['momentum_score'] * 0.2
        )
        
        return scores
    
    def analyze_stock(self, code: str, name: str) -> UnifiedScore:
        """分析单只股票"""
        behavioral = self.calculate_behavioral_factors(code)
        macro = self.calculate_macro_factors(code)
        quant = self.calculate_quant_factors(code)
        
        # 综合评分
        total = (
            behavioral['behavioral_score'] * 0.30 +
            macro['macro_score'] * 0.30 +
            quant['quant_score'] * 0.40
        )
        
        # 建议
        if total > 70:
            rec = "STRONG_BUY"
        elif total > 60:
            rec = "BUY"
        elif total > 45:
            rec = "HOLD"
        elif total > 35:
            rec = "SELL"
        else:
            rec = "STRONG_SELL"
        
        # 风险等级
        if total > 65 and behavioral['sentiment_score'] < 70:
            risk = "LOW"
        elif total > 45:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        
        return UnifiedScore(
            code=code, name=name,
            sentiment_score=behavioral['sentiment_score'],
            money_flow_score=behavioral['money_flow_score'],
            analyst_sentiment=behavioral['analyst_sentiment'],
            monetary_score=macro['monetary_score'],
            cycle_score=macro['cycle_score'],
            policy_score=macro['policy_score'],
            valuation_score=quant['valuation_score'],
            growth_score=quant['growth_score'],
            quality_score=quant['quality_score'],
            momentum_score=quant['momentum_score'],
            behavioral_score=behavioral['behavioral_score'],
            macro_score=macro['macro_score'],
            quant_score=quant['quant_score'],
            total_score=total,
            recommendation=rec,
            risk_level=risk
        )
    
    def run_analysis(self, stock_list: List[Tuple[str, str]]) -> List[UnifiedScore]:
        """运行分析"""
        results = []
        for code, name in stock_list:
            score = self.analyze_stock(code, name)
            results.append(score)
        
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    from pathlib import Path
    
    DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")
    OUTPUT_DIR = Path("/home/liujerry/金融数据/strategies")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 股票列表 (蓝筹 + 创业板)
    STOCKS = [
        ("sh.600000", "浦发银行"), ("sh.600016", "民生银行"),
        ("sh.600036", "招商银行"), ("sh.600050", "中国联通"),
        ("sh.600104", "上汽集团"), ("sh.600111", "北方稀土"),
        ("sh.600183", "生益科技"), ("sh.600196", "复星医药"),
        ("sh.600208", "新湖中宝"), ("sh.600219", "阳光电源"),
        ("sz.300033", "同花顺"), ("sz.300059", "东方财富"),
        ("sz.300015", "爱尔眼科"), ("sz.300017", "网宿科技"),
        ("sz.300073", "当升科技"), ("sz.300001", "特锐德"),
    ]
    
    print("="*80)
    print("📊 统合量化投资分析系统 v1.0")
    print("   整合: 行为金融学 + 货币金融学 + 量化金融学")
    print("="*80)
    print("\n因子权重:")
    print("   行为因子 (30%): 投资者情绪、资金流向、分析师情绪")
    print("   宏观因子 (30%): 货币环境、经济周期、政策影响")
    print("   量化因子 (40%): 估值、成长、质量、动量\n")
    
    analyzer = UnifiedQuantAnalyzer()
    analyzer.load_data(DATA_DIR)
    results = analyzer.run_analysis(STOCKS)
    
    # 输出
    print("-"*80)
    print(f"{'排名':<4} {'代码':<12} {'名称':<10} {'行为':>6} {'宏观':>6} {'量化':>6} {'总分':>6} {'建议':<12} {'风险'}")
    print("-"*80)
    
    for i, s in enumerate(results):
        print(f"{i+1:<4} {s.code:<12} {s.name:<10} "
              f"{s.behavioral_score:>6.1f} {s.macro_score:>6.1f} {s.quant_score:>6.1f} "
              f"{s.total_score:>6.1f} {s.recommendation:<12} {s.risk_level}")
    
    # 保存结果
    output = {
        "model": "UnifiedQuant_v1",
        "version": "1.0.0",
        "update_time": datetime.now().isoformat(),
        "framework": {
            "behavioral": "30% (情绪、资金流、分析师)",
            "macro": "30% (货币、周期、政策)",
            "quantitative": "40% (估值、成长、质量、动量)"
        },
        "results": [
            {
                "code": s.code,
                "name": s.name,
                "behavioral": round(s.behavioral_score, 1),
                "macro": round(s.macro_score, 1),
                "quant": round(s.quant_score, 1),
                "total": round(s.total_score, 1),
                "recommendation": s.recommendation,
                "risk": s.risk_level
            }
            for s in results
        ]
    }
    
    output_file = OUTPUT_DIR / "unified_quant_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存: {output_file}")
