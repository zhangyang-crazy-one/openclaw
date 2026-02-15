#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期基本面量化模型 v3.2 - 基于Baostock真实财报数据
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


@dataclass
class FundamentalScore:
    code: str
    name: str
    pb_score: float = 50
    roe_score: float = 50
    revenue_growth_score: float = 50
    profit_growth_score: float = 50
    profit_margin_score: float = 50
    gross_margin_score: float = 50
    asset_turn_score: float = 50
    total_score: float = 50
    recommendation: str = "HOLD"


class FundamentalQuantModelV3:
    def __init__(self):
        self.dupont = None
        self.growth = None
        self.profit = None
        
    def load_data(self, data_dir: Path):
        print("📂 加载财报数据...")
        
        dupont_file = data_dir / "baostock_dupont.csv"
        if dupont_file.exists():
            self.dupont = pd.read_csv(dupont_file)
            print(f"   ✅ 杜邦分析: {len(self.dupont)} 条")
        
        growth_file = data_dir / "baostock_growth.csv"
        if growth_file.exists():
            self.growth = pd.read_csv(growth_file)
            print(f"   ✅ 成长能力: {len(self.growth)} 条")
        
        profit_file = data_dir / "baostock_profit.csv"
        if profit_file.exists():
            self.profit = pd.read_csv(profit_file)
            print(f"   ✅ 盈利能力: {len(self.profit)} 条")
    
    def get_latest_financials(self, code: str) -> Dict:
        result = {
            'roe': None, 'revenue_growth': None, 'profit_growth': None,
            'profit_margin': None, 'gross_margin': None, 'asset_turn': None
        }
        
        # 杜邦分析
        if self.dupont is not None:
            df = self.dupont[self.dupont['code'] == code].sort_values('statDate', ascending=False)
            if not df.empty:
                roe = df['dupontROE'].dropna().head(1).values
                result['roe'] = float(roe[0]) * 100 if len(roe) > 0 and not pd.isna(roe[0]) else None
                at = df['dupontAssetTurn'].dropna().head(1).values
                result['asset_turn'] = float(at[0]) * 100 if len(at) > 0 and not pd.isna(at[0]) else None
        
        # 成长能力
        if self.growth is not None:
            df = self.growth[self.growth['code'] == code].sort_values('statDate', ascending=False)
            if not df.empty:
                rev = df['YOYAsset'].dropna().head(1).values
                result['revenue_growth'] = float(rev[0]) * 100 if len(rev) > 0 and not pd.isna(rev[0]) else None
                prof = df['YOYNI'].dropna().head(1).values
                result['profit_growth'] = float(prof[0]) * 100 if len(prof) > 0 and not pd.isna(prof[0]) else None
        
        # 盈利能力
        if self.profit is not None:
            df = self.profit[self.profit['code'] == code].sort_values('statDate', ascending=False)
            if not df.empty:
                pm = df['npMargin'].dropna().head(1).values
                result['profit_margin'] = float(pm[0]) * 100 if len(pm) > 0 and not pd.isna(pm[0]) else None
                gm = df['gpMargin'].dropna().head(1).values
                result['gross_margin'] = float(gm[0]) * 100 if len(gm) > 0 and not pd.isna(gm[0]) else None
        
        return result
    
    def calculate_scores(self, fin_data: Dict) -> Dict:
        scores = {}
        
        roe = fin_data.get('roe')
        scores['roe_score'] = min(100, max(0, 50 + roe * 2)) if roe else 50
        
        rev = fin_data.get('revenue_growth')
        scores['revenue_growth_score'] = min(100, max(0, 50 + rev)) if rev else 50
        
        prof = fin_data.get('profit_growth')
        scores['profit_growth_score'] = min(100, max(0, 50 + prof)) if prof else 50
        
        pm = fin_data.get('profit_margin')
        scores['profit_margin_score'] = min(100, max(0, pm * 1.5)) if pm else 50
        
        gm = fin_data.get('gross_margin')
        scores['gross_margin_score'] = min(100, max(0, gm)) if gm else 50
        
        at = fin_data.get('asset_turn')
        scores['asset_turn_score'] = min(100, max(0, at * 4)) if at else 50
        
        scores['pb_score'] = min(100, max(0, 50 + roe * 1.5)) if roe else 50
        
        return scores
    
    def analyze_stock(self, code: str, name: str) -> FundamentalScore:
        fin_data = self.get_latest_financials(code)
        scores = self.calculate_scores(fin_data)
        
        total = (
            scores['pb_score'] * 0.30 +
            (scores['roe_score'] + scores['revenue_growth_score'] + scores['profit_growth_score']) / 3 * 0.40 +
            (scores['profit_margin_score'] + scores['gross_margin_score'] + scores['asset_turn_score']) / 3 * 0.30
        )
        
        if total > 75: rec = "STRONG_BUY"
        elif total > 60: rec = "BUY"
        elif total > 40: rec = "HOLD"
        else: rec = "SELL"
        
        return FundamentalScore(
            code=code, name=name,
            pb_score=scores['pb_score'], roe_score=scores['roe_score'],
            revenue_growth_score=scores['revenue_growth_score'],
            profit_growth_score=scores['profit_growth_score'],
            profit_margin_score=scores['profit_margin_score'],
            gross_margin_score=scores['gross_margin_score'],
            asset_turn_score=scores['asset_turn_score'],
            total_score=total, recommendation=rec
        )
    
    def run_analysis(self, stock_list: List[tuple]) -> List[FundamentalScore]:
        results = [self.analyze_stock(c, n) for c, n in stock_list]
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results


