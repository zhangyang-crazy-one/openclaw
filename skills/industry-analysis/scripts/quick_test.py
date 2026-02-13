#!/usr/bin/env python3
"""
行业分析 - 快速测试脚本
"""
import sys
from pathlib import Path

# 添加技能路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from industry_analysis import IndustryAnalyzer, DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR

def quick_test():
    """快速测试"""
    print("="*60)
    print("行业分析技能 - 快速测试")
    print("="*60)
    
    # 初始化
    analyzer = IndustryAnalyzer(
        data_dir=DEFAULT_DATA_DIR,
        output_dir=DEFAULT_OUTPUT_DIR
    )
    
    # 获取部分股票代码
    stock_files = list(DEFAULT_DATA_DIR.glob("300*.csv"))[:100]
    stock_codes = [f.stem for f in stock_files]
    
    print(f"\n分析 {len(stock_codes)} 只股票...")
    
    # 分析
    results = analyzer.analyze_industry(stock_codes)
    print(f"完成 {len(results)} 只股票分析")
    
    # TOP 10
    print("\n" + "="*60)
    print("TOP 10 股票评分")
    print("="*60)
    
    top_10 = analyzer.get_top_industries(10)
    for i, stock in enumerate(top_10, 1):
        print(f"{i:2d}. {stock['code']}: 综合={stock['composite_score']:.1f}")
    
    # 轮动信号
    print("\n" + "="*60)
    print("轮动信号")
    print("="*60)
    
    analyzer.generate_rotation_signals()
    signals = analyzer.rotation_signals
    
    signal_counts = {}
    for signal in signals.values():
        signal_counts[signal] = signal_counts.get(signal, 0) + 1
    
    for signal, count in sorted(signal_counts.items(), key=lambda x: -x[1]):
        print(f"  {signal}: {count}只")
    
    # 保存
    output = analyzer.save_results()
    print(f"\n结果已保存: {output}")
    
    return results

if __name__ == "__main__":
    quick_test()
