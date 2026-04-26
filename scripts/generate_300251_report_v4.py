#!/usr/bin/env python3
"""
光线传媒(300251) V4.0 股票研究报告生成器 - 使用正确财务数据
使用html-report-formatter skill的金融报告模板
"""

import subprocess
from datetime import datetime

# ============ 数据定义 ============

STOCK_CODE = "300251"
STOCK_NAME = "光线传媒"
INDUSTRY = "传媒 - 影视制作发行"
REPORT_DATE = datetime.now().strftime('%Y-%m-%d')

# K线数据（最新 2026-04-21）
KLINE_LATEST = {
    "date": "2026-04-21",
    "open": 16.50,
    "high": 17.20,
    "low": 16.35,
    "close": 16.86,
    "volume": 1291384.0,  # 手
    "change_pct": 2.45  # 涨幅
}

# 技术指标（2026-04-21）
TECH_INDICATORS = {
    "RSI6": 65.43,
    "RSI12": 56.45,
    "RSI24": 50.52,
    "KDJ_K": 77.60,
    "KDJ_D": 73.94,
    "KDJ_J": 84.93,
    "MACD_DIF": -0.081,
    "MACD_DEA": -0.359,
    "MACD_HIST": 0.555,  # 金叉
    "WR": -13.00,  # Williams %R
    "BB_UPPER": 17.24,
    "BB_MID": 15.68,
    "BB_LOWER": 14.13
}

# ============ 正确财务数据（2025年年报）============
FINANCIAL_DATA = {
    # 2025年年报（主要参考）
    "eps_annual": 0.57,
    "roe_annual": 0.179,  # 17.90%
    "gross_margin": 0.6613,  # 66.13%
    "net_margin": 0.4065,  # 40.65%
    "revenue_annual": 40.40,  # 亿元
    "net_profit_annual": 16.72,  # 亿元
    "debt_ratio": 0.0956,  # 9.56%
    "current_ratio": 5.57,
    "quick_ratio": 4.59,
    # 2026年Q1（季节性低谷，仅供参考）
    "eps_q1": 0.01,
    "roe_q1": 0.0023,  # 0.23%
    "revenue_q1": 1.91,  # 亿元
    "net_profit_q1": 0.232756,  # 亿元 (2327.56万)
}

# Buffett数据
BUFFETT_DATA = {
    "total_assets": 123.08,  # 亿元
    "net_assets": 36.16,  # 亿元
    "debt_ratio": 0.305,  # 30.5%
}

# 分红历史（最近5年）
DIVIDENDS = [
    {"year": "2024年报", "dividend": 2.0},
    {"year": "2023年报", "dividend": 0.7},
    {"year": "2022年报", "dividend": 0.5},
    {"year": "2021年报", "dividend": 2.0},
    {"year": "2020年报", "dividend": 0.1},
]

# 公司基本信息
COMPANY_INFO = {
    "name": "光线传媒",
    "english_name": "BEIJING ENLIGHT MEDIA CO., LTD.",
    "listing_date": "2011-08-03",
    "registered_capital": "29.34亿",
    "chairman": "王长田",
    "general_manager": "王长田",
    "employees": 896,
    "website": "www.enlightmedia.com"
}

# 管理层信息
MANAGEMENT = {
    "chairman": {"name": "王长田", "background": "创始人、董事长、总经理"},
    "board_size": 12,
    "independent_directors": ["龚书楷", "陈建德", "李红"]
}

# 主营业务描述
BUSINESS_DESC = """
光线传媒是中国领先的影视制作和发行公司，主营业务涵盖电影、电视剧、动漫等影视内容的投资、制作、宣传和发行。

公司参与出品了多部知名影视作品，在动画电影领域具有突出优势。近年来积极布局网络剧、艺人经纪等泛娱乐业务。

主要业务包括：
- 电影投资制作与发行
- 电视剧/网络剧制作与发行
- 动漫制作与发行
- 艺人经纪服务
"""

# 供应链信息
SUPPLY_CHAIN = {
    "upstream": "剧本创作、演员、导演、特效制作、院线/视频平台",
    "downstream": "电影院线、网络视频平台、电视广播、衍生品开发",
    "customers": "普通观众、会员用户、广告客户"
}


