#!/usr/bin/env python3
"""
价值投资筛选器 - 两阶段高效筛选
阶段1: 纯财务数据筛选（向量化，快速）
阶段2: K线数据增强（对通过的候选股）
"""

import pandas as pd
import numpy as np
import os
import glob
from typing import Dict, List, Optional
import time

# Paths
FINANCIAL_DATA = '/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv'
KLINE_DIR = '/home/liujerry/金融数据/stocks/'
OUTPUT_DIR = '/home/liujerry/金融数据/screening_results/'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def stage1_financial_screen(financial_df: pd.DataFrame) -> pd.DataFrame:
    """阶段1: 纯财务数据筛选 - 向量化操作，极快"""
    print("\n" + "=" * 70)
    print("📊 阶段1: 财务数据筛选 (向量化处理)")
    print("=" * 70)
    
    # 只取年报数据
    annual_df = financial_df[financial_df['REPORT_TYPE'] == '年报'].copy()
    annual_df['YEAR'] = pd.to_datetime(annual_df['REPORT_DATE']).dt.year
    
    # 转换数字字段
    num_cols = ['ROEJQ', 'ROEKCJQ', 'ZCFZL', 'XSMLL', 'XSJLL', 'PARENTNETPROFIT', 
                'KCFJCXSYJLR', 'TOTALOPERATEREVE', 'BPS', 'EPSJB', 'NETCASH_OPERATE_PK']
    for col in num_cols:
        if col in annual_df.columns:
            annual_df[col] = pd.to_numeric(annual_df[col], errors='coerce')
    
    print(f"  年报记录: {len(annual_df)}, 股票数: {annual_df['code'].nunique()}")
    
    # ===== 向量化计算每只股票的财务指标 =====
    print("  计算5年平均ROE...")
    
    # 最近5年
    max_year = annual_df['YEAR'].max()
    recent_5 = annual_df[annual_df['YEAR'] >= max_year - 4]
    
    # 按股票分组计算ROE统计
    roe_stats = recent_5.groupby('code')['ROEJQ'].agg(['mean', 'min', 'count']).reset_index()
    roe_stats.columns = ['code', 'avg_roe_5y', 'min_roe_5y', 'roe_years']
    
    # 扣非ROE
    roe_kc_stats = recent_5.groupby('code')['ROEKCJQ'].agg(['mean']).reset_index()
    roe_kc_stats.columns = ['code', 'avg_roe_kc_5y']
    
    # 最近3年FCF为正的年数
    recent_3 = recent_5[recent_5['YEAR'] >= max_year - 2]
    fcf_positive = recent_3.groupby('code').apply(
        lambda x: (x['NETCASH_OPERATE_PK'] > 0).sum()
    ).reset_index()
    fcf_positive.columns = ['code', 'fcf_positive_years']
    
    # 取最新年报数据
    latest_reports = annual_df.loc[annual_df.groupby('code')['YEAR'].idxmax()]
    latest_cols = ['code', 'SECURITY_NAME_ABBR', 'YEAR', 'ROEJQ', 'ZCFZL', 'XSMLL', 
                   'XSJLL', 'PARENTNETPROFIT', 'KCFJCXSYJLR', 'BPS', 'EPSJB', 'NETCASH_OPERATE_PK',
                   'TOTAL_EQUITY_PK', 'TOTALOPERATEREVE']
    available_cols = [c for c in latest_cols if c in latest_reports.columns]
    latest_df = latest_reports[available_cols].copy()
    latest_df.columns = ['code', 'name', 'latest_year', 'roe_latest', 'debt_ratio', 
                         'gross_margin', 'net_margin', 'net_profit', 'kfc_net_profit',
                         'bps', 'eps', 'operating_cf', 'total_equity', 'total_revenue']
    
    # 合并所有统计
    merged = latest_df.merge(roe_stats, on='code', how='left')
    merged = merged.merge(roe_kc_stats, on='code', how='left')
    merged = merged.merge(fcf_positive, on='code', how='left')
    
    merged['fcf_positive_years'] = merged['fcf_positive_years'].fillna(0)
    
    # ===== 财务条件筛选 =====
    print("  应用财务筛选条件...")
    
    # 条件掩码
    mask = (
        (merged['avg_roe_5y'] >= 12.0) &                    # 5年平均ROE >= 12%
        (merged['min_roe_5y'] >= 8.0) &                     # 每年ROE >= 8%
        (merged['debt_ratio'] <= 60) &                       # 负债率 <= 60%
        (merged['net_profit'] >= 1e8) &                       # 净利润 >= 1亿
        (merged['kfc_net_profit'] > 0) &                     # 扣非净利润 > 0
        (merged['gross_margin'] > 20) &                      # 毛利率 > 20%
        (merged['fcf_positive_years'] >= 3) &                # FCF连续3年为正
        (merged['roe_years'] >= 3)                            # 至少3年ROE数据
    )
    
    candidates = merged[mask].copy()
    
    print(f"  ✅ 阶段1通过: {len(candidates)} 只 (从 {len(merged)} 只中)")
    print(f"\n  各条件过滤分布:")
    print(f"    ROE均值>=12%:  {(merged['avg_roe_5y'] >= 12.0).sum()}")
    print(f"    每年ROE>=8%:   {(merged['min_roe_5y'] >= 8.0).sum()}")
    print(f"    负债率<=60%:   {(merged['debt_ratio'] <= 60).sum()}")
    print(f"    净利润>=1亿:   {(merged['net_profit'] >= 1e8).sum()}")
    print(f"    扣非净利>0:    {(merged['kfc_net_profit'] > 0).sum()}")
    print(f"    毛利率>20%:    {(merged['gross_margin'] > 20).sum()}")
    print(f"    FCF正3年+:     {(merged['fcf_positive_years'] >= 3).sum()}")
    
    return candidates

