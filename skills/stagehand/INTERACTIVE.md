#!/usr/bin/env python3
"""
MiniMax Browser Interactive Mode - Quick Start

有头模式使用指南
"""

print("=" * 80)
print("🖥️  MiniMax Browser - 有头模式快速使用")
print("=" * 80)

print("""
📖 使用方法:

1️⃣  首次登录 (需要手动操作):
   
   python3 scripts/browser_interactive.py --init --headed
   
   浏览器窗口会打开:
   - 手动访问你想登录的网站
   - 手动登录你的账号
   - 保持浏览器打开
   - 按 Ctrl+C 退出
   - 会自动保存 cookies

2️⃣  恢复登录状态:
   
   python3 scripts/browser_interactive.py --init --session github
   
   自动加载 cookies，恢复登录状态

3️⃣  自动操作 (有头/无头):
   
   python3 scripts/browser_interactive.py -u https://github.com
   python3 scripts/browser_interactive.py -a "点击某个按钮"
   python3 scripts/browser_interactive.py -e "提取页面内容"

4️⃣  保存/加载 Session:
   
   # 保存当前登录状态
   python3 scripts/browser_interactive.py --save-session
   
   # 列出所有 sessions
   python3 scripts/browser_interactive.py --sessions

💡 常用命令组合:

# GitHub 登录场景
python3 scripts/browser_interactive.py --init --headed --session github
# → 手动登录 GitHub
# → Ctrl+C 保存

# 后续自动恢复登录
python3 scripts/browser_interactive.py --init --session github
# → 自动恢复登录状态

# 任何网站登录
python3 scripts/browser_interactive.py --init --headed
# → 手动操作浏览器
# → 登录任意网站

📁 Session 存储位置:
   ~/.stagehand/sessions/{session_name}/
   ├── cookies.json   # Cookies
   └── session.json  # Session 状态

🔧 当前配置:
   API Base: https://api.minimaxi.com/v1
   Headless: False (有头模式)
""")

print("=" * 80)
