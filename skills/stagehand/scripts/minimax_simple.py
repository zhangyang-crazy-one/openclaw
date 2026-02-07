#!/usr/bin/env python3
"""
MiniMax Browser Automation - Simplified & Stable Version

支持国内版 MiniMax API: https://api.minimaxi.com
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import httpx
from playwright.async_api import async_playwright


class MiniMaxBrowser:
    """使用 MiniMax AI 的浏览器自动化."""

    def __init__(
        self,
        model: str = "MiniMax-M2",
        headless: bool = True,
    ):
        self.model = model
        self.headless = headless

        # MiniMax 配置 - 国内版
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")

        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY 未设置")

        self.browser = None
        self.context = None
        self.page = None
        self.initialized = False

    async def _call_minimax(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        """调用 MiniMax API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def initialize(self) -> Dict[str, Any]:
        """初始化浏览器."""
        try:
            playwright = await async_playwright().start()
            
            chrome_path = os.getenv("CHROME_PATH") or "/usr/bin/google-chrome"
            
            if os.path.exists(chrome_path):
                self.browser = await playwright.chromium.launch(
                    headless=self.headless,
                    executable_path=chrome_path,
                )
            else:
                self.browser = await playwright.chromium.launch(headless=self.headless)
            
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.initialized = True

            return {"success": True, "message": "浏览器初始化成功", "model": self.model}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def navigate(self, url: str) -> Dict[str, Any]:
        """导航到 URL."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            return {
                "success": True,
                "url": url,
                "title": await self.page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def act(self, instruction: str) -> Dict[str, Any]:
        """执行自然语言指令."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            page_info = {
                "title": await self.page.title(),
                "url": self.page.url,
            }
            
            # 获取页面链接
            links = await self.page.locator("a").all()
            link_count = len(links)

            messages = [
                {"role": "system", "content": "You are a browser automation assistant."},
                {
                    "role": "user",
                    "content": f"""Page info:
Title: {page_info['title']}
URL: {page_info['url']}
Links: {link_count}

Instruction: {instruction}

Respond with JSON:
{{"action": "scroll|click_nth_link|wait", "value": "scroll_amount|link_index"}}
"""
                }
            ]

            response = await self._call_minimax(messages)
            
            # 解析响应
            try:
                plan = json.loads(response)
            except:
                plan = {"action": "wait", "value": "0"}

            action = plan.get("action", "")
            
            if action == "scroll":
                await self.page.evaluate(f"window.scrollBy(0, {plan.get('value', 300)})")
            elif action.startswith("click_nth_link"):
                idx = int(plan.get("value", 0))
                links = await self.page.locator("a").all()
                if idx < len(links):
                    await links[idx].click()

            return {"success": True, "instruction": instruction, "action": action, "plan": plan}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract(self, instruction: str) -> Dict[str, Any]:
        """提取页面文本."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            # 获取页面文本
            content = await self.page.evaluate("document.body.innerText")
            
            messages = [
                {"role": "system", "content": "You are a data extraction assistant. Respond with JSON."},
                {
                    "role": "user",
                    "content": f"""Extract information based on:

Instruction: {instruction}

Page content (first 4000 chars):
{content[:4000]}

Return JSON:
{{"extracted": "...", "summary": "..."}}
"""
                }
            ]

            response = await self._call_minimax(messages)
            
            try:
                data = json.loads(response)
            except:
                data = {"extracted": response}

            return {"success": True, "instruction": instruction, "data": data}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def observe(self) -> Dict[str, Any]:
        """观察页面元素."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            links = await self.page.locator("a").count()
            buttons = await self.page.locator("button").count()
            inputs = await self.page.locator("input").count()
            headings = await self.page.locator("h1, h2, h3").count()
            
            return {
                "success": True,
                "elements": {
                    "links": links,
                    "buttons": buttons,
                    "inputs": inputs,
                    "headings": headings,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """关闭浏览器."""
        if self.browser:
            await self.browser.close()
            self.initialized = False


async def test():
    print("=" * 60)
    print("MiniMax Browser Test")
    print("=" * 60)
    
    browser = MiniMaxBrowser()
    
    # Init
    result = await browser.initialize()
    print(f"\n1. {result.get('message')}")
    
    # Navigate
    result = await browser.navigate("https://example.com")
    print(f"2. Title: {result.get('title')}")
    
    # Observe
    result = await browser.observe()
    print(f"3. Elements: {result.get('elements')}")
    
    # Extract
    result = await browser.extract("What is this page about?")
    print(f"4. Extracted: {result.get('data', {})}")
    
    await browser.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(test())
