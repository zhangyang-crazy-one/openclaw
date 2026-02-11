#!/bin/bash
# 真实交互模式 - 可以看到浏览器操作

cd /home/liujerry/moltbot/skills/stagehand

source venv/bin/activate

echo "🚀 启动真实交互模式..."
echo "   你将看到浏览器窗口和所有操作"
echo ""
echo "💡 使用方法:"
echo "   输入命令如: goto https://github.com"
echo "   或自然语言: 点击登录按钮"
echo ""
echo "🛑 按 Ctrl+C 保存并退出"
echo ""

python3 interactive.py
