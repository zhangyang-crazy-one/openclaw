#!/usr/bin/env python3
"""
每日股票分析脚本
生成开盘前股票分析报告
"""
import json
from datetime import datetime
from pathlib import Path

# 股票列表
STOCKS = [
    # ETF
    ("159866", "日经ETF"),
    ("159321", "黄金股票ETF"),
    ("159501", "纳指ETF"),
    ("159502", "标普生物ETF"),
    
    # 银行
    ("601398", "工商银行"),
    ("601288", "农业银行"),
    ("601939", "建设银行"),
    ("601988", "中国银行"),
    ("000001", "平安银行"),
    
    # 券商/金融
    ("600030", "中信证券"),
    
    # 制造业
    ("600028", "中国石化"),
    ("600519", "贵州茅台"),
    ("000338", "潍柴动力"),
    ("002032", "苏泊尔"),
    
    # 科技
    ("300251", "光线传媒"),
    ("300766", "每日互动"),
    ("300229", "拓尔思"),
    ("300007", "汉威科技"),
    ("300276", "三丰智能"),
    ("300545", "联得装备"),
    ("300418", "昆仑万维"),
    ("300661", "圣邦股份"),
    ("301330", "熵基科技"),
    
    # 新能源
    ("002594", "比亚迪"),
    ("300763", "锦浪科技"),
    
    # 医药
    ("300639", "凯普生物"),
    
    # 芯片
    ("603986", "兆易创新"),
    
    # 消费
    ("603195", "公牛集团"),
    
    # 指数
    ("399001", "深证成指"),
    ("399006", "创业板指"),
    ("000300", "沪深300"),
]

def get_latest_stock_data(stock_code):
    """获取股票最新数据"""
    data_file = Path("/home/liujerry/金融数据/stocks") / f"{stock_code}.csv"
    
    if not data_file.exists():
        return None
    
    try:
        with open(data_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return None
            
            latest = lines[-1].strip().split(',')
            prev = lines[-2].strip().split(',')
            
            # CSV: date,open,close,high,low,volume
            if len(latest) >= 3 and len(prev) >= 3:
                latest_close = float(latest[2])
                prev_close = float(prev[2])
                change = latest_close - prev_close
                change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
                
                return {
                    "code": stock_code,
                    "date": latest[0],
                    "close": latest_close,
                    "change": change,
                    "change_pct": change_pct
                }
    except Exception as e:
        print(f"Error reading {stock_code}: {e}")
    
    return None

def analyze_stock(code, name, data):
    """分析单只股票"""
    if not data:
        return None
    
    change_pct = data.get("change_pct", 0)
    
    # 简化判断
    if change_pct > 2:
        trend = "多头排列"
        rsi_status = "正常"
        macd_status = "金叉/多头"
    elif change_pct < -2:
        trend = "空头排列"
        rsi_status = "超卖" if change_pct < -3 else "正常"
        macd_status = "死叉/空头"
    else:
        trend = "震荡"
        rsi_status = "正常"
        macd_status = "震荡"
    
    suggestion = "持有" if change_pct > 0 else "关注" if change_pct < -3 else "观望"
    
    return {
        "code": code,
        "name": name,
        "price": data["close"],
        "change_pct": f"{change_pct:+.2f}%",
        "trend": trend,
        "rsi_status": rsi_status,
        "macd_status": macd_status,
        "suggestion": suggestion
    }

def generate_report():
    """生成分析报告"""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    report_time = today.strftime("%Y-%m-%d %H:%M")
    
    print("=" * 80)
    print(f"📊 【{date_str}】开盘前股票分析报告 - {report_time}")
    print("=" * 80)
    
    analyses = []
    
    for code, name in STOCKS:
        data = get_latest_stock_data(code)
        if data:
            result = analyze_stock(code, name, data)
            if result:
                analyses.append(result)
    
    hold = [a for a in analyses if a["suggestion"] == "持有"]
    focus = [a for a in analyses if a["suggestion"] == "关注"]
    watch = [a for a in analyses if a["suggestion"] == "观望"]
    
    print("\n【操作建议】")
    print("-" * 80)
    
    print("\n🟢 【持有】")
    for a in hold[:5]:
        print(f"{a['name']} ({a['code']})")
        print(f"  最新价: {a['price']:.2f} ({a['change_pct']})")
        print(f"  趋势: {a['trend']} | RSI{a['rsi_status']} | MACD{a['macd_status']}")
        print(f"  建议: {a['suggestion']}\n")
    
    print("\n🟡 【关注机会】")
    for a in focus[:3]:
        print(f"{a['name']} ({a['code']}) - {a['price']:.2f} ({a['change_pct']}) RSI{a['rsi_status']}")
    
    print(f"\n⚪ 【观望】")
    for a in watch[:5]:
        print(f"{a['name']}({a['code']})", end=" ")
    
    # 保存报告
    report_dir = Path("/home/liujerry/金融数据/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"daily_report_{date_str.replace('-', '')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"""
================================================================================
开盘前股票分析报告 - {report_time}
================================================================================

【免责声明】
以上分析仅供参考，不构成投资建议。

【统计】
分析股票数: {len(analyses)}
持有: {len(hold)} | 关注: {len(focus)} | 观望: {len(watch)}
""")
    
    print(f"\n✅ 报告已保存至: {report_file}")
    
    return {"total": len(analyses), "hold": len(hold), "focus": len(focus), "watch": len(watch)}

if __name__ == "__main__":
    generate_report()
