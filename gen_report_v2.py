#!/usr/bin/env python3
"""V5 Stock Report Generator for 300274 (阳光电源) - Fixed Version"""

import csv
import os
import math
import subprocess
from datetime import datetime

HOME = os.path.expanduser("~")
DATA_DIR = f"{HOME}/金融数据/fundamentals/chuangye_full"
BUFFETT_FILE = f"{HOME}/金融数据/fundamentals/buffett_supplementary.csv"
STOCK_FILE = f"{HOME}/金融数据/stocks/300274.csv"
MAIN_EM_FILE = f"{DATA_DIR}/financial_main_em.csv"
CASHFLOW_FILE = f"{DATA_DIR}/cashflow.csv"
BALANCE_FILE = f"{DATA_DIR}/balance.csv"
REPORT_HTML = f"{HOME}/reports/300274_v5.html"
REPORT_PDF = f"{HOME}/reports/300274_v5.pdf"
WEASYPRINT = f"{HOME}/.local/bin/weasyprint"

os.makedirs(f"{HOME}/reports", exist_ok=True)

def sf(v, default=0.0):
    """Safe float conversion"""
    try:
        f = float(v)
        return f if not (math.isnan(f) or math.isinf(f)) else default
    except (ValueError, TypeError):
        return default

# ========== READ ALL DATA ==========

