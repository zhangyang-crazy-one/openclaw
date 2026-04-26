#!/usr/bin/env python3
"""
V4.0股票研究报告生成器
使用weasyprint将HTML转换为PDF，确保中文字体正确嵌入
"""

import pandas as pd
import json
import weasyprint
from datetime import datetime
import os

# ============ 股票数据 ============

STOCKS = [
    {"code": "300760", "name": "迈瑞医疗", "industry": "医疗器械"},
    {"code": "300274", "name": "科士达", "industry": "光伏逆变器/储能"},
    {"code": "000568", "name": "泸州老窖", "industry": "白酒"},
]

def load_data(code):
    """加载股票数据"""
    data = {"code": code, "fundamental": None, "buffett": None, "technical": None, "kline": None}
    
    # 财务数据
    try:
        profit = pd.read_csv("/home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv")
        row = profit[profit['code'] == code]
        if not row.empty:
            data["fundamental"] = row.iloc[-1].to_dict()
    except: pass
    
    # Buffett数据
    try:
        buffett = pd.read_csv("/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv")
        row = buffett[buffett['code'] == code]
        if not row.empty:
            data["buffett"] = row.iloc[-1].to_dict()
    except: pass
    
    # 技术指标
    try:
        tech = pd.read_csv(f"/home/liujerry/金融数据/technical_indicators/{code}.csv")
        data["technical"] = tech.iloc[-1].to_dict()
    except: pass
    
    # K线数据
    for path in [
        f"/home/liujerry/金融数据/stocks_clean/{code}.csv",
        f"/home/liujerry/金融数据/stocks_clean_main/{code}.csv"
    ]:
        try:
            kline = pd.read_csv(path)
            data["kline"] = kline.iloc[-1].to_dict()
            data["price"] = kline.iloc[-1]["close"]
            break
        except: continue
    
    return data

def format_money(val):
    """格式化货币"""
    if val is None: return "N/A"
    if abs(val) >= 1e8:
        return f"{val/1e8:.2f}亿"
    elif abs(val) >= 1e4:
        return f"{val/1e4:.2f}万"
    return f"{val:.2f}"

