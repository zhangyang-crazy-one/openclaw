#!/usr/bin/env python3
"""
K线数据更新脚本 - 基于新浪财经API
解决 EastMoney push2his 被封锁的问题

使用方法:
    python3 update_kline_sina.py                    # 更新所有939只股票
    python3 update_kline_sina.py --limit 10          # 仅测试前10只
    python3 update_kline_sina.py --codes 600519,000001  # 指定股票
"""

import os
import sys
import time
import argparse
import urllib.request
import json
from pathlib import Path
from datetime import datetime, timedelta

PROXY = "http://127.0.0.1:7897"
PROXY_HANDLER = urllib.request.ProxyHandler({
    'http': PROXY,
    'https': PROXY,
})

STOCKS_DIR = Path("/home/liujerry/金融数据/stocks_clean")
LOG_FILE = Path("/home/liujerry/金融数据/logs/sina_kline_update.log")

# A股代码前缀 -> 新浪symbol前缀
def get_sina_symbol(code: str) -> str:
    """根据代码判断交易所前缀"""
    if code.startswith(('6', '5', '9')):  # 上交所
        return f"sh{code}"
    else:  # 深交所
        return f"sz{code}"


def get_latest_date(csv_path: Path) -> str:
    """获取CSV最新日期"""
    if not csv_path.exists():
        return None
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        if len(lines) <= 1:
            return None
        last_line = lines[-1].strip()
        return last_line.split(',')[0]
    except:
        return None


def fetch_kline_sina(symbol: str, scale: int = 240, datalen: int = 500) -> list:
    """从新浪财经获取K线数据"""
    url = (
        f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
        f"/CN_MarketData.getKLineData"
        f"?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
    )
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://finance.sina.com.cn/',
    })
    
    try:
        opener = urllib.request.build_opener(PROXY_HANDLER)
        response = opener.open(req, timeout=15)
        data = response.read().decode('utf-8')
        return json.loads(data)
    except Exception as e:
        return None


