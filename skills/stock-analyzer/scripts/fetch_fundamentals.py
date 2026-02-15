#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报数据定期获取任务
====================
每周获取财报数据用于长期基本面分析

使用方法:
    python3 fetch_fundamentals.py

计划任务 (cron):
    0 9 * * 1  # 每周一 9:00 执行

作者: OpenClaw Quant Team
版本: 1.0.0
"""

import akshare as ak
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')


# 配置
DATA_DIR = Path("/home/liujerry/金融数据/fundamentals")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_stock_spot():
    """获取实时行情 (PE, PB, 市值)"""
    print("📊 获取实时行情...")
    try:
        df = ak.stock_zh_a_spot()
        df.to_csv(DATA_DIR / "stock_spot.csv", index=False)
        print(f"   ✅ 保存 stock_spot.csv ({len(df)} 只)")
        return df
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None


def get_market_valuation():
    """获取全市场估值数据"""
    print("📊 获取全市场估值...")
    try:
        df = ak.stock_a_all_pb()
        df.to_csv(DATA_DIR / "market_valuation.csv", index=False)
        print(f"   ✅ 保存 market_valuation.csv")
        return df
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None


def get_blue_chip_data():
    """获取蓝筹股基本面数据"""
    BLUE_CHIP = [
        ("600000", "浦发银行"), ("600016", "民生银行"), ("600019", "宝钢股份"),
        ("600028", "中国石化"), ("600030", "中信证券"), ("600036", "招商银行"),
        ("600050", "中国联通"), ("600104", "上汽集团"), ("600111", "北方稀土"),
        ("600170", "上海建工"), ("600176", "中国巨石"), ("600177", "雅戈尔"),
        ("600183", "生益科技"), ("600188", "兖州煤业"), ("600196", "复星医药"),
        ("600208", "新湖中宝"), ("600219", "阳光电源"), ("600221", "海航创新"),
    ]
    
    print("📊 获取蓝筹股基本面...")
    results = []
    
    for code, name in BLUE_CHIP:
        try:
            spot = ak.stock_zh_a_spot()
            stock = spot[spot['代码'] == code]
            
            if not stock.empty:
                data = {
                    "code": code,
                    "name": name,
                    "price": float(stock['最新价'].values[0]),
                    "change_pct": float(stock['涨跌幅'].values[0]),
                    "pe": float(stock['市盈率-动态'].values[0]) if '市盈率-动态' in stock.columns else None,
                    "pb": float(stock['市净率'].values[0]) if '市净率' in stock.columns else None,
                    "market_cap": float(stock['总市值'].values[0]) if '总市值' in stock.columns else None,
                    "pe_ratio": float(stock['市盈率-动态'].values[0]) if '市盈率-动态' in stock.columns else None,
                }
                results.append(data)
                time.sleep(0.2)
                
        except Exception as e:
            print(f"   ❌ {code}: {e}")
            continue
    
    # 保存
    with open(DATA_DIR / "blue_chip_fundamentals.json", 'w', encoding='utf-8') as f:
        json.dump({
            "update_time": datetime.now().isoformat(),
            "stocks": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 保存 blue_chip_fundamentals.json ({len(results)} 只)")
    return results


def get_chuangye_data():
    """获取创业板基本面数据"""
    CHUANGYE = [
        ("300001", "特锐德"), ("300015", "爱尔眼科"), ("300017", "网宿科技"),
        ("300024", "机器人"), ("300033", "同花顺"), ("300059", "东方财富"),
        ("300068", "南都电源"), ("300072", "宁波长策"), ("300073", "当升科技"),
        ("300076", "维宏股份"), ("300077", "国民技术"), ("300098", "高新兴"),
    ]
    
    print("📊 获取创业板基本面...")
    results = []
    
    for code, name in CHUANGYE:
        try:
            spot = ak.stock_zh_a_spot()
            stock = spot[spot['代码'] == code]
            
            if not stock.empty:
                data = {
                    "code": code,
                    "name": name,
                    "price": float(stock['最新价'].values[0]),
                    "change_pct": float(stock['涨跌幅'].values[0]),
                    "pe": float(stock['市盈率-动态'].values[0]) if '市盈率-动态' in stock.columns else None,
                    "pb": float(stock['市净率'].values[0]) if '市净率' in stock.columns else None,
                }
                results.append(data)
                time.sleep(0.2)
                
        except Exception as e:
            print(f"   ❌ {code}: {e}")
            continue
    
    with open(DATA_DIR / "chuangye_fundamentals.json", 'w', encoding='utf-8') as f:
        json.dump({
            "update_time": datetime.now().isoformat(),
            "stocks": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 保存 chuangye_fundamentals.json ({len(results)} 只)")
    return results


def analyze_fundamentals():
    """分析基本面"""
    print("\n📊 分析基本面...")
    
    try:
        # 读取数据
        with open(DATA_DIR / "blue_chip_fundamentals.json", 'r', encoding='utf-8') as f:
            blue_data = json.load(f)
        
        with open(DATA_DIR / "chuangye_fundamentals.json", 'r', encoding='utf-8') as f:
            chuangye_data = json.load(f)
        
        # 分析
        all_stocks = []
        
        for stock in blue_data.get('stocks', []):
            pe = stock.get('pe', 0) or 0
            pb = stock.get('pb', 0) or 0
            
            # 估值得分
            val_score = 100
            if pe and pe > 0:
                if pe > 50: val_score -= 50
                elif pe > 30: val_score -= 30
                elif pe > 15: val_score -= 10
            
            if pb and pb > 0:
                if pb > 10: val_score -= 30
                elif pb > 5: val_score -= 15
                elif pb > 2: val_score -= 5
            
            stock['valuation_score'] = max(0, val_score)
            stock['type'] = '蓝筹'
            all_stocks.append(stock)
        
        for stock in chuangye_data.get('stocks', []):
            pe = stock.get('pe', 0) or 0
            pb = stock.get('pb', 0) or 0
            
            val_score = 100
            if pe and pe > 0:
                if pe > 100: val_score -= 50
                elif pe > 50: val_score -= 30
                elif pe > 25: val_score -= 10
            
            stock['valuation_score'] = max(0, val_score)
            stock['type'] = '创业板'
            all_stocks.append(stock)
        
        # 按估值得分排序
        all_stocks.sort(key=lambda x: x.get('valuation_score', 0), reverse=True)
        
        # 保存
        analysis = {
            "update_time": datetime.now().isoformat(),
            "analysis": all_stocks[:50],
            "summary": {
                "total_stocks": len(all_stocks),
                "blue_chip_count": len(blue_data.get('stocks', [])),
                "chuangye_count": len(chuangye_data.get('stocks', [])),
            }
        }
        
        with open(DATA_DIR / "fundamental_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 保存 fundamental_analysis.json")
        
        # 输出 Top 10
        print("\n   Top 10 低估值股票:")
        for i, s in enumerate(all_stocks[:10]):
            print(f"   {i+1}. {s['name']} ({s['type']}): PE={s['pe']}, PB={s['pb']}, 估值得分={s['valuation_score']}")
        
        return analysis
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None


def run():
    """运行任务"""
    print("\n" + "="*60)
    print("📅 财报数据定期获取任务")
    print(f"⏰ 执行时间: {datetime.now().isoformat()}")
    print("="*60 + "\n")
    
    get_stock_spot()
    get_market_valuation()
    get_blue_chip_data()
    get_chuangye_data()
    analyze_fundamentals()
    
    print("\n" + "="*60)
    print("✅ 任务完成!")
    print("="*60)


if __name__ == "__main__":
    run()
