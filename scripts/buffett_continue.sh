#!/bin/bash
# Buffett数据持续采集脚本
# 检查进度，如果还有未处理的股票，继续采集50只
cd /home/liujerry/moltbot
PROGRESS_FILE="/home/liujerry/金融数据/fundamentals/buffett_progress.json"
OUTPUT_FILE="/home/liujerry/金融数据/fundamentals/buffett_supplementary.csv"

if [ ! -f "$PROGRESS_FILE" ]; then
    echo "无进度文件，退出"
    exit 0
fi

PROCESSED=$(python3 -c "import json; print(json.load(open('$PROGRESS_FILE'))['processed'])")
TOTAL=$(python3 -c "import json; print(json.load(open('$PROGRESS_FILE'))['total'])")

if [ "$PROCESSED" -ge "$TOTAL" ]; then
    echo "采集完成！共 $TOTAL 只股票"
    # 验证数据
    python3 -c "
import pandas as pd
df = pd.read_csv('$OUTPUT_FILE')
print(f'记录数: {len(df)}')
print(f'interest_expense非零: {(df[\"interest_expense\"] > 0).sum()}')
print(f'operating_profit非零: {(df[\"operating_profit\"] != 0).sum()}')
"
    exit 0
fi

echo "进度: $PROCESSED/$TOTAL，继续采集..."
python3 scripts/collect_buffett_data.py --start 0 --batch 50 --limit 50 2>&1 | tail -5