def stage2_kline_enhance(candidates: pd.DataFrame) -> pd.DataFrame:
    """阶段2: K线数据增强 - 只对候选股"""
    print("\n" + "=" * 70)
    print("📊 阶段2: K线数据增强 (仅处理候选股)")
    print("=" * 70)
    
    kline_data = []
    total = len(candidates)
    
    print(f"  需加载K线股票数: {total}")
    
    for i, (_, row) in enumerate(candidates.iterrows()):
        if (i + 1) % 50 == 0:
            print(f"  已处理 {i+1}/{total}...")
        
        code = str(int(row['code'])).zfill(6)
        kline_path = os.path.join(KLINE_DIR, f'{code}.csv')
        
        kline_info = {
            'code': code,
            'price': 0, 'pe': 0, 'pb': 0,
            'momentum_6m': 0, 'momentum_1y': 0,
            'volatility': 0.5
        }
        
        if os.path.exists(kline_path):
            try:
                df = pd.read_csv(kline_path)
                if len(df) >= 60:
                    current_price = df.iloc[-1]['close']
                    kline_info['price'] = current_price
                    
                    # PE, PB
                    eps = row['eps'] if row['eps'] > 0 else 0
                    bps = row['bps'] if row['bps'] > 0 else 0
                    kline_info['pe'] = current_price / eps if eps > 0 else 0
                    kline_info['pb'] = current_price / bps if bps > 0 else 0
                    
                    # 6个月动量 (~126交易日)
                    if len(df) >= 126:
                        price_6m = df.iloc[-126]['close']
                        kline_info['momentum_6m'] = (current_price / price_6m - 1) * 100
                    else:
                        kline_info['momentum_6m'] = 0
                    
                    # 1年动量 (~252交易日)
                    if len(df) >= 252:
                        price_1y = df.iloc[-252]['close']
                        kline_info['momentum_1y'] = (current_price / price_1y - 1) * 100
                    elif len(df) >= 126:
                        price_1y = df.iloc[0]['close']
                        kline_info['momentum_1y'] = (current_price / price_1y - 1) * 100
                    else:
                        kline_info['momentum_1y'] = 0
                    
                    # 波动率
                    if len(df) >= 252:
                        returns = df['close'].pct_change().dropna()[-252:]
                        kline_info['volatility'] = returns.std() * np.sqrt(252)
                    elif len(df) >= 60:
                        returns = df['close'].pct_change().dropna()
                        kline_info['volatility'] = returns.std() * np.sqrt(252) if len(returns) > 20 else 0.5
                    
            except Exception as e:
                pass
        
        kline_data.append(kline_info)
    
    kline_df = pd.DataFrame(kline_data)
    
    # 合并
    result = candidates.copy()
    result['code'] = result['code'].apply(lambda x: str(int(x)).zfill(6))
    result = result.merge(kline_df, on='code', how='left')
    
    return result

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """计算综合评分"""
    
    scores = []
    
    for _, row in df.iterrows():
        # === ROE得分 (最高25分) ===
        avg_roe = row['avg_roe_5y'] if row['avg_roe_5y'] > 0 else 0
        if avg_roe >= 25:
            roe_score = 25
        elif avg_roe >= 20:
            roe_score = 22
        elif avg_roe >= 15:
            roe_score = 18
        elif avg_roe >= 12:
            roe_score = 14
        else:
            roe_score = 10
        
        # ROE稳定性加分 (最低ROE不低于15%额外加分)
        if row['min_roe_5y'] >= 15:
            roe_score += 3
        elif row['min_roe_5y'] >= 12:
            roe_score += 2
        elif row['min_roe_5y'] >= 10:
            roe_score += 1
        
        roe_score = min(30, roe_score)
        
        # === 盈利能力得分 (最高20分) ===
        net_margin = row['net_margin'] if row['net_margin'] > 0 else 0
        gross_margin = row['gross_margin'] if row['gross_margin'] > 0 else 0
        
        profit_score = 0
        if net_margin >= 30:
            profit_score += 10
        elif net_margin >= 20:
            profit_score += 8
        elif net_margin >= 10:
            profit_score += 5
        
        if gross_margin >= 50:
            profit_score += 10
        elif gross_margin >= 30:
            profit_score += 7
        elif gross_margin >= 20:
            profit_score += 4
        
        profit_score = min(20, profit_score)
        
        # === 财务健康得分 (最高20分) ===
        debt = row['debt_ratio'] if row['debt_ratio'] > 0 else 100
        if debt <= 20:
            health_score = 20
        elif debt <= 40:
            health_score = 16
        elif debt <= 60:
            health_score = 12
        else:
            health_score = 5
        
        # === 估值得分 (最高20分) ===
        pe = row['pe'] if row['pe'] > 0 else 100
        pb = row['pb'] if row['pb'] > 0 else 100
        
        val_score = 0
        
        # PE估值 (PE越低越好，但也要考虑业绩增长)
        if 0 < pe <= 15:
            val_score += 12
        elif 15 < pe <= 25:
            val_score += 9
        elif 25 < pe <= 35:
            val_score += 6
        elif 35 < pe <= 50:
            val_score += 3
        else:
            val_score += 0
        
        # PB估值
        if 0 < pb <= 2:
            val_score += 8
        elif 2 < pb <= 4:
            val_score += 6
        elif 4 < pb <= 6:
            val_score += 3
        else:
            val_score += 0
        
        val_score = min(20, val_score)
        
        # === 动量得分 (最高10分) ===
        mom_6m = row['momentum_6m'] if row['momentum_6m'] else 0
        
        # 最佳动量区间: -10% 到 +20%
        if -10 <= mom_6m <= 0:
            mom_score = 10
        elif 0 < mom_6m <= 10:
            mom_score = 9
        elif 10 < mom_6m <= 20:
            mom_score = 7
        elif -20 <= mom_6m < -10:
            mom_score = 7
        else:
            mom_score = 4
        
        mom_score = min(10, mom_score)
        
        # === 安全边际得分 (最高10分) ===
        # 基于PE倒数(盈利收益率) vs 无风险利率(3%)
        if pe > 0:
            earnings_yield = (1 / pe) * 100
            margin = earnings_yield - 3  # 相对无风险利率的超额收益
        else:
            margin = -5
        
        if margin >= 5:
            safety_score = 10
        elif margin >= 3:
            safety_score = 8
        elif margin >= 1:
            safety_score = 6
        elif margin >= -1:
            safety_score = 4
        else:
            safety_score = 2
        
        safety_score = min(10, safety_score)
        
        # === 扣非净利润质量加分 (最高5分) ===
        quality_score = 0
        kfc = row['kfc_net_profit'] if row['kfc_net_profit'] > 0 else 0
        np = row['net_profit'] if row['net_profit'] > 0 else 0
        if np > 0 and kfc > 0:
            ratio = kfc / np
            if ratio >= 0.8:
                quality_score = 5
            elif ratio >= 0.6:
                quality_score = 4
            elif ratio >= 0.4:
                quality_score = 3
        
        total_score = roe_score + profit_score + health_score + val_score + mom_score + safety_score + quality_score
        
        scores.append({
            'code': row['code'],
            'name': row['name'],
            'price': row['price'],
            'pe': round(row['pe'], 1) if row['pe'] > 0 else 0,
            'pb': round(row['pb'], 2) if row['pb'] > 0 else 0,
            'avg_roe_5y': round(row['avg_roe_5y'], 1) if row['avg_roe_5y'] > 0 else 0,
            'min_roe_5y': round(row['min_roe_5y'], 1) if row['min_roe_5y'] > 0 else 0,
            'debt_ratio': round(row['debt_ratio'], 1) if row['debt_ratio'] > 0 else 0,
            'gross_margin': round(row['gross_margin'], 1) if row['gross_margin'] > 0 else 0,
            'net_margin': round(row['net_margin'], 1) if row['net_margin'] > 0 else 0,
            'net_profit_y': round(row['net_profit'] / 1e8, 2) if row['net_profit'] > 0 else 0,
            'fcf_positive_years': int(row['fcf_positive_years']),
            'momentum_6m': round(mom_6m, 1),
            'volatility': round(row['volatility'] * 100, 1) if row['volatility'] > 0 else 0,
            # 得分
            'roe_score': roe_score,
            'profit_score': profit_score,
            'health_score': health_score,
            'val_score': val_score,
            'mom_score': mom_score,
            'safety_score': safety_score,
            'quality_score': quality_score,
            'total_score': round(total_score, 1),
        })
    
    return pd.DataFrame(scores)

