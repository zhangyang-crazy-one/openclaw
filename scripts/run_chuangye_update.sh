#!/bin/bash
# 创业板数据每日更新 — wrapper 脚本
# 更新创业板 K线 + 财务数据，输出汇总

set -e
PYTHON=/home/liujerry/moltbot/openclaw_py/bin/python
SKILL_DIR=/home/liujerry/moltbot/skills/claw-screener-cn/src

echo "=== [1/2] 创业板K线更新 (300只) ==="
$PYTHON $SKILL_DIR/update_all_a_stocks.py --start=1491 300 2>&1
echo ""

echo "=== [2/2] 创业板财务数据更新 ==="
$PYTHON $SKILL_DIR/update_financial_batch.py 100 2>&1
echo ""

echo "=== 验证 ==="
echo "K线文件数: $(ls /home/liujerry/金融数据/stocks/300*.csv 2>/dev/null | wc -l)"
echo "财务记录: $(wc -l < /home/liujerry/金融数据/fundamentals/chuangye_full/profit.csv 2>/dev/null || echo 0)"
echo ""
echo "done."
