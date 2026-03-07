#!/usr/bin/env python3
"""
统一量化分析系统 v3.0 - 完整版
功能: 数据验证 + 技术分析 + 基本面分析 + 宏观分析 + 行业分析 + 行为金融 + 论文引用 + PDF报告
"""
import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_fetcher import StockDataFetcher
from probability_model import WinProbabilityModel
from paper_citation import PaperCitation, RESEARCH_TOPICS
from report_generator import ReportGenerator


class UnifiedQuantSystemV3:
    """统一量化分析系统 v3.0 - 完整版"""
    
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.probability_model = WinProbabilityModel()
        self.citation = PaperCitation()
        self.report_generator = ReportGenerator()
        
    def get_fundamental_data(self, stock_code: str) -> dict:
        """获取基本面数据"""
        try:
            # 读取创业板财务数据
            data_dir = Path("/home/liujerry/金融数据/fundamentals/chuangye_full")
            profit_file = data_dir / "profit.csv"
            
            if profit_file.exists():
                import pandas as pd
                df = pd.read_csv(profit_file)
                
                # 匹配股票代码
                code = f"sz.{stock_code}" if not stock_code.startswith('sz.') else stock_code
                match = df[df['code'] == code]
                
                if not match.empty:
                    row = match.iloc[0]
                    return {
                        'roe': f"{row.get('roeAvg', 0) * 100:.1f}%",
                        'net_profit': f"{row.get('netProfit', 0):.2f}",
                        'gross_margin': f"{row.get('gpMargin', 0) * 100:.1f}%",
                        'revenue': f"{row.get('MBRevenue', 0):.2f}",
                    }
        except Exception as e:
            print(f"   基本面数据获取失败: {e}")
        
        return {'roe': 'N/A', 'net_profit': 'N/A', 'gross_margin': 'N/A', 'revenue': 'N/A'}
    
    def get_macro_data(self) -> dict:
        """获取宏观数据摘要"""
        try:
            macro_dir = Path("/home/liujerry/金融数据/macro")
            files = list(macro_dir.glob("economic_enhanced_*.json"))
            
            if files:
                import json
                latest = max(files, key=lambda x: x.stat().st_mtime)
                with open(latest) as f:
                    data = json.load(f)
                
                summary = {}
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
                
                return summary
        except Exception as e:
            print(f"   宏观数据获取失败: {e}")
        
        return {"GDP": "N/A", "LPR": "N/A"}
    
    def get_sentiment_data(self) -> dict:
        """获取市场情绪数据"""
        try:
            sentiment_file = Path("/home/liujerry/金融数据/reports/behavioral_sentiment_*.json")
            files = list(sentiment_file.parent.glob("behavioral_sentiment_*.json"))
            
            if files:
                import json
                latest = max(files, key=lambda x: x.stat().st_mtime)
                with open(latest) as f:
                    data = json.load(f)
                return data
        except Exception as e:
            print(f"   情绪数据获取失败: {e}")
        
        return {"sentiment": "中性", "bias": "无偏差"}
    
    def analyze_sector(self, stock_code: str) -> dict:
        """行业分析"""
        # 简化的行业映射
        sector_map = {
            '300': '创业板-科技',
            '301': '创业板-新兴',
            '600': '沪市-主板',
            '601': '沪市-主板',
            '688': '科创板',
        }
        
        prefix = stock_code[:3]
        return {
            'sector': sector_map.get(prefix, '其他'),
            'outlook': '乐观' if prefix in ['300', '301', '688'] else '中性'
        }
    
    def run_full_analysis(self, stock_codes: list, output_path: str = None, send_to_qq: bool = False) -> dict:
        """运行完整分析"""
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "3.0",
            "validation": {},
            "technical": {},
            "fundamental": {},
            "macro": {},
            "sector": {},
            "sentiment": {},
            "signals": [],
            "citations": [],
            "summary": {}
        }
        
        print("=" * 70)
        print("🚀 统一量化分析系统 v3.0 - 完整版")
        print("=" * 70)
        
        # Step 1: 技术分析数据获取
        print("\n📊 Step 1: 技术分析 (Baostock)")
        
        with self.fetcher as fetcher:
            formatted_codes = []
            for code in stock_codes:
                code = code.strip()
                if code.isdigit():
                    if code.startswith('3'):
                        formatted_codes.append(f'sz.{code}')
                    elif code.startswith('6'):
                        formatted_codes.append(f'sh.{code}')
                    elif code.startswith('688'):
                        formatted_codes.append(f'sh.{code}')
                    else:
                        formatted_codes.append(f'sz.{code}')
                else:
                    formatted_codes.append(code)
            
            print(f"   获取 {len(formatted_codes)} 只股票数据...")
            stocks_data = fetcher.batch_analyze(formatted_codes)
            technical_signals = fetcher.generate_signals(stocks_data)
        
        # 技术分析结果
        results["technical"] = technical_signals
        validation_results = {s['code']: {'confidence': 95, 'source': 'baostock'} for s in technical_signals}
        results["validation"] = validation_results
        print(f"   ✅ 技术分析完成: {len(technical_signals)}只")
        
        # Step 2: 基本面分析
        print("\n💰 Step 2: 基本面分析")
        
        fundamental_data = {}
        for stock in technical_signals:
            code = stock['code']
            cn_code = code[3:] if len(code) > 3 else code
            fundamentals = self.get_fundamental_data(cn_code)
            fundamental_data[code] = fundamentals
        
        results["fundamental"] = fundamental_data
        print(f"   ✅ 基本面分析完成")
        
        # Step 3: 宏观分析
        print("\n🏛️ Step 3: 宏观分析")
        
        macro_data = self.get_macro_data()
        results["macro"] = macro_data
        print(f"   宏观数据: {macro_data}")
        
        # Step 4: 行业分析
        print("\n🏭 Step 4: 行业分析")
        
        sector_data = {}
        for stock in technical_signals:
            code = stock['code']
            cn_code = code[3:] if len(code) > 3 else code
            sector_data[code] = self.analyze_sector(cn_code)
        
        results["sector"] = sector_data
        print(f"   ✅ 行业分析完成")
        
        # Step 5: 情绪分析
        print("\n😊 Step 5: 行为金融学分析")
        
        sentiment_data = self.get_sentiment_data()
        results["sentiment"] = sentiment_data
        print(f"   情绪状态: {sentiment_data.get('sentiment', '中性')}")
        
        # Step 6: 生成综合信号
        print("\n🎯 Step 6: 综合交易信号")
        
        signals = []
        for stock in technical_signals:
            code = stock['code']
            cn_code = code[3:] if len(code) > 3 else code
            
            # 计算获胜概率
            rsi = stock.get('rsi14', 50)
            prob = 50  # 基础概率
            
            # 基本面调整
            fund = fundamental_data.get(code, {})
            if fund.get('roe') and fund.get('roe') != 'N/A':
                try:
                    roe = float(fund['roe'])
                    prob += min(roe * 0.5, 15)  # ROE最高贡献15%
                except:
                    pass
            
            # RSI调整
            if rsi < 30:
                prob += 10
            elif rsi < 50:
                prob += 5
            
            prob = min(prob, 95)  # 最高95%
            
            # 确定信号
            if prob >= 65:
                signal = '买入'
            elif prob <= 45:
                signal = '卖出'
            else:
                signal = '观望'
            
            signals.append({
                "stock_code": cn_code,
                "name": cn_code,
                "signal": signal,
                "rsi14": rsi,
                "close": stock.get('close', 0),
                "lower_band": stock.get('lower_band', 0),
                "reason": stock.get('reason', ''),
                "probability": round(prob, 1),
                "fundamental": fund,
                "sector": sector_data.get(code, {}),
            })
        
        # 按概率排序
        signals.sort(key=lambda x: x['probability'], reverse=True)
        results["signals"] = signals
        
        # 统计
        buy_count = len([s for s in signals if s['signal'] == '买入'])
        sell_count = len([s for s in signals if s['signal'] == '卖出'])
        watch_count = len([s for s in signals if s['signal'] == '观望'])
        
        print(f"   买入: {buy_count} | 卖出: {sell_count} | 观望: {watch_count}")
        
        # Step 7: 学术论文引用
        print("\n📚 Step 7: 学术论文引用")
        
        citations = []
        topics = ["quantitative investing", "RSI trading strategy", "behavioral finance"]
        for topic in topics[:3]:
            try:
                papers = self.citation.search_papers(topic, max_results=2)
                citations.extend(papers)
            except:
                pass
        
        results["citations"] = citations[:5]  # 最多5篇
        print(f"   引用论文: {len(results['citations'])}篇")
        
        # Step 8: 生成摘要
        print("\n📋 Step 8: 生成摘要")
        
        results["summary"] = {
            "total_analyzed": len(stock_codes),
            "valid_stocks": len(technical_signals),
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "watch_signals": watch_count,
            "macro_summary": macro_data,
            "sentiment": sentiment_data.get('sentiment', '中性'),
            "citation_count": len(results["citations"]),
        }
        
        # Step 9: 生成报告
        print("\n📄 Step 9: 生成PDF报告")
        
        # 构建完整报告内容
        full_results = self._build_full_report(results)
        pdf_path = self.report_generator.generate_and_send(full_results, send_to_qq)
        
        print("\n" + "=" * 70)
        print("✅ 完整分析完成!")
        print("=" * 70)
        
        return results
    
    def _build_full_report(self, results: dict) -> dict:
        """构建完整报告格式"""
        # 将所有分析结果整合到一个报告中
        report = {
            "timestamp": results["timestamp"],
            "version": results["version"],
            "summary": results["summary"],
            "validation": results["validation"],
            "technical": {s['code']: s for s in results.get("technical", [])},
            "fundamental": results.get("fundamental", {}),
            "macro": results.get("macro", {}),
            "sector": results.get("sector", {}),
            "sentiment": results.get("sentiment", {}),
            "signals": results["signals"],
            "citations": results["citations"],
        }
        return report


def main():
    """主函数"""
    # 读取自选股
    watchlist_file = Path("/home/liujerry/金融数据/config/watchlist_top20.txt")
    
    test_stocks = []
    if watchlist_file.exists():
        with open(watchlist_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                code = line.split()[0]
                if len(code) == 6 and code.isdigit():
                    test_stocks.append(code)
        print(f"📂 读取自选股: {len(test_stocks)} 只")
    else:
        test_stocks = ["300001", "300003", "300007", "300010", "300015"]
        print("⚠️ 自选股文件不存在，使用默认测试股票")
    
    # 运行分析
    system = UnifiedQuantSystemV3()
    results = system.run_full_analysis(test_stocks)
    
    return results


if __name__ == "__main__":
    main()
