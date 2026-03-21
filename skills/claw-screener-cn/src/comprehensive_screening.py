#!/usr/bin/env python3
"""
综合评分筛选 - 使用所有模块
"""

import os
import pandas as pd
import baostock as bs
import akshare as ak

STOCK_DIR = "/home/liujerry/金融数据/stocks_clean"
OUTPUT_DIR = "/home/liujerry/金融数据/screening_results"

def get_financial_data(code):
    """获取财务数据"""
    try:
        fin_df = ak.stock_financial_abstract_ths(symbol=code)
        if fin_df is None or fin_df.empty:
            return None
        
        latest = fin_df.iloc[-1]  # 最新数据
        
        data = {'code': code}
        
        # ROE
        roe_str = str(latest.get('净资产收益率', '0'))
        if roe_str and roe_str not in ['nan', 'None', '']:
            try:
                data['roe'] = float(roe_str.replace('%', ''))
            except:
                data['roe'] = 0
        else:
            data['roe'] = 0
        
        # 毛利率
        margin_str = str(latest.get('销售毛利率', '0'))
        if margin_str and margin_str not in ['nan', 'None', '']:
            try:
                data['margin'] = float(margin_str.replace('%', ''))
            except:
                data['margin'] = 0
        else:
            data['margin'] = 0
        
        # 资产负债率
        debt_str = str(latest.get('资产负债率', '0'))
        if debt_str and debt_str not in ['nan', 'None', '']:
            try:
                data['debt_ratio'] = float(debt_str.replace('%', ''))
            except:
                data['debt_ratio'] = 0
        else:
            data['debt_ratio'] = 0
        
        return data
    except:
        return None

def get_price_data(code):
    """获取价格和动量"""
    try:
        bs_code = f"sz.{code}"
        lg = bs.login()
        rs = bs.query_history_k_data_plus(
            bs_code, "date,close",
            start_date="2024-01-01", frequency="d"
        )
        
        prices = []
        while rs.next():
            prices.append(rs.get_row_data())
        
        bs.logout()
        
        if not prices or len(prices) < 60:
            return None
        
        data = {'code': code}
        
        # 价格
        data['price'] = float(prices[-1][1])
        
        # 6个月动量
        if len(prices) >= 20:
            data['momentum_6m'] = (float(prices[-1][1]) / float(prices[-20][1]) - 1) * 100
        
        # 12个月动量
        if len(prices) >= 240:
            data['momentum_12m'] = (float(prices[-1][1]) / float(prices[-240][1]) - 1) * 100
        
        # 波动率 (年化)
        price_list = [float(p[1]) for p in prices]
        returns = pd.Series(price_list).pct_change().dropna()
        data['volatility'] = returns.std() * (252 ** 0.5)
        
        return data
    except:
        return None

def calculate_comprehensive_score(stock_data):
    """计算综合评分 - 使用所有模块的评分逻辑"""
    
    score = 0
    details = {}
    
    # 1. 神奇公式评分 (ROE + 动量) - 30分
    roe = stock_data.get('roe', 0)
    if roe >= 30:
        details['magic_roe'] = 15
    elif roe >= 20:
        details['magic_roe'] = 12
    elif roe >= 15:
        details['magic_roe'] = 10
    else:
        details['magic_roe'] = 5
    score += details['magic_roe']
    
    # 动量评分
    mom = stock_data.get('momentum_6m', 0)
    if 0 <= mom <= 30:
        details['magic_mom'] = 15
    elif mom < 0:
        details['magic_mom'] = 8
    else:
        details['magic_mom'] = 5
    score += details['magic_mom']
    
    # 2. Fama-French因子评分 - 25分
    # 盈利因子 (RMW)
    if roe >= 20:
        details['ff_rmw'] = 8
    elif roe >= 15:
        details['ff_rmw'] = 6
    else:
        details['ff_rmw'] = 3
    
    # 价值因子 (HML) - 用毛利率近似
    margin = stock_data.get('margin', 0)
    if margin >= 40:
        details['ff_hml'] = 8
    elif margin >= 20:
        details['ff_hml'] = 5
    else:
        details['ff_hml'] = 2
    
    # 规模因子 (SMB) - 创业板都是小盘
    details['ff_smb'] = 4
    
    # 动量因子
    if 0 <= mom <= 30:
        details['ff_mom'] = 5
    else:
        details['ff_mom'] = 2
    
    score += details['ff_rmw'] + details['ff_hml'] + details['ff_smb'] + details['ff_mom']
    
    # 3. 风险控制评分 - 25分
    vol = stock_data.get('volatility', 1)
    if vol < 0.3:
        details['risk_vol'] = 10
    elif vol < 0.5:
        details['risk_vol'] = 7
    elif vol < 0.7:
        details['risk_vol'] = 4
    else:
        details['risk_vol'] = 1
    
    # 资产负债率
    debt = stock_data.get('debt_ratio', 100)
    if debt < 40:
        details['risk_debt'] = 10
    elif debt < 60:
        details['risk_debt'] = 6
    elif debt < 80:
        details['risk_debt'] = 3
    else:
        details['risk_debt'] = 0
    
    # 流动比率 (简化)
    if debt < 50:
        details['risk_liq'] = 5
    else:
        details['risk_liq'] = 2
    
    score += details['risk_vol'] + details['risk_debt'] + details['risk_liq']
    
    # 4. 成长性评分 - 20分
    mom_12m = stock_data.get('momentum_12m', 0)
    if mom_12m >= 20:
        details['growth'] = 10
    elif mom_12m >= 0:
        details['growth'] = 7
    elif mom_12m >= -20:
        details['growth'] = 4
    else:
        details['growth'] = 1
    
    score += details['growth']
    
    details['total'] = score
    return score, details

