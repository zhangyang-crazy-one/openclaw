#!/usr/bin/env python3
"""
MiniMax Browser Automation - 基于 Playwright + MiniMax API

支持国内版 MiniMax API: https://api.minimaxi.com

功能:
- 🧭 导航到网页
- 🎯 执行自然语言操作
- 🔍 提取结构化数据  
- 👁️ 观察页面元素
- 🤖 自主代理工作流
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from playwright.async_api import async_playwright


class MiniMaxBrowser:
    """使用 MiniMax AI 的浏览器自动化."""

    def __init__(
        self,
        model: str = "MiniMax-M2",
        headless: bool = True,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.model = model
        self.headless = headless

        # MiniMax 配置 - 支持国内版和国际版
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.api_base = api_base or os.getenv(
            "MINIMAX_API_BASE",
            "https://api.minimaxi.com/v1"  # 国内版默认地址
        )

        if not self.api_key:
            raise ValueError("❌ MINIMAX_API_KEY 未设置")

        self.browser = None
        self.context = None
        self.page = None
        self.initialized = False

    async def _call_minimax(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
    ) -> str:
        """调用 MiniMax API (国内版: api.minimaxi.com)."""
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
            result = response.json()

            return result["choices"][0]["message"]["content"]

    def _build_system_prompt(self) -> str:
        """构建系统提示词."""
        return """You are a helpful browser automation assistant. 
Given a webpage and user instructions, you must:
1. Analyze the page structure
2. Provide clear action plans
3. Extract requested information

Always respond with valid JSON."""

    async def initialize(self) -> Dict[str, Any]:
        """初始化浏览器."""
        try:
            playwright = await async_playwright().start()
            
            # 使用系统 Chrome
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

            return {
                "success": True,
                "message": "✅ 浏览器初始化成功",
                "model": self.model,
                "api_base": self.api_base,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 初始化失败: {e}"
            }

    async def navigate(self, url: str) -> Dict[str, Any]:
        """导航到 URL."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            title = await self.page.title()

            # 获取页面内容
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
            # 获取当前页面信息
            page_info = {
                "title": await self.page.title(),
                "url": self.page.url,
            }

            # 获取页面可点击元素
            elements = await self._get_clickable_elements()

            # 构建指令
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {
                    "role": "user",
                    "content": f"""
页面信息:
- 标题: {page_info['title']}
- URL: {page_info['url']}

可交互元素: {json.dumps(elements[:10], ensure_ascii=False)}

指令: {instruction}

请分析如何执行这个指令，并返回 JSON:
{{
    "action": "click|fill|hover|scroll|press|wait",
    "selector": "元素选择器 (CSS selector)",
    "value": "要填写的值 (如果需要)",
    "reason": "为什么选择这个操作"
}}
""",
                }
            ]

            result = await self._call_minimax(messages)
            
            # 解析 JSON 响应
            try:
                action_plan = json.loads(result)
            except json.JSONDecodeError:
                # 尝试提取 JSON
                start = result.find("{")
                end = result.rfind("}") + 1
                action_plan = json.loads(result[start:end])

            # 执行操作
            action = action_plan.get("action", "")
            selector = action_plan.get("selector", "")

            if action == "click" and selector:
                await self.page.click(selector)
            elif action == "fill" and selector:
                await self.page.fill(selector, action_plan.get("value", ""))
            elif action == "hover":
                await self.page.hover(selector)
            elif action == "scroll":
                await self.page.evaluate(f"window.scrollBy(0, {action_plan.get('value', 300)})")
            elif action == "press":
                await self.page.press(selector or "body", action_plan.get("value", "Enter"))

            return {
                "success": True,
                "instruction": instruction,
                "action": action,
                "selector": selector,
                "analysis": action_plan,
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
                () => {
                    const text = [];
                    document.querySelectorAll('h1, h2, h3, p, li, td, th, div, span, a').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.top >= 0 && rect.left >= 0 && 
                            rect.bottom <= window.innerHeight && rect.right <= window.innerWidth) {
                            const t = el.innerText?.trim();
                            if (t && t.length > 0 && t.length < 500) text.push(t);
                        }
                    });
                    return text.slice(0, 100).join('\\n');
                }
            """)

            # 构建提取指令
            schema_hint = ""
            if schema:
                schema_hint = f"\n请按照此 schema 格式返回:\n{json.dumps(schema, ensure_ascii=False)}"

            messages = [
                {"role": "system", "content": "You are a data extraction assistant. Always respond with valid JSON."},
                {
                    "role": "user",
                    "content": f"""
