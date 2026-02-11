#!/usr/bin/env python3
"""
MiniMax Browser - Real Interactive Mode

真实浏览器自动化 - 你可以看到每一步操作
"""

import asyncio
import json
import sys
from pathlib import Path
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def interactive_session():
    """交互式浏览器会话"""
    
    print("=" * 80)
    print("🖥️  MiniMax Browser - 真实交互模式")
    print("=" * 80)
    print()
    print("💡 特性:")
    print("   • 有头模式 - 你可以看到浏览器操作")
    print("   • 实时显示 - 每步操作都有反馈")
    print("   • 自动保存 - 退出时自动保存 cookies")
    print("   • 长期保持 - 下次打开自动恢复登录")
    print()
    print("📝 使用方法:")
    print("   输入命令:")
    print("     goto <url>      - 访问网站")
    print("     click <描述>     - 点击元素")
    print("     fill <文本>     - 输入文本")
    print("     scroll          - 向下滚动")
    print("     extract         - 提取页面数据")
    print("     status          - 查看当前状态")
    print("     save            - 保存 cookies")
    print("     quit            - 退出")
    print()
    print("=" * 80)
    
    # 创建浏览器
    browser = MiniMaxBrowserInteractive(
        headless=False,  # 有头模式！
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
    
    # 实时显示
    print("\n" + "=" * 80)
    print("✅ 浏览器已就绪！")
    print(f"   📍 {browser.page.url}")
    print("=" * 80)
    
    # 交互循环
    print("\n💬 输入命令 (或 quit 退出):")
    
    commands = {
        "goto": lambda url: browser.navigate(url),
        "navigate": lambda url: browser.navigate(url),
        "click": lambda desc: browser.act(f"点击: {desc}"),
        "fill": lambda text: browser.act(f"输入: {text}"),
        "type": lambda text: browser.act(f"输入: {text}"),
        "scroll": lambda _: browser.act("向下滚动"),
        "down": lambda _: browser.act("向下滚动"),
        "up": lambda _: browser.act("向上滚动"),
        "extract": lambda _: browser.extract("提取页面所有重要信息"),
        "data": lambda _: browser.extract("提取结构化数据"),
        "status": lambda _: asyncio.coroutine(lambda: {"success": True, "url": browser.page.url, "title": browser.page.title}),
        "save": lambda _: browser.save_session(),
        "quit": lambda _: asyncio.coroutine(lambda: {"success": True, "quit": True})(),
    }
    
    try:
        while True:
            try:
                # 显示当前 URL
                current = browser.page.url[:50]
                print(f"\n[{current}...] ", end="", flush=True)
                
                cmd = input().strip().lower()
                
                if cmd in ["quit", "exit", "q"]:
                    break
                
                if not cmd:
                    continue
                
                # 解析命令
                parts = cmd.split(None, 1)
                action = parts[0]
                arg = parts[1] if len(parts) > 1 else ""
                
                # 执行
                if action in commands:
                    print(f"🔄 执行: {cmd}")
                    
                    if action in ["goto", "navigate"] and arg:
                        result = await browser.navigate(arg)
                        print(f"   ✅ 访问: {result.get('url', arg)}")
                    elif action in ["click", "fill", "type", "scroll", "up", "down"]:
                        result = await browser.act(arg if arg else "")
                        method = result.get('action_plan', {}).get('method', action)
                        print(f"   ✅ 动作: {method}")
                    elif action in ["extract", "data"]:
                        result = await browser.extract("页面内容")
                        data = result.get('data', {})
                        print(f"   📊 数据: {json.dumps(data, ensure_ascii=False)[:200]}")
                    elif action == "status":
                        print(f"   📍 URL: {browser.page.url}")
                        print(f"   📄 Title: {browser.page.title}")
                    elif action == "save":
                        result = await browser.save_session()
                        print(f"   💾 {result.get('message')}")
                else:
                    # 当作自然语言指令
                    print(f"🔄 执行: {cmd}")
                    result = await browser.act(cmd)
                    method = result.get('action_plan', {}).get('method', 'unknown')
                    print(f"   ✅ 动作: {method}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"   ❌ 错误: {e}")
                
    except KeyboardInterrupt:
        pass
    
    # 保存并退出
    print("\n\n💾 保存 cookies...")
    r = await browser.save_session()
    print(f"   {r.get('message')}")
    
    await browser.close()
    
    print("\n" + "=" * 80)
    print("👋 会话已保存，下此自动恢复登录状态！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(interactive_session())
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
