#!/usr/bin/env python3
"""
获取所有A股历史数据
目标：每只股票至少1000条数据（5年历史）
截止日期：2026年2月6日
"""
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 配置
END_DATE = datetime(2026, 2, 6)
START_DATE = END_DATE - timedelta(days=1825)  # 5年

PROGRESS_FILE = Path.home() / ".config" / "deepseeker" / "all_a_stocks_progress.json"


def get_all_a_stocks_from_baostock():
    """从baostock获取所有A股列表"""
    import baostock as bs
    
    print("📋 获取所有A股列表...")
    all_stocks = []
    
    lg = bs.login()
    if lg.error_code != '0':
        print("   ❌ baostock 登录失败")
        return []
    
    rs = bs.query_stock_industry()
    
    while (rs.error_code == '0') and rs.next():
        row = rs.get_row_data()
        code = row[1]  # sh.600000
        name = row[2]  # 浦发银行
        
        # 提取纯代码
        pure_code = code.split('.')[-1]
        
        if pure_code and name:
            all_stocks.append((pure_code, name))
    
    bs.logout()
    
    print(f"   ✅ 共获取 {len(all_stocks)} 只A股")
    return all_stocks


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_stocks": 0,
        "completed": [],
        "failed": [],
        "batch_index": 0,
        "total_fetched": 0,
        "last_run": None,
        "data_range": {
            "start": START_DATE.strftime("%Y-%m-%d"),
            "end": END_DATE.strftime("%Y-%m-%d")
        }
    }


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)


def fetch_history_baostock(symbol, name):
    """baostock 获取历史数据"""
    try:
        import baostock as bs
        
        lg = bs.login()
        if lg.error_code != '0':
            return None, None
        
        bs_symbol = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"
        
        rs = bs.query_history_k_data_plus(
            bs_symbol,
            "date,open,high,low,close,volume",
            start_date=START_DATE.strftime("%Y-%m-%d"),
            end_date=END_DATE.strftime("%Y-%m-%d"),
            frequency="d",
            adjustflag="2"
        )
        
        data_list = []
        while (rs.error_code == '0') and rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if data_list:
            df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df, "baostock"
    
    except Exception as e:
        pass
    
    return None, None


def fetch_stock_history(symbol, name):
    """获取单只股票历史数据"""
    df, source = fetch_history_baostock(symbol, name)
    return df, source


