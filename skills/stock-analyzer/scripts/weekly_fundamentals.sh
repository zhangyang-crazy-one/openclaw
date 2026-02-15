#!/bin/bash
# 每周财报数据获取任务
# 时间: 每周一 9:00

cd /home/liujerry/moltbot/skills/stock-analyzer/scripts

# 激活虚拟环境
source /home/liujerry/文档/programs/.venv/bin/activate 2>/dev/null || true

# 运行获取任务
python3 fetch_fundamentals.py

# 输出日志
echo "完成时间: $(date)" >> /home/liujerry/金融数据/fundamentals/fetch.log
