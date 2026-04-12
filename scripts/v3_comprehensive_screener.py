#!/usr/bin/env python3
"""
V3.0 全面筛选脚本
使用巴菲特10大公式 + 技术面 + 基本面 + DCF四维评分
必须先检查数据质量
"""

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

# ========== 配置 ==========
BUFFETT_FILE = '/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv'
FINANCIAL_FILE = '/home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv'
KLINE_DIR = '/home/liujerry/金融数据/stocks'
TECH_DIR = '/home/liujerry/金融数据/technical_indicators'
OUTPUT_FILE = '/home/liujerry/reports/v3_screening_top200.csv'
LOG_FILE = '/home/liujerry/金融数据/logs/v3_screening.log'

def log(msg):
    """日志记录"""
    timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def check_data_quality():
    """检查数据质量"""
    log("=" * 60)
    log("步骤1: 数据质量检查")
    log("=" * 60)
    
    issues = []
    
    # 1. 检查Buffett数据
    log("检查Buffett数据...")
    buffett = pd.read_csv(BUFFETT_FILE)
    total_buffett = len(buffett)
    
    zero_revenue = len(buffett[buffett['revenue'] == 0])
    zero_income = len(buffett[buffett['net_income'] == 0])
    zero_equity = len(buffett[buffett['equity'] == 0])
    zero_cash = len(buffett[buffett['cash'] == 0])
    
    log(f"  Buffett总数: {total_buffett}")
    log(f"  收入为0: {zero_revenue} ({zero_revenue/total_buffett*100:.1f}%)")
    log(f"  净利润为0: {zero_income} ({zero_income/total_buffett*100:.1f}%)")
    log(f"  权益为0: {zero_equity} ({zero_equity/total_buffett*100:.1f}%)")
    log(f"  现金为0: {zero_cash} ({zero_cash/total_buffett*100:.1f}%)")
    
    if zero_revenue / total_buffett > 0.05:
        issues.append(f"Buffett收入数据质量问题: {zero_revenue}条记录收入为0")
    if zero_income / total_buffett > 0.1:
        issues.append(f"Buffett净利润数据质量问题: {zero_income}条记录净利润为0")
    
    # 2. 检查财务数据
    log("检查财务数据...")
    fin_df = pd.read_csv(FINANCIAL_FILE)
    total_fin = len(fin_df)
    
    # 取最新一期
    fin_df['code_num'] = fin_df['code'].apply(lambda x: x.split('.')[1] if '.' in str(x) else str(x))
    fin_df['code_int'] = fin_df['code_num'].astype(int)
    fin_latest = fin_df.sort_values('statDate', ascending=False).drop_duplicates(subset=['code_int'], keep='first')
    
    zero_roe = len(fin_latest[fin_latest['roeAvg'] == 0])
    zero_margin = len(fin_latest[fin_latest['npMargin'] == 0])
    
    log(f"  财务数据总数: {len(fin_latest)}")
    log(f"  ROE为0: {zero_roe} ({zero_roe/len(fin_latest)*100:.1f}%)")
    log(f"  净利率为0: {zero_margin} ({zero_margin/len(fin_latest)*100:.1f}%)")
    
    if issues:
        log("⚠️ 数据质量问题:")
        for issue in issues:
            log(f"  - {issue}")
    else:
        log("✅ 数据质量检查通过")
    
    return buffett, fin_latest, issues

def load_technical_data(code):
    """加载技术指标数据"""
    # 尝试不同的代码格式
    for fname in [f"{code}.csv", f"{code:06d}.csv"]:
        fpath = os.path.join(TECH_DIR, fname)
        if os.path.exists(fpath):
            try:
                df = pd.read_csv(fpath)
                if len(df) > 0:
                    latest = df.iloc[-1]
                    return {
                        'RSI6': float(latest.get('RSI6', latest.get('RSI_6', 50))),
                        'RSI14': float(latest.get('RSI14', latest.get('RSI_14', 50))),
                        'MACD_DIF': float(latest.get('MACD_DIF', 0)),
                        'MACD_DEA': float(latest.get('MACD_DEA', 0)),
                        'KDJ_K': float(latest.get('KDJ_K', 50)),
                        'KDJ_D': float(latest.get('KDJ_D', 50)),
                        'WR14': float(latest.get('WR14', -50)),
                        'BB_POSITION': float(latest.get('BB_POSITION', 50)),
                        'date': latest.get('date', latest.get('datetime', ''))
                    }
            except:
                pass
    return None

