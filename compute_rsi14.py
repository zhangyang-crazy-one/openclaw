#!/usr/bin/env python3
"""
Compute RSI(14) for stock 300274 using Wilder's smoothing method.
Reads close prices from stocks CSV, computes RSI14, adds it to the technical indicators CSV.
Uses only csv module, no pandas.
"""

import csv
import os

STOCKS_DIR = "/home/liujerry/金融数据/stocks"
TI_DIR = "/home/liujerry/金融数据/technical_indicators"
SYMBOL = "300274"
PERIOD = 14


def load_close_prices(filepath):
    """Load close prices from K-line CSV, returns list of (date, close_price)."""
    rows = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['date']
            close = float(row['close'])
            rows.append((date, close))
    return rows


def compute_rsi_wilder(closes, period=14):
    """
    Compute RSI using Wilder's smoothing method.
    Returns a list of same length as closes, with None for first `period` entries.
    
    Wilder's smoothing:
    - First avg_gain and avg_loss are simple averages of first `period` days.
    - Subsequent values use: 
        avg_gain = (prev_avg_gain * (period-1) + current_gain) / period
        avg_loss = (prev_avg_loss * (period-1) + current_loss) / period
    """
    n = len(closes)
    rsi = [None] * n
    
    if n <= period:
        return rsi
    
    # Compute daily price changes
    gains = []
    losses = []
    for i in range(1, n):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
    
    # First avg_gain/avg_loss: simple average of first `period` changes
    initial_avg_gain = sum(gains[:period]) / period
    initial_avg_loss = sum(losses[:period]) / period
    
    # Compute RSI for first period (index = period, which maps to closes index period)
    if initial_avg_loss == 0:
        rsi_val = 100.0
    else:
        rs = initial_avg_gain / initial_avg_loss
        rsi_val = 100.0 - (100.0 / (1.0 + rs))
    rsi[period] = rsi_val
    
    # Wilder smoothing for subsequent values
    avg_gain = initial_avg_gain
    avg_loss = initial_avg_loss
    
    for i in range(period + 1, n):
        idx = i - 1  # index into gains/losses (0-based, offset by 1 from closes)
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
        
        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi


def main():
    stocks_file = os.path.join(STOCKS_DIR, f"{SYMBOL}.csv")
    ti_file = os.path.join(TI_DIR, f"{SYMBOL}.csv")
    
    # Load close prices
    price_data = load_close_prices(stocks_file)
    dates_price = [d for d, _ in price_data]
    closes = [c for _, c in price_data]
    print(f"Loaded {len(closes)} price rows from {stocks_file}")
    print(f"  Date range: {dates_price[0]} to {dates_price[-1]}")
    
    # Compute RSI14
    rsi14_values = compute_rsi_wilder(closes, PERIOD)
    print(f"  RSI14 computed: {len([x for x in rsi14_values if x is not None])} non-None values")
    print(f"  First RSI14 value at index {PERIOD}: {rsi14_values[PERIOD]:.2f} (date: {dates_price[PERIOD]})")
    print(f"  Last RSI14 value: {rsi14_values[-1]:.2f} (date: {dates_price[-1]})")
    
    # Read existing TI CSV
    with open(ti_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        ti_rows = list(reader)
    
    header = ti_rows[0]
    data_rows = ti_rows[1:]
    print(f"\nExisting TI CSV: {len(data_rows)} data rows, {len(header)} columns")
    print(f"  Columns: {header}")
    
    # Check if rsi14 already exists
    if 'rsi14' in header:
        print("  rsi14 column already exists. Updating values...")
        rsi_idx = header.index('rsi14')
    else:
        print("  rsi14 column MISSING. Adding new column.")
        header.append('rsi14')
        rsi_idx = len(header) - 1
        # Extend all existing rows with empty string
        for row in data_rows:
            row.append('')
    
    # Map dates to RSI14 values
    rsi_by_date = {}
    for i, (date, _) in enumerate(price_data):
        if rsi14_values[i] is not None:
            rsi_by_date[date] = round(rsi14_values[i], 6)
    
    # Update RSI14 for existing rows
    updated = 0
    for row in data_rows:
        date = row[0]
        if date in rsi_by_date:
            row[rsi_idx] = str(rsi_by_date[date])
            updated += 1
    print(f"  Updated {updated} existing rows with RSI14 values")
    
    # Check if there are new price rows not in TI CSV (e.g., 2026-05-07)
    existing_dates = set(row[0] for row in data_rows)
    new_dates = []
    for date, close in price_data:
        if date not in existing_dates:
            new_dates.append(date)
    
    if new_dates:
        print(f"\n  New dates found in stocks CSV but missing from TI CSV: {new_dates}")
        # We need to compute full indicators for these new rows.
        # For now, at minimum add the date, close, and rsi14.
        # Other columns will stay empty.
        for date in new_dates:
            new_row = ['' for _ in header]
            new_row[0] = date  # date
            new_row[1] = str(rsi_by_date.get(date, '')) if header[1] == 'close' else ''
            new_row[rsi_idx] = str(rsi_by_date.get(date, ''))
            data_rows.append(new_row)
        print(f"  Appended {len(new_dates)} new rows for missing dates")
    
    # Write back
    with open(ti_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_rows)
    
    print(f"\nDone. File written: {ti_file}")
    print(f"  Final: {len(data_rows)} data rows, {len(header)} columns")
    print(f"  Columns: {header}")


if __name__ == "__main__":
    main()
