#!/usr/bin/env python3
"""
价值投资筛选器 - 基于本地数据
使用 financial_main_em.csv 和本地K线数据进行综合评分
"""

import pandas as pd
import numpy as np
import os
import glob
from typing import Dict, List, Tuple, Optional

# Paths
FINANCIAL_DATA = '/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv'
KLINE_DIR = '/home/liujerry/金融数据/stocks/'
OUTPUT_DIR = '/home/liujerry/金融数据/screening_results/'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_financial_data() -> pd.DataFrame:
    """加载财务数据，只取年报"""
    print("📂 加载财务数据...")
    df = pd.read_csv(FINANCIAL_DATA, low_memory=False)
    
    # 只取年报数据 (避免重复)
    annual_df = df[df['REPORT_TYPE'] == '年报'].copy()
    
    # 转换年份
    annual_df['YEAR'] = pd.to_datetime(annual_df['REPORT_DATE']).dt.year
    
    # 转换数字字段
    num_cols = ['ROEJQ', 'ROEKCJQ', 'ZCFZL', 'XSMLL', 'XSJLL', 'PARENTNETPROFIT', 
                'KCFJCXSYJLR', 'TOTALOPERATEREVE', 'BPS', 'EPSJB', 'NETCASH_OPERATE_PK',
                'XSMGXJLL', 'YYZSRGDHBZC', 'NETPROFITRPHBZC', 'KFJLRGDHBZC',
                'EQUITY_YOYRATIO_PK', 'TOTAL_EQUITY_PK']
    for col in num_cols:
        if col in annual_df.columns:
            annual_df[col] = pd.to_numeric(annual_df[col], errors='coerce')
    
    print(f"  年报记录数: {len(annual_df)}, 覆盖股票: {annual_df['code'].nunique()}")
    return annual_df

def load_kline_data(code: str) -> Optional[Dict]:
    """加载K线数据"""
    kline_path = os.path.join(KLINE_DIR, f'{code}.csv')
    if not os.path.exists(kline_path):
        return None
    
    try:
        df = pd.read_csv(kline_path)
        if len(df) < 60:
            return None
        
        # 最新价格
        current_price = df.iloc[-1]['close']
        
        # 6个月前价格 (约126个交易日)
        if len(df) >= 126:
            price_6m = df.iloc[-126]['close']
        else:
            price_6m = df.iloc[0]['close']
        
        # 年化波动率
        if len(df) >= 252:
            returns = df['close'].pct_change().dropna()[-252:]
            volatility = returns.std() * np.sqrt(252)
        else:
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) if len(returns) > 20 else 0.5
        
        # 市值 (使用最新K线数据估算)
        date_str = df.iloc[-1]['date']
        
        return {
            'current_price': current_price,
            'price_6m': price_6m,
            'momentum_6m': (current_price / price_6m - 1) * 100 if price_6m > 0 else 0,
            'volatility': volatility,
        }
    except Exception as e:
        return None

def calculate_roe_stability(group: pd.DataFrame) -> Dict:
    """计算ROE稳定性"""
    roe_col = 'ROEJQ'
    years = group.sort_values('YEAR', ascending=False)
    
    # 取最近5年
    recent_5 = years[years['YEAR'] >= years['YEAR'].max() - 4]
    
    if len(recent_5) == 0:
        return {'avg_roe': 0, 'min_roe': 0, 'roe_count': 0, 'roe_years': 0}
    
    valid_roe = recent_5[roe_col].dropna()
    
    return {
        'avg_roe': valid_roe.mean() if len(valid_roe) > 0 else 0,
        'min_roe': valid_roe.min() if len(valid_roe) > 0 else 0,
        'roe_count': len(valid_roe),
        'roe_years': len(recent_5),
        'roe_trend': 'rising' if len(valid_roe) >= 2 and valid_roe.values[0] > valid_roe.values[-1] else 'flat'
    }

def calculate_fcf_stability(group: pd.DataFrame) -> Dict:
    """计算自由现金流稳定性"""
    fcf_col = 'NETCASH_OPERATE_PK'
    years = group.sort_values('YEAR', ascending=False)
    recent_5 = years[years['YEAR'] >= years['YEAR'].max() - 4]
    
    if len(recent_5) == 0:
        return {'fcf_positive_years': 0, 'total_fcf': 0}
    
    valid_fcf = recent_5[fcf_col].dropna()
    positive_years = (valid_fcf > 0).sum()
    
    return {
        'fcf_positive_years': positive_years,
        'total_fcf': valid_fcf.sum(),
    }

