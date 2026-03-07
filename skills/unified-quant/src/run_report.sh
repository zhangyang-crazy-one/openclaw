#!/bin/bash
# 统一量化分析报告生成并发送PDF

cd /home/liujerry/moltbot/skills/unified-quant/src

# 运行Python脚本生成HTML
HTML_FILE=$(python3 unified_quant_report.py 2>&1 | tail -1)

if [[ -f "$HTML_FILE" ]]; then
    # 转换为PDF
    PDF_FILE="${HTML_FILE%.html}.pdf"
    libreoffice --headless --convert-to pdf --outdir /tmp "$HTML_FILE" 2>&1
    
    # 发送PDF
    if [[ -f "$PDF_FILE" ]]; then
        openclaw message send --channel qq --target 740884666 --file "$PDF_FILE" --message "📊 量化分析报告"
        echo "PDF已发送"
    else
        echo "PDF生成失败"
    fi
else:
    echo "HTML生成失败"
fi
