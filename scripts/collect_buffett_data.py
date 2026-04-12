#!/usr/bin/env python3
"""
巴菲特10大公式数据补齐脚本
收集缺失的字段：货币资金、短期借款、长期借款、流动资产、流动负债、利息支出、自由现金流等

使用分批处理 + 延迟避免封禁
"""
import akshare as ak
import pandas as pd
import time
import json
import os
from datetime import datetime

# 配置
BATCH_SIZE = 50  # 每批处理数量
BATCH_DELAY = 30  # 批次间延迟(秒)
API_DELAY = 3  # API调用间隔(秒)
OUTPUT_FILE = "/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv"
PROGRESS_FILE = "/home/liujerry/金融数据/fundamentals/buffett_progress.json"

# 获取股票列表
def get_stock_list():
    """获取A股股票列表"""
    # 使用现有的financial数据中的股票代码
    fin_df = pd.read_csv("/home/liujerry/金融数据/fundamentals/chuangye_full/financial_main_em.csv", low_memory=False)
    codes = fin_df['code'].unique().tolist()
    # 转换为6位代码
    codes = [str(int(c)).zfill(6) for c in codes if pd.notna(c)]
    return codes

def get_buffett_data(code):
    """
    获取单只股票的巴菲特公式补充数据
    返回: dict 或 None
    """
    try:
        # 使用新浪财务报告接口 (成功率最高)
        df = ak.stock_financial_report_sina(stock=code)
        if df is None or len(df) == 0:
            return None
        
        # 获取最新一期数据 (第一行)
        latest = df.iloc[0]
        
        # 提取所需字段
        data = {
            'code': code,
            'report_date': latest.get('报告日', ''),
        }
        
        # 货币资金 (Cash)
        data['cash'] = latest.get('货币资金', 0) or 0
        
        # 短期借款 (Short-term borrowings)
        data['short_debt'] = latest.get('短期借款', 0) or 0
        
        # 长期借款 (Long-term borrowings)  
        data['long_debt'] = latest.get('长期借款', 0) or 0
        
        # 流动资产 (Current assets)
        data['current_assets'] = latest.get('流动资产', 0) or 0
        
        # 流动负债 (Current liabilities)
        data['current_liabilities'] = latest.get('流动负债', 0) or 0
        
        # 总资产 (Total assets)
        data['total_assets'] = latest.get('资产总计', 0) or 0
        
        # 总负债 (Total liabilities)
        data['total_liabilities'] = latest.get('负债合计', 0) or 0
        
        # 所有者权益 (Equity)
        data['equity'] = latest.get('所有者权益合计', 0) or 0
        
        # 利息支出 (Interest expense) - 可能需要从现金流量表获取
        data['interest_expense'] = latest.get('利息支出', 0) or 0
        
        # 营业收入 (Revenue)
        data['revenue'] = latest.get('营业总收入', 0) or latest.get('营业收入', 0) or 0
        
        # 营业利润 (Operating profit)
        data['operating_profit'] = latest.get('营业利润', 0) or 0
        
        # 净利润 (Net income)
        data['net_income'] = latest.get('净利润', 0) or latest.get('归属净利润', 0) or 0
        
        return data
        
    except Exception as e:
        # 如果新浪接口失败，尝试东方财富 abstract 接口
        try:
            suffix = 'sz' if code.startswith('000') or code.startswith('001') or code.startswith('002') or code.startswith('300') else 'sh'
            df = ak.stock_financial_abstract(symbol=f"{suffix}{code}")
            if df is None:
                return None
            
            # 查找最新一期的数据
            # 获取"常用指标"部分的流动资产和流动负债
            latest_date = df.columns[2]  # 第三列开始是日期
            row = df[df['指标'] == '流动资产合计']
            if len(row) > 0:
                current_assets = row[latest_date].values[0]
            else:
                current_assets = 0
            
            row = df[df['指标'] == '流动负债合计']
            current_liabilities = row[latest_date].values[0] if len(row) > 0 else 0
            
            row = df[df['指标'] == '货币资金']
            cash = row[latest_date].values[0] if len(row) > 0 else 0
            
            row = df[df['指标'] == '短期借款']
            short_debt = row[latest_date].values[0] if len(row) > 0 else 0
            
            row = df[df['指标'] == '长期借款']
            long_debt = row[latest_date].values[0] if len(row) > 0 else 0
            
            row = df[df['指标'] == '资产总计']
            total_assets = row[latest_date].values[0] if len(row) > 0 else 0
            
            row = df[df['指标'] == '负债合计']
            total_liabilities = row[latest_date].values[0] if len(row) > 0 else 0
            
            row = df[df['指标'] == '归属净利润']
            net_income = row[latest_date].values[0] if len(row) > 0 else 0
            
            return {
                'code': code,
                'report_date': latest_date,
                'cash': cash or 0,
                'short_debt': short_debt or 0,
                'long_debt': long_debt or 0,
                'current_assets': current_assets or 0,
                'current_liabilities': current_liabilities or 0,
                'total_assets': total_assets or 0,
                'total_liabilities': total_liabilities or 0,
                'equity': 0,
                'interest_expense': 0,
                'revenue': 0,
                'operating_profit': 0,
                'net_income': net_income or 0,
            }
        except Exception as e2:
            print(f"    {code} 第二方案也失败: {e2}")
            return None