def screen_stocks(financial_df: pd.DataFrame, min_roe: float = 12.0, 
                  max_debt_ratio: float = 0.6, min_net_profit: float = 1e8) -> pd.DataFrame:
    """筛选股票"""
    results = []
    
    print("🔍 开始筛选股票...")
    stock_codes = financial_df['code'].unique()
    total = len(stock_codes)
    
    screened_count = 0
    for i, code in enumerate(stock_codes):
        if (i + 1) % 500 == 0:
            print(f"  已处理 {i+1}/{total}...")
        
        stock_data = financial_df[financial_df['code'] == code]
        
        # 基本信息
        latest = stock_data.sort_values('YEAR', ascending=False).iloc[0]
        name = str(latest.get('SECURITY_NAME_ABBR', ''))
        code_full = str(int(code)).zfill(6)
        
        if name == '' or name == 'nan':
            name = code_full
        
        # 1. ROE稳定性分析
        roe_info = calculate_roe_stability(stock_data)
        avg_roe = roe_info['avg_roe']
        min_roe_val = roe_info['min_roe']
        roe_years = roe_info['roe_years']
        
        # 2. 财务健康分析 (最新年报)
        debt_ratio = pd.to_numeric(latest.get('ZCFZL', 0), errors='coerce') or 0
        gross_margin = pd.to_numeric(latest.get('XSMLL', 0), errors='coerce') or 0
        net_margin = pd.to_numeric(latest.get('XSJLL', 0), errors='coerce') or 0
        net_profit = pd.to_numeric(latest.get('PARENTNETPROFIT', 0), errors='coerce') or 0
        fcf = pd.to_numeric(latest.get('NETCASH_OPERATE_PK', 0), errors='coerce') or 0
        
        # 3. 盈利质量 (扣非净利润)
        kfc_net_profit = pd.to_numeric(latest.get('KCFJCXSYJLR', 0), errors='coerce') or 0
        
        # 4. FCF分析
        fcf_info = calculate_fcf_stability(stock_data)
        fcf_positive_years = fcf_info['fcf_positive_years']
        
        # 5. 估值数据
        bps = pd.to_numeric(latest.get('BPS', 0), errors='coerce') or 0
        eps = pd.to_numeric(latest.get('EPSJB', 0), errors='coerce') or 0
        total_equity = pd.to_numeric(latest.get('TOTAL_EQUITY_PK', 0), errors='coerce') or 0
        
        # 6. 加载K线数据
        kline_info = load_kline_data(code_full)
        
        if kline_info:
            current_price = kline_info['current_price']
            momentum_6m = kline_info['momentum_6m']
            volatility = kline_info['volatility']
        else:
            # 跳过没有K线数据的股票
            continue
        
        # 计算PE和PB
        pe = current_price / eps if eps > 0 else 0
        pb = current_price / bps if bps > 0 else 0
        
        # ===== 筛选条件 =====
        # 条件1: 平均ROE >= min_roe%
        if avg_roe < min_roe:
            continue
        
        # 条件2: 每年ROE都不低于10%
        if min_roe_val < 8:
            continue
        
        # 条件3: 负债率 <= max_debt_ratio
        if debt_ratio > max_debt_ratio * 100:  # ZCFZL是百分比
            continue
        
        # 条件4: 净利润 >= min_net_profit
        if net_profit < min_net_profit:
            continue
        
        # 条件5: 扣非净利润为正
        if kfc_net_profit <= 0:
            continue
        
        # 条件6: 毛利率 > 20%
        if gross_margin <= 20:
            continue
        
        # 条件7: FCF连续3年为正
        if fcf_positive_years < 3:
            continue
        
        # ===== 综合评分 =====
        # ROE评分 (最高30分)
        roe_score = min(30, avg_roe * 2)
        
        # 盈利能力 (最高20分)
        profit_score = min(20, net_margin * 2)
        
        # 财务健康 (最高20分)
        health_score = max(0, 20 - debt_ratio * 0.2)
        
        # 估值评分 (最高20分)
        if 0 < pe <= 20:
            val_score = 20
        elif 20 < pe <= 30:
            val_score = 15
        elif 30 < pe <= 50:
            val_score = 10
        else:
            val_score = 5
        
        # 动量评分 (最高10分)
        if -10 < momentum_6m < 20:
            mom_score = 10 - abs(momentum_6m) / 10
        else:
            mom_score = max(0, 5 - abs(momentum_6m - 10) / 10)
        
        total_score = roe_score + profit_score + health_score + val_score + mom_score
        
        # 安全边际估算 (基于PE倒数 vs 无风险利率假设)
        # 假设无风险利率 3%
        earnings_yield = (1 / pe * 100) if pe > 0 else 0
        safety_margin = earnings_yield - 3  # 相对于3%无风险利率
        
        results.append({
            'code': code_full,
            'name': name,
            'price': round(current_price, 2),
            'avg_roe_5y': round(avg_roe, 2),
            'min_roe_5y': round(min_roe_val, 2),
            'roe_years': roe_years,
            'debt_ratio': round(debt_ratio, 2),
            'gross_margin': round(gross_margin, 2),
            'net_margin': round(net_margin, 2),
            'net_profit_y': round(net_profit / 1e8, 2),  # 亿元
            'kfc_net_profit_y': round(kfc_net_profit / 1e8, 2),  # 亿元
            'fcf_positive_years': fcf_positive_years,
            'eps': round(eps, 2),
            'bps': round(bps, 2),
            'pe': round(pe, 1),
            'pb': round(pb, 2),
            'momentum_6m': round(momentum_6m, 1),
            'volatility': round(volatility * 100, 1),
            'safety_margin': round(safety_margin, 1),
            'total_score': round(total_score, 1),
            # 细分得分
            'roe_score': round(roe_score, 1),
            'profit_score': round(profit_score, 1),
            'health_score': round(health_score, 1),
            'val_score': round(val_score, 1),
            'mom_score': round(mom_score, 1),
        })
        
        screened_count += 1
    
    print(f"  ✅ 初筛通过: {screened_count} 只")
    
    result_df = pd.DataFrame(results)
    
    if len(result_df) > 0:
        result_df = result_df.sort_values('total_score', ascending=False)
    
    return result_df

