#!/usr/bin/env python3
"""
行为金融学分析 v4 - 整合宏观金融数据
每日多维度舆情分析 + 宏观经济摘要

版本: 4.0 (2026-03-04)
功能:
  - 资金情绪分析
  - 涨跌情绪分析
  - 涨停情绪分析
  - 板块舆情
  - 新闻情绪
  - 行为偏差检测
  - 宏观经济数据摘要 (新增)
"""
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
DATA_DIR = Path("/home/liujerry/金融数据")
PYTHON_BIN = "/home/liujerry/moltbot/openclaw_py/bin/python"
REPORT_DIR = DATA_DIR / "reports"


def log(msg, level="INFO"):
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "ℹ️")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix} {msg}")


def retry_request(func, max_retries=3, delay=5, *args, **kwargs):
    """带重试的请求函数"""
    import time
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = str(e)[:100]
            if attempt < max_retries:
                log(f"第 {attempt}/{max_retries} 次尝试失败: {last_error}, {delay}秒后重试...", "WARNING")
                time.sleep(delay)
            else:
                log(f"全部 {max_retries} 次尝试失败: {last_error}", "ERROR")
    
    return None


def try_multiple_sources(sources, source_names):
    """
    尝试多个数据源，自动切换
    sources: [(func1, args1), (func2, args2), ...]
    source_names: ["akshare", "baostock", ...]
    """
    import time
    
    for i, (func, args, kwargs) in enumerate(sources):
        try:
            name = source_names[i] if i < len(source_names) else f"数据源{i+1}"
            log(f"尝试数据源: {name}...", "INFO")
            result = func(*args, **kwargs)
            if result is not None:
                log(f"✅ {name} 成功获取数据", "SUCCESS")
                return result
        except Exception as e:
            log(f"⚠️ {source_names[i]} 失败: {str(e)[:50]}, 切换下一个...", "WARNING")
            time.sleep(2)
    
    log("❌ 所有数据源都失败", "ERROR")
    return None


def load_economic_summary():
    """加载宏观经济数据摘要"""
    log("📈 加载宏观经济数据...")
    
    # 先运行经济数据更新 (v3版本)
    try:
        subprocess.run(
            [PYTHON_BIN, str(DATA_DIR / "scripts/economic_data_enhanced_v3.py")],
            capture_output=True, timeout=180
        )
    except Exception as e:
        log(f"更新经济数据失败: {str(e)[:50]}", "WARNING")
    
    # 读取最新数据
    try:
        data_file = list(DATA_DIR.glob("macro/economic_enhanced_*.json"))
        if not data_file:
            return None
        
        latest = max(data_file, key=lambda x: x.stat().st_mtime)
        with open(latest) as f:
            data = json.load(f)
        
        summary = {}
        
        # 中国数据
        if "sources" in data and "china" in data["sources"]:
            china = data["sources"]["china"]
            
            # GDP
            if "gdp_yearly" in china:
                gdp = china["gdp_yearly"]
                if "今值" in gdp and gdp["今值"]:
                    vals = [v for v in gdp["今值"].values() if v and v != "NaN"]
                    if vals:
                        summary["GDP"] = f"{vals[-1]}%"
            
            # LPR
            if "lpr" in china:
                lpr = china["lpr"]
                if "lpr" in lpr and lpr["lpr"]:
                    vals = [v for v in lpr["lpr"].values() if v and v != "NaN"]
                    if vals:
                        summary["LPR"] = f"{vals[0]}%"
            
            # CPI
            if "cpi_yearly" in china:
                cpi = china["cpi_yearly"]
                if "今值" in cpi and cpi["今值"]:
                    vals = [v for v in cpi["今值"].values() if v and v != "NaN"]
                    if vals:
                        summary["CPI"] = f"{vals[-1]}%"
        
        # 汇率
        if "sources" in data and "exchange" in data["sources"]:
            ex = data["sources"]["exchange"]
            if "USD" in ex:
                usd = ex["USD"]
                if "CNY" in usd:
                    summary["USD/CNY"] = usd["CNY"]
        
        return summary
        
    except Exception as e:
        log(f"加载经济数据失败: {str(e)[:50]}", "WARNING")
        return None


