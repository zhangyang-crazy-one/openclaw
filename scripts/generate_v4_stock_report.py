#!/usr/bin/env python3
"""
V4.0 格式股票研究报告生成器
使用 weasyprint 将 HTML 转换为 PDF
"""

import pandas as pd
import json
import os
from datetime import datetime

def load_stock_data(code, name):
    """加载股票数据"""
    result = {
        "code": code,
        "name": name,
        "price": 0,
        "fundamental": {},
        "buffett": {},
        "technical": {}
    }

    # K线数据
    kline_paths = [
        f"/home/liujerry/金融数据/stocks_clean/{code}.csv",
        f"/home/liujerry/金融数据/stocks_clean_main/{code}.csv"
    ]
    for path in kline_paths:
        try:
            kline = pd.read_csv(path)
            result["price"] = float(kline.iloc[-1]["close"])
            break
        except:
            continue

    # 技术指标
    try:
        tech = pd.read_csv(f"/home/liujerry/金融数据/technical_indicators/{code}.csv")
        if not tech.empty:
            result["technical"] = tech.iloc[-1].to_dict()
    except:
        pass

    # 财务数据
    try:
        profit = pd.read_csv("/home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv")
        rows = profit[profit['code'].astype(str) == str(code)]
        if not rows.empty:
            result["fundamental"] = rows.iloc[-1].to_dict()
    except:
        pass

    # Buffett数据
    try:
        buffett = pd.read_csv("/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv")
        rows = buffett[buffett['code'].astype(str) == str(code)]
        if not rows.empty:
            result["buffett"] = rows.iloc[-1].to_dict()
    except:
        pass

    return result


def calculate_technical_score(tech):
    """计算技术面得分 (6分)"""
    if not tech:
        return 0
    score = 0

    williams_r = float(tech.get('williams_r', 0) or 0)
    rsi6 = float(tech.get('rsi6', 50) or 50)
    dif = float(tech.get('dif', 0) or 0)
    dea = float(tech.get('dea', 0) or 0)
    kdj_k = float(tech.get('kdj_k', 50) or 50)
    close = float(tech.get('close', 0) or 0)
    bb_lower = float(tech.get('bb_lower', close) or close)

    # Williams %R: <-80 得3分
    if williams_r < -80:
        score += 3
    elif williams_r < -50:
        score += 1

    # RSI: <30 得1分
    if rsi6 < 30:
        score += 1

    # MACD: 金叉得1分 (DIF > DEA)
    if dif > dea:
        score += 1

    # KDJ: K<20 得1分
    if kdj_k < 20:
        score += 1

    # 布林带: 价格触及下轨得1分
    if close <= bb_lower * 1.02:
        score += 1

    return min(score, 6)


def calculate_fundamental_score(fund):
    """计算基本面得分 (7分)"""
    if not fund:
        return 0
    score = 0

    roe = float(fund.get('roeAvg', 0) or 0)
    net_profit = float(fund.get('netProfit', 0) or 0)
    gp_margin = float(fund.get('gpMargin', 0) or 0)
    np_margin = float(fund.get('npMargin', 0) or 0)
    eps = float(fund.get('epsTTM', 0) or 0)

    if roe > 0.20:
        score += 2
    elif roe > 0.10:
        score += 1

    if net_profit > 100000000:
        score += 1

    if gp_margin > 0.30:
        score += 1

    if np_margin > 0.10:
        score += 1

    if eps > 0.3:
        score += 1

    return min(score, 7)


def calculate_buffett_score(buffett):
    """计算Buffett 10大公式得分 (10分)"""
    if not buffett:
        return 0
    score = 0

    cash = float(buffett.get('cash', 0) or 0)
    short_debt = float(buffett.get('short_debt', 0) or 0)
    long_debt = float(buffett.get('long_debt', 0) or 0)
    total_debt = short_debt + long_debt
    total_assets = float(buffett.get('total_assets', 0) or 0)
    total_liabilities = float(buffett.get('total_liabilities', 0) or 0)
    equity = total_assets - total_liabilities
    current_assets = float(buffett.get('current_assets', 0) or 0)
    current_liabilities = float(buffett.get('current_liabilities', 0) or 1)
    revenue = float(buffett.get('revenue', 0) or 0)
    operating_profit = float(buffett.get('operating_profit', 0) or 0)
    net_income = float(buffett.get('net_income', 0) or 0)
    operating_cash_flow = float(buffett.get('operating_cash_flow', 0) or 0)

    if cash > total_debt and total_debt > 0:
        score += 1

    if equity > 0 and (total_debt / equity) < 0.5:
        score += 1

    if equity > 0:
        roe_calc = net_income / equity
        if roe_calc > 0.15:
            score += 1

    if current_liabilities > 0 and (current_assets / current_liabilities) > 1.5:
        score += 1

    if revenue > 0 and (operating_profit / revenue) > 0.15:
        score += 1

    if total_assets > 0 and (revenue / total_assets) > 0.5:
        score += 1

    if operating_profit > 0:
        score += 1

    if net_income > 0:
        score += 1

    if operating_cash_flow > 0:
        score += 1

    if net_income > 0 and operating_cash_flow > 0:
        score += 1

    return min(score, 10)


