#!/usr/bin/env python3
"""
LLM-Driven Smart Browser Automation

使用 LLM 分析页面并智能执行操作
"""

import asyncio
import json
import os
import httpx
from scripts.browser_interactive import MiniMaxBrowserInteractive


class SmartBrowserAutomation:
    """LLM 驱动的智能浏览器自动化"""
    
    def __init__(self):
        # 从配置文件读取
        config_path = os.path.expanduser("~/.minimax_config")
        if os.path.exists(config_path):
            import json
            with open(config_path) as f:
                config = json.load(f)
                self.api_key = config.get("api_key")
                self.api_base = config.get("api_base", "https://api.minimaxi.com/v1")
        else:
            self.api_key = os.getenv("MINIMAX_API_KEY")
            self.api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
        
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "MiniMax-M2",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000
                }
            )
            
            data = response.json()
            # MiniMax API 格式
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            elif "result" in data:
                return data["result"]
            else:
                return str(data)
    
    async def get_page_info(self, page) -> dict:
        """获取页面信息"""
        return await page.evaluate("""
            () => {
                const info = {
                    url: window.location.href,
                    title: document.title,
                    body_text: document.body.innerText.substring(0, 3000)
                };
                
                // 查找搜索框
                const searchInputs = document.querySelectorAll('input[type="search"], input[name="q"]');
                info.search_input = searchInputs.length > 0 ? {
                    selector: searchInputs[0].tagName + (searchInputs[0].id ? '#' + searchInputs[0].id : '') + (searchInputs[0].className ? '.' + searchInputs[0].className.split(' ')[0] : ''),
                    placeholder: searchInputs[0].placeholder || '',
                    visible: searchInputs[0].offsetParent !== null
                } : null;
                
                // 查找仓库链接
                const repoLinks = document.querySelectorAll('a[href*="/openclaw/"]');
                info.repo_links = Array.from(repoLinks).slice(0, 5).map(a => ({
                    href: a.href,
                    text: a.innerText.substring(0, 100)
                }));
                
                return info;
            }
        """)
    
    async def smart_search_github(self, browser, query: str):
        """智能搜索 GitHub"""
        
        print("=" * 80)
        print(f"🔍 智能搜索: {query}")
        print("=" * 80)
        
        # 1. 获取页面信息
        print("\n📊 Step 1: 分析当前页面...")
        page_info = await self.get_page_info(browser.page)
        print(f"   URL: {page_info.get('url', 'unknown')[:60]}")
        
        # 2. 使用 LLM 决定下一步操作
        print("\n🤖 Step 2: LLM 分析...")
        prompt = f"""
当前页面信息:
- URL: {page_info.get('url', '')}
- 标题: {page_info.get('title', '')}
- 搜索框: {page_info.get('search_input', {})}

任务: 在 GitHub 上搜索仓库 "{query}"

请分析并返回 JSON:
{{"action": "search|navigate|click", "selector": "CSS选择器", "value": "搜索词或URL", "reasoning": "为什么选择这个操作"}}
"""
        
        response = await self._call_llm(prompt)
        print(f"   LLM 响应: {response[:200]}...")
        
        # 解析响应
        try:
            action_plan = json.loads(response)
            print(f"   计划: {action_plan}")
        except:
            action_plan = {"action": "navigate", "value": f"https://github.com/search?q={query}&type=repositories"}
        
        # 3. 执行操作
        print(f"\n🎯 Step 3: 执行操作...")
        
        action = action_plan.get("action", "navigate")
        
        if action == "navigate" or action == "search":
            url = action_plan.get("value", f"https://github.com/search?q={query}&type=repositories")
            print(f"   导航到: {url}")
            result = await browser.navigate(url)
            print(f"   ✅ {result.get('title', 'Done')}")
            
        elif action == "click":
            selector = action_plan.get("selector", "")
            print(f"   点击: {selector}")
            try:
                await browser.page.click(selector)
                print(f"   ✅ 点击成功")
            except Exception as e:
                print(f"   ⚠️ 点击失败: {e}")
        
        await asyncio.sleep(3)
        
        # 4. 验证结果
        print(f"\n✅ Step 4: 验证结果...")
        final_info = await self.get_page_info(browser.page)
        print(f"   URL: {final_info.get('url', '')[:60]}")
        
        # 5. 提取结果
        print(f"\n📊 Step 5: 提取数据...")
        extract_prompt = f"""
当前页面标题: {final_info.get('title', '')}
页面内容: {final_info.get('body_text', '')[:1000]}

请提取前 3 个仓库的名称和描述，返回 JSON:
{{"repositories": [{{"name": "owner/repo", "description": "描述"}}]}}
"""
        
        extract_response = await self._call_llm(extract_prompt)
        print(f"   结果: {extract_response[:300]}...")
        
        return final_info


async def main():
    """主函数"""
    
    print("=" * 80)
    print("🤖 LLM 驱动的智能浏览器演示")
    print("=" * 80)
    print()
    print("💡 我会使用 LLM 来:")
    print("   1. 分析当前页面结构")
    print("   2. 智能决定最佳操作")
    print("   3. 精确执行搜索")
    print("   4. 提取搜索结果")
    print()
    print("🔍 搜索目标: openclaw/openclaw 仓库")
    print("=" * 80)
    
    # 创建浏览器
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    
    # 初始化
    print("\n🚀 启动浏览器...")
    r = await browser.initialize(load_cookies=True)
    print(f"   ✅ {r.get('message')}")
    
    # 执行智能搜索
    automation = SmartBrowserAutomation()
    
    await asyncio.sleep(2)
    
    result = await automation.smart_search_github(
        browser,
        "openclaw/openclaw"
    )
    
    # 保存
    print(f"\n💾 保存 cookies...")
    r = await browser.save_session()
    print(f"   ✅ {r.get('message')}")
    
    await browser.close()
    
    print("\n" + "=" * 80)
    print("✅ 演示完成!")
    print("=" * 80)
    print()
    print("💡 请查看 Xvfb 显示确认操作是否执行")


if __name__ == "__main__":
    asyncio.run(main())