def get_market_sentiment():
    """获取市场情绪数据 - 多数据源"""
    log("📊 获取市场情绪数据...")
    
    # 数据源1: akshare 实时行情 (可能失败)
    def source_akshare():
        import akshare as ak
        try:
            stock_zh_a_spot_em = ak.stock_zh_a_spot_em()
            
            up_count = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] > 0])
            down_count = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] < 0])
            flat_count = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] == 0])
            limit_up = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] >= 9.9])
            
            return {
                "上涨": up_count,
                "下跌": down_count,
                "平盘": flat_count,
                "涨停": limit_up,
                "总成交": len(stock_zh_a_spot_em),
                "source": "akshare"
            }
        except Exception as e:
            log(f"  ⚠️ akshare实时行情失败: {type(e).__name__}")
            return None
    
    # 数据源1.5: akshare 历史数据 - 创业板全量
    def source_akshare_hist():
        import akshare as ak
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        try:
            today = datetime.now().strftime('%Y%m%d')
            
            # 获取创业板股票列表 (300xxx开头)
            stock_list = ak.stock_info_a_code_name()
            chinese_stocks = stock_list[stock_list['code'].str.startswith('300')]['code'].tolist()
            log(f"  📊 创业板股票: {len(chinese_stocks)}只")
            
            def get_change(code):
                try:
                    df = ak.stock_zh_a_hist(symbol=code, period='daily', 
                                           start_date=today, end_date=today)
                    if len(df) > 0:
                        return float(df.iloc[0]['涨跌幅'])
                except:
                    pass
                return None
            
            # 多线程获取
            changes = []
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(get_change, code): code for code in chinese_stocks}
                for future in as_completed(futures, timeout=90):
                    try:
                        change = future.result()
                        if change is not None:
                            changes.append(change)
                    except:
                        pass
            
            if len(changes) > 0:
                up = sum(1 for c in changes if c > 0)
                down = sum(1 for c in changes if c < 0)
                flat = sum(1 for c in changes if c == 0)
                limit_up = sum(1 for c in changes if c >= 9.9)
                limit_down = sum(1 for c in changes if c <= -9.9)
                total = len(changes)
                
                log(f"  ✅ 获取创业板 {total} 只数据")
                
                return {
                    "上涨": up,
                    "下跌": down,
                    "平盘": flat,
                    "涨停": limit_up,
                    "跌停": limit_down,
                    "总成交": total,
                    "source": "创业板全量"
                }
        except Exception as e:
            log(f"  ⚠️ 创业板数据获取失败: {type(e).__name__}")
        return None
    
    # 数据源2: baostock
    def source_baostock():
        import baostock as bs
        import pandas as pd
        
        lg = bs.login()
        # 获取所有A股实时行情
        rs = bs.query_all_stock()
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        bs.logout()
        
        if not data_list:
            return None
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 转换涨跌幅为数值
        if 'changePercent' in df.columns:
            df['涨跌幅'] = pd.to_numeric(df['changePercent'], errors='coerce')
        
        up_count = len(df[df['涨跌幅'] > 0]) if '涨跌幅' in df.columns else 0
        down_count = len(df[df['涨跌幅'] < 0]) if '涨跌幅' in df.columns else 0
        flat_count = len(df[df['涨跌幅'] == 0]) if '涨跌幅' in df.columns else 0
        limit_up = len(df[df['涨跌幅'] >= 9.9]) if '涨跌幅' in df.columns else 0
        
        return {
            "上涨": up_count,
            "下跌": down_count,
            "平盘": flat_count,
            "涨停": limit_up,
            "总成交": len(df),
            "source": "baostock"
        }
    
    # 数据源3: sina (网页爬取)
    def source_sina():
        import requests
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 5000,
            "po": 1,
            "np": 1,
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f1,f2,f3,f4,f12,f13"
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        if data.get('data') and data['data'].get('diff'):
            stocks = data['data']['diff']
            up = sum(1 for s in stocks if float(s.get('f3', 0)) > 0)
            down = sum(1 for s in stocks if float(s.get('f3', 0)) < 0)
            flat = sum(1 for s in stocks if float(s.get('f3', 0)) == 0)
            limit_up = sum(1 for s in stocks if float(s.get('f3', 0)) >= 9.9)
            
            return {
                "上涨": up,
                "下跌": down,
                "平盘": flat,
                "涨停": limit_up,
                "总成交": len(stocks),
                "source": "sina/eastmoney"
            }
        return None
    
    # 尝试多个数据源
    sources = [
        (source_akshare, (), {}),
        (source_akshare_hist, (), {}),
        (source_baostock, (), {}),
        (source_sina, (), {})
    ]
    source_names = ["akshare", "akshare-hist", "baostock", "sina"]
    
    result = try_multiple_sources(sources, source_names)
    
    # 如果成功，移除 source 字段（用于显示）
    if result:
        result = {k: v for k, v in result.items() if k != 'source'}
    
    return result


