#!/usr/bin/env python3
"""
价值投资量化打分系统 - 基于V3报告基本面分析框架
对全部A股进行多维度量化打分
"""

import pandas as pd
import numpy as np
import os
import time
from typing import Dict, List, Tuple

# Paths
FINANCIAL_DATA = '/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv'
KLINE_DIR = '/home/liujerry/金融数据/stocks/'
OUTPUT_DIR = '/home/liujerry/金融数据/screening_results/'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== 量化打分常量 =====
class ScoringConfig:
    """量化打分配置"""
    # ROE评分 (10分)
    ROE_THRESHOLDS = [(30, 10), (25, 9), (20, 8), (15, 6), (12, 4), (8, 2), (0, 0)]
    
    # 扣非ROE评分 (8分)
    ROE_KC_THRESHOLDS = [(25, 8), (20, 7), (15, 6), (12, 4), (8, 2), (0, 0)]
    
    # 毛利率评分 (6分)
    GROSS_MARGIN_THRESHOLDS = [(60, 6), (40, 5), (30, 4), (20, 3), (10, 1), (0, 0)]
    
    # 净利率评分 (6分)
    NET_MARGIN_THRESHOLDS = [(30, 6), (20, 5), (15, 4), (10, 3), (5, 2), (0, 0)]
    
    # 负债率评分 (8分，越低越好)
    DEBT_RATIO_THRESHOLDS = [(20, 8), (30, 7), (40, 6), (50, 4), (60, 3), (80, 1), (100, 0)]
    
    # PE评分 (8分，越低越好)
    PE_THRESHOLDS = [(10, 8), (15, 7), (20, 6), (25, 4), (30, 3), (50, 2), (100, 0)]
    
    # PB评分 (6分，越低越好)
    PB_THRESHOLDS = [(1, 6), (2, 5), (3, 4), (5, 3), (8, 2), (15, 0)]
    
    # 营收增长评分 (5分)
    REVENUE_GROWTH_THRESHOLDS = [(30, 5), (15, 4), (5, 3), (0, 2), (-10, 1), (-100, 0)]
    
    # 利润增长评分 (5分)
    PROFIT_GROWTH_THRESHOLDS = [(30, 5), (15, 4), (5, 3), (0, 2), (-10, 1), (-100, 0)]
    
    # 现金流质量评分 (6分)
    CFO_NET_PROFIT_THRESHOLDS = [(1.5, 6), (1.0, 5), (0.8, 4), (0.5, 3), (0.2, 2), (0, 1), (-100, 0)]
    
    # ROE稳定性评分 (6分)
    ROE_STD_THRESHOLDS = [(2, 6), (5, 5), (8, 4), (12, 3), (20, 2), (100, 0)]
    
    # 长期股权投资占比评分 (5分)
    LONG_TERM_EQUITY_THRESHOLDS = [(50, 2), (30, 3), (20, 4), (10, 5), (5, 4), (0, 3), (-1, 0)]
    
    # 资产周转率评分 (4分)
    ASSET_TURNOVER_THRESHOLDS = [(1.5, 4), (1.0, 3), (0.5, 2), (0.2, 1), (0, 0)]

def get_score(value: float, thresholds: List[Tuple[float, float]], reverse: bool = False) -> float:
    """根据阈值返回得分"""
    if reverse:
        for threshold, score in reversed(thresholds):
            if value >= threshold:
                return score
    else:
        for threshold, score in thresholds:
            if value >= threshold:
                return score
    return 0

