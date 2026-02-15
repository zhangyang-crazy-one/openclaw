#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整财报数据获取系统
"""

import akshare as ak
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BLUE_CHIP = [
    ("600000", "浦发银行"), ("600016", "民生银行"), ("600036", "招商银行"),
    ("600028", "中国石化"), ("600030", "中信证券"), ("600050", "中国联通"),
]

print("="*60)
print("获取财报数据...")

# 1. 全市场PE/PB
print("\n1. stock_a_all_pb")
try:
    df = ak.stock_a_all_pb()
    df.to_csv(DATA_DIR / "stock_a_all_pb.csv", index=False)
    print(f"   OK: {len(df)} 条")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n2. stock_a_all_pe")
try:
    df = ak.stock_a_all_pe()
    df.to_csv(DATA_DIR / "stock_a_all_pe.csv", index=False)
    print(f"   OK: {len(df)} 条")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n3. stock_zh_a_spot")
try:
    df = ak.stock_zh_a_spot()
    df.to_csv(DATA_DIR / "stock_spot.csv", index=False)
    print(f"   OK: {len(df)} 条")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n4. stock_financial_analysis_indicator")
try:
    df = ak.stock_financial_analysis_indicator(symbol="600036")
    df.to_csv(DATA_DIR / "financial_indicator.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n5. stock_financial_analysis_indicator_em")
try:
    df = ak.stock_financial_analysis_indicator_em(symbol="600036")
    df.to_csv(DATA_DIR / "financial_indicator_em.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n6. stock_a_indicator_lg")
try:
    df = ak.stock_a_indicator_lg(symbol="600036")
    df.to_csv(DATA_DIR / "stock_indicator_lg.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n7. stock_profit_sheet_by_yearly_em")
try:
    df = ak.stock_profit_sheet_by_yearly_em(symbol="600036")
    df.to_csv(DATA_DIR / "profit_sheet_yearly.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n8. stock_balance_sheet_by_yearly_em")
try:
    df = ak.stock_balance_sheet_by_yearly_em(symbol="600036")
    df.to_csv(DATA_DIR / "balance_sheet_yearly.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n9. stock_cash_flow_sheet_by_yearly_em")
try:
    df = ak.stock_cash_flow_sheet_by_yearly_em(symbol="600036")
    df.to_csv(DATA_DIR / "cash_flow_sheet_yearly.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n10. stock_financial_report_sina")
try:
    df = ak.stock_financial_report_sina(stock="sh600036")
    df.to_csv(DATA_DIR / "financial_report_sina.csv", index=False)
    print(f"   OK: {len(df)} 条, 列: {list(df.columns)[:5]}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n" + "="*60)
print("完成! 数据保存在:", DATA_DIR)
