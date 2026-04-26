"""
A股财务数据加载器
从本地CSV文件读取真实财务数据
支持新格式: financial_main_em.csv (EastMoney, 157字段)
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import glob

FINANCIAL_DIR = Path("/home/liujerry/金融数据/fundamentals")


def _get_buffett_real_data(stock_code: str) -> Optional[Dict]:
    """从buffett_supplementary.csv获取真实财务数据"""
    try:
        buffett_file = FINANCIAL_DIR / "buffett_supplementary.csv"
        if not buffett_file.exists():
            return None
        
        buffett_df = pd.read_csv(buffett_file)
        rows = buffett_df[buffett_df['code'].astype(str) == stock_code]
        
        if rows.empty:
            return None
        
        b = rows.iloc[-1]
        
        # 获取operating_cash_flow并处理单位
        operating_cash_flow = b['operating_cash_flow']
        if operating_cash_flow < 100:  # 亿元单位
            operating_cash_flow *= 100000000  # 转为元
        
        return {
            'cash_equivalents': b['cash'] / 1e8,  # 元 -> 亿元
            'short_term_debt': b['short_debt'] / 1e8,
            'long_term_debt': b['long_debt'] / 1e8,
            'total_liabilities': b['total_liabilities'] / 1e8,
            'total_equity': b['equity'] / 1e8,
            'revenue': b['revenue'] / 1e8,
            'net_profit': b['net_income'] / 1e8,
            'operating_profit': b['operating_profit'] / 1e8,
            'current_assets': b['current_assets'] / 1e8,
            'current_liabilities': b['current_liabilities'] / 1e8,
            'total_assets': b['total_assets'] / 1e8,
            'interest_expense': b['interest_expense'] / 1e8,
            'operating_cash_flow': operating_cash_flow / 1e8,
        }
    except Exception:
        return None


def load_financial_data(stock_code: str) -> Optional[Dict]:
    """
    加载指定股票的真实财务数据 (新格式)
    
    Args:
        stock_code: 股票代码，如 '300502'
    
    Returns:
        财务数据字典
    """
    # 股票代码格式化为6位
    stock_code = str(stock_code).zfill(6)
    
    # 优先读取新格式 financial_main_em.csv
    new_file = FINANCIAL_DIR / "chuangye_full" / "financial_main_em.csv"
    if new_file.exists():
        try:
            df = pd.read_csv(new_file)
            # SECUCODE列格式: "300001.SZ" 或 "600519.SH"
            # 从SECUCODE提取股票代码进行匹配
            df['code_clean'] = df['SECUCODE'].astype(str).str.extract(r'(\d+)')[0].str.zfill(6)
            df = df[df['code_clean'] == stock_code]
            
            if df.empty:
                return None
            
            # 获取最新报告期
            latest_period = df['REPORT_DATE'].max()
            df = df[df['REPORT_DATE'] == latest_period]
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            
            result = {}
            
            # ROE (净资产收益率) - ROEJQ 是加权平均
            if pd.notna(row.get('ROEJQ')):
                result['roe'] = float(row['ROEJQ'])
            
            # 毛利率 (MLR = 毛利率)
            if pd.notna(row.get('MLR')):
                result['gross_margin'] = float(row['MLR'])
            
            # 营业收入 (TOTALOPERATEREVE = 营业总收入, 单位元)
            if pd.notna(row.get('TOTALOPERATEREVE')):
                revenue = float(row['TOTALOPERATEREVE'])
                result['revenue'] = revenue / 10000  # 转换为万元
            
            # 净利润 (PARENTNETPROFIT = 归母净利润, 单位元)
            if pd.notna(row.get('PARENTNETPROFIT')):
                profit = float(row['PARENTNETPROFIT'])
                result['net_profit'] = profit / 10000  # 转换为万元
            
            # 资产负债率 (ZCFZL)
            if pd.notna(row.get('ZCFZL')):
                result['debt_ratio'] = float(row['ZCFZL'])
            
            # 基本每股收益 (EPSJB)
            if pd.notna(row.get('EPSJB')):
                result['basic_eps'] = float(row['EPSJB'])
            
            # 每股净资产 (BPS)
            if pd.notna(row.get('BPS')):
                result['book_value_per_share'] = float(row['BPS'])
            
            # 流动比率 (LD = 流动比率)
            if pd.notna(row.get('LD')):
                result['current_ratio'] = float(row['LD'])
            
            # 速动比率 (SD = 速动比率)
            if pd.notna(row.get('SD')):
                result['quick_ratio'] = float(row['SD'])
            
            # 扣非净利润 (KCFJCXSYJLR = 扣非归母净利润)
            if pd.notna(row.get('KCFJCXSYJLR')):
                result['deducted_profit'] = float(row['KCFJCXSYJLR']) / 10000
            
            # 经营现金流 (XJJL = 现金及等价物, 近似)
            if pd.notna(row.get('MGJYXJJE')):  # 每股经营现金流
                result['operating_cash_flow_per_share'] = float(row['MGJYXJJE'])
            
            result['report_period'] = str(latest_period)
            result['stock_name'] = str(row.get('SECURITY_NAME_ABBR', ''))
            
            return result
            
        except Exception as e:
            print(f"读取新格式失败: {e}")
            # 继续尝试旧格式
    
    # 旧格式 fallback: a_stock_financial_new_batch*.csv
    pattern = str(FINANCIAL_DIR / "a_stock_financial_new_batch*.csv")
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # 读取所有文件
    all_data = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df = df[df['stock_code'].astype(str).str.zfill(6) == stock_code]
            if not df.empty:
                all_data.append(df)
        except Exception as e:
            continue
    
    if not all_data:
        return None
    
    # 合并所有数据
    data = pd.concat(all_data, ignore_index=True)
    
    if data.empty:
        return None
    
    # 获取最新报告期
    latest_period = data['report_period'].max()
    data = data[data['report_period'] == latest_period]
    
    if data.empty:
        return None
    
    # 提取关键指标
    result = {}
    
    # 提取 ROE (净资产收益率)
    roe_rows = data[data['metric_name'].str.contains('roe|ROE', case=False, na=False)]
    if not roe_rows.empty:
        result['roe'] = float(roe_rows.iloc[0]['value'])
    
    # 提取 毛利率
    margin_rows = data[data['metric_name'].str.contains('gross_margin|销售毛利率', case=False, na=False)]
    if not margin_rows.empty:
        result['gross_margin'] = float(margin_rows.iloc[0]['value'])
    
    # 提取 营业收入
    revenue_rows = data[data['metric_name'].str.contains('operating_income|营业收入', case=False, na=False)]
    if not revenue_rows.empty:
        result['revenue'] = float(revenue_rows.iloc[0]['value'])
    
    # 提取 净利润
    profit_rows = data[data['metric_name'].str.contains('net_profit|净利润', case=False, na=False)]
    if not profit_rows.empty:
        result['net_profit'] = float(profit_rows.iloc[0]['value'])
    
    # 提取 流动比率
    current_rows = data[data['metric_name'].str.contains('current_ratio|流动比率', case=False, na=False)]
    if not current_rows.empty:
        result['current_ratio'] = float(current_rows.iloc[0]['value'])
    
    # 提取 资产负债率
    debt_rows = data[data['metric_name'].str.contains('assets_debt_ratio|资产负债率', case=False, na=False)]
    if not debt_rows.empty:
        result['debt_ratio'] = float(debt_rows.iloc[0]['value'])
    
    # 提取 基本每股收益
    eps_rows = data[data['metric_name'].str.contains('basic_eps|基本每股收益', case=False, na=False)]
    if not eps_rows.empty:
        result['basic_eps'] = float(eps_rows.iloc[0]['value'])
    
    result['report_period'] = latest_period
    
    return result


def get_financial_data_for_buffett(stock_code: str) -> Dict:
    """
    获取适合巴菲特10大公式的财务数据
    
    Args:
        stock_code: 股票代码
    
    Returns:
        格式化后的财务数据
    """
    data = load_financial_data(stock_code)
    
    if data is None:
        return {}
    
    result = {}
    
    # ROE (已经是百分比)
    if 'roe' in data:
        result['roe'] = data['roe'] * 100  # 转为百分比
    
    # 毛利率
    if 'gross_margin' in data:
        result['gross_margin'] = data['gross_margin']
    
    # 营业收入 (万元)
    if 'revenue' in data:
        result['revenue'] = data['revenue']
    
    # 净利润 (万元)
    if 'net_profit' in data:
        result['net_profit'] = data['net_profit']
    
    # 流动比率
    if 'current_ratio' in data:
        result['current_ratio'] = data['current_ratio']
    
    # 资产负债率
    if 'debt_ratio' in data:
        result['debt_ratio'] = data['debt_ratio']
    
    # 优先从buffett_supplementary.csv获取真实数据
    buffett_real = _get_buffett_real_data(code)
    
    if buffett_real:
        # 使用真实数据 (单位已经是亿元，需要转换为万元)
        result['cash_equivalents'] = buffett_real['cash_equivalents'] * 10000
        result['total_liabilities'] = buffett_real['total_liabilities'] * 10000
        result['total_equity'] = buffett_real['total_equity'] * 10000
        result['short_term_debt'] = buffett_real['short_term_debt'] * 10000
        result['operating_profit'] = buffett_real['operating_profit'] * 10000
        result['current_assets'] = buffett_real['current_assets'] * 10000
        result['current_liabilities'] = buffett_real['current_liabilities'] * 10000
        result['interest_expense'] = buffett_real['interest_expense'] * 10000
        result['operating_cash_flow'] = buffett_real['operating_cash_flow'] * 10000
    else:
        # 降级：估算数据 (仅当真实数据不可用时)
        # 现金及等价物 = 营收的 20%
        if 'revenue' in data:
            result['cash_equivalents'] = data['revenue'] * 0.2
        
        # 总负债 = 资产负债率 * 总资产 (假设总资产 = 营收 * 2)
        if 'debt_ratio' in data and 'revenue' in data:
            total_assets = data['revenue'] * 2
            result['total_liabilities'] = total_assets * data['debt_ratio'] / 100
            result['total_equity'] = total_assets - result['total_liabilities']
        
        # 短期负债 = 总负债的 50%
        if 'total_liabilities' in result:
            result['short_term_debt'] = result['total_liabilities'] * 0.5
        
        # 营业利润 = 营收 * 毛利率
        if 'revenue' in data and 'gross_margin' in data:
            result['operating_profit'] = data['revenue'] * data['gross_margin'] / 100
        
        # 流动资产 = 总资产 * 40%
        if 'total_liabilities' in result and 'total_equity' in result:
            total_assets = result['total_liabilities'] + result['total_equity']
            result['current_assets'] = total_assets * 0.4
            result['current_liabilities'] = total_assets * 0.25
        
        # 利息费用 = 负债 * 5%
        if 'total_liabilities' in result:
            result['interest_expense'] = result['total_liabilities'] * 0.05
        
        # 经营现金流 = 净利润 * 1.1
        if 'net_profit' in data:
            result['operating_cash_flow'] = data['net_profit'] * 1.1
    
    result['report_period'] = data.get('report_period', 'N/A')
    
    return result


if __name__ == "__main__":
    # 测试
    codes = ['300502', '300308', '300276']
    
    for code in codes:
        print(f"\n{'='*50}")
        print(f"股票代码: {code}")
        print('='*50)
        
        data = load_financial_data(code)
        
        if data:
            print(f"报告期: {data.get('report_period')}")
            for k, v in data.items():
                print(f"  {k}: {v}")
        else:
            print("  无数据")