def save_progress(processed, failed, total):
    """保存进度"""
    progress = {
        'processed': processed,
        'failed': failed,
        'total': total,
        'last_update': datetime.now().isoformat()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def load_progress():
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'processed': 0, 'failed': [], 'total': 0}

def run(start_idx=0, batch_count=0, limit=0):
    """
    运行数据采集
    
    Args:
        start_idx: 起始索引
        batch_count: 每批数量 (0表示处理全部)
        limit: 总处理限制 (0表示不限制)
    """
    stocks = get_stock_list()
    total = len(stocks)
    
    # 加载进度
    progress = load_progress()
    start_idx = progress.get('processed', start_idx)
    failed_codes = set(progress.get('failed', []))
    
    print(f"=== 巴菲特数据补齐脚本 ===")
    print(f"总股票数: {total}")
    print(f"起始索引: {start_idx}")
    print(f"每批数量: {batch_count if batch_count > 0 else '全部'}")
    print(f"总限制: {limit if limit > 0 else '不限制'}")
    print()
    
    # 初始化结果列表
    results = []
    
    # 如果已有输出文件，加载现有数据
    if os.path.exists(OUTPUT_FILE):
        existing = pd.read_csv(OUTPUT_FILE)
        results = existing.to_dict('records')
        existing_codes = set(existing['code'].tolist())
        print(f"已存在 {len(results)} 条记录")
    else:
        existing_codes = set()
    
    # 处理股票
    processed = start_idx
    failed = list(failed_codes)
    
    for i, code in enumerate(stocks[start_idx:], start=start_idx):
        # 检查限制
        if limit > 0 and i >= start_idx + limit:
            print(f"\n达到处理限制 {limit}，停止")
            break
        
        # 跳过已处理的
        if code in existing_codes:
            continue
        
        print(f"[{i+1}/{total}] 处理 {code}...", end=" ", flush=True)
        
        data = get_buffett_data(code)
        
        if data:
            results.append(data)
            print(f"✅")
        else:
            failed.append(code)
            print(f"❌")
        
        processed = i + 1
        
        # API延迟
        time.sleep(API_DELAY)
        
        # 每批次保存
        if (i + 1) % 10 == 0:
            df = pd.DataFrame(results)
            df.to_csv(OUTPUT_FILE, index=False)
            save_progress(processed, failed, total)
            print(f"    已保存 {len(results)} 条记录")
        
        # 批次间延迟
        if batch_count > 0 and (i + 1) % batch_count == 0:
            print(f"\n批次完成，休息 {BATCH_DELAY} 秒...")
            time.sleep(BATCH_DELAY)
    
    # 最终保存
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)
    save_progress(processed, failed, total)
    
    print(f"\n=== 完成 ===")
    print(f"总记录: {len(results)}")
    print(f"失败数: {len(failed)}")
    print(f"输出: {OUTPUT_FILE}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0, help='起始索引')
    parser.add_argument('--batch', type=int, default=0, help='每批数量(0=全部)')
    parser.add_argument('--limit', type=int, default=0, help='总处理限制(0=不限制)')
    args = parser.parse_args()
    
    run(args.start, args.batch, args.limit)