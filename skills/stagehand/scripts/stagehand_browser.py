#!/usr/bin/env python3
"""
Stagehand Browser Automation with MiniMax AI

This skill provides AI-powered browser automation using Stagehand framework
with MiniMax 2.1 model for natural language understanding and actions.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Stagehand
try:
    from stagehand import Stagehand, StagehandModel
    from stagehand.schemas import AvailableModel
except ImportError:
    print("ERROR: Stagehand not installed. Run: pip install stagehand")
    sys.exit(1)

# Import MiniMax provider
try:
    from vercel_minimax_ai_provider import minimax, minimaxAnthropic, minimaxOpenAI
    MINIMAX_AVAILABLE = True
except ImportError:
    MINIMAX_AVAILABLE = False
    print("WARNING: MiniMax provider not installed. Run: pnpm add vercel-minimax-ai-provider")


class MiniMaxStagehand:
    """Stagehand browser automation with MiniMax AI integration."""

    def __init__(
        self,
        model: str = "MiniMax-M2",
        headless: bool = True,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.model = model
        self.headless = headless
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.api_base = api_base or os.getenv("MINIMAX_API_BASE", "https://api.minimax.io/v1")

        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY is required. Set it in environment or pass as argument.")

        self.stagehand: Optional[Stagehand] = None
        self.initialized = False

    async def initialize(self) -> Dict[str, Any]:
        """Initialize Stagehand with MiniMax LLM."""
        try:
            # Configure MiniMax client
            if MINIMAX_AVAILABLE:
                # Use MiniMax via Vercel AI SDK provider
                llm_config = {
                    "provider": minimaxOpenAI({
                        "api_key": self.api_key,
                        "base_url": self.api_base,
                    }),
                    "model": self.model,
                }
            else:
                # Fallback to default Stagehand models if MiniMax provider not available
                llm_config = None

            # Initialize Stagehand
            self.stagehand = Stagehand(
                env="local",  # Use local Playwright
                headless=self.headless,
                llmClient=llm_config,
            )

            await self.stagehand.init()

            self.initialized = True

            return {
                "success": True,
                "message": f"Stagehand initialized with MiniMax model: {self.model}",
                "model": self.model,
                "browser": "chromium",
                "mode": "headless" if self.headless else "headed",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to initialize Stagehand: {e}",
            }

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        if not self.initialized or not self.stagehand:
            return {"success": False, "error": "Stagehand not initialized"}

        try:
            await self.stagehand.page.goto(url)

            # Get page title
            title = await self.stagehand.page.title()

            return {
                "success": True,
                "url": url,
                "title": title,
                "message": f"Navigated to {url}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def act(self, instruction: str) -> Dict[str, Any]:
        """Perform an action using natural language."""
        if not self.initialized or not self.stagehand:
            return {"success": False, "error": "Stagehand not initialized"}

        try:
            result = await self.stagehand.act(instruction)

            return {
                "success": True,
                "instruction": instruction,
                "result": str(result),
                "message": f"Action completed: {instruction}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract(
        self,
        instruction: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract structured data from the page."""
        if not self.initialized or not self.stagehand:
            return {"success": False, "error": "Stagehand not initialized"}

        try:
            if schema:
                # Use structured extraction
                result = await self.stagehand.extract({
                    "instruction": instruction,
                    "schema": schema,
                })
            else:
                # Simple extraction
                result = await self.stagehand.extract(instruction)

            return {
                "success": True,
                "instruction": instruction,
                "data": result if isinstance(result, dict) else {"content": result},
                "message": f"Extracted data based on: {instruction}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def observe(self, instruction: str) -> Dict[str, Any]:
        """Observe available actions on the page."""
        if not self.initialized or not self.stagehand:
            return {"success": False, "error": "Stagehand not initialized"}

        try:
            result = await self.stagehand.observe(instruction)

            return {
                "success": True,
                "instruction": instruction,
                "elements": result if isinstance(result, list) else [result],
                "message": f"Observed elements: {instruction}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def agent(self, task: str) -> Dict[str, Any]:
        """Run an autonomous agent to complete a workflow."""
        if not self.initialized or not self.stagehand:
            return {"success": False, "error": "Stagehand not initialized"}

        try:
            # Create agent with MiniMax model
            agent = self.stagehand.agent({
                "mode": "cua",
                "model": self.model,
            })

            # Execute the task
            result = await agent.execute(task)

            return {
                "success": True,
                "task": task,
                "result": str(result),
                "message": f"Agent completed task: {task}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self) -> None:
        """Close the browser."""
        if self.stagehand:
            await self.stagehand.close()
            self.initialized = False


# CLI Interface
async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Stagehand Browser Automation with MiniMax AI"
    )
    parser.add_argument(
        "--command", "-c",
        choices=["navigate", "act", "extract", "observe", "agent", "init"],
        default="init",
        help="Command to execute"
    )
    parser.add_argument("--url", "-u", help="URL for navigate command")
    parser.add_argument(
        "--instruction", "-i",
        help="Instruction for act/extract/observe commands"
    )
    parser.add_argument(
        "--task", "-t",
        help="Task for agent command"
    )
    parser.add_argument(
        "--schema", "-s",
        help="JSON schema for structured extraction"
    )
    parser.add_argument(
        "--model", "-m",
        default="MiniMax-M2",
        help="MiniMax model to use"
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode"
    )
    parser.add_argument(
        "--api-key",
        help="MiniMax API key"
    )

    args = parser.parse_args()

    # Initialize
    browser = MiniMaxStagehand(
        model=args.model,
        headless=not args.headed,
        api_key=args.api_key,
    )

    result = await browser.initialize()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("success"):
        # Execute command
        if args.command == "navigate" and args.url:
            result = await browser.navigate(args.url)
        elif args.command == "act" and args.instruction:
            result = await browser.act(args.instruction)
        elif args.command == "extract" and args.instruction:
            schema = json.loads(args.schema) if args.schema else None
            result = await browser.extract(args.instruction, schema)
        elif args.command == "observe" and args.instruction:
            result = await browser.observe(args.instruction)
        elif args.command == "agent" and args.task:
            result = await browser.agent(args.task)

        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Cleanup
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
