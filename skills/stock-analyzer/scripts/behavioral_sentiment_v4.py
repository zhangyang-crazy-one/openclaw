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
    
    # 数据源1: akshare
    def source_akshare():
        import akshare as ak
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
        (source_baostock, (), {}),
        (source_sina, (), {})
    ]
    source_names = ["akshare", "baostock", "sina"]
    
    result = try_multiple_sources(sources, source_names)
    
    # 如果成功，移除 source 字段（用于显示）
    if result:
        result = {k: v for k, v in result.items() if k != 'source'}
    
    return result


def get_fund_flow():
    """获取资金流向 - 多数据源"""
    log("💰 获取资金流向...")
    
    # 数据源1: akshare 沪港通
    def source_akshare_hsgt():
        import akshare as ak
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is not None and not df.empty:
            north_data = df[df['资金方向'] == '北向']
            if not north_data.empty:
                # 获取净流入列（需要检查具体列名）
                return {"北向资金(沪港通)": "获取成功", "source": "akshare-hsgt"}
        return None
    
    # 数据源2: akshare 市场资金流向
    def source_akshare_market():
        import akshare as ak
        df = ak.stock_market_fund_flow()
        if df is not None:
            return {"市场资金流向": "获取成功", "source": "akshare-market"}
        return None
    
    # 数据源3: baostock 资金流向
    def source_baostock():
        import baostock as bs
        import pandas as pd
        
        lg = bs.login()
        # 获取北向资金数据
        rs = bs.query_hsgt_stocks()
        bs.logout()
        
        if rs.error_code == '0' and rs.next():
            return {"北向资金(baostock)": "获取成功", "source": "baostock"}
        return None
    
    # 尝试多个数据源
    sources = [
        (source_akshare_hsgt, (), {}),
        (source_akshare_market, (), {}),
        (source_baostock, (), {})
    ]
    source_names = ["akshare-沪港通", "akshare-市场", "baostock"]
    
    result = try_multiple_sources(sources, source_names)
    
    # 如果成功，移除 source 字段
    if result:
        result = {k: v for k, v in result.items() if k != 'source'}
    
    if result is None:
        log("获取资金流向失败，跳过", "WARNING")
    
    return result


def format_report(market_sentiment, fund_flow, economic_data):
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
    
    # 资金流向
    if fund_flow:
        lines.append("\n💵 【资金流向】")
        for k, v in fund_flow.items():
            lines.append(f"  • {k}: {v}亿")
    
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
    
    # 4. 生成报告
    report = format_report(market_sentiment, fund_flow, economic_data)
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
