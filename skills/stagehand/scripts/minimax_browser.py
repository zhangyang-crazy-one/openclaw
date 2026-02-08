#!/usr/bin/env python3
"""
MiniMax Browser Automation - 使用 Playwright + MiniMax API

结合 Playwright 的浏览器控制能力和 MiniMax 2.1 的 AI 理解能力
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from playwright.async_api import async_playwright


class MiniMaxBrowser:
    """浏览器自动化，使用 MiniMax AI."""

    def __init__(
        self,
        model: str = "MiniMax-M2",
        headless: bool = True,
    ):
        self.model = model
        self.headless = headless

        # MiniMax 配置
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.api_base = os.getenv(
            "MINIMAX_API_BASE",
            "https://api.minimax.io/anthropic/v1"
        )

        if not self.api_key:
            raise ValueError("❌ MINIMAX_API_KEY 未设置")

        self.browser = None
        self.context = None
        self.page = None
        self.initialized = False

    async def _call_minimax(self, prompt: str, schema: Optional[Dict] = None) -> Dict:
        """调用 MiniMax API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4000,
        }

        if schema:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                urljoin(self.api_base, "/chat/completions"),
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"content": content}

    async def initialize(self) -> Dict[str, Any]:
        """初始化浏览器."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            self.initialized = True

            return {
                "success": True,
                "message": "浏览器初始化成功",
                "model": self.model,
                "api_base": self.api_base,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"初始化失败: {e}"
            }

    async def navigate(self, url: str) -> Dict[str, Any]:
        """导航到 URL."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            await self.page.goto(url)
            title = await self.page.title()

            # 获取页面内容摘要
            content = await self.page.content()

            return {
                "success": True,
                "url": url,
                "title": title,
                "content_length": len(content),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def act(self, instruction: str) -> Dict[str, Any]:
        """执行自然语言指令."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            # 获取当前页面 HTML
            html = await self.page.content()

            # 使用 MiniMax 分析如何执行指令
            prompt = f"""
当前页面标题: {await self.page.title()}
当前URL: {self.page.url}

请分析以下指令并返回执行步骤:
指令: {instruction}

请用 JSON 格式返回:
{{
    "action": "click|fill|navigate|scroll|wait|etc",
    "selector": "要操作的元素选择器",
    "value": "如果需要填写的值",
    "reason": "为什么选择这个操作"
}}
"""

            result = await self._call_minimax(prompt)
            action = result.get("action", "unknown")
            selector = result.get("selector", "")

            # 执行操作
            if action == "click" and selector:
                await self.page.click(selector)
            elif action == "fill" and selector:
                await self.page.fill(selector, result.get("value", ""))
            elif action == "navigate":
                await self.page.goto(result.get("value", ""))

            return {
                "success": True,
                "instruction": instruction,
                "action": action,
                "analysis": result,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract(
        self,
        instruction: str,
        schema: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """提取结构化数据."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            # 获取页面可见文本
            content = await self.page.evaluate("""
                Array.from(document.querySelectorAll('body *'))
                    .filter(el => el.offsetParent !== null)
                    .map(el => el.innerText.trim())
                    .filter(text => text.length > 0)
                    .join('\\n')
            """)

            prompt = f"""
从以下页面内容中提取信息:
指令: {instruction}

页面内容:
{content[:8000]}

请提取并用 JSON 格式返回:
"""

            if schema:
                prompt += f"按照此 schema 格式: {json.dumps(schema)}\n"

            result = await self._call_minimax(prompt, schema={"type": "object"})

            return {
                "success": True,
                "instruction": instruction,
                "data": result,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def observe(self, instruction: str) -> Dict[str, Any]:
        """观察页面元素."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            # 获取所有可交互元素
            elements = await self.page.evaluate("""
                const elements = [];
                document.querySelectorAll('a, button, input, select, textarea, [onclick], [role], [tabindex]').forEach(el => {
                    if (el.offsetParent !== null) {
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            text: el.innerText.substring(0, 100),
                            href: el.href || null,
                            placeholder: el.placeholder || null,
                            class: el.className.substring(0, 50),
                        });
                    }
                });
                return elements.slice(0, 20);
            """)

            return {
                "success": True,
                "instruction": instruction,
                "elements": elements,
                "count": len(elements),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def agent(self, task: str) -> Dict[str, Any]:
        """运行自主代理完成复杂任务."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            steps = []

            # 分析任务
            prompt = f"""
分析以下浏览器任务并规划步骤:
任务: {task}

请用 JSON 格式返回步骤数组:
[
    {{"step": 1, "action": "navigate|click|fill|extract", "description": "步骤描述"}}
]
"""

            plan = await self._call_minimax(prompt)
            steps = plan if isinstance(plan, list) else plan.get("steps", [])

            results = []
            for step in steps[:10]:  # 最多10步
                action = step.get("action")
                desc = step.get("description", "")

                if action == "navigate":
                    url = step.get("value", "")
                    await self.page.goto(url)
                    results.append({"step": step.get("step"), "action": "navigate", "url": url})

                elif action == "extract":
                    instruction = step.get("description", "")
                    data = await self.extract(instruction)
                    results.append({"step": step.get("step"), "action": "extract", "data": data})

            return {
                "success": True,
                "task": task,
                "plan": plan,
                "results": results,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """关闭浏览器."""
        if self.browser:
            await self.browser.close()
            self.initialized = False


async def test_connection():
    """测试 MiniMax API 连接."""
    print("=" * 60)
    print("🧪 测试 MiniMax API 连接")
    print("=" * 60)

    api_key = os.getenv("MINIMAX_API_KEY")
    api_base = os.getenv("MINIMAX_API_BASE")

    if not api_key:
        print("❌ MINIMAX_API_KEY 未设置")
        return False

    print(f"\nAPI Key: {api_key[:20]}...")
    print(f"API Base: {api_base}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                urljoin(api_base, "/chat/completions"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "MiniMax-M2",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10,
                }
            )

            if response.status_code == 200:
                print("✅ API 连接成功!")
                return True
            else:
                print(f"❌ API 错误: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


async def main():
    """CLI 主入口."""
    import argparse

    parser = argparse.ArgumentParser(description="MiniMax Browser Automation")
    parser.add_argument("--test", action="store_true", help="测试连接")
    parser.add_argument("--init", action="store_true", help="初始化浏览器")
    parser.add_argument("--navigate", "-u", help="导航到 URL")
    parser.add_argument("--act", "-a", help="执行操作")
    parser.add_argument("--extract", "-e", help="提取数据")
    parser.add_argument("--model", "-m", default="MiniMax-M2", help="模型名称")

    args = parser.parse_args()

    # 测试连接
    if args.test:
        await test_connection()
        return

    # 初始化
    browser = MiniMaxBrowser(model=args.model)

    result = await browser.initialize()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("success"):
        if args.navigate:
            result = await browser.navigate(args.navigate)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.act:
            result = await browser.act(args.act)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.extract:
            result = await browser.extract(args.extract)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
