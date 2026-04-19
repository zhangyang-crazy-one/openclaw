#!/usr/bin/env python3
"""
A股数据清洗脚本
根据 2026-02-13 清洗标准重建

清洗标准:
1. 必须有指定基准日期的数据
2. 必要列完整 (date, open, high, low, close, volume)
3. 无负价格、无极端波动 (±10σ)
4. 至少500条数据
5. 去重、日期升序排列

使用方法:
    python3 stock_data_cleaner.py                    # 全量清洗
    python3 stock_data_cleaner.py --date 2026-02-06   # 指定基准日期
    python3 stock_data_cleaner.py --board chuangye   # 只清洗创业板
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# 配置
STOCKS_DIR = Path("/home/liujerry/金融数据/stocks")
OUTPUT_DIR = Path("/home/liujerry/金融数据")

# 清洗后的数据目录（输入源，因为有完整历史数据）
# stocks/ = 增量更新（只有近2年）
# stocks_clean*/ = 原始完整历史数据（用于清洗）
BOARD_CLEAN_INPUT = {
    "chuangye": Path("/home/liujerry/金融数据/stocks_clean"),       # 创业板
    "main": Path("/home/liujerry/金融数据/stocks_clean_main"),      # 主板
    "sme": Path("/home/liujerry/金融数据/stocks_clean_sme"),        # 中小板
    "star": Path("/home/liujerry/金融数据/stocks_clean_star"),       # 科创板
}

# 板块配置
BOARD_CONFIG = {
    "chuangye": {
        "name": "创业板",
        "prefix": ("300",),
        "output": OUTPUT_DIR / "stocks_clean",
        "clean_stats_key": "chuangye"
    },
    "main": {
        "name": "主板A股",
        "prefix": ("600", "601", "603"),
        "output": OUTPUT_DIR / "stocks_clean_main",
        "clean_stats_key": "main"
    },
    "sme": {
        "name": "中小板",
        "prefix": ("002",),
        "output": OUTPUT_DIR / "stocks_clean_sme",
        "clean_stats_key": "sme"
    },
    "star": {
        "name": "科创板",
        "prefix": ("688",),
        "output": OUTPUT_DIR / "stocks_clean_star",
        "clean_stats_key": "star"
    },
    "all": {
        "name": "全部",
        "prefix": ("300", "600", "601", "603", "002", "688"),
        "output": None,  # 不输出，用于统计
        "clean_stats_key": "all"
    }
}

# 清洗参数
MIN_DATA_POINTS = 500
VOLATILITY_SIGMA = 10.0  # ±10σ 极端波动阈值
REQUIRED_COLS = ["date", "open", "high", "low", "close", "volume"]


def get_board(code: str) -> Optional[str]:
    """根据代码判断板块"""
    if code.startswith("300"):
        return "chuangye"
    elif code.startswith(("600", "601", "603")):
        return "main"
    elif code.startswith("002"):
        return "sme"
    elif code.startswith("688"):
        return "star"
    return None


def validate_csv(csv_path: Path, reference_date: str) -> dict:
    """
    验证单个股票CSV文件
    
    返回:
        {
            "valid": bool,
            "reason": str,
            "rows": int,
            "date_range": tuple,
            "issues": list
        }
    """
    if not csv_path.exists():
        return {"valid": False, "reason": "文件不存在", "rows": 0, "date_range": None, "issues": ["文件不存在"]}
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        issues = []
        
        # 1. 检查必要列
        missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
        if missing_cols:
            return {
                "valid": False,
                "reason": f"缺少列: {missing_cols}",
                "rows": len(df),
                "date_range": None,
                "issues": [f"缺少列: {missing_cols}"]
            }
        
        # 2. 数据点数检查
        if len(df) < MIN_DATA_POINTS:
            return {
                "valid": False,
                "reason": f"数据不足{MIN_DATA_POINTS}条",
                "rows": len(df),
                "date_range": None,
                "issues": [f"数据不足: {len(df)} < {MIN_DATA_POINTS}"]
            }
        
        # 3. 检查基准日期是否有数据
        if reference_date:
            dates = df["date"].astype(str).tolist()
            if reference_date not in dates:
                return {
                    "valid": False,
                    "reason": f"基准日期{reference_date}无数据",
                    "rows": len(df),
                    "date_range": None,
                    "issues": [f"基准日期无数据: {reference_date}"]
                }
        
        # 4. 检查负价格
        numeric_cols = ["open", "high", "low", "close"]
        for col in numeric_cols:
            if (df[col] < 0).any():
                neg_count = (df[col] < 0).sum()
                return {
                    "valid": False,
                    "reason": f"{col}列有{neg_count}个负值",
                    "rows": len(df),
                    "date_range": None,
                    "issues": [f"{col}列有负值: {neg_count}个"]
                }
        
        # 5. 检查极端波动 (±10σ)
        if "close" in df.columns and len(df) > 20:
            returns = df["close"].pct_change().dropna()
            if len(returns) > 0:
                mean_ret = returns.mean()
                std_ret = returns.std()
                if std_ret > 0:
                    lower = mean_ret - VOLATILITY_SIGMA * std_ret
                    upper = mean_ret + VOLATILITY_SIGMA * std_ret
                    extreme_returns = returns[(returns < lower) | (returns > upper)]
                    if len(extreme_returns) > len(returns) * 0.05:  # 超过5%的极端值
                        return {
                            "valid": False,
                            "reason": f"极端波动过多: {len(extreme_returns)}个(>{len(returns)*0.05:.0f})",
                            "rows": len(df),
                            "date_range": None,
                            "issues": [f"极端波动过多: {len(extreme_returns)}个"]
                        }
        
        # 6. 检查日期范围
        try:
            df["date_dt"] = pd.to_datetime(df["date"])
            date_range = (df["date_dt"].min().strftime("%Y-%m-%d"), df["date_dt"].max().strftime("%Y-%m-%d"))
        except:
            date_range = None
        
        return {
            "valid": True,
            "reason": "通过",
            "rows": len(df),
            "date_range": date_range,
            "issues": []
        }
    
    except Exception as e:
        return {
            "valid": False,
            "reason": f"解析错误: {str(e)[:50]}",
            "rows": 0,
            "date_range": None,
            "issues": [f"解析错误: {str(e)[:50]}"]
        }


def clean_stock(csv_path: Path) -> Optional[list]:
    """
    清洗单个股票CSV: 去重、排序
    
    返回清洗后的数据行列表，失败返回None
    """
    try:
        import pandas as pd
        
        df = pd.read_csv(csv_path)
        
        # 1. 转换日期
        df["_date_dt"] = pd.to_datetime(df["date"], errors="coerce")
        
        # 2. 移除无效日期
        df = df.dropna(subset=["_date_dt"])
        
        # 3. 去重（同一日期保留最后一条）
        df = df.drop_duplicates(subset=["date"], keep="last")
        
        # 4. 按日期升序排列
        df = df.sort_values("_date_dt")
        
        # 5. 删除辅助列
        df = df.drop(columns=["_date_dt"])
        
        return df.to_dict("records")
    
    except Exception as e:
        return None


def process_board(board_key: str, reference_date: str, dry_run: bool = False) -> dict:
    """处理指定板块"""
    config = BOARD_CONFIG[board_key]
    output_dir = config["output"]
    
    print(f"\n{'='*60}")
    print(f"板块: {config['name']} ({board_key})")
    print(f"基准日期: {reference_date}")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}")
    
    # 统计
    stats = {
        "board": config["name"],
        "board_key": board_key,
        "reference_date": reference_date,
        "total_checked": 0,
        "total_valid": 0,
        "total_invalid": 0,
        "total_rows_min": float("inf"),
        "total_rows_max": 0,
        "total_rows_sum": 0,
        "invalid_reasons": {},
        "valid_codes": [],
        "invalid_codes": []
    }
    
    # 获取所有CSV文件（从清洗后的数据目录读取）
    input_dir = BOARD_CLEAN_INPUT.get(board_key, output_dir)
    if not input_dir or not input_dir.exists():
        print(f"错误: 输入目录不存在: {input_dir}")
        return stats
    
    all_csvs = list(input_dir.glob("*.csv"))
    # 排除非CSV文件
    all_csvs = [f for f in all_csvs if f.suffix == ".csv" and f.stem not in ["clean_stats", "valid_stocks"]]
    print(f"股票总数: {len(all_csvs)}")
    
    for csv_path in sorted(all_csvs):
        code = csv_path.stem
        
        # 检查是否属于该板块
        board = get_board(code)
        if board != board_key:
            continue
        
        stats["total_checked"] += 1
        
        # 验证
        validation = validate_csv(csv_path, reference_date)
        
        if validation["valid"]:
            stats["total_valid"] += 1
            stats["valid_codes"].append(code)
            stats["total_rows_min"] = min(stats["total_rows_min"], validation["rows"])
            stats["total_rows_max"] = max(stats["total_rows_max"], validation["rows"])
            stats["total_rows_sum"] += validation["rows"]
            
            if not dry_run and output_dir:
                # 清洗并写入
                cleaned_data = clean_stock(csv_path)
                if cleaned_data is not None:
                    output_path = output_dir / csv_path.name
                    import pandas as pd
                    df_clean = pd.DataFrame(cleaned_data)
                    # 确保列顺序
                    df_clean = df_clean[REQUIRED_COLS]
                    df_clean.to_csv(output_path, index=False)
        else:
            stats["total_invalid"] += 1
            stats["invalid_codes"].append(code)
            reason = validation["reason"]
            stats["invalid_reasons"][reason] = stats["invalid_reasons"].get(reason, 0) + 1
    
    # 计算平均值
    if stats["total_valid"] > 0:
        stats["total_rows_avg"] = stats["total_rows_sum"] / stats["total_valid"]
    else:
        stats["total_rows_avg"] = 0
        stats["total_rows_min"] = 0
    
    # 打印结果
    print(f"\n检查: {stats['total_checked']} 只")
    print(f"通过: {stats['total_valid']} 只")
    print(f"失败: {stats['total_invalid']} 只")
    
    if stats["total_valid"] > 0:
        print(f"数据量: 最小{stats['total_rows_min']}, 最大{stats['total_rows_max']}, 平均{stats['total_rows_avg']:.1f}")
    
    if stats["invalid_reasons"]:
        print(f"\n失败原因分布:")
        for reason, count in sorted(stats["invalid_reasons"].items(), key=lambda x: -x[1]):
            print(f"  {reason}: {count}")
    
    # 保存结果
    if not dry_run and output_dir:
        # 保存 valid_stocks.txt
        valid_file = output_dir / "valid_stocks.txt"
        with open(valid_file, "w") as f:
            for code in sorted(stats["valid_codes"]):
                f.write(f"{code}\n")
        print(f"\n有效股票列表: {valid_file} ({stats['total_valid']}只)")
        
        # 保存 clean_stats.json
        clean_stats = {
            "total_stocks": stats["total_valid"],
            "valid_date": reference_date,
            "min_rows": int(stats["total_rows_min"]) if stats["total_rows_min"] != float("inf") else 0,
            "max_rows": int(stats["total_rows_max"]),
            "avg_rows": round(stats["total_rows_avg"], 2)
        }
        stats_file = output_dir / "clean_stats.json"
        with open(stats_file, "w") as f:
            json.dump(clean_stats, f, indent=2, ensure_ascii=False)
        print(f"清洗统计: {stats_file}")
        print(f"清洗后文件数: {len(list(output_dir.glob('*.csv')))}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="A股数据清洗脚本")
    parser.add_argument("--date", type=str, default="2026-02-06", help="基准日期 (默认: 2026-02-06)")
    parser.add_argument("--board", type=str, default="all", 
                        choices=list(BOARD_CONFIG.keys()),
                        help="板块 (默认: all)")
    parser.add_argument("--dry-run", action="store_true", help="仅验证，不写入文件")
    parser.add_argument("--min-rows", type=int, default=500, help=f"最小数据点数 (默认: 500)")
    
    args = parser.parse_args()
    
    global MIN_DATA_POINTS
    MIN_DATA_POINTS = args.min_rows
    
    reference_date = args.date
    board_key = args.board
    
    print(f"=== A股数据清洗 ===")
    print(f"基准日期: {reference_date}")
    print(f"板块: {BOARD_CONFIG[board_key]['name']}")
    print(f"最小数据点: {MIN_DATA_POINTS}")
    print(f"极端波动阈值: ±{VOLATILITY_SIGMA}σ")
    print(f"模式: {'干运行' if args.dry_run else '正式运行'}")
    
    if board_key == "all":
        # 全量清洗所有板块
        all_stats = {}
        for key in ["chuangye", "main", "sme", "star"]:
            stats = process_board(key, reference_date, args.dry_run)
            all_stats[key] = stats
        
        # 汇总
        print(f"\n{'='*60}")
        print("=== 全量清洗汇总 ===")
        total_valid = sum(s["total_valid"] for s in all_stats.values())
        total_invalid = sum(s["total_invalid"] for s in all_stats.values())
        print(f"总计: 检查 {sum(s['total_checked'] for s in all_stats.values())} 只")
        print(f"通过: {total_valid} 只")
        print(f"失败: {total_invalid} 只")
        
        # 更新总 clean_stats.json
        if not args.dry_run:
            total_stats = {
                "total_stocks": total_valid,
                "valid_date": reference_date,
                "min_rows": min(s["total_rows_min"] for s in all_stats.values() if s["total_rows_min"] > 0),
                "max_rows": max(s["total_rows_max"] for s in all_stats.values()),
                "avg_rows": round(sum(s["total_rows_avg"] * s["total_valid"] for s in all_stats.values()) / total_valid, 2) if total_valid > 0 else 0,
                "by_board": {
                    key: {
                        "total": stats["total_valid"],
                        "min_rows": int(stats["total_rows_min"]) if stats["total_rows_min"] != float("inf") else 0,
                        "max_rows": int(stats["total_rows_max"]),
                        "avg_rows": round(stats["total_rows_avg"], 2)
                    }
                    for key, stats in all_stats.items()
                }
            }
            with open(OUTPUT_DIR / "stocks_clean" / "clean_stats.json", "w") as f:
                json.dump(total_stats, f, indent=2, ensure_ascii=False)
    else:
        stats = process_board(board_key, reference_date, args.dry_run)
    
    print(f"\n完成!")


if __name__ == "__main__":
    main()
