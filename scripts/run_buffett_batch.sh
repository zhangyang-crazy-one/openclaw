#!/bin/bash
cd /home/liujerry/moltbot
START=$(python3 -c "import json; print(json.load(open('金融数据/fundamentals/buffett_progress.json'))['processed'])")
LIMIT=50
echo "=== Buffett采集批处理 ==="
echo "起始: $START, 限制: $LIMIT"
python3 scripts/collect_buffett_data.py --start $START --batch 50 --limit $LIMIT 2>&1
