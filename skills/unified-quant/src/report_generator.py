"""
PDF报告生成模块
功能: 生成量化分析报告并发送到QQ
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 尝试导入reportlab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("Warning: reportlab not available, using markdown fallback")


class ReportGenerator:
    """PDF报告生成器"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_markdown_report(self, results: Dict, output_path: str = None) -> str:
        """生成Markdown格式报告"""
        timestamp = results.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        md_content = f"""# 📈 量化分析报告

**生成时间**: {timestamp}

---

## 📊 数据验证结果

| 股票代码 | 数据置信度 | 状态 |
|---------|------------|------|
"""
        
        # 添加验证结果
        for code, val in results.get('validation', {}).items():
            confidence = val.get('confidence', 0)
            status = "✅ 可用" if confidence >= 70 else "⚠️ 不可用"
            md_content += f"| {code} | {confidence}% | {status} |\n"
        
        md_content += f"""

## 🎯 交易信号

| 股票代码 | 信号 | 获胜概率 | 预期收益 | 引用 |
|---------|------|----------|----------|-------|
"""
        
        # 添加信号结果
        for stock in results.get('signals', []):
            code = stock.get('stock_code', '')
            signal = stock.get('signal', '')
            prob = stock.get('probability', 0)
            ret = stock.get('expected_return', 0)
            cite = stock.get('citation', '')
            md_content += f"| {code} | {signal} | {prob}% | {ret}% | {cite} |\n"
        
        # 添加摘要
        summary = results.get('summary', {})
        md_content += f"""

---

## 📋 摘要

- 分析股票数: {summary.get('total_analyzed', 0)}
- 可信股票数: {summary.get('valid_stocks', 0)}
- 买入信号: {summary.get('buy_signals', 0)}
- 卖出信号: {summary.get('sell_signals', 0)}

---

*本报告由统一量化分析系统自动生成*
"""
        
        # 保存Markdown
        if not output_path:
            output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(output_path)
    
    def generate_pdf_report(self, results: Dict, output_path: str = None) -> str:
        """生成PDF格式报告"""
        if not HAS_REPORTLAB:
            # 回退到Markdown
            return self.generate_markdown_report(results, output_path.replace('.pdf', '.md') if output_path else None)
        
        if not output_path:
            output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 创建PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
        )
        story.append(Paragraph("📈 量化分析报告", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # 时间
        timestamp = results.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        story.append(Paragraph(f"生成时间: {timestamp}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # 交易信号表格
        story.append(Paragraph("🎯 交易信号", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        if results.get('signals'):
            # 表头
            data = [['股票', '信号', '概率', '预期收益', '引用']]
            
            for stock in results['signals']:
                data.append([
                    stock.get('stock_code', ''),
                    stock.get('signal', ''),
                    f"{stock.get('probability', 0)}%",
                    f"{stock.get('expected_return', 0)}%",
                    stock.get('citation', '')[:20]
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(table)
        
        # 摘要
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("📋 摘要", styles['Heading2']))
        
        summary = results.get('summary', {})
        summary_text = f"""
        分析股票数: {summary.get('total_analyzed', 0)}<br/>
        可信股票数: {summary.get('valid_stocks', 0)}<br/>
        买入信号: {summary.get('buy_signals', 0)}<br/>
        卖出信号: {summary.get('sell_signals', 0)}
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        
        # 生成PDF
        doc.build(story)
        
        return str(output_path)
    
    def generate_and_send(self, results: Dict, send_to_qq: bool = True) -> str:
        """生成报告并(可选)发送到QQ"""
        # 生成Markdown报告
        md_path = self.generate_markdown_report(results)
        
        # 生成PDF报告
        pdf_path = self.generate_pdf_report(results)
        
        print(f"📄 报告已生成:")
        print(f"   Markdown: {md_path}")
        print(f"   PDF: {pdf_path}")
        
        return pdf_path


if __name__ == "__main__":
    # 测试
    test_results = {
        "timestamp": "2026-02-21 12:00:00",
        "summary": {
            "total_analyzed": 10,
            "valid_stocks": 8,
            "buy_signals": 3,
            "sell_signals": 2,
        },
        "signals": [
            {"stock_code": "sz.300001", "signal": "BUY", "probability": 68, "expected_return": 3.2, "citation": "[Markowitz, 1952]"},
            {"stock_code": "sz.300003", "signal": "SELL", "probability": 35, "expected_return": -1.5, "citation": "[Fama, 1992]"},
        ]
    }
    
    generator = ReportGenerator()
    path = generator.generate_and_send(test_results)
    print(f"Output: {path}")
