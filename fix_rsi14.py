#!/usr/bin/env python3
"""修复 batch_rsi14.py 失败的194个文件 — 处理 BOM 问题"""
import csv
from pathlib import Path

TECH_DIR = Path("/home/liujerry/金融数据/technical_indicators")
STOCKS_DIR = Path("/home/liujerry/金融数据/stocks")

def compute_rsi14(closes):
    if len(closes) < 15:
        return [None] * len(closes)
    rsi = [None] * 14
    gains, losses = [], []
    for i in range(1, 15):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    if avg_loss == 0:
        rsi.append(100.0)
    else:
        rsi.append(100.0 - 100.0 / (1 + avg_gain / avg_loss))
    for i in range(15, len(closes)):
        diff = closes[i] - closes[i-1]
        gain = max(diff, 0)
        loss = max(-diff, 0)
        avg_gain = (avg_gain * 13 + gain) / 14
        avg_loss = (avg_loss * 13 + loss) / 14
        if avg_loss == 0:
            rsi.append(100.0)
        else:
            rsi.append(100.0 - 100.0 / (1 + avg_gain / avg_loss))
    return rsi

def process_file(code):
    tech_path = TECH_DIR / f"{code}.csv"
    stock_path = STOCKS_DIR / f"{code}.csv"
    
    if not tech_path.exists() or not stock_path.exists():
        return False, "no_file"
    
    # 读取技术指标 (encoding='utf-8-sig' 处理BOM)
    with open(tech_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    if not fieldnames:
        return False, "empty"
    
    # 标准化列名
    date_col = None
    for col in fieldnames:
        if col.lower().strip('\ufeff') == 'date':
            date_col = col
            break
    
    if not date_col:
        return False, f"no_date_col: {fieldnames[:5]}"
    
    # 已有rsi14
    rsi14_cols = [c for c in fieldnames if c.lower().strip('\ufeff') == 'rsi14']
    if rsi14_cols:
        return False, "has_rsi14"
    
    # 读取K线收盘价 (also handle BOM)
    closes = []
    dates = []
    with open(stock_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                closes.append(float(row['close']))
                dates.append(row['date'])
            except (KeyError, ValueError):
                closes.append(None)
                dates.append('')
    
    # 计算RSI14
    rsi14_vals = compute_rsi14(closes)
    
    # 日期到RSI映射
    date_to_rsi = {}
    for i, d in enumerate(dates):
        if rsi14_vals[i] is not None:
            date_to_rsi[d] = round(rsi14_vals[i], 6)
    
    # 写入
    new_fieldnames = list(fieldnames) + ['rsi14']
    for row in rows:
        d = row.get(date_col, '').strip()
        if d in date_to_rsi:
            row['rsi14'] = str(date_to_rsi[d])
        else:
            row['rsi14'] = ''
    
    with open(tech_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return True, "ok"

def main():
    # 找尚未有 rsi14 的文件
    codes = sorted([f.stem for f in TECH_DIR.glob("*.csv") if f.stem != 'errors'])
    missing = []
    for code in codes:
        tech_path = TECH_DIR / f"{code}.csv"
        with open(tech_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fn = reader.fieldnames or []
        has_rsi14 = any(c.lower().strip('\ufeff') == 'rsi14' for c in fn)
        if not has_rsi14:
            missing.append(code)
    
    print(f"Total missing rsi14: {len(missing)}")
    
    ok = 0
    errors = 0
    for i, code in enumerate(missing):
        try:
            success, reason = process_file(code)
            if success:
                ok += 1
            else:
                errors += 1
                if errors <= 10:
                    print(f"  Skip {code}: {reason}")
        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"  Error {code}: {e}")
        
        if (i+1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(missing)} (ok={ok}, err={errors})")
    
    print(f"\nDone: ok={ok}, errors={errors}")

if __name__ == "__main__":
    main()
