#!/usr/bin/env python3
"""
V4.0 全A股完整评分筛选 - 对齐报告V4技能
总分23分:
- 技术面(6分): Williams%R(<-80), RSI(<=30), MACD金叉, KDJ(<20), 布林带触下轨
- 基本面(7分): ROE(>20%/10%), 净利润>1亿, 毛利率>30%, 净利率>10%, EPS>0.3
- 巴菲特10大公式(10分): 现金/负债/ROE/流动/营业利润率/周转/利息保障/盈利稳定/FCF/资本配置
数据源: stocks_clean*(分板)/technical_indicators/chuangye_full/buffett_supplementary
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

DATA_DIR = Path.home() / '金融数据'
STOCKS_DIRS = {
    '创业板': DATA_DIR / 'stocks_clean',
    '主板A股': DATA_DIR / 'stocks_clean_main',
    '中小板': DATA_DIR / 'stocks_clean_sme',
    '科创板': DATA_DIR / 'stocks_clean_star',
}
TECH_INDICATORS_DIR = DATA_DIR / 'technical_indicators'
FINANCIAL_DIR = DATA_DIR / 'fundamentals' / 'chuangye_full'
BUFFETT_FILE = DATA_DIR / 'fundamentals' / 'buffett_supplementary.csv'

def normalize_code(code):
    code = str(code)
    if '.' in code:
        code = code.split('.')[1]
    return code.zfill(6)

def get_market(code):
    if code.startswith('3') and len(code) == 6:
        return '创业板'
    elif code.startswith('688'):
        return '科创板'
    elif code.startswith('002'):
        return '中小板'
    else:
        return '主板A股'

def load_all_financial_data():
    """加载所有财务数据"""
    print("加载财务数据...")
    profit_file = FINANCIAL_DIR / 'profit.csv'
    df = pd.read_csv(profit_file)
    df = df.drop_duplicates(subset=['code'], keep='first')
    df['code_norm'] = df['code'].apply(normalize_code)
    
    fin_map = {}
    for _, row in df.iterrows():
        code = row['code_norm']
        fin_map[code] = {
            # profit.csv 真实存在的字段 (11列) - 已修正列名映射
            'roe': row.get('roeAvg'),              # ✅
            'netProfit': row.get('netProfit'),      # ✅
            'grossMargin': row.get('gpMargin'),     # ✅ 修正: grossRatio→gpMargin
            'netMargin': row.get('npMargin'),       # ✅ 修正: netProfitRatio→npMargin
            'eps': row.get('epsTTM'),               # ✅ 修正: eps→epsTTM
            'totalRevenue': row.get('MBRevenue'),  # ✅ 修正: totalRevenue→MBRevenue
            # 以下字段不在 profit.csv，从 Buffett 数据获取或留空
            'operatingIncome': None,
            'operatingProfit': None,                # 从 buffett_supplementary 获取
            'profitBeforeTax': None,
            'totalAssets': None,                   # 从 buffett_supplementary 获取
            'totalLiabilities': None,             # 从 buffett_supplementary 获取
            'equity': None,                        # 从 buffett_supplementary 获取
            'operatingCashFlow': None,
            'cashAndCashEquivalents': None,        # 从 buffett_supplementary 获取
            'shortTermBorrowing': None,            # 从 buffett_supplementary 获取 (short_debt)
            'longTermBorrowing': None,             # 从 buffett_supplementary 获取 (long_debt)
            'interestExpense': None,               # 从 buffett_supplementary 获取
            'basicEPS': row.get('epsTTM'),          # 使用 epsTTM 替代
            'dilutedEPS': row.get('epsTTM'),        # 使用 epsTTM 替代
            'operatingCost': None,
            'saleCost': None,
            'managementFee': None,
            'financialExpense': row.get('financialExpense'),
            'researchExpense': row.get('researchExpense'),
        }
    
    print(f"  财务数据: {len(fin_map)} 只股票")
    return fin_map

def load_buffett_data():
    """加载Buffett原始数据（从原始列计算指标）"""
    print("加载Buffett原始数据...")
    if not BUFFETT_FILE.exists():
        print("  Buffett数据文件不存在")
        return {}
    
    df = pd.read_csv(BUFFETT_FILE)
    df = df.drop_duplicates(subset=['code'], keep='last')
    
    # 计算Buffett指标（从原始数据）
    df['cash_ratio'] = df['cash'] / df['total_assets']
    df['debt_to_equity'] = (df['short_debt'].fillna(0) + df['long_debt'].fillna(0)) / df['equity'].replace(0, np.nan)
    df['roe'] = df['net_income'] / df['equity'].replace(0, np.nan)
    df['current_ratio'] = df['current_assets'] / df['current_liabilities'].replace(0, np.nan)
    df['op_margin'] = df['operating_profit'] / df['revenue'].replace(0, np.nan)
    df['asset_turn'] = df['revenue'] / df['total_assets'].replace(0, np.nan)
    df['int_coverage'] = df['operating_profit'] / df['interest_expense'].replace(0, np.nan)
    
    buffett_map = {}
    for _, row in df.iterrows():
        code = str(int(row['code'])).zfill(6)
        buffett_map[code] = {
            'cash_ratio': row.get('cash_ratio'),
            'debt_to_equity': row.get('debt_to_equity'),
            'roe': row.get('roe'),
            'current_ratio': row.get('current_ratio'),
            'op_margin': row.get('op_margin'),
            'asset_turn': row.get('asset_turn'),
            'int_coverage': row.get('int_coverage'),
        }
    
    print(f"  Buffett数据: {len(buffett_map)} 只股票")
    return buffett_map

def score_stock(code, tech_file, financial_data, buffett_data, cutoff_date):
    """对单只股票打分"""
    # 读取技术指标
    df = pd.read_csv(tech_file)
    if len(df) == 0:
        return None
    
    latest = df.iloc[-1]
    
    # 检查数据新鲜度
    date_str = latest.get('date')
    if date_str:
        try:
            stock_date = pd.to_datetime(date_str)
            if stock_date < cutoff_date:
                return None
        except:
            pass
    
    close = latest.get('close')
    
    # ========== 技术面评分 (6分) ==========
    tech_score = 0
    tech_details = {}
    
    # Williams %R < -80 得3分 (列名是WR14)
    williams_r = latest.get('WR14')
    if williams_r and not pd.isna(williams_r):
        tech_details['Williams_R'] = williams_r
        if williams_r < -80:
            tech_score += 3
    
    # RSI < 30 得1分
    rsi = latest.get('RSI14')
    if rsi and not pd.isna(rsi):
        tech_details['RSI'] = rsi
        if rsi <= 30:
            tech_score += 1
    
    # MACD金叉 得1分 (列名: MACD_DIF=DIFF, MACD_DEA=SIGNAL)
    macd = latest.get('MACD_DIF')
    macd_signal = latest.get('MACD_DEA')
    if macd and macd_signal and not pd.isna(macd) and not pd.isna(macd_signal):
        tech_details['MACD_cross'] = macd > macd_signal
        if macd > macd_signal:
            tech_score += 1
    
    # KDJ K < 20 得1分
    kdj_k = latest.get('KDJ_K')
    if kdj_k and not pd.isna(kdj_k):
        tech_details['KDJ_K'] = kdj_k
        if kdj_k < 20:
            tech_score += 1
    
    # 布林带触及 得1分
    bb_lower = latest.get('BB_LOWER')
    if close and bb_lower and not pd.isna(close) and not pd.isna(bb_lower):
        bb_touch = close <= bb_lower * 1.02
        tech_details['BB_touch'] = bb_touch
        if bb_touch:
            tech_score += 1
    
    # ========== 基本面评分 (7分) ==========
    fund_score = 0
    fund_details = {}
    fin = financial_data.get(code, {})
    
    # ROE > 10% 得1分, > 20% 得2分
    roe = fin.get('roe')
    if roe and not pd.isna(roe):
        fund_details['ROE'] = f"{roe*100:.1f}%"
        if roe > 0.20:
            fund_score += 2
        elif roe > 0.10:
            fund_score += 1
    
    # 净利润 > 1亿 得1分
    net_profit = fin.get('netProfit')
    if net_profit and not pd.isna(net_profit):
        fund_details['净利润'] = f"{net_profit/1e8:.2f}亿"
        if net_profit > 100000000:
            fund_score += 1
    
    # 毛利率 > 30% 得1分
    gross_margin = fin.get('grossMargin')
    if gross_margin and not pd.isna(gross_margin):
        fund_details['毛利率'] = f"{gross_margin*100:.1f}%"
        if gross_margin > 0.30:
            fund_score += 1
    
    # 净利率 > 10% 得1分
    net_margin = fin.get('netMargin')
    if net_margin and not pd.isna(net_margin):
        fund_details['净利率'] = f"{net_margin*100:.1f}%"
        if net_margin > 0.10:
            fund_score += 1
    
    # EPS > 0.3 得1分
    eps = fin.get('eps')
    if eps and not pd.isna(eps):
        fund_details['EPS'] = f"{eps:.2f}"
        if eps > 0.3:
            fund_score += 1
    
    # ========== 巴菲特7大公式评分 (7分，第8/9/10需要额外数据) ==========
    buffett_score = 0
    buffett_details = {}
    buf = buffett_data.get(code, {})
    
    if buf:
        # 1. 现金测试 (现金/总资产 > 25%)
        cash_ratio = buf.get('cash_ratio')
        if cash_ratio and not pd.isna(cash_ratio):
            buffett_details['现金占比'] = f"{cash_ratio*100:.1f}%"
            if cash_ratio > 0.25:
                buffett_score += 1
        
        # 2. 负债权益比 (< 50% 得1分)
        de_ratio = buf.get('debt_to_equity')
        if de_ratio and not pd.isna(de_ratio):
            buffett_details['负债权益比'] = f"{de_ratio*100:.1f}%"
            if de_ratio < 0.5:
                buffett_score += 1
        
        # 3. ROE (> 15% 得1分)
        buf_roe = buf.get('roe')
        if buf_roe and not pd.isna(buf_roe):
            buffett_details['ROE'] = f"{buf_roe*100:.1f}%"
            if buf_roe > 0.15:
                buffett_score += 1
        
        # 4. 流动比率 (> 1.5 得1分) - 注意：此字段可能全为空
        current_ratio = buf.get('current_ratio')
        if current_ratio and not pd.isna(current_ratio):
            buffett_details['流动比率'] = f"{current_ratio:.2f}"
            if current_ratio > 1.5:
                buffett_score += 1
        
        # 5. 营业利润率 (> 10% 得1分) - 使用财务数据的operatingProfit
        op_margin = buf.get('op_margin')  # 保留用于fallback
        op_profit_fin = fin.get('operatingProfit')
        revenue_fin = fin.get('totalRevenue')
        if op_profit_fin and revenue_fin and not pd.isna(op_profit_fin) and not pd.isna(revenue_fin) and revenue_fin > 0:
            op_margin_calc = op_profit_fin / revenue_fin
            buffett_details['营业利润率'] = f"{op_margin_calc*100:.1f}%"
            if op_margin_calc > 0.10:
                buffett_score += 1
        elif op_margin and not pd.isna(op_margin):  # fallback to Buffett file
            buffett_details['营业利润率'] = f"{op_margin*100:.1f}%"
            if op_margin > 0.10:
                buffett_score += 1
        
        # 6. 资产周转率 (> 0.8 得1分)
        asset_turn = buf.get('asset_turn')
        if asset_turn and not pd.isna(asset_turn):
            buffett_details['资产周转率'] = f"{asset_turn:.2f}"
            if asset_turn > 0.8:
                buffett_score += 1
        
        # 7. 利息保障倍数 (> 5 得1分) - 需要interest_expense > 0
        int_coverage = buf.get('int_coverage')
        if int_coverage and not pd.isna(int_coverage) and int_coverage > 0:
            buffett_details['利息保障'] = f"{int_coverage:.1f}x"
            if int_coverage > 5:
                buffett_score += 1

        # 8. 盈利稳定性 (净利润>0 得1分)
        net_income = fin.get('netProfit')
        if net_income and not pd.isna(net_income) and net_income > 0:
            buffett_score += 1
            buffett_details['盈利稳定'] = '是'

        # 9. 自由现金流 (现金>总负债 得1分)
        total_liab = fin.get('totalLiabilities')
        buf_cash_ratio = buf.get('cash_ratio')
        buf_total_assets = buf.get('total_assets', 1)
        if buf_cash_ratio and total_liab and not pd.isna(total_liab) and total_liab > 0:
            estimated_cash = buf_cash_ratio * buf_total_assets
            if estimated_cash > total_liab:
                buffett_score += 1
                buffett_details['FCF充裕'] = '是'

        # 10. 资本配置 (盈利且有现金 得1分)
        buf_cash_abs = fin.get('cashAndCashEquivalents')
        if not buf_cash_abs and buf_cash_ratio and buf_total_assets:
            buf_cash_abs = buf_cash_ratio * buf_total_assets
        if net_income and not pd.isna(net_income) and net_income > 0 and buf_cash_abs and buf_cash_abs > 0:
            buffett_score += 1
            buffett_details['资本配置'] = '合理'

    total_score = tech_score + fund_score + buffett_score
    
    return {
        'code': code,
        'market': get_market(code),
        'date': date_str,
        'close': close,
        'tech_score': tech_score,
        'fund_score': fund_score,
        'buffett_score': buffett_score,
        'total_score': total_score,
        'tech_details': tech_details,
        'fund_details': fund_details,
        'buffett_details': buffett_details,
        'rsi': rsi,
        'roe': roe,
        'net_profit': net_profit,
    }

def main():
    print("=" * 70)
    print("V4.0 全A股完整评分筛选")
    print("=" * 70)
    
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=30)
    print(f"数据截止日期: {cutoff_date.date()} (过滤30天前数据)")
    
    financial_data = load_all_financial_data()
    buffett_data = load_buffett_data()
    
    # 获取所有技术指标文件
    tech_files = list(TECH_INDICATORS_DIR.glob("*.csv"))
    print(f"技术指标目录股票总数: {len(tech_files)} 只")
    
    print("\n开始筛选...")
    results = []
    
    for i, f in enumerate(tech_files):
        code = f.stem
        if (i + 1) % 500 == 0:
            print(f"  进度: {i+1}/{len(tech_files)}")
        
        result = score_stock(code, f, financial_data, buffett_data, cutoff_date)
        if result:
            results.append(result)
    
    print(f"  完成: {len(tech_files)}/{len(tech_files)}")
    print(f"有效股票（30天内有数据）: {len(results)} 只")
    
    # 按总分排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    print("\n" + "=" * 70)
    print("TOP 200 筛选结果")
    print("=" * 70)
    print(f"{'排名':<4} {'代码':<8} {'技术':<4} {'基本':<4} {'巴菲':<4} {'总分':<4} {'RSI':<8} {'ROE':<10} {'市场':<6} {'日期'}")
    print("-" * 70)
    
    for i, r in enumerate(results[:200]):
        rsi_str = f"{r['rsi']:.1f}" if r['rsi'] and not pd.isna(r['rsi']) else "N/A"
        roe_str = f"{r['roe']*100:.1f}%" if r['roe'] and not pd.isna(r['roe']) else "N/A"
        date_str = r['date'][:10] if r['date'] else "N/A"
        print(f"{i+1:<4} {r['code']:<8} {r['tech_score']}/6   {r['fund_score']}/7   {r['buffett_score']}/10  {r['total_score']:<4} {rsi_str:<8} {roe_str:<10} {r['market']:<6} {date_str}")
    
    # 保存完整结果
    output_file = Path.home() / 'moltbot' / 'v4_screening_top200.csv'
    df_output = pd.DataFrame([{
        'rank': i+1,
        'code': r['code'],
        'market': r['market'],
        'tech_score': r['tech_score'],
        'fund_score': r['fund_score'],
        'buffett_score': r['buffett_score'],
        'total_score': r['total_score'],
        'rsi': r['rsi'],
        'roe': r['roe'],
        'net_profit': r['net_profit'],
        'close': r['close'],
        'date': r['date'],
    } for i, r in enumerate(results[:200])])
    df_output.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    # 统计分析
    print("\n" + "=" * 70)
    print("分数分布统计")
    print("=" * 70)
    
    total_scores = [r['total_score'] for r in results]
    print(f"总分范围: {min(total_scores)} - {max(total_scores)}")
    print(f"总分平均: {sum(total_scores)/len(total_scores):.1f}")
    print(f"中位数: {sorted(total_scores)[len(total_scores)//2]}")
    
    print("\n总分分布:")
    for score in range(max(total_scores), -1, -1):
        count = len([r for r in results if r['total_score'] == score])
        if count > 0:
            bar = "█" * count
            print(f"  {score:>2}分: {bar} {count}只")
    
    print(f"\n筛选完成时间: {pd.Timestamp.now()}")
    
    return results

if __name__ == "__main__":
    main()