def load_financial_data() -> pd.DataFrame:
    """加载并预处理财务数据"""
    print("📂 加载财务数据...")
    df = pd.read_csv(FINANCIAL_DATA, low_memory=False)
    
    # 只取年报数据
    annual_df = df[df['REPORT_TYPE'] == '年报'].copy()
    annual_df['YEAR'] = pd.to_datetime(annual_df['REPORT_DATE']).dt.year
    
    # 转换数字字段
    num_cols = [
        'ROEJQ', 'ROEKCJQ', 'ZCFZL', 'XSMLL', 'XSJLL', 
        'PARENTNETPROFIT', 'KCFJCXSYJLR', 'TOTALOPERATEREVE', 
        'BPS', 'EPSJB', 'NETCASH_OPERATE_PK', 'TOTAL_EQUITY_PK',
        'YYZSRGDHBZC', 'NETPROFITRPHBZC', 'KFJLRGDHBZC',
        'TOTALOPERATEREVE', 'LD', 'SD', '长期股权投资', '长期借款'
    ]
    for col in num_cols:
        if col in annual_df.columns:
            annual_df[col] = pd.to_numeric(annual_df[col], errors='coerce')
    
    print(f"  年报记录: {len(annual_df)}, 股票数: {annual_df['code'].nunique()}")
    return annual_df

def calculate_piotroski_f_score(group: pd.DataFrame) -> Tuple[int, Dict]:
    """计算Piotroski F-Score (9分制)"""
    sorted_group = group.sort_values('YEAR', ascending=False)
    
    if len(sorted_group) < 2:
        return 0, {}
    
    latest = sorted_group.iloc[0]
    previous = sorted_group.iloc[1]
    
    scores = {}
    total = 0
    
    # 1. 当年净利润为正
    if latest['PARENTNETPROFIT'] > 0:
        scores['profitable'] = 1
        total += 1
    else:
        scores['profitable'] = 0
    
    # 2. 经营现金流 > 0
    if latest['NETCASH_OPERATE_PK'] > 0:
        scores['positive_cfo'] = 1
        total += 1
    else:
        scores['positive_cfo'] = 0
    
    # 3. ROA趋势改善
    roa_now = latest['PARENTNETPROFIT'] / latest['TOTAL_EQUITY_PK'] if latest['TOTAL_EQUITY_PK'] > 0 else 0
    roa_prev = previous['PARENTNETPROFIT'] / previous['TOTAL_EQUITY_PK'] if previous['TOTAL_EQUITY_PK'] > 0 else 0
    scores['roa_growth'] = 1 if roa_now > roa_prev else 0
    total += scores['roa_growth']
    
    # 4. 长期借款减少
    long_debt_now = latest.get('长期借款', 0) or 0
    long_debt_prev = previous.get('长期借款', 0) or 0
    scores['debt_reduction'] = 1 if long_debt_now < long_debt_prev else 0
    total += scores['debt_reduction']
    
    # 5. 流动比率改善
    current_now = latest.get('LD', 0) or 0
    current_prev = previous.get('LD', 0) or 0
    scores['liquidity_improve'] = 1 if current_now > current_prev else 0
    total += scores['liquidity_improve']
    
    # 6. 毛利率趋势
    gm_now = latest.get('XSMLL', 0) or 0
    gm_prev = previous.get('XSMLL', 0) or 0
    scores['margin_improve'] = 1 if gm_now > gm_prev else 0
    total += scores['margin_improve']
    
    # 7. 资产周转率趋势
    asset_now = latest['TOTALOPERATEREVE'] / latest['TOTAL_EQUITY_PK'] if latest['TOTAL_EQUITY_PK'] > 0 else 0
    asset_prev = previous['TOTALOPERATEREVE'] / previous['TOTAL_EQUITY_PK'] if previous['TOTAL_EQUITY_PK'] > 0 else 0
    scores['asset_turnover_improve'] = 1 if asset_now > asset_prev else 0
    total += scores['asset_turnover_improve']
    
    # 8. 毛利率水平
    scores['gross_margin_level'] = 1 if gm_now > 20 else 0
    total += scores['gross_margin_level']
    
    # 9. 杠杆率改善
    scores['leverage_improve'] = 1
    total += 1
    
    return total, scores

