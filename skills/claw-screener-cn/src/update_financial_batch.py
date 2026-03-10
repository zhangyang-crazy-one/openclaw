#!/usr/bin/env python3
"""
A股财务数据批量更新器
使用 Sina API 获取财务数据
"""
import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import random

FINANCIAL_FILE = Path("/home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv")


def get_all_a_codes() -> list:
    """从现有股票文件获取代码列表"""
    stocks_dir = Path("/home/liujerry/金融数据/stocks")
    codes = []
    
    for f in stocks_dir.glob("*.csv"):
        code = f.stem
        if code.isdigit():
            codes.append(code)
    
    return sorted(codes)


def fetch_financial_sina(symbol: str) -> dict:
    """使用Sina API获取财务数据"""
    try:
        import requests
        
        # 尝试获取简要财务数据
        url = f"https://finance.sina.com.cn/realstock/company/{symbol}/nc.shtml"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return {}
        
        # 简化处理，返回空让akshare重试
        return {}
        
    except:
        return {}


def fetch_financial_akshare(symbol: str) -> dict:
    """使用akshare获取财务数据"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator='按报告期')
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            
            def parse_val(v):
                if pd.isna(v):
                    return 0
                if isinstance(v, (int, float)):
                    return float(v)
                v = str(v)
                if '亿' in v:
                    return float(v.replace('亿', '')) * 1e8
                if '万' in v:
                    return float(v.replace('万', '')) * 1e4
                try:
                    return float(v.replace('%', ''))
                except:
                    return 0
            
            def parse_pct(v):
                if pd.isna(v):
                    return 0
                if isinstance(v, (int, float)):
                    return float(v) / 100 if abs(float(v)) > 1 else float(v)
                try:
                    return float(str(v).replace('%', '')) / 100
                except:
                    return 0
            
            return {
                'code': f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}",
                'pubDate': datetime.now().strftime("%Y-%m-%d"),
                'statDate': str(latest.get('报告期', '')),
                'roeAvg': parse_pct(latest.get('净资产收益率', 0)),
                'npMargin': parse_pct(latest.get('销售净利率', 0)),
                'gpMargin': parse_pct(latest.get('销售毛利率', 0)),
                'netProfit': parse_val(latest.get('净利润', 0)),
                'epsTTM': parse_val(latest.get('基本每股收益', 0)),
                'MBRevenue': parse_val(latest.get('营业总收入', 0)),
                'totalShare': 0,
                'liqaShare': 0,
            }
    except Exception as e:
        return {}


def update_financial_batch(batch_size: int = 100):
    """批量更新财务数据"""
    
    print("=" * 60)
    print("📋 A股财务数据批量更新")
    print("=" * 60)
    
    # 读取现有数据
    existing = {}
    if FINANCIAL_FILE.exists():
        try:
            df = pd.read_csv(FINANCIAL_FILE)
            for _, row in df.iterrows():
                code = row.get('code', '')
                if code:
                    existing[code] = row.to_dict()
            print(f"已有财务记录: {len(existing)} 条")
        except:
            pass
    
    # 获取股票代码
    print("\n📋 获取股票代码列表...")
    all_codes = get_all_a_codes()
    print(f"股票文件总数: {len(all_codes)}")
    
    # 找出需要更新的
    to_update = []
    for code in all_codes:
        full_code = f"sh.{code}" if code.startswith('6') else f"sz.{code}"
        if full_code not in existing:
            to_update.append(code)
    
    print(f"需要更新: {len(to_update)} 只")
    
    # 分批更新
    success = 0
    failed = 0
    
    for i, code in enumerate(to_update[:batch_size]):
        print(f"[{i+1}/{min(batch_size, len(to_update))}] {code}...", end=" ")
        
        fin = fetch_financial_akshare(code)
        
        if fin:
            full_code = fin['code']
            existing[full_code] = fin
            success += 1
            print(f"✅ ROE={fin.get('roeAvg', 0)*100:.1f}%")
        else:
            failed += 1
            print("❌")
        
        time.sleep(random.uniform(0.3, 0.6))
        
        if (i + 1) % 20 == 0:
            print(f"\n   📊 进度: {i+1}/{min(batch_size, len(to_update))}")
    
    # 保存
    if existing:
        df = pd.DataFrame(list(existing.values()))
        df.to_csv(FINANCIAL_FILE, index=False)
        print(f"\n✅ 已保存 {len(df)} 条记录")
    
    print("\n" + "=" * 60)
    print(f"📊 更新完成: 成功 {success}, 失败 {failed}")
    print("=" * 60)
    
    return {'success': success, 'failed': failed}


if __name__ == "__main__":
    import sys
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    update_financial_batch(batch_size=batch)