def main():
    start_time = time.time()
    
    print("=" * 70)
    print("📊 A股价值投资筛选器 - 两阶段高效筛选")
    print("=" * 70)
    
    # 加载财务数据
    print("\n📂 加载财务数据...")
    financial_df = pd.read_csv(FINANCIAL_DATA, low_memory=False)
    print(f"  总记录: {len(financial_df)}")
    
    # 阶段1: 财务筛选
    candidates = stage1_financial_screen(financial_df)
    
    if len(candidates) == 0:
        print("没有通过阶段1筛选的股票")
        return
    
    # 阶段2: K线增强
    enhanced = stage2_kline_enhance(candidates)
    
    # 计算评分
    print("\n  计算综合评分...")
    scored = calculate_scores(enhanced)
    
    # 排序
    scored = scored.sort_values('total_score', ascending=False)
    
    # 输出Top 10
    print("\n" + "=" * 70)
    print("🏆 价值投资 Top 10 (两阶段筛选)")
    print("=" * 70)
    
    top10 = scored.head(10)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'价格':<7} {'PE':<5} {'PB':<5} {'ROE均':<6} {'ROE低':<6} {'负债率':<6} {'毛利率':<6} {'净利率':<6} {'6月动量':<7} {'综合分':<6}")
    print("-" * 90)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"{rank:<4} {row['code']:<8} {row['name']:<10} {row['price']:<7.2f} {row['pe']:<5.1f} {row['pb']:<5.2f} {row['avg_roe_5y']:<5.1f}% {row['min_roe_5y']:<5.1f}% {row['debt_ratio']:<5.1f}% {row['gross_margin']:<5.1f}% {row['net_margin']:<5.1f}% {row['momentum_6m']:<6.1f}% {row['total_score']:<5.1f}")
    
    # 细分得分
    print("\n" + "=" * 70)
    print("📋 Top 10 细分得分")
    print("=" * 70)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'ROE':<6} {'盈利':<6} {'健康':<6} {'估值':<6} {'动量':<6} {'安全':<6} {'质量':<6} {'总分':<6}")
    print("-" * 75)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"{rank:<4} {row['code']:<8} {row['name']:<10} {row['roe_score']:<5.1f} {row['profit_score']:<5.1f} {row['health_score']:<5.1f} {row['val_score']:<5.1f} {row['mom_score']:<5.1f} {row['safety_score']:<5.1f} {row['quality_score']:<5.1f} {row['total_score']:<5.1f}")
    
    # 统计摘要
    print("\n" + "=" * 70)
    print("📊 Top 10 统计摘要")
    print("=" * 70)
    
    print(f"\n  平均ROE(5年): {top10['avg_roe_5y'].mean():.1f}%")
    print(f"  平均最低ROE: {top10['min_roe_5y'].mean():.1f}%")
    print(f"  平均负债率: {top10['debt_ratio'].mean():.1f}%")
    print(f"  平均毛利率: {top10['gross_margin'].mean():.1f}%")
    print(f"  平均净利率: {top10['net_margin'].mean():.1f}%")
    print(f"  平均PE: {top10['pe'].mean():.1f}")
    print(f"  平均PB: {top10['pb'].mean():.2f}")
    print(f"  平均6月动量: {top10['momentum_6m'].mean():.1f}%")
    print(f"  平均安全边际得分: {top10['safety_score'].mean():.1f}/10")
    
    elapsed = time.time() - start_time
    print(f"\n  总耗时: {elapsed:.1f} 秒")
    
    # 保存完整候选结果
    output_all = os.path.join(OUTPUT_DIR, 'value_screening_all_candidates.csv')
    scored.to_csv(output_all, index=False, encoding='utf-8-sig')
    print(f"\n💾 完整候选结果已保存: {output_all}")
    
    # 保存Top 10
    output_top10 = os.path.join(OUTPUT_DIR, 'value_screening_top10_v2.csv')
    top10.to_csv(output_top10, index=False, encoding='utf-8-sig')
    print(f"💾 Top 10 已保存: {output_top10}")

if __name__ == '__main__':
    main()