def calculate_buffett_score(b):
    """计算巴菲特10大公式得分"""
    scores = {}
    total_score = 0
    
    # 1. 现金测试 (cash / total assets) - 优质公司持有大量现金
    # >20% 得2分, >10% 得1分
    try:
        if b['total_assets'] > 0:
            cash_ratio = b['cash'] / b['total_assets']
            if cash_ratio > 0.2:
                scores['cash_test'] = 2
            elif cash_ratio > 0.1:
                scores['cash_test'] = 1
            else:
                scores['cash_test'] = 0
        else:
            scores['cash_test'] = 0
    except:
        scores['cash_test'] = 0
    
    # 2. 负债权益比 - 优质公司负债低
    # <0.5 得2分, <1 得1分, >=1 得0分
    try:
        if b['equity'] > 0:
            de_ratio = b['total_liabilities'] / b['equity']
            if de_ratio < 0.5:
                scores['debt_equity'] = 2
            elif de_ratio < 1:
                scores['debt_equity'] = 1
            else:
                scores['debt_equity'] = 0
        else:
            scores['debt_equity'] = 0
    except:
        scores['debt_equity'] = 0
    
    # 3. ROE - 衡量股东权益收益水平
    # >20% 得2分, >15% 得1分
    try:
        if b['equity'] > 0:
            roe = b['net_income'] / b['equity']
            if roe > 0.2:
                scores['roe'] = 2
            elif roe > 0.15:
                scores['roe'] = 1
            else:
                scores['roe'] = 0
        else:
            scores['roe'] = 0
    except:
        scores['roe'] = 0
    
    # 4. 流动比率 (current assets / current liabilities) - 短期偿债能力
    # >2 得1分, >1 得0.5分
    try:
        if b['current_liabilities'] > 0:
            current_ratio = b['current_assets'] / b['current_liabilities']
            if current_ratio > 2:
                scores['current_ratio'] = 1
            elif current_ratio > 1:
                scores['current_ratio'] = 0.5
            else:
                scores['current_ratio'] = 0
        else:
            scores['current_ratio'] = 0.5  # 无短期负债算及格
    except:
        scores['current_ratio'] = 0
    
    # 5. 营业利润率 - 主业盈利能力
    # >20% 得2分, >10% 得1分
    try:
        if b['revenue'] > 0 and b['operating_profit'] > 0:
            op_margin = b['operating_profit'] / b['revenue']
            if op_margin > 0.2:
                scores['op_margin'] = 2
            elif op_margin > 0.1:
                scores['op_margin'] = 1
            else:
                scores['op_margin'] = 0
        else:
            scores['op_margin'] = 0
    except:
        scores['op_margin'] = 0
    
    # 6. 资产周转率 (revenue / total assets) - 资产使用效率
    # >1 得2分, >0.5 得1分
    try:
        if b['total_assets'] > 0:
            asset_turnover = b['revenue'] / b['total_assets']
            if asset_turnover > 1:
                scores['asset_turnover'] = 2
            elif asset_turnover > 0.5:
                scores['asset_turnover'] = 1
            else:
                scores['asset_turnover'] = 0
        else:
            scores['asset_turnover'] = 0
    except:
        scores['asset_turnover'] = 0
    
    # 7. 利息保障倍数 (EBIT / interest) - 利息偿付能力
    # >10 得1分, >5 得0.5分
    try:
        if b['interest_expense'] > 0:
            # 用营业利润近似EBIT
            if b['operating_profit'] > 0:
                interest_coverage = b['operating_profit'] / b['interest_expense']
                if interest_coverage > 10:
                    scores['interest_coverage'] = 1
                elif interest_coverage > 5:
                    scores['interest_coverage'] = 0.5
                else:
                    scores['interest_coverage'] = 0
            else:
                scores['interest_coverage'] = 0
        else:
            scores['interest_coverage'] = 1  # 无利息支出得满分
    except:
        scores['interest_coverage'] = 0
    
    # 8. 盈利稳定性 - 用净利率标准差衡量 (简化版)
    # 如果净利润>0 得1分
    try:
        if b['net_income'] > 0:
            scores['earnings_stability'] = 1
        else:
            scores['earnings_stability'] = 0
    except:
        scores['earnings_stability'] = 0
    
    # 9. 自由现金流 - 现金充裕
    # 现金>总负债 得2分, 现金>短期负债 得1分
    try:
        if b['cash'] > b['total_liabilities']:
            scores['free_cashflow'] = 2
        elif b['cash'] > b['short_debt'] if b['short_debt'] > 0 else b['cash'] > 0:
            scores['free_cashflow'] = 1
        else:
            scores['free_cashflow'] = 0
    except:
        scores['free_cashflow'] = 0
    
    # 10. 资本配置(分红) - 用分红率衡量
    # 由于没有分红数据，用股息率替代
    # 这里简化为: 盈利且有现金 得1分
    try:
        if b['net_income'] > 0 and b['cash'] > 0:
            scores['capital_allocation'] = 1
        else:
            scores['capital_allocation'] = 0
    except:
        scores['capital_allocation'] = 0
    
    total_score = sum(scores.values())
    return scores, total_score

