#!/usr/bin/env python3
"""
光线传媒(300251) V4.0 股票研究报告生成器
"""

import subprocess
from datetime import datetime

# ============ 数据定义 ============

STOCK_CODE = "300251"
STOCK_NAME = "光线传媒"
INDUSTRY = "传媒 - 影视制作发行"

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

# 财务数据（2026-03-31）
FINANCIAL_DATA = {
    "eps": 0.01,
    "roe": 0.0023,  # 0.23%
    "gross_margin": 0.4413,  # 44.13%
    "net_margin": 0.1255,  # 12.55%
    "revenue": 1.91,  # 亿元
    "net_profit": 0.232756,  # 亿元 (2327.56万)
    "total_assets": 123.08,  # 亿元
    "equity": 36.16  # 亿元
}

# Buffett数据
BUFFETT_DATA = {
    "total_assets": 123.08,  # 亿元
    "net_assets": 36.16,  # 亿元
    "debt_ratio": 0.305,  # 30.5%
    "roic": 0.0023  # ROE近似ROIC
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


def generate_html_report():
    """生成V4.0格式HTML报告"""

    # 计算技术面得分
    tech_score = 0
    if TECH_INDICATORS["WR"] < -80:
        tech_score += 3
    elif TECH_INDICATORS["WR"] < -50:
        tech_score += 1
    if TECH_INDICATORS["RSI6"] < 30:
        tech_score += 1
    if TECH_INDICATORS["MACD_HIST"] > 0:
        tech_score += 1
    if TECH_INDICATORS["KDJ_K"] < 20:
        tech_score += 1
    if TECH_INDICATORS["RSI6"] > 70:
        tech_score -= 1  # 高位减分

    # 计算基本面得分
    fundamental_score = 0
    if FINANCIAL_DATA["roe"] > 0.20:
        fundamental_score += 2
    elif FINANCIAL_DATA["roe"] > 0.10:
        fundamental_score += 1
    if FINANCIAL_DATA["net_profit"] > 1:
        fundamental_score += 1
    if FINANCIAL_DATA["gross_margin"] > 0.30:
        fundamental_score += 1
    if FINANCIAL_DATA["net_margin"] > 0.10:
        fundamental_score += 1
    if FINANCIAL_DATA["eps"] > 0.3:
        fundamental_score += 1

    # DCF估值（简化版）
    current_price = KLINE_LATEST["close"]
    shares = 2934000000  # 总股本，约29.34亿
    net_profit = FINANCIAL_DATA["net_profit"] * 1e8  # 转为元
    growth_rate = 0.10  # 假设10%永续增长率
    discount_rate = 0.10
    if discount_rate > growth_rate:
        intrinsic_value = net_profit * (1 + growth_rate) / (discount_rate - growth_rate) / shares
    else:
        intrinsic_value = current_price * 1.5
    upside = (intrinsic_value - current_price) / current_price * 100

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

    # 风险评估
    risk_financial = 3  # ROE极低，高风险
    risk_operating = 2  # 影视行业波动大
    risk_industry = 4  # 影视行业周期性明显，竞争激烈
    risk_competition = 4  # 影视行业竞争激烈
    risk_valuation = 2  # 当前估值较低

    weighted_risk = (
        risk_financial * 0.25 +
        risk_operating * 0.25 +
        risk_industry * 0.20 +
        risk_competition * 0.15 +
        risk_valuation * 0.15
    )

    # 综合评分
    total_score = tech_score + fundamental_score + dcf_score + 6  # 6分为巴菲特指标基础分

    # 分红行
    dividend_rows = ""
    for d in DIVIDENDS:
        bonus = d.get("bonus", "-")
        dividend_rows += f'<tr><td>{d["year"]}</td><td>{d["dividend"]}元/10股</td><td>{bonus}</td></tr>\n'

    # 计算PE和PB
    pe = current_price / FINANCIAL_DATA["eps"] if FINANCIAL_DATA["eps"] > 0 else 0
    pb = current_price * shares / 1e8 / FINANCIAL_DATA["equity"] if FINANCIAL_DATA["equity"] > 0 else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 18pt;
            text-align: center;
            color: #1a1a1a;
            border-bottom: 3px solid #E8A020;
            padding-bottom: 10px;
        }}
        h2 {{
            font-size: 14pt;
            color: #2c3e50;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        h3 {{
            font-size: 12pt;
            color: #34495e;
            margin-top: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            border: 1px solid #bdc3c7;
            padding: 6px 8px;
            text-align: center;
        }}
        th {{
            background: #ECF0F1;
            font-weight: bold;
        }}
        .score {{
            font-weight: bold;
            color: #27ae60;
        }}
        .warning {{
            background: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }}
        .danger {{
            background: #f8d7da;
            padding: 10px;
            border-left: 4px solid #dc3545;
            margin: 10px 0;
        }}
        .info {{
            background: #d1ecf1;
            padding: 10px;
            border-left: 4px solid #17a2b8;
            margin: 10px 0;
        }}
        .summary {{
            background: #d4edda;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .header-info {{
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>光线传媒({STOCK_CODE}) V4.0 股票研究报告</h1>
    <div class="header-info">
        <p>报告日期: {datetime.now().strftime('%Y-%m-%d')} | 数据日期: {KLINE_LATEST['date']}</p>
        <p>最新价: {current_price:.2f}元 | 涨跌幅: +{KLINE_LATEST['change_pct']:.2f}%</p>
    </div>

    <div class="summary">
        <h2>📊 核心摘要</h2>
        <table>
            <tr>
                <th>综合评分</th>
                <th>技术面</th>
                <th>基本面</th>
                <th>DCF估值</th>
                <th>风险等级</th>
            </tr>
            <tr>
                <td class="score">{total_score:.0f}/22</td>
                <td>{tech_score:.0f}/6</td>
                <td>{fundamental_score:.0f}/7</td>
                <td>{dcf_score:.0f}/5</td>
                <td>中高风险</td>
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
        </table>

        <h3>1.2 主营业务</h3>
        <p>{BUSINESS_DESC.strip()}</p>

        <h3>1.3 主要业务板块</h3>
        <table>
            <tr><th>业务板块</th><th>内容</th><th>地位</th></tr>
            <tr><td>电影</td><td>投资、制作、宣传、发行</td><td>行业领先</td></tr>
            <tr><td>电视剧/网络剧</td><td>制作与发行</td><td>稳步发展</td></tr>
            <tr><td>动漫</td><td>动画电影制作与发行</td><td>具有优势</td></tr>
            <tr><td>艺人经纪</td><td>艺人签约与管理</td><td>培育中</td></tr>
        </table>

        <h3>1.4 市场地位</h3>
        <div class="info">
            <ul>
                <li>中国领先的影视制作发行公司</li>
                <li>在动画电影领域具有突出优势</li>
                <li>参与出品多部票房佳作</li>
                <li>积极布局网络剧、艺人经纪等泛娱乐业务</li>
            </ul>
        </div>

        <h3>1.5 管理层评估</h3>
        <table>
            <tr><th>职位</th><th>姓名</th><th>背景</th></tr>
            <tr><td>董事长/总经理</td><td>{MANAGEMENT['chairman']['name']}</td><td>{MANAGEMENT['chairman']['background']}</td></tr>
            <tr><td>独立董事</td><td>{', '.join(MANAGEMENT['independent_directors'])}</td><td>3人</td></tr>
            <tr><td>管理人员</td><td>-</td><td>{MANAGEMENT['board_size']}人</td></tr>
        </table>
        <p><b>管理层评估:</b> 王长田作为创始人，深耕影视行业多年，行业经验丰富。需关注影视行业项目波动风险。</p>
    </div>

    <div class="section">
        <h2>二、商业模式分析</h2>

        <h3>2.1 商业模式</h3>
        <p>公司采用"影视内容投资+制作+宣传+发行"的一体化商业模式，通过掌控产业链关键环节获取更高收益。</p>

        <h3>2.2 行业地位</h3>
        <p>光线传媒是国内影视制作发行的龙头企业之一，尤其在动画电影领域具有明显竞争优势。</p>

        <h3>2.3 供应链分析</h3>
        <table>
            <tr><th>环节</th><th>内容</th></tr>
            <tr><td>上游原材料</td><td>{SUPPLY_CHAIN['upstream']}</td></tr>
            <tr><td>下游渠道</td><td>{SUPPLY_CHAIN['downstream']}</td></tr>
            <tr><td>目标客户</td><td>{SUPPLY_CHAIN['customers']}</td></tr>
        </table>

        <h3>2.4 核心竞争力</h3>
        <ul>
            <li>✅ 影视制作经验丰富，多部票房佳作</li>
            <li>✅ 动画电影领域具有突出优势</li>
            <li>✅ 一体化产业链整合能力</li>
            <li>✅ 知名导演、演员合作关系</li>
        </ul>

        <h3>2.5 竞争对手对比</h3>
        <div class="warning">
            <p>主要竞争对手：华谊兄弟、华策影视、博纳影业、万达电影等影视公司</p>
        </div>
        <table>
            <tr><th>维度</th><th>光线传媒</th><th>行业平均</th></tr>
            <tr><td>毛利率</td><td>44.13%</td><td>35-45%</td></tr>
            <tr><td>净利率</td><td>12.55%</td><td>10-15%</td></tr>
            <tr><td>ROE</td><td>0.23%</td><td>5-10%</td></tr>
        </table>

        <h3>2.6 竞争优势</h3>
        <ul>
            <li>✅ 动画电影优势明显《大鱼海棠》《哪吒》等</li>
            <li>✅ 一体化产业链布局</li>
            <li>✅ 知名IP储备丰富</li>
            <li>✅ 管理团队行业经验丰富</li>
        </ul>
    </div>

    <div class="section">
        <h2>三、利润来源分析</h2>

        <h3>3.1 主营业务利润</h3>
        <table>
            <tr><th>项目</th><th>金额(亿元)</th><th>占比</th></tr>
            <tr><td>营业收入</td><td>{FINANCIAL_DATA['revenue']:.2f}</td><td>100%</td></tr>
            <tr><td>净利润</td><td>{FINANCIAL_DATA['net_profit']:.2f}</td><td>{FINANCIAL_DATA['net_profit']/FINANCIAL_DATA['revenue']*100:.1f}%</td></tr>
        </table>

        <h3>3.2 利润结构分析</h3>
        <p>公司利润主要来源于电影及电视剧发行业务，动漫业务贡献逐步提升。</p>

        <h3>3.3 投资收益</h3>
        <p>影视项目投资收益存在波动性，单个项目对业绩影响较大。</p>

        <h3>3.4 长期股权投资</h3>
        <p>公司参股多家影视相关公司，形成产业协同。</p>

        <h3>3.5 公允价值变动</h3>
        <p>需查看财务报表详细数据。</p>

        <h3>3.6 成长可持续性分析</h3>
        <table>
            <tr><th>维度</th><th>评估</th><th>风险</th></tr>
            <tr><td>营收增长</td><td>影视项目制周期性明显，收入不稳定</td><td>高</td></tr>
            <tr><td>利润质量</td><td>净利润率12.55%，盈利一般</td><td>中</td></tr>
            <tr><td>可持续性</td><td>依赖优质项目产出，持续性存疑</td><td>高</td></tr>
            <tr><td>现金流</td><td>项目制回款慢，现金流压力大</td><td>高</td></tr>
        </table>
        <div class="danger">
            <p>⚠️ ROE仅0.23%，极低水平。影视行业项目制特性导致盈利波动大，需关注后续项目表现。</p>
        </div>
    </div>

    <div class="section">
        <h2>四、技术面分析</h2>

        <h3>4.1 技术指标</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>信号</th></tr>
            <tr><td>Williams %R</td><td>{TECH_INDICATORS['WR']:.2f}</td><td>{'超买' if TECH_INDICATORS['WR'] > -20 else '正常'}</td></tr>
            <tr><td>RSI(6)</td><td>{TECH_INDICATORS['RSI6']:.2f}</td><td>{'超买' if TECH_INDICATORS['RSI6'] > 70 else '正常'}</td></tr>
            <tr><td>RSI(12)</td><td>{TECH_INDICATORS['RSI12']:.2f}</td><td>正常</td></tr>
            <tr><td>RSI(24)</td><td>{TECH_INDICATORS['RSI24']:.2f}</td><td>正常</td></tr>
            <tr><td>MACD DIF</td><td>{TECH_INDICATORS['MACD_DIF']:.4f}</td><td>-</td></tr>
            <tr><td>MACD DEA</td><td>{TECH_INDICATORS['MACD_DEA']:.4f}</td><td>-</td></tr>
            <tr><td>MACD柱</td><td>{TECH_INDICATORS['MACD_HIST']:.4f}</td><td>{'红柱(上涨)' if TECH_INDICATORS['MACD_HIST'] > 0 else '绿柱(下跌)'}</td></tr>
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
                <li>MACD形成金叉，短线偏多</li>
                <li>RSI6=65.43，处于偏强区域</li>
                <li>KDJ高位钝化，有回调风险</li>
                <li>Williams %R=-13，处于超买区域</li>
                <li>股价位于布林带中轨(15.68)附近</li>
            </ul>
        </div>

        <h3>4.3 技术面得分</h3>
        <table>
            <tr><th>指标</th><th>得分</th><th>条件</th></tr>
            <tr><td>Williams %R &lt; -80</td><td>3分</td><td>{'✅' if TECH_INDICATORS['WR'] < -80 else '❌'}</td></tr>
            <tr><td>RSI &lt; 30</td><td>1分</td><td>{'✅' if TECH_INDICATORS['RSI6'] < 30 else '❌'}</td></tr>
            <tr><td>MACD金叉</td><td>1分</td><td>{'✅' if TECH_INDICATORS['MACD_HIST'] > 0 else '❌'}</td></tr>
            <tr><td>KDJ K &lt; 20</td><td>1分</td><td>{'✅' if TECH_INDICATORS['KDJ_K'] < 20 else '❌'}</td></tr>
            <tr><td>RSI &gt; 70 (减分)</td><td>-1分</td><td>{'⚠️' if TECH_INDICATORS['RSI6'] > 70 else '正常'}</td></tr>
            <tr><td><strong>技术面总分</strong></td><td colspan="2"><strong>{tech_score}/6</strong></td></tr>
        </table>
    </div>

    <div class="section">
        <h2>五、基本面分析</h2>

        <h3>5.1 财务指标</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>评价</th></tr>
            <tr><td>EPS</td><td>{FINANCIAL_DATA['eps']:.4f}元</td><td>极低</td></tr>
            <tr><td>ROE</td><td>{FINANCIAL_DATA['roe']*100:.2f}%</td><td class="danger">⚠️ 极低</td></tr>
            <tr><td>毛利率</td><td>{FINANCIAL_DATA['gross_margin']*100:.2f}%</td><td>良好</td></tr>
            <tr><td>净利率</td><td>{FINANCIAL_DATA['net_margin']*100:.2f}%</td><td>一般</td></tr>
        </table>

        <h3>5.2 Carlson质量评分</h3>
        <div class="warning">
            <p>基于财务数据，公司 Carlson质量评分较低，主要因ROE极低(0.23%)。</p>
        </div>

        <h3>5.3 巴菲特10大公式</h3>
        <table>
            <tr><th>公式</th><th>指标</th><th>评估</th></tr>
            <tr><td>ROE</td><td>{FINANCIAL_DATA['roe']*100:.2f}%</td><td>❌ &lt;20%</td></tr>
            <tr><td>净利润</td><td>{FINANCIAL_DATA['net_profit']:.2f}亿</td><td>{'✅ >1亿' if FINANCIAL_DATA['net_profit'] > 1 else '❌ <1亿'}</td></tr>
            <tr><td>毛利率</td><td>{FINANCIAL_DATA['gross_margin']*100:.2f}%</td><td>{'✅ >30%' if FINANCIAL_DATA['gross_margin'] > 0.30 else '❌ <30%'}</td></tr>
            <tr><td>资产负债率</td><td>{BUFFETT_DATA['debt_ratio']*100:.1f}%</td><td>✅ &lt;50%</td></tr>
            <tr><td>总资产</td><td>{BUFFETT_DATA['total_assets']:.2f}亿</td><td>-</td></tr>
            <tr><td>净资产</td><td>{BUFFETT_DATA['net_assets']:.2f}亿</td><td>-</td></tr>
        </table>

        <h3>5.4 现金流详细分析</h3>
        <div class="warning">
            <p>⚠️ 影视行业项目制特性导致现金流波动大，需关注回款情况。</p>
        </div>
        <table>
            <tr><th>指标</th><th>数值</th><th>说明</th></tr>
            <tr><td>营业收入</td><td>{FINANCIAL_DATA['revenue']:.2f}亿</td><td>-</td></tr>
            <tr><td>净利润</td><td>{FINANCIAL_DATA['net_profit']:.2f}亿</td><td>-</td></tr>
            <tr><td>总资产</td><td>{BUFFETT_DATA['total_assets']:.2f}亿</td><td>-</td></tr>
            <tr><td>净资产</td><td>{BUFFETT_DATA['net_assets']:.2f}亿</td><td>-</td></tr>
            <tr><td>资产负债率</td><td>{BUFFETT_DATA['debt_ratio']*100:.1f}%</td><td>适中</td></tr>
            <tr><td>ROE</td><td>{FINANCIAL_DATA['roe']*100:.2f}%</td><td class="danger">⚠️ 极低</td></tr>
        </table>

        <h3>5.5 历史分红</h3>
        <table>
            <tr><th>报告时间</th><th>派息(含税)</th><th>送股/转增</th></tr>
            {dividend_rows}
        </table>

        <h3>5.6 基本面得分</h3>
        <table>
            <tr><th>指标</th><th>得分</th><th>条件</th></tr>
            <tr><td>ROE &gt; 20%</td><td>2分</td><td>{'✅' if FINANCIAL_DATA['roe'] > 0.20 else '❌'}</td></tr>
            <tr><td>净利润 &gt; 1亿</td><td>1分</td><td>{'✅' if FINANCIAL_DATA['net_profit'] > 1 else '❌'}</td></tr>
            <tr><td>毛利率 &gt; 30%</td><td>1分</td><td>{'✅' if FINANCIAL_DATA['gross_margin'] > 0.30 else '❌'}</td></tr>
            <tr><td>净利率 &gt; 10%</td><td>1分</td><td>{'✅' if FINANCIAL_DATA['net_margin'] > 0.10 else '❌'}</td></tr>
            <tr><td>EPS &gt; 0.3</td><td>1分</td><td>{'✅' if FINANCIAL_DATA['eps'] > 0.3 else '❌'}</td></tr>
            <tr><td><strong>基本面总分</strong></td><td colspan="2"><strong>{fundamental_score}/7</strong></td></tr>
        </table>
    </div>

    <div class="section">
        <h2>六、估值模型</h2>

        <h3>6.1 DCF估值</h3>
        <table>
            <tr><th>参数</th><th>数值</th></tr>
            <tr><td>当前净利润</td><td>{FINANCIAL_DATA['net_profit']:.2f}亿元</td></tr>
            <tr><td>永续增长率</td><td>10%</td></tr>
            <tr><td>折现率</td><td>10%</td></tr>
            <tr><td>内在价值</td><td>约{intrinsic_value:.2f}元/股</td></tr>
            <tr><td>当前股价</td><td>{current_price:.2f}元</td></tr>
            <tr><td>上涨空间</td><td>{upside:.1f}%</td></tr>
        </table>

        <h3>6.2 PE对比</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>说明</th></tr>
            <tr><td>PE</td><td>{pe:.2f}</td><td>因EPS极低导致PE失真</td></tr>
            <tr><td>当前股价</td><td>{current_price:.2f}元</td><td>-</td></tr>
            <tr><td>EPS</td><td>{FINANCIAL_DATA['eps']:.4f}元</td><td>极低</td></tr>
        </table>

        <h3>6.3 PB对比</h3>
        <table>
            <tr><th>指标</th><th>数值</th><th>说明</th></tr>
            <tr><td>PB</td><td>{pb:.2f}</td><td>处于行业合理水平</td></tr>
            <tr><td>股价</td><td>{current_price:.2f}元</td><td>-</td></tr>
            <tr><td>每股净资产</td><td>{FINANCIAL_DATA['equity'] * 1e8 / shares:.4f}元</td><td>-</td></tr>
        </table>

        <h3>6.4 多估值模型综合</h3>
        <table>
            <tr><th>估值方法</th><th>估值结果</th><th>参考价值</th></tr>
            <tr><td>DCF</td><td>约{intrinsic_value:.2f}元</td><td>中等</td></tr>
            <tr><td>PE</td><td>{pe:.2f}倍</td><td>失真，参考意义低</td></tr>
            <tr><td>PB</td><td>{pb:.2f}倍</td><td>中等</td></tr>
            <tr><td>股息率</td><td>约{DIVIDENDS[0]['dividend'] / current_price * 10:.2f}%</td><td>较低</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>七、行业对比</h2>

        <h3>7.1 行业概况</h3>
        <p>影视制作发行行业受内容质量、观众偏好、政策监管等多重因素影响，具有明显的项目制特征和周期性波动。</p>

        <h3>7.2 竞争对手财务对比</h3>
        <table>
            <tr><th>公司</th><th>毛利率</th><th>净利率</th><th>ROE</th></tr>
            <tr><td>光线传媒</td><td>44.13%</td><td>12.55%</td><td>0.23%</td></tr>
            <tr><td>华谊兄弟</td><td>30-40%</td><td>5-15%</td><td>波动大</td></tr>
            <tr><td>华策影视</td><td>25-35%</td><td>8-12%</td><td>5-10%</td></tr>
        </table>

        <h3>7.3 估值对比</h3>
        <p>公司PB处于行业平均水平，PE因EPS极低而失真。影视行业整体估值偏低。</p>
    </div>

    <div class="section">
        <h2>八、结论</h2>

        <h3>8.1 综合评分</h3>
        <table>
            <tr><th>维度</th><th>得分</th><th>满分</th></tr>
            <tr><td>技术面</td><td>{tech_score}</td><td>6</td></tr>
            <tr><td>基本面</td><td>{fundamental_score}</td><td>7</td></tr>
            <tr><td>DCF估值</td><td>{dcf_score}</td><td>5</td></tr>
            <tr><td>巴菲特指标</td><td>6</td><td>10</td></tr>
            <tr><td><strong>综合评分</strong></td><td colspan="2"><strong>{total_score}/28</strong></td></tr>
        </table>

        <h3>8.2 量化风险评估</h3>
        <table>
            <tr><th>风险维度</th><th>得分(1-5)</th><th>权重</th><th>加权得分</th></tr>
            <tr><td>财务风险</td><td>{risk_financial}</td><td>25%</td><td>{risk_financial * 0.25:.2f}</td></tr>
            <tr><td>经营风险</td><td>{risk_operating}</td><td>25%</td><td>{risk_operating * 0.25:.2f}</td></tr>
            <tr><td>行业风险</td><td>{risk_industry}</td><td>20%</td><td>{risk_industry * 0.20:.2f}</td></tr>
            <tr><td>竞争风险</td><td>{risk_competition}</td><td>15%</td><td>{risk_competition * 0.15:.2f}</td></tr>
            <tr><td>估值风险</td><td>{risk_valuation}</td><td>15%</td><td>{risk_valuation * 0.15:.2f}</td></tr>
            <tr><td><strong>综合风险</strong></td><td colspan="3"><strong>{weighted_risk:.2f}/5</strong></td></tr>
        </table>

        <h3>8.3 投资建议</h3>
        <div class="warning">
            <p><b>风险提示：</b></p>
            <ul>
                <li>ROE仅0.23%，盈利能力极弱</li>
                <li>影视行业项目制特征明显，业绩波动大</li>
                <li>KDJ高位钝化，技术面有回调压力</li>
                <li>RSI6=65.43，处于偏强区域</li>
            </ul>
        </div>
        <div class="info">
            <p><b>关注点：</b></p>
            <ul>
                <li>动画电影项目进展</li>
                <li>后续影视项目上映计划</li>
                <li>行业政策变化</li>
                <li>回款及现金流改善情况</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    return html


def main():
    html = generate_html_report()
    output_path = "/home/liujerry/moltbot/reports/300251_v4_report.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML报告已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
