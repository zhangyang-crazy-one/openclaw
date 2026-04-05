#!/usr/bin/env python3
"""
批量补全 EastMoney 主要财务指标 V2
修复格式比对问题
"""
import requests
import pandas as pd
import time
from pathlib import Path
from datetime import datetime

API_BASE = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
API_REPORT = "RPT_F10_FINANCE_MAINFINADATA"

def normalize_code(code):
    """统一格式: sz.300023 -> 300023, sh.600000 -> 600000"""
    code = str(code).upper()
    if '.' in code:
        # 去掉前缀和点: sz.300023 -> 300023
        parts = code.split('.')
        if len(parts) == 2:
            return parts[1]  # 只取数字部分
    return code

def get_all_stocks():
    """从profit.csv获取全部股票列表"""
    profit_file = Path('/home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv')
    df = pd.read_csv(profit_file, low_memory=False)
    # 统一格式
    codes = set()
    for code in df['code'].dropna().unique():
        codes.add(normalize_code(code))
    return codes

def get_existing_stocks():
    """获取financial_main_em.csv中已有的股票"""
    fin_file = Path('/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv')
    if not fin_file.exists():
        return set()
    df = pd.read_csv(fin_file, low_memory=False)
    if 'SECUCODE' not in df.columns:
        return set()
    # 格式: 300001.SZ -> 300001
    codes = set()
    for secucode in df['SECUCODE'].dropna().unique():
        # 去掉.SH/.SZ后缀
        code = secucode.replace('.SH', '').replace('.SZ', '')
        codes.add(code)
    return codes

def fetch_em_financial(code):
    """获取EastMoney财务数据"""
    # 判断交易所
    if code.startswith('688') or code.startswith('600') or code.startswith('601') or code.startswith('603'):
        secucode = f'{code}.SH'
    else:
        secucode = f'{code}.SZ'
    
    params = {
        'reportName': API_REPORT,
        'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,REPORT_DATE,REPORT_DATE_NAME,EPSJB,EPSKCJB,BPS,MGZBGJ,MGWFPLR,MGJYXJJE,TOTALOPERATEREVE,MLR,PARENTNETPROFIT,KCFJCXSYJLR,ROEJQ,ROEKCJQ,ZZCJLL,XSJLL,XSMLL,LD,SD,ZCFZL,UPDATE_DATE',
        'filter': f'(SECUCODE="{secucode}")',
        'pageNumber': '1',
        'pageSize': '100',
        'sortTypes': '-1',
        'sortColumns': 'REPORT_DATE',
        'source': 'HSF10',
        'client': 'HSF10'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://emweb.securities.eastmoney.com/'
    }
    
    try:
        resp = requests.get(API_BASE, params=params, headers=headers, timeout=15)
        data = resp.json()
        
        if data.get('result') and data['result'].get('data'):
            return pd.DataFrame(data['result']['data'])
        return None
    except:
        return None

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始批量采集 V2...")
    
    all_stocks = get_all_stocks()
    existing_stocks = get_existing_stocks()
    
    # 计算真正的缺口
    missing_stocks = [s for s in all_stocks if s not in existing_stocks]
    
    print(f"全部股票: {len(all_stocks)}")
    print(f"已存在: {len(existing_stocks)}")
    print(f"缺口: {len(missing_stocks)}")
    
    if not missing_stocks:
        print("没有缺失股票，数据已完整!")
        return
    
    # 加载现有数据
    fin_file = Path('/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv')
    if fin_file.exists():
        df_existing = pd.read_csv(fin_file, low_memory=False)
    else:
        df_existing = pd.DataFrame()
    
    # 排序确保一致性
    missing_stocks = sorted(missing_stocks)
    
    # 分批采集
    batch_size = 50
    total = len(missing_stocks)
    success_count = 0
    fail_count = 0
    new_rows = []
    
    start_time = time.time()
    
    for i, code in enumerate(missing_stocks):
        if i % batch_size == 0:
            elapsed = time.time() - start_time
            rate = (i / elapsed) if elapsed > 0 else 0
            remaining = (total - i) / rate if rate > 0 else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 进度: {i}/{total} ({i/total*100:.1f}%) - 成功:{success_count} 失败:{fail_count} - 预计剩余: {remaining/60:.1f}分钟")
        
        df = fetch_em_financial(code)
        if df is not None and len(df) > 0:
            new_rows.append(df)
            success_count += 1
        else:
            fail_count += 1
        
        # 每50个保存一次
        if (i + 1) % batch_size == 0:
            if new_rows:
                df_new = pd.concat(new_rows, ignore_index=True)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined = df_combined.drop_duplicates(subset=['SECUCODE', 'REPORT_DATE'], keep='last')
                df_combined.to_csv(fin_file, index=False)
                df_existing = df_combined
                new_rows = []
        
        time.sleep(0.3)
    
    # 保存剩余
    if new_rows:
        df_new = pd.concat(new_rows, ignore_index=True)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['SECUCODE', 'REPORT_DATE'], keep='last')
        df_combined.to_csv(fin_file, index=False)
    
    # 最终统计
    df_final = pd.read_csv(fin_file, low_memory=False)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 完成!")
    print(f"总股票: {df_final['SECUCODE'].nunique()}")
    print(f"总行数: {len(df_final)}")
    print(f"本次成功: {success_count}")
    print(f"本次失败: {fail_count}")

if __name__ == '__main__':
    main()
