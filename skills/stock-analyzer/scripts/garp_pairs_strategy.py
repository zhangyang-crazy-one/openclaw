#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GARP + 配对交易策略
====================
1. GARP (Growth at a Reasonable Price) - 合理价格成长策略
2. Pairs Trading - 基于相关性的配对交易

作者: OpenClaw Quant Team
版本: 1.1.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from scipy import stats
from sklearn.linear_model import LinearRegression
import json
import warnings
warnings.filterwarnings('ignore')


class SignalType(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0


@dataclass
class GARPSignal:
    stock_code: str
    growth_score: float
    valuation_score: float
    garp_score: float
    pe: float
    peg: float
    eps_growth: float
    recommendation: str


@dataclass
class PairsSignal:
    stock_a: str
    stock_b: str
    correlation: float
    spread_zscore: float
    signal: SignalType
    position: str
    expected_return: float


# ============================================
# GARP 策略
# ============================================

class GARPStrategy:
    """GARP (Growth at a Reasonable Price) 策略"""
    
    def __init__(self, 
                 lookback_eps: int = 4,
                 pe_threshold: float = 30,
                 peg_threshold: float = 1.5):
        self.lookback_eps = lookback_eps
        self.pe_threshold = pe_threshold
        self.peg_threshold = peg_threshold
        
    def calculate_growth(self, df: pd.DataFrame) -> float:
        """计算年化增长率"""
        prices = df['close'].dropna().values
        if len(prices) < 252:
            return 0.0
        start = prices[-252]
        end = prices[-1]
        if start <= 0:
            return 0.0
        return (end / start) - 1
    
    def calculate_pe(self, df: pd.DataFrame) -> float:
        """估算PE"""
        prices = df['close'].dropna().values
        if len(prices) < 252:
            return float('inf')
        returns = (prices[-1] / prices[-252]) - 1
        if returns <= 0:
            return float('inf')
        return min(1 / returns, self.pe_threshold)
    
    def calculate_peg(self, pe: float, growth: float) -> float:
        """计算PEG"""
        if pe <= 0 or growth <= 0:
            return float('inf')
        return min(pe / (growth * 100), self.peg_threshold * 2)
    
    def analyze_stock(self, df: pd.DataFrame, code: str) -> GARPSignal:
        """分析单只股票"""
        growth = self.calculate_growth(df)
        pe = self.calculate_pe(df)
        peg = self.calculate_peg(pe, growth)
        
        # 成长得分 (0-100)
        growth_score = min(100, max(0, (growth * 100)))
        # 估值得分 (0-100，越低越好)
        valuation_score = max(0, 100 - (pe / self.pe_threshold) * 50 - (peg / self.peg_threshold) * 30)
        garp_score = (growth_score + valuation_score) / 2
        
        recommendation = "BUY" if garp_score > 60 else "HOLD" if garp_score > 40 else "SELL"
        if pe > self.pe_threshold:
            recommendation = "SELL"
            
        return GARPSignal(
            stock_code=code,
            growth_score=growth_score,
            valuation_score=valuation_score,
            garp_score=garp_score,
            pe=pe,
            peg=peg,
            eps_growth=growth,
            recommendation=recommendation
        )
    
    def rank_stocks(self, stock_data: Dict[str, pd.DataFrame]) -> List[GARPSignal]:
        """排名所有股票"""
        signals = []
        for code, df in stock_data.items():
            signal = self.analyze_stock(df, code)
            signals.append(signal)
        signals.sort(key=lambda x: x.garp_score, reverse=True)
        return signals


# ============================================
# 配对交易策略
# ============================================

class PairsTradingStrategy:
    """基于相关性的配对交易策略"""
    
    def __init__(self, 
                 min_correlation: float = 0.6,
                 zscore_entry: float = 2.0,
                 zscore_exit: float = 0.5):
        self.min_correlation = min_correlation
        self.zscore_entry = zscore_entry
        self.zscore_exit = zscore_exit
        
    def calculate_hedge_ratio(self, price_a: np.ndarray, price_b: np.ndarray) -> float:
        """计算对冲比率"""
        valid = ~(np.isnan(price_a) | np.isnan(price_b))
        a, b = price_a[valid], price_b[valid]
        if len(a) < 10:
            return 1.0
        model = LinearRegression()
        model.fit(b.reshape(-1, 1), a)
        return model.coef_[0] if len(model.coef_) > 0 else 1.0
    
    def calculate_zscore(self, spread: np.ndarray, window: int = 20) -> float:
        """计算当前Z-score"""
        if len(spread) < window:
            return 0.0
        recent = spread[-window:]
        return (spread[-1] - np.mean(recent)) / (np.std(recent) + 1e-10)
    
    def analyze_pair(self, df_a: pd.DataFrame, df_b: pd.DataFrame,
                    code_a: str, code_b: str) -> PairsSignal:
        """分析配对"""
        # 收益率相关性
        returns_a = np.diff(df_a['close'].dropna().values) / (df_a['close'].dropna().values[:-1] + 1e-10)
        returns_b = np.diff(df_b['close'].dropna().values) / (df_b['close'].dropna().values[:-1] + 1e-10)
        correlation = np.corrcoef(returns_a, returns_b)[0, 1]
        
        # Spread和Z-score
        price_a = df_a['close'].dropna().values
        price_b = df_b['close'].dropna().values
        min_len = min(len(price_a), len(price_b), 252)
        price_a, price_b = price_a[-min_len:], price_b[-min_len:]
        
        hedge_ratio = self.calculate_hedge_ratio(price_a, price_b)
        spread = price_a - hedge_ratio * price_b
        zscore = self.calculate_zscore(spread)
        
        # 信号
        if abs(zscore) < self.zscore_exit:
            signal = SignalType.HOLD
            position = "观望"
        elif zscore > self.zscore_entry:
            signal = SignalType.SELL
            position = "做空A/做多B"
        elif zscore < -self.zscore_entry:
            signal = SignalType.BUY
            position = "做多A/做空B"
        else:
            signal = SignalType.HOLD
            position = "观望"
            
        expected = -zscore * 0.02
        
        return PairsSignal(
            stock_a=code_a, stock_b=code_b,
            correlation=correlation,
            spread_zscore=zscore,
            signal=signal, position=position,
            expected_return=expected
        )
    
    def find_pairs(self, stock_data: Dict[str, pd.DataFrame]) -> List[PairsSignal]:
        """寻找所有有效配对"""
        results = []
        codes = list(stock_data.keys())
        n = len(codes)
        
        print(f"   分析 {n} 只股票的配对...")
        
        for i in range(n):
            for j in range(i + 1, n):
                code_a, code_b = codes[i], codes[j]
                try:
                    signal = self.analyze_pair(
                        stock_data[code_a], stock_data[code_b], code_a, code_b
                    )
                    if signal.correlation > self.min_correlation:
                        results.append(signal)
                except:
                    continue
        
        results.sort(key=lambda x: x.correlation, reverse=True)
        print(f"   发现 {len(results)} 对高相关股票 (corr > {self.min_correlation})")
        return results


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    from pathlib import Path
    
    DATA_DIR = Path("/home/liujerry/金融数据/stocks")
    OUTPUT_DIR = Path("/home/liujerry/金融数据/strategies")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 蓝筹股列表
    BLUE_CHIP = [
        "600000", "600016", "600019", "600028", "600030",
        "600036", "600050", "600104", "600111", "600169",
        "600170", "600176", "600177", "600183", "600188",
        "600196", "600208", "600219", "600221", "600225",
        "600230", "600251", "600252", "600256", "600258",
        "600260", "600265", "600267", "600269", "600271",
        "600272", "600273", "600275", "600276", "600277",
        "600282", "600285", "600287", "600288", "600289",
        "600290", "600292", "600295", "600297", "600298",
    ]
    
    # 加载数据
    print("📂 加载股票数据...")
    stock_data = {}
    for code in BLUE_CHIP:
        filepath = DATA_DIR / f"{code}.csv"
        if filepath.exists():
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            for col in ['close', 'open', 'high', 'low', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['close'])
            if len(df) > 100:
                stock_data[code] = df
    
    print(f"   加载 {len(stock_data)} 只股票\n")
    
    # GARP策略
    print("="*60)
    print("📊 GARP 策略分析")
    print("="*60)
    
    garp = GARPStrategy()
    garp_signals = garp.rank_stocks(stock_data)
    
    print("\n   Top 10 GARP股票:")
    for i, s in enumerate(garp_signals[:10]):
        print(f"   {i+1}. {s.stock_code}: GARP={s.garp_score:.1f}, "
              f"PE={s.pe:.1f}, PEG={s.peg:.2f}, {s.recommendation}")
    
    # 配对交易
    print("\n" + "="*60)
    print("📊 配对交易分析")
    print("="*60)
    
    pairs = PairsTradingStrategy(min_correlation=0.6)
    pair_signals = pairs.find_pairs(stock_data)
    
    print("\n   Top 10 高相关配对:")
    for i, s in enumerate(pair_signals[:10]):
        print(f"   {i+1}. {s.stock_a}-{s.stock_b}: "
              f"corr={s.correlation:.3f}, z={s.spread_zscore:.2f}, {s.position}")
    
    # 保存结果
    output = {
        'garp_signals': [
            {'code': s.stock_code, 'garp': s.garp_score, 
             'pe': s.pe, 'peg': s.peg, 'rec': s.recommendation}
            for s in garp_signals[:20]
        ],
        'pairs_signals': [
            {'a': s.stock_a, 'b': s.stock_b, 'corr': s.correlation,
             'zscore': s.spread_zscore, 'signal': s.signal.name,
             'position': s.position}
            for s in pair_signals[:20]
        ]
    }
    
    with open(OUTPUT_DIR / 'garp_pairs_results.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存: {OUTPUT_DIR / 'garp_pairs_results.json'}")