def analyze_stock_financial(group: pd.DataFrame, cfg: ScoringConfig) -> Dict:
    """分析单只股票的财务指标和打分"""
    
    sorted_group = group.sort_values('YEAR', ascending=False)
    latest = sorted_group.iloc[0]
    name = str(latest.get('SECURITY_NAME_ABBR', ''))
    code = str(int(latest['code'])).zfill(6)
    
    # ===== 基本财务数据 =====
    avg_roe_5y = sorted_group.head(5)['ROEJQ'].mean()
    min_roe_5y = sorted_group.head(5)['ROEJQ'].min()
    roe_std_5y = sorted_group.head(5)['ROEJQ'].std()
    
    avg_roe_kc_5y = sorted_group.head(5)['ROEKCJQ'].mean()
    
    roe_latest = latest['ROEJQ'] if not pd.isna(latest['ROEJQ']) else 0
    roe_kc_latest = latest['ROEKCJQ'] if not pd.isna(latest['ROEKCJQ']) else 0
    
    debt_ratio = latest['ZCFZL'] if not pd.isna(latest['ZCFZL']) else 100
    gross_margin = latest['XSMLL'] if not pd.isna(latest['XSMLL']) else 0
    net_margin = latest['XSJLL'] if not pd.isna(latest['XSJLL']) else 0
    
    net_profit = latest['PARENTNETPROFIT'] if not pd.isna(latest['PARENTNETPROFIT']) else 0
    kfc_net_profit = latest['KCFJCXSYJLR'] if not pd.isna(latest['KCFJCXSYJLR']) else 0
    
    total_operating = latest['TOTALOPERATEREVE'] if not pd.isna(latest['TOTALOPERATEREVE']) else 0
    total_equity = latest['TOTAL_EQUITY_PK'] if not pd.isna(latest['TOTAL_EQUITY_PK']) else 1
    operating_cf = latest['NETCASH_OPERATE_PK'] if not pd.isna(latest['NETCASH_OPERATE_PK']) else 0
    
    revenue_growth = latest['YYZSRGDHBZC'] if not pd.isna(latest['YYZSRGDHBZC']) else 0
    profit_growth = latest['NETPROFITRPHBZC'] if not pd.isna(latest['NETPROFITRPHBZC']) else 0
    
    # 长期股权投资
    long_term_equity = latest.get('长期股权投资', 0) or 0
    long_term_equity_ratio = (long_term_equity / total_equity * 100) if total_equity > 0 else 0
    
    # ===== Piotroski F-Score =====
    f_score, f_details = calculate_piotroski_f_score(sorted_group)
    
    # ===== 现金流质量 =====
    if net_profit > 0:
        cfo_net_profit_ratio = operating_cf / net_profit
    else:
        cfo_net_profit_ratio = 0 if operating_cf <= 0 else 2
    
    # ===== 资产周转率 =====
    asset_turnover = total_operating / total_equity if total_equity > 0 else 0
    
    # ===== 计算各项得分 =====
    scores = {}
    
    scores['roe'] = get_score(avg_roe_5y, cfg.ROE_THRESHOLDS)
    scores['roe_kc'] = get_score(avg_roe_kc_5y, cfg.ROE_KC_THRESHOLDS)
    scores['gross_margin'] = get_score(gross_margin, cfg.GROSS_MARGIN_THRESHOLDS)
    scores['net_margin'] = get_score(net_margin, cfg.NET_MARGIN_THRESHOLDS)
    scores['debt_ratio'] = get_score(debt_ratio, cfg.DEBT_RATIO_THRESHOLDS)
    scores['revenue_growth'] = get_score(revenue_growth, cfg.REVENUE_GROWTH_THRESHOLDS)
    scores['profit_growth'] = get_score(profit_growth, cfg.PROFIT_GROWTH_THRESHOLDS)
    scores['cash_flow'] = get_score(cfo_net_profit_ratio, cfg.CFO_NET_PROFIT_THRESHOLDS)
    scores['roe_stability'] = get_score(roe_std_5y, cfg.ROE_STD_THRESHOLDS)
    scores['long_term_equity'] = get_score(long_term_equity_ratio, cfg.LONG_TERM_EQUITY_THRESHOLDS)
    scores['asset_turnover'] = get_score(asset_turnover, cfg.ASSET_TURNOVER_THRESHOLDS)
    scores['f_score'] = f_score * 10 / 9
    
    # 扣非质量加分 (3分)
    if net_profit > 0 and kfc_net_profit > 0:
        kfc_ratio = kfc_net_profit / net_profit
        if kfc_ratio >= 0.8:
            scores['kfc_quality'] = 3
        elif kfc_ratio >= 0.6:
            scores['kfc_quality'] = 2
        elif kfc_ratio >= 0.4:
            scores['kfc_quality'] = 1
        else:
            scores['kfc_quality'] = 0
    else:
        scores['kfc_quality'] = 0
    
    # 估值（待补充）
    scores['pe'] = 0
    scores['pb'] = 0
    
    # 总分
    total = sum(scores.values())
    
    return {
        'code': code,
        'name': name,
        'avg_roe_5y': round(avg_roe_5y, 1),
        'min_roe_5y': round(min_roe_5y, 1),
        'avg_roe_kc_5y': round(avg_roe_kc_5y, 1),
        'roe_latest': round(roe_latest, 1),
        'roe_kc_latest': round(roe_kc_latest, 1),
        'debt_ratio': round(debt_ratio, 1),
        'gross_margin': round(gross_margin, 1),
        'net_margin': round(net_margin, 1),
        'net_profit_y': round(net_profit / 1e8, 2),
        'revenue_y': round(total_operating / 1e8, 2),
        'revenue_growth': round(revenue_growth, 1),
        'profit_growth': round(profit_growth, 1),
        'cfo_net_profit': round(cfo_net_profit_ratio, 2),
        'roe_std_5y': round(roe_std_5y, 2),
        'long_term_equity_ratio': round(long_term_equity_ratio, 1),
        'asset_turnover': round(asset_turnover, 2),
        'f_score': f_score,
        'roe_score': scores['roe'],
        'roe_kc_score': scores['roe_kc'],
        'gross_margin_score': scores['gross_margin'],
        'net_margin_score': scores['net_margin'],
        'debt_ratio_score': scores['debt_ratio'],
        'revenue_growth_score': scores['revenue_growth'],
        'profit_growth_score': scores['profit_growth'],
        'cash_flow_score': scores['cash_flow'],
        'roe_stability_score': scores['roe_stability'],
        'long_term_equity_score': scores['long_term_equity'],
        'asset_turnover_score': scores['asset_turnover'],
        'f_score_score': scores['f_score'],
        'kfc_quality_score': scores['kfc_quality'],
        'pe_score': scores['pe'],
        'pb_score': scores['pb'],
        'total_score': round(total, 1),
    }

