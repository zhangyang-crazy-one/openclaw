#!/bin/bash
# A股技术指标批量计算脚本
# 用法: 
#   bash run_calculation.sh          # 全量计算
#   bash run_calculation.sh --dry-run # 仅检查数据
#   bash run_calculation.sh -w 16     # 16并发
#   bash run_calculation.sh -s 000001 # 仅计算单只股票

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/home/liujerry/moltbot/openclaw_py/bin/python3"

cd /home/liujerry/moltbot

echo "📊 启动技术指标计算..."
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

$PYTHON_BIN "$SCRIPT_DIR/calculator.py" "$@"

echo ""
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
