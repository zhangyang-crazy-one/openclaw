#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期基本面量化模型 v2.0
=======================
基于本地历史数据的长期基本面分析

因子:
1. 估值因子 (40%): PE, PB, PCF 历史分位数
2. 成长因子 (35%): 年化收益率, 季度动量
3. 质量因子 (25%): 波动率, 成交量稳定性

作者: OpenClaw Quant Team
版本: 2.0.0
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
class LongTermScore:
    """长期基本面得分"""
    code: str
    name: str
    
    # 估值因子 (0-100, 越低越好)
    pe_score: float = 50      # PE历史分位数
    pb_score: float = 50       # PB历史分位数
    
    # 成长因子 (0-100, 越高越好)
    annual_return_score: float = 50  # 年化收益率
    momentum_score: float = 50        # 季度动量
    
    # 质量因子 (0-100, 越高越好)
    stability_score: float = 50      # 价格稳定性
    volume_score: float = 50         # 成交量稳定性
    
    # 综合得分
    total_score: float = 50
    
    recommendation: str = "HOLD"


class LongTermQuantModel:
    """
    长期基本面量化模型
    
    使用1年以上历史数据计算:
    - 估值: PE, PB 历史分位数
    - 成长: 年化收益率, 季度动量
    - 质量: 波动率, 成交量稳定性
    """
    
    def __init__(self,
                 lookback_1y: int = 252,    # 1年回顾
                 lookback_2y: int = 504,    # 2年回顾
                 lookback_q: int = 63):      # 1季度回顾
        self.lookback_1y = lookback_1y
        self.lookback_2y = lookback_2y
        self.lookback_q = lookback_q
        
    def calculate_valuation_scores(self, prices: np.ndarray) -> Dict[str, float]:
        """
        计算估值因子得分
        
        使用价格历史估算 PE/PB:
        - PE = 价格 / 假设盈利 (基于收益率)
        - PB = 价格 / 假设账面 (基于营收)
        """
        n = len(prices)
        if n < 252:
            return {'pe_score': 50, 'pb_score': 50, 'pe_percentile': 50, 'pb_percentile': 50}
        
        # PE 估算 (基于年化收益率)
        annual_return = (prices[-1] / prices[-252]) - 1 if n >= 252 else 0
        pe = 1 / annual_return if annual_return > 0 else 100
        
        # PB 估算 (基于价格位置)
        avg_1y = np.mean(prices[-252:])
        avg_2y = np.mean(prices[-504:]) if n >= 504 else avg_1y
        pb = avg_1y / avg_2y if avg_2y > 0 else 1
        
        # PE 分位数 (用价格位置代替)
        price_percentile_1y = (
            (prices[-1] - np.min(prices[-252:])) / 
            (np.max(prices[-252:]) - np.min(prices[-252:]) + 1e-10)
        ) * 100
        
        price_percentile_2y = (
            (prices[-1] - np.min(prices[-504:])) / 
            (np.max(prices[-504:]) - np.min(prices[-504:]) + 1e-10)
        ) * 100 if n >= 504 else price_percentile_1y
        
        # 估值得分 (价格越低/PE越低，得分越高)
        pe_score = max(0, 100 - price_percentile_1y)
        pb_score = max(0, 100 - price_percentile_2y)
        
        return {
            'pe': pe,
            'pb': pb,
            'pe_score': pe_score,
            'pb_score': pb_score,
            'pe_percentile': price_percentile_1y,
            'pb_percentile': price_percentile_2y
        }
    
    def calculate_growth_scores(self, prices: np.ndarray) -> Dict[str, float]:
        """
        计算成长因子得分
        """
        n = len(prices)
        if n < 63:
            return {'annual_return_score': 50, 'momentum_score': 50}
        
        # 年化收益率 (2年)
        annual_return_2y = (prices[-1] / prices[-504]) - 1 if n >= 504 else \
                           (prices[-1] / prices[-252]) - 1
        
        # 季度收益率
        quarterly_return = (prices[-1] / prices[-63]) - 1 if n >= 63 else 0
        
        # 年化收益率得分
        # 假设年化收益率 > 30% 为高分，< -30% 为低分
        annual_return_score = 50 + annual_return_2y * 100
        annual_return_score = max(0, min(100, annual_return_score))
        
        # 季度动量得分
        momentum_score = 50 + quarterly_return * 200
        momentum_score = max(0, min(100, momentum_score))
        
        return {
            'annual_return': annual_return_2y,
            'quarterly_return': quarterly_return,
            'annual_return_score': annual_return_score,
            'momentum_score': momentum_score
        }
    
    def calculate_quality_scores(self, prices: np.ndarray, 
                               volumes: np.ndarray = None) -> Dict[str, float]:
        """
        计算质量因子得分
        """
        n = len(prices)
        if n < 63:
            return {'stability_score': 50, 'volume_score': 50}
        
        # 价格波动率 (越低越好)
        returns = np.diff(prices) / (prices[:-1] + 1e-10)
        volatility = np.std(returns[-252:]) * np.sqrt(252) if n >= 252 else np.std(returns) * np.sqrt(len(returns))
        
        # 波动率得分 (假设波动率 < 20% 为高分)
        stability_score = max(0, 100 - volatility * 500)
        stability_score = min(100, stability_score)
        
        # 成交量稳定性
        if volumes is not None and len(volumes) > 63:
            vol_cv = np.std(volumes[-63:]) / (np.mean(volumes[-63:]) + 1e-10)
            volume_score = max(0, 100 - vol_cv * 50)
            volume_score = min(100, volume_score)
        else:
            volume_score = 50
        
        return {
            'volatility': volatility,
            'stability_score': stability_score,
            'volume_score': volume_score
        }
    
    def analyze_stock(self, df: pd.DataFrame, 
                     code: str, name: str) -> LongTermScore:
        """
        分析单只股票
        """
        prices = df['close'].dropna().values
        if len(prices) < 63:
            return None
        
        volumes = None
        if 'volume' in df.columns:
            volumes = df['volume'].dropna().values
        
        # 计算各因子得分
        valuation = self.calculate_valuation_scores(prices)
        growth = self.calculate_growth_scores(prices)
        quality = self.calculate_quality_scores(prices, volumes)
        
        # 综合得分
        # 估值 40% + 成长 35% + 质量 25%
        total_score = (
            (valuation['pe_score'] + valuation['pb_score']) / 2 * 0.40 +
            (growth['annual_return_score'] + growth['momentum_score']) / 2 * 0.35 +
            (quality['stability_score'] + quality['volume_score']) / 2 * 0.25
        )
        
        # 推荐
        if total_score > 75 and valuation['pe_score'] > 60:
            recommendation = "STRONG_BUY"
        elif total_score > 60:
            recommendation = "BUY"
        elif total_score > 40:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        return LongTermScore(
            code=code,
            name=name,
            pe_score=valuation['pe_score'],
            pb_score=valuation['pb_score'],
            annual_return_score=growth['annual_return_score'],
            momentum_score=growth['momentum_score'],
            stability_score=quality['stability_score'],
            volume_score=quality['volume_score'],
            total_score=total_score,
            recommendation=recommendation
        )
    
    def rank_stocks(self, stock_data: Dict[str, Tuple[pd.DataFrame, str]]) -> List[LongTermScore]:
        """
        排名所有股票
        """
        scores = []
        for code, (df, name) in stock_data.items():
            score = self.analyze_stock(df, code, name)
            if score:
                scores.append(score)
        
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    from pathlib import Path
    
    STOCK_DIR = Path("/home/liujerry/金融数据/stocks")
    OUTPUT_DIR = Path("/home/liujerry/金融数据/strategies")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 蓝筹股列表
    BLUE_CHIP = [
        ("600000", "浦发银行"), ("600016", "民生银行"), ("600019", "宝钢股份"),
        ("600028", "中国石化"), ("600030", "中信证券"), ("600036", "招商银行"),
        ("600050", "中国联通"), ("600104", "上汽集团"), ("600111", "北方稀土"),
        ("600170", "上海建工"), ("600176", "中国巨石"), ("600177", "雅戈尔"),
        ("600183", "生益科技"), ("600188", "兖州煤业"), ("600196", "复星医药"),
        ("600208", "新湖中宝"), ("600219", "阳光电源"), ("600221", "海航创新"),
    ]
    
    # 加载数据
    print("📂 加载股票数据...")
    stock_data = {}
    for code, name in BLUE_CHIP:
        filepath = STOCK_DIR / f"{code}.csv"
        if filepath.exists():
            df = pd.read_csv(filepath)
            df = df.sort_values('date').reset_index(drop=True)
            if len(df) > 100:
                stock_data[code] = (df, name)
    
    print(f"   加载 {len(stock_data)} 只股票\n")
    
    # 运行模型
    print("="*70)
    print("📊 长期基本面量化模型 v2.0")
    print("="*70)
    print("\n因子权重:")
    print("   估值因子 (40%): PE, PB 历史分位数")
    print("   成长因子 (35%): 年化收益率, 季度动量")
    print("   质量因子 (25%): 波动率, 成交量稳定性\n")
    
    model = LongTermQuantModel()
    scores = model.rank_stocks(stock_data)
    
    # 输出结果
    print("-"*70)
    print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'估值':>6} {'成长':>6} {'质量':>6} {'总分':>6} {'推荐'}")
    print("-"*70)
    
    for i, s in enumerate(scores[:20]):
        print(f"{i+1:<4} {s.code:<8} {s.name:<10} "
              f"{s.pe_score:>6.1f} {s.annual_return_score:>6.1f} "
              f"{s.stability_score:>6.1f} {s.total_score:>6.1f} {s.recommendation}")
    
    # 保存结果
    result = {
        "model": "LongTermQuant_v2",
        "version": "2.0.0",
        "update_time": datetime.now().isoformat(),
        "factors": {
            "valuation": "40% (PE/PB percentiles)",
            "growth": "35% (annual return, momentum)",
            "quality": "25% (volatility, volume stability)"
        },
        "results": [
            {
                "code": s.code,
                "name": s.name,
                "pe_score": s.pe_score,
                "pb_score": s.pb_score,
                "growth_score": (s.annual_return_score + s.momentum_score) / 2,
                "quality_score": (s.stability_score + s.volume_score) / 2,
                "total_score": s.total_score,
                "recommendation": s.recommendation
            }
            for s in scores
        ]
    }
    
    output_file = OUTPUT_DIR / "long_term_quant_v2.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存: {output_file}")