def get_fund_flow():
    """获取资金流向 - 行为金融核心数据"""
    log("💰 获取资金流向...")
    
    # 数据源1: akshare 市场资金流向 (主力/散户)
    def source_akshare_market():
        import akshare as ak
        
        df = ak.stock_market_fund_flow()
        if df is None or len(df) == 0:
            return None
        
        # 取最新数据
        latest = df.iloc[-1]
        
        # 解析主力资金（超大单+大单）
        main_flow = float(latest.get('超大单净流入-净额', 0)) + float(latest.get('大单净流入-净额', 0))
        small_flow = float(latest.get('小单净流入-净额', 0))
        
        # 判断主力动向
        if main_flow > 0:
            main_action = "净流入"
        elif main_flow < 0:
            main_action = "净流出"
        else:
            main_action = "持平"
        
        return {
            "主力净流入": main_flow,
            "主力动向": main_action,
            "小单净流入": small_flow,
            "source": "市场资金"
        }
    
    # 数据源2: akshare 北向资金
    def source_akshare_hsgt():
        import akshare as ak
        
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is None or len(df) == 0:
            return None
        
        # 汇总北向资金（沪股通+深股通）
        north_money = 0
        north_up = north_down = 0
        
        for _, row in df.iterrows():
            if row.get('资金方向') == '北向' and row.get('板块') in ['沪股通', '深股通']:
                north_money += float(row.get('成交净买额', 0) or 0)
                north_up += int(row.get('上涨数', 0) or 0)
                north_down += int(row.get('下跌数', 0) or 0)
        
        return {
            "北向资金": north_money,
            "北向上涨": north_up,
            "北向下跌": north_down,
            "source": "北向资金"
        }
    
    # 数据源3: akshare 行业资金流向
    def source_akshare_industry():
        import akshare as ak
        
        df = ak.stock_fund_flow_industry()
        if df is None or len(df) == 0:
            return None
        
        # 取前5名资金流入行业
        top_inflow = df.nlargest(5, '净额')[['行业', '净额', '行业-涨跌幅']].values.tolist()
        
        # 取前5名资金流出行业
        top_outflow = df.nsmallest(5, '净额')[['行业', '净额', '行业-涨跌幅']].values.tolist()
        
        return {
            "流入前五": top_inflow,
            "流出前五": top_outflow,
            "source": "行业资金"
        }
    
    # 尝试多个数据源
    results = {}
    for source_fn in [source_akshare_market, source_akshare_hsgt, source_akshare_industry]:
        try:
            result = source_fn()
            if result:
                results.update(result)
        except Exception as e:
            log(f"  ⚠️ {source_fn.__name__} 失败: {type(e).__name__}")
    
    if results:
        return results
    
    return None