def merge_kline_data(csv_path: Path, new_data: list) -> tuple:
    """合并新旧数据，返回 (新增行数, 跳过行数)"""
    if not new_data:
        return 0, 0
    
    existing_dates = set()
    if csv_path.exists():
        with open(csv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if parts:
                        existing_dates.add(parts[0])
    
    new_rows = []
    skipped = 0
    for item in new_data:
        day = item.get('day', '')
        if not day or day in existing_dates:
            skipped += 1
            continue
        
        open_p = item.get('open', '')
        high = item.get('high', '')
        low = item.get('low', '')
        close = item.get('close', '')
        volume = item.get('volume', '')
        
        new_rows.append(f"{day},{open_p},{high},{low},{close},{volume}")
    
    if not new_rows:
        return 0, skipped
    
    # 追加写入
    with open(csv_path, 'a') as f:
        for row in new_rows:
            f.write(row + '\n')
    
    return len(new_rows), skipped


def update_stock(code: str, dry_run: bool = False) -> dict:
    """更新单只股票的K线数据"""
    symbol = get_sina_symbol(code)
    csv_path = STOCKS_DIR / f"{code}.csv"
    latest = get_latest_date(csv_path)
    
    # 获取数据（最多500天，足够覆盖缺失的54天）
    data = fetch_kline_with_retry(symbol, scale=240, datalen=500)
    
    if data is None:
        return {'code': code, 'status': 'failed', 'reason': 'fetch_failed'}
    
    if not data:
        return {'code': code, 'status': 'failed', 'reason': 'empty_data'}
    
    # 计算需要添加的行
    existing_dates = set()
    if csv_path.exists():
        with open(csv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if parts:
                        existing_dates.add(parts[0])
    
    new_rows = []
    for item in data:
        day = item.get('day', '')
        if day and day not in existing_dates:
            new_rows.append(item)
    
    if not new_rows:
        return {'code': code, 'status': 'skip', 'reason': 'already_latest', 'latest': latest}
    
    if dry_run:
        return {
            'code': code,
            'status': 'dry_run',
            'would_add': len(new_rows),
            'first_new': new_rows[0].get('day') if new_rows else None,
            'last_new': new_rows[-1].get('day') if new_rows else None,
        }
    
    added, skipped = merge_kline_data(csv_path, new_rows)
    return {
        'code': code,
        'status': 'success',
        'added': added,
        'skipped': skipped,
        'latest': data[0].get('day') if data else None,
    }


def get_all_codes() -> list:
    """获取所有已有CSV的股票代码"""
    if not STOCKS_DIR.exists():
        return []
    return [f.stem for f in STOCKS_DIR.glob("*.csv")]


def fetch_kline_with_retry(symbol: str, scale: int = 240, datalen: int = 500) -> list:
    """带1次重试的K线获取（失败后等10秒再试）"""
    data = fetch_kline_sina(symbol, scale, datalen)
    if data is not None:
        return data
    # 重试一次，失败后等待10秒
    time.sleep(10)
    return fetch_kline_sina(symbol, scale, datalen)


def update_stock_with_retry(code: str, dry_run: bool = False, delay: float = 0.5) -> dict:
    """带延迟的更新单只股票"""
    time.sleep(delay)
    return update_stock(code, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(description='K线数据更新 - 新浪财经API')
    parser.add_argument('--codes', type=str, help='指定股票代码，逗号分隔')
    parser.add_argument('--limit', type=int, help='限制数量（测试用）')
    parser.add_argument('--dry-run', action='store_true', help='仅测试不写入')
    parser.add_argument('--delay', type=float, default=5.0, help='请求间隔(秒)')
    parser.add_argument('--retry-failed', action='store_true', help='仅重试上次失败的')
    args = parser.parse_args()
    
    os.makedirs(STOCKS_DIR.parent / "logs", exist_ok=True)
    
    if args.codes:
        codes = args.codes.split(',')
    elif args.retry_failed:
        # 从日志中提取失败的代码
        codes = []
        if LOG_FILE.exists():
            with open(LOG_FILE) as f:
                for line in f:
                    if '✗' in line and 'fetch_failed' in line:
                        parts = line.strip().split(']')
                        if len(parts) >= 2:
                            code_part = parts[1].split(':')[0].strip()
                            codes.append(code_part)
        codes = list(dict.fromkeys(codes))  # 去重保持顺序
        if not codes:
            print("没有找到上次失败的股票")
            return
    else:
        codes = get_all_codes()
    
    if args.limit:
        codes = codes[:args.limit]
    
    log(LOG_FILE, f"=== K线更新开始 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    log(LOG_FILE, f"股票数量: {len(codes)}, 干运行: {args.dry_run}, 延迟: {args.delay}s")
    
    success = failed = skip = 0
    results = []
    
    for i, code in enumerate(codes, 1):
        result = update_stock_with_retry(code, dry_run=args.dry_run, delay=0)
        results.append(result)
        
        if result['status'] == 'success':
            success += 1
            msg = f"✓ [{i}/{len(codes)}] {code}: +{result['added']}行"
        elif result['status'] == 'skip':
            skip += 1
            msg = f"○ [{i}/{len(codes)}] {code}: 已最新"
        elif result['status'] == 'dry_run':
            msg = f"? [{i}/{len(codes)}] {code}: 将添加{result['would_add']}行"
        else:
            failed += 1
            msg = f"✗ [{i}/{len(codes)}] {code}: {result.get('reason')}"
        
        print(msg)
        log(LOG_FILE, msg)
        
        # 礼貌延迟
        time.sleep(args.delay)
    
    summary = f"完成: ✓{success} ○{skip} ✗{failed}"
    print(f"\n{summary}")
    log(LOG_FILE, summary)


def log(path: Path, msg: str):
    """写入日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")


if __name__ == "__main__":
    main()