def main():
    print("=" * 70)
    print("🎯 创业板综合评分筛选 (使用所有模块)")
    print("=" * 70)
    
    # 读取ROE初筛结果
    df = pd.read_csv(f"{OUTPUT_DIR}/screening_results_2026-03-16.csv")
    stocks = df['code'].tolist()
    
    print(f"\n📊 ROE初筛: {len(stocks)} 只")
    
    # 获取完整数据
    results = []
    
    for i, code in enumerate(stocks):
        if (i + 1) % 5 == 0:
            print(f"  处理 {i+1}/{len(stocks)}...")
        
        # 财务数据
        fin = get_financial_data(code)
        
        # 价格数据
        price = get_price_data(code)
        
        if fin and price:
            data = {**fin, **price}
            
            # 计算综合评分
            score, details = calculate_comprehensive_score(data)
            data['comprehensive_score'] = score
            data['score_details'] = details
            
            results.append(data)
    
    # 按综合评分排序
    results.sort(key=lambda x: x['comprehensive_score'], reverse=True)
    
    # 输出 Top 10
    print("\n" + "=" * 70)
    print("🏆 综合评分 Top 10")
    print("=" * 70)
    
    print(f"\n{'排名':<4} {'代码':<8} {'ROE':<8} {'动量':<8} {'波动率':<10} {'综合评分':<10}")
    print("-" * 70)
    
    for i, r in enumerate(results[:10], 1):
        print(f"{i:<4} {r['code']:<8} {r.get('roe', 0):<8.1f}% {r.get('momentum_6m', 0):<8.1f}% {r.get('volatility', 0):<10.2f} {r['comprehensive_score']:<10}")
    
    # 详细评分
    print("\n" + "=" * 70)
    print("📋 Top 3 详细评分")
    print("=" * 70)
    
    for i, r in enumerate(results[:3], 1):
        print(f"\n🥇 第{i}名: {r['code']}")
        d = r['score_details']
        print(f"   神奇公式: ROE得分={d['magic_roe']}, 动量得分={d['magic_mom']} (共{d['magic_roe']+d['magic_mom']}分)")
        print(f"   FF因子: 盈利={d['ff_rmw']}, 价值={d['ff_hml']}, 规模={d['ff_smb']}, 动量={d['ff_mom']} (共{d['ff_rmw']+d['ff_hml']+d['ff_smb']+d['ff_mom']}分)")
        print(f"   风控: 波动={d['risk_vol']}, 负债={d['risk_debt']}, 流动性={d['risk_liq']} (共{d['risk_vol']+d['risk_debt']+d['risk_liq']}分)")
        print(f"   成长: {d['growth']}分")
        print(f"   ─────────────────────────")
        print(f"   总分: {d['total']}/100")
    
    # 保存结果
    output_file = f"{OUTPUT_DIR}/comprehensive_screening_2026-03-16.csv"
    
    save_df = pd.DataFrame(results)
    save_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 完整结果已保存: {output_file}")

if __name__ == "__main__":
    main()