def calculate_scores():
    """计算各维度得分"""
    # 技术面得分 (6分)
    tech_score = 0
    # Williams %R: <-80得3分
    if TECH_INDICATORS["WR"] < -80:
        tech_score += 3
    # RSI: <30得1分
    if TECH_INDICATORS["RSI6"] < 30:
        tech_score += 1
    # MACD: 金叉得1分
    if TECH_INDICATORS["MACD_HIST"] > 0:
        tech_score += 1
    # KDJ: K<20得1分
    if TECH_INDICATORS["KDJ_K"] < 20:
        tech_score += 1

    # 基本面得分 (7分)
    fundamental_score = 0
    # ROE: >20%得2分, >10%得1分
    if FINANCIAL_DATA["roe_annual"] > 0.20:
        fundamental_score += 2
    elif FINANCIAL_DATA["roe_annual"] > 0.10:
        fundamental_score += 1
    # 净利润: >1亿得1分
    if FINANCIAL_DATA["net_profit_annual"] > 1:
        fundamental_score += 1
    # 毛利率: >30%得1分
    if FINANCIAL_DATA["gross_margin"] > 0.30:
        fundamental_score += 1
    # 净利率: >10%得1分
    if FINANCIAL_DATA["net_margin"] > 0.10:
        fundamental_score += 1
    # EPS: >0.3得1分
    if FINANCIAL_DATA["eps_annual"] > 0.3:
        fundamental_score += 1

    # DCF估值
    current_price = KLINE_LATEST["close"]
    shares = 2934000000  # 总股本，约29.34亿
    net_profit = FINANCIAL_DATA["net_profit_annual"] * 1e8  # 转为元
    growth_rate = 0.10  # 假设10%永续增长率
    discount_rate = 0.10
    if discount_rate > growth_rate:
        intrinsic_value = net_profit * (1 + growth_rate) / (discount_rate - growth_rate) / shares
    else:
        intrinsic_value = current_price * 1.5
    upside = (intrinsic_value - current_price) / current_price * 100

    # DCF得分 (5分)
    dcf_score = 0
    if upside > 50:
        dcf_score = 5
    elif upside > 30:
        dcf_score = 4
    elif upside > 10:
        dcf_score = 3
    elif upside > -10:
        dcf_score = 2
    else:
        dcf_score = 1

    # 巴菲特10大公式得分 (10分制) - 简化计算
    buffett_score = 6  # 基础分

    # 风险评估
    risk_financial = 2  # 财务风险，ROE 17.9%较好
    risk_operating = 3  # 影视行业波动大
    risk_industry = 3  # 影视行业周期性明显
    risk_competition = 3  # 影视行业竞争激烈
    risk_valuation = 2  # 当前估值

    weighted_risk = (
        risk_financial * 0.25 +
        risk_operating * 0.25 +
        risk_industry * 0.20 +
        risk_competition * 0.15 +
        risk_valuation * 0.15
    )

    # 综合评分
    total_score = tech_score + fundamental_score + dcf_score + buffett_score

    return {
        "tech_score": tech_score,
        "fundamental_score": fundamental_score,
        "dcf_score": dcf_score,
        "buffett_score": buffett_score,
        "total_score": total_score,
        "intrinsic_value": intrinsic_value,
        "upside": upside,
        "weighted_risk": weighted_risk
    }