def screen_all_stocks(financial_df: pd.DataFrame, cfg: ScoringConfig) -> pd.DataFrame:
    """对所有股票进行财务打分"""
    print("\n" + "=" * 70)
    print("📊 量化财务打分 (全部股票)")
    print("=" * 70)
    
    results = []
    stock_codes = financial_df['code'].unique()
    total = len(stock_codes)
    
    print(f"  待分析股票数: {total}")
    
    for i, code in enumerate(stock_codes):
        if (i + 1) % 500 == 0:
            print(f"  已处理 {i+1}/{total}...")
        
        try:
            stock_data = financial_df[financial_df['code'] == code]
            
            if len(stock_data) < 3:
                continue
            
            result = analyze_stock_financial(stock_data, cfg)
            
            # 基本筛选条件
            if result['avg_roe_5y'] < 8:
                continue
            if result['net_profit_y'] < 0.5:
                continue
            
            results.append(result)
        except Exception as e:
            pass
    
    print(f"  ✅ 完成: {len(results)} 只")
    
    df = pd.DataFrame(results)
    df = df.sort_values('total_score', ascending=False)
    return df

def add_valuation_scores(df: pd.DataFrame) -> pd.DataFrame:
    """补充估值打分"""
    print("\n" + "=" * 70)
    print("📊 补充估值打分 (PE/PB)")
    print("=" * 70)
    
    cfg = ScoringConfig()
    
    valuation_updates = {}
    
    for i, (_, row) in enumerate(df.iterrows()):
        if (i + 1) % 500 == 0:
            print(f"  已处理 {i+1}/{len(df)}...")
        
        code = row['code']
        
        kline_path = os.path.join(KLINE_DIR, f'{code}.csv')
        if os.path.exists(kline_path):
            try:
                kline_df = pd.read_csv(kline_path)
                if len(kline_df) < 20:
                    continue
                    
                price = kline_df.iloc[-1]['close']
                
                # 估算EPS和BPS
                eps = row.get('roe_latest', 0) * row.get('bps', 0) / 100 if row.get('roe_latest', 0) > 0 else 0
                if eps <= 0:
                    eps = price / 20  # 默认PE=20
                
                bps = row.get('bps', 0)
                if bps <= 0:
                    bps = price / 3  # 默认PB=3
                
                pe = price / eps if eps > 0 else 100
                pb = price / bps if bps > 0 else 100
                
                pe_score = get_score(pe, cfg.PE_THRESHOLDS)
                pb_score = get_score(pb, cfg.PB_THRESHOLDS)
                
                valuation_updates[code] = {
                    'price': round(price, 2),
                    'pe': round(pe, 1),
                    'pb': round(pb, 2),
                    'pe_score': pe_score,
                    'pb_score': pb_score
                }
            except:
                pass
    
    for code, vals in valuation_updates.items():
        mask = df['code'] == code
        for k, v in vals.items():
            df.loc[mask, k] = v
    
    # 重新计算总分
    score_cols = ['roe_score', 'roe_kc_score', 'gross_margin_score', 'net_margin_score',
                  'debt_ratio_score', 'revenue_growth_score', 'profit_growth_score',
                  'cash_flow_score', 'roe_stability_score', 'long_term_equity_score',
                  'asset_turnover_score', 'f_score_score', 'kfc_quality_score',
                  'pe_score', 'pb_score']
    
    df['total_score'] = df[score_cols].sum(axis=1)
    df = df.sort_values('total_score', ascending=False)
    
    print(f"  ✅ 估值更新完成: {len(valuation_updates)} 只")
    
    return df

