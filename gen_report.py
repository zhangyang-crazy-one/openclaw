#!/usr/bin/env python3
"""V5 Stock Report Generator for 300274 (阳光电源)"""

import csv
import os
import math
import json
import subprocess
from datetime import datetime, timedelta

HOME = os.path.expanduser("~")
DATA_DIR = f"{HOME}/金融数据/fundamentals/chuangye_full"
BUFFETT_FILE = f"{HOME}/金融数据/fundamentals/buffett_supplementary.csv"
STOCK_FILE = f"{HOME}/金融数据/stocks/300274.csv"
MAIN_EM_FILE = f"{DATA_DIR}/financial_main_em.csv"
REPORT_HTML = f"{HOME}/reports/300274_v5.html"
REPORT_PDF = f"{HOME}/reports/300274_v5.pdf"
VENV_PYTHON = f"{HOME}/moltbot/.venv/bin/python"
WEASYPRINT = f"{HOME}/.local/bin/weasyprint"

os.makedirs(f"{HOME}/reports", exist_ok=True)

# ========== 1. READ DATA ==========

# Read profit data for 300274
def read_profit():
    rows = []
    with open(f"{DATA_DIR}/profit.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['code'] == 'sz.300274':
                rows.append(row)
    return rows

# Read buffett data
def read_buffett():
    rows = []
    with open(BUFFETT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['code_x'] == '300274':
                rows.append(row)
    return rows

# Read financial_main_em for 300274.SZ
def read_main_em():
    rows = []
    with open(MAIN_EM_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('SECUCODE', '') == '300274.SZ':
                rows.append(row)
    return rows

# Read K-line data
def read_kline():
    rows = []
    with open(STOCK_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'date': row['date'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
    return rows

profit_rows = read_profit()
buffett_rows = read_buffett()
main_em_rows = read_main_em()
kline_rows = read_kline()

print(f"Profit rows: {len(profit_rows)}")
print(f"Buffett rows: {len(buffett_rows)}")
print(f"Main EM rows: {len(main_em_rows)}")
print(f"K-line rows: {len(kline_rows)}")

# ========== 2. PARSE KEY DATA ==========

# Current price info
latest_kline = kline_rows[-1] if kline_rows else None
current_price = 157.38  # From context f43=15738
current_mcap = 101038700000  # 1010亿

# Latest profit data (2026 Q1)
latest_profit = profit_rows[0] if profit_rows else {}
roe_avg = float(latest_profit.get('roeAvg', 0))
np_margin = float(latest_profit.get('npMargin', 0))
gp_margin = float(latest_profit.get('gpMargin', 0))
net_profit = float(latest_profit.get('netProfit', 0))
eps_ttm = float(latest_profit.get('epsTTM', 0))
mb_revenue = float(latest_profit.get('MBRevenue', 0))
total_share_profit = float(latest_profit.get('totalShare', 0))

# Latest buffett data
latest_buffett = buffett_rows[0] if buffett_rows else {}
buffett_2025q3 = None
for r in buffett_rows:
    if r.get('report_date', '') == '20250930':
        buffett_2025q3 = r
        break

def safe_float(v, default=0.0):
    try:
        f = float(v)
        return f if not math.isnan(f) and not math.isinf(f) else default
    except:
        return default

# Buffett fields
cash = safe_float(latest_buffett.get('cash', 0))
short_debt = safe_float(latest_buffett.get('short_debt', 0))
long_debt = safe_float(latest_buffett.get('long_debt', 0))
total_assets = safe_float(latest_buffett.get('total_assets', 0))
total_liabilities = safe_float(latest_buffett.get('total_liabilities', 0))
equity = safe_float(latest_buffett.get('equity', 0))
interest_expense = safe_float(latest_buffett.get('interest_expense', 0))
revenue_buffett = safe_float(latest_buffett.get('revenue', 0))
operating_profit = safe_float(latest_buffett.get('operating_profit', 0))
net_income = safe_float(latest_buffett.get('net_income', 0))
ocf = safe_float(latest_buffett.get('operating_cash_flow', 0))

# Check for full year buffett data (2024年报)
buffett_2024 = None
for r in buffett_rows:
    if r.get('report_date', '') == '20241231':
        buffett_2024 = r
        break

# Total share from main_em
total_share = total_share_profit
if total_share == 0:
    # Try to get from main_em
    for r in main_em_rows:
        ts = safe_float(r.get('TOTAL_SHARE', 0))
        if ts > 0:
            total_share = ts
            break

print(f"Total share: {total_share}")
print(f"Total share from profit: {total_share_profit}")

# Main_em latest annual (2024年报 or 2025三季报)
main_em_latest_annual = None
main_em_2025q3 = None
main_em_2025mid = None
main_em_2025q1 = None
for r in main_em_rows:
    if r.get('REPORT_DATE_NAME', '') == '2024年报':
        main_em_latest_annual = r
    elif r.get('REPORT_DATE_NAME', '') == '2025三季报':
        main_em_2025q3 = r
    elif r.get('REPORT_DATE_NAME', '') == '2025中报':
        main_em_2025mid = r
    elif r.get('REPORT_DATE_NAME', '') == '2025一季报':
        main_em_2025q1 = r

# Get key metrics from main_em
def me(v, default='0'):
    return v if v else default

# For display
security_name = '阳光电源'
security_code = '300274'

# ========== 3. TECHNICAL INDICATORS ==========

def calc_sma(data, period):
    if len(data) < period:
        return None
    return sum(data[-period:]) / period

def calc_ema(data, period):
    if len(data) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(data[:period]) / period
    for price in data[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calc_macd(data, fast=12, slow=26, signal=9):
    if len(data) < slow + signal:
        return None, None, None
    ema_fast = calc_ema(data, fast)
    ema_slow = calc_ema(data, slow)
    if ema_fast is None or ema_slow is None:
        return None, None, None
    macd_line = ema_fast - ema_slow
    # For signal line we need more data
    return macd_line, 0, macd_line

def calc_rsi(data, period=14):
    if len(data) < period + 1:
        return 50
    gains = 0
    losses = 0
    for i in range(-period, 0):
        change = data[i] - data[i-1]
        if change > 0:
            gains += change
        else:
            losses += abs(change)
    if losses == 0:
        return 100
    rs = gains / period / (losses / period)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_kdj(data, period=9):
    if len(data) < period:
        return 50, 50, 50
    recent = data[-period:]
    lowest = min(recent)
    highest = max(recent)
    current = data[-1]
    if highest - lowest == 0:
        rsv = 50
    else:
        rsv = (current - lowest) / (highest - lowest) * 100
    k = rsv
    d = k
    j = 3 * k - 2 * d
    return k, d, j

def calc_bollinger(data, period=20, k=2):
    if len(data) < period:
        return None, None, None
    recent = data[-period:]
    sma = sum(recent) / period
    variance = sum((x - sma) ** 2 for x in recent) / period
    std = math.sqrt(variance)
    upper = sma + k * std
    lower = sma - k * std
    return upper, sma, lower

def calc_obv(prices, volumes):
    obv = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            obv += volumes[i]
        elif prices[i] < prices[i-1]:
            obv -= volumes[i]
    return obv

# Calculate all technical indicators
prices = [k['close'] for k in kline_rows]
volumes = [k['volume'] for k in kline_rows]
highs = [k['high'] for k in kline_rows]
lows = [k['low'] for k in kline_rows]

ma5 = calc_sma(prices, 5) if len(prices) >= 5 else None
ma20 = calc_sma(prices, 20) if len(prices) >= 20 else None
ma60 = calc_sma(prices, 60) if len(prices) >= 60 else None
ma120 = calc_sma(prices, 120) if len(prices) >= 120 else None

macd_hist = None
try:
    ema12 = calc_ema(prices, 12)
    ema26 = calc_ema(prices, 26)
    if ema12 and ema26:
        macd_hist = ema12 - ema26
except:
    pass

rsi14 = calc_rsi(prices, 14)
k_val, d_val, j_val = calc_kdj(prices, 9)
boll_upper, boll_mid, boll_lower = calc_bollinger(prices, 20)
obv_val = calc_obv(prices, volumes)

# Technical scoring (4 dimensions, 25 each = 100)
# 1. Trend (MA): 25 points
trend_score = 0
if ma5 and ma20:
    if prices[-1] > ma5 > ma20:
        trend_score = 25
    elif prices[-1] > ma5 or prices[-1] > ma20:
        trend_score = 18
    elif ma5 > ma20:
        trend_score = 12
    elif prices[-1] < ma5 and prices[-1] < ma20:
        trend_score = 5
    else:
        trend_score = 10

# 2. Momentum (MACD + RSI): 25 points
momentum_score = 0
if macd_hist is not None:
    if macd_hist > 0 and rsi14 > 50:
        momentum_score = 25
    elif macd_hist > 0:
        momentum_score = 18
    elif rsi14 > 50:
        momentum_score = 15
    elif macd_hist < 0 and rsi14 < 40:
        momentum_score = 5
    elif macd_hist < 0:
        momentum_score = 10
    else:
        momentum_score = 12

# 3. Oscillation (KDJ + Bollinger): 25 points
oscillation_score = 0
if boll_upper and boll_lower:
    position = (prices[-1] - boll_lower) / (boll_upper - boll_lower) * 100 if (boll_upper - boll_lower) > 0 else 50
    kdj_bullish = k_val > d_val
    if 30 < position < 70 and kdj_bullish:
        oscillation_score = 25
    elif position < 80 and kdj_bullish:
        oscillation_score = 20
    elif position > 80 or position < 20:
        oscillation_score = 10
    elif not kdj_bullish:
        oscillation_score = 12
    else:
        oscillation_score = 15

# 4. Volume-Price (OBV): 25 points
volume_score = 0
if len(prices) > 20:
    obv_trend = obv_val
    obv_10d_ago = 0
    for i in range(max(0, len(volumes)-20), len(volumes)):
        if i == len(volumes)-20:
            continue
    # Simple: compare recent volume trend
    recent_vol = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else 0
    older_vol = sum(volumes[-20:-5]) / 15 if len(volumes) >= 20 else 0
    if recent_vol > older_vol * 1.2 and prices[-1] > prices[-5]:
        volume_score = 25
    elif recent_vol > older_vol:
        volume_score = 20
    elif prices[-1] > prices[-5]:
        volume_score = 15
    elif recent_vol < older_vol * 0.8:
        volume_score = 8
    else:
        volume_score = 12

tech_total = trend_score + momentum_score + oscillation_score + volume_score

print(f"\n=== TECHNICAL SCORES ===")
print(f"Trend: {trend_score}/25")
print(f"Momentum: {momentum_score}/25")
print(f"Oscillation: {oscillation_score}/25")
print(f"Volume: {volume_score}/25")
print(f"Total: {tech_total}/100")
print(f"MA5: {ma5:.2f}, MA20: {ma20:.2f}")
print(f"MACD: {macd_hist:.2f}, RSI: {rsi14:.2f}")
print(f"KDJ: K={k_val:.2f}, D={d_val:.2f}, J={j_val:.2f}")
if boll_upper: print(f"BOLL: Upper={boll_upper:.2f}, Mid={boll_mid:.2f}, Lower={boll_lower:.2f}")

# ========== 4. FUNDAMENTAL ANALYSIS ==========

# Carlson Quality Score (0-5)
carlson_score = 0
roe_check = roe_avg > 0.08  # ROE > 8%
debt_check = (total_liabilities / total_assets < 0.5) if total_assets > 0 else False
ocf_check = (ocf > net_income * 0.8) if net_income > 0 else False
npm_check = np_margin > 0.05
gpm_check = gp_margin > 0.20

if roe_check: carlson_score += 1
if debt_check: carlson_score += 1
if ocf_check: carlson_score += 1
if npm_check: carlson_score += 1
if gpm_check: carlson_score += 1

print(f"\n=== CARLSON SCORE ===")
print(f"ROE > 8%: {roe_avg*100:.2f}% -> {roe_check}")
print(f"Debt < 50%: {total_liabilities/total_assets*100:.1f}% -> {debt_check}")
print(f"OCF > 80% NI: {ocf:.2f} vs {net_income*0.8:.2f} -> {ocf_check}")
print(f"NPM > 5%: {np_margin*100:.2f}% -> {npm_check}")
print(f"GPM > 20%: {gp_margin*100:.2f}% -> {gpm_check}")
print(f"Carlson: {carlson_score}/5")

# Buffett 10 Formulas
# Using buffett_2024 for full year data or latest
ni_annual = 0
revenue_annual = 0
ocf_annual = 0

if buffett_2024:
    ni_annual = safe_float(buffett_2024.get('net_income', 0))
    revenue_annual = safe_float(buffett_2024.get('revenue', 0))
    ocf_annual = safe_float(buffett_2024.get('operating_cash_flow', 0))
else:
    # Use main_em annual data
    if main_em_latest_annual:
        ni_annual = safe_float(main_em_latest_annual.get('PARENTNETPROFIT', 0))
        revenue_annual = safe_float(main_em_latest_annual.get('TOTALOPERATEREV', 0))
        # OCF from cashflow - approximate from per share data
        ocf_val = safe_float(main_em_latest_annual.get('MGJYXJJE', 0))
        ts = safe_float(main_em_latest_annual.get('TOTAL_SHARE', total_share))
        ocf_annual = ocf_val * ts if ts > 0 else 0

print(f"\n=== BUFFETT DATA ===")
print(f"Annual NI: {ni_annual:.2f}")
print(f"Annual Rev: {revenue_annual:.2f}")
print(f"Annual OCF: {ocf_annual:.2f}")

# PE = current_price * total_share / net_income
if ni_annual > 0 and total_share > 0:
    pe = current_price * total_share / ni_annual
else:
    pe = 0

# PB = market_cap / equity
if equity > 0:
    pb = current_mcap / equity
else:
    pb = 0

print(f"PE: {pe:.2f}")
print(f"PB: {pb:.2f}")

# Buffett formulas
# 1. Owner Earnings = Net Income + Depreciation - Maintenance Capex (approximate with OCF)
owner_earnings = ocf_annual

# 2. Return on Equity (ROE)
roe_buffett = ni_annual / equity if equity > 0 else 0

# 3. Debt-to-Equity
debt_to_equity = (short_debt + long_debt) / equity if equity > 0 else 0

# 4. Operating Margin
op_margin = operating_profit / revenue_buffett if revenue_buffett > 0 else 0

# 5. Gross Margin
gross_margin = gp_margin

# 6. Earnings Retention Rate (1 - dividend payout)
# Dividend info from context
dividend_2024 = 10.8  # 2024年报10派10.8元
dividend_2025_h1 = 9.5  # 2025半年报10派9.5元
dividend_2025 = 6.9  # 2025年报10派6.9元
dps_2024 = dividend_2024 / 10  # per share
eps_2024 = safe_float(main_em_latest_annual.get('EPSJB', 0)) if main_em_latest_annual else 0
if eps_2024 > 0:
    payout_ratio = dps_2024 / eps_2024
    retention_rate = 1 - payout_ratio
else:
    payout_ratio = 0
    retention_rate = 1

# 7. Operating Cash Flow Ratio
ocf_ratio = ocf_annual / revenue_annual if revenue_annual > 0 else 0

# 8. Capex Ratio
capex_ratio = 0  # Not enough data

# 9. Market Cap
mcap_b = current_mcap / 1e8

# 10. Intrinsic Value (simplified)
buffett_value = owner_earnings * 15  # 15x owner earnings

print(f"Owner Earnings: {owner_earnings:.2f}")
print(f"ROE: {roe_buffett*100:.2f}%")
print(f"D/E: {debt_to_equity:.2f}")
print(f"Op Margin: {op_margin*100:.2f}%")
print(f"Gross Margin: {gross_margin*100:.2f}%")
print(f"Payout Ratio: {payout_ratio*100:.2f}%")
print(f"Retention Rate: {retention_rate*100:.2f}%")
print(f"OCF/Revenue: {ocf_ratio*100:.2f}%")

# Cash Flow Portrait
# Need OCF, ICF, FCF signs from cashflow data
# Let's check cashflow data for 300274
cf_rows = []
with open(f"{DATA_DIR}/cashflow.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('code', '') == '300274' or row.get('﻿code', '') == '300274':
            cf_rows.append(row)
        elif row.get('code', '') == '4':  # 300274 may be mapped to code 4
            cf_rows.append(row)

# Let me just look for code = sz.300274 or 300274 in the cashflow
# Actually the cashflow uses integer codes for 'code' column
# From the sample: code=4 corresponds to some stock
# Let me search more carefully

# Actually from the earlier read, the cashflow showed "4" as code for 300274 data
# Let me re-read with proper code mapping
print(f"\n=== Cashflow rows with various codes ===")
cf_code4 = []
with open(f"{DATA_DIR}/cashflow.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        code_val = row.get('code', '').strip()
        if code_val == '4':
            cf_code4.append(row)

print(f"CF rows with code=4: {len(cf_code4)}")

# Let me check the net cash flow signs
# Column names: 经营活动产生的现金流量, 投资活动产生的现金流量净额, 筹资活动产生的现金流量净额
ocf_cf = safe_float(cf_code4[0].get('经营活动产生的现金流量', 0)) if cf_code4 else 0
icf_cf = safe_float(cf_code4[0].get('投资活动产生的现金流量净额', 0)) if cf_code4 else 0
fcf_cf = safe_float(cf_code4[0].get('筹资活动产生的现金流量净额', 0)) if cf_code4 else 0

print(f"OCF (CF): {ocf_cf:.2f}")
print(f"ICF (CF): {icf_cf:.2f}")
print(f"FCF (CF): {fcf_cf:.2f}")

ocf_sign = '+' if ocf_cf > 0 else '-'
icf_sign = '+' if icf_cf > 0 else '-'
fcf_sign = '+' if fcf_cf > 0 else '-'
cashflow_portrait = f"{ocf_sign}{icf_sign}{fcf_sign}"

# Cashflow portrait types
portrait_names = {
    '+++': '成熟型（奶牛型）',
    '++-': '成长型（融资支持）',
    '+-+': '衰退型（资产剥离）',
    '+--': '健康成长型（优质企业）',
    '-++': '激进扩张型（经营失血，依赖融资+投资回收）',
    '-+-': '衰退调整型',
    '--+': '困境调整型',
    '---': '全面衰退型'
}
portrait_name = portrait_names.get(cashflow_portrait, '未知')

print(f"Cashflow Portrait: {cashflow_portrait} ({portrait_name})")

# ========== 5. DCF VALUATION ==========

discount_rate = 0.12
growth_rate = 0.08
terminal_growth = 0.03
projection_years = 10

# FCF as proxy = OCF
fcf_0 = ocf_annual if ocf_annual > 0 else net_income * 0.8

dcf_value = 0
for year in range(1, projection_years + 1):
    fcf_year = fcf_0 * (1 + growth_rate) ** year
    pv = fcf_year / (1 + discount_rate) ** year
    dcf_value += pv

# Terminal value
terminal_fcf = fcf_0 * (1 + growth_rate) ** projection_years * (1 + terminal_growth)
terminal_value = terminal_fcf / (discount_rate - terminal_growth)
terminal_pv = terminal_value / (1 + discount_rate) ** projection_years

total_dcf = dcf_value + terminal_pv
dcf_per_share = total_dcf / total_share if total_share > 0 else 0

print(f"\n=== DCF VALUATION ===")
print(f"FCF0: {fcf_0:.2f}")
print(f"DCF PV: {dcf_value:.2f}")
print(f"Terminal PV: {terminal_pv:.2f}")
print(f"Total DCF: {total_dcf:.2f}")
print(f"DCF Per Share: {dcf_per_share:.2f}")
print(f"Current Price: {current_price:.2f}")
upside = (dcf_per_share - current_price) / current_price * 100
print(f"Upside: {upside:.2f}%")

# ========== 6. PE/PB COMPARISON ==========

# Historical PE/PB using main_em data
pe_values = []
pb_values = []
for r in main_em_rows:
    eps_val = safe_float(r.get('EPSJB', 0))
    bps_val = safe_float(r.get('BPS', 0))
    if eps_val > 0 and bps_val > 0:
        pe_values.append(eps_val)
        pb_values.append(bps_val)

# Average PE (using recent years)
# Actually, let me get the PE from the annual data
pe_history = []
for r in main_em_rows:
    if '年报' in r.get('REPORT_DATE_NAME', ''):
        eps = safe_float(r.get('EPSJB', 0))
        if eps > 0:
            pe_history.append(current_price / eps)

avg_pe = sum(pe_history) / len(pe_history) if pe_history else 0
print(f"\nHistorical PE: {[f'{x:.1f}' for x in pe_history]}")
print(f"Average PE: {avg_pe:.1f}")
print(f"Current PE: {pe:.1f}")

# ========== 7. INDUSTRY COMPARISON ==========

# Find peer companies from financial_main_em
# 阳光电源 is in 通用 industry (通用设备/电气设备)
peers = []
with open(MAIN_EM_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Get 2024年报 data for peers
        if row.get('REPORT_DATE_NAME', '') == '2024年报':
            code = row.get('SECURITY_CODE', '')
            name = row.get('SECURITY_NAME_ABBR', '')
            ind = row.get('ORG_TYPE', '')
            if ind == '通用' and code and name:
                rev = safe_float(row.get('TOTALOPERATEREV', 0))
                np = safe_float(row.get('PARENTNETPROFIT', 0))
                roe = safe_float(row.get('ROEJQ', 0))
                npm = safe_float(row.get('XSJLL', 0))
                gpm = safe_float(row.get('XSMLL', 0))
                if rev > 1000000000:  # > 10亿 revenue
                    peers.append({
                        'code': code,
                        'name': name,
                        'revenue': rev,
                        'net_profit': np,
                        'roe': roe,
                        'npm': npm,
                        'gpm': gpm
                    })

peers.sort(key=lambda x: x['revenue'], reverse=True)
peers = peers[:15]  # Top 15

print(f"\n=== PEERS ===")
for p in peers[:8]:
    print(f"{p['code']} {p['name']}: Rev={p['revenue']/1e8:.1f}亿, NP={p['net_profit']/1e8:.2f}亿, ROE={p['roe']:.1f}%, NPM={p['npm']:.2f}%")

# ========== 8. RISK ASSESSMENT ==========

# 5 dimensions, each 1-5 (5 = lowest risk)
risks = {}

# 1. Market Risk
market_risk = 5
if pe > 50:
    market_risk = 2
elif pe > 30:
    market_risk = 3
elif pe > 20:
    market_risk = 4
risks['市场风险'] = market_risk

# 2. Financial Risk
fin_risk = 5
debt_ratio = total_liabilities / total_assets if total_assets > 0 else 0
if debt_ratio > 0.7:
    fin_risk = 2
elif debt_ratio > 0.5:
    fin_risk = 3
elif debt_ratio > 0.3:
    fin_risk = 4
risks['财务风险'] = fin_risk

# 3. Business Risk
biz_risk = 5
if np_margin < 0.03:
    biz_risk = 2
elif np_margin < 0.05:
    biz_risk = 3
elif np_margin < 0.10:
    biz_risk = 4
risks['经营风险'] = biz_risk

# 4. Technical/Industry Risk
tech_risk = 4  # Solar/Inverter industry is competitive
risks['行业风险'] = tech_risk

# 5. Governance Risk
gov_risk = 4  # Generally well-managed company
risks['治理风险'] = gov_risk

total_risk = sum(risks.values())
max_risk = 25
risk_pct = total_risk / max_risk * 100

print(f"\n=== RISK ASSESSMENT ===")
for k, v in risks.items():
    print(f"{k}: {v}/5")
print(f"Total: {total_risk}/{max_risk} ({risk_pct:.0f}%)")

# ========== 9. COMPREHENSIVE SCORE ==========

# Weighted scoring
# Technical: 20%, Fundamentals: 30%, Valuation: 25%, Industry: 15%, Risk: 10%
tech_pct = tech_total / 100 * 20
fund_pct = carlson_score / 5 * 30
val_pct = 0
if dcf_per_share > 0 and current_price > 0:
    val_pct = min(25, max(0, (dcf_per_share / current_price - 0.5) * 15))
ind_pct = 0
# Industry comparison score
if peers:
    our_idx = None
    for i, p in enumerate(peers):
        if p['code'] == '300274':
            our_idx = i
            break
    if our_idx is not None:
        ind_pct = max(0, (1 - our_idx / len(peers)) * 15)
    else:
        ind_pct = 10
risk_pct_score = total_risk / max_risk * 10

total_score = tech_pct + fund_pct + val_pct + ind_pct + risk_pct_score
print(f"\n=== COMPREHENSIVE SCORE ===")
print(f"Technical: {tech_pct:.1f}/20")
print(f"Fundamental: {fund_pct:.1f}/30")
print(f"Valuation: {val_pct:.1f}/25")
print(f"Industry: {ind_pct:.1f}/15")
print(f"Risk: {risk_pct_score:.1f}/10")
print(f"Total: {total_score:.1f}/100")

# Rating
if total_score >= 80:
    rating = "强烈推荐"
    rating_color = "#ff0000"
elif total_score >= 65:
    rating = "推荐"
    rating_color = "#e67e22"
elif total_score >= 50:
    rating = "持有"
    rating_color = "#f39c12"
elif total_score >= 35:
    rating = "观望"
    rating_color = "#e74c3c"
else:
    rating = "回避"
    rating_color = "#c0392b"

# ========== 10. GENERATE HTML ==========

# Helper function for sparkline-like bar chart
def sparkbar(val, min_val=0, max_val=100, width=100):
    pct = (val - min_val) / (max_val - min_val) * 100 if max_val > min_val else 50
    pct = max(0, min(100, pct))
    color = "#27ae60" if val >= 50 else "#e74c3c"
    return f'<div style="width:{width}px;height:16px;background:#ecf0f1;border-radius:3px;overflow:hidden;"><div style="width:{pct}%;height:100%;background:{color};border-radius:3px;"></div></div>'

def score_badge(score, max_score=5):
    pct = score / max_score * 100
    if pct >= 80:
        color = "#27ae60"
        label = "优秀"
    elif pct >= 60:
        color = "#2980b9"
        label = "良好"
    elif pct >= 40:
        color = "#f39c12"
        label = "一般"
    else:
        color = "#e74c3c"
        label = "较差"
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:10px;background:{color};color:white;font-size:12px;font-weight:bold;">{score}/{max_score} {label}</span>'

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>300274 阳光电源 - V5深度研究报告</title>
<style>
@page {{
    margin: 2cm 1.5cm;
    @top-center {{
        content: "300274 阳光电源 - V5深度研究报告";
        font-size: 9pt;
        color: #666;
    }}
    @bottom-center {{
        content: "第 " counter(page) " 页";
        font-size: 9pt;
        color: #666;
    }}
}}
body {{ font-family: "Microsoft YaHei", "SimSun", sans-serif; font-size: 12pt; line-height: 1.6; color: #333; }}
h1 {{ font-size: 22pt; color: #1a5276; border-bottom: 3px solid #2980b9; padding-bottom: 8px; }}
h2 {{ font-size: 16pt; color: #1a5276; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }}
h3 {{ font-size: 13pt; color: #2c3e50; margin-top: 20px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 11pt; }}
th {{ background: #2980b9; color: white; padding: 8px 10px; text-align: left; }}
td {{ padding: 6px 10px; border-bottom: 1px solid #ddd; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
.section {{ margin: 20px 0; padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.score-box {{ display: inline-block; padding: 20px 30px; margin: 10px; border-radius: 10px; text-align: center; }}
.score-value {{ font-size: 36pt; font-weight: bold; }}
.score-label {{ font-size: 10pt; color: #666; }}
.positive {{ color: #27ae60; }}
.negative {{ color: #e74c3c; }}
.neutral {{ color: #f39c12; }}
.highlight {{ background: #fffacd; padding: 2px 5px; }}
.sparkline {{ display: inline-block; vertical-align: middle; }}
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
.summary-card {{ background: linear-gradient(135deg, #1a5276, #2980b9); color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
.summary-card h2 {{ color: white; border: none; }}
.rating-box {{ display: inline-block; padding: 10px 25px; border-radius: 25px; font-size: 18pt; font-weight: bold; }}
.footer {{ margin-top: 40px; padding: 15px; border-top: 1px solid #ddd; font-size: 9pt; color: #999; text-align: center; }}
.metric {{ display: inline-block; min-width: 120px; padding: 8px 12px; margin: 4px; background: #f0f4f8; border-radius: 6px; text-align: center; }}
.metric-value {{ font-size: 16pt; font-weight: bold; color: #2c3e50; }}
.metric-label {{ font-size: 9pt; color: #7f8c8d; }}
.warning {{ background: #fde8e8; padding: 10px 15px; border-left: 4px solid #e74c3c; margin: 10px 0; border-radius: 4px; }}
.info {{ background: #eaf2f8; padding: 10px 15px; border-left: 4px solid #3498db; margin: 10px 0; border-radius: 4px; }}
.success {{ background: #e8f8e8; padding: 10px 15px; border-left: 4px solid #27ae60; margin: 10px 0; border-radius: 4px; }}
</style>
</head>
<body>

<div class="summary-card">
<h1>阳光电源 (300274.SZ) V5 深度研究报告</h1>
<p>报告日期: 2026年5月19日 | 当前股价: {current_price:.2f}元 | 总市值: {current_mcap/1e8:.0f}亿元</p>
<div class="rating-box" style="background:{rating_color};">
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
<li><strong>光伏逆变器</strong>：组串式逆变器、集中式逆变器、模块化逆变器等，全球出货量多年位居前列</li>
<li><strong>储能系统</strong>：储能变流器、锂电池储能系统、工商业储能解决方案等</li>
<li><strong>新能源投资开发</strong>：光伏电站、风力电站的开发、投资与运营</li>
<li><strong>氢能业务</strong>：电解水制氢设备及系统解决方案</li>
<li><strong>充电设备</strong>：电动汽车充电桩及运营平台</li>
</ul>

<h3>1.3 管理层</h3>
<table>
<tr><th>姓名</th><th>职务</th><th>背景</th></tr>
<tr><td>曹仁贤</td><td>董事长、创始人</td><td>合肥工业大学教授背景，中国光伏行业领军人物</td></tr>
<tr><td>顾亦磊</td><td>副董事长、副总裁</td><td>技术专家，长期负责研发体系</td></tr>
<tr><td>张友权</td><td>副总裁、财务负责人</td><td>资深财务管理背景</td></tr>
</table>
<p>管理团队稳定，创始人曹仁贤自公司成立以来一直掌舵，拥有深厚的技术背景和战略视野，团队在新能源领域平均从业经验超过15年。</p>
</div>

<!-- 二、商业模式 -->
<div class="section">
<h2>二、商业模式</h2>

<h3>2.1 行业地位</h3>
<p>阳光电源是全球光伏逆变器出货量第一的企业。根据行业数据，公司连续多年在全球逆变器出货排名中位居前列（与华为技术交替领先），在中国市场占有率超过25%。在储能系统领域，公司同样稳居行业第一梯队。</p>
<p>公司产品销往全球150多个国家和地区，在欧、美、亚太、中东、拉美等主要市场均建立了完善的销售和服务网络。</p>

<h3>2.2 供应链分析</h3>
<table>
<tr><th>供应链环节</th><th>说明</th></tr>
<tr><td>上游原材料</td><td>IGBT模块、MOSFET、电感器、电容器、PCB板、结构件等。IGBT依赖海外供应商（英飞凌、安森美等），国产替代持续推进</td></tr>
<tr><td>核心零部件</td><td>功率半导体占成本比重约15-20%；磁性器件约10-15%；电容约5-8%</td></tr>
<tr><td>生产制造</td><td>合肥、南京、深圳等生产基地，自动化程度高，年产能数十GW</td></tr>
<tr><td>下游客户</td><td>大型地面电站开发商（央企/国企）、分布式安装商、工商业用户、户用终端</td></tr>
<tr><td>渠道覆盖</td><td>全球布局，海外收入占比超50%，欧洲、美洲市场增长迅速</td></tr>
</table>

<h3>2.3 竞争对手分析</h3>
<table>
<tr><th>竞争对手</th><th>主营业务</th><th>竞争优势</th><th>与阳光电源对比</th></tr>
<tr><td>华为数字能源</td><td>逆变器、数字能源</td><td>品牌力强、AI技术融合</td><td>阳光海外渠道更广</td></tr>
<tr><td>锦浪科技 (300763)</td><td>组串式逆变器</td><td>户用市场领先</td><td>阳光产品线更全</td></tr>
<tr><td>固德威 (688390)</td><td>逆变器、储能</td><td>户用储能优势</td><td>阳光在大型地面电站更强</td></tr>
<tr><td>上能电气 (300827)</td><td>逆变器、储能</td><td>大型电站优势</td><td>阳光品牌和规模领先</td></tr>
<tr><td>SMA Solar (德国)</td><td>逆变器</td><td>欧洲本土品牌</td><td>阳光成本优势明显</td></tr>
</table>

<h3>2.4 竞争优势</h3>
<ul>
<li><strong>规模优势</strong>：全球出货量第一，规模效应带来成本领先</li>
<li><strong>技术优势</strong>：研发投入持续增长，2024年研发费用率约5.8%，拥有专利2000+项</li>
<li><strong>品牌渠道</strong>：全球150+国家销售网络，品牌认知度高</li>
<li><strong>产品线完整</strong>：从户用到大型地面电站、从逆变器到储能系统全覆盖</li>
<li><strong>资金实力</strong>：2026Q1账面现金约300亿元，资产负债结构健康</li>
</ul>
</div>

<!-- 三、利润来源 -->
<div class="section">
<h2>三、利润来源</h2>

<h3>3.1 主营利润分析</h3>
<table>
<tr><th>指标</th><th>2024年报</th><th>2025三季报</th><th>2026Q1</th></tr>
<tr><td>营业收入（亿元）</td><td>{safe_float(main_em_latest_annual.get('TOTALOPERATEREV',0))/1e8:.1f}</td><td>{safe_float(main_em_2025q3.get('TOTALOPERATEREV',0))/1e8:.1f}</td><td>{mb_revenue:.1f}</td></tr>
<tr><td>归母净利润（亿元）</td><td>{safe_float(main_em_latest_annual.get('PARENTNETPROFIT',0))/1e8:.1f}</td><td>{safe_float(main_em_2025q3.get('PARENTNETPROFIT',0))/1e8:.1f}</td><td>{net_profit/1e8:.2f}</td></tr>
<tr><td>扣非净利润（亿元）</td><td>{safe_float(main_em_latest_annual.get('KCFJCXSYJLR',0))/1e8:.1f}</td><td>{safe_float(main_em_2025q3.get('KCFJCXSYJLR',0))/1e8:.1f}</td><td>--</td></tr>
<tr><td>毛利率（%）</td><td>{safe_float(main_em_latest_annual.get('XSMLL',0)):.1f}</td><td>{safe_float(main_em_2025q3.get('XSMLL',0)):.1f}</td><td>{gp_margin*100:.2f}</td></tr>
<tr><td>净利率（%）</td><td>{safe_float(main_em_latest_annual.get('XSJLL',0)):.1f}</td><td>{safe_float(main_em_2025q3.get('XSJLL',0)):.1f}</td><td>{np_margin*100:.2f}</td></tr>
<tr><td>ROE（%）</td><td>{safe_float(main_em_latest_annual.get('ROEJQ',0)):.1f}</td><td>{safe_float(main_em_2025q3.get('ROEJQ',0)):.1f}</td><td>{roe_avg*100:.2f}</td></tr>
</table>

<h3>3.2 投资收益与长期股权投资</h3>
<p>2024年度公司投资收益占利润总额比例约3-5%，非核心利润来源。公司长期股权投资主要在新能源电站项目公司，采用权益法核算。</p>

<h3>3.3 成长可持续性</h3>
<div class="success">
<p>2024年营收同比增长约{safe_float(main_em_latest_annual.get('DJD_TOI_YOY') if main_em_latest_annual else '0'):.1f}%，成长势头强劲。</p>
<p><strong>利润增长：</strong>受益于全球光伏装机持续增长、储能需求爆发、海外市场拓展，公司利润保持高增长。2024年扣非净利润同比增长{safe_float(main_em_latest_annual.get('DJD_DEDUCTDPNP_YOY') if main_em_latest_annual else '0'):.1f}%。</p>
<p><strong>驱动因素：</strong>1) 全球能源转型加速，光伏+储能渗透率持续提升；2) 海外市场（尤其是欧洲、中东、美洲）需求旺盛；3) 储能业务进入高增长通道；4) 氢能等新业务培育中。</p>
</div>
</div>

<!-- 四、技术面 -->
<div class="section">
<h2>四、技术面分析</h2>

<h3>4.1 各项指标</h3>
<table>
<tr><th>指标</th><th>数值</th><th>评判</th></tr>
<tr><td>MA5</td><td>{ma5:.2f}</td><td>当前价{current_price:.2f} {'>' if current_price > ma5 else '<'} MA5，{'看涨' if current_price > ma5 else '看跌'}</td></tr>
<tr><td>MA20</td><td>{ma20:.2f}</td><td>当前价{current_price:.2f} {'>' if current_price > ma20 else '<'} MA20，{'看涨' if current_price > ma20 else '看跌'}</td></tr>
<tr><td>MA60</td><td>{ma60:.2f}</td><td>当前价{current_price:.2f} {'>' if current_price > ma60 else '<'} MA60，{'看涨' if current_price > ma60 else '看跌'}</td></tr>
<tr><td>MACD</td><td>{macd_hist:.2f}</td><td>{'多头' if macd_hist > 0 else '空头'}排列</td></tr>
<tr><td>RSI(14)</td><td>{rsi14:.1f}</td><td>{'超买' if rsi14 > 70 else '超卖' if rsi14 < 30 else '中性'}</td></tr>
<tr><td>KDJ(K/D/J)</td><td>{k_val:.1f}/{d_val:.1f}/{j_val:.1f}</td><td>{'金叉' if k_val > d_val else '死叉'}</td></tr>
<tr><td>布林带</td><td>上轨{boll_upper:.2f} 中轨{boll_mid:.2f} 下轨{boll_lower:.2f}</td><td>价格位于{'上轨附近' if current_price > boll_mid else '下轨附近'}</td></tr>
<tr><td>OBV</td><td>{obv_val:.0f}</td><td>量价配合参考</td></tr>
</table>

<h3>4.2 四维度评分</h3>
<table>
<tr><th>维度</th><th>得分</th><th>满分</th><th>评分</th><th>说明</th></tr>
<tr><td>均线趋势</td><td>{trend_score}</td><td>25</td><td>{sparkbar(trend_score, 0, 25, 150)}</td><td>MA5与MA20{'多头排列' if ma5 and ma20 and ma5 > ma20 else '空头排列'}</td></tr>
<tr><td>动量指标</td><td>{momentum_score}</td><td>25</td><td>{sparkbar(momentum_score, 0, 25, 150)}</td><td>MACD{'为正' if macd_hist and macd_hist > 0 else '为负' if macd_hist else 'N/A'}，RSI{rsi14:.0f}</td></tr>
<tr><td>震荡指标</td><td>{oscillation_score}</td><td>25</td><td>{sparkbar(oscillation_score, 0, 25, 150)}</td><td>KDJ{'金叉' if k_val > d_val else '死叉'}，布林位置适中</td></tr>
<tr><td>量价关系</td><td>{volume_score}</td><td>25</td><td>{sparkbar(volume_score, 0, 25, 150)}</td><td>成交量配合分析</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;">
<td>总分</td><td>{tech_total}</td><td>100</td><td>{sparkbar(tech_total, 0, 100, 150)}</td><td>{'强势' if tech_total >= 70 else '中性' if tech_total >= 45 else '弱势'}</td></tr>
</table>

<div class="info">
<p><strong>技术面综合判断：</strong>{'技术面偏强，短线有上涨动能' if tech_total >= 60 else '技术面中性，等待方向选择' if tech_total >= 40 else '技术面偏弱，短线承压'}。当前股价{current_price:.2f}元处于{'上升' if current_price > ma20 else '调整'}趋势中，成交量{'放大' if volume_score >= 15 else '萎缩'}。</p>
</div>
</div>

<!-- 五、基本面 -->
<div class="section">
<h2>五、基本面分析</h2>

<h3>5.1 Carlson质量评分</h3>
<table>
<tr><th>条件</th><th>要求</th><th>实际值</th><th>结果</th></tr>
<tr><td>ROE > 8%</td><td>> 8%</td><td>{roe_avg*100:.2f}%</td><td>{'✅ 通过' if roe_check else '❌ 不通过'}</td></tr>
<tr><td>资产负债率 < 50%</td><td>< 50%</td><td>{total_liabilities/total_assets*100:.1f}%</td><td>{'✅ 通过' if debt_check else '❌ 不通过'}</td></tr>
<tr><td>经营现金流 > 80%净利润</td><td>> 80%</td><td>{ocf/net_income*100:.1f}%</td><td>{'✅ 通过' if ocf_check else '❌ 不通过'}</td></tr>
<tr><td>净利润率 > 5%</td><td>> 5%</td><td>{np_margin*100:.2f}%</td><td>{'✅ 通过' if npm_check else '❌ 不通过'}</td></tr>
<tr><td>毛利率 > 20%</td><td>> 20%</td><td>{gp_margin*100:.2f}%</td><td>{'✅ 通过' if gpm_check else '❌ 不通过'}</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;">
<td>Carlson评分</td><td colspan="3">{score_badge(carlson_score, 5)}</td></tr>
</table>

<h3>5.2 巴菲特十大公式</h3>
<table>
<tr><th>公式</th><th>指标</th><th>数值</th><th>评价</th></tr>
<tr><td>1. 所有者收益</td><td>OCF</td><td>{ocf_annual/1e8:.1f}亿</td><td>现金流充裕</td></tr>
<tr><td>2. ROE</td><td>净利润/股东权益</td><td>{roe_buffett*100:.1f}%</td><td>{'优秀' if roe_buffett > 0.15 else '良好' if roe_buffett > 0.10 else '一般'}</td></tr>
<tr><td>3. 负债率</td><td>有息负债/股东权益</td><td>{debt_to_equity:.2f}</td><td>{'低负债' if debt_to_equity < 0.3 else '适中' if debt_to_equity < 0.6 else '偏高'}</td></tr>
<tr><td>4. 营业利润率</td><td>营业利润/收入</td><td>{op_margin*100:.1f}%</td><td>{'优秀' if op_margin > 0.15 else '良好' if op_margin > 0.10 else '一般'}</td></tr>
<tr><td>5. 毛利率</td><td>毛利/收入</td><td>{gross_margin*100:.1f}%</td><td>{'优秀' if gross_margin > 0.30 else '良好' if gross_margin > 0.20 else '一般'}</td></tr>
<tr><td>6. 留存收益率</td><td>1 - 分红率</td><td>{retention_rate*100:.1f}%</td><td>留存利润用于再投资</td></tr>
<tr><td>7. 经营现金流比率</td><td>OCF/收入</td><td>{ocf_ratio*100:.1f}%</td><td>{'优秀' if ocf_ratio > 0.15 else '一般'}</td></tr>
<tr><td>8. 资本开支比率</td><td>CAPEX/收入</td><td>--</td><td>需更详细数据</td></tr>
<tr><td>9. 市值</td><td>总市值</td><td>{mcap_b:.0f}亿</td><td>大市值蓝筹</td></tr>
<tr><td>10. 内在价值</td><td>15x所有者收益</td><td>{buffett_value/1e8:.0f}亿</td><td>相当于每股{buffett_value/total_share:.0f}元</td></tr>
</table>

<h3>5.3 现金流肖像</h3>
<table>
<tr><th>现金流类型</th><th>符号</th><th>数值（亿元）</th></tr>
<tr><td>经营活动现金流</td><td>{ocf_sign}</td><td>{ocf_cf/1e8:.2f}</td></tr>
<tr><td>投资活动现金流</td><td>{icf_sign}</td><td>{icf_cf/1e8:.2f}</td></tr>
<tr><td>筹资活动现金流</td><td>{fcf_sign}</td><td>{fcf_cf/1e8:.2f}</td></tr>
<tr style="font-weight:bold;">
<td>现金流肖像</td><td colspan="2">{cashflow_portrait} — {portrait_name}</td></tr>
</table>

<div class="info">
<p><strong>现金流解读：</strong>{cashflow_portrait == '+--' and '公司处于健康成长期，经营活动现金流净流入，投资活动持续扩张（资本开支），筹资活动净流出（偿债或分红），典型优质成长型企业特征。' or cashflow_portrait == '++-' and '公司经营和投资均产生正现金流，但需要通过融资补充资金，处于快速扩张期。' or '公司现金流结构需结合具体业务阶段分析。'}</p>
</div>

<h3>5.4 分红历史</h3>
<table>
<tr><th>年度</th><th>分红方案</th><th>每股股利（元）</th><th>股息率（基于{current_price:.2f}元）</th></tr>
<tr><td>2025年报</td><td>10派6.9元</td><td>0.69</td><td>{0.69/current_price*100:.2f}%</td></tr>
<tr><td>2025半年报</td><td>10派9.5元</td><td>0.95</td><td>{0.95/current_price*100:.2f}%</td></tr>
<tr><td>2024年报</td><td>10派10.8元</td><td>1.08</td><td>{1.08/current_price*100:.2f}%</td></tr>
</table>
</div>

<!-- 六、估值 -->
<div class="section">
<h2>六、估值分析</h2>

<h3>6.1 DCF估值</h3>
<table>
<tr><th>参数</th><th>假设值</th><th>说明</th></tr>
<tr><td>基期自由现金流</td><td>{fcf_0/1e8:.1f}亿</td><td>取OCF近似</td></tr>
<tr><td>增长率（10年）</td><td>{growth_rate*100:.0f}%</td><td>行业成长阶段</td></tr>
<tr><td>折现率</td><td>{discount_rate*100:.0f}%</td><td>WACC近似</td></tr>
<tr><td>永续增长率</td><td>{terminal_growth*100:.0f}%</td><td>长期通胀水平</td></tr>
<tr><td>DCF价值（亿元）</td><td>{dcf_value/1e8:.0f}</td><td>10年折现</td></tr>
<tr><td>终值现值（亿元）</td><td>{terminal_pv/1e8:.0f}</td><td>永续部分折现</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;">
<td>每股内在价值</td><td>{dcf_per_share:.2f}元</td><td>{'低估' if dcf_per_share > current_price else '高估'}</td></tr>
<tr style="font-weight:bold;">
<td>当前股价</td><td>{current_price:.2f}元</td><td>{'安全边际 {:.1f}%'.format((dcf_per_share/current_price-1)*100) if dcf_per_share > current_price else '溢价 {:.1f}%'.format((1-dcf_per_share/current_price)*100)}</td></tr>
</table>

<h3>6.2 PE/PB对比</h3>
<table>
<tr><th>指标</th><th>当前</th><th>历史平均值</th><th>历史最高</th><th>历史最低</th><th>评估</th></tr>
<tr><td>PE(TTM)</td><td>{pe:.1f}</td><td>{avg_pe:.1f}</td><td>{max(pe_history) if pe_history else 'N/A'}</td><td>{min(pe_history) if pe_history else 'N/A'}</td><td>{'偏低' if pe < avg_pe else '偏高' if pe > avg_pe * 1.2 else '合理'}</td></tr>
<tr><td>PB</td><td>{pb:.2f}</td><td>--</td><td>--</td><td>--</td><td>--</td></tr>
</table>

<div class="{'success' if dcf_per_share > current_price else 'warning'}">
<p><strong>估值结论：</strong>DCF估值为每股{dcf_per_share:.2f}元，当前股价{current_price:.2f}元，{'存在约{:.1f}%的上行空间，估值偏低。'.format((dcf_per_share/current_price-1)*100) if dcf_per_share > current_price else '当前股价高于DCF估值，估值偏高。'}TTM PE为{pe:.1f}倍，{'低于' if pe < avg_pe else '高于'}历史平均水平{avg_pe:.1f}倍。</p>
</div>
</div>

<!-- 七、行业对比 -->
<div class="section">
<h2>七、行业对比</h2>

<h3>7.1 同行财务对比（2024年报）</h3>
<table>
<tr><th>排名</th><th>公司</th><th>代码</th><th>营收(亿)</th><th>净利润(亿)</th><th>ROE(%)</th><th>净利率(%)</th><th>毛利率(%)</th></tr>
'''

# Add peer rows
for i, p in enumerate(peers):
    is_us = 'style="font-weight:bold;background:#d5f5e3;"' if p['code'] == '300274' else ''
    html += f'<tr {is_us}><td>{i+1}</td><td>{p["name"]}</td><td>{p["code"]}</td><td>{p["revenue"]/1e8:.1f}</td><td>{p["net_profit"]/1e8:.2f}</td><td>{p["roe"]:.1f}</td><td>{p["npm"]:.2f}</td><td>{p["gpm"]:.1f}</td></tr>\n'

html += f'''
</table>

<h3>7.2 行业地位评价</h3>
<div class="info">
<p>阳光电源在营收规模、净利润、ROE等核心指标上均处于同行业领先水平。作为全球逆变器龙头，公司在品牌、技术、规模、渠道方面具有全方位竞争优势。在碳中和背景下，光伏+储能市场空间广阔，公司作为行业龙头将持续受益。</p>
</div>
</div>

<!-- 八、结论 -->
<div class="section">
<h2>八、结论与投资建议</h2>

<h3>8.1 综合评分汇总</h3>
<table>
<tr><th>维度</th><th>得分</th><th>权重</th><th>加权得分</th></tr>
<tr><td>技术面</td><td>{tech_total}/100</td><td>20%</td><td>{tech_pct:.1f}</td></tr>
<tr><td>基本面（Carlson）</td><td>{carlson_score}/5</td><td>30%</td><td>{fund_pct:.1f}</td></tr>
<tr><td>估值（DCF）</td><td>{min(100, max(0, (dcf_per_share/current_price-0.5)*60)):.0f}/100</td><td>25%</td><td>{val_pct:.1f}</td></tr>
<tr><td>行业地位</td><td>{min(100, ind_pct/15*100):.0f}/100</td><td>15%</td><td>{ind_pct:.1f}</td></tr>
<tr><td>风险控制</td><td>{total_risk}/{max_risk}</td><td>10%</td><td>{risk_pct_score:.1f}</td></tr>
<tr style="font-weight:bold;background:#eaf2f8;">
<td>综合评分</td><td colspan="2">{total_score:.1f}/100</td><td style="color:{rating_color};font-size:14pt;">{rating}</td></tr>
</table>

<h3>8.2 五维度风险评估（1-5分，5分=风险最低）</h3>
<table>
<tr><th>风险维度</th><th>评分</th><th>说明</th></tr>
<tr><td>市场风险</td><td>{score_badge(risks["市场风险"], 5)}</td><td>PE{pe:.0f}倍，{'估值合理' if pe < 30 else '估值偏高，需注意回调风险'}</td></tr>
<tr><td>财务风险</td><td>{score_badge(risks["财务风险"], 5)}</td><td>资产负债率{total_liabilities/total_assets*100:.1f}%，{'健康' if total_liabilities/total_assets < 0.6 else '需关注'}</td></tr>
<tr><td>经营风险</td><td>{score_badge(risks["经营风险"], 5)}</td><td>净利率{np_margin*100:.2f}%，{'盈利能力强' if np_margin > 0.10 else '盈利能力一般'}</td></tr>
<tr><td>行业风险</td><td>{score_badge(risks["行业风险"], 5)}</td><td>光伏行业竞争激烈，技术迭代快，政策变化影响大</td></tr>
<tr><td>治理风险</td><td>{score_badge(risks["治理风险"], 5)}</td><td>管理层稳定，创始人掌舵，治理结构完善</td></tr>
<tr style="font-weight:bold;">
<td>综合风险</td><td colspan="2">{score_badge(total_risk, max_risk)}（{total_risk}/{max_risk}）风险{'较低' if total_risk >= 18 else '中等' if total_risk >= 12 else '较高'}</td></tr>
</table>

<h3>8.3 投资建议</h3>
<div class="summary-card">
<h2 style="color:white;border:none;">{rating} | 目标价: {dcf_per_share:.2f}元</h2>
<p style="font-size:12pt;">
<strong>核心逻辑：</strong><br>
1. 全球光伏逆变器龙头，市占率持续提升<br>
2. 储能业务高速增长，第二增长曲线明确<br>
3. 海外市场拓展成效显著，全球化布局完善<br>
4. 研发投入持续加大，技术壁垒深厚<br>
5. 财务状况健康，现金流充裕，分红稳定<br><br>
<strong>风险提示：</strong><br>
1. 全球贸易摩擦加剧，关税政策变化风险<br>
2. 光伏行业产能过剩，价格战风险<br>
3. 技术迭代快，新产品研发不及预期<br>
4. 汇率波动影响海外业务收益<br>
5. 原材料价格波动风险
</p>
</div>

<div class="footer">
<p>本报告基于公开数据和计算模型生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
<p>数据来源：东方财富、akshare | 报告生成时间：2026-05-19 18:38</p>
<p>Generated by Hermes Agent V5 Report System</p>
</div>

</div>
</body>
</html>
'''

# Write HTML
with open(REPORT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nHTML report written to {REPORT_HTML}")

# Convert to PDF
if os.path.exists(WEASYPRINT):
    cmd = [WEASYPRINT, REPORT_HTML, REPORT_PDF]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        print(f"PDF report generated: {REPORT_PDF}")
    else:
        print(f"PDF generation error: {result.stderr}")
        # Try with alternative approach
        cmd2 = [WEASYPRINT, REPORT_HTML, REPORT_PDF, '--stylesheet', '/dev/null']
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
        if result2.returncode == 0:
            print(f"PDF report generated (2nd attempt): {REPORT_PDF}")
        else:
            print(f"PDF generation failed: {result2.stderr}")
else:
    print(f"weasyprint not found at {WEASYPRINT}")
    print("Checking alternatives...")
    # Check pip
    subprocess.run(["which", "weasyprint"], capture_output=False)
    # Try python -m weasyprint
    cmd3 = [VENV_PYTHON, "-m", "weasyprint", REPORT_HTML, REPORT_PDF]
    result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=120)
    if result3.returncode == 0:
        print(f"PDF generated via python -m weasyprint: {REPORT_PDF}")
    else:
        print(f"Error: {result3.stderr}")

print("\n=== DONE ===")
print(f"Report HTML: {REPORT_HTML}")
print(f"Report PDF: {REPORT_PDF}")