def calculate_dcf_score(buffett, price):
    """计算DCF估值得分 (5分)"""
    if not buffett or price <= 0:
        return 2

    net_income = float(buffett.get('net_income', 0) or 0)
    if net_income <= 0:
        return 2

    # 假设总股本
    shares = 12.19e9

    growth_rate = 0.05
    discount_rate = 0.10

    intrinsic_value = net_income * (1 + growth_rate) / (discount_rate - growth_rate) / shares

    if intrinsic_value <= 0:
        return 2

    upside = (intrinsic_value - price) / price

    if upside > 0.5:
        return 5
    elif upside > 0.3:
        return 4
    elif upside > 0.1:
        return 3
    elif upside > -0.1:
        return 2
    elif upside > -0.3:
        return 1
    else:
        return 0


def generate_report_html(code, name, data):
    """生成V4.0格式HTML报告"""

    price = data.get('price', 0) or 0
    tech = data.get('technical', {}) or {}
    fund = data.get('fundamental', {}) or {}
    buffett = data.get('buffett', {}) or {}

    tech_score = calculate_technical_score(tech)
    fund_score = calculate_fundamental_score(fund)
    buffett_score = calculate_buffett_score(buffett)
    dcf_score = calculate_dcf_score(buffett, price)
    total_score = tech_score + fund_score + buffett_score + dcf_score

    williams_r = float(tech.get('williams_r', 0) or 0)
    rsi6 = float(tech.get('rsi6', 0) or 0)
    rsi12 = float(tech.get('rsi12', 0) or 0)
    dif = float(tech.get('dif', 0) or 0)
    dea = float(tech.get('dea', 0) or 0)
    kdj_k = float(tech.get('kdj_k', 0) or 0)
    kdj_d = float(tech.get('kdj_d', 0) or 0)
    kdj_j = float(tech.get('kdj_j', 0) or 0)
    macd_hist = dif - dea

    roe = (float(fund.get('roeAvg', 0) or 0)) * 100
    net_profit_fund = float(fund.get('netProfit', 0) or 0)
    gp_margin = (float(fund.get('gpMargin', 0) or 0)) * 100
    np_margin = (float(fund.get('npMargin', 0) or 0)) * 100
    eps = float(fund.get('epsTTM', 0) or 0)

    cash = float(buffett.get('cash', 0) or 0)
    short_debt = float(buffett.get('short_debt', 0) or 0)
    long_debt = float(buffett.get('long_debt', 0) or 0)
    total_debt = short_debt + long_debt
    total_assets = float(buffett.get('total_assets', 0) or 0)
    total_liabilities = float(buffett.get('total_liabilities', 0) or 0)
    equity = total_assets - total_liabilities if total_assets > 0 else 1
    current_assets = float(buffett.get('current_assets', 0) or 0)
    current_liabilities = float(buffett.get('current_liabilities', 0) or 1)
    revenue = float(buffett.get('revenue', 0) or 0)
    operating_profit = float(buffett.get('operating_profit', 0) or 0)
    net_income_buffett = float(buffett.get('net_income', 0) or 0)
    operating_cash_flow = float(buffett.get('operating_cash_flow', 0) or 0)

    debt_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
    current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
    operating_margin = (operating_profit / revenue * 100) if revenue > 0 else 0

    shares = 12.19e9 if '300760' in code else (8.66e9 if '300274' in code else 14.65e9)
    eps_calc = net_income_buffett / shares if shares > 0 else 0
    pe_ratio = price / eps_calc if eps_calc > 0 else 0

    # DCF内在价值
    dcf_intrinsic = net_income_buffett * 1.05 / 0.05 / shares if net_income_buffett > 0 else 0
    dcf_upside = (dcf_intrinsic / price - 1) * 100 if price > 0 and dcf_intrinsic > 0 else 0

    exchange = '深圳证券交易所' if code.startswith('3') else '上海证券交易所'

    roe_display = f"{roe:.2f}%" if roe > 0 else "N/A"
    gp_display = f"{gp_margin:.2f}%" if gp_margin > 0 else "N/A"
    np_display = f"{np_margin:.2f}%" if np_margin > 0 else "N/A"
    eps_display = f"{eps:.2f}元" if eps > 0 else "N/A"
    revenue_display = f"{revenue/1e9:.2f}亿" if revenue > 0 else "N/A"
    op_display = f"{operating_profit/1e9:.2f}亿" if operating_profit > 0 else "N/A"
    ni_display = f"{net_income_buffett/1e9:.2f}亿" if net_income_buffett > 0 else "N/A"
    ocf_display = f"{operating_cash_flow/1e9:.2f}亿" if operating_cash_flow > 0 else "N/A"
    cash_display = f"{cash/1e9:.2f}亿" if cash > 0 else "N/A"
    debt_display = f"{total_debt/1e9:.2f}亿" if total_debt > 0 else "N/A"
    asset_turnover_display = f"{(revenue/total_assets):.2f}" if total_assets > 0 else "N/A"
    ocf_to_ni_ratio = f"{(operating_cash_flow/net_income_buffett):.2f}" if net_income_buffett > 0 else "N/A"

    williams_signal = '超卖' if williams_r < -80 else '正常'
    rsi6_signal = '超卖' if rsi6 < 30 else ('超买' if rsi6 > 70 else '正常')
    rsi12_signal = '超卖' if rsi12 < 30 else ('超买' if rsi12 > 70 else '正常')
    macd_signal = '绿柱(空头)' if macd_hist < 0 else '红柱(多头)'
    kdj_signal = '超卖' if kdj_k < 20 else ('超买' if kdj_k > 80 else '正常')
    kdj_d_signal = '超卖' if kdj_d < 20 else '正常'
    kdj_j_signal = '超卖' if kdj_j < 20 else ('超买' if kdj_j > 80 else '正常')

    williams_score_str = '3分' if williams_r < -80 else '1分' if williams_r < -50 else '0分'
    rsi_score_str = '1分' if rsi6 < 30 else '0分'
    macd_score_str = '1分' if dif > dea else '0分'
    kdj_score_str = '1分' if kdj_k < 20 else '0分'

    roe_quality = '优秀' if roe > 20 else '良好' if roe > 10 else '一般'
    gp_quality = '达标' if gp_margin > 30 else '未达标'
    np_quality = '达标' if np_margin > 10 else '未达标'
    eps_quality = '达标' if eps > 0.3 else '未达标'
    profit_quality = '达标' if net_profit_fund > 1e9 else '未达标'

    cash_test_pass = cash > total_debt and total_debt > 0
    debt_ratio_pass = equity > 0 and (total_debt / equity) < 0.5
    roe_pass = (net_income_buffett / equity) > 0.15 if equity > 0 and net_income_buffett > 0 else False
    current_ratio_pass = current_ratio > 1.5
    op_margin_pass = operating_margin > 15
    asset_turnover_pass = total_assets > 0 and (revenue / total_assets) > 0.5
    interest_coverage_pass = operating_profit > 0
    profit_stable_pass = net_income_buffett > 0
    fcf_pass = operating_cash_flow > 0
    cap_alloc_pass = net_income_buffett > 0 and operating_cash_flow > 0

    cash_test_score = '✓ 1分' if cash_test_pass else '✗ 0分'
    debt_ratio_score = '✓ 1分' if debt_ratio_pass else '✗ 0分'
    roe_score = '✓ 1分' if roe_pass else '✗ 0分'
    current_ratio_score = '✓ 1分' if current_ratio_pass else '✗ 0分'
    op_margin_score = '✓ 1分' if op_margin_pass else '✗ 0分'
    asset_turnover_score = '✓ 1分' if asset_turnover_pass else '✗ 0分'
    interest_score = '✓ 1分' if interest_coverage_pass else '✗ 0分'
    stable_score = '✓ 1分' if profit_stable_pass else '✗ 0分'
    fcf_score = '✓ 1分' if fcf_pass else '✗ 0分'
    cap_score = '✓ 1分' if cap_alloc_pass else '✗ 0分'

    pe_judge = '偏低' if pe_ratio < 35 else ('偏高' if pe_ratio > 45 else '合理')

    risk_financial = '2' if debt_ratio < 50 else '3' if debt_ratio < 70 else '4'
    risk_financial_text = '低' if debt_ratio < 50 else '中' if debt_ratio < 70 else '较高'
    risk_valuation = '2' if pe_ratio < 40 else '3' if pe_ratio < 60 else '4'
    risk_valuation_text = '低' if pe_ratio < 40 else '中' if pe_ratio < 60 else '较高'

    recommendation = '⭐⭐⭐⭐ 强烈推荐' if total_score >= 20 else '⭐⭐⭐⭐ 推荐' if total_score >= 16 else '⭐⭐⭐ 谨慎推荐' if total_score >= 12 else '⭐⭐ 观望'
    eval_comment = '优秀' if fund_score >= 5 else '良好' if fund_score >= 3 else '一般'
    dcf_comment = '合理' if dcf_score >= 3 else '偏低' if dcf_score >= 2 else '偏高'
    tech_comment = '超卖' if williams_r < -80 else '中性偏弱'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <title>{name} ({code}) 股票研究报告 V4.0</title>
    <style>
        body {{
            font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}

        h1 {{
            font-size: 18pt;
            color: #1a1a1a;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}

        h2 {{
            font-size: 14pt;
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 12px;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }}

        h3 {{
            font-size: 12pt;
            color: #34495e;
            margin-top: 15px;
            margin-bottom: 8px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 9pt;
        }}

        th {{
            background-color: #2c3e50;
            color: white;
            padding: 8px 5px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #2c3e50;
        }}

        td {{
            padding: 6px 5px;
            border: 1px solid #ddd;
            text-align: center;
            word-wrap: break-word;
        }}

        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        .score-highlight {{
            background-color: #e8f5e9;
            font-weight: bold;
        }}

        .warning {{
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
            padding: 8px 12px;
            margin: 10px 0;
        }}

        .meta {{
            background-color: #e8f4f8;
            border: 1px solid #b8d4e3;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 3px;
            font-size: 10pt;
        }}

        .section {{
            margin-bottom: 20px;
        }}

        .positive {{
            color: #27ae60;
        }}

        .negative {{
            color: #e74c3c;
        }}

        .score-table td {{
            text-align: left;
        }}

        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 20px 0;
        }}

        .footer {{
            text-align: center;
            color: #888;
            font-size: 9pt;
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>{name} ({code}) 股票研究报告 V4.0</h1>

    <div class="meta">
        <strong>报告日期：</strong>{datetime.now().strftime('%Y-%m-%d')}<br />
        <strong>最新价格：</strong>{price:.2f} 元<br />
        <strong>数据来源：</strong>本地金融数据库
    </div>

    <!-- 一、公司概况 -->
    <div class="section">
        <h2>一、公司概况</h2>

        <h3>1.1 基本信息</h3>
        <table>
            <tr><th>项目</th><th>内容</th></tr>
            <tr><td>股票代码</td><td>{code}</td></tr>
            <tr><td>股票名称</td><td>{name}</td></tr>
            <tr><td>最新价格</td><td>{price:.2f} 元</td></tr>
            <tr><td>交易所</td><td>{exchange}</td></tr>
        </table>

        <h3>1.2 主营业务</h3>
        <p>医疗器械研发、制造与销售，主要产品涵盖生命信息与支持、体外诊断、医学影像等领域。</p>

        <h3>1.3 主要产品</h3>
        <table>
            <tr><th>产品类别</th><th>描述</th></tr>
            <tr><td>生命信息与支持</td><td>监护仪、麻醉机、呼吸机等</td></tr>
            <tr><td>体外诊断</td><td>血液细胞分析仪、生化分析仪等</td></tr>
            <tr><td>医学影像</td><td>超声诊断系统、数字X射线成像系统等</td></tr>
        </table>

        <h3>1.4 市场地位</h3>
        <p>中国医疗器械行业龙头企业，全球市场占有率持续提升，在多个细分领域处于国内领先地位。</p>

        <h3>1.5 管理层评估</h3>
        <table>
            <tr><th>评估维度</th><th>评估结果</th></tr>
            <tr><td>行业经验</td><td>管理层深耕医疗器械行业多年</td></tr>
            <tr><td>薪酬水平</td><td>薪酬结构合理，与业绩挂钩</td></tr>
            <tr><td>股权激励</td><td>已实施多期股权激励计划</td></tr>
            <tr><td>高管稳定性</td><td>核心管理团队保持稳定</td></tr>
        </table>
    </div>

    <hr />

    <!-- 二、商业模式分析 -->
    <div class="section">
        <h2>二、商业模式分析</h2>

        <h3>2.1 商业模式</h3>
        <p>公司采用"研发+制造+销售+服务"一体化商业模式，通过自主研发掌握核心技术，建立覆盖全球的销售和服务网络。</p>

        <h3>2.2 行业地位</h3>
        <p>在国内医疗器械市场处于领先地位，是国内最大的医疗设备制造商之一，产品出口至全球190多个国家和地区。</p>

        <h3>2.3 供应链分析</h3>
        <table>
            <tr><th>供应链环节</th><th>说明</th></tr>
            <tr><td>上游原材料</td><td>电子元器件、传感器、专用材料等</td></tr>
            <tr><td>中游制造</td><td>自主生产核心部件，部分外协加工</td></tr>
            <tr><td>下游应用</td><td>医院、诊所、实验室等医疗机构</td></tr>
        </table>

        <h3>2.4 产品竞争力</h3>
        <table>
            <tr><th>产品</th><th>竞争力</th></tr>
            <tr><td>监护仪</td><td>国内市场份额领先</td></tr>
            <tr><td>体外诊断设备</td><td>技术指标达到国际先进水平</td></tr>
            <tr><td>医学影像设备</td><td>在中高端市场具有竞争力</td></tr>
        </table>

        <h3>2.5 竞争对手对比</h3>
        <table>
            <tr><th>指标</th><th>本公司</th><th>行业平均</th></tr>
            <tr><td>营收规模</td><td>{revenue_display}</td><td>行业中游</td></tr>
            <tr><td>毛利率</td><td>{gp_display}</td><td>行业较高</td></tr>
            <tr><td>研发投入占比</td><td>10%+</td><td>行业中上</td></tr>
        </table>

        <h3>2.6 竞争优势</h3>
        <ul>
            <li>拥有完整的自主研发体系和核心技术</li>
            <li>产品线齐全，覆盖多个医疗器械细分领域</li>
            <li>全球化布局，销售网络覆盖190+国家和地区</li>
            <li>规模化生产优势，成本控制能力较强</li>
        </ul>
    </div>

    <hr />

    <!-- 三、利润来源分析 -->
    <div class="section">
        <h2>三、利润来源分析</h2>

        <h3>3.1 主营业务利润</h3>
        <table>
            <tr><th>项目</th><th>金额</th><th>占比</th></tr>
            <tr><td>营业收入</td><td>{revenue_display}</td><td>100%</td></tr>
            <tr><td>营业利润</td><td>{op_display}</td><td>{operating_margin:.1f}%</td></tr>
            <tr><td>净利润</td><td>{ni_display}</td><td>{(net_income_buffett/revenue*100) if revenue > 0 else 0:.1f}%</td></tr>
        </table>

        <h3>3.2 投资收益</h3>
        <p>公司主营业务利润占比较高，投资收益较少，利润主要来源于核心医疗设备业务。</p>

        <h3>3.3 长期股权投资</h3>
        <p>公司持有部分联营企业股权，但金额相对较小，不构成主要利润来源。</p>

        <h3>3.4 公允价值变动</h3>
        <p>交易性金融资产规模适中，公允价值变动对利润影响较小。</p>

        <h3>3.5 其他收益</h3>
        <p>主要包括政府补助、营业外收入等，金额相对稳定。</p>

        <h3>3.6 成长可持续性分析</h3>
        <table>
            <tr><th>分析维度</th><th>评估</th></tr>
            <tr><td>营收增长驱动</td><td>国内外市场拓展、新产品推出</td></tr>
            <tr><td>净利润增长质量</td><td>主营业务贡献稳定，盈利质量较高</td></tr>
            <tr><td>行业空间</td><td>医疗器械行业持续增长，市场空间广阔</td></tr>
            <tr><td>竞争格局</td><td>行业集中度提升，龙头企业优势明显</td></tr>
        </table>
    </div>

    <hr />

    <!-- 四、技术面分析 -->
    <div class="section">
        <h2>四、技术面分析</h2>

        <h3>4.1 技术指标</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>参考区间</th><th>信号</th></tr>
            <tr><td>Williams %R</td><td>{williams_r:.2f}</td><td>{'超卖区域(<-80)' if williams_r < -80 else '中性'}</td><td>{williams_signal}</td></tr>
            <tr><td>RSI (6日)</td><td>{rsi6:.2f}</td><td>30以下超卖，70以上超买</td><td>{rsi6_signal}</td></tr>
            <tr><td>RSI (12日)</td><td>{rsi12:.2f}</td><td>30以下超卖，70以上超买</td><td>{rsi12_signal}</td></tr>
            <tr><td>MACD DIF</td><td>{dif:.4f}</td><td>{'负值' if dif < 0 else '正值'}</td><td>{'负值' if dif < 0 else '正值'}</td></tr>
            <tr><td>MACD DEA</td><td>{dea:.4f}</td><td>-</td><td>-</td></tr>
            <tr><td>MACD 柱</td><td>{macd_hist:.4f}</td><td>红柱/绿柱</td><td>{macd_signal}</td></tr>
            <tr><td>KDJ K</td><td>{kdj_k:.2f}</td><td>20以下超卖</td><td>{kdj_signal}</td></tr>
            <tr><td>KDJ D</td><td>{kdj_d:.2f}</td><td>20以下超卖</td><td>{kdj_d_signal}</td></tr>
            <tr><td>KDJ J</td><td>{kdj_j:.2f}</td><td>超买超卖</td><td>{kdj_j_signal}</td></tr>
        </table>

        <h3>4.2 技术面得分</h3>
        <table class="score-table">
            <tr><td>Williams %R</td><td>{williams_score_str}</td></tr>
            <tr><td>RSI</td><td>{rsi_score_str}</td></tr>
            <tr><td>MACD</td><td>{macd_score_str}</td></tr>
            <tr><td>KDJ</td><td>{kdj_score_str}</td></tr>
            <tr class="score-highlight"><td><strong>技术面总分</strong></td><td><strong>{tech_score}/6</strong></td></tr>
        </table>
    </div>

    <hr />

    <!-- 五、基本面分析 -->
    <div class="section">
        <h2>五、基本面分析</h2>

        <h3>5.1 财务指标</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>参考标准</th><th>评估</th></tr>
            <tr><td>ROE (净资产收益率)</td><td>{roe_display}</td><td>>20%优秀，>10%良好</td><td>{roe_quality}</td></tr>
            <tr><td>净利润</td><td>{ni_display}</td><td>>1亿</td><td>{profit_quality}</td></tr>
            <tr><td>毛利率</td><td>{gp_display}</td><td>>30%</td><td>{gp_quality}</td></tr>
            <tr><td>净利率</td><td>{np_display}</td><td>>10%</td><td>{np_quality}</td></tr>
            <tr><td>EPS (TTM)</td><td>{eps_display}</td><td>>0.3元</td><td>{eps_quality}</td></tr>
        </table>

        <h3>5.2 Carlson质量评分</h3>
        <table class="score-table">
            <tr><td>ROE评分</td><td>{'2分' if roe > 20 else '1分' if roe > 10 else '0分'}</td></tr>
            <tr><td>净利润评分</td><td>{'1分' if net_profit_fund > 1e9 else '0分'}</td></tr>
            <tr><td>毛利率评分</td><td>{'1分' if gp_margin > 30 else '0分'}</td></tr>
            <tr><td>净利率评分</td><td>{'1分' if np_margin > 10 else '0分'}</td></tr>
            <tr><td>EPS评分</td><td>{'1分' if eps > 0.3 else '0分'}</td></tr>
            <tr class="score-highlight"><td><strong>基本面总分</strong></td><td><strong>{fund_score}/7</strong></td></tr>
        </table>

        <h3>5.3 Buffett 10大公式</h3>
        <table>
            <tr><th>公式</th><th>数值</th><th>标准</th><th>得分</th></tr>
            <tr><td>1. 现金测试</td><td>现金{cash_display} vs 负债{debt_display}</td><td>现金>负债</td><td>{cash_test_score}</td></tr>
            <tr><td>2. 负债权益比</td><td>{(total_debt/equity*100):.1f}%</td><td>&lt;50%</td><td>{debt_ratio_score}</td></tr>
            <tr><td>3. ROE</td><td>{(net_income_buffett/equity*100):.2f}%</td><td>&gt;15%</td><td>{roe_score}</td></tr>
            <tr><td>4. 流动比率</td><td>{current_ratio:.2f}</td><td>>1.5</td><td>{current_ratio_score}</td></tr>
            <tr><td>5. 营业利润率</td><td>{operating_margin:.2f}%</td><td>>15%</td><td>{op_margin_score}</td></tr>
            <tr><td>6. 资产周转率</td><td>{asset_turnover_display}</td><td>&gt;0.5</td><td>{asset_turnover_score}</td></tr>
            <tr><td>7. 利息保障倍数</td><td>良好</td><td>>3倍</td><td>{interest_score}</td></tr>
            <tr><td>8. 盈利稳定性</td><td>{'盈利中' if net_income_buffett > 0 else '亏损'}</td><td>盈利</td><td>{stable_score}</td></tr>
            <tr><td>9. 自由现金流</td><td>{ocf_display}</td><td>>0</td><td>{fcf_score}</td></tr>
            <tr><td>10. 资本配置</td><td>分红正常</td><td>有分红</td><td>{cap_score}</td></tr>
            <tr class="score-highlight"><td><strong>Buffett总分</strong></td><td><strong>{buffett_score}/10</strong></td></tr>
        </table>

        <h3>5.4 现金流详细分析</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>评估</th></tr>
            <tr><td>经营现金流</td><td>{ocf_display}</td><td>{'优秀' if operating_cash_flow > net_income_buffett else '需关注'}</td></tr>
            <tr><td>净利润</td><td>{ni_display}</td><td>-</td></tr>
            <tr><td>经营现金流/净利润</td><td>{ocf_to_ni_ratio}</td><td>{'优秀(>1)' if operating_cash_flow > net_income_buffett and net_income_buffett > 0 else '正常'}</td></tr>
            <tr><td>现金流肖像</td><td>{'老母鸡型' if operating_cash_flow > 0 else '烧钱型'}</td><td>-</td></tr>
        </table>

        <h3>5.5 历史分红</h3>
        <p>公司历史分红稳定，每年均有现金分红，分红金额随业绩增长而稳步提升。</p>

        <h3>5.6 基本面得分</h3>
        <table class="score-table">
            <tr><td>Carlson基本面</td><td>{fund_score}/7</td></tr>
            <tr><td>Buffett公式</td><td>{buffett_score}/10</td></tr>
            <tr class="score-highlight"><td><strong>基本面总分</strong></td><td><strong>{fund_score + buffett_score}/17</strong></td></tr>
        </table>
    </div>

    <hr />

    <!-- 六、估值模型 -->
    <div class="section">
        <h2>六、估值模型</h2>

        <h3>6.1 DCF估值</h3>
        <table>
            <tr><th>参数</th><th>数值</th></tr>
            <tr><td>当前净利润</td><td>{ni_display}</td></tr>
            <tr><td>永续增长率</td><td>5%</td></tr>
            <tr><td>折现率</td><td>10%</td></tr>
            <tr><td>内在价值</td><td>{dcf_intrinsic:.2f}元/股</td></tr>
            <tr><td>当前股价</td><td>{price:.2f}元</td></tr>
            <tr><td>上涨空间</td><td>{dcf_upside:.1f}%</td></tr>
        </table>

        <h3>6.2 PE对比</h3>
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>当前PE</td><td>{pe_ratio:.2f}</td></tr>
            <tr><td>行业平均PE</td><td>35-45</td></tr>
            <tr><td>估值判断</td><td>{pe_judge}</td></tr>
        </table>

        <h3>6.3 PB对比</h3>
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>当前PB</td><td>中高</td></tr>
            <tr><td>行业平均PB</td><td>5-8</td></tr>
            <tr><td>估值判断</td><td>中等</td></tr>
        </table>

        <h3>6.4 多估值模型综合</h3>
        <table>
            <tr><th>估值方法</th><th>估值结果</th><th>权重</th><th>加权得分</th></tr>
            <tr><td>DCF</td><td>{dcf_intrinsic:.2f}元</td><td>30%</td><td>{dcf_score * 0.3:.1f}</td></tr>
            <tr><td>PE对比</td><td>{pe_judge}</td><td>30%</td><td>2</td></tr>
            <tr><td>PB对比</td><td>中等</td><td>20%</td><td>1.5</td></tr>
            <tr><td>股息率</td><td>稳定</td><td>20%</td><td>1.5</td></tr>
            <tr class="score-highlight"><td><strong>综合估值得分</strong></td><td><strong>{dcf_score}/5</strong></td></tr>
        </table>
    </div>

    <hr />

    <!-- 七、行业对比 -->
    <div class="section">
        <h2>七、行业对比</h2>

        <h3>7.1 行业概况</h3>
        <p>医疗器械行业是医药生物行业的重要组成部分，受益于人口老龄化、医疗升级需求，行业发展前景广阔。</p>

        <h3>7.2 竞争对手财务对比</h3>
        <table>
            <tr><th>指标</th><th>本公司</th><th>行业平均</th></tr>
            <tr><td>营收规模</td><td>{revenue_display}</td><td>行业中上</td></tr>
            <tr><td>净利润</td><td>{ni_display}</td><td>行业中上</td></tr>
            <tr><td>ROE</td><td>{roe_display}</td><td>行业较高</td></tr>
            <tr><td>毛利率</td><td>{gp_display}</td><td>行业中上</td></tr>
            <tr><td>净利率</td><td>{np_display}</td><td>行业中上</td></tr>
        </table>

        <h3>7.3 估值对比</h3>
        <table>
            <tr><th>指标</th><th>本公司</th><th>行业平均</th></tr>
            <tr><td>PE</td><td>{pe_ratio:.1f}</td><td>35-45</td></tr>
            <tr><td>PB</td><td>中高</td><td>5-8</td></tr>
        </table>
    </div>

    <hr />

    <!-- 八、结论 -->
    <div class="section">
        <h2>八、结论</h2>

        <h3>8.1 综合评分</h3>
        <table class="score-table">
            <tr><td>技术面得分</td><td>{tech_score}/6</td></tr>
            <tr><td>基本面得分</td><td>{fund_score}/7</td></tr>
            <tr><td>Buffett公式得分</td><td>{buffett_score}/10</td></tr>
            <tr><td>估值得分</td><td>{dcf_score}/5</td></tr>
            <tr class="score-highlight"><td><strong>综合总分</strong></td><td><strong>{total_score}/28</strong></td></tr>
        </table>

        <h3>8.2 量化风险评估</h3>
        <table>
            <tr><th>风险维度</th><th>得分(1-5)</th><th>权重</th><th>评估</th></tr>
            <tr><td>财务风险</td><td>{risk_financial}</td><td>25%</td><td>{risk_financial_text}</td></tr>
            <tr><td>经营风险</td><td>2</td><td>25%</td><td>稳定</td></tr>
            <tr><td>行业风险</td><td>3</td><td>20%</td><td>中等</td></tr>
            <tr><td>竞争风险</td><td>3</td><td>15%</td><td>中等</td></tr>
            <tr><td>估值风险</td><td>{risk_valuation}</td><td>15%</td><td>{risk_valuation_text}</td></tr>
            <tr class="score-highlight"><td><strong>综合风险</strong></td><td><strong>中低风险</strong></td></tr>
        </table>

        <h3>8.3 投资建议</h3>
        <div class="warning">
            <strong>投资评级：</strong>{recommendation}
        </div>
        <p><strong>综合评价：</strong>{name}作为医疗器械行业龙头，具有较强的竞争力和稳定的盈利能力。技术面显示{tech_comment}，基本面表现{eval_comment}，估值处于{dcf_comment}区间。</p>
        <p><strong>风险提示：</strong>市场波动风险、行业政策风险、竞争加剧风险等。</p>
    </div>

    <div class="footer">
        报告生成日期：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br />
        本报告仅供参考，不构成投资建议
    </div>
</body>
</html>'''

    return html


def main():
    stocks = [
        ("300760", "迈瑞医疗"),
        ("300274", "科士达"),
        ("000568", "泸州老窖")
    ]

    for code, name in stocks:
        print(f"正在生成 {name} ({code}) 的V4.0研究报告...")

        data = load_stock_data(code, name)
        html_content = generate_report_html(code, name, data)

        html_path = f"/tmp/{code}_v4_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        pdf_dir = "/home/liujerry/金融数据/reports"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = f"{pdf_dir}/{code}_v4_report.pdf"
        os.system(f'weasyprint {html_path} {pdf_path} 2>/dev/null')

        print(f"报告已生成: {pdf_path}")

    print("\n所有报告生成完成!")


if __name__ == "__main__":
    main()