def calculate_fundamental_score(fin, b):
    """计算基本面得分"""
    scores = {}
    
    # ROE: >20%得2分, >10%得1分
    roe = fin.get('roeAvg', 0) * 100 if fin.get('roeAvg', 0) <= 1 else fin.get('roeAvg', 0)
    if roe > 20:
        scores['roe'] = 2
    elif roe > 10:
        scores['roe'] = 1
    else:
        scores['roe'] = 0
    
    # 净利润: >1亿得1分
    net_profit = fin.get('netProfit', 0)
    if net_profit > 1e8:
        scores['net_profit'] = 1
    else:
        scores['net_profit'] = 0
    
    # 毛利率: >30%得1分
    gp_margin = fin.get('gpMargin', 0) * 100 if fin.get('gpMargin', 0) <= 1 else fin.get('gpMargin', 0)
    if gp_margin > 30:
        scores['gp_margin'] = 1
    else:
        scores['gp_margin'] = 0
    
    # 净利率: >10%得1分
    np_margin = fin.get('npMargin', 0) * 100 if fin.get('npMargin', 0) <= 1 else fin.get('npMargin', 0)
    if np_margin > 10:
        scores['np_margin'] = 1
    else:
        scores['np_margin'] = 0
    
    # EPS: >0.3得1分
    eps = fin.get('epsTTM', 0)
    if eps > 0.3:
        scores['eps'] = 1
    else:
        scores['eps'] = 0
    
    # 资产负债率: <50%得1分
    if b['total_assets'] > 0:
        debt_ratio = b['total_liabilities'] / b['total_assets']
        if debt_ratio < 0.5:
            scores['debt_ratio'] = 1
        else:
            scores['debt_ratio'] = 0
    else:
        scores['debt_ratio'] = 0
    
    total_score = sum(scores.values())
    return scores, total_score

def calculate_technical_score(tech):
    """计算技术面得分"""
    if tech is None:
        return {}, 0
    
    scores = {}
    
    # Williams %R: <-80得3分 (超卖)
    wr = tech.get('WR14', -50)
    if wr < -80:
        scores['wr'] = 3
    elif wr < -60:
        scores['wr'] = 1.5
    else:
        scores['wr'] = 0
    
    # RSI: <30得1分 (超卖)
    rsi = tech.get('RSI6', 50)
    if rsi < 30:
        scores['rsi'] = 1
    elif rsi < 40:
        scores['rsi'] = 0.5
    else:
        scores['rsi'] = 0
    
    # MACD: 金叉得1分
    macd_dif = tech.get('MACD_DIF', 0)
    macd_dea = tech.get('MACD_DEA', 0)
    if macd_dif > macd_dea:
        scores['macd'] = 1
    else:
        scores['macd'] = 0
    
    # KDJ: K<20得1分 (超卖)
    kdj_k = tech.get('KDJ_K', 50)
    if kdj_k < 20:
        scores['kdj'] = 1
    else:
        scores['kdj'] = 0
    
    # 布林带: 触及下轨得1分
    bb_pos = tech.get('BB_POSITION', 50)
    if bb_pos < 20:
        scores['bollinger'] = 1
    else:
        scores['bollinger'] = 0
    
    total_score = sum(scores.values())
    return scores, total_score

