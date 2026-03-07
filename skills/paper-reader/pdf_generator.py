#!/usr/bin/env python3
"""
Paper Reader - PDF 生成模块 v2.1 (优化版)
生成美观的专业学术论文报告
修复中文重叠和布局问题
"""
from fpdf import FPDF
from datetime import datetime
from pathlib import Path
import os


# 学术风格配色
COLORS = {
    'primary': (26, 54, 93),
    'secondary': (44, 82, 130),
    'accent': (49, 130, 206),
    'text': (45, 55, 72),
    'light_text': (113, 128, 150),
    'background': (255, 255, 255),
    'light_bg': (247, 250, 252),
    'border': (226, 232, 240),
    'success': (56, 161, 105),
    'warning': (214, 158, 46),
    'tldr_bg': (235, 248, 255),
}


class PaperPDFGenerator(FPDF):
    """学术论文报告 PDF 生成器 - 优化版"""
    
    def __init__(self):
        super().__init__(orientation='portrait', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=15)
        
        self.margin_left = 20
        self.margin_right = 20
        self.margin_top = 20
        self.current_y = 20
        
        # 添加中文字体支持
        self.main_font = 'Helvetica'
        try:
            font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
            if os.path.exists(font_path):
                self.add_font('NotoSans', '', font_path)
                self.add_font('NotoSans', 'B', font_path)
                self.main_font = 'NotoSans'
        except Exception as e:
            pass
    
    def header(self):
        pass
    
    def footer(self):
        self.set_y(-15)
        self.set_font(self.main_font, '', 8)
        self.set_text_color(*COLORS['light_text'])
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
    
    def set_title_style(self):
        self.set_text_color(*COLORS['primary'])
        self.set_font(self.main_font, 'B', 18)
    
    def set_subtitle_style(self):
        self.set_text_color(*COLORS['secondary'])
        self.set_font(self.main_font, 'B', 14)
    
    def set_heading_style(self):
        self.set_text_color(*COLORS['primary'])
        self.set_font(self.main_font, 'B', 12)
    
    def set_body_style(self):
        self.set_text_color(*COLORS['text'])
        self.set_font(self.main_font, '', 10)
    
    def set_small_style(self):
        self.set_text_color(*COLORS['light_text'])
        self.set_font(self.main_font, '', 8)
    
    def add_spacer(self, height=5):
        self.ln(height)
    
    def safe_cell(self, text, h=5, new_x="LMARGIN", new_y="NEXT"):
        """安全输出文本，避免中文问题"""
        if not text:
            return
        # 限制文本长度
        text = str(text)[:200]
        try:
            self.cell(0, h, text, new_x=new_x, new_y=new_y)
        except:
            pass
    
    def add_section_title(self, title, icon=''):
        self.ln(5)
        full_title = f"{icon} {title}" if icon else title
        self.set_heading_style()
        self.cell(0, 8, full_title, new_x="LMARGIN", new_y="NEXT")
        
        self.set_draw_color(*COLORS['accent'])
        self.set_line_width(0.5)
        line_width = min(len(title) * 3, 50)
        self.line(self.get_x(), self.get_y() - 1, self.get_x() + line_width, self.get_y() - 1)
        self.ln(3)
    
    def add_tldr(self, tldr_text):
        self.ln(5)
        
        self.set_fill_color(*COLORS['tldr_bg'])
        self.set_draw_color(*COLORS['accent'])
        self.set_line_width(0.5)
        
        # 简化TL;DR区域
        h = 15
        self.rect(x=self.margin_left + 3, y=self.get_y(), 
                  w=self.w - self.margin_left - self.margin_right - 6, 
                  h=h, style='FD')
        
        self.set_xy(self.margin_left + 6, self.get_y() + 3)
        self.set_font(self.main_font, 'B', 10)
        self.set_text_color(*COLORS['accent'])
        self.cell(25, 5, 'TL;DR', new_x="LMARGIN", new_y="NEXT")
        
        self.set_xy(self.margin_left + 6, self.get_y() + 3)
        self.set_font(self.main_font, '', 9)
        self.set_text_color(*COLORS['text'])
        
        # 分行输出
        tldr_text = str(tldr_text)[:100]
        self.multi_cell(self.w - self.margin_left - self.margin_right - 15, 4, tldr_text)
        
        self.ln(3)
    
    def add_contribution(self, contributions):
        if not contributions:
            return
        
        self.ln(3)
        for i, contrib in enumerate(contributions, 1):
            self.set_font(self.main_font, 'B', 10)
            self.set_text_color(*COLORS['success'])
            self.cell(8, 5, f'{i}.', new_x="LMARGIN", new_y="NEXT")
            
            self.set_font(self.main_font, '', 10)
            self.set_text_color(*COLORS['text'])
            contrib = str(contrib)[:80]
            self.multi_cell(0, 5, contrib, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
    
    def add_key_points(self, points):
        if not points:
            return
        
        self.ln(3)
        for point in points:
            self.set_text_color(*COLORS['accent'])
            self.set_font(self.main_font, '', 10)
            self.cell(5, 4, '-', new_x="LMARGIN", new_y="NEXT")
            
            self.set_text_color(*COLORS['text'])
            point = str(point)[:70]
            self.multi_cell(0, 4, point, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)
    
    def add_abstract(self, abstract_text):
        self.set_body_style()
        abstract_text = str(abstract_text)[:1500]
        self.multi_cell(0, 4.5, abstract_text)
    
    def add_method(self, method_text):
        self.ln(3)
        self.set_body_style()
        method_text = str(method_text)[:800]
        self.multi_cell(0, 4.5, method_text)
    
    def add_results_table(self, results_dict):
        if not results_dict:
            return
        
        self.ln(5)
        
        # 表头
        self.set_fill_color(*COLORS['primary'])
        self.set_text_color(255, 255, 255)
        self.set_font(self.main_font, 'B', 9)
        
        keys = list(results_dict.keys())
        col_width = (self.w - self.margin_left - self.margin_right) / len(keys)
        
        for key in keys:
            self.cell(col_width, 7, str(key)[:15], 1, 0, 'C', True)
        self.ln()
        
        # 数据行
        self.set_fill_color(*COLORS['light_bg'])
        self.set_text_color(*COLORS['text'])
        self.set_font(self.main_font, '', 9)
        
        values = list(results_dict.values())
        for i, val in enumerate(values):
            fill = (i % 2 == 1)
            self.cell(col_width, 6, str(val)[:15], 1, 0, 'C', fill)
        self.ln()
    
    def add_notes_area(self):
        self.ln(8)
        
        self.set_heading_style()
        self.cell(0, 8, 'Notes', new_x="LMARGIN", new_y="NEXT")
        
        self.set_draw_color(*COLORS['border'])
        self.set_line_width(0.2)
        
        note_height = 35
        self.rect(x=self.margin_left, y=self.get_y(), 
                  w=self.w - self.margin_left - self.margin_right, 
                  h=note_height, style='D')
        
        self.set_xy(self.margin_left + 5, self.get_y() + 5)
        self.set_small_style()
        self.cell(0, 5, 'Write your notes here...', new_x="LMARGIN", new_y="NEXT")
        
        # 划线
        y_start = self.get_y() + 3
        for i in range(4):
            self.line(self.margin_left + 5, y_start + i * 7, 
                     self.w - self.margin_right - 5, y_start + i * 7)
    
    def generate_single(self, paper_data, output_path):
        self.add_page()
        
        # 标题区域
        self.set_xy(self.margin_left, self.margin_top)
        
        self.set_title_style()
        title = str(paper_data.get('title', 'Untitled'))[:70]
        self.multi_cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        
        self.ln(3)
        
        # 作者/来源
        self.set_text_color(*COLORS['secondary'])
        self.set_font(self.main_font, '', 10)
        authors = paper_data.get('authors', [])
        if authors:
            author_str = ', '.join([str(a)[:30] for a in authors[:3]])
            self.cell(0, 5, f"来源: {author_str}", new_x="LMARGIN", new_y="NEXT")
        
        # 日期
        published = paper_data.get('published', '')
        if published:
            self.set_text_color(*COLORS['light_text'])
            self.set_font(self.main_font, '', 9)
            self.cell(0, 4, f"日期: {published}", new_x="LMARGIN", new_y="NEXT")
        
        # TL;DR
        tldr = paper_data.get('tldr', '')
        if tldr:
            self.add_tldr(tldr)
        
        # 摘要
        self.add_section_title('Abstract', '')
        abstract = paper_data.get('abstract', paper_data.get('summary', ''))
        if abstract:
            self.add_abstract(abstract[:800])
        
        # 核心贡献
        contributions = paper_data.get('contributions', [])
        if contributions:
            self.add_section_title('Core Contributions', '')
            self.add_contribution(contributions[:4])
        
        # 关键要点
        key_points = paper_data.get('key_points', [])
        if key_points:
            self.add_section_title('Key Points', '')
            self.add_key_points(key_points[:5])
        
        # 方法论
        method = paper_data.get('method', '')
        if method:
            self.add_section_title('Method', '')
            self.add_method(method[:500])
        
        # 实验结果
        results = paper_data.get('results', {})
        if results:
            self.add_section_title('Results', '')
            self.add_results_table(results)
        
        # 笔记区域
        self.add_notes_area()
        
        # 保存 PDF
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output(str(output_path))
        
        return str(output_path)


def generate_pdf(paper_data, output_path='paper_report.pdf'):
    """便捷函数：生成单篇论文 PDF"""
    pdf = PaperPDFGenerator()
    return pdf.generate_single(paper_data, output_path)


def generate_batch(papers, output_dir='.'):
    """便捷函数：批量生成 PDF"""
    results = []
    for i, paper in enumerate(papers):
        safe_title = ''.join(c for c in paper.get('title', f'paper_{i}')[:30] 
                            if c.isalnum() or c in ' -')
        output_path = Path(output_dir) / f"{safe_title}.pdf"
        pdf = PaperPDFGenerator()
        path = pdf.generate_single(paper, str(output_path))
        results.append(path)
    return results


if __name__ == '__main__':
    # 测试
    test_paper = {
        'title': '量化分析报告 - 2026年3月5日',
        'authors': ['统一量化分析系统'],
        'arxiv_id': '',
        'published': '2026-03-05',
        'tldr': '分析13只自选股，买入0只，关注8只',
        'abstract': '本次分析涵盖13只自选股，数据置信度95%。买入信号0只，卖出信号0只，关注信号8只。',
        'contributions': [
            '分析股票数: 13',
            '可信股票数: 13', 
            '买入信号: 0',
            '卖出信号: 0'
        ],
        'key_points': [
            '300199 翰宇药业 - 关注 (50%)',
            '300628 亿联网络 - 关注 (50%)',
            '300533 冰川网络 - 关注 (50%)'
        ],
        'method': '使用Baostock获取实时行情数据，结合RSI、MACD、布林带等技术指标进行信号分析',
        'results': {
            '买入': '0',
            '卖出': '0', 
            '关注': '8',
            '观望': '5'
        }
    }
    
    output = generate_pdf(test_paper, '/home/liujerry/reports/test_quant.pdf')
    print(f"Generated: {output}")
