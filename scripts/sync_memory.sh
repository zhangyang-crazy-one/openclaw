#!/bin/bash
# 夜间记忆同步脚本 - 同步到GitHub
# cron: 9a721acd-d8a2-4a75-a770-f5417d637d90
# 同步内容: MEMORY.md, HEARTBEAT.md
# 注意: memory/insights/ (gitignored) 和 skills/auto-explorer/ (不存在) 无法同步

set -e

WORKDIR="/home/liujerry/moltbot"
cd "$WORKDIR"

# 要同步的文件和目录
# 注意: memory/insights/ 在 .gitignore 中无法同步
#       skills/auto-explorer/ 不存在
# 只同步: MEMORY.md, HEARTBEAT.md
SYNC_ITEMS="MEMORY.md HEARTBEAT.md"

# 检查是否有要同步的内容
if [ ! -f "MEMORY.md" ] && [ ! -d "memory/insights" ]; then
    echo "没有找到要同步的记忆文件"
    exit 0
fi

# 添加文件
git add $SYNC_ITEMS

# 检查是否有变更
if git diff --cached --quiet; then
    echo "没有变更需要同步"
    exit 0
fi

# 提交
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
git commit -m "夜间记忆同步 $TIMESTAMP"

# 推送
git push origin main 2>/dev/null || git push origin master 2>/dev/null || git push upstream main 2>/dev/null || git push upstream master

echo "记忆同步完成: $TIMESTAMP"
