#!/bin/bash
# 保持浏览器打开模式

cd /home/liujerry/moltbot/skills/stagehand

source venv/bin/activate

echo "🚀 启动有头模式浏览器..."
echo "   按 Ctrl+C 保存并退出"
echo ""

python3 keep_open.py
