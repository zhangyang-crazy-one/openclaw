#!/bin/bash
# cron_health_check.sh - 防腐化自检 (每 6 小时)
# 检查项: 1) 关键 cron 路径存在  2) K线数据新鲜度  3) tech_indicators 新鲜度
# 输出: ~/.logs/cron_health.log (追加)
# 失败: 写入 ~/.logs/cron_health_alert.flag

set +e
LOG=~/.logs/cron_health.log
ALERT=~/.logs/cron_health_alert.flag
ERRORS=0

echo "============================================================" >> "$LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] cron_health_check 开始" >> "$LOG"

# === 1. 关键脚本路径 ===
SCRIPTS=(
  "/home/liujerry/moltbot/skills/claw-screener-cn/src/update_all_a_stocks.py"
  "/home/liujerry/moltbot/scripts/academic_final.py"
  "/home/liujerry/moltbot/scripts/moltbook_knowledge_sync_v3.py"
  "/home/liujerry/moltbot/scripts/auto_extract_knowledge.py"
  "/home/liujerry/moltbot/scripts/morning_wakeup.sh"
  "/home/liujerry/scripts/tech_indicators_cron.sh"
)
for s in "${SCRIPTS[@]}"; do
  if [ ! -f "$s" ]; then
    echo "❌ MISSING: $s" >> "$LOG"
    ERRORS=$((ERRORS+1))
  else
    echo "✅ OK: $s" >> "$LOG"
  fi
done

# === 2. K线数据新鲜度 (核心资产) ===
# K线 cron 整点 9/11/13/15/17/19/21 + 半点 10/12/14/16/18/20/22
# 工作日 16:30 跑最后一批, 周末不跑
# 6h 阈值 200 在 06:00 永远不达标 (上次 22:30, 距今 7.5h+)
# → 阈值 1500 (-mtime -1) 涵盖 1 天内单次或多次跑的全量
# 6h 仅做"是否在跑"轻检查
STOCK_DIR=/home/liujerry/金融数据/stocks
FRESH=$(find "$STOCK_DIR" -name "*.csv" -mmin -360 2>/dev/null | wc -l)
echo "📊 K线 mtime<6h: $FRESH 只" >> "$LOG"
# 工作日 9-22, 周末 0; 阈值 200 对 16:30 之后那次 (10h) 永远不达标
# 改为 -mtime -1 (24h), 涵盖工作日至少 3 次跑 (200-2400+)
FRESH_24H=$(find "$STOCK_DIR" -name "*.csv" -mtime -1 2>/dev/null | wc -l)
echo "📊 K线 mtime<24h: $FRESH_24H 只" >> "$LOG"
if [ "$FRESH_24H" -lt 100 ]; then
  echo "⚠️ K线数据陈旧: 24h 内只新增 $FRESH_24H (预期 500+)" >> "$LOG"
  ERRORS=$((ERRORS+1))
fi

# === 3. tech_indicators 新鲜度 ===
# tech_incremental.py 是增量更新: 每天 19:45 跑 1 分钟, 更新 ~2000/5474 只
# 阈值应基于"今天 19:45 这次跑更新了多少"而不是 -mtime -1
# 用 -mmin -1500 (25h, 涵盖 19:45 之后到第二天 21:00) 抓 24h 单次跑的全量
# 实际 ~2000-2500 是健康 (其它已最新被 skip)
TECH_DIR=/home/liujerry/金融数据/technical_indicators
TECH_FRESH=$(find "$TECH_DIR" -name "*.csv" -mmin -1500 2>/dev/null | wc -l)
echo "📊 tech_indicators mtime<25h: $TECH_FRESH 只" >> "$LOG"
if [ "$TECH_FRESH" -lt 1500 ]; then
  echo "⚠️ tech_indicators 陈旧: 25h 内只 $TECH_FRESH (预期 2000-2500)" >> "$LOG"
  ERRORS=$((ERRORS+1))
fi

# === 4. 知识图谱健康 (wakeup_memory_loader.py) ===
WAKEUP_FILE=/tmp/wakeup_kg_context.txt
if [ -f "$WAKEUP_FILE" ]; then
  WAKEUP_AGE_MIN=$(( ( $(date +%s) - $(stat -c %Y "$WAKEUP_FILE") ) / 60 ))
  echo "📊 wakeup 上下文: $WAKEUP_AGE_MIN 分钟前" >> "$LOG"
  if [ "$WAKEUP_AGE_MIN" -gt 900 ]; then  # 15h
    echo "⚠️ wakeup 上下文陈旧: $WAKEUP_AGE_MIN 分钟 (预期 < 900)" >> "$LOG"
    ERRORS=$((ERRORS+1))
  fi
else
  echo "❌ wakeup 上下文文件不存在" >> "$LOG"
  ERRORS=$((ERRORS+1))
fi

# === 5. 总结 ===
if [ "$ERRORS" -gt 0 ]; then
  echo "❌ 总计 $ERRORS 项异常" >> "$LOG"
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERRORS=$ERRORS" > "$ALERT"
else
  echo "✅ 全部健康" >> "$LOG"
  rm -f "$ALERT"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] cron_health_check 完成 (errors=$ERRORS)" >> "$LOG"
