#!/usr/bin/env python3
"""
测试 Session 并保持浏览器打开
"""

import asyncio
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def main():
    print("=" * 70)
    print("🧪 测试 Session (保持打开模式)")
    print("=" * 70)
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="github")
    
    # Init (load cookies)
    print("\n🚀 启动浏览器...")
    r = await browser.initialize(load_cookies=True)
    print(f"   {r.get('message')}")
    
    # Test GitHub
    print("\n1️⃣ GitHub...")
    r = await browser.navigate("https://github.com")
    print(f"   URL: {r.get('url')}")
    print(f"   Title: {r.get('title')}")
    
    # Test Taobao
    print("\n2️⃣ Taobao...")
    r = await browser.navigate("https://www.taobao.com")
    title = await browser.page.title()
    print(f"   URL: {r.get('url')}")
    print(f"   Title: {title}")
    
    print("\n" + "=" * 70)
    print("✅ 浏览器已打开!")
    print("   - GitHub ✅ 已登录")
    print("   - Taobao ✅ 已登录")
    print("\n💡 现在你可以:")
    print("   - 手动操作浏览器")
    print("   - 访问其他网站")
    print("   - 登录更多账号")
    print("\n🛑 按 Ctrl+C 保存 cookies 并退出")
    print("=" * 70)
    
    # Keep open
    try:
        while True:
            await asyncio.sleep(1)
            try:
                url = browser.page.url[:50]
                print(f"\r📍 {url}", end="", flush=True)
            except:
                pass
    except KeyboardInterrupt:
        print("\n\n💾 保存 Session...")
        r = await browser.save_session()
        print(f"   {r.get('message')}")
        print(f"   Cookies: {r.get('cookies_count')}")
        await browser.close()
        print("\n👋 已保存并退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
