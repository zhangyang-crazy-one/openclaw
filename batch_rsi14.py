#!/usr/bin/env python3
"""批量给所有技术指标CSV添加RSI14列，增量更新（跳过已有rsi14的）"""
import csv, os, sys
from pathlib import Path

TECH_DIR = Path("/home/liujerry/金融数据/technical_indicators")
STOCKS_DIR = Path("/home/liujerry/金融数据/stocks")

def compute_rsi14(closes):
    """Wilder's smoothing RSI(14)"""
    if len(closes) < 15:
        return [None] * len(closes)
    
    rsi = [None] * 14  # 前14天无值
    
    # 计算第14天的初始avg_gain/avg_loss
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
        rs = avg_gain / avg_loss
        rsi.append(100.0 - 100.0 / (1 + rs))
    
    for i in range(15, len(closes)):
        diff = closes[i] - closes[i-1]
        gain = max(diff, 0)
        loss = max(-diff, 0)
        avg_gain = (avg_gain * 13 + gain) / 14
        avg_loss = (avg_loss * 13 + loss) / 14
        if avg_loss == 0:
            rsi.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100.0 - 100.0 / (1 + rs))
    
    return rsi

def process_file(code):
    tech_path = TECH_DIR / f"{code}.csv"
    stock_path = STOCKS_DIR / f"{code}.csv"
    
    if not tech_path.exists() or not stock_path.exists():
        return False, "no_file"
    
    # 读取技术指标
    with open(tech_path, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # 已有rsi14
    if 'rsi14' in fieldnames:
        return False, "has_rsi14"
    
    # 读取K线收盘价
    closes = []
    with open(stock_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                closes.append(float(row['close']))
            except (KeyError, ValueError):
                closes.append(None)
    
    # 计算RSI14
    rsi14_vals = compute_rsi14(closes)
    
    # 对齐：技术指标CSV的行数可能与K线不同
    # 按日期匹配
    date_to_rsi = {}
    with open(stock_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if rsi14_vals[i] is not None:
                date_to_rsi[row['date']] = round(rsi14_vals[i], 6)
    
    # 更新技术指标CSV的rsi14列
    new_fieldnames = list(fieldnames) + ['rsi14']
    for row in rows:
        date = row.get('date', '')
        if date in date_to_rsi:
            row['rsi14'] = str(date_to_rsi[date])
        else:
            row['rsi14'] = ''
    
    with open(tech_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return True, "ok"

def main():
    # 获取所有code
    codes = sorted([f.stem for f in TECH_DIR.glob("*.csv") if f.stem != 'errors'])
    total = len(codes)
    processed = 0
    skipped_has = 0
    skipped_nofile = 0
    errors = 0
    
    print(f"Total: {total} files")
    
    for i, code in enumerate(codes):
        try:
            ok, reason = process_file(code)
            if ok:
                processed += 1
            elif reason == "has_rsi14":
                skipped_has += 1
            else:
                skipped_nofile += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error {code}: {e}", file=sys.stderr)
        
        if (i+1) % 500 == 0:
            print(f"  Progress: {i+1}/{total} (ok={processed}, skip_has={skipped_has}, skip_nofile={skipped_nofile}, err={errors})")
    
    print(f"\nDone: total={total}, ok={processed}, skip_has_rsi14={skipped_has}, skip_nofile={skipped_nofile}, errors={errors}")

if __name__ == "__main__":
    main()
