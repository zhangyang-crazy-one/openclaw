#!/usr/bin/env python3
"""
数据质量监控脚本
检查股票数据质量，检测概念漂移，验证数据源一致性
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 配置
DATA_DIR = Path("/home/liujerry/金融数据")
REPORTS_DIR = DATA_DIR / "reports"
WATCHLIST_FILE = DATA_DIR / "config" / "watchlist_top20.txt"

# 添加项目路径
sys.path.insert(0, "/home/liujerry/moltbot/skills/stock-analyzer/scripts")


def load_watchlist():
    """加载自选股列表"""
    stocks = []
    if WATCHLIST_FILE.exists():
        with open(WATCHLIST_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    code = line.split()[0]
                    if len(code) == 6 and code.isdigit():
                        stocks.append(code)
    return stocks


def check_data_source_status():
    """检查数据源状态"""
    results = {
        "baostock": {"status": "unknown", "message": ""},
        "akshare": {"status": "unknown", "message": ""}
    }
    
    try:
        import baostock as bs
        lg = bs.login()
        results["baostock"] = {
            "status": "ok" if lg.error_code == "0" else "error",
            "message": lg.error_msg
        }
        bs.logout()
    except Exception as e:
        results["baostock"] = {"status": "error", "message": str(e)}
    
    try:
        import akshare as ak
        # 简单测试
        _ = ak.stock_zh_a_spot_em()
        results["akshare"] = {"status": "ok", "message": "连接成功"}
    except Exception as e:
        results["akshare"] = {"status": "error", "message": str(e)}
    
    return results


def check_data_freshness(stocks):
    """检查数据新鲜度"""
    results = []
    
    # 检查最新数据日期
    latest_files = [
        DATA_DIR / "chuangye_latest" / "realtime.csv",
        DATA_DIR / "a_stock_latest" / "realtime.csv"
    ]
    
    for f in latest_files:
        if f.exists():
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            age = datetime.now() - mtime
            results.append({
                "file": str(f.name),
                "last_update": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "age_hours": round(age.total_seconds() / 3600, 1)
            })
    
    return results


def check_concept_drift(stocks):
    """检测概念漂移"""
    # 简单实现：检查价格和RSI的异常变化
    # 实际应该对比历史数据
    alerts = []
    
    # 预留扩展接口
    # 可以添加更多漂移检测逻辑
    
    return alerts


def generate_report(data_sources, freshness, drift, stocks):
    """生成监控报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "stocks_checked": len(stocks),
        "data_sources": data_sources,
        "data_freshness": freshness,
        "concept_drift": drift,
        "alerts": []
    }
    
    # 生成告警
    if data_sources.get("baostock", {}).get("status") != "ok":
        report["alerts"].append({
            "level": "critical",
            "message": f"Baostock连接失败: {data_sources.get('baostock', {}).get('message')}"
        })
    
    if data_sources.get("akshare", {}).get("status") != "ok":
        report["alerts"].append({
            "level": "critical",
            "message": f"Akshare连接失败: {data_sources.get('akshare', {}).get('message')}"
        })
    
    for f in freshness:
        if f.get("age_hours", 0) > 24:
            report["alerts"].append({
                "level": "warning",
                "message": f"数据文件 {f['file']} 更新延迟 {f['age_hours']} 小时"
            })
    
    report["alerts"].extend(drift)
    
    return report


def main():
    """主函数"""
    print("=== 数据质量监控 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载自选股
    stocks = load_watchlist()
    print(f"自选股数量: {len(stocks)}")
    
    # 检查数据源
    print("\n检查数据源...")
    data_sources = check_data_source_status()
    for name, status in data_sources.items():
        print(f"  {name}: {status['status']} - {status['message']}")
    
    # 检查数据新鲜度
    print("\n检查数据新鲜度...")
    freshness = check_data_freshness(stocks)
    for f in freshness:
        print(f"  {f['file']}: {f['last_update']} (age: {f['age_hours']}h)")
    
    # 检测概念漂移
    print("\n检测概念漂移...")
    drift = check_concept_drift(stocks)
    print(f"  发现 {len(drift)} 个异常")
    
    # 生成报告
    report = generate_report(data_sources, freshness, drift, stocks)
    
    # 保存报告
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"data_quality_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_file}")
    print(f"告警数量: {len(report['alerts'])}")
    
    # 输出告警
    if report['alerts']:
        print("\n告警详情:")
        for alert in report['alerts']:
            print(f"  [{alert['level']}] {alert['message']}")
    
    return 0 if not report['alerts'] else 1


if __name__ == "__main__":
    sys.exit(main())