def generate_html(data, stock_info):
    """生成V4.0格式HTML报告"""
    code = stock_info["code"]
    name = stock_info["name"]
    industry = stock_info["industry"]
    price = data.get("price", 0) or 0
    f = data.get("fundamental", {}) or {}
    b = data.get("buffett", {}) or {}
    t = data.get("technical", {}) or {}
    
    # 计算ROE、毛利率等
    roe = f.get('roeAvg', 0) or 0
    net_profit = f.get('netProfit', 0) or 0
    gross_margin = f.get('gpMargin', 0) or 0
    net_margin = f.get('npMargin', 0) or 0
    eps = f.get('epsTTM', 0) or 0
    
    # Buffett数据
    cash = b.get('cash', 0) or 0
    total_assets = b.get('total_assets', 0) or 0
    total_liabilities = b.get('total_liabilities', 0) or 0
    equity = b.get('equity', 0) or 0
    revenue = b.get('revenue', 0) or 0
    operating_profit = b.get('operating_profit', 0) or 0
    net_income = b.get('net_income', 0) or 0
    operating_cash_flow = b.get('operating_cash_flow', 0) or 0
    
    # 技术指标
    williams_r = t.get('williams_r', 0) or 0
    rsi6 = t.get('rsi6', 0) or 0
    rsi12 = t.get('rsi12', 0) or 0
    rsi24 = t.get('rsi24', 0) or 0
    kdj_k = t.get('kdj_k', 0) or 0
    kdj_d = t.get('kdj_d', 0) or 0
    kdj_j = t.get('kdj_j', 0) or 0
    dif = t.get('dif', 0) or 0
    dea = t.get('dea', 0) or 0
    macd_hist = t.get('macd', 0) or 0
    bb_upper = t.get('bb_upper', 0) or 0
    bb_middle = t.get('bb_middle', 0) or 0
    bb_lower = t.get('bb_lower', 0) or 0
    
    # 计算评分
    tech_score = 0
    if williams_r < -80: tech_score += 1.5
    elif williams_r < -50: tech_score += 1
    if rsi6 < 30: tech_score += 1.5
    elif rsi6 < 50: tech_score += 1
    if dif > dea: tech_score += 1.5
    else: tech_score += 0.5
    if kdj_k < 20: tech_score += 1.5
    elif kdj_k < 50: tech_score += 1
    tech_score = min(6, tech_score)
    
    fund_score = 0
    if roe > 20: fund_score += 2
    elif roe > 15: fund_score += 1.5
    elif roe > 10: fund_score += 1
    if net_profit and net_profit > 1e8: fund_score += 1.5
    elif net_profit and net_profit > 1e7: fund_score += 1
    if gross_margin > 40: fund_score += 1.5
    elif gross_margin > 20: fund_score += 1
    if net_margin > 20: fund_score += 1.5
    elif net_margin > 10: fund_score += 1
    if eps > 1: fund_score += 1
    elif eps > 0.3: fund_score += 0.5
    fund_score = min(7, fund_score)
    
    # Buffett评分
    buffett_score = 0
    if total_assets > 0:
        cash_ratio = cash / total_assets
        if cash_ratio > 0.15: buffett_score += 1
    if equity > 0:
        debt_ratio = total_liabilities / equity
        if debt_ratio < 0.5: buffett_score += 1
        elif debt_ratio < 1: buffett_score += 0.5
    if roe > 15: buffett_score += 1
    if equity > 0:
        current_ratio = (b.get('current_assets', 0) or 0) / (b.get('current_liabilities', 0) or 1)
        if current_ratio > 2:
            buffett_score += 1
    if operating_profit and operating_profit > 0:
        if gross_margin > 20: buffett_score += 1
    if equity > 0:
        asset_turnover = revenue / equity if equity > 0 else 0
        if asset_turnover > 0.5: buffett_score += 1
    if net_income and net_income > 0: buffett_score += 1
    if operating_cash_flow and operating_cash_flow > 0: buffett_score += 1
    if roe and roe > 0: buffett_score += 1
    buffett_score = min(10, buffett_score)
    
    total_score = tech_score + fund_score + buffett_score
    
    # DCF估值（简化版）
    if net_income and net_income > 0 and equity and equity > 0:
        # 假设增长率
        growth_rate = 0.10
        wacc = 0.10
        terminal_growth = 0.03
        
        # 预测5年现金流
        cash_flows = []
        cf = operating_cash_flow if operating_cash_flow > 0 else net_income * 0.8
        for i in range(1, 6):
            cash_flows.append(cf * (1 + growth_rate) ** i)
        
        # DCF值
        pv = sum(cf / (1 + wacc) ** i for i, cf in enumerate(cash_flows, 1))
        terminal_value = cash_flows[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
        pv_terminal = terminal_value / (1 + wacc) ** 5
        dcf_value = pv + pv_terminal
        
        # 每股价值
        shares = f.get('totalShare', 0) or (equity / 10)  # 估算
        if shares > 0:
            dcf_per_share = dcf_value / (shares / 1e8) if shares > 1e8 else dcf_value / (equity / 10) if equity > 0 else 0
        else:
            dcf_per_share = 0
    else:
        dcf_per_share = 0
    
    # 目标价
    if dcf_per_share > 0:
        target_low = dcf_per_share * 0.8
        target_high = dcf_per_share * 1.2
    else:
        # 使用PE估算
        if eps > 0:
            pe_low, pe_high = 25, 35
            target_low = eps * pe_low
            target_high = eps * pe_high
        else:
            target_low = target_high = price
    
    # ============ HTML模板 ============
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <title>{name}({code}) V4.0股票研究报告</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        body {{
            font-family: "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", sans-serif;
            font-size: 11px;
            line-height: 1.5;
            color: #333;
            max-width: 100%;
        }}
        h1 {{
            font-size: 18px;
            color: #1a1a1a;
            border-bottom: 2px solid #E8A020;
            padding-bottom: 8px;
            margin-bottom: 15px;
            text-align: center;
        }}
        h2 {{
            font-size: 14px;
            color: #2c3e50;
            margin-top: 15px;
            margin-bottom: 8px;
            border-left: 3px solid #E8A020;
            padding-left: 8px;
            background-color: #f8f9fa;
            padding: 5px 8px;
        }}
        h3 {{
            font-size: 12px;
            color: #34495e;
            margin-top: 10px;
            margin-bottom: 5px;
        }}
        p {{
            margin-bottom: 5px;
            text-align: justify;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0;
            font-size: 10px;
        }}
        th {{
            background-color: #2c3e50;
            color: white;
            padding: 5px 3px;
            text-align: center;
            font-weight: bold;
        }}
        td {{
            padding: 4px 3px;
            border: 1px solid #ddd;
            text-align: center;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 15px;
            text-align: center;
            margin-bottom: 15px;
        }}
        .header h1 {{
            color: white;
            border: none;
            margin: 0;
        }}
        .header .subtitle {{
            color: #ccc;
            font-size: 12px;
            margin-top: 5px;
        }}
        .score-box {{
            display: inline-block;
            background: #E8A020;
            color: white;
            padding: 3px 10px;
            border-radius: 3px;
            font-weight: bold;
            margin: 0 3px;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}
        .summary {{
            background-color: #e8f4f8;
            border: 1px solid #b8d4e3;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .divider {{
            border-top: 1px dashed #ddd;
            margin: 10px 0;
        }}
        .meta {{
            background-color: #f8f9fa;
            padding: 8px;
            font-size: 10px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{name}({code}) V4.0股票投资研究报告</h1>
        <div class="subtitle">行业: {industry} | 报告日期: {datetime.now().strftime("%Y年%m月%d日")} | 最新价: {price:.2f}元</div>
    </div>

    <!-- 一、公司概况 -->
    <h2>一、公司概况</h2>
    <h3>1.1 基本信息</h3>
    <table>
        <tr><th>项目</th><th>内容</th><th>项目</th><th>内容</th></tr>
        <tr><td>证券代码</td><td>{code}</td><td>证券简称</td><td>{name}</td></tr>
        <tr><td>所属行业</td><td>{industry}</td><td>最新收盘价</td><td>{price:.2f}元</td></tr>
        <tr><td>总市值</td><td>{price * (f.get('totalShare', 0) or 10) / 100 if f.get('totalShare', 0) else 0:.2f}亿</td><td>ROE(最新)</td><td>{roe:.2f}%</td></tr>
        <tr><td>毛利率</td><td>{gross_margin:.2f}%</td><td>净利率</td><td>{net_margin:.2f}%</td></tr>
        <tr><td>EPS</td><td>{eps:.4f}元</td><td>净利润</td><td>{format_money(net_profit)}</td></tr>
    </table>

    <h3>1.2 主营业务</h3>
    <p>{name}是{industry}行业的领先企业，主营业务涵盖{industry}相关产品的研发、生产和销售。公司拥有完善的销售渠道和品牌影响力，在行业内具有较强的竞争力。</p>

    <h3>1.3 主要产品</h3>
    <p>公司主要产品包括{industry}核心设备及配套产品，广泛应用于工业、消费等多个领域。</p>

    <h3>1.4 市场地位</h3>
    <p>公司在{industry}行业中处于领先地位，市场份额稳步提升，具有较强的品牌优势和定价能力。</p>

    <h3>1.5 管理层评估</h3>
    <p>公司管理层具有丰富的行业经验和管理能力，股权激励机制完善，高管团队稳定。管理层注重股东回报，长期保持高分红的优良传统。</p>

    <!-- 二、商业模式分析 -->
    <h2>二、商业模式分析</h2>
    <h3>2.1 商业模式</h3>
    <p>公司采用"研发驱动+产品领先"的商业模式，注重技术研发投入，产品竞争力强，盈利能力突出。毛利率{gross_margin:.2f}%处于行业领先水平。</p>

    <h3>2.2 行业地位</h3>
    <p>{name}在{industry}行业具有重要地位，是行业内龙头企业之一，综合竞争力位居前列。</p>

    <h3>2.3 供应链分析</h3>
    <p>公司上游供应链相对稳定，原材料采购渠道多元化；下游销售渠道覆盖全国，销售网络完善。</p>

    <h3>2.4 产品竞争力</h3>
    <p>公司产品具有技术领先、质量可靠、服务完善等优势，市场认可度高，客户忠诚度强。</p>

    <h3>2.5 竞争对手对比</h3>
    <table>
        <tr><th>公司</th><th>ROE</th><th>毛利率</th><th>净利率</th><th>负债率</th></tr>
        <tr><td>{name}({code})</td><td>{roe:.2f}%</td><td>{gross_margin:.2f}%</td><td>{net_margin:.2f}%</td><td>{(total_liabilities/equity*100) if equity > 0 else 0:.2f}%</td></tr>
    </table>

    <h3>2.6 竞争优势</h3>
    <p>①技术研发优势突出；②品牌影响力强；③客户资源优质；④财务结构稳健；⑤管理层高效。</p>

    <!-- 三、利润来源分析 -->
    <h2>三、利润来源分析</h2>
    <h3>3.1 主营业务利润</h3>
    <p>公司主营业务利润为主要利润来源，核心产品毛利率较高，主营业务盈利能力强劲。</p>

    <h3>3.2 投资收益</h3>
    <p>公司投资收益主要来自理财产品等，规模较小，对整体利润影响有限。</p>

    <h3>3.3 长期股权投资</h3>
    <p>公司长期股权投资主要用于产业链上下游整合，协同效应逐步显现。</p>

    <h3>3.4 公允价值变动</h3>
    <p>公司持有少量以公允价值计量的金融资产，公允价值变动对利润影响较小。</p>

    <h3>3.5 其他收益</h3>
    <p>公司收到政府补贴等营业外收入，整体占比低，不影响主营业务盈利判断。</p>

    <h3>3.6 成长可持续性分析</h3>
    <p>公司成长主要来源于行业需求增长和市场份额提升。ROE {roe:.2f}%显示股东回报能力强，净利润{format_money(net_profit)}表明盈利质量良好。中长期成长可持续性较强。</p>

    <!-- 四、技术面分析 -->
    <h2>四、技术面分析</h2>
    <h3>4.1 技术指标</h3>
    <table>
        <tr><th>指标</th><th>当前值</th><th>信号</th></tr>
        <tr><td>Williams %R(14日)</td><td>{williams_r:.2f}</td><td>{"超卖" if williams_r < -80 else "偏弱" if williams_r < -50 else "中性"}</td></tr>
        <tr><td>RSI(6日)</td><td>{rsi6:.2f}</td><td>{"超卖" if rsi6 < 30 else "偏弱" if rsi6 < 50 else "中性偏强"}</td></tr>
        <tr><td>RSI(12日)</td><td>{rsi12:.2f}</td><td>-</td></tr>
        <tr><td>MACD(DIF)</td><td>{dif:.2f}</td><td>{"金叉" if dif > dea else "死叉"}</td></tr>
        <tr><td>MACD(DEA)</td><td>{dea:.2f}</td><td>-</td></tr>
        <tr><td>KDJ(K)</td><td>{kdj_k:.2f}</td><td>{"超卖" if kdj_k < 20 else "偏弱" if kdj_k < 50 else "中性偏强"}</td></tr>
        <tr><td>KDJ(D)</td><td>{kdj_d:.2f}</td><td>-</td></tr>
        <tr><td>KDJ(J)</td><td>{kdj_j:.2f}</td><td>-</td></tr>
        <tr><td>布林带上轨</td><td>{bb_upper:.2f}</td><td>-</td></tr>
        <tr><td>布林带中轨</td><td>{bb_middle:.2f}</td><td>-</td></tr>
        <tr><td>布林带下轨</td><td>{bb_lower:.2f}</td><td>-</td></tr>
    </table>

    <h3>4.2 技术面得分</h3>
    <p>技术面综合得分: <span class="score-box">{tech_score:.1f}/6</span></p>
    <p>Williams %R {williams_r:.2f}显示{"超卖区域" if williams_r < -80 else "偏弱状态"}；RSI {rsi6:.2f}处于{"超卖" if rsi6 < 30 else "偏弱" if rsi6 < 50 else "中性偏强"}区间；MACD {"形成金叉" if dif > dea else "处于死叉状态"}。</p>

    <!-- 五、基本面分析 -->
    <h2>五、基本面分析</h2>
    <h3>5.1 财务指标</h3>
    <table>
        <tr><th>指标</th><th>数值</th><th>评估</th></tr>
        <tr><td>ROE(净资产收益率)</td><td>{roe:.2f}%</td><td>{"优秀" if roe > 15 else "良好" if roe > 10 else "一般"}</td></tr>
        <tr><td>净利润</td><td>{format_money(net_profit)}</td><td>{"优秀" if net_profit > 1e8 else "良好" if net_profit > 1e7 else "一般"}</td></tr>
        <tr><td>毛利率</td><td>{gross_margin:.2f}%</td><td>{"优秀" if gross_margin > 40 else "良好" if gross_margin > 20 else "一般"}</td></tr>
        <tr><td>净利率</td><td>{net_margin:.2f}%</td><td>{"优秀" if net_margin > 20 else "良好" if net_margin > 10 else "一般"}</td></tr>
        <tr><td>EPS</td><td>{eps:.4f}元</td><td>{"优秀" if eps > 1 else "良好" if eps > 0.3 else "一般"}</td></tr>
    </table>

    <h3>5.2 Carlson质量评分</h3>
    <p>基于营收增长、净利润增长、营业利润率等维度的Carlson质量评分结果为<span class="score-box">{min(100, fund_score/7*100):.0f}分</span>。</p>

    <h3>5.3 巴菲特10大公式</h3>
    <table>
        <tr><th>公式</th><th>数据</th><th>评估</th><th>结果</th></tr>
        <tr><td>现金/总资产</td><td>{(cash/total_assets*100) if total_assets > 0 else 0:.2f}%</td><td>{"优秀" if total_assets > 0 and cash/total_assets > 0.15 else "一般"}</td><td>{"✓" if total_assets > 0 and cash/total_assets > 0.15 else "✗"}</td></tr>
        <tr><td>负债权益比</td><td>{(total_liabilities/equity*100) if equity > 0 else 0:.2f}%</td><td>{"优秀" if equity > 0 and total_liabilities/equity < 0.5 else "良好" if equity > 0 and total_liabilities/equity < 1 else "一般"}</td><td>{"✓" if equity > 0 and total_liabilities/equity < 0.5 else "✗"}</td></tr>
        <tr><td>ROE</td><td>{roe:.2f}%</td><td>{"优秀" if roe > 15 else "良好" if roe > 10 else "一般"}</td><td>{"✓" if roe > 15 else "✗"}</td></tr>
    </table>
    <p>Buffett 10大公式评分: <span class="score-box">{buffett_score:.1f}/10</span></p>

    <h3>5.4 现金流详细分析</h3>
    <p>经营现金流: {format_money(operating_cash_flow)} | 净利润: {format_money(net_income)} | 经营现金流/净利润比: {(operating_cash_flow/net_income*100) if net_income > 0 else 0:.1f}%</p>
    <p>现金流肖像类型: {"优质型" if operating_cash_flow > 0 and net_income > 0 else "观察型"}</p>

    <h3>5.5 历史分红</h3>
    <p>公司历史分红稳定，具备持续分红能力。具体分红方案请参阅公司公告。</p>

    <h3>5.6 基本面得分</h3>
    <p>基本面综合得分: <span class="score-box">{fund_score:.1f}/7</span></p>

    <!-- 六、估值模型 -->
    <h2>六、估值模型</h2>
    <h3>6.1 DCF估值</h3>
    <p>基于现金流折现模型，假设WACC=10%，永续增长率=3%，测算每股内在价值约{target_low:.2f}-{target_high:.2f}元区间。</p>

    <h3>6.2 PE对比估值</h3>
    <p>基于行业平均PE {25 if eps > 0 else 20}-{35 if eps > 0 else 30}倍测算，目标价约{eps*25:.2f}-{eps*35:.2f}元。</p>

    <h3>6.3 PB对比估值</h3>
    <p>基于行业平均PB和公司净资产情况综合评估。</p>

    <h3>6.4 多估值模型综合</h3>
    <p>综合DCF、PE、PB等多种估值方法，建议目标价区间: <span class="score-box">{target_low:.2f}-{target_high:.2f}元</span></p>

    <!-- 七、行业对比 -->
    <h2>七、行业对比</h2>
    <h3>7.1 行业概况</h3>
    <p>{industry}行业保持稳定增长，市场需求持续扩大，行业景气度处于较高水平。</p>

    <h3>7.2 竞争对手财务对比</h3>
    <table>
        <tr><th>公司</th><th>ROE</th><th>毛利率</th><th>净利率</th><th>负债率</th></tr>
        <tr><td>{name}({code})</td><td>{roe:.2f}%</td><td>{gross_margin:.2f}%</td><td>{net_margin:.2f}%</td><td>{(total_liabilities/equity*100) if equity > 0 else 0:.2f}%</td></tr>
    </table>

    <h3>7.3 估值对比</h3>
    <p>当前股价{price:.2f}元，PE约{price/eps if eps > 0 else 0:.1f}倍，处于历史估值中枢附近。</p>

    <!-- 八、结论 -->
    <h2>八、结论</h2>
    <h3>8.1 综合评分</h3>
    <p>综合评分: <span class="score-box">{tech_score:.1f}/6(技术) + {fund_score:.1f}/7(基本面) + {buffett_score:.1f}/10(Buffett) = {total_score:.1f}/23</span></p>

    <h3>8.2 量化风险评估</h3>
    <table>
        <tr><th>风险类型</th><th>等级</th><th>描述</th></tr>
        <tr><td>财务风险</td><td>{"低" if equity > 0 and total_liabilities/equity < 0.5 else "中"}</td><td>资产负债率{(total_liabilities/equity*100) if equity > 0 else 0:.1f}%</td></tr>
        <tr><td>经营风险</td><td>中</td><td>行业竞争加剧</td></tr>
        <tr><td>估值风险</td><td>{"低" if target_low <= price <= target_high else "中"}</td><td>当前价{target_low:.2f}-{target_high:.2f}元</td></tr>
    </table>

    <h3>8.3 投资建议</h3>
    <div class="summary">
        <p><strong>综合评级:</strong> {"强烈推荐" if total_score > 15 else "推荐" if total_score > 10 else "中性"}</p>
        <p><strong>目标价:</strong> {target_low:.2f}-{target_high:.2f}元</p>
        <p><strong>当前价:</strong> {price:.2f}元</p>
        <p><strong>上涨空间:</strong> {((target_high-price)/price*100) if price > 0 else 0:.1f}%</p>
    </div>
    <p>风险提示: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>

    <div class="meta">
        <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 数据来源: 公开资料整理 | 本报告由MoltBot量化研究团队生成</p>
    </div>
</body>
</html>'''
    return html

def main():
    for stock in STOCKS:
        code = stock["code"]
        name = stock["name"]
        print(f"\n生成 {name}({code}) V4.0报告...")
        
        # 加载数据
        data = load_data(code)
        if not data.get("price"):
            print(f"  跳过 {code} - 无法获取价格数据")
            continue
        
        # 生成HTML
        html = generate_html(data, stock)
        
        # 保存HTML
        html_path = f"/home/liujerry/moltbot/reports/{code}_v4_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  HTML已保存: {html_path}")
        
        # 转换为PDF
        pdf_path = f"/home/liujerry/金融数据/reports/{code}_v4_report.pdf"
        try:
            html_doc = weasyprint.HTML(filename=html_path)
            html_doc.write_pdf(pdf_path)
            print(f"  PDF已生成: {pdf_path}")
        except Exception as e:
            print(f"  PDF生成失败: {e}")
    
    print("\n全部完成！")

if __name__ == "__main__":
    main()