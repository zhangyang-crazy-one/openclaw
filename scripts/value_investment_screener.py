#!/usr/bin/env python3
"""
价值投资批量筛选脚本
使用本地Buffett数据、财务数据、技术指标
评分权重: 价值投资70% > 技术面30%
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 数据路径
BUFFETT_FILE = "/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv"
FINANCIAL_DIR = "/home/liujerry/金融数据/fundamentals/chuangye_full"
TECH_DIR = "/home/liujerry/金融数据/technical_indicators"
OUTPUT_DIR = "/home/liujerry/金融数据/screening_results"

def load_buffett_data():
    """加载Buffett数据"""
    print("📂 加载Buffett数据...")
    df = pd.read_csv(BUFFETT_FILE)
    print(f"   Buffett数据: {len(df)} 条记录")
    return df

def load_financial_data():
    """加载财务数据"""
    print("📂 加载财务数据...")
    profit_file = os.path.join(FINANCIAL_DIR, "profit.csv")
    if os.path.exists(profit_file):
        df = pd.read_csv(profit_file)
        print(f"   财务数据: {len(df)} 条记录")
        return df
    else:
        print(f"   财务文件不存在: {profit_file}")
        return None

def load_chuangye_stock_list():
    """加载创业板股票列表"""
    list_file = "/home/liujerry/金融数据/fundamentals/chuangye_stock_list.csv"
    if os.path.exists(list_file):
        df = pd.read_csv(list_file)
        return df['code'].tolist() if 'code' in df.columns else df['代码'].tolist()
    return None

def normalize_code(code):
    """将各种格式的股票代码标准化为6位字符串"""
    code_str = str(code)
    
    # 移除前缀: sz., sh., 等
    if '.' in code_str:
        code_str = code_str.split('.')[1]
    
    # 移除 .csv 后缀
    code_str = code_str.replace('.csv', '')
    
    # 确保6位，前面补0
    return code_str.zfill(6)

def load_stock_names_from_akshare():
    """从akshare获取股票名称和状态"""
    try:
        import akshare as ak
        # 使用 stock_info_a_code_name 获取A股股票信息
        df = ak.stock_info_a_code_name()
        # 创建代码到名称的映射
        name_dict = {}
        for _, row in df.iterrows():
            code = str(row['code']).zfill(6)
            name = row['name']
            name_dict[code] = name
        print(f"   获取到 {len(name_dict)} 只股票名称")
        return name_dict
    except Exception as e:
        print(f"   ⚠️ 无法获取股票名称: {e}")
        return {}

def is_delisted(name):
    """检查股票是否退市"""
    if not name:
        return False
    # 退市股票名称通常包含 "退"、"ST"、"*ST" 等
    delist_markers = ['退', 'ST', '*ST', 'S*ST', 'SST']
    return any(marker in name for marker in delist_markers)

def get_buffett_metrics(buffett_df, code):
    """获取Buffett指标 - 从原始数据计算"""
    # 标准化代码
    code_normalized = normalize_code(code)
    
    # 尝试直接匹配
    row = buffett_df[buffett_df['code'].astype(str) == code_normalized]
    
    # 如果没找到，尝试整数匹配
    if len(row) == 0:
        try:
            code_int = int(code_normalized)
            row = buffett_df[buffett_df['code'] == code_int]
        except:
            pass
    
    if len(row) == 0:
        return None
    
    # 获取最新一期数据
    row = row.sort_values('report_date', ascending=False).iloc[0]
    
    # 获取原始数据
    total_assets = row.get('total_assets', 0) or 0
    total_liabilities = row.get('total_liabilities', 0) or 0
    equity = row.get('equity', 0) or 0
    net_income = row.get('net_income', 0) or 0
    revenue = row.get('revenue', 0) or 0
    operating_profit = row.get('operating_profit', 0) or 0
    cash = row.get('cash', 0) or 0
    current_assets = row.get('current_assets', 0) or 0
    current_liabilities = row.get('current_liabilities', 0) or 0
    
    # 转换为浮点数
    try:
        total_assets = float(total_assets) if total_assets else 0
        total_liabilities = float(total_liabilities) if total_liabilities else 0
        equity = float(equity) if equity else 0
        net_income = float(net_income) if net_income else 0
        revenue = float(revenue) if revenue else 0
        operating_profit = float(operating_profit) if operating_profit else 0
        cash = float(cash) if cash else 0
        current_assets = float(current_assets) if current_assets else 0
        current_liabilities = float(current_liabilities) if current_liabilities else 0
    except:
        return None
    
    # 计算指标
    # ROE = 净利润 / 股东权益
    roe = (net_income / equity * 100) if equity > 0 else 0
    
    # 毛利率 = (营收 - 营业成本) / 营收， 用营业利润近似
    # 这里用营业利润/营收作为近似
    gross_margin = (operating_profit / revenue * 100) if revenue > 0 else 0
    
    # 净利率 = 净利润 / 营收
    net_margin = (net_income / revenue * 100) if revenue > 0 else 0
    
    # 资产负债率 = 总负债 / 总资产
    debt_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
    
    # 流动比率 = 流动资产 / 流动负债
    current_ratio = (current_assets / current_liabilities) if current_liabilities > 0 else 0
    
    # 速动比率 = (流动资产 - 存货) / 流动负债，这里简化
    quick_ratio = current_ratio * 0.8  # 近似
    
    # 现金比率 = 现金 / 流动负债
    cash_ratio = (cash / current_liabilities * 100) if current_liabilities > 0 else 0
    
    # 营收转换为亿
    revenue_yi = revenue / 1e8
    net_income_yi = net_income / 1e8
    
    metrics = {
        'code': code_normalized,
        'report_date': row.get('report_date', ''),
        'roe': roe,
        'gross_margin': gross_margin,
        'net_margin': net_margin,
        'current_ratio': current_ratio,
        'quick_ratio': quick_ratio,
        'debt_ratio': debt_ratio,
        'cash_ratio': cash_ratio,
        'fcf': net_income_yi,  # 用净利润近似自由现金流
        'revenue': revenue_yi,
        'operating_profit': operating_profit / 1e8,
        'net_income': net_income_yi,
        'equity': equity / 1e8,
        'total_assets': total_assets / 1e8,
    }
    
    return metrics

def get_financial_metrics(fin_df, code):
    """从财务数据获取指标 - 使用直接计算替代npMargin列"""
    if fin_df is None:
        return None
    
    code_normalized = normalize_code(code)
    
    # 财务数据中的code可能是 "sz.300001" 格式，需要提取后面的部分
    def extract_code(c):
        c_str = str(c)
        if '.' in c_str:
            return c_str.split('.')[1].zfill(6)
        return c_str.zfill(6)
    
    fin_df['code_normalized'] = fin_df['code'].apply(extract_code)
    
    row = fin_df[fin_df['code_normalized'] == code_normalized]
    
    if len(row) == 0:
        return None
    
    # 获取最新一期 (按statDate排序)
    row = row.sort_values('statDate', ascending=False).iloc[0]
    
    # 获取原始指标
    roe_raw = row.get('roeAvg', 0)
    np_margin_raw = row.get('npMargin', 0)  # 旧列（可能不准确）
    gp_margin_raw = row.get('gpMargin', 0)
    net_profit_raw = row.get('netProfit', 0)
    mb_revenue_raw = row.get('MBRevenue', 0)  # 主营业务收入
    eps_raw = row.get('epsTTM', 0)
    
    # 转换为浮点数
    try:
        roe = float(roe_raw) * 100 if roe_raw else 0  # roeAvg 是小数，转百分比
    except:
        roe = 0
    try:
        gp_margin = float(gp_margin_raw) * 100 if gp_margin_raw else 0  # 毛利率是小数
    except:
        gp_margin = 0
    try:
        net_profit = float(net_profit_raw) / 1e8 if net_profit_raw else 0  # 转为亿
    except:
        net_profit = 0
    try:
        revenue = float(mb_revenue_raw) / 1e8 if mb_revenue_raw else 0  # 营收转为亿
    except:
        revenue = 0
    try:
        eps = float(eps_raw) if eps_raw else 0
    except:
        eps = 0
    
    # ========== 关键修复：直接计算净利率 ==========
    # 使用 netProfit / MBRevenue 计算，而不是用 npMargin 列
    # 因为 npMargin 的营收基数可能与 MBRevenue 不同（如300799案例）
    try:
        if net_profit_raw and mb_revenue_raw and float(mb_revenue_raw) > 0:
            np_margin = (float(net_profit_raw) / float(mb_revenue_raw)) * 100
        else:
            np_margin = 0
    except:
        np_margin = 0
    
    metrics = {
        'roe': roe,
        'net_margin': np_margin,
        'gross_margin': gp_margin,
        'net_income': net_profit,
        'revenue': revenue,  # 新增：营收字段
        'eps': eps,
    }
    
    return metrics

def get_technical_score(tech_df):
    """计算技术面得分 (7分制)"""
    if tech_df is None or tech_df.empty:
        return 0, {}
    
    score = 0
    details = {}
    
    latest = tech_df.iloc[-1]
    
    # Williams %R (3分) - 超卖信号
    wr = latest.get('WR14', latest.get('wr14', 0))
    if isinstance(wr, str):
        try:
            wr = float(wr)
        except:
            wr = 0
    
    if wr < -80:
        score += 3
        details['wr'] = f"{wr:.1f} 超卖 ✅"
    elif wr < -50:
        score += 1.5
        details['wr'] = f"{wr:.1f} 偏低"
    else:
        details['wr'] = f"{wr:.1f} 正常"
    
    # RSI (1分)
    rsi = latest.get('RSI6', latest.get('rsi6', 50))
    if isinstance(rsi, str):
        try:
            rsi = float(rsi)
        except:
            rsi = 50
    
    if rsi < 30:
        score += 1
        details['rsi'] = f"{rsi:.1f} 超卖 ✅"
    elif rsi > 70:
        score += 0
        details['rsi'] = f"{rsi:.1f} 超买"
    else:
        score += 0.5
        details['rsi'] = f"{rsi:.1f} 中性"
    
    # MACD (1分)
    macd_dif = latest.get('MACD_DIF', latest.get('macd_dif', 0))
    macd_dea = latest.get('MACD_DEA', latest.get('macd_dea', 0))
    if isinstance(macd_dif, str):
        try:
            macd_dif = float(macd_dif)
        except:
            macd_dif = 0
    if isinstance(macd_dea, str):
        try:
            macd_dea = float(macd_dea)
        except:
            macd_dea = 0
    
    if macd_dif > macd_dea:
        score += 1
        details['macd'] = "金叉 ✅"
    else:
        details['macd'] = "死叉"
    
    # KDJ (1分)
    kdj_k = latest.get('KDJ_K', latest.get('kdj_k', 50))
    if isinstance(kdj_k, str):
        try:
            kdj_k = float(kdj_k)
        except:
            kdj_k = 50
    
    if kdj_k < 20:
        score += 1
        details['kdj'] = f"{kdj_k:.1f} 超卖 ✅"
    elif kdj_k > 80:
        score += 0
        details['kdj'] = f"{kdj_k:.1f} 超买"
    else:
        score += 0.5
        details['kdj'] = f"{kdj_k:.1f} 中性"
    
    # 布林带 (1分)
    boll_pos = latest.get('布林带位置', latest.get('boll_position', 0.5))
    if isinstance(boll_pos, str):
        try:
            boll_pos = float(boll_pos.replace('%', '')) / 100
        except:
            boll_pos = 0.5
    
    if boll_pos < 0.2:
        score += 1
        details['boll'] = f"{boll_pos*100:.1f}% 触及下轨 ✅"
    else:
        details['boll'] = f"{boll_pos*100:.1f}%"
    
    return score, details

def calculate_buffett_score(metrics):
    """计算Buffett公式得分 (10分制)"""
    if metrics is None:
        return 0, {}
    
    score = 0
    details = {}
    
    # 1. 现金测试 (2分) - 现金/总资产 > 10%
    cash_ratio = metrics.get('cash_ratio', 0)
    if cash_ratio > 20:
        score += 2
        details['cash'] = f"{cash_ratio:.1f}% 优秀 ✅"
    elif cash_ratio > 10:
        score += 1
        details['cash'] = f"{cash_ratio:.1f}% 良好"
    else:
        details['cash'] = f"{cash_ratio:.1f}% 偏低"
    
    # 2. 负债权益比 (2分) - 负债/权益 < 0.5
    debt_ratio = metrics.get('debt_ratio', 100)
    if debt_ratio < 30:
        score += 2
        details['debt'] = f"{debt_ratio:.1f}% 极低 ✅"
    elif debt_ratio < 50:
        score += 1
        details['debt'] = f"{debt_ratio:.1f}% 低"
    else:
        details['debt'] = f"{debt_ratio:.1f}% 高"
    
    # 3. ROE (2分) - > 15%
    roe = metrics.get('roe', 0)
    if roe > 25:
        score += 2
        details['roe'] = f"{roe:.1f}% 极优秀 ✅"
    elif roe > 15:
        score += 1
        details['roe'] = f"{roe:.1f}% 良好"
    else:
        details['roe'] = f"{roe:.1f}% 一般"
    
    # 4. 流动比率 (1分) - > 1.5
    current_ratio = metrics.get('current_ratio', 0)
    if current_ratio > 2:
        score += 1
        details['current'] = f"{current_ratio:.2f} 优秀 ✅"
    elif current_ratio > 1.5:
        score += 0.5
        details['current'] = f"{current_ratio:.2f} 良好"
    else:
        details['current'] = f"{current_ratio:.2f} 偏低"
    
    # 5. 营业利润率 (1分) - > 15%
    net_margin = metrics.get('net_margin', 0)
    if net_margin > 20:
        score += 1
        details['margin'] = f"{net_margin:.1f}% 优秀 ✅"
    elif net_margin > 10:
        score += 0.5
        details['margin'] = f"{net_margin:.1f}% 良好"
    else:
        details['margin'] = f"{net_margin:.1f}% 一般"
    
    # 6-10. 其他指标 (2分)
    # 毛利率
    gross_margin = metrics.get('gross_margin', 0)
    if gross_margin > 40:
        score += 0.5
        details['gross'] = f"{gross_margin:.1f}% 高毛利 ✅"
    else:
        details['gross'] = f"{gross_margin:.1f}%"
    
    # 速动比率
    quick_ratio = metrics.get('quick_ratio', 0)
    if quick_ratio > 1:
        score += 0.5
        details['quick'] = f"{quick_ratio:.2f} 良好 ✅"
    else:
        details['quick'] = f"{quick_ratio:.2f}"
    
    # 自由现金流
    fcf = metrics.get('fcf', 0)
    if fcf > 0:
        score += 0.5
        details['fcf'] = f"{fcf:.2f} 正 ✅"
    else:
        details['fcf'] = f"{fcf:.2f} 负"
    
    # 营收
    revenue = metrics.get('revenue', 0)
    if revenue > 10:  # 10亿以上
        score += 0.5
        details['revenue'] = f"{revenue:.1f}亿 大规模 ✅"
    else:
        details['revenue'] = f"{revenue:.1f}亿"
    
    return score, details

def calculate_fundamental_score(metrics):
    """计算基本面得分 (7分制) - 带防作弊检测"""
    if metrics is None:
        return 0, {}
    
    score = 0
    details = {}
    warnings = []
    
    # 获取原始数据
    net_margin = metrics.get('net_margin', 0)
    roe = metrics.get('roe', 0)
    net_income = metrics.get('net_income', 0)
    gross_margin = metrics.get('gross_margin', 0)
    eps = metrics.get('eps', 0)
    revenue = metrics.get('revenue', 0)
    
    # ========== 防作弊检测 ==========
    # 1. 检查异常净利率（>200%通常是非经常性收益，疑似财务操纵）
    if net_margin > 200:
        warnings.append(f"⚠️ 异常净利率{net_margin:.0f}%！净利润可能含非经常性收益")
        # 净利率>200%时，该项不给分
        details['net_margin'] = f"{net_margin:.1f}% 异常 ❌"
    elif net_margin > 50:
        warnings.append(f"⚠️ 净利率{net_margin:.0f}%偏高")
        score += 0.3
        details['net_margin'] = f"{net_margin:.1f}% 偏高"
    elif net_margin > 20:
        score += 1
        details['net_margin'] = f"{net_margin:.1f}% 高净利 ✅"
    elif net_margin > 10:
        score += 0.5
        details['net_margin'] = f"{net_margin:.1f}% 良好"
    else:
        details['net_margin'] = f"{net_margin:.1f}%"
    
    # 2. 检查净利润/营收比（如果净利润很高但营收极低，疑似造假）
    if revenue > 0 and net_income > 1:  # 净利润>1亿且营收>0
        ratio = net_income / revenue
        if ratio > 10:
            warnings.append(f"⚠️ 净利润/营收={ratio:.1f}倍，严重异常！")
        elif ratio > 5:
            warnings.append(f"⚠️ 净利润/营收={ratio:.1f}倍偏高")
    
    # 3. ROE检测（如果净利率异常，ROE也可能是虚高的）
    if net_margin > 200:
        # 净利率异常时，ROE需要打折
        details['roe'] = f"{roe:.1f}% 疑似虚高 ⚠️"
    elif roe > 25:
        score += 2
        details['roe'] = f"{roe:.1f}% 极优秀 ✅"
    elif roe > 15:
        score += 1
        details['roe'] = f"{roe:.1f}% 良好"
    else:
        details['roe'] = f"{roe:.1f}%"
    
    # 4. 净利润规模 (1分)
    if net_income > 10:
        score += 1
        details['income'] = f"{net_income:.1f}亿 大规模 ✅"
    elif net_income > 1:
        score += 0.5
        details['income'] = f"{net_income:.1f}亿 达标"
    else:
        details['income'] = f"{net_income:.1f}亿"
    
    # 5. 毛利率 (1分)
    if gross_margin > 50:
        score += 1
        details['gross'] = f"{gross_margin:.1f}% 高毛利 ✅"
    elif gross_margin > 30:
        score += 0.5
        details['gross'] = f"{gross_margin:.1f}% 良好"
    else:
        details['gross'] = f"{gross_margin:.1f}%"
    
    # 6. 每股收益 (1分)
    if eps > 1:
        score += 1
        details['eps'] = f"{eps:.2f}元 高EPS ✅"
    elif eps > 0.3:
        score += 0.5
        details['eps'] = f"{eps:.2f}元 达标"
    else:
        details['eps'] = f"{eps:.2f}元"
    
    # 7. 成长性 (1分) - 用营收规模
    if revenue > 50:
        score += 1
        details['growth'] = f"{revenue:.1f}亿 大规模 ✅"
    elif revenue > 10:
        score += 0.5
        details['growth'] = f"{revenue:.1f}亿 良好"
    else:
        details['growth'] = f"{revenue:.1f}亿"
    
    # 添加警告信息
    details['warnings'] = warnings
    
    return score, details

def main():
    print("=" * 80)
    print("🎯 价值投资批量筛选 V2")
    print("   评分权重: 价值投资(Buffett+基本面) > 技术面")
    print("   新增: 防作弊检测 + 退市股票过滤")
    print("=" * 80)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 加载数据
    buffett_df = load_buffett_data()
    financial_df = load_financial_data()
    
    # 获取股票名称（用于过滤退市股票）
    print("📂 加载股票名称数据...")
    stock_names = load_stock_names_from_akshare()
    
    # 获取全部A股股票列表（从Buffett数据）
    # Buffett数据有5392只，覆盖主板、创业板、科创板
    stock_list = buffett_df['code'].astype(str).unique().tolist()
    print(f"\n📊 待筛选股票: {len(stock_list)} 只 (全A股)")
    
    # 批量筛选
    results = []
    delisted_count = 0
    warning_count = 0
    total = len(stock_list)
    
    print("\n🔍 开始筛选...")
    
    for i, code in enumerate(stock_list):
        if (i + 1) % 100 == 0:
            print(f"   进度: {i+1}/{total} ({100*(i+1)//total}%)")
        
        # 标准化代码
        code_normalized = normalize_code(code)
        
        # ========== 退市股票检查 ==========
        stock_name = stock_names.get(code_normalized, "")
        if is_delisted(stock_name):
            delisted_count += 1
            continue  # 跳过退市股票
        
        # 获取Buffett指标
        buffett_metrics = get_buffett_metrics(buffett_df, code_normalized)
        
        # 获取财务指标 (用于ROE、净利率、毛利率等)
        fin_metrics = get_financial_metrics(financial_df, code_normalized)
        
        # 合并指标 - 优先使用财务数据的计算结果
        merged_metrics = buffett_metrics.copy() if buffett_metrics else {}
        if fin_metrics:
            # 用财务数据覆盖Buffett数据中的对应指标
            for k, v in fin_metrics.items():
                if v != 0 and v is not None:  # 优先使用有值的数据
                    merged_metrics[k] = v
            # 如果Buffett没有但财务有，也添加
            for k, v in fin_metrics.items():
                if k not in merged_metrics or merged_metrics[k] == 0:
                    merged_metrics[k] = v
        
        # 获取技术指标 (使用标准化6位代码)
        tech_file = os.path.join(TECH_DIR, f"{code_normalized}.csv")
        tech_df = None
        if os.path.exists(tech_file):
            tech_df = pd.read_csv(tech_file)
        
        # 计算各项得分
        tech_score, tech_details = get_technical_score(tech_df)
        buffett_score, buffett_details = calculate_buffett_score(merged_metrics)
        fund_score, fund_details = calculate_fundamental_score(merged_metrics)
        
        # 检查警告
        warnings_list = fund_details.get('warnings', [])
        if warnings_list:
            warning_count += 1
        
        # 综合得分 (加权)
        # 价值投资权重: Buffett(10) + 基本面(7) = 17 分 → 70%
        # 技术面权重: 技术(7) = 30%
        total_score = buffett_score + fund_score + tech_score * 0.5  # 技术面半权重
        
        # 保存结果
        result = {
            'code': code_normalized,
            'name': stock_name,
            'buffett_score': buffett_score,
            'fund_score': fund_score,
            'tech_score': tech_score,
            'total_score': total_score,
            'roe': merged_metrics.get('roe', 0),
            'gross_margin': merged_metrics.get('gross_margin', 0),
            'net_margin': merged_metrics.get('net_margin', 0),
            'debt_ratio': merged_metrics.get('debt_ratio', 0),
            'fcf': merged_metrics.get('fcf', 0),
            'net_income': merged_metrics.get('net_income', 0),
            'warnings': '; '.join(warnings_list) if warnings_list else '',
        }
        
        results.append(result)
    
    print(f"\n📊 筛选完成:")
    print(f"   跳过退市股票: {delisted_count} 只")
    print(f"   触发警告股票: {warning_count} 只")
    print(f"   有效股票: {len(results)} 只")
    
    # 排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 输出Top 20
    print("\n" + "=" * 80)
    print("🏆 价值投资评分 Top 20 (已过滤退市股票)")
    print("   评分体系: Buffett公式(10分) + 基本面(7分) + 技术面半权重")
    print("   ⚠️ 警告 = 异常财务数据，需仔细核实")
    print("=" * 80)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<10} {'Buffett':<10} {'基本面':<10} {'技术面':<8} {'综合':<8} {'ROE':<8} {'净利率':<8}")
    print("-" * 100)
    
    for i, r in enumerate(results[:20], 1):
        warnings_flag = " ⚠️" if r['warnings'] else ""
        print(f"{i:<4} {r['code']:<8} {r['name'][:8]:<10} {r['buffett_score']:<10.1f} {r['fund_score']:<10.1f} {r['tech_score']:<8.1f} {r['total_score']:<8.1f} {r['roe']:<8.1f}% {r['net_margin']:<8.1f}%{warnings_flag}")
    
    # Top 5 详细分析
    print("\n" + "=" * 80)
    print("📋 Top 5 详细评分")
    print("=" * 80)
    
    for i, r in enumerate(results[:5], 1):
        warnings_text = f"\n   ⚠️ 警告: {r['warnings']}" if r['warnings'] else ""
        print(f"\n🥇 第{i}名: {r['code']} {r['name']}{warnings_text}")
        print(f"   Buffett公式: {r['buffett_score']:.1f}/10")
        print(f"   基本面: {r['fund_score']:.1f}/7")
        print(f"   技术面: {r['tech_score']:.1f}/7 (半权重后: {r['tech_score']*0.5:.1f})")
        print(f"   综合得分: {r['total_score']:.1f}")
        print(f"   ─────────────────────────")
        print(f"   ROE: {r['roe']:.1f}% | 毛利率: {r['gross_margin']:.1f}% | 净利率: {r['net_margin']:.1f}%")
        print(f"   负债率: {r['debt_ratio']:.1f}% | 自由现金流: {r['fcf']:.2f}")
    
    # 排序
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 输出Top 200
    print("\n" + "=" * 100)
    print("🏆 价值投资评分 Top 200 (全A股筛选)")
    print("   评分体系: Buffett公式(10分) + 基本面(7分) + 技术面半权重")
    print("=" * 100)
    
    print(f"\n{'排名':<4} {'代码':<8} {'名称':<12} {'Buffett':<8} {'基本面':<8} {'技术面':<8} {'综合':<8} {'ROE':<6} {'净利率':<8} {'负债率':<6} {'状态':<4}")
    print("-" * 100)
    
    for i, r in enumerate(results[:200], 1):
        warnings_flag = "⚠️" if r['warnings'] else ""
        name = r.get('name', r['code'])
        print(f"{i:<4} {r['code']:<8} {name[:10]:<12} {r['buffett_score']:<8.1f} {r['fund_score']:<8.1f} {r['tech_score']:<8.1f} {r['total_score']:<8.1f} {r['roe']:<6.1f}% {r['net_margin']:<7.1f}% {r['debt_ratio']:<6.1f}% {warnings_flag}")
    
    # 保存完整结果
    output_file = os.path.join(OUTPUT_DIR, f"value_screening_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    save_df = pd.DataFrame(results)
    save_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 完整结果已保存: {output_file}")
    
    # 统计信息
    print("\n📊 评分分布统计")
    scores = [r['total_score'] for r in results]
    print(f"   最高分: {max(scores):.1f}")
    print(f"   最低分: {min(scores):.1f}")
    print(f"   平均分: {np.mean(scores):.1f}")
    print(f"   中位数: {np.median(scores):.1f}")
    
    # 筛选高分股票 (>15分)
    high_score = [r for r in results if r['total_score'] > 15]
    print(f"\n🎯 高分股票 (>15分): {len(high_score)} 只")

if __name__ == "__main__":
    main()
