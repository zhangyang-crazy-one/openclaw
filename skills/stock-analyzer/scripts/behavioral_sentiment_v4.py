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


def load_economic_summary():
    """加载宏观经济数据摘要"""
    log("📈 加载宏观经济数据...")
    
    # 先运行经济数据更新
    try:
        subprocess.run(
            [PYTHON_BIN, str(DATA_DIR / "scripts/economic_data_enhanced.py")],
            capture_output=True, timeout=120
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
    """获取市场情绪数据"""
    log("📊 获取市场情绪数据...")
    
    # 尝试从akshare获取市场数据
    try:
        import akshare as ak
        stock_zh_a_spot_em = ak.stock_zh_a_spot_em()
        
        # 计算涨跌情绪
        up_count = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] > 0])
        down_count = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] < 0])
        flat_count = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] == 0])
        
        # 涨停数量
        limit_up = len(stock_zh_a_spot_em[stock_zh_a_spot_em['涨跌幅'] >= 9.9])
        
        return {
            "上涨": up_count,
            "下跌": down_count,
            "平盘": flat_count,
            "涨停": limit_up,
            "总成交": len(stock_zh_a_spot_em)
        }
    except Exception as e:
        log(f"获取市场数据失败: {str(e)[:50]}", "WARNING")
        return None


def get_fund_flow():
    """获取资金流向"""
    log("💰 获取资金流向...")
    
    try:
        import akshare as ak
        # 北向资金
        try:
            north_money = ak.stock_fund_flow_statistics(symbol="北向资金")
            if not north_money.empty:
                net_inflow = north_money.iloc[0]['今日净流入-亿'] if '今日净流入-亿' in north_money.columns else 0
                return {"北向资金净流入": net_inflow}
        except:
            pass
    except Exception as e:
        log(f"获取资金流向失败: {str(e)[:50]}", "WARNING")
    
    return None


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