def get_institutional_behavior():
    """获取机构行为数据 - 龙虎榜+融资融券"""
    log("🏦 获取机构行为数据...")
    
    results = {}
    
    # 数据源1: 龙虎榜机构行为
    def source_lhb():
        import akshare as ak
        
        df = ak.stock_lhb_stock_statistic_em()
        if df is None or len(df) == 0:
            return None
        
        # 获取最新日期的数据
        latest_date = df['最近上榜日'].max()
        today_lhb = df[df['最近上榜日'] == latest_date]
        
        if len(today_lhb) == 0:
            return None
        
        # 统计机构买入/卖出
        institutional_buy = today_lhb['买方机构次数'].sum()
        institutional_sell = today_lhb['卖方机构次数'].sum()
        
        # 计算龙虎榜净买入
        net_buy = today_lhb['龙虎榜净买额'].sum()
        
        return {
            "龙虎榜净买额": net_buy,
            "机构买入": int(institutional_buy),
            "机构卖出": int(institutional_sell),
            "上榜股数": len(today_lhb),
            "数据日期": latest_date,
            "source": "龙虎榜"
        }
    
    # 数据源2: 融资融券 (杠杆情绪)
    def source_margin():
        import akshare as ak
        
        df = ak.stock_margin_account_info()
        if df is None or len(df) == 0:
            return None
        
        # 获取最新数据
        latest = df.iloc[-1]
        margin_balance = float(latest.get('融资余额', 0)) * 1e8  # 转换为元
        margin_buy = float(latest.get('融资买入额', 0)) * 1e8
        
        # 融资余额变化
        if len(df) >= 2:
            prev = df.iloc[-2]
            prev_balance = float(prev.get('融资余额', 0)) * 1e8
            margin_change = margin_balance - prev_balance
        else:
            margin_change = 0
        
        # 维持担保比
        avg_ratio = latest.get('平均维持担保比例', 0)
        
        # 参与交易投资者
        traders = latest.get('参与交易的投资者数量', 0)
        
        return {
            "融资余额": margin_balance,
            "融资买入": margin_buy,
            "融资变化": margin_change,
            "avg_ratio": float(avg_ratio),
            "参与交易者": int(traders),
            "数据日期": str(latest.get('日期', '')),
            "source": "融资融券"
        }
    
    # 获取数据
    for source_fn in [source_lhb, source_margin]:
        try:
            result = source_fn()
            if result:
                results.update(result)
        except Exception as e:
            log(f"  ⚠️ {source_fn.__name__} 失败: {type(e).__name__}")
    
    if results:
        return results
    
    return None


