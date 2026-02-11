#!/bin/bash
# 真实使用 - 保持打开模式

cd /home/liujerry/moltbot/skills/stagehand

source venv/bin/activate

echo "🖥️ 启动浏览器 (长期保持模式)..."
echo ""
echo "💡 你现在可以:"
echo "   1. 在浏览器中手动操作"
echo "   2. 登录任何网站"
echo "   3. 访问任何页面"
echo ""
echo "🛑 按 Ctrl+C 保存 cookies 并退出"
echo ""

python3 keep_open.py
