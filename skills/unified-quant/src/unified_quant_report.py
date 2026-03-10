#!/usr/bin/env python3
"""
统一量化分析报告生成器
生成包含：宏观、基本面(价值投资)、技术面、行为金融、行业景气的完整报告
"""

import akshare as ak
import baostock as bs
import pandas as pd
import json
import glob
import numpy as np
from datetime import datetime
from pathlib import Path

# ========== 配置 ==========
WATCHLIST = [
    ('300276', '三丰智能'),
    ('300199', '翰宇药业'),
    ('301381', '待确认'),
    ('300502', '新易盛'),
    ('300394', '天孚通信'),
    ('300308', '中际旭创'),
    ('300628', '亿联网络'),
    ('300573', '兴齐眼药'),
    ('300533', '冰川网络'),
    ('300274', '阳光电源'),
    ('300251', '光线传媒'),
    ('300604', '长川科技'),
    ('300456', '赛微电子'),
    ('300926', '博俊科技'),
]

DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")
OUTPUT_DIR = Path("/home/liujerry/reports")

# ========== 工具函数 ==========
def calc_rsi(p, n=14):
    """计算RSI"""
    d = p.diff()
    g = d.where(d>0, 0).rolling(n).mean()
    l = (-d.where(d<0, 0)).rolling(n).mean()
    return 100 - (100/(1+g/l))

def calc_bb(p, n=20):
    """计算布林带"""
    ma = p.rolling(n).mean()
    std = p.rolling(n).std()
    return ma, ma+2*std, ma-2*std

# ========== 获取技术面数据 ==========
def get_technical_data():
    """获取技术面数据"""
    print("获取技术面数据...")
    lg = bs.login()
    results = []
    
    for code, name in WATCHLIST:
        full_code = f'sz.{code}'
        rs = bs.query_history_k_data_plus(full_code, 'date,close', '2025-01-01', '2026-03-05', 'd', '3')
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        
        if len(data) < 50:
            continue
        
        df = pd.DataFrame(data, columns=['date','close'])
        df['close'] = pd.to_numeric(df['close'], errors='coerce').dropna()
        
        # 计算指标
        rsi = calc_rsi(df['close'], 14)
        ma20, upper, lower = calc_bb(df['close'], 20)
        
        price = df['close'].iloc[-1]
        rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        lower_val = lower.iloc[-1] if not pd.isna(lower.iloc[-1]) else price
        
        # 信号判断
        if rsi_val < 20 and price <= lower_val * 1.05:
            signal = '买入'
        elif rsi_val < 30:
            signal = '关注'
        else:
            signal = '观望'
        
        results.append({
            'code': code,
            'name': name,
            'price': round(price, 2),
            'rsi14': round(rsi_val, 1),
            'lower': round(lower_val, 2),
            'signal': signal,
        })
    
    bs.logout()
    return results

# ========== 获取基本面数据 ==========
def get_fundamental_data():
    """从本地CSV获取基本面数据"""
    print("获取基本面数据...")
    stocks = [code for code, _ in WATCHLIST]
    
    files = glob.glob(str(DATA_DIR / "a_stock_financial_batch*.csv"))
    
    all_data = []
    for f in files:
        try:
            df = pd.read_csv(f, usecols=['code', '报告期', '净资产收益率', '销售净利率', '销售毛利率', '基本每股收益', '每股净资产', '净利润'])
            matched = df[df['code'].astype(str).isin(stocks)]
            if len(matched) > 0:
                all_data.append(matched)
        except:
            pass
    
    if not all_data:
        return {}
    
    df = pd.concat(all_data, ignore_index=True)
    latest = df.sort_values('报告期', ascending=False).drop_duplicates('code')
    
    result = {}
    for _, row in latest.iterrows():
        code = str(row['code'])
        roe = row.get('净资产收益率', 'N/A')
        npm = row.get('销售净利率', 'N/A')
        gpm = row.get('销售毛利率', 'N/A')
        eps = row.get('基本每股收益', 'N/A')
        bvps = row.get('每股净资产', 'N/A')
        
        # 处理ROE格式
        if isinstance(roe, str) and '%' in roe:
            roe = roe
        elif pd.notna(roe):
            roe = f"{roe*100:.2f}%" if roe < 1 else f"{roe:.2f}%"
        
        result[code] = {
            'ROE': roe,
            '净利润率': npm,
            '毛利率': gpm,
            'EPS': eps,
            'BVPS': bvps,
        }
    
    return result

# ========== 获取分红数据 ==========
def get_dividend_data():
    """获取分红数据"""
    print("获取分红数据...")
    stocks = [code for code, _ in WATCHLIST]
    
    dividend_data = {}
    for code in stocks:
        try:
            df = ak.stock_dividend_cninfo(symbol=code)
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                dividend_data[code] = latest.get('实施方案分红说明', 'N/A')
        except:
            dividend_data[code] = 'N/A'
    
    return dividend_data