def format_report(market_sentiment, fund_flow, economic_data, institutional=None):
    """格式化分析报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 每日行为金融学分析 + 宏观数据")
    lines.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("=" * 60)
    
    # 宏观经济数据
    if economic_data:
        lines.append("\n🌍 【宏观经济摘要】")
        for k, v in economic_data.items():
            lines.append(f"  • {k}: {v}")
    
    # 市场情绪
    if market_sentiment:
        lines.append("\n📈 【市场情绪】")
        total = market_sentiment.get("总成交", 1)
        up_pct = market_sentiment.get("上涨", 0) / total * 100
        down_pct = market_sentiment.get("下跌", 0) / total * 100
        lines.append(f"  • 上涨: {market_sentiment.get('上涨', 0)} ({up_pct:.1f}%)")
        lines.append(f"  • 下跌: {market_sentiment.get('下跌', 0)} ({down_pct:.1f}%)")
        lines.append(f"  • 涨停: {market_sentiment.get('涨停', 0)}")
    
    # 资金流向 - 行为金融核心
    if fund_flow:
        lines.append("\n💵 【资金流向 - 行为金融分析】")
        
        # 主力资金
        if "主力净流入" in fund_flow:
            main_flow = fund_flow.get("主力净流入", 0) / 1e8  # 转换为亿
            main_action = fund_flow.get("主力动向", "未知")
            lines.append(f"  • 主力资金: {main_action} ({main_flow:.2f}亿)")
        
        # 北向资金
        if "北向资金" in fund_flow:
            north = fund_flow.get("北向资金", 0) / 1e8
            north_up = fund_flow.get("北向上涨", 0)
            north_down = fund_flow.get("北向下跌", 0)
            lines.append(f"  • 北向资金: {north:.2f}亿 (上涨{north_up}家/下跌{north_down}家)")
        
        # 行业资金
        if "流入前五" in fund_flow:
            lines.append("\n  📊 资金流入行业:")
            for item in fund_flow.get("流入前五", [])[:3]:
                lines.append(f"    • {item[0]}: +{item[1]:.2f}亿 ({item[2]:+.2f}%)")
        
        if "流出前五" in fund_flow:
            lines.append("\n  📊 资金流出行业:")
            for item in fund_flow.get("流出前五", [])[:3]:
                lines.append(f"    • {item[0]}: {item[1]:.2f}亿 ({item[2]:+.2f}%)")
    
    # 机构行为 - 龙虎榜+融资融券
    if institutional:
        lines.append("\n🏦 【机构行为 - 杠杆与主力】")
        
        # 龙虎榜
        if "龙虎榜净买额" in institutional:
            lhb_net = institutional.get("龙虎榜净买额", 0) / 1e8
            lhb_count = institutional.get("上榜股数", 0)
            inst_buy = institutional.get("机构买入", 0)
            inst_sell = institutional.get("机构卖出", 0)
            lhb_date = institutional.get("数据日期", "未知")
            lines.append(f"  • 龙虎榜 ({lhb_date}): 净买入 {lhb_net:.2f}亿 ({lhb_count}只股票)")
            lines.append(f"    - 机构买入: {inst_buy}次, 机构卖出: {inst_sell}次")
        
        # 融资融券
        if "融资余额" in institutional:
            margin = institutional.get("融资余额", 0) / 1e8
            margin_buy = institutional.get("融资买入", 0) / 1e8
            margin_change = institutional.get("融资变化", 0) / 1e8
            avg_ratio = institutional.get("avg_ratio", 0)
            traders = institutional.get("参与交易者", 0)
            margin_date = institutional.get("数据日期", "未知")
            lines.append(f"  • 融资融券 ({margin_date}):")
            lines.append(f"    - 融资余额: {margin:.2f}亿, 今日买入: {margin_buy:.2f}亿")
            lines.append(f"    - 融资变化: {margin_change:+.2f}亿")
            lines.append(f"    - 维持担保比: {avg_ratio:.1f}%")
            lines.append(f"    - 参与交易者: {traders:,}人")
    
    # 行为建议
    lines.append("\n🎯 【投资建议】")
    
    # 基于数据分析给出建议
    if market_sentiment:
        limit_up = market_sentiment.get("涨停", 0)
        if limit_up > 50:
            lines.append("  • 市场情绪过热，谨慎追高")
        elif limit_up < 10:
            lines.append("  • 市场情绪低迷，可能存在反弹机会")
    
    if economic_data:
        lines.append("  • 关注宏观经济数据变化")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)


def main():
    log("=" * 50)
    log("📊 行为金融学分析 v4 + 宏观数据")
    log("=" * 50)
    
    # 1. 宏观经济数据
    economic_data = load_economic_summary()
    
    # 2. 市场情绪
    market_sentiment = get_market_sentiment()
    
    # 3. 资金流向
    fund_flow = get_fund_flow()
    
    # 4. 机构行为 (龙虎榜+融资融券)
    institutional = get_institutional_behavior()
    
    # 5. 生成报告
    report = format_report(market_sentiment, fund_flow, economic_data, institutional)
    print(report)
    
    # 5. 保存报告
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORT_DIR / f"behavioral_macro_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    log(f"\n💾 报告已保存: {report_file}")
    
    # 6. 保存JSON数据
    json_file = REPORT_DIR / f"behavioral_macro_{datetime.now().strftime('%Y%m%d')}.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "economic": economic_data,
        "market": market_sentiment,
        "fund": fund_flow
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    log(f"📄 JSON数据: {json_file}")
    
    return report


if __name__ == "__main__":
    main()
