#!/usr/bin/env python3
"""
MiniMax Browser - Keep Open Mode

浏览器会保持打开，直到你按 Ctrl+C
会自动保存 cookies 和 session
"""

import asyncio
import sys
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def main():
    print("=" * 80)
    print("🖥️  MiniMax Browser - 保持打开模式")
    print("=" * 80)
    print()
    print("💡 使用说明:")
    print("   1. 浏览器窗口已经打开")
    print("   2. 手动操作浏览器 (访问网站、登录等)")
    print("   3. 按 Ctrl+C 保存 cookies 并退出")
    print()
    print("📁 Session: github")
    print("📍 URL: https://github.com (如果没自动导航)")
    print()
    print("=" * 80)
    
    # 创建浏览器 (有头模式)
    browser = MiniMaxBrowserInteractive(
        headless=False,  # 有头模式！
        session_name="github"
    )
    
    # 初始化
    print("\n🚀 正在启动浏览器...")
    r = await browser.initialize(load_cookies=False)
    
    if not r.get('success'):
        print(f"❌ 初始化失败: {r.get('error')}")
        return
    
    print(f"✅ {r.get('message')}")
    
    # 导航到 GitHub
    print("\n🌐 正在导航到 GitHub...")
    r = await browser.navigate("https://github.com")
    print(f"✅ 标题: {r.get('title')}")
    
    print("\n" + "=" * 80)
    print("🛑 浏览器已打开!")
    print("   - 你现在可以手动操作浏览器")
    print("   - 访问需要登录的网站")
    print("   - 登录你的账号")
    print()
    print("💾 按 Ctrl+C 保存 cookies 并退出")
    print("=" * 80)
    
    # 保持打开
    try:
        while True:
            await asyncio.sleep(1)
            # 实时显示当前状态
            if browser.page:
                try:
                    status = f"📍 {browser.page.url[:50]}"
                    sys.stdout.write(f"\r{status}")
                    sys.stdout.flush()
                except:
                    pass
    except KeyboardInterrupt:
        print("\n\n💾 保存 session...")
        r = await browser.save_session()
        print(f"✅ {r.get('message')}")
        print(f"   Cookies: {r.get('cookies_count')} items")
        print()
        print("👋 下次使用: python3 scripts/browser_interactive.py --init --session github")
        print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
