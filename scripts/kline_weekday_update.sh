#!/bin/bash
# 工作日K线全量更新 - 分批执行
# 替代 AI Agent cron job，直接 shell 执行，避免 session 膨胀

set -e
cd /home/liujerry/moltbot
PY="$(pwd)/openclaw_py/bin/python"
SCRIPT="skills/claw-screener-cn/src/update_all_a_stocks.py"
DATA_DIR="/home/liujerry/金融数据/stocks"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=== 工作日K线全量更新开始 ==="

# Batch 1: 科创板1 (16:30)
log "Batch 1: 科创板 start=4587 count=150"
$PY $SCRIPT --start=4587 150 2>&1 | tail -5

# Batch 2: 科创板2
log "Batch 2: 科创板 start=4737 count=150"
$PY $SCRIPT --start=4737 150 2>&1 | tail -5

# Batch 3: 科创板3
log "Batch 3: 科创板 start=4887 count=150"
$PY $SCRIPT --start=4887 150 2>&1 | tail -5

# Batch 4: 科创板4
log "Batch 4: 科创板 start=5037 count=200"
$PY $SCRIPT --start=5037 200 2>&1 | tail -5

# Batch 5: 000深市1
log "Batch 5: 000深市 start=0 count=150"
$PY $SCRIPT --start=0 150 2>&1 | tail -5

# Batch 6: 000深市2
log "Batch 6: 000深市 start=150 count=150"
$PY $SCRIPT --start=150 150 2>&1 | tail -5

# Batch 7: 002中小板
log "Batch 7: 002中小板 start=527 count=500"
$PY $SCRIPT --start=527 500 2>&1 | tail -5

# Batch 8: 300创业板
log "Batch 8: 300创业板 start=1490 count=500"
$PY $SCRIPT --start=1490 500 2>&1 | tail -5

log "=== 更新完成 ==="
log "K线文件总数: $(ls "$DATA_DIR"/*.csv 2>/dev/null | wc -l)"
log "今天更新: $(find "$DATA_DIR" -maxdepth 1 -mtime -1 -name '*.csv' | wc -l)"