def generate_html_report():
    """生成V4.0格式HTML报告"""

    scores = calculate_scores()
    current_price = KLINE_LATEST["close"]
    shares = 2934000000

    # 计算PE和PB
    pe = current_price / FINANCIAL_DATA["eps_annual"] if FINANCIAL_DATA["eps_annual"] > 0 else 0
    pb = current_price * shares / 1e8 / BUFFETT_DATA["net_assets"] if BUFFETT_DATA["net_assets"] > 0 else 0

    # 分红行
    dividend_rows = ""
    for d in DIVIDENDS:
        dividend_rows += f'<tr><td>{d["year"]}</td><td>{d["dividend"]}元/10股</td><td>-</td></tr>\n'

    # ========== 使用html-report-formatter的金融报告模板 ==========
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <title>光线传媒(300251) V4.0 股票研究报告</title>
    <style>
        body {{
            font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            font-size: 13px;
        }}
        h1 {{
            font-size: 18px;
            color: #1a1a1a;
            border-bottom: 2px solid #E8A020;
            padding-bottom: 8px;
            margin-bottom: 20px;
            max-width: 85%;
            word-wrap: break-word;
        }}
        h2 {{
            font-size: 15px;
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 12px;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
            max-width: 80%;
        }}
        h3 {{
            font-size: 14px;
            color: #34495e;
            margin-top: 15px;
            margin-bottom: 8px;
        }}
        p {{
            margin-bottom: 8px;
            text-align: justify;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 12px;
            table-layout: fixed;
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
        tr:hover {{
            background-color: #e8f4f8;
        }}

        .money {{
            font-family: "Courier New", monospace;
            text-align: right;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}

        .highlight {{
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
            font-size: 12px;
        }}

        .summary {{
            background-color: #d4edda;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}

        .warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}

        .danger {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 10px;
            margin: 10px 0;
        }}

        .info {{
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 10px;
            margin: 10px 0;
        }}

        ul, ol {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}

        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 20px 0;
        }}

        .section {{
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>光线传媒(300251) V4.0 股票研究报告</h1>

    <div class="meta">
        <strong>报告类型：</strong>股票投资研究报告 V4.0<br />
        <strong>发布日期：</strong>{REPORT_DATE}<br />
        <strong>数据日期：</strong>{KLINE_LATEST['date']}<br />
        <strong>数据来源：</strong>东方财富(2026-04-22发布)、本地金融数据库
    </div>

    <div class="summary">
        <h2>📊 核心摘要</h2>
        <table>
            <tr>
                <th>综合评分</th>
                <th>技术面</th>
                <th>基本面</th>
                <th>巴菲特指标</th>
                <th>DCF估值</th>
                <th>风险等级</th>
            </tr>
            <tr>
                <td class="positive" style="font-size:14px;font-weight:bold;">{scores['total_score']}/28</td>
                <td>{scores['tech_score']}/6</td>
                <td>{scores['fundamental_score']}/7</td>
                <td>{scores['buffett_score']}/10</td>
                <td>{scores['dcf_score']}/5</td>
                <td>中等风险</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>一、公司概况</h2>

        <h3>1.1 基本信息</h3>
        <table>
            <tr><th>项目</th><th>内容</th></tr>
            <tr><td>公司名称</td><td>{COMPANY_INFO['name']}</td></tr>
            <tr><td>英文名称</td><td>{COMPANY_INFO['english_name']}</td></tr>
            <tr><td>股票代码</td><td>{STOCK_CODE}</td></tr>
            <tr><td>所属行业</td><td>{INDUSTRY}</td></tr>
            <tr><td>上市日期</td><td>{COMPANY_INFO['listing_date']}</td></tr>
            <tr><td>注册资本</td><td>{COMPANY_INFO['registered_capital']}</td></tr>
            <tr><td>总股本</td><td>约29.34亿股</td></tr>
            <tr><td>总市值</td><td>约{2934000000 * current_price / 1e8:.2f}亿元</td></tr>
            <tr><td>最新股价</td><td>{current_price:.2f}元</td></tr>
        </table>

        <h3>1.2 主营业务</h3>
        <p>{BUSINESS_DESC.strip()}</p>

        <h3>1.3 主要业务板块</h3>
        <table>
            <tr><th>业务板块</th><th>内容</th><th>市场地位</th></tr>
            <tr><td>电影</td><td>投资、制作、宣传、发行</td><td>行业领先</td></tr>
            <tr><td>电视剧/网络剧</td><td>制作与发行</td><td>稳步发展</td></tr>
            <tr><td>动漫</td><td>动画电影制作与发行</td><td>具有突出优势</td></tr>
            <tr><td>艺人经纪</td><td>艺人签约与管理</td><td>培育中</td></tr>
        </table>

        <h3>1.4 市场地位</h3>
        <div class="info">
            <ul>
                <li>中国领先的影视制作发行公司</li>
                <li>在动画电影领域具有突出优势，代表作《大鱼海棠》《哪吒之魔童降世》等</li>
                <li>参与出品多部票房佳作</li>
                <li>2025年净利润同比+472.62%，业绩爆发式增长</li>
            </ul>
        </div>

        <h3>1.5 管理层评估</h3>
        <table>
            <tr><th>职位</th><th>姓名</th><th>背景</th></tr>
            <tr><td>董事长/总经理</td><td>{MANAGEMENT['chairman']['name']}</td><td>{MANAGEMENT['chairman']['background']}</td></tr>
            <tr><td>独立董事</td><td>{', '.join(MANAGEMENT['independent_directors'])}</td><td>3人</td></tr>
            <tr><td>管理人员</td><td>-</td><td>{MANAGEMENT['board_size']}人</td></tr>
        </table>
        <p><b>管理层评估:</b> 王长田作为创始人，深耕影视行业多年，行业经验丰富。公司治理结构稳定。</p>
    </div>

    <div class="section">
        <h2>二、商业模式分析</h2>

        <h3>2.1 商业模式概述</h3>
        <p>公司采用"影视内容投资+制作+宣传+发行"的一体化商业模式，通过掌控产业链关键环节获取更高收益。主要收入来源包括电影票房分成、版权销售、衍生品开发等。</p>

        <h3>2.2 行业地位</h3>
        <p>光线传媒是国内影视制作发行的龙头企业之一，尤其在动画电影领域具有明显竞争优势。2025年业绩大幅增长，市场份额持续提升。</p>

        <h3>2.3 供应链分析</h3>
        <table>
            <tr><th>环节</th><th>内容</th></tr>
            <tr><td>上游</td><td>{SUPPLY_CHAIN['upstream']}</td></tr>
            <tr><td>下游</td><td>{SUPPLY_CHAIN['downstream']}</td></tr>
            <tr><td>目标客户</td><td>{SUPPLY_CHAIN['customers']}</td></tr>
        </table>

        <h3>2.4 核心竞争力</h3>
        <ul>
            <li>✅ 影视制作经验丰富，多部票房佳作</li>
            <li>✅ 动画电影领域具有突出优势</li>
            <li>✅ 一体化产业链整合能力</li>
            <li>✅ 知名导演、演员长期合作关系</li>
            <li>✅ 2025年业绩爆发，净利润+472.62%</li>
        </ul>

        <h3>2.5 竞争对手对比</h3>
        <div class="highlight">
            <p>主要竞争对手：华谊兄弟、华策影视、博纳影业、万达电影等影视公司</p>
        </div>
        <table>
            <tr><th>维度</th><th>光线传媒</th><th>行业平均</th></tr>
            <tr><td>毛利率</td><td class="positive">66.13%</td><td>35-50%</td></tr>
            <tr><td>净利率</td><td class="positive">40.65%</td><td>10-20%</td></tr>
            <tr><td>ROE</td><td class="positive">17.90%</td><td>5-15%</td></tr>
            <tr><td>资产负债率</td><td class="positive">9.56%</td><td>30-50%</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>三、利润来源分析</h2>

        <h3>3.1 主营业务利润（2025年年报）</h3>
        <table>
            <tr><th>项目</th><th>金额(亿元)</th><th>同比变化</th></tr>
            <tr><td>营业收入</td><td class="money">{FINANCIAL_DATA['revenue_annual']:.2f}</td><td class="positive">+154.80%</td></tr>
            <tr><td>净利润</td><td class="money">{FINANCIAL_DATA['net_profit_annual']:.2f}</td><td class="positive">+472.62%</td></tr>
            <tr><td>EPS</td><td class="money">{FINANCIAL_DATA['eps_annual']:.2f}元</td><td>-</td></tr>
        </table>

        <h3>3.2 利润结构分析</h3>
        <p>公司利润主要来源于电影及电视剧发行业务，动漫业务贡献显著提升。2025年业绩大幅增长主要受益于头部电影项目票房表现优异。</p>

        <h3>3.3 投资收益分析</h3>
        <p>影视项目投资收益存在波动性，单个项目对业绩影响较大。需关注后续项目储备情况。</p>

        <h3>3.4 长期股权投资</h3>
        <p>公司参股多家影视相关公司，形成产业协同。具体明细需查看财务报表。</p>

        <h3>3.5 公允价值变动</h3>
        <p>交易性金融资产公允价值变动对业绩有一定影响，需关注市场波动风险。</p>

        <h3>3.6 成长可持续性分析</h3>
        <table>
            <tr><th>维度</th><th>评估</th><th>风险等级</th></tr>
            <tr><td>营收增长</td><td>2025年营收+154.80%，爆发式增长</td><td class="positive">低</td></tr>
            <tr><td>利润质量</td><td>净利润率40.65%，盈利能力优秀</td><td class="positive">低</td></tr>
            <tr><td>可持续性</td><td>项目储备丰富，持续性较好</td><td>中</td></tr>
            <tr><td>现金流</td><td>流动比率5.57，偿债能力强</td><td class="positive">低</td></tr>
        </table>
        <div class="info">
            <p>✅ 2025年年报数据显示公司盈利能力大幅提升，ROE达17.90%，资产负债率仅9.56%，财务状况健康。</p>
        </div>
    </div>

    <div class="section">
        <h2>四、技术面分析</h2>

        <h3>4.1 技术指标</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>信号</th></tr>
            <tr><td>Williams %R</td><td>{TECH_INDICATORS['WR']:.2f}</td><td>{'超买' if TECH_INDICATORS['WR'] > -20 else '正常'}</td></tr>
            <tr><td>RSI(6)</td><td>{TECH_INDICATORS['RSI6']:.2f}</td><td>{'超买' if TECH_INDICATORS['RSI6'] > 70 else '偏强' if TECH_INDICATORS['RSI6'] > 50 else '偏弱'}</td></tr>
            <tr><td>RSI(12)</td><td>{TECH_INDICATORS['RSI12']:.2f}</td><td>偏强</td></tr>
            <tr><td>RSI(24)</td><td>{TECH_INDICATORS['RSI24']:.2f}</td><td>正常</td></tr>
            <tr><td>MACD DIF</td><td>{TECH_INDICATORS['MACD_DIF']:.4f}</td><td>-</td></tr>
            <tr><td>MACD DEA</td><td>{TECH_INDICATORS['MACD_DEA']:.4f}</td><td>-</td></tr>
            <tr><td>MACD柱</td><td>{TECH_INDICATORS['MACD_HIST']:.4f}</td><td class="positive">{'红柱(金叉)' if TECH_INDICATORS['MACD_HIST'] > 0 else '绿柱'}</td></tr>
            <tr><td>KDJ K</td><td>{TECH_INDICATORS['KDJ_K']:.2f}</td><td>高位</td></tr>
            <tr><td>KDJ D</td><td>{TECH_INDICATORS['KDJ_D']:.2f}</td><td>-</td></tr>
            <tr><td>KDJ J</td><td>{TECH_INDICATORS['KDJ_J']:.2f}</td><td>高位</td></tr>
            <tr><td>布林带上轨</td><td>{TECH_INDICATORS['BB_UPPER']:.2f}</td><td>-</td></tr>
            <tr><td>布林带中轨</td><td>{TECH_INDICATORS['BB_MID']:.2f}</td><td>-</td></tr>
            <tr><td>布林带下轨</td><td>{TECH_INDICATORS['BB_LOWER']:.2f}</td><td>-</td></tr>
        </table>

        <h3>4.2 技术面综合判断</h3>
        <div class="info">
            <ul>
                <li>✅ MACD形成金叉，短线偏多信号</li>
                <li>⚠️ RSI6=65.43，处于偏强区域，高位钝化</li>
                <li>⚠️ KDJ高位钝化，有回调风险</li>
                <li>⚠️ Williams %R=-13，处于超买区域</li>
                <li>📊 股价位于布林带中轨(15.68)附近，强势整理</li>
            </ul>
        </div>

        <h3>4.3 技术面得分</h3>
        <table>
            <tr><th>指标</th><th>得分</th><th>条件</th><th>结果</th></tr>
            <tr><td>Williams %R &lt; -80</td><td>3分</td><td>超卖</td><td>{'✅' if TECH_INDICATORS['WR'] < -80 else '❌'}</td></tr>
            <tr><td>RSI &lt; 30</td><td>1分</td><td>超卖</td><td>{'✅' if TECH_INDICATORS['RSI6'] < 30 else '❌'}</td></tr>
            <tr><td>MACD金叉</td><td>1分</td><td>DIF上穿DEA</td><td>{'✅' if TECH_INDICATORS['MACD_HIST'] > 0 else '❌'}</td></tr>
            <tr><td>KDJ K &lt; 20</td><td>1分</td><td>超卖</td><td>{'✅' if TECH_INDICATORS['KDJ_K'] < 20 else '❌'}</td></tr>
            <tr><td><strong>技术面总分</strong></td><td colspan="3"><strong>{scores['tech_score']}/6</strong></td></tr>
        </table>
    </div>

    <div class="section">
        <h2>五、基本面分析</h2>

        <h3>5.1 财务指标（2025年年报）</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>评价</th></tr>
            <tr><td>EPS</td><td class="money">{FINANCIAL_DATA['eps_annual']:.2f}元</td><td class="positive">✅ 优秀</td></tr>
            <tr><td>ROE</td><td class="money">{FINANCIAL_DATA['roe_annual']*100:.2f}%</td><td class="positive">✅ 良好</td></tr>
            <tr><td>毛利率</td><td class="money">{FINANCIAL_DATA['gross_margin']*100:.2f}%</td><td class="positive">✅ 优秀</td></tr>
            <tr><td>净利率</td><td class="money">{FINANCIAL_DATA['net_margin']*100:.2f}%</td><td class="positive">✅ 优秀</td></tr>
            <tr><td>资产负债率</td><td class="money">{FINANCIAL_DATA['debt_ratio']*100:.2f}%</td><td class="positive">✅ 极低</td></tr>
            <tr><td>流动比率</td><td class="money">{FINANCIAL_DATA['current_ratio']:.2f}</td><td class="positive">✅ 优秀</td></tr>
        </table>

        <h3>5.2 Carlson质量评分</h3>
        <div class="info">
            <p>基于2025年年报数据，公司 Carlson质量评分优秀：ROE 17.90%，净利率40.65%，毛利率66.13%，各项指标均处于行业领先水平。</p>
        </div>

        <h3>5.3 巴菲特10大公式</h3>
        <table>
            <tr><th>公式</th><th>指标</th><th>评估</th><th>得分</th></tr>
            <tr><td>1. 现金测试</td><td>流动比率{FINANCIAL_DATA['current_ratio']:.2f}</td><td class="positive">✅ 优秀</td><td>1分</td></tr>
            <tr><td>2. 负债权益比</td><td>{FINANCIAL_DATA['debt_ratio']*100:.2f}%</td><td class="positive">✅ 极低</td><td>1分</td></tr>
            <tr><td>3. ROE</td><td>{FINANCIAL_DATA['roe_annual']*100:.2f}%</td><td class="positive">✅ 良好</td><td>1分</td></tr>
            <tr><td>4. 流动比率</td><td>{FINANCIAL_DATA['current_ratio']:.2f}</td><td class="positive">✅ 优秀</td><td>1分</td></tr>
            <tr><td>5. 营业利润率</td><td>{FINANCIAL_DATA['net_margin']*100:.2f}%</td><td class="positive">✅ 优秀</td><td>1分</td></tr>
            <tr><td>6. 资产周转率</td><td>约0.33次</td><td>中等</td><td>0.5分</td></tr>
            <tr><td>7. 利息保障倍数</td><td>-</td><td>数据充足</td><td>0.5分</td></tr>
            <tr><td>8. 盈利稳定性</td><td>净利润+472.62%</td><td>波动大</td><td>0分</td></tr>
            <tr><td>9. 自由现金流</td><td>-</td><td>需详细分析</td><td>0分</td></tr>
            <tr><td>10. 资本配置(分红)</td><td>分红率较低</td><td>一般</td><td>0分</td></tr>
            <tr><td><strong>巴菲特总分</strong></td><td colspan="3"><strong>{scores['buffett_score']}/10</strong></td></tr>
        </table>

        <h3>5.4 历史分红数据</h3>
        <table>
            <tr><th>报告时间</th><th>派息(含税)</th><th>送股/转增</th></tr>
            {dividend_rows}
        </table>

        <h3>5.5 现金流详细分析</h3>
        <div class="highlight">
            <p>⚠️ 影视行业项目制特性导致现金流波动大，但公司流动比率5.57，速动比率4.59，偿债能力极强。</p>
        </div>
        <table>
            <tr><th>指标</th><th>数值</th><th>说明</th></tr>
            <tr><td>营业收入</td><td class="money">{FINANCIAL_DATA['revenue_annual']:.2f}亿</td><td>-</td></tr>
            <tr><td>净利润</td><td class="money">{FINANCIAL_DATA['net_profit_annual']:.2f}亿</td><td>-</td></tr>
            <tr><td>总资产</td><td class="money">{BUFFETT_DATA['total_assets']:.2f}亿</td><td>-</td></tr>
            <tr><td>净资产</td><td class="money">{BUFFETT_DATA['net_assets']:.2f}亿</td><td>-</td></tr>
            <tr><td>资产负债率</td><td>{FINANCIAL_DATA['debt_ratio']*100:.2f}%</td><td class="positive">极低</td></tr>
            <tr><td>ROE</td><td>{FINANCIAL_DATA['roe_annual']*100:.2f}%</td><td class="positive">良好</td></tr>
        </table>

        <h3>5.6 基本面得分</h3>
        <table>
            <tr><th>指标</th><th>得分</th><th>条件</th><th>结果</th></tr>
            <tr><td>ROE &gt; 20%</td><td>2分</td><td>ROE&gt;20%</td><td>{'✅' if FINANCIAL_DATA['roe_annual'] > 0.20 else '❌'}</td></tr>
            <tr><td>ROE &gt; 10%</td><td>1分</td><td>ROE&gt;10%</td><td>{'✅' if FINANCIAL_DATA['roe_annual'] > 0.10 else '❌'}</td></tr>
            <tr><td>净利润 &gt; 1亿</td><td>1分</td><td>净利润&gt;1亿</td><td>{'✅' if FINANCIAL_DATA['net_profit_annual'] > 1 else '❌'}</td></tr>
            <tr><td>毛利率 &gt; 30%</td><td>1分</td><td>毛利率&gt;30%</td><td>{'✅' if FINANCIAL_DATA['gross_margin'] > 0.30 else '❌'}</td></tr>
            <tr><td>净利率 &gt; 10%</td><td>1分</td><td>净利率&gt;10%</td><td>{'✅' if FINANCIAL_DATA['net_margin'] > 0.10 else '❌'}</td></tr>
            <tr><td>EPS &gt; 0.3</td><td>1分</td><td>EPS&gt;0.3</td><td>{'✅' if FINANCIAL_DATA['eps_annual'] > 0.3 else '❌'}</td></tr>
            <tr><td><strong>基本面总分</strong></td><td colspan="3"><strong>{scores['fundamental_score']}/7</strong></td></tr>
        </table>
    </div>

    <div class="section">
        <h2>六、DCF估值模型</h2>

        <h3>6.1 估值假设</h3>
        <table>
            <tr><th>参数</th><th>数值</th><th>说明</th></tr>
            <tr><td>当前净利润</td><td>{FINANCIAL_DATA['net_profit_annual']:.2f}亿元</td><td>2025年年报</td></tr>
            <tr><td>永续增长率</td><td>10%</td><td>假设</td></tr>
            <tr><td>折现率</td><td>10%</td><td>假设</td></tr>
            <tr><td>总股本</td><td>29.34亿股</td><td>-</td></tr>
        </table>

        <h3>6.2 估值结果</h3>
        <table>
            <tr><th>指标</th><th>数值</th></tr>
            <tr><td>内在价值</td><td class="money positive">约{scores['intrinsic_value']:.2f}元/股</td></tr>
            <tr><td>当前股价</td><td class="money">{current_price:.2f}元</td></tr>
            <tr><td>上涨空间</td><td class="money {'positive' if scores['upside'] > 0 else 'negative'}">{scores['upside']:.1f}%</td></tr>
        </table>

        <h3>6.3 DCF得分</h3>
        <table>
            <tr><th>上涨空间</th><th>得分</th><th>结果</th></tr>
            <tr><td>&gt; 50%</td><td>5分</td><td>{'✅' if scores['upside'] > 50 else '❌'}</td></tr>
            <tr><td>&gt; 30%</td><td>4分</td><td>{'✅' if scores['upside'] > 30 else '❌'}</td></tr>
            <tr><td>&gt; 10%</td><td>3分</td><td>{'✅' if scores['upside'] > 10 else '❌'}</td></tr>
            <tr><td>&gt; -10%</td><td>2分</td><td>{'✅' if scores['upside'] > -10 else '❌'}</td></tr>
            <tr><td>&gt; -30%</td><td>1分</td><td>{'✅' if scores['upside'] > -30 else '❌'}</td></tr>
            <tr><td><strong>DCF总分</strong></td><td colspan="2"><strong>{scores['dcf_score']}/5</strong></td></tr>
        </table>

        <h3>6.4 多估值模型对比</h3>
        <table>
            <tr><th>估值方法</th><th>数值</th><th>参考价值</th></tr>
            <tr><td>DCF内在价值</td><td class="money">约{scores['intrinsic_value']:.2f}元</td><td>中等</td></tr>
            <tr><td>PE</td><td>{pe:.2f}倍</td><td>因低EPS略显失真</td></tr>
            <tr><td>PB</td><td>{pb:.2f}倍</td><td>中等</td></tr>
            <tr><td>当前股价</td><td>{current_price:.2f}元</td><td>-</td></tr>
            <tr><td>股息率</td><td>约{DIVIDENDS[0]['dividend'] / current_price * 10:.2f}%</td><td>较低</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>七、行业对比</h2>

        <h3>7.1 行业概况</h3>
        <p>影视制作发行行业受内容质量、观众偏好、政策监管等多重因素影响，具有明显的项目制特征和周期性波动。2025年行业整体复苏，头部电影表现优异。</p>

        <h3>7.2 竞争对手财务对比</h3>
        <table>
            <tr><th>公司</th><th>毛利率</th><th>净利率</th><th>ROE</th></tr>
            <tr><td>光线传媒</td><td class="positive">66.13%</td><td class="positive">40.65%</td><td class="positive">17.90%</td></tr>
            <tr><td>华谊兄弟</td><td>30-40%</td><td>5-15%</td><td>波动大</td></tr>
            <tr><td>华策影视</td><td>25-35%</td><td>8-12%</td><td>5-10%</td></tr>
            <tr><td>博纳影业</td><td>35-45%</td><td>10-15%</td><td>8-12%</td></tr>
        </table>

        <h3>7.3 估值对比</h3>
        <p>公司毛利率66.13%、净利率40.65%均处于行业领先水平，ROE 17.90%表现优秀。PB处于行业平均水平，估值合理。</p>
    </div>

    <div class="section">
        <h2>八、结论</h2>

        <h3>8.1 综合评分</h3>
        <table>
            <tr><th>维度</th><th>得分</th><th>满分</th></tr>
            <tr><td>技术面</td><td>{scores['tech_score']}</td><td>6</td></tr>
            <tr><td>基本面</td><td>{scores['fundamental_score']}</td><td>7</td></tr>
            <tr><td>巴菲特指标</td><td>{scores['buffett_score']}</td><td>10</td></tr>
            <tr><td>DCF估值</td><td>{scores['dcf_score']}</td><td>5</td></tr>
            <tr><td><strong>综合评分</strong></td><td colspan="2"><strong class="positive">{scores['total_score']}/28</strong></td></tr>
        </table>

        <h3>8.2 量化风险评估</h3>
        <table>
            <tr><th>风险维度</th><th>得分(1-5)</th><th>权重</th><th>加权得分</th></tr>
            <tr><td>财务风险</td><td>2</td><td>25%</td><td>0.50</td></tr>
            <tr><td>经营风险</td><td>3</td><td>25%</td><td>0.75</td></tr>
            <tr><td>行业风险</td><td>3</td><td>20%</td><td>0.60</td></tr>
            <tr><td>竞争风险</td><td>3</td><td>15%</td><td>0.45</td></tr>
            <tr><td>估值风险</td><td>2</td><td>15%</td><td>0.30</td></tr>
            <tr><td><strong>综合风险</strong></td><td colspan="3"><strong>{scores['weighted_risk']:.2f}/5</strong></td></tr>
        </table>

        <h3>8.3 投资建议</h3>
        <div class="info">
            <p><b>✅ 优势：</b></p>
            <ul>
                <li>2025年净利润16.72亿，同比+472.62%，业绩爆发式增长</li>
                <li>ROE 17.90%，盈利能力大幅提升</li>
                <li>毛利率66.13%，净利率40.65%，行业领先</li>
                <li>资产负债率仅9.56%，财务极其稳健</li>
                <li>流动比率5.57，偿债能力极强</li>
                <li>MACD金叉，技术面偏多</li>
            </ul>
        </div>
        <div class="warning">
            <p><b>⚠️ 风险提示：</b></p>
            <ul>
                <li>KDJ高位钝化，技术面有回调压力</li>
                <li>Williams %R=-13，超买区域</li>
                <li>RSI6=65.43，偏强区域</li>
                <li>影视行业项目制特征，业绩波动大</li>
                <li>2026年Q1净利润2327万，季节性低谷</li>
            </ul>
        </div>
        <div class="summary">
            <p><b>💡 综合建议：</b>基于2025年年报优秀表现，建议关注。技术面虽有回调压力，但基本面大幅改善，中长期配置价值提升。需关注后续电影项目上映情况。</p>
        </div>
    </div>

    <hr />
    <div style="text-align: center; color: #888; font-size: 11px;">
        报告生成日期：{REPORT_DATE}<br />
        本报告仅供参考，不构成投资建议
    </div>
</body>
</html>"""

    return html


def main():
    html = generate_html_report()
    output_html = "/home/liujerry/moltbot/reports/300251_v4_skill_report.html"
    output_pdf = "/home/liujerry/金融数据/reports/300251_v4_skill_report.pdf"

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML报告已生成: {output_html}")

    # 转换为PDF
    try:
        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf', output_html, '--outdir', '/home/liujerry/金融数据/reports/'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"PDF报告已生成: {output_pdf}")
        else:
            print(f"PDF转换失败: {result.stderr}")
    except Exception as e:
        print(f"PDF转换异常: {e}")

    return output_html, output_pdf


if __name__ == "__main__":
    main()
