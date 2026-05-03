#!/bin/bash
# K线数据每日采集 — wrapper 脚本
# 直接调用 Python 脚本更新新浪 K线，输出汇总
# 用于 openclaw cron 的 message 字段，让 LLM 只需执行一条命令

cd /home/liujerry/moltbot/scripts || exit 1

# 运行更新脚本，捕获输出
OUTPUT=$(python3 update_kline_sina.py --delay 1 2>&1)
RC=$?

# 统计结果
TOTAL=$(echo "$OUTPUT" | grep -c "^\s*[✓○✗]")
SUCCESS=$(echo "$OUTPUT" | grep -c "^✓")
SKIPPED=$(echo "$OUTPUT" | grep -c "^○")
FAILED=$(echo "$OUTPUT" | grep -c "^✗")

echo "exit_code=$RC"
echo "total=$TOTAL success=$SUCCESS skipped=$SKIPPED failed=$FAILED"
echo "---last-3-lines---"
echo "$OUTPUT" | tail -3

exit $RC