def calculate_dcf_score(tech):
    """计算DCF得分 (简化版，用技术面估值)"""
    if tech is None:
        return 0
    
    # 由于没有DCF所需的现金流数据，用PB和PE综合估值
    # 这里简化处理，返回0分
    # 完整DCF需要在报告中计算
    return 0

def check_anomalies(b, fin):
    """检查异常情况"""
    anomalies = []
    
    # 1. 检查退市风险
    # 股票名称含"退"字
    
    # 2. 检查ROE异常高
    if b['equity'] > 0:
        roe = b['net_income'] / b['equity']
        if roe > 0.5:  # >50%
            anomalies.append(f"ROE异常高: {roe*100:.1f}%")
    
    # 3. 检查净利率异常
    if b['revenue'] > 0:
        np_ratio = b['net_income'] / b['revenue']
        if np_ratio > 1:  # >100%
            anomalies.append(f"净利率异常: {np_ratio*100:.1f}%")
    
    # 4. 检查负债率异常高
    if b['total_assets'] > 0:
        debt_ratio = b['total_liabilities'] / b['total_assets']
        if debt_ratio > 0.9:  # >90%
            anomalies.append(f"负债率过高: {debt_ratio*100:.1f}%")
    
    # 5. 检查数据质量问题
    if b['revenue'] == 0 or b['net_income'] == 0:
        anomalies.append("收入或净利润为0")
    
    return anomalies

