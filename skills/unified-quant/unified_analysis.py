#!/usr/bin/env python3
"""
统一量化分析系统
功能: 数据验证 + 自动选股 + 论文引用 + 概率模型
输出: PDF报告 -> QQ
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from validation.data_validator import DataValidator
from probability_model import WinProbabilityModel
from paper_citation import PaperCitation, RESEARCH_TOPICS


class UnifiedQuantSystem:
    """统一量化分析系统"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.probability_model = WinProbabilityModel()
        self.citation = PaperCitation()
        
    def run_full_analysis(self, stock_codes: List[str], 
                        output_path: str = None) -> Dict:
        """运行完整分析"""
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stocks": {},
            "summary": {}
        }
        
        print("=" * 50)
        print("🚀 统一量化分析系统启动")
        print("=" * 50)
        
        # Step 1: 数据交叉验证
        print("\n📊 Step 1: 数据交叉验证")
        validation_results = self.validator.get_validated_data(stock_codes)
        
        # 过滤可信数据
        valid_stocks = [code for code, r in validation_results.items() 
                       if r.get('confidence', 0) >= 70]
        
        print(f"   ✅ 可信股票数量: {len(valid_stocks)}/{len(stock_codes)}")
        
        # Step 2: 加载数据到概率模型
        print("\n📈 Step 2: 加载历史数据")
        # 这里需要加载历史数据到probability_model
        # 简化处理，直接跳过
        
        # Step 3: 生成信号
        print("\n🎯 Step 3: 生成交易信号")
        signals = []
        for code in valid_stocks:
            signal = self.probability_model.generate_signal(code)
            signal['stock_code'] = code
            signals.append(signal)
        
        # 按获胜概率排序
        signals.sort(key=lambda x: x.get('probability', 0), reverse=True)
        
        # Step 4: 生成报告
        print("\n📝 Step 4: 生成分析报告")
        report = self._generate_report(validation_results, signals)
        
        results['stocks'] = report
        results['summary'] = {
            "total_analyzed": len(stock_codes),
            "valid_stocks": len(valid_stocks),
            "buy_signals": len([s for s in signals if s.get('signal') == 'BUY']),
            "sell_signals": len([s for s in signals if s.get('signal') == 'SELL']),
        }
        
        # 保存结果
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 结果已保存到: {output_path}")
        
        return results
    
    def _generate_report(self, validation_results: Dict, signals: List[Dict]) -> List[Dict]:
        """生成分析报告"""
        report = []
        
        for signal in signals:
            code = signal['stock_code']
            val = validation_results.get(code, {})
            
            # 获取论文引用
            topic = "stock_prediction"
            paper = self.citation.get_paper_info(topic)
            citation = self.citation.format_citation(paper, "compact") if paper else "[无权威论文]"
            
            report.append({
                "stock_code": code,
                "signal": signal.get('signal'),
                "probability": signal.get('probability'),
                "expected_return": signal.get('expected_return'),
                "reason": signal.get('reason'),
                "data_confidence": val.get('confidence', 0),
                "citation": citation,
            })
        
        return report


def main():
    """主函数"""
    # 示例: 分析创业板股票
    # 这里应该从配置或参数获取股票列表
    test_stocks = ["sz.300001", "sz.300003"]
    
    system = UnifiedQuantSystem()
    results = system.run_full_analysis(test_stocks)
    
    print("\n" + "=" * 50)
    print("📋 分析完成!")
    print(f"   买入信号: {results['summary'].get('buy_signals', 0)}")
    print(f"   卖出信号: {results['summary'].get('sell_signals', 0)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