# ========== 获取宏观数据 ==========
def get_macro_data():
    """获取宏观数据"""
    print("获取宏观数据...")
    return {
        'GDP': '5.2%',
        'CPI': '0.5%',
        'USD_CNY': '6.8973',
        'MLF': '2.50%',
    }

# ========== 生成HTML报告 ==========
def generate_html_report(technical, fundamentals, dividends, macro):
    """生成HTML报告"""
    
    # 按ROE排序基本面
    fund_sorted = sorted(fundamentals.items(), key=lambda x: 
        float(str(x[1].get('ROE', '0%')).replace('%','')) if x[1].get('ROE') not in ['N/A', None] else 0, 
        reverse=True)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
body {{ font-family: 'Noto Sans SC', 'Microsoft YaHei', Arial; font-size: 9pt; line-height: 1.5; color: #333; max-width: 800px; margin: 0 auto; padding: 20px 15px; }}
h1 {{ font-size: 15pt; color: #1a1a1a; text-align: center; margin-bottom: 3px; }}
h2 {{ font-size: 10.5pt; color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding: 4px 0; margin: 14px 0 8px 0; }}
h3 {{ font-size: 9.5pt; color: #555; margin: 10px 0 5px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 8pt; }}
th, td {{ border: 1px solid #bbb; padding: 4px 6px; text-align: left; }}
th {{ background: linear-gradient(135deg, #2c5aa0, #4a7bc4); color: white; }}
tr:nth-child(even) {{ background-color: #f8f9fa; }}
.buy {{ color: #28a745; font-weight: 700; }}
.watch {{ color: #f59e0b; font-weight: 700; }}
.hold {{ color: #6c757d; }}
.text-right {{ text-align: right; }}
.highlight {{ background-color: #fff8e1; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 12px 0; }}
.footer {{ text-align: center; color: #888; font-size: 7pt; margin-top: 12px; }}
</style>
</head>
<body>

<h1>📈 统一量化分析报告</h1>
<p style="text-align:center;color:#666;font-size:8pt">生成时间: {datetime.now().strftime('%Y-%m-%d')}</p>

<h2>🌍 宏观分析</h2>
<table>
<tr><th style="width:30%">指标</th><th>数值</th><th>说明</th></tr>
<tr><td>中国GDP</td><td class="text-right">{macro.get('GDP', 'N/A')}</td><td>2025年增速</td></tr>
<tr><td>CPI</td><td class="text-right">{macro.get('CPI', 'N/A')}</td><td>通胀温和</td></tr>
<tr><td>USD/CNY</td><td class="text-right">{macro.get('USD_CNY', 'N/A')}</td><td>人民币汇率</td></tr>
<tr><td>MLF利率</td><td class="text-right">{macro.get('MLF', 'N/A')}</td><td>货币政策</td></tr>
</table>

<h2>💰 基本面分析 (价值投资)</h2>
<table>
<tr><th>代码</th><th>ROE</th><th>净利润率</th><th>毛利率</th><th>EPS</th><th>分红(最新)</th></tr>
'''
    
    # 添加基本面数据
    name_map = {code: name for code, name in WATCHLIST}
    for code, fund in fund_sorted:
        name = name_map.get(code, code)
        div = dividends.get(code, 'N/A')
        roe = fund.get('ROE', 'N/A')
        npm = fund.get('净利润率', 'N/A')
        gpm = fund.get('毛利率', 'N/A')
        eps = fund.get('EPS', 'N/A')
        
        # 格式化为百分比
        if isinstance(npm, float):
            npm = f"{npm*100:.2f}%" if npm < 1 else f"{npm:.2f}%"
        if isinstance(gpm, float):
            gpm = f"{gpm*100:.2f}%" if gpm < 1 else f"{gpm:.2f}%"
        
        html += f'<tr><td>{code} {name}</td><td class="text-right">{roe}</td><td class="text-right">{npm}</td><td class="text-right">{gpm}</td><td class="text-right">{eps}</td><td>{div}</td></tr>\n'
    
    html += f'''</table>
<p style="font-size:7.5pt;color:#666">数据来源: A股财务+分红 | 报告期: 2025Q3 | 分红时间: 历史最新</p>

<h2>📊 技术面分析 - 保守策略</h2>
<p><strong>策略: RSI14 &lt; 20 + 布林带下轨</strong></p>
<table>
<tr><th>代码</th><th>收盘价</th><th class="text-right">RSI14</th><th class="text-right">布林下轨</th><th>信号</th></tr>
'''
    
    # 添加技术面数据
    tech_sorted = sorted(technical, key=lambda x: x['rsi14'])
    for t in tech_sorted:
        cls = 'highlight' if t['signal'] == '关注' else ''
        signal_cls = 'watch' if t['signal'] == '关注' else ('hold' if t['signal'] == '观望' else 'buy')
        signal_icon = '👀' if t['signal'] == '关注' else ('🏷️' if t['signal'] == '观望' else '📈')
        html += f'<tr class="{cls}"><td>{t["code"]} {t["name"]}</td><td>{t["price"]}</td><td class="text-right">{t["rsi14"]}</td><td class="text-right">{t["lower"]}</td><td class="{signal_cls}">{signal_icon} {t["signal"]}</td></tr>\n'
    
    # 统计
    buy_count = len([t for t in technical if t['signal'] == '买入'])
    watch_count = len([t for t in technical if t['signal'] == '关注'])
    hold_count = len([t for t in technical if t['signal'] == '观望'])
    
    html += f'''</table>

<h2>🧠 行为金融分析</h2>
<table>
<tr><th style="width:25%">偏差类型</th><th style="width:35%">当前市场表现</th><th>应对策略</th></tr>
<tr><td><strong>损失厌恶</strong></td><td>近期创业板回调，投资者恐慌抛售，RSI逼近超卖区域</td><td>遵守策略纪律，不因恐惧改变既定买入条件</td></tr>
<tr><td><strong>锚定效应</strong></td><td>投资者仍锚定2025年高点</td><td>关注基本面和估值，而非历史价格锚点</td></tr>
<tr><td><strong>从众心理</strong></td><td>市场情绪低迷，资金流出科技股</td><td>逆向投资，在超卖时积累优质筹码</td></tr>
<tr><td><strong>过度自信</strong></td><td>部分投资者认为可以准确预测底部</td><td>承认择时困难，坚持定投/分批建仓</td></tr>
<tr><td><strong>处置效应</strong></td><td>投资者倾向卖出盈利股，持有亏损股</td><td>定期检视，卖出已达目标的盈利股</td></tr>
</table>

<h2>🏭 行业景气度</h2>
<table>
<tr><th style="width:30%">行业</th><th style="width:20%">景气度</th><th>建议</th></tr>
<tr><td>AI算力/光模块</td><td>⭐⭐⭐⭐⭐</td><td>中际旭创、天孚通信、新易盛 - 高景气</td></tr>
<tr><td>半导体</td><td>⭐⭐⭐⭐</td><td>长川科技、赛微电子 - 国产替代</td></tr>
<tr><td>新能源/电源</td><td>⭐⭐⭐⭐</td><td>阳光电源 - 龙头稳固</td></tr>
<tr><td>医药/眼科</td><td>⭐⭐⭐</td><td>翰宇药业、兴齐眼药 - 稳定</td></tr>
<tr><td>影视传媒</td><td>⭐⭐</td><td>光线传媒 - 周期性强</td></tr>
</table>

<h2>📈 统计</h2>
<table>
<tr><td>分析股票</td><td class="text-right">{len(technical)}</td></tr>
<tr><td class="buy">📈 买入</td><td class="text-right">{buy_count}</td></tr>
<tr><td class="watch">👀 关注</td><td class="text-right">{watch_count}</td></tr>
<tr><td class="hold">🏷️ 观望</td><td class="text-right">{hold_count}</td></tr>
</table>

<h2>💡 投资建议</h2>
<p><strong>结论：</strong><span class="buy">{"无买入信号，等待RSI<20时机" if buy_count == 0 else f"买入{buy_count}只股票"}</span></p>

<p><strong>价值投资Top3 (ROE+分红)：</strong></p>
<ol style="font-size:8.5pt">
'''
    
    # Top3推荐
    for i, (code, fund) in enumerate(fund_sorted[:3]):
        div = dividends.get(code, 'N/A')
        name = name_map.get(code, code)
        html += f'<li><strong>{code} {name}</strong> - ROE {fund.get("ROE","N/A")}, 分红{div}</li>\n'
    
    html += '''</ol>

<p><strong>风险提示：</strong></p>
<ul style="font-size:8pt">
<li>控制仓位，不超过30%</li>
<li>关注人民币汇率波动</li>
<li>科技股估值较高，回调风险</li>
</ul>

<hr>
<p class="footer">统一量化分析系统 | 数据: Baostock + A股财务 + 分红</p>

</body>
</html>'''
    
    return html

# ========== 主函数 ==========
def main():
    print("="*50)
    print("统一量化分析报告生成器")
    print("="*50)
    
    # 获取数据
    macro = get_macro_data()
    technical = get_technical_data()
    fundamentals = get_fundamental_data()
    dividends = get_dividend_data()
    
    # 生成HTML
    html = generate_html_report(technical, fundamentals, dividends, macro)
    
    # 保存HTML
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d')
    html_file = OUTPUT_DIR / f"量化分析报告_{date_str}.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nHTML报告已保存: {html_file}")
    
    # 返回文件路径
    return str(html_file)

if __name__ == '__main__':
    main()