def main():
    """主筛选流程"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    log("=" * 60)
    log("V3.0 全A股全面筛选")
    log("=" * 60)
    
    # 步骤1: 数据质量检查
    buffett, fin_latest, issues = check_data_quality()
    
    # 步骤2: 合并数据
    log("\n" + "=" * 60)
    log("步骤2: 合并数据")
    log("=" * 60)
    
    # 创建股票列表 (从Buffett数据)
    stock_list = buffett['code'].unique().tolist()
    log(f"待筛选股票数量: {len(stock_list)}")
    
    # 创建财务数据查找字典
    fin_dict = {}
    for _, row in fin_latest.iterrows():
        code = int(row['code_int'])
        fin_dict[code] = row.to_dict()
    
    # 步骤3: 筛选计算
    log("\n" + "=" * 60)
    log("步骤3: 计算评分")
    log("=" * 60)
    
    results = []
    skipped_delisted = 0
    skipped_no_data = 0
    skipped_anomaly = 0
    processed = 0
    
    for code in stock_list:
        try:
            # 获取Buffett数据
            b_rows = buffett[buffett['code'] == code]
            if len(b_rows) == 0:
                continue
            b = b_rows.iloc[0].to_dict()
            
            # 获取财务数据
            fin = fin_dict.get(int(code), None)
            if fin is None:
                skipped_no_data += 1
                continue
            
            # 获取技术数据
            tech = load_technical_data(int(code))
            
            # 检查异常
            anomalies = check_anomalies(b, fin)
            
            # 检查退市
            # (由于Buffett数据中没有股票名称，跳过名称检查)
            
            # 检查数据完整性
            if b['revenue'] == 0 and b['net_income'] == 0:
                skipped_no_data += 1
                continue
            
            # 计算各项得分
            buffett_scores, buffett_total = calculate_buffett_score(b)
            fund_scores, fund_total = calculate_fundamental_score(fin, b)
            tech_scores, tech_total = calculate_technical_score(tech)
            dcf_total = calculate_dcf_score(tech)
            
            # 计算综合得分 (满分28分)
            # 巴菲特10 + 基本面7 + 技术面6 + DCF5
            total_score = buffett_total + fund_total + tech_total + dcf_total
            
            # 记录结果
            result = {
                'code': int(code),
                'name': fin.get('security_name_abbr', ''),  # 财务数据中有名称
                'buffett_score': buffett_total,
                'fundamental_score': fund_total,
                'technical_score': tech_total,
                'dcf_score': dcf_total,
                'total_score': total_score,
                # 关键指标
                'roe': fin.get('roeAvg', 0) * 100 if fin.get('roeAvg', 0) <= 1 else fin.get('roeAvg', 0),
                'gp_margin': fin.get('gpMargin', 0) * 100 if fin.get('gpMargin', 0) <= 1 else fin.get('gpMargin', 0),
                'np_margin': fin.get('npMargin', 0) * 100 if fin.get('npMargin', 0) <= 1 else fin.get('npMargin', 0),
                'net_profit': fin.get('netProfit', 0) / 1e8,  # 亿元
                'revenue': fin.get('MBRevenue', 0) / 1e8,  # 亿元
                'debt_ratio': b['total_liabilities'] / b['total_assets'] if b['total_assets'] > 0 else 0,
                'cash': b['cash'] / 1e8,  # 亿元
                'equity': b['equity'] / 1e8,  # 亿元
                'anomalies': '; '.join(anomalies) if anomalies else '',
                'tech_date': tech.get('date', '') if tech else ''
            }
            
            results.append(result)
            processed += 1
            
            if processed % 500 == 0:
                log(f"已处理: {processed}/{len(stock_list)}")
            
        except Exception as e:
            continue
    
    log(f"\n筛选完成! 有效股票: {len(results)}")
    log(f"跳过(无数据): {skipped_no_data}")
    
    # 步骤4: 排序输出
    log("\n" + "=" * 60)
    log("步骤4: 生成结果")
    log("=" * 60)
    
    # 转换为DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values('total_score', ascending=False)
    
    # 输出Top 200
    top200 = df.head(200).copy()
    top200['rank'] = range(1, len(top200) + 1)
    
    # 格式化输出
    output_cols = ['rank', 'code', 'name', 'total_score', 'buffett_score', 
                   'fundamental_score', 'technical_score', 'dcf_score',
                   'roe', 'gp_margin', 'np_margin', 'net_profit', 'debt_ratio', 'anomalies']
    top200_output = top200[output_cols].copy()
    
    # 保留2位小数
    for col in ['total_score', 'buffett_score', 'fundamental_score', 'technical_score', 
                'roe', 'gp_margin', 'np_margin', 'debt_ratio']:
        if col in top200_output.columns:
            top200_output[col] = top200_output[col].round(2)
    
    top200_output.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    log(f"结果已保存: {OUTPUT_FILE}")
    
    # 输出Top 20详情
    log("\n" + "=" * 60)
    log("Top 20 股票")
    log("=" * 60)
    
    for idx, row in top200.head(20).iterrows():
        anomaly_str = f" ⚠️{row['anomalies']}" if row['anomalies'] else ""
        print(f"{row['rank']:3d}. {int(row['code']):06d} {row['name']:10s} "
              f"总分:{row['total_score']:.1f} "
              f"(巴菲特:{row['buffett_score']:.1f} 基本面:{row['fundamental_score']:.1f} 技术:{row['technical_score']:.1f} DCF:{row['dcf_score']:.1f}) "
              f"ROE:{row['roe']:.1f}% 负债:{row['debt_ratio']*100:.1f}%{anomaly_str}")
    
    # 统计信息
    log("\n" + "=" * 60)
    log("筛选统计")
    log("=" * 60)
    log(f"有效股票: {len(results)}")
    log(f"Top 200分数范围: {top200['total_score'].min():.1f} - {top200['total_score'].max():.1f}")
    log(f"Top 200平均分: {top200['total_score'].mean():.1f}")
    
    # 检查异常
    anomalies_df = top200[top200['anomalies'] != '']
    if len(anomalies_df) > 0:
        log(f"\n⚠️ Top 200中有 {len(anomalies_df)} 只股票存在异常:")
        for _, row in anomalies_df.iterrows():
            log(f"  {int(row['code'])} {row['name']}: {row['anomalies']}")
    
    return top200

if __name__ == '__main__':
    main()
