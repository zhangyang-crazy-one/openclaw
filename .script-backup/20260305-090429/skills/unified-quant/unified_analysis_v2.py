#!/usr/bin/env python3
"""
统一量化分析系统 v2.0
功能: 数据验证 + 自动选股 + 论文引用 + 概率模型 + PDF报告 + QQ发送
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from validation.data_validator import DataValidator
from probability_model import WinProbabilityModel
from paper_citation import PaperCitation, RESEARCH_TOPICS
from report_generator import ReportGenerator


class UnifiedQuantSystem:
    """统一量化分析系统 v2.0"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.probability_model = WinProbabilityModel()
        self.citation = PaperCitation()
        self.report_generator = ReportGenerator()
        
    def run_full_analysis(self, stock_codes: list, 
                        output_path: str = None,
                        send_to_qq: bool = True) -> dict:
        """运行完整分析"""
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "2.0",
            "validation": {},
            "signals": [],
            "summary": {}
        }
        
        print("=" * 60)
        print("🚀 统一量化分析系统 v2.0")
        print("=" * 60)
        
        # Step 1: 数据交叉验证
        print("\n📊 Step 1: 数据交叉验证 (Baostock ↔ Akshare)")
        validation_results = {}
        
        for code in stock_codes:
            print(f"   验证 {code}...", end=" ")
            try:
                val_result = self.validator.cross_validate(code)
                validation_results[code] = val_result
                confidence = val_result.get('confidence', 0)
                status = "✅" if confidence >= 70 else "⚠️"
                print(f"置信度 {confidence}% {status}")
            except Exception as e:
                print(f"错误: {e}")
                validation_results[code] = {"confidence": 0, "error": str(e)}
        
        results["validation"] = validation_results
        
        # 过滤可信股票
        valid_stocks = [code for code, r in validation_results.items() 
                      if r.get('confidence', 0) >= 70]
        
        print(f"\n   ✅ 可信股票: {len(valid_stocks)}/{len(stock_codes)}")
        
        # Step 2: 生成交易信号
        print("\n🎯 Step 2: 生成交易信号")
        
        # 加载论文引用
        paper_citations = {}
        for topic, papers in RESEARCH_TOPICS.items():
            if papers:
                paper = self.citation.get_paper_info(papers[0]['topic'])
                paper_citations[topic] = self.citation.format_citation(paper, "compact") if paper else "[无引用]"
        
        for code in valid_stocks:
            print(f"   分析 {code}...", end=" ")
            try:
                signal = self.probability_model.generate_signal(code)
                
                # 添加论文引用
                citation = paper_citations.get('stock_prediction', '[无引用]')
                
                results["signals"].append({
                    "stock_code": code,
                    "signal": signal.get('signal', 'HOLD'),
                    "probability": signal.get('probability', 0),
                    "expected_return": signal.get('expected_return', 0),
                    "reason": signal.get('reason', ''),
                    "strategy": signal.get('strategy', ''),
                    "citation": citation,
                })
                print(f"信号: {signal.get('signal', 'HOLD')}")
            except Exception as e:
                print(f"错误: {e}")
        
        # 按概率排序
        results["signals"].sort(key=lambda x: x.get('probability', 0), reverse=True)
        
        # Step 3: 生成摘要
        print("\n📋 Step 3: 生成摘要")
        
        results["summary"] = {
            "total_analyzed": len(stock_codes),
            "valid_stocks": len(valid_stocks),
            "buy_signals": len([s for s in results["signals"] if s.get('signal') == 'BUY']),
            "sell_signals": len([s for s in results["signals"] if s.get('signal') == 'SELL']),
            "hold_signals": len([s for s in results["signals"] if s.get('signal') == 'HOLD']),
        }
        
        print(f"   买入: {results['summary']['buy_signals']}")
        print(f"   卖出: {results['summary']['sell_signals']}")
        print(f"   观望: {results['summary']['hold_signals']}")
        
        # Step 4: 生成报告
        print("\n📄 Step 4: 生成PDF报告")
        pdf_path = self.report_generator.generate_and_send(results, send_to_qq)
        
        # Step 5: 发送到QQ (可选)
        if send_to_qq:
            print("\n📤 Step 5: 发送到QQ")
            self._send_to_qq(pdf_path, results)
        
        # 保存JSON结果
        if output_path:
            json_path = output_path.replace('.pdf', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"   💾 JSON: {json_path}")
        
        print("\n" + "=" * 60)
        print("✅ 分析完成!")
        print("=" * 60)
        
        return results
    
    def _send_to_qq(self, pdf_path: str, results: dict):
        """发送到QQ (通过OpenClaw message)"""
        try:
            # 构建摘要消息
            summary = results.get('summary', {})
            signals = results.get('signals', [])
            
            msg = f"""📈 量化分析报告 v2.0

📊 摘要:
- 分析: {summary.get('total_analyzed', 0)}只
- 可信: {summary.get('valid_stocks', 0)}只
- 🟢 买入: {summary.get('buy_signals', 0)}只
- 🔴 卖出: {summary.get('sell_signals', 0)}只

🎯 Top信号:"""
            
            for s in signals[:3]:
                msg += f"\n- {s.get('stock_code')}: {s.get('signal')} ({s.get('probability')}%)"
            
            msg += f"\n\n📄 报告: {pdf_path}"
            
            print(f"   消息内容:\n{msg}")
            print("\n   💡 可通过OpenClaw发送到QQ")
            
        except Exception as e:
            print(f"   ⚠️ 发送失败: {e}")


def main():
    """主函数"""
    # 从命令行参数或配置文件获取股票列表
    test_stocks = [
        "sz.300001", "sz.300003", "sz.300007", 
        "sz.300010", "sz.300015", "sz.300017"
    ]
    
    # 也可以从文件读取
    config_file = Path(__file__).parent / "stocks_to_analyze.txt"
    if config_file.exists():
        with open(config_file) as f:
            test_stocks = [line.strip() for line in f if line.strip()]
    
    # 运行分析
    system = UnifiedQuantSystem()
    results = system.run_full_analysis(test_stocks)
    
    return results


if __name__ == "__main__":
    main()