从以下页面内容中提取信息:

{content[:6000]}

提取要求: {instruction}{schema_hint}

请返回 JSON:
{{
    "data": {{提取的数据}},
    "summary": "提取摘要"
}}
""",
                }
            ]

            result = await self._call_minimax(messages)

            try:
                extracted = json.loads(result)
            except json.JSONDecodeError:
                start = result.find("{")
                end = result.rfind("}") + 1
                extracted = json.loads(result[start:end])

            return {
                "success": True,
                "instruction": instruction,
                "data": extracted,
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
                const els = [];
                document.querySelectorAll('a, button, input, select, textarea, [role], [onclick], [tabindex]').forEach(el => {
                    if (el.offsetParent !== null) {
                        els.push({
                            tag: el.tagName.toLowerCase(),
                            text: el.innerText?.substring(0, 80)?.trim(),
                            href: el.href || null,
                            placeholder: el.placeholder || null,
                            type: el.type || null,
                            class: el.className.substring(0, 40),
                            selector: getCSSSelector(el)
                        });
                    }
                });
                return els.slice(0, 30);

                function getCSSSelector(el) {
                    if (el.id) return '#' + el.id;
                    if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
                    let path = el.tagName.toLowerCase();
                    if (el.className && typeof el.className === 'string') {
                        path += '.' + el.className.split(' ')[0];
                    }
                    return path;
                }
            """)

            # 使用 AI 分析元素
            messages = [
                {"role": "system", "content": "You are a UI analyst."},
                {
                    "role": "user",
                    "content": f"""
分析这些页面元素:

{json.dumps(elements[:20], ensure_ascii=False)}

用户需求: {instruction}

返回 JSON:
{{
    "relevant_elements": [符合需求的元素索引列表],
    "description": "页面结构描述"
}}
""",
                }
            ]

            ai_analysis = await self._call_minimax(messages)

            return {
                "success": True,
                "instruction": instruction,
                "elements": elements,
                "analysis": ai_analysis,
                "count": len(elements),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def agent(self, task: str) -> Dict[str, Any]:
        """运行自主代理完成复杂任务."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}

        try:
            results = []
            current_url = self.page.url

            # 分析任务并规划步骤
            messages = [
                {"role": "system", "content": "You are a task planning assistant."},
                {
                    "role": "user",
                    "content": f"""
当前页面: {current_url}
任务: {task}

请规划执行步骤，返回 JSON:
[
    {{"step": 1, "action": "navigate|click|fill|extract", "description": "步骤描述", "value": "URL或选择器"}}
]
最多 5 个步骤。
""",
                }
            ]

            plan_str = await self._call_minimax(messages)

            try:
                plan = json.loads(plan_str)
            except json.JSONDecodeError:
                start = plan_str.find("[")
                end = plan_str.rfind("]") + 1
                plan = json.loads(plan_str[start:end])

            # 执行计划
            for step in plan[:5]:
                step_num = step.get("step", 0)
                action = step.get("action", "")
                desc = step.get("description", "")
                value = step.get("value", "")

                if action == "navigate" and value:
                    await self.page.goto(value)
                    results.append({
                        "step": step_num,
                        "action": "navigate",
                        "url": value,
                        "title": await self.page.title(),
                    })

                elif action == "click" and value:
                    try:
                        await self.page.click(value)
                        results.append({"step": step_num, "action": "click", "selector": value})
                    except Exception as e:
                        results.append({"step": step_num, "action": "click", "error": str(e)})

                elif action == "extract":
                    data = await self.extract(desc)
                    results.append({"step": step_num, "action": "extract", "data": data})

            return {
                "success": True,
                "task": task,
                "plan": plan,
                "results": results,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_clickable_elements(self) -> List[Dict]:
        """获取可点击元素列表."""
        if not self.page:
            return []

        return await self.page.evaluate("""
            const els = [];
            document.querySelectorAll('a, button, [role="button"], [onclick]').forEach(el => {
                if (el.offsetParent !== null) {
                    els.push({
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText?.substring(0, 50)?.trim(),
                        href: el.href || null,
                        selector: getCSSSelector(el)
                    });
                }
            });
            return els.slice(0, 15);

            function getCSSSelector(el) {
                if (el.id) return '#' + el.id;
                let path = el.tagName.toLowerCase();
                if (el.className && typeof el.className === 'string') {
                    path += '.' + el.className.split(' ')[0];
                }
                return path;
            }
        """)

    async def close(self):
        """关闭浏览器."""
        if self.browser:
            await self.browser.close()
            self.initialized = False


# ============ CLI 界面 ============

async def main():
    """CLI 主入口."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MiniMax Browser Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --test                    # 测试 API 连接
  %(prog)s --init                   # 初始化浏览器
  %(prog)s -u https://example.com   # 导航到网页
  %(prog)s -a "点击登录按钮"         # 执行操作
  %(prog)s -e "提取所有标题"         # 提取数据
  %(prog)s --agent "完成注册流程"     # 运行自主代理
        """
    )
    parser.add_argument("--test", action="store_true", help="测试 API 连接")
    parser.add_argument("--init", action="store_true", help="初始化浏览器")
    parser.add_argument("--navigate", "-u", help="导航到 URL")
    parser.add_argument("--act", "-a", help="执行自然语言操作")
    parser.add_argument("--extract", "-e", help="提取数据")
    parser.add_argument("--agent", "--workflow", dest="agent", help="运行自主代理")
    parser.add_argument("--model", "-m", default="MiniMax-M2", help="模型名称")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")

    args = parser.parse_args()

    # 测试 API 连接
    if args.test:
        await test_connection()
        return

    # 创建浏览器实例
    browser = MiniMaxBrowser(
        model=args.model,
        headless=not args.headed,
    )

    # 初始化
    result = await browser.initialize()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("success"):
        # 执行命令
        if args.navigate:
            result = await browser.navigate(args.navigate)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.act:
            result = await browser.act(args.act)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.extract:
            result = await browser.extract(args.extract)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.agent:
            result = await browser.agent(args.agent)
            print(json.dumps(result, indent=2, ensure_ascii=False))

    await browser.close()


async def test_connection():
    """测试 MiniMax API 连接."""
    import sys

    print("=" * 60)
    print("🧪 测试 MiniMax API 连接")
    print("=" * 60)

    api_key = os.getenv("MINIMAX_API_KEY")
    api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")

    if not api_key:
        print("❌ MINIMAX_API_KEY 未设置")
        print("\n请设置环境变量:")
        print('  export MINIMAX_API_KEY="your-api-key"')
        print('  export MINIMAX_API_BASE="https://api.minimaxi.com/v1"')
        sys.exit(1)

    print(f"\nAPI Key: {api_key[:15]}...")
    print(f"API Base: {api_base}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "MiniMax-M2",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 10,
                }
            )

            if response.status_code == 200:
                print("\n✅ API 连接成功!")
                print(f"   响应: {response.json()['choices'][0]['message']['content']}")
            else:
                print(f"\n❌ API 错误: {response.status_code}")
                print(f"   {response.text}")

    except Exception as e:
        print(f"\n❌ 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
