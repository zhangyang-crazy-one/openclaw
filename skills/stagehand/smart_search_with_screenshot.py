#!/usr/bin/env python3
"""
智能搜索演示 - 带截图验证
截图保存在 ~/stagehand_screenshots/
"""

import asyncio
import json
import os
import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def main():
    SCREENSHOT_DIR = os.path.expanduser("~/stagehand_screenshots")
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    print("=" * 80)
    print("📸 智能搜索 + 截图验证")
    print("=" * 80)
    print(f"\n📁 截图保存目录: {SCREENSHOT_DIR}")
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    
    # 1. 启动
    print("\n🚀 Step 1: 启动浏览器...")
    r = await browser.initialize(load_cookies=True)
    print(f"   ✅ {r.get('message')}")
    
    # 2. 截图 - 初始状态
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"{SCREENSHOT_DIR}/step1_initial_{timestamp}.png"
    
    await browser.page.screenshot(path=screenshot_path)
    print(f"   📸 截图: step1_initial_{timestamp}.png")
    
    # 3. 导航到 GitHub
    print("\n🌐 Step 2: 访问 GitHub...")
    r = await browser.navigate("https://github.com")
    await asyncio.sleep(2)
    screenshot_path = f"{SCREENSHOT_DIR}/step2_github_home_{timestamp}.png"
    await browser.page.screenshot(path=screenshot_path)
    print(f"   ✅ {r.get('title')}")
    print(f"   📸 截图: step2_github_home_{timestamp}.png")
    
    # 4. 搜索
    print("\n🔍 Step 3: 搜索 openclaw/openclaw...")
    search_url = "https://github.com/search?q=openclaw%2Fopenclaw&type=repositories"
    r = await browser.navigate(search_url)
    await asyncio.sleep(3)
    screenshot_path = f"{SCREENSHOT_DIR}/step3_search_results_{timestamp}.png"
    await browser.page.screenshot(path=screenshot_path)
    print(f"   ✅ 搜索完成")
    print(f"   📸 截图: step3_search_results_{timestamp}.png")
    
    # 5. 提取信息
    print("\n📊 Step 4: 提取搜索结果...")
    r = await browser.extract("提取页面标题和前3个仓库名称")
    data = r.get('data', {})
    print(f"   📊 {json.dumps(data, ensure_ascii=False)[:200]}...")
    
    # 6. 点击进入仓库
    print("\n👆 Step 5: 点击进入 openclaw/openclaw...")
    try:
        await browser.page.click('a[href="/openclaw/openclaw"]', timeout=10000)
        await asyncio.sleep(3)
        screenshot_path = f"{SCREENSHOT_DIR}/step5_repo_page_{timestamp}.png"
        await browser.page.screenshot(path=screenshot_path)
        print(f"   ✅ 进入仓库: {browser.page.url}")
        print(f"   📸 截图: step5_repo_page_{timestamp}.png")
    except Exception as e:
        print(f"   ⚠️ 点击失败")
        screenshot_path = f"{SCREENSHOT_DIR}/step5_error_{timestamp}.png"
        await browser.page.screenshot(path=screenshot_path)
    
    # 7. 提取仓库信息
    if "github.com/openclaw" in browser.page.url:
        print("\n📄 Step 6: 提取仓库信息...")
        r = await browser.extract("提取仓库名称、描述、stars数量")
        print(f"   📊 {json.dumps(r.get('data', {}), ensure_ascii=False)[:200]}")
    
    # 8. 保存
    print("\n💾 Step 7: 保存 cookies...")
    r = await browser.save_session()
    print(f"   ✅ {r.get('message')}")
    
    await browser.close()
    
    print("\n" + "=" * 80)
    print("✅ 演示完成!")
    print("=" * 80)
    print(f"\n📁 所有截图保存在: {SCREENSHOT_DIR}")
    print("\n📸 截图列表:")
    os.system(f"ls -la {SCREENSHOT_DIR}/*.png | tail -10")


if __name__ == "__main__":
    asyncio.run(main())
