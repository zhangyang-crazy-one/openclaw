"""
PDF报告生成模块 v3.0 - 完整版
功能: 生成完整的量化分析报告
"""
import os
from datetime import datetime
from pathlib import Path

# 尝试导入markdown-pdf (中文支持最好)
try:
    from markdown_pdf import MarkdownPdf, Section
    HAS_MDPDF = True
except ImportError:
    HAS_MDPDF = False
    print("Warning: markdown_pdf not available")


class ReportGeneratorV3:
    """PDF报告生成器 v3.0 - 完整版"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_full_report(self, results: dict, output_path: str = None) -> str:
        """生成完整Markdown格式报告"""
        timestamp = results.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        md_content = f"""# 📈 量化分析报告 v3.0

**生成时间**: {timestamp}
**版本**: 完整版

---

## 📋 摘要

| 指标 | 数值 |
|------|------|
| 分析股票数 | {results.get('summary', {}).get('total_analyzed', 0)} |
| 有效数据 | {results.get('summary', {})} |
| 买入信号 | {results.get('summary', {}).get('buy_signals', 0)} |
| 卖出信号 | {results.get('summary', {}).get('sell_signals', 0)} |
| 观望信号 | {results.get('summary', {}).get('watch_signals', 0)} |

---

## 🏛️ 宏观分析

"""
        
        # 添加宏观数据
        macro = results.get('macro', {})
        if macro:
            for key, value in macro.items():
                md_content += f"- **{key}**: {value}\n"
        else:
            md_content += "- 暂无宏观数据\n"
        
        md_content += f"""

---

## 😊 市场情绪

- **情绪状态**: {results.get('summary', {}).get('sentiment', '中性')}

"""
        
        # 添加情绪数据
        sentiment = results.get('sentiment', {})
        if sentiment:
            for key, value in sentiment.items():
                md_content += f"- {key}: {value}\n"
        
        md_content += """

---

## 📊 技术分析 + 基本面 + 行业

| 股票代码 | 信号 | 获胜概率 | RSI(14) | 收盘价 | 行业 | ROE |
|---------|------|----------|---------|--------|-----|-----|
"""
        
        # 添加所有股票分析
        for stock in results.get('signals', []):
            code = stock.get('stock_code', '')
            signal = stock.get('signal', '')
            prob = stock.get('probability', 0)
            rsi = stock.get('rsi14', 0)
            close = stock.get('close', 0)
            fund = stock.get('fundamental', {})
            sector = stock.get('sector', {})
            
            roe = fund.get('roe', 'N/A')
            sector_name = sector.get('sector', 'N/A')
            
            md_content += f"| {code} | {signal} | {prob}% | {rsi} | {close} | {sector_name} | {roe} |\n"
        
        md_content += """

---

## 🎯 交易信号详情

"""
        
        # 添加详细信号
        buy_signals = [s for s in results.get('signals', []) if s.get('signal') == '买入']
        if buy_signals:
            md_content += "### 🟢 买入信号\n\n"
            for s in buy_signals:
                md_content += f"""**{s.get('stock_code')}**
- 获胜概率: {s.get('probability')}%
- RSI(14): {s.get('rsi14')}
- 收盘价: {s.get('close')}
- 原因: {s.get('reason')}

"""
        
        watch_signals = [s for s in results.get('signals', []) if s.get('signal') == '观望']
        if watch_signals:
            md_content += "### 🏷️ 观望信号\n\n"
            for s in watch_signals[:5]:  # 只显示前5个
                md_content += f"- **{s.get('stock_code')}**: {s.get('probability')}% (RSI={s.get('rsi14')})\n"
        
        md_content += f"""

---

## 📚 学术论文引用

"""
        
        # 添加论文引用
        citations = results.get('citations', [])
        if citations:
            for i, cite in enumerate(citations, 1):
                md_content += f"{i}. {cite.get('title', 'N/A')} - {cite.get('authors', ['N/A'])} ({cite.get('year', 'N/A')})\n"
        else:
            md_content += "暂无论文引用\n"
        
        md_content += f"""

---

## 📈 行业分布

"""
        
        # 统计行业分布
        sectors = {}
        for stock in results.get('signals', []):
            sector = stock.get('sector', {}).get('sector', '未知')
            sectors[sector] = sectors.get(sector, 0) + 1
        
        for sector, count in sectors.items():
            md_content += f"- {sector}: {count}只\n"
        
        md_content += """

---

*本报告由统一量化分析系统 v3.0 自动生成*

"""
        
        # 保存Markdown
        if not output_path:
            output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(output_path)
    
    def generate_pdf(self, results: dict, output_path: str = None) -> str:
        """生成PDF报告"""
        # 先生成markdown
        md_path = output_path.replace('.pdf', '.md') if output_path and output_path.endswith('.pdf') else None
        md_path = self.generate_full_report(results, md_path)
        
        if not output_path:
            output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        elif not output_path.endswith('.pdf'):
            output_path = output_path.replace('.md', '.pdf')
        
        if HAS_MDPDF:
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pdf = MarkdownPdf()
                pdf.add_section(Section(content))
                pdf.save(output_path)
                
                return str(output_path)
            except Exception as e:
                print(f"PDF生成失败: {e}")
        
        return md_path
    
    def generate_and_send(self, results: dict, send_to_qq: bool = False) -> str:
        """生成报告"""
        # 生成Markdown报告
        md_path = self.generate_full_report(results)
        
        # 生成PDF报告
        pdf_path = self.generate_pdf(results)
        
        print(f"📄 报告已生成:")
        print(f"   Markdown: {md_path}")
        print(f"   PDF: {pdf_path}")
        
        return pdf_path


# 兼容旧版本
class ReportGenerator(ReportGeneratorV3):
    pass