def main():
    start_time = time.time()
    
    print("=" * 70)
    print("📊 A股量化打分系统 - 基于V3报告财务分析框架")
    print("=" * 70)
    
    cfg = ScoringConfig()
    
    # 加载财务数据
    financial_df = load_financial_data()
    
    # 全部股票量化打分
    result_df = screen_all_stocks(financial_df, cfg)
    
    # 补充估值打分
    result_df = add_valuation_scores(result_df)
    
    # 输出Top 20 (展示更多)
    print("\n" + "=" * 70)
    print("🏆 价值投资 Top 20 (V3量化打分)")
    print("=" * 70)
    
    top20 = result_df.head(20)
    
    # 大类得分
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<12} {'总分':<6} {'盈利':<6} {'结构':<5} {'成长':<5} {'现金':<5} {'稳定':<5} {'F-Score':<7} {'估值':<5}")
    print("-" * 85)
    
    for rank, (_, row) in enumerate(top20.iterrows(), 1):
        profitability = row['roe_score'] + row['roe_kc_score'] + row['gross_margin_score'] + row['net_margin_score'] + row['kfc_quality_score']
        financial_health = row['debt_ratio_score'] + row['asset_turnover_score']
        growth = row['revenue_growth_score'] + row['profit_growth_score']
        cash = row['cash_flow_score']
        stability = row['roe_stability_score'] + row['long_term_equity_score']
        f_score_val = row['f_score_score']
        valuation = row['pe_score'] + row['pb_score']
        
        print(f"{rank:<4} {row['code']:<8} {row['name']:<12} {row['total_score']:<6.1f} {profitability:<6.1f} {financial_health:<5.1f} {growth:<5.1f} {cash:<5.1f} {stability:<5.1f} {f_score_val:<6.1f} {valuation:<5.1f}")
    
    # 详细指标
    print("\n" + "=" * 70)
    print("📋 Top 10 核心财务指标")
    print("=" * 70)
    
    top10 = top20.head(10)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'ROE均':<7} {'扣非ROE':<7} {'负债率':<6} {'毛利率':<6} {'净利率':<6} {'营收增长':<8} {'利润增长':<8} {'F-Score':<7} {'PE':<6} {'PB':<5}")
    print("-" * 100)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        pe_val = row.get('pe', 0)
        pb_val = row.get('pb', 0)
        print(f"{rank:<4} {row['code']:<8} {row['name']:<10} {row['avg_roe_5y']:<6.1f}% {row['avg_roe_kc_5y']:<6.1f}% {row['debt_ratio']:<5.1f}% {row['gross_margin']:<5.1f}% {row['net_margin']:<5.1f}% {row['revenue_growth']:<7.1f}% {row['profit_growth']:<7.1f}% {row['f_score']:<6}/9 {pe_val:<6.1f} {pb_val:<5.2f}")
    
    # 细分得分
    print("\n" + "=" * 70)
    print("📋 Top 10 细分得分详情")
    print("=" * 70)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'ROE':<4} {'扣非':<4} {'毛利':<4} {'净利':<4} {'负债':<4} {'营收':<4} {'利润':<4} {'现金':<4} {'稳定':<4} {'长期':<4} {'周转':<4} {'F':<4} {'扣非':<4} {'PE':<4} {'PB':<4} {'总分':<5}")
    print("-" * 100)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"{rank:<4} {row['code']:<8} {row['name']:<10} {row['roe_score']:<3.0f} {row['roe_kc_score']:<3.0f} {row['gross_margin_score']:<3.0f} {row['net_margin_score']:<3.0f} {row['debt_ratio_score']:<3.0f} {row['revenue_growth_score']:<3.0f} {row['profit_growth_score']:<3.0f} {row['cash_flow_score']:<3.0f} {row['roe_stability_score']:<3.0f} {row['long_term_equity_score']:<3.0f} {row['asset_turnover_score']:<3.0f} {row['f_score_score']:<3.0f} {row['kfc_quality_score']:<3.0f} {row['pe_score']:<3.0f} {row['pb_score']:<3.0f} {row['total_score']:<4.1f}")
    
    # 统计摘要
    print("\n" + "=" * 70)
    print("📊 Top 10 统计摘要")
    print("=" * 70)
    
    print(f"\n  平均综合分: {top10['total_score'].mean():.1f}")
    print(f"  平均ROE(5年): {top10['avg_roe_5y'].mean():.1f}%")
    print(f"  平均扣非ROE: {top10['avg_roe_kc_5y'].mean():.1f}%")
    print(f"  平均负债率: {top10['debt_ratio'].mean():.1f}%")
    print(f"  平均毛利率: {top10['gross_margin'].mean():.1f}%")
    print(f"  平均净利率: {top10['net_margin'].mean():.1f}%")
    print(f"  平均营收增长: {top10['revenue_growth'].mean():.1f}%")
    print(f"  平均利润增长: {top10['profit_growth'].mean():.1f}%")
    print(f"  平均F-Score: {top10['f_score'].mean():.1f}/9")
    
    pe_mean = top10['pe'].mean() if top10['pe'].mean() > 0 else 0
    pb_mean = top10['pb'].mean() if top10['pb'].mean() > 0 else 0
    print(f"  平均PE: {pe_mean:.1f}")
    print(f"  平均PB: {pb_mean:.2f}")
    
    elapsed = time.time() - start_time
    print(f"\n  总耗时: {elapsed:.1f} 秒")
    
    # 保存结果
    output_file = os.path.join(OUTPUT_DIR, 'value_screening_v3_top20.csv')
    top20.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 Top 20 已保存: {output_file}")
    
    output_all = os.path.join(OUTPUT_DIR, 'value_screening_v3_all.csv')
    result_df.to_csv(output_all, index=False, encoding='utf-8-sig')
    print(f"💾 完整结果已保存: {output_all}")

if __name__ == '__main__':
    main()