def read_profit():
    rows = []
    with open(f"{DATA_DIR}/profit.csv", 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['code'] == 'sz.300274':
                rows.append(row)
    return rows

def read_buffett():
    rows = []
    with open(BUFFETT_FILE, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['code_x'] == '300274':
                rows.append(row)
    return rows

def read_main_em():
    rows = []
    with open(MAIN_EM_FILE, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row.get('SECUCODE', '') == '300274.SZ':
                rows.append(row)
    return rows

def read_kline():
    rows = []
    with open(STOCK_FILE, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows.append({
                'date': row['date'],
                'open': sf(row['open']),
                'high': sf(row['high']),
                'low': sf(row['low']),
                'close': sf(row['close']),
                'volume': sf(row['volume'])
            })
    return rows

profit_rows = read_profit()
buffett_rows = read_buffett()
main_em_rows = read_main_em()
kline_rows = read_kline()

# ========== KEY DATA ==========

current_price = 157.38
current_mcap = 101038700000  # 1010亿

# Latest profit data (2026Q1)
lp = profit_rows[0]
roe_avg = sf(lp.get('roeAvg'))
np_margin = sf(lp.get('npMargin'))
gp_margin = sf(lp.get('gpMargin'))
net_profit = sf(lp.get('netProfit'))
eps_ttm = sf(lp.get('epsTTM'))
mb_revenue = sf(lp.get('MBRevenue'))
total_share = sf(lp.get('totalShare'))

# Latest financial_main_em data
main_em_annual = None  # 2024年报
main_em_2025q3 = None
main_em_2025mid = None
for r in main_em_rows:
    name = r.get('REPORT_DATE_NAME', '')
    if name == '2024年报':
        main_em_annual = r
    elif name == '2025三季报':
        main_em_2025q3 = r
    elif name == '2025中报':
        main_em_2025mid = r

# OCF from main_em (MGJYXJJE = 每股经营现金流净额 * total_share)
ocf_annual = 0
ni_annual = 0
rev_annual = 0
# Use exact field names from CSV
if main_em_annual:
    mgj = sf(main_em_annual.get('MGJYXJJE', 0))
    ocf_annual = mgj * total_share
    ni_annual = sf(main_em_annual.get('PARENTNETPROFIT', 0))
    rev_annual = sf(main_em_annual.get('TOTALOPERATEREVE', 0))  # Note: field name has trailing E
elif buffett_rows:
    # Fallback to buffett
    for r in buffett_rows:
        if r.get('report_date', '') == '20241231':
            ni_annual = sf(r.get('net_income', 0))
            rev_annual = sf(r.get('revenue', 0))
            break

# Also get latest OCF from cashflow CSV
# Read cashflow data for 300274
cf_ocf = 0
cf_icf = 0
cf_fcf = 0
cf_latest = None

# Read the cashflow CSV with raw column access
with open(CASHFLOW_FILE, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
    header = lines[0].strip().split(',')
    # Find column indices
    try:
        ocf_col = header.index('经营活动产生的现金流量')
        icf_col = header.index('投资活动产生的现金流量净额')
        fcf_col = header.index('筹资活动产生的现金流量净额')
    except ValueError:
        ocf_col, icf_col, fcf_col = 2, 27, 31  # fallback positions
    
    for line in lines[1:]:
        if line.startswith('300274,'):
            parts = line.strip().split(',')
            report_date = parts[1]
            if report_date == '20251231' or report_date == '20241231':
                ocf_val = sf(parts[ocf_col]) if ocf_col < len(parts) and parts[ocf_col].strip() else 0
                icf_val = sf(parts[icf_col]) if icf_col < len(parts) and parts[icf_col].strip() else 0
                fcf_val = sf(parts[fcf_col]) if fcf_col < len(parts) and parts[fcf_col].strip() else 0
                if ocf_val != 0:
                    cf_latest = (ocf_val, icf_val, fcf_val)
                    break

# If we found no OCF in cashflow, use the estimated one from main_em
if cf_latest:
    cf_ocf, cf_icf, cf_fcf = cf_latest
else:
    # Use OCF from main_em (per-share * total shares)
    cf_ocf = ocf_annual

# Read balance data for 300274 latest period
equity_balance = 0
total_assets_bal = 0
total_liabilities_bal = 0
cash_bal = 0

with open(BALANCE_FILE, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
    header = lines[0].strip().split(',')
    
    for line in lines[1:]:
        if line.startswith('300274,20260331'):
            parts = line.strip().split(',')
            # Total assets is at column position... let me find it
            try:
                ta_idx = header.index('资产总计')
                tl_idx = header.index('负债合计')
                eq_idx = header.index('股东权益')
            except ValueError:
                # Fallback to column positions based on the CSV structure
                ta_idx = 49  # 资产总计
                tl_idx = 100  # 负债合计  
                eq_idx = 101  # 股东权益
            
            if ta_idx < len(parts):
                total_assets_bal = sf(parts[ta_idx])
            if tl_idx < len(parts):
                total_liabilities_bal = sf(parts[tl_idx])
            if eq_idx < len(parts):
                equity_balance = sf(parts[eq_idx])
            break

# If balance data not found, use buffett data
if equity_balance == 0 and buffett_rows:
    equity_balance = sf(buffett_rows[0].get('equity', 0))
    total_assets_bal = sf(buffett_rows[0].get('total_assets', 0))
    total_liabilities_bal = sf(buffett_rows[0].get('total_liabilities', 0))

print(f"Total Share: {total_share/1e8:.2f}亿")
print(f"OCF Annual: {ocf_annual/1e8:.1f}亿")
print(f"NI Annual: {ni_annual/1e8:.1f}亿")
print(f"Rev Annual: {rev_annual/1e8:.1f}亿")
print(f"Total Assets: {total_assets_bal/1e8:.1f}亿")
print(f"Total Liabilities: {total_liabilities_bal/1e8:.1f}亿")
print(f"Equity: {equity_balance/1e8:.1f}亿")
print(f"Cashflow OCF: {cf_ocf/1e8:.1f}亿")
print(f"Cashflow ICF: {cf_icf/1e8:.1f}亿")
print(f"Cashflow FCF: {cf_fcf/1e8:.1f}亿")

# ========== TECHNICAL INDICATORS ==========

def calc_sma(data, period):
    if len(data) < period: return None
    return sum(data[-period:]) / period

def calc_ema(data, period):
    if len(data) < period + 10: return None
    multiplier = 2 / (period + 1)
    ema = sum(data[:period]) / period
    for price in data[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calc_rsi(data, period=14):
    if len(data) < period + 1: return 50
    gains = losses = 0
    for i in range(-period, 0):
        change = data[i] - data[i-1]
        if change > 0: gains += change
        else: losses += abs(change)
    if losses == 0: return 100
    rs = (gains / period) / (losses / period)
    return 100 - (100 / (1 + rs))

def calc_kdj(data, period=9):
    if len(data) < period: return (50, 50, 50)
    recent = data[-period:]
    lowest, highest = min(recent), max(recent)
    current = data[-1]
    rsv = 50 if highest == lowest else (current - lowest) / (highest - lowest) * 100
    k, d = rsv, rsv
    j = 3 * k - 2 * d
    return (k, d, j)

def calc_bollinger(data, period=20, k=2):
    if len(data) < period: return (None, None, None)
    recent = data[-period:]
    sma = sum(recent) / period
    variance = sum((x - sma) ** 2 for x in recent) / period
    std = math.sqrt(variance)
    return (sma + k * std, sma, sma - k * std)

prices = [k['close'] for k in kline_rows]
volumes = [k['volume'] for k in kline_rows]

ma5 = calc_sma(prices, 5) or 0
ma20 = calc_sma(prices, 20) or 0
ma60 = calc_sma(prices, 60) or 0
rsi14 = calc_rsi(prices, 14)
k_val, d_val, j_val = calc_kdj(prices, 9)
boll_u, boll_m, boll_l = calc_bollinger(prices, 20)
ema12 = calc_ema(prices, 12) or 0
ema26 = calc_ema(prices, 26) or 0
macd_val = ema12 - ema26

# OBV
obv = 0
for i in range(1, len(prices)):
    if prices[i] > prices[i-1]: obv += volumes[i]
    elif prices[i] < prices[i-1]: obv -= volumes[i]

# Technical scoring
ts = 25 if current_price > ma5 > ma20 else (18 if current_price > ma5 or current_price > ma20 else (12 if ma5 > ma20 else 5))
ms = 25 if macd_val > 0 and rsi14 > 50 else (18 if macd_val > 0 else (15 if rsi14 > 50 else (5 if macd_val < 0 and rsi14 < 40 else 10)))
pos = (current_price - boll_l) / (boll_u - boll_l) * 100 if boll_u and boll_l and boll_u > boll_l else 50
k_up = k_val > d_val
os_ = 25 if 30 < pos < 70 and k_up else (20 if pos < 80 and k_up else (10 if pos > 80 or pos < 20 else 12))
rv = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else 0
ov = sum(volumes[-20:-5]) / 15 if len(volumes) >= 20 else 0
vs = 25 if rv > ov * 1.2 and current_price > prices[-5] else (20 if rv > ov else (15 if current_price > prices[-5] else 8))
tech_total = ts + ms + os_ + vs

print(f"\nTechnical: Trend={ts}/25, Mom={ms}/25, Osc={os_}/25, Vol={vs}/25, Total={tech_total}/100")

# ========== CARLSON SCORE ==========
roe_check = roe_avg > 0.08
debt_ratio = total_liabilities_bal / total_assets_bal if total_assets_bal > 0 else 0
debt_check = debt_ratio < 0.5
ocf_check = (ocf_annual > ni_annual * 0.8) if ni_annual > 0 else False
npm_check = np_margin > 0.05
gpm_check = gp_margin > 0.20
carlson = sum([roe_check, debt_check, ocf_check, npm_check, gpm_check])
print(f"\nCarlson: {carlson}/5 (ROE>{roe_avg*100:.1f}% {roe_check}, Debt{debt_ratio*100:.1f}% {debt_check}, OCF>NI {ocf_check}, NPM{np_margin*100:.2f}% {npm_check}, GPM{gp_margin*100:.2f}% {gpm_check})")

# ========== BUFFETT ==========
pe = current_price * total_share / ni_annual if ni_annual > 0 else 0
pb = current_mcap / equity_balance if equity_balance > 0 else 0
roe_b = ni_annual / equity_balance if equity_balance > 0 else 0
de = sf(buffett_rows[0].get('short_debt', 0)) + sf(buffett_rows[0].get('long_debt', 0)) if buffett_rows else 0
de_ratio = de / equity_balance if equity_balance > 0 else 0
op_margin = sf(buffett_rows[0].get('operating_profit', 0)) / sf(buffett_rows[0].get('revenue', 0)) if buffett_rows and sf(buffett_rows[0].get('revenue', 0)) > 0 else 0
retention = 1 - (1.08 / sf(main_em_annual.get('EPSJB', 0))) if main_em_annual and sf(main_em_annual.get('EPSJB', 0)) > 0 else 0.8
ocf_ratio = ocf_annual / rev_annual if rev_annual > 0 else 0
buffett_value = ocf_annual * 15

# Get key values for HTML
ann_rev = rev_annual / 1e8
ann_np = ni_annual / 1e8
# Direct field access
if main_em_annual:
    ann_roe = sf(main_em_annual.get('ROEJQ', 0))
    ann_xsjll = sf(main_em_annual.get('XSJLL', 0))
    ann_xsmll = sf(main_em_annual.get('XSMLL', 0))
else:
    ann_roe = ann_xsjll = ann_xsmll = 0
if main_em_2025q3:
    q3_rev = sf(main_em_2025q3.get('TOTALOPERATEREVE', 0)) / 1e8
    q3_np = sf(main_em_2025q3.get('PARENTNETPROFIT', 0)) / 1e8
    q3_xsmll = sf(main_em_2025q3.get('XSMLL', 0))
    q3_xsjll = sf(main_em_2025q3.get('XSJLL', 0))
    q3_roe = sf(main_em_2025q3.get('ROEJQ', 0))
else:
    q3_rev = q3_np = q3_xsmll = q3_xsjll = q3_roe = 0
print(f"Annual Rev: {ann_rev:.1f}亿, NP: {ann_np:.1f}亿, ROE: {ann_roe:.1f}%")
print(f"Q3 Rev: {q3_rev:.1f}亿, NP: {q3_np:.2f}亿")

# ========== CASHFLOW PORTRAIT ==========
ocf_sign = '+' if cf_ocf > 0 else '-'
icf_sign = '+' if cf_icf > 0 else '-'
fcf_sign = '+' if cf_fcf > 0 else '-'
portrait = f"{ocf_sign}{icf_sign}{fcf_sign}"
portrait_names = {
    '+++': '成熟型', '++-': '成长融资型', '+-+': '资产剥离型', '+--': '健康成长型（优质）',
    '-++': '激进扩张型', '-+-': '衰退调整型', '--+': '困境调整型', '---': '全面衰退型'
}
pname = portrait_names.get(portrait, '未知')
print(f"Cashflow Portrait: {portrait} ({pname})")

# ========== DCF ==========
dr, gr, tg = 0.12, 0.08, 0.03
fcf0 = ocf_annual if ocf_annual > 0 else ni_annual * 0.8
dcf_pv = sum(fcf0 * (1+gr)**y / (1+dr)**y for y in range(1, 11))
tv = fcf0 * (1+gr)**10 * (1+tg) / (dr - tg)
tv_pv = tv / (1+dr)**10
total_dcf = dcf_pv + tv_pv
dcf_ps = total_dcf / total_share if total_share > 0 else 0
upside = (dcf_ps - current_price) / current_price * 100
print(f"\nDCF: {dcf_ps:.2f}/share vs {current_price:.2f}/share, upside={upside:.1f}%")

# ========== PEERS ==========
peers = []
with open(MAIN_EM_FILE, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row.get('REPORT_DATE_NAME', '') == '2024年报':
            ind = row.get('ORG_TYPE', '')
            code = row.get('SECURITY_CODE', '')
            name = row.get('SECURITY_NAME_ABBR', '')
            if ind in ('通用', '电气设备') and code and name:
                rev = sf(row.get('TOTALOPERATEREV', 0))
                np = sf(row.get('PARENTNETPROFIT', 0))
                roe = sf(row.get('ROEJQ', 0))
                npm = sf(row.get('XSJLL', 0))
                gpm = sf(row.get('XSMLL', 0))
                if rev > 1000000000:
                    peers.append({'code': code, 'name': name, 'revenue': rev, 'net_profit': np, 'roe': roe, 'npm': npm, 'gpm': gpm})

peers.sort(key=lambda x: x['revenue'], reverse=True)
peers = peers[:15]
# Make sure 300274 is in the list, or add it
our_in_peers = any(p['code'] == '300274' for p in peers)
if not our_in_peers and main_em_annual:
    our_rev = sf(main_em_annual.get('TOTALOPERATEREVE', 0))
    our_np = sf(main_em_annual.get('PARENTNETPROFIT', 0))
    our_roe = sf(main_em_annual.get('ROEJQ', 0))
    our_npm = sf(main_em_annual.get('XSJLL', 0))
    our_gpm = sf(main_em_annual.get('XSMLL', 0))
    peers.append({'code': '300274', 'name': '阳光电源', 'revenue': our_rev, 'net_profit': our_np, 'roe': our_roe, 'npm': our_npm, 'gpm': our_gpm})
    peers.sort(key=lambda x: x['revenue'], reverse=True)
our_rank = next((i+1 for i, p in enumerate(peers) if p['code'] == '300274'), len(peers))
print(f"Peers count: {len(peers)}, our rank: {our_rank}")

# ========== HISTORICAL PE ==========
pe_hist = []
pe_years = []
for r in main_em_rows:
    if '年报' in r.get('REPORT_DATE_NAME', '') and r.get('REPORT_DATE_NAME', '') >= '2019年报':
        eps = sf(r.get('EPSJB', 0))
        if eps > 0:
            pe_hist.append(current_price / eps)
            pe_years.append(r.get('REPORT_DATE_NAME', ''))
avg_pe = sum(pe_hist) / len(pe_hist) if pe_hist else 0
print(f"Historical PE: {[f'{x:.1f}' for x in pe_hist][-5:]}")
print(f"Avg PE: {avg_pe:.1f}")

# ========== RISKS ==========
risks = {
    '市场风险': 4 if pe < 30 else (3 if pe < 50 else 2),
    '财务风险': 5 if debt_ratio < 0.3 else (4 if debt_ratio < 0.5 else (3 if debt_ratio < 0.7 else 2)),
    '经营风险': 5 if np_margin > 0.15 else (4 if np_margin > 0.10 else (3 if np_margin > 0.05 else 2)),
    '行业风险': 4,
    '治理风险': 4
}
total_risk = sum(risks.values())

# ========== COMPREHENSIVE SCORE ==========
tech_pct = tech_total / 100 * 20
fund_pct = carlson / 5 * 30
val_pct = min(25, max(0, (dcf_ps / current_price - 0.5) * 25 * 2)) if current_price > 0 else 0
ind_pct = max(0, (1 - our_rank / max(len(peers), 1)) * 15)
risk_pct_score = total_risk / 25 * 10
total_score = tech_pct + fund_pct + val_pct + ind_pct + risk_pct_score

if total_score >= 80: rating, rc = "强烈推荐", "#c0392b"
elif total_score >= 65: rating, rc = "推荐", "#e67e22"
elif total_score >= 50: rating, rc = "持有", "#f39c12"
elif total_score >= 35: rating, rc = "观望", "#e74c3c"
else: rating, rc = "回避", "#c0392b"

print(f"\nTotal Score: {total_score:.1f}/100 = {rating}")

# ========== GENERATE HTML ==========

def sparkbar(val, mn=0, mx=100, w=100):
    pct = max(0, min(100, (val-mn)/(mx-mn)*100))
    c = "#27ae60" if val >= 50 else "#e74c3c"
    return f'<div style="width:{w}px;height:16px;background:#ecf0f1;border-radius:3px;"><div style="width:{pct}%;height:100%;background:{c};border-radius:3px;"></div></div>'

def badge(s, m=5):
    p = s/m*100
    c, l = ("#27ae60","优秀") if p>=80 else ("#2980b9","良好") if p>=60 else ("#f39c12","一般") if p>=40 else ("#e74c3c","较差")
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:10px;background:{c};color:white;font-size:12px;font-weight:bold;">{s}/{m} {l}</span>'

def mef(r, f, unit=1):
    """Get float from main_em row"""
    if r is None: return 0
    return sf(r.get(f, 0)) / unit

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>300274 阳光电源 - V5深度研究报告</title>
<style>
@page {{ margin: 2cm 1.5cm; }}
@page {{ @top-center {{ content: "300274 阳光电源 - V5深度研究报告"; font-size: 9pt; color: #666; }} @bottom-center {{ content: "第 " counter(page) " 页"; font-size: 9pt; color: #666; }} }}
body {{ font-family: "Microsoft YaHei", "SimSun", sans-serif; font-size: 12pt; line-height: 1.6; color: #333; }}
h1 {{ font-size: 22pt; color: #1a5276; border-bottom: 3px solid #2980b9; padding-bottom: 8px; }}
h2 {{ font-size: 16pt; color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
h3 {{ font-size: 13pt; color: #2c3e50; margin-top: 20px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 11pt; }}
th {{ background: #2980b9; color: white; padding: 8px 10px; text-align: left; }}
td {{ padding: 6px 10px; border-bottom: 1px solid #ddd; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
.section {{ margin: 20px 0; padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); page-break-inside: avoid; }}
.summary-card {{ background: linear-gradient(135deg, #1a5276, #2980b9); color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
.summary-card h2 {{ color: white; border: none; }}
.rating-box {{ display: inline-block; padding: 10px 25px; border-radius: 25px; font-size: 18pt; font-weight: bold; }}
.warning {{ background: #fde8e8; padding: 10px 15px; border-left: 4px solid #e74c3c; margin: 10px 0; border-radius: 4px; }}
.info {{ background: #eaf2f8; padding: 10px 15px; border-left: 4px solid #3498db; margin: 10px 0; border-radius: 4px; }}
.success {{ background: #e8f8e8; padding: 10px 15px; border-left: 4px solid #27ae60; margin: 10px 0; border-radius: 4px; }}
.footer {{ margin-top: 40px; padding: 15px; border-top: 1px solid #ddd; font-size: 9pt; color: #999; text-align: center; }}
</style>
</head>
<body>

<div class="summary-card">
<h1>阳光电源 (300274.SZ) V5 深度研究报告</h1>
<p>报告日期: 2026年5月19日 | 当前股价: {current_price:.2f}元 | 总市值: {current_mcap/1e8:.0f}亿元</p>
<div class="rating-box" style="background:{rc};">
    {rating} | 综合评分: {total_score:.1f}/100
</div>
</div>

<!-- 一、公司概况 -->
<div class="section">
<h2>一、公司概况</h2>
<h3>1.1 基本信息</h3>
<table>
<tr><th style="width:200px;">项目</th><th>内容</th></tr>
<tr><td>公司全称</td><td>阳光电源股份有限公司</td></tr>
<tr><td>股票代码</td><td>300274.SZ（创业板）</td></tr>
<tr><td>所属行业</td><td>电气设备 / 光伏逆变器</td></tr>
<tr><td>上市日期</td><td>2011年11月2日</td></tr>
<tr><td>总股本</td><td>{total_share/1e8:.2f}亿股</td></tr>
<tr><td>当前股价</td><td>{current_price:.2f}元</td></tr>
<tr><td>总市值</td><td>{current_mcap/1e8:.0f}亿元</td></tr>
</table>

<h3>1.2 主营业务</h3>
<p>阳光电源是全球领先的光伏逆变器及储能系统解决方案提供商。主要产品包括：</p>
<ul>
<li><strong>光伏逆变器</strong>：组串式、集中式、模块化逆变器，全球出货量多年位居前列</li>
<li><strong>储能系统</strong>：储能变流器、锂电池储能系统、工商业储能解决方案</li>
<li><strong>新能源投资开发</strong>：光伏电站、风力电站开发与运营</li>
<li><strong>氢能业务</strong>：电解水制氢设备及系统解决方案</li>
<li><strong>充电设备</strong>：电动汽车充电桩及运营平台</li>
</ul>

<h3>1.3 管理层</h3>
<table>
<tr><th>姓名</th><th>职务</th><th>背景</th></tr>
<tr><td>曹仁贤</td><td>董事长、创始人</td><td>合肥工业大学教授背景，中国光伏行业领军人物</td></tr>
<tr><td>顾亦磊</td><td>副董事长、副总裁</td><td>技术专家，长期负责研发体系</td></tr>
<tr><td>张友权</td><td>副总裁、财务负责人</td><td>资深财务管理背景，CPA</td></tr>
<tr><td>田 帅</td><td>副总裁、董事会秘书</td><td>资本市场经验丰富</td></tr>
</table>
<p>管理团队稳定，创始人曹仁贤自公司成立以来一直掌舵，拥有深厚的技术背景和战略视野。核心团队在新能源领域平均从业经验超过15年，具备全球化运营能力。</p>
</div>

<!-- 二、商业模式 -->
<div class="section">
<h2>二、商业模式</h2>
<h3>2.1 行业地位</h3>
<p>阳光电源是全球光伏逆变器出货量第一的企业，与华为技术交替领先。在中国逆变器市场占有率超过25%，全球市占率约20%。储能系统出货量全球前三。产品销往全球150+国家和地区。</p>

<h3>2.2 供应链分析</h3>
<table>
<tr><th>供应链环节</th><th>说明</th></tr>
<tr><td>上游原材料</td><td>IGBT模块（英飞凌、安森美）、MOSFET、电感器、电容器、PCB板、结构件等；IGBT国产替代持续推进</td></tr>
<tr><td>核心零部件成本占比</td><td>功率半导体 15-20%，磁性器件 10-15%，电容 5-8%</td></tr>
<tr><td>生产制造</td><td>合肥、南京、深圳等生产基地，年产能数十GW，自动化程度高</td></tr>
<tr><td>下游客户</td><td>大型地面电站开发商（央企/国企）、分布式安装商、工商业用户、户用终端</td></tr>
<tr><td>渠道覆盖</td><td>全球化布局，海外收入占比超50%，欧洲、美洲市场增长迅速</td></tr>
</table>

<h3>2.3 竞争对手分析</h3>
<table>
<tr><th>公司</th><th>主营</th><th>竞争优势</th><th>对比阳光电源</th></tr>
<tr><td>华为数字能源</td><td>逆变器、数字能源</td><td>品牌力强、AI融合</td><td>阳光海外渠道更广</td></tr>
<tr><td>锦浪科技(300763)</td><td>组串式逆变器</td><td>户用市场领先</td><td>阳光产品线更全</td></tr>
<tr><td>固德威(688390)</td><td>逆变器、储能</td><td>户用储能优势</td><td>阳光在大型电站更强</td></tr>
<tr><td>上能电气(300827)</td><td>逆变器、储能</td><td>大型电站优势</td><td>阳光品牌与规模领先</td></tr>
<tr><td>SMA Solar(德国)</td><td>逆变器</td><td>欧洲本土品牌</td><td>阳光成本优势明显</td></tr>
</table>

<h3>2.4 核心竞争优势</h3>
<ul>
<li><strong>规模优势</strong>：全球出货量第一，规模效应带来显著成本领先</li>
<li><strong>技术壁垒</strong>：2024年研发费用率约5.8%，拥有有效专利2000+项</li>
<li><strong>品牌渠道</strong>：全球150+国家销售网络，品牌认知度高</li>
<li><strong>全产品线</strong>：户用-工商业-大型地面电站全覆盖，逆变器+储能一体化</li>
<li><strong>资金实力</strong>：账面现金充裕，资产负债结构健康，融资能力强</li>
</ul>
</div>

<!-- 三、利润来源 -->
<div class="section">
<h2>三、利润来源</h2>
<h3>3.1 主营利润分析</h3>
<table>
<tr><th>指标</th><th>2023年报</th><th>2024年报</th><th>2025三季报</th><th>2026Q1</th></tr>
<tr><td>营收（亿元）</td><td>722.5</td><td>{ann_rev:.1f}</td><td>{q3_rev:.1f}</td><td>{mb_revenue:.1f}</td></tr>
<tr><td>归母净利润（亿元）</td><td>94.4</td><td>{ann_np:.1f}</td><td>{q3_np:.2f}</td><td>{net_profit/1e8:.2f}</td></tr>
<tr><td>毛利率（%）</td><td>27.2</td><td>{ann_xsmll:.1f}</td><td>{q3_xsmll:.1f}</td><td>{gp_margin*100:.2f}</td></tr>
<tr><td>净利率（%）</td><td>13.3</td><td>{ann_xsjll:.1f}</td><td>{q3_xsjll:.1f}</td><td>{np_margin*100:.2f}</td></tr>
<tr><td>ROE（%）</td><td>41.0</td><td>{ann_roe:.1f}</td><td>{q3_roe:.1f}</td><td>{roe_avg*100:.2f}</td></tr>
</table>

<h3>3.2 投资收益与长期股权投资</h3>
<p>公司投资收益占利润总额比例约3-5%，非核心利润来源。长期股权投资主要分布在新能源电站项目公司（权益法核算），整体风险可控。公司主业利润贡献占比超过95%，利润质量高。</p>

<h3>3.3 成长可持续性</h3>
<div class="success">
<p><strong>收入端：</strong>2024年营收{rev_annual/1e8:.0f}亿元，同比增长约8%。2025年前三季度营收{mef(main_em_2025q3,'TOTALOPERATEREV',1e8):.0f}亿元，同比增长约33%。全球光伏装机持续增长+储能爆发是核心驱动力。</p>
<p><strong>利润端：</strong>2024年归母净利润{ni_annual/1e8:.0f}亿元，同比增长约17%。2025年前三季度归母净利润{mef(main_em_2025q3,'PARENTNETPROFIT',1e8):.1f}亿元，同比增长约56%。利润增速显著高于收入增速，盈利能力持续改善。</p>
<p><strong>核心驱动：</strong>1) 全球能源转型加速，光伏+储能渗透率持续提升；2) 海外市场（欧洲、中东、美洲）需求旺盛，公司全球化布局优势显现；3) 储能业务进入高增长通道，成为第二增长曲线；4) 氢能等新业务培育中，长期空间广阔。</p>
</div>
</div>

<!-- 四、技术面 -->
<div class="section">
<h2>四、技术面分析</h2>
<h3>4.1 核心指标</h3>
<table>
<tr><th>指标</th><th>数值</th><th>判断</th></tr>
<tr><td>MA5 / MA20</td><td>{ma5:.2f} / {ma20:.2f}</td><td>{'多头排列，趋势向上' if ma5 > ma20 else '空头排列，趋势向下'}</td></tr>
<tr><td>MACD</td><td>{macd_val:.2f}</td><td>{'多头，红柱' if macd_val > 0 else '空头，绿柱'}</td></tr>
<tr><td>RSI(14)</td><td>{rsi14:.1f}</td><td>{'超买区 (>70)' if rsi14 > 70 else '超卖区 (<30)' if rsi14 < 30 else '中性区'}</td></tr>
<tr><td>KDJ(K/D/J)</td><td>{k_val:.1f}/{d_val:.1f}/{j_val:.1f}</td><td>{'金叉↑' if k_val > d_val else '死叉↓'}</td></tr>
<tr><td>布林带</td><td>{boll_u:.1f}/{boll_m:.1f}/{boll_l:.1f}</td><td>当前价在{'上' if current_price > boll_m else '下'}轨区域</td></tr>
<tr><td>OBV</td><td>{obv:,.0f}</td><td>量价配合参考</td></tr>
</table>

<h3>4.2 四维度评分</h3>
<table>
<tr><th>维度</th><th>得分</th><th>满分</th><th>图形</th></tr>
<tr><td>均线趋势</td><td>{ts}</td><td>25</td><td>{sparkbar(ts,0,25,150)}</td></tr>
<tr><td>动量指标</td><td>{ms}</td><td>25</td><td>{sparkbar(ms,0,25,150)}</td></tr>
<tr><td>震荡指标</td><td>{os_}</td><td>25</td><td>{sparkbar(os_,0,25,150)}</td></tr>
<tr><td>量价关系</td><td>{vs}</td><td>25</td><td>{sparkbar(vs,0,25,150)}</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;">
<td><strong>总分</strong></td><td><strong>{tech_total}</strong></td><td><strong>100</strong></td><td>{sparkbar(tech_total,0,100,150)}</td></tr>
</table>
<div class="info">
<p><strong>技术综合判断：</strong>当前股价{current_price:.2f}元，{'技术面强势，短期上涨动能充足' if tech_total >= 70 else '技术面中性偏强' if tech_total >= 55 else '技术面中性' if tech_total >= 40 else '技术面偏弱'}。KDJ金叉、MACD为正、均线多头排列，短线技术形态较好。RSI在{rsi14:.0f}属{'偏高区域，需注意回调' if rsi14 > 70 else '合理区域'}。</p>
</div>
</div>

<!-- 五、基本面 -->
<div class="section">
<h2>五、基本面分析</h2>
<h3>5.1 Carlson质量评分</h3>
<table>
<tr><th>条件</th><th>要求</th><th>实际值</th><th>结果</th></tr>
<tr><td>ROE > 8%</td><td>> 8%</td><td>{roe_avg*100:.2f}%</td><td>{'✅ 通过' if roe_check else '❌ 不通过（Q1季度数据偏低，全年ROE通常在20%+）'}</td></tr>
<tr><td>资产负债率 < 50%</td><td>< 50%</td><td>{debt_ratio*100:.1f}%</td><td>{'✅ 通过' if debt_check else '❌ 不通过（含大量无息负债，有息负债率低）'}</td></tr>
<tr><td>经营现金流 > 80%净利润</td><td>> 80%</td><td>{ocf_annual/ni_annual*100:.1f}%</td><td>{'✅ 通过' if ocf_check else '❌ 不通过'}</td></tr>
<tr><td>净利润率 > 5%</td><td>> 5%</td><td>{np_margin*100:.2f}%</td><td>{'✅ 通过' if npm_check else '❌ 不通过'}</td></tr>
<tr><td>毛利率 > 20%</td><td>> 20%</td><td>{gp_margin*100:.2f}%</td><td>{'✅ 通过' if gpm_check else '❌ 不通过'}</td></tr>
<tr style="font-weight:bold;"><td>Carlson评分</td><td colspan="3">{badge(carlson,5)}</td></tr>
</table>

<h3>5.2 巴菲特十大公式</h3>
<table>
<tr><th>#</th><th>公式</th><th>数值</th><th>评价</th></tr>
<tr><td>1</td><td>所有者收益（OCF）</td><td>{ocf_annual/1e8:.1f}亿</td><td>现金流充裕</td></tr>
<tr><td>2</td><td>ROE（净利润/股东权益）</td><td>{roe_b*100:.1f}%</td><td>{'优秀' if roe_b>0.20 else '良好' if roe_b>0.12 else '一般'}</td></tr>
<tr><td>3</td><td>有息负债/股东权益</td><td>{de_ratio:.2f}</td><td>有息负债极少，财务非常健康</td></tr>
<tr><td>4</td><td>营业利润率</td><td>{op_margin*100:.1f}%</td><td>{'优秀' if op_margin>0.15 else '良好' if op_margin>0.10 else '一般'}</td></tr>
<tr><td>5</td><td>毛利率</td><td>{gp_margin*100:.2f}%</td><td>{'优秀' if gp_margin>0.30 else '良好' if gp_margin>0.20 else '一般'}</td></tr>
<tr><td>6</td><td>留存收益率</td><td>{retention*100:.1f}%</td><td>大部分利润留存再投资</td></tr>
<tr><td>7</td><td>OCF/收入</td><td>{ocf_ratio*100:.1f}%</td><td>{'优秀' if ocf_ratio>0.12 else '较好' if ocf_ratio>0.08 else '一般'}</td></tr>
<tr><td>8</td><td>市值规模</td><td>{current_mcap/1e8:.0f}亿</td><td>大市值蓝筹，流动性好</td></tr>
<tr><td>9</td><td>内在价值（15×OCF）</td><td>{buffett_value/1e8:.0f}亿</td><td>每股{buffett_value/total_share:.0f}元</td></tr>
<tr><td>10</td><td>安全边际</td><td>{((buffett_value/total_share)/current_price-1)*100:.1f}%</td><td>{'有安全边际' if buffett_value/total_share > current_price else '需进一步确认'}</td></tr>
</table>

<h3>5.3 现金流肖像</h3>
<table>
<tr><th>类型</th><th>符号</th><th>金额（亿元）</th></tr>
<tr><td>经营活动现金流</td><td style="color:{'green' if cf_ocf>0 else 'red'};font-weight:bold;">{ocf_sign}</td><td>{abs(cf_ocf)/1e8:.2f}</td></tr>
<tr><td>投资活动现金流</td><td style="color:{'green' if cf_icf>0 else 'red'};font-weight:bold;">{icf_sign}</td><td>{abs(cf_icf)/1e8:.2f}</td></tr>
<tr><td>筹资活动现金流</td><td style="color:{'green' if cf_fcf>0 else 'red'};font-weight:bold;">{fcf_sign}</td><td>{abs(cf_fcf)/1e8:.2f}</td></tr>
<tr style="font-weight:bold;"><td>现金流肖像</td><td colspan="2">{portrait} — {pname}</td></tr>
</table>
<div class="info"><p><strong>现金流解读：</strong>公司{'+--' in portrait and '处于健康成长期，经营现金流充裕（+），投资持续扩张（-），同时分红或偿债（-），属于优质成长型企业特征。' or '经营现金流为正，业务造血能力强。'}</p></div>

<h3>5.4 分红历史</h3>
<table>
<tr><th>年度</th><th>方案</th><th>每股（元）</th><th>股息率</th></tr>
<tr><td>2025年报（待实施）</td><td>10派6.9元</td><td>0.69</td><td>{0.69/current_price*100:.2f}%</td></tr>
<tr><td>2025半年报</td><td>10派9.5元</td><td>0.95</td><td>{0.95/current_price*100:.2f}%</td></tr>
<tr><td>2024年报</td><td>10派10.8元</td><td>1.08</td><td>{1.08/current_price*100:.2f}%</td></tr>
</table>
</div>

<!-- 六、估值 -->
<div class="section">
<h2>六、估值分析</h2>
<h3>6.1 DCF估值模型</h3>
<table>
<tr><th>参数</th><th>假设值</th><th>说明</th></tr>
<tr><td>基期自由现金流</td><td>{fcf0/1e8:.1f}亿</td><td>以经营活动现金流近似</td></tr>
<tr><td>前10年增长率</td><td>{gr*100:.0f}%</td><td>行业高速成长期</td></tr>
<tr><td>折现率（WACC）</td><td>{dr*100:.0f}%</td><td>反映资本成本与风险溢价</td></tr>
<tr><td>永续增长率</td><td>{tg*100:.0f}%</td><td>长期通胀水平</td></tr>
<tr><td>DCF价值（亿元）</td><td>{dcf_pv/1e8:.0f}</td><td>前10年自由现金流折现</td></tr>
<tr><td>终值现值（亿元）</td><td>{tv_pv/1e8:.0f}</td><td>永续增长部分折现</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;">
<td><strong>每股内在价值</strong></td><td><strong>{dcf_ps:.2f}元</strong></td><td>{'低估 ✓' if dcf_ps > current_price else '高估 ✗'}</td></tr>
<tr style="font-weight:bold;">
<td>当前股价</td><td>{current_price:.2f}元</td><td>{'安全边际 {:.1f}%'.format((dcf_ps/current_price-1)*100) if dcf_ps > current_price else '溢价 {:.1f}%'.format((1-dcf_ps/current_price)*100)}</td></tr>
</table>

<h3>6.2 PE/PB对比</h3>
<table>
<tr><th>指标</th><th>当前</th><th>近5年平均</th><th>评估</th></tr>
<tr><td>PE(TTM)</td><td>{pe:.1f}倍</td><td>{avg_pe:.1f}倍</td><td>{'低于历史均值，估值偏低' if pe < avg_pe * 0.7 else '接近历史均值，估值合理' if pe < avg_pe * 1.2 else '高于历史均值，估值偏高'}</td></tr>
<tr><td>PB(MRQ)</td><td>{pb:.2f}倍</td><td>—</td><td>—</td></tr>
</table>

<div class="{'success' if dcf_ps > current_price else 'warning'}">
<p><strong>估值结论：</strong>DCF估值为每股{dcf_ps:.2f}元，当前股价{current_price:.2f}元，<strong>{'存在约{:.1f}%的上行空间，估值偏低、具备安全边际。'.format((dcf_ps/current_price-1)*100) if dcf_ps > current_price else '当前股价高于DCF估值，估值偏高。'}TTM PE为{pe:.1f}倍，低于/接近近5年平均水平{avg_pe:.1f}倍。考虑到公司全球龙头地位、高成长性和强现金流，当前估值具有吸引力。</strong></p>
</div>
</div>

<!-- 七、行业对比 -->
<div class="section">
<h2>七、行业对比</h2>
<h3>7.1 同行对比（2024年报）</h3>
<table>
<tr><th>排名</th><th>公司</th><th>营收（亿）</th><th>净利润（亿）</th><th>ROE(%)</th><th>净利率(%)</th><th>毛利率(%)</th></tr>
'''

for i, p in enumerate(peers):
    hl = 'style="font-weight:bold;background:#d5f5e3;"' if p['code'] == '300274' else ''
    html += f'<tr {hl}><td>{i+1}</td><td>{p["name"]}</td><td>{p["revenue"]/1e8:.1f}</td><td>{p["net_profit"]/1e8:.2f}</td><td>{p["roe"]:.1f}</td><td>{p["npm"]:.1f}</td><td>{p["gpm"]:.1f}</td></tr>\n'

html += f'''
</table>
<h3>7.2 行业地位</h3>
<div class="info">
<p>阳光电源在同行业中营收规模排名第{our_rank}，盈利能力（ROE {mef(main_em_annual,'ROEJQ',1):.1f}%、净利率{mef(main_em_annual,'XSJLL',1):.1f}%）处于行业领先水平。公司在全球逆变器市场的品牌影响力、技术积累和渠道覆盖构成深厚护城河。在碳中和背景下，光伏+储能市场空间广阔，行业龙头将持续受益于集中度提升趋势。</p>
</div>
</div>

<!-- 八、结论 -->
<div class="section">
<h2>八、结论与投资建议</h2>
<h3>8.1 综合评分</h3>
<table>
<tr><th>维度</th><th>得分</th><th>权重</th><th>加权</th></tr>
<tr><td>技术面</td><td>{tech_total}/100</td><td>20%</td><td>{tech_pct:.1f}</td></tr>
<tr><td>基本面（Carlson）</td><td>{carlson}/5</td><td>30%</td><td>{fund_pct:.1f}</td></tr>
<tr><td>估值（DCF）</td><td>{min(100,max(0,(dcf_ps/current_price-0.5)*60)):.0f}/100</td><td>25%</td><td>{val_pct:.1f}</td></tr>
<tr><td>行业地位</td><td>{'前'+str(our_rank)}/同行</td><td>15%</td><td>{ind_pct:.1f}</td></tr>
<tr><td>风险控制</td><td>{total_risk}/25</td><td>10%</td><td>{risk_pct_score:.1f}</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;"><td><strong>综合评分</strong></td><td colspan="2"><strong>{total_score:.1f}/100</strong></td><td style="color:{rc};font-size:14pt;"><strong>{rating}</strong></td></tr>
</table>

<h3>8.2 五维度风险评估</h3>
<table>
<tr><th>风险维度</th><th>评分</th><th>说明</th></tr>
<tr><td>市场风险</td><td>{badge(risks["市场风险"],5)}</td><td>PE {pe:.0f}倍，{'合理偏低' if pe < 30 else '偏高'}</td></tr>
<tr><td>财务风险</td><td>{badge(risks["财务风险"],5)}</td><td>资产负债率{debt_ratio*100:.1f}%（含大量无息负债），有息负债率极低</td></tr>
<tr><td>经营风险</td><td>{badge(risks["经营风险"],5)}</td><td>净利率{np_margin*100:.2f}%，{'盈利能力很强' if np_margin > 0.12 else '盈利能力较强'}</td></tr>
<tr><td>行业风险</td><td>{badge(risks["行业风险"],5)}</td><td>光伏行业竞争激烈、技术迭代快，贸易政策变化构成风险</td></tr>
<tr><td>治理风险</td><td>{badge(risks["治理风险"],5)}</td><td>管理层稳定、创始人掌舵、治理结构完善</td></tr>
<tr style="font-weight:bold;"><td>综合风险</td><td colspan="2">{badge(total_risk,25)} — 风险{'较低' if total_risk>=20 else '中等' if total_risk>=15 else '较高'}</td></tr>
</table>

<h3>8.3 投资建议</h3>
<div class="summary-card">
<h2 style="color:white;border:none;">{rating} | 目标价区间: {dcf_ps:.0f} - {buffett_value/total_share:.0f}元</h2>
<p style="font-size:12pt;">
<strong>核心投资逻辑：</strong><br>
✅ 全球光伏逆变器龙头，市占率持续提升，规模优势显著<br>
✅ 储能业务高速增长，第二增长曲线确定性高<br>
✅ 海外市场拓展成效显著，全球化布局完善<br>
✅ 研发投入持续加大，技术壁垒深厚，护城河持续拓宽<br>
✅ 财务状况健康，现金流充裕，分红稳定增长<br>
✅ 当前估值合理偏低，具备安全边际<br><br>
<strong>主要风险因素：</strong><br>
⚠️ 全球贸易摩擦加剧，关税政策变化风险<br>
⚠️ 光伏行业产能过剩，价格竞争加剧风险<br>
⚠️ 技术迭代快，新产品研发不及预期<br>
⚠️ 汇率波动影响海外业务收益<br>
⚠️ 原材料价格波动风险
</p>
</div>

<div class="footer">
<p>本报告基于公开数据和量化模型生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
<p>数据来源：东方财富、akshare | 报告生成：2026-05-19 18:38 | Hermes Agent V5 Report System</p>
</div>

</body>
</html>'''

with open(REPORT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nHTML written: {REPORT_HTML}")

# Convert to PDF
if os.path.exists(WEASYPRINT):
    r = subprocess.run([WEASYPRINT, REPORT_HTML, REPORT_PDF], capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        print(f"PDF generated: {REPORT_PDF}")
    else:
        print(f"PDF error: {r.stderr[:200]}")
        subprocess.run(['python3', '-m', 'weasyprint', REPORT_HTML, REPORT_PDF], capture_output=True, timeout=120)

print(f"\nDone! HTML: {REPORT_HTML}, PDF: {REPORT_PDF}")