def save_to_csv(df, symbol):
    output_dir = Path("/home/liujerry/金融数据/stocks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{symbol}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    return output_file


def init_all_stocks():
    """初始化所有股票列表"""
    progress = load_progress()
    
    if 'all_stocks' in progress and progress['all_stocks']:
        print(f"📊 已加载 {len(progress['all_stocks'])} 只股票")
        return progress['all_stocks']
    
    # 获取所有A股
    stocks = get_all_a_stocks_from_baostock()
    
    if stocks:
        progress['all_stocks'] = stocks
        progress['total_stocks'] = len(stocks)
        save_progress(progress)
        return stocks
    else:
        print("⚠️ 无法获取股票列表")
        return []


def batch_fetch(batch_index, batch_size=200):
    """批量获取"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print("📈 获取所有A股历史数据")
    print(f"⏰ {timestamp}")
    print(f"📅 范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")
    print(f"📦 批次: {batch_index}, 每批: {batch_size}只")
    print("=" * 80)
    
    progress = load_progress()
    
    # 确保有股票列表
    if 'all_stocks' not in progress:
        stocks = init_all_stocks()
        if not stocks:
            print("❌ 无法获取股票列表")
            return
    else:
        stocks = progress['all_stocks']
    
    total_stocks = len(stocks)
    
    # 获取已完成列表
    completed = set(progress.get('completed', []))
    failed = set(progress.get('failed', []))
    
    # 计算本批次
    start_idx = batch_index * batch_size
    end_idx = min(start_idx + batch_size, total_stocks)
    
    if start_idx >= total_stocks:
        print(f"\n✅ 所有批次已完成！")
        print(f"📊 总进度: {len(completed)}/{total_stocks}")
        return
    
    batch_stocks = stocks[start_idx:end_idx]
    
    print(f"\n📊 进度: {start_idx}/{total_stocks} ({start_idx/total_stocks*100:.1f}%)")
    print(f"   本批次: {start_idx}~{end_idx}")
    
    success = failed_count = 0
    qualified = 0
    source_counts = {}
    
    for i, (symbol, name) in enumerate(batch_stocks, 1):
        current = start_idx + i
        
        if symbol in completed:
            if i <= 5:  # 只显示前5个
                print(f"[{current}/{total_stocks}] {symbol} ({name})... ⏭️ 已完成")
            elif i == 6:
                print(f"   ... (还有更多已完成)")
            continue
        
        if i <= 5:  # 只显示前5个
            print(f"[{current}/{total_stocks}] {symbol} ({name})...", end=" ", flush=True)
        elif i == 6:
            print("   ...")
        
        df, source = fetch_stock_history(symbol, name)
        
        if df is not None and not df.empty:
            save_to_csv(df, symbol)
            records = len(df)
            latest = df['date'].iloc[-1].strftime("%Y-%m-%d")
            
            if i <= 5:
                if records >= 1000:
                    print(f"✓ ({source}, {latest}, {records}条) ✅")
                else:
                    print(f"✓ ({source}, {latest}, {records}条) ⚠️")
            
            if records >= 1000:
                qualified += 1
            
            success += 1
            source_counts[source] = source_counts.get(source, 0) + 1
            completed.add(symbol)
            
            if symbol in failed:
                failed.discard(symbol)
        else:
            if i <= 5:
                print("✗")
            failed_count += 1
            failed.add(symbol)
        
        # 每100只输出进度
        if i % 100 == 0:
            print(f"\n📊 批次进度: {i}/{len(batch_stocks)}")
        
        time.sleep(0.2)
    
    # 保存进度
    progress['completed'] = list(completed)
    progress['failed'] = list(failed)
    progress['batch_index'] = batch_index
    progress['total_fetched'] = len(completed)
    progress['last_run'] = timestamp
    save_progress(progress)
    
    # 统计
    pct = len(completed) / total_stocks * 100 if total_stocks > 0 else 0
    
    print(f"\n" + "=" * 80)
    print(f"📊 批次完成: {success}, 失败: {failed_count}")
    print(f"📈 达标股票: {qualified}/{success}")
    print(f"📊 总体进度: {len(completed)}/{total_stocks} ({pct:.2f}%)")
    print("=" * 80)
    
    # 预计剩余时间
    remaining = total_stocks - len(completed)
    batches_left = (remaining + batch_size - 1) // batch_size
    print(f"📅 预计还需 {batches_left} 批次完成全部")
    
    # JSON 输出
    print("\n---OUTPUT_START---")
    result = {
        "status": "batch_complete",
        "batch_index": batch_index,
        "success": success,
        "failed": failed_count,
        "qualified": qualified,
        "total_completed": len(completed),
        "total_stocks": total_stocks,
        "progress_pct": round(pct, 2),
        "batches_left": batches_left,
        "timestamp": timestamp
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---OUTPUT_END---")


def check_quality():
    """检查数据质量"""
    progress = load_progress()
    completed = progress.get('completed', [])
    total = len(completed)
    
    if total == 0:
        print("📊 暂无数据")
        return
    
    qualified = 0
    data_dir = Path("/home/liujerry/金融数据/stocks")
    
    print("📊 数据质量检查:")
    print(f"   总完成: {total} 只")
    
    for symbol in completed[:20]:
        file_path = data_dir / f"{symbol}.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            records = len(df)
            if records >= 1000:
                qualified += 1
                status = "✅"
            else:
                status = "⚠️"
            print(f"   {status} {symbol}: {records}条")
    
    if total > 20:
        print(f"   ... 还有 {total - 20} 只")
    
    print(f"\n📈 达标率: {qualified}/{total} ({qualified/total*100:.1f}%)")


def show_summary():
    """显示摘要"""
    progress = load_progress()
    
    print("\n" + "=" * 80)
    print("📊 A股历史数据获取进度")
    print("=" * 80)
    
    total = progress.get('total_stocks', 0)
    completed = len(progress.get('completed', []))
    failed = len(progress.get('failed', []))
    batch_idx = progress.get('batch_index', 0)
    last_run = progress.get('last_run', '未知')
    
    pct = completed / total * 100 if total > 0 else 0
    
    print(f"\n📅 数据范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")
    print(f"📦 当前批次: {batch_idx}")
    print(f"⏰ 最后运行: {last_run}")
    print(f"\n📊 完成: {completed}/{total} ({pct:.2f}%)")
    print(f"📊 失败: {failed}")
    
    if total > 0:
        batches_total = (total + 199) // 200
        batches_done = batch_idx + 1
        batches_left = batches_total - batches_done
        
        print(f"\n📅 批次: {batches_done}/{batches_total}")
        print(f"📅 还需: {batches_left} 批次")
    
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--init":
            stocks = init_all_stocks()
            if stocks:
                print(f"✅ 已加载 {len(stocks)} 只A股")
        elif sys.argv[1] == "--status":
            show_summary()
        elif sys.argv[1] == "--quality":
            check_quality()
        elif sys.argv[1] == "--reset":
            if PROGRESS_FILE.exists():
                PROGRESS_FILE.unlink()
            print("✅ 进度已重置")
        elif sys.argv[1] == "--full":
            # 完整获取
            stocks = init_all_stocks()
            if stocks:
                total = len(stocks)
                for i in range((total + 199) // 200):
                    if i > 0:
                        time.sleep(5)
                    batch_fetch(i, 200)
        else:
            try:
                batch_index = int(sys.argv[1])
                batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
                batch_fetch(batch_index, batch_size)
            except:
                batch_fetch(0, 200)
    else:
        show_summary()
