#!/usr/bin/env python3
"""
MiniMax Browser - True Automation Demo

真正的自动化操作演示：
1. 打开浏览器
2. 访问 GitHub
3. 检查登录状态
4. 如果未登录，显示登录
5. 执行实际操作
6. 等待观察
"""

import asyncio
import json
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def true_automation_demo():
    """真正的自动化演示"""
    
    print("=" * 80)
    print("🤖 真正的浏览器自动化演示")
    print("=" * 80)
    print()
    print("💡 我会:")
    print("   1. 打开浏览器")
    print("   2. 访问 GitHub 并检查登录状态")
    print("   3. 如果未登录，演示登录流程")
    print("   4. 执行实际操作（滚动、点击等）")
    print("   5. 提取页面数据")
    print("   6. 等待你观察")
    print()
    print("🛑 浏览器打开后请观察，不用输入任何东西")
    print("   按 Ctrl+C 可以随时停止")
    print("=" * 80)
    
    browser = MiniMaxBrowserInteractive(
        headless=False,  # 有头模式！
        session_name="main"
    )
    
    # 1. 打开浏览器
    print("\n🔄 Step 1: 打开浏览器...")
    r = await browser.initialize(load_cookies=True)
    print(f"   ✅ 浏览器已打开")
    print(f"   📁 Session: main")
    print(f"   🍪 Cookies: 已加载")
    
    # 2. 访问 GitHub
    print("\n🔄 Step 2: 访问 GitHub...")
    r = await browser.navigate("https://github.com")
    print(f"   ✅ 已访问: {r.get('title')}")
    print(f"   📍 {r.get('url')}")
    
    # 等待加载
    await asyncio.sleep(2)
    
    # 3. 检查登录状态
    print("\n🔄 Step 3: 检查登录状态...")
    page_text = await browser.page.evaluate("document.body.innerText.substring(0, 1500)")
    
    if "Sign out" in page_text or "退出" in page_text:
        print("   ✅ GitHub 已登录!")
        logged_in = True
    elif "Sign in" in page_text:
        print("   ⚠️ GitHub 未登录")
        print("   🔄 演示登录流程...")
        logged_in = False
    else:
        print("   ❓ 状态不确定，请查看浏览器")
        logged_in = None
    
    # 4. 执行实际操作
    print("\n🔄 Step 4: 执行实际操作...")
    
    # 滚动
    print("   📜 向下滚动...")
    await browser.page.evaluate("window.scrollBy(0, 500)")
    await asyncio.sleep(1)
    
    # 点击某个元素 (比如 Features)
    print("   👆 点击 Features 链接...")
    try:
        await browser.page.click("a:has-text('Features')", timeout=5000)
        await asyncio.sleep(2)
        print("   ✅ 点击成功")
    except Exception as e:
        print(f"   ⚠️ 点击失败: {e}")
    
    # 5. 提取数据
    print("\n🔄 Step 5: 提取页面数据...")
    r = await browser.extract("提取页面标题和主要内容")
    data = r.get('data', {})
    print(f"   📊 数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
    
    # 6. 访问 Taobao
    print("\n🔄 Step 6: 访问 Taobao...")
    r = await browser.navigate("https://www.taobao.com")
    print(f"   ✅ 已访问: {await browser.page.title()}")
    
    await asyncio.sleep(3)
    
    # 检查 Taobao 登录状态
    print("\n🔄 Step 7: 检查 Taobao 登录状态...")
    taobao_text = await browser.page.evaluate("document.body.innerText.substring(0, 1000)")
    
    if "我的淘宝" in taobao_text or "已登录" in taobao_text:
        print("   ✅ Taobao 已登录!")
    elif "登录" in taobao_text and "免费注册" in taobao_text:
        print("   ⚠️ Taobao 未登录")
        print("   💡 请在浏览器中手动登录")
    else:
        print("   ❓ 请查看浏览器确认状态")
    
    # 7. 保存
    print("\n🔄 Step 8: 保存 Session...")
    r = await browser.save_session()
    print(f"   💾 {r.get('message')}")
    print(f"   🍪 {r.get('cookies_count')} cookies")
    
    print("\n" + "=" * 80)
    print("✅ 自动化演示完成！")
    print("=" * 80)
    print()
    print("💡 观察结果:")
    print("   • 浏览器是否打开？")
    print("   • GitHub 登录状态？")
    print("   • Taobao 登录状态？")
    print("   • 滚动和点击操作是否执行？")
    print()
    print("🛑 浏览器保持打开，请查看！")
    print("   按 Ctrl+C 保存并退出")
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
        print("\n\n💾 保存并退出...")
        r = await browser.save_session()
        print(f"   {r.get('message')}")
        await browser.close()
        print("\n👋 已保存退出")


if __name__ == "__main__":
    try:
        asyncio.run(true_automation_demo())
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
