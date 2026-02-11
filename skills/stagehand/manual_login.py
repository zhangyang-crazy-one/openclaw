#!/usr/bin/env python3
"""
Stagehand Manual Login Tool

使用方法:
1. 运行此脚本
2. 在浏览器中登录所有需要的网站
3. 按 Ctrl+C 保存 cookies
4. 之后自动访问时会自动使用登录状态
"""

import asyncio
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def main():
    print("=" * 80)
    print("🔐 Stagehand 手动登录工具")
    print("=" * 80)
    print()
    print("💡 使用方法:")
    print("   1. 浏览器会打开")
    print("   2. 登录所有需要的网站:")
    print("      - GitHub")
    print("      - Taobao")
    print("      - 其他网站...")
    print("   3. 登录完成后")
    print("   4. 按 Ctrl+C 保存 cookies")
    print()
    print("📁 Session 名称: main")
    print("🍪 Cookies 保存位置: ~/.stagehand/sessions/main/")
    print()
    print("=" * 80)
    
    browser = MiniMaxBrowserInteractive(
        headless=False,
        session_name="main"
    )
    
    # 初始化
    print("\n🚀 启动浏览器...")
    r = await browser.initialize(load_cookies=True)
    
    if not r.get('success'):
        print(f"❌ 启动失败: {r.get('error')}")
        return
    
    print(f"✅ {r.get('message')}")
    
    # 访问 GitHub
    print("\n🌐 访问 GitHub...")
    r = await browser.navigate("https://github.com")
    print(f"   ✅ {r.get('title')}")
    
    print()
    print("=" * 80)
    print("✅ 浏览器已打开!")
    print("=" * 80)
    print()
    print("📝 现在请:")
    print("   1. 在浏览器中登录 GitHub")
    print("   2. 在浏览器中登录 Taobao")
    print("   3. 登录任何其他需要的网站")
    print()
    print("🛑 完成后按 Ctrl+C 保存 cookies")
    print("=" * 80)
    
    # 保持打开
    try:
        while True:
            await asyncio.sleep(1)
            try:
                url = browser.page.url[:60]
                print(f"\r📍 {url}", end="", flush=True)
            except:
                pass
    except KeyboardInterrupt:
        print("\n\n💾 保存 cookies...")
        r = await browser.save_session()
        print(f"   ✅ {r.get('message')}")
        print(f"   🍪 {r.get('cookies_count')} cookies")
        await browser.close()
        print()
        print("=" * 80)
        print("✅ 已保存登录状态!")
        print("=" * 80)
        print()
        print("💡 之后可以使用:")
        print("   • keep_open.py - 打开浏览器")
        print("   • smart_search_with_screenshot.py - 自动化操作")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
