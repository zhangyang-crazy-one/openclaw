#!/usr/bin/env python3
"""Debug field names in main_em for 300274"""
import csv, os
HOME = os.path.expanduser("~")
MAIN_EM_FILE = f"{HOME}/金融数据/fundamentals/chuangye_full/financial_main_em.csv"

with open(MAIN_EM_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('SECUCODE', '') == '300274.SZ':
            # Print all keys for this row
            keys = list(row.keys())
            print(f"Total keys: {len(keys)}")
            # Print first 50 keys
            for i, k in enumerate(keys[:60]):
                val = row.get(k, '')
                print(f"  [{i}] {k} = {val[:80] if isinstance(val, str) else val}")
            
            # Also print some specific values
            print(f"\n--- Specific fields ---")
            print(f"TOTALOPERATEREV: {row.get('TOTALOPERATEREV', 'NOT FOUND')}")
            print(f"TOTALOPERATEREVE: {row.get('TOTALOPERATEREVE', 'NOT FOUND')}")
            print(f"PARENTNETPROFIT: {row.get('PARENTNETPROFIT', 'NOT FOUND')}")
            print(f"MGJYXJJE: {row.get('MGJYXJJE', 'NOT FOUND')}")
            print(f"ORG_TYPE: {row.get('ORG_TYPE', 'NOT FOUND')}")
            print(f"XSMLL: {row.get('XSMLL', 'NOT FOUND')}")
            print(f"XSJLL: {row.get('XSJLL', 'NOT FOUND')}")
            print(f"ROEJQ: {row.get('ROEJQ', 'NOT FOUND')}")
            print(f"EPSJB: {row.get('EPSJB', 'NOT FOUND')}")
            print(f"BPS: {row.get('BPS', 'NOT FOUND')}")
            break