def main():
    print("=" * 70)
    print("📊 A股价值投资筛选器 - 基于本地数据")
    print("=" * 70)
    
    # 加载财务数据
    financial_df = load_financial_data()
    
    # 筛选股票
    # 标准: ROE均值>=12%, 负债率<=60%, 净利润>=1亿, 扣非为正, 毛利率>20%, FCF连续3年正
    result_df = screen_stocks(
        financial_df,
        min_roe=12.0,
        max_debt_ratio=0.6,
        min_net_profit=1e8
    )
    
    # 输出Top 10
    print("\n" + "=" * 70)
    print("🏆 价值投资Top 10 (综合评分)")
    print("=" * 70)
    
    if len(result_df) == 0:
        print("没有符合条件的股票")
        return
    
    top10 = result_df.head(10)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'价格':<8} {'PE':<6} {'PB':<5} {'ROE均':<6} {'ROE低':<6} {'负债率':<7} {'毛利率':<7} {'净利率':<6} {'6月动量':<8} {'安全边际':<8} {'综合分':<6}")
    print("-" * 110)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"{rank:<4} {row['code']:<8} {row['name']:<10} {row['price']:<8.2f} {row['pe']:<6.1f} {row['pb']:<5.2f} {row['avg_roe_5y']:<6.1f}% {row['min_roe_5y']:<6.1f}% {row['debt_ratio']:<6.1f}% {row['gross_margin']:<6.1f}% {row['net_margin']:<5.1f}% {row['momentum_6m']:<7.1f}% {row['safety_margin']:<7.1f}% {row['total_score']:<5.1f}")
    
    # 保存完整结果
    output_file = os.path.join(OUTPUT_DIR, 'value_screening_top10.csv')
    top10.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 完整数据已保存: {output_file}")
    
    # 详细得分分析
    print("\n" + "=" * 70)
    print("📋 Top 10 细分得分分析")
    print("=" * 70)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'ROE得分':<9} {'盈利得分':<9} {'健康得分':<9} {'估值得分':<9} {'动量得分':<9} {'总分':<6}")
    print("-" * 75)
    
    for rank, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"{rank:<4} {row['code']:<8} {row['name']:<10} {row['roe_score']:<8.1f} {row['profit_score']:<8.1f} {row['health_score']:<8.1f} {row['val_score']:<8.1f} {row['mom_score']:<8.1f} {row['total_score']:<5.1f}")
    
    # 统计摘要
    print("\n" + "=" * 70)
    print("📊 筛选统计摘要")
    print("=" * 70)
    
    print(f"\n符合初筛条件股票数: {len(result_df)}")
    print(f"\nTop 10 平均ROE: {top10['avg_roe_5y'].mean():.1f}%")
    print(f"Top 10 平均负债率: {top10['debt_ratio'].mean():.1f}%")
    print(f"Top 10 平均毛利率: {top10['gross_margin'].mean():.1f}%")
    print(f"Top 10 平均净利率: {top10['net_margin'].mean():.1f}%")
    print(f"Top 10 平均PE: {top10['pe'].mean():.1f}")
    print(f"Top 10 平均PB: {top10['pb'].mean():.2f}")
    print(f"Top 10 平均6个月动量: {top10['momentum_6m'].mean():.1f}%")
    print(f"Top 10 平均安全边际: {top10['safety_margin'].mean():.1f}%")

if __name__ == '__main__':
    main()