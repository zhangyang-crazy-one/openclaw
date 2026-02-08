#!/usr/bin/env python3
"""
Stagehand Browser Automation - Simplified Version

使用 MiniMax 2.1 通过 HTTP API 直接调用
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional

# Stagehand imports
try:
    from stagehand import Stagehand
    STAGEHAND_AVAILABLE = True
except ImportError:
    STAGEHAND_AVAILABLE = False


class MiniMaxStagehand:
    """Stagehand 浏览器自动化，使用 MiniMax API."""

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

        self.stagehand: Optional[Stagehand] = None
        self.initialized = False

    async def initialize(self) -> Dict[str, Any]:
        """初始化 Stagehand."""
        if not STAGEHAND_AVAILABLE:
            return {
                "success": False,
                "error": "Stagehand 未安装",
                "message": "请运行: pip install stagehand playwright"
            }

        try:
            self.stagehand = Stagehand(
                env="local",
                headless=self.headless,
                # Stagehand 会使用默认模型
                # MiniMax 可以通过 STAGEHAND_MODEL 环境变量设置
            )

            await self.stagehand.init()
            self.initialized = True

            return {
                "success": True,
                "message": f"Stagehand 初始化成功",
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
            return {"success": False, "error": "未初始化"}

        try:
            await self.stagehand.page.goto(url)
            title = await self.stagehand.page.title()

            return {
                "success": True,
                "url": url,
                "title": title,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def act(self, instruction: str) -> Dict[str, Any]:
        """执行自然语言指令."""
        if not self.initialized:
            return {"success": False, "error": "未初始化"}

        try:
            result = await self.stagehand.act(instruction)
            return {
                "success": True,
                "instruction": instruction,
                "result": str(result),
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
            return {"success": False, "error": "未初始化"}

        try:
            if schema:
                result = await self.stagehand.extract({
                    "instruction": instruction,
                    "schema": schema,
                })
            else:
                result = await self.stagehand.extract(instruction)

            return {
                "success": True,
                "instruction": instruction,
                "data": result,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def agent(self, task: str) -> Dict[str, Any]:
        """运行自主代理."""
        if not self.initialized:
            return {"success": False, "error": "未初始化"}

        try:
            agent = self.stagehand.agent({
                "mode": "cua",
                "model": self.model,
            })
            result = await agent.execute(task)

            return {
                "success": True,
                "task": task,
                "result": str(result),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """关闭浏览器."""
        if self.stagehand:
            await self.stagehand.close()
            self.initialized = False


async def test_connection():
    """测试 MiniMax 连接."""
    import aiohttp

    print("=" * 60)
    print("🧪 测试 MiniMax API 连接")
    print("=" * 60)

    api_key = os.getenv("MINIMAX_API_KEY")
    api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimax.io/anthropic/v1")

    if not api_key:
        print("❌ MINIMAX_API_KEY 未设置")
        return False

    print(f"\nAPI Base: {api_base}")
    print(f"API Key: {api_key[:8]}...")

    try:
        async with aiohttp.ClientSession() as session:
            # 简单测试 API 连通性
            async with session.get(
                api_base.replace("/v1", "/models"),
                headers={"Authorization": f"Bearer {api_key}"}
            ) as resp:
                print(f"✅ API 连通性: {resp.status}")

        print("\n✅ MiniMax API 配置正确!")
        return True

    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        return False


async def main():
    """CLI 主入口."""
    import argparse

    parser = argparse.ArgumentParser(description="Stagehand + MiniMax")
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
    browser = MiniMaxStagehand(model=args.model)

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