if __name__ == "__main__":
    DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")
    OUTPUT_DIR = Path("/home/liujerry/金融数据/strategies")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    BLUE_CHIP = [
        ("sh.600000", "浦发银行"), ("sh.600016", "民生银行"),
        ("sh.600036", "招商银行"), ("sh.600028", "中国石化"),
        ("sh.600030", "中信证券"), ("sh.600050", "中国联通"),
        ("sh.600104", "上汽集团"), ("sh.600111", "北方稀土"),
        ("sh.600170", "上海建工"), ("sh.600176", "中国巨石"),
        ("sh.600177", "雅戈尔"), ("sh.600183", "生益科技"),
        ("sh.600188", "兖州煤业"), ("sh.600196", "复星医药"),
        ("sh.600208", "新湖中宝"), ("sh.600219", "阳光电源"),
    ]
    
    print("="*70)
    print("📊 长期基本面量化模型 v3.2 (Baostock真实财报)")
    print("="*70)
    print("\n因子权重: 估值30% | 成长40% | 质量30%\n")
    
    model = FundamentalQuantModelV3()
    model.load_data(DATA_DIR)
    results = model.run_analysis(BLUE_CHIP)
    
    print("-"*70)
    print(f"{'排名':<4} {'代码':<10} {'名称':<10} {'估值':>6} {'成长':>6} {'质量':>6} {'总分':>6} {'推荐'}")
    print("-"*70)
    
    for i, s in enumerate(results):
        growth = (s.roe_score + s.revenue_growth_score + s.profit_growth_score) / 3
        quality = (s.profit_margin_score + s.gross_margin_score + s.asset_turn_score) / 3
        print(f"{i+1:<4} {s.code:<10} {s.name:<10} {s.pb_score:>6.1f} {growth:>6.1f} {quality:>6.1f} {s.total_score:>6.1f} {s.recommendation}")
    
    output = {
        "model": "FundamentalQuant_v3.2",
        "version": "3.2.0",
        "data_source": "Baostock",
        "update_time": datetime.now().isoformat(),
        "factors": {"valuation": "30%", "growth": "40%", "quality": "30%"},
        "results": [
            {"code": s.code, "name": s.name, "total_score": s.total_score, "recommendation": s.recommendation}
            for s in results
        ]
    }
    
    output_file = OUTPUT_DIR / "fundamental_quant_v3.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存: {output_file}")
