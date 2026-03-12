#!/bin/bash
# 每周备份 OpenClaw 配置到 memory 目录
# 创建时间: 2026-03-11

BACKUP_DIR="/home/liujerry/moltbot-memory"
SOURCE_DIR="$HOME/.openclaw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 复制文件 (保留权限)
cp -r "$SOURCE_DIR" "$BACKUP_DIR/openclaw_${TIMESTAMP}"

# 只保留最近4周备份
cd "$BACKUP_DIR" && ls -dt openclaw_* | tail -n +5 | xargs -r rm -rf

echo "[$(date)] OpenClaw 备份完成: openclaw_${TIMESTAMP}"
