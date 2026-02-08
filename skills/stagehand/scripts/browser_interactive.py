#!/usr/bin/env python3
"""
MiniMax Browser Automation - Interactive Mode

有头模式: 直接操作浏览器，手动登录账号
"""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx
from playwright.async_api import async_playwright

from scripts.a11y_tree import AccessibilityTreeBuilder


class MiniMaxBrowserInteractive:
    """
    有头模式浏览器自动化
    
    使用方法:
    1. 启动有头模式浏览器
    2. 手动登录账号
    3. 保存 session
    4. 后续自动恢复登录状态
    """
    
    def __init__(
        self,
        model: str = "MiniMax-M2",
        headless: bool = False,  # 默认有头模式！
        session_name: str = "default",
    ):
        self.model = model
        self.headless = headless
        
        # Session 配置
        self.user_data_dir = str(Path.home() / ".stagehand" / "sessions" / session_name)
        self.cookies_file = f"{self.user_data_dir}/cookies.json"
        self.session_file = f"{self.user_data_dir}/session.json"
        
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        
        # MiniMax 配置
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
        
        if not self.api_key:
            try:
                from scripts.config import get_api_config
                config = get_api_config()
                if config:
                    self.api_key = config.get("api_key")
            except:
                pass
        
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY 未设置")
        
        # 组件
        self.a11y_builder = AccessibilityTreeBuilder()
        
        # 状态
        self.browser = None
        self.context = None
        self.page = None
        self.initialized = False
        self._cached_tree = None
        self._tree_version = 0
        self._is_logged_in = False
    
    # ============ LLM API ============
    
    async def _call_llm(self, messages: List[Dict], max_tokens: int = 4000) -> str:
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
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    
    # ============ Browser Control ============
    
    async def initialize(self, load_cookies: bool = True) -> Dict[str, Any]:
        """
        初始化浏览器
        
        Args:
            load_cookies: 是否加载保存的 cookies
        """
        try:
            playwright = await async_playwright().start()
            
            # 检测 Chrome 路径
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            # 创建浏览器 (有头模式！)
            self.context = await playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,  # 有头模式！
                executable_path=chrome_path,
                viewport={"width": 1280, "height": 900},
                locale="zh-CN",
            )
            
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            self.initialized = True
            
            # 加载 cookies
            if load_cookies and os.path.exists(self.cookies_file):
                await self._load_cookies()
                cookies_count = len(json.load(open(self.cookies_file)))
                print(f"🍪 Loaded {cookies_count} cookies")
            
            # 检查登录状态
            await self._check_login_state()
            
            mode = "🖥️ 有头模式" if not self.headless else "📻 无头模式"
            
            return {
                "success": True,
                "message": f"{mode} - 浏览器已启动",
                "user_data_dir": self.user_data_dir,
                "logged_in": self._is_logged_in,
                "url": self.page.url if self.page else "",
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self, save_cookies: bool = True):
        """关闭浏览器 (自动保存 cookies)."""
        if self.context:
            if save_cookies:
                await self._save_cookies()
                await self._save_session()
            
            await self.context.close()
            self.initialized = False
    
    # ============ Cookie/Session ============
    
    async def _save_cookies(self):
        """保存 cookies."""
        try:
            if self.context:
                cookies = await self.context.cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                print(f"💾 Saved {len(cookies)} cookies to {self.cookies_file}")
        except Exception as e:
            print(f"⚠️  Save cookies failed: {e}")
    
    async def _load_cookies(self):
        """加载 cookies."""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
        except Exception as e:
            print(f"⚠️  Load cookies failed: {e}")
    
    async def _save_session(self):
        """保存 session."""
        try:
            session_data = {
                "url": self.page.url if self.page else "",
                "title": await self.page.title() if self.page else "",
                "user_data_dir": self.user_data_dir,
            }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except:
            pass
    
    async def _check_login_state(self):
        """检查登录状态."""
        try:
            if not self.page:
                self._is_logged_in = False
                return
            
            current_url = self.page.url
            page_text = await self.page.evaluate("() => document.body.innerText")
            
            # 常见登录检测
            logged_in_indicators = [
                "Sign out", "Logout", "退出", "Sign out",
                "个人中心", "我的", "Settings", "设置",
                "头像", "avatar", "Profile"
            ]
            
            self._is_logged_in = any(x in page_text for x in logged_in_indicators)
            
            # GitHub 特定检测
            if "github.com" in current_url:
                self._is_logged_in = "Sign out" in page_text or "Your repositories" in page_text
            
        except:
            self._is_logged_in = False
    
    # ============ Session Management ============
    
    async def save_session(self) -> Dict[str, Any]:
        """手动保存 session."""
        await self._save_cookies()
        await self._save_session()
        
        return {
            "success": True,
            "message": f"Session saved to {self.user_data_dir}",
            "cookies_count": len(await self.context.cookies()) if self.context else 0
        }
    
    def get_sessions(self) -> List[str]:
        """列出所有 sessions."""
        sessions_dir = str(Path(self.user_data_dir).parent)
        if os.path.exists(sessions_dir):
            return [d for d in os.listdir(sessions_dir) 
                   if os.path.isdir(os.path.join(sessions_dir, d))]
        return []
    
    # ============ Accessibility Tree ============
    
    async def get_tree(self) -> str:
        """获取 A11y Tree."""
        if not self._cached_tree:
            self._cached_tree = await self.a11y_builder.build_tree(self.page)
            self._tree_version += 1
        return self._cached_tree
    
    # ============ Main Methods ============
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """导航."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            tree = await self.get_tree()
            
            return {
                "success": True,
                "url": url,
                "title": await self.page.title(),
                "elements_count": len(tree.split("\n"))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def act(self, instruction: str) -> Dict[str, Any]:
        """执行动作."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            tree = await self.get_tree()
            tree_lines = tree.split("\n")
            
            messages = [
                {"role": "system", "content": "Browser automation. Actions: click, fill, scroll, press_key. JSON only."},
                {"role": "user", "content": f"""Tree (indices 0-{len(tree_lines)-1}):
{tree}

Instruction: {instruction}

JSON: {{"element_id": <index>,"method":"click","value":"text","reasoning":"..."}}

If no match: {{"element_id": -1}}"""}
            ]
            
            response = await self._call_llm(messages)
            plan = self._parse_llm_response(response)
            
            success = await self._execute_action(plan)
            
            return {
                "success": success,
                "instruction": instruction,
                "action_plan": plan,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_action(self, plan: Dict) -> bool:
        """执行动作."""
        element_id = plan.get("element_id", 0)
        method = plan.get("method", "")
        value = plan.get("value", "")
        
        try:
            if method == "click":
                await self.page.evaluate(f"""() => {{
                    const elements = document.querySelectorAll('a, button, [role]');
                    if (elements[{element_id}]) elements[{element_id}].click();
                }}""")
            elif method == "fill":
                await self.page.evaluate(f"""(v) => {{
                    const elements = document.querySelectorAll('input, textarea');
                    if (elements[{element_id}]) elements[{element_id}].value = v;
                }}""", value or "")
            elif method == "scroll":
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif method == "press_key":
                await self.page.keyboard.press(value or "Enter")
            
            return True
        except:
            return False
    
    async def extract(self, instruction: str) -> Dict[str, Any]:
        """提取数据."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            page_text = await self.page.evaluate("() => document.body.innerText")
            
            messages = [
                {"role": "system", "content": "Extract data. JSON only."},
                {"role": "user", "content": f"""Extract: {instruction}

Text: {page_text[:3000]}

JSON: {{"data": {{"key": "value"}}}}"""}
            ]
            
            response = await self._call_llm(messages)
            data = self._parse_extract_response(response)
            
            return {"success": True, "instruction": instruction, "data": data}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def observe(self, instruction: str) -> Dict[str, Any]:
        """观察元素."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        tree = await self.get_tree()
        
        return {
            "success": True,
            "instruction": instruction,
            "tree": tree,
            "element_count": len(tree.split("\n"))
        }
    
    # ============ Response Parsing ============
    
    def _parse_llm_response(self, response: str) -> Dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'\{[^{}]+\}', response.replace("\n", ""))
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {"element_id": -1}
    
    def _parse_extract_response(self, response: str) -> Dict:
        try:
            return json.loads(response)
        except:
            return {"data": {"raw": response[:500]}}


# ============ CLI ============

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🖥️ MiniMax Browser - 有头模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
💡 使用方法:

1️⃣  首次登录 (手动操作):
   %(prog)s --init --headed
   # 浏览器窗口会打开
   # 手动访问网站并登录
   %(prog)s --save-session

2️⃣  恢复登录状态:
   %(prog)s --init --session github
   # 自动加载 cookies，恢复登录状态

3️⃣  自动操作:
   %(prog)s -u https://github.com
   %(prog)s -a "点击登录按钮"
   %(prog)s -e "提取页面内容"

🎯 常用场景:
   %(prog)s --init --headed  # 有头模式，手动登录
   %(prog)s --save-session    # 保存登录状态
        """
    )
    
    parser.add_argument("--test", action="store_true", help="测试 API")
    parser.add_argument("--init", action="store_true", help="初始化浏览器")
    parser.add_argument("--headed", action="store_true", help="有头模式 (默认)")
    parser.add_argument("--navigate", "-u", help="导航 URL")
    parser.add_argument("--act", "-a", help="执行动作")
    parser.add_argument("--extract", "-e", help="提取数据")
    parser.add_argument("--observe", "-o", help="观察元素")
    parser.add_argument("--save-session", action="store_true", help="保存 session")
    parser.add_argument("--sessions", action="store_true", help="列出 sessions")
    parser.add_argument("--session", "-s", default="default", help="Session 名称")
    
    args = parser.parse_args()
    
    # 默认有头模式
    headless = False if args.headed else False
    
    browser = MiniMaxBrowserInteractive(
        headless=headless,
        session_name=args.session
    )
    
    # Test
    if args.test:
        print("Testing MiniMax API...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{browser.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {browser.api_key}"},
                    json={"model": browser.model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}
                )
                print(f"API Status: {resp.status_code}")
        except Exception as e:
            print(f"API Error: {e}")
        return
    
    # Init
    if args.init:
        print("=" * 80)
        print("🖥️  初始化浏览器...")
        print("=" * 80)
        
        result = await browser.initialize()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("success"):
            print("\n💡 现在你可以:")
            print("   1. 在浏览器窗口中手动操作")
            print("   2. 访问需要登录的网站")
            print("   3. 登录你的账号")
            print("   4. 运行 --save-session 保存状态")
            print("\n⏸️  浏览器窗口保持打开，按 Ctrl+C 退出")
            print("=" * 80)
            
            # 保持浏览器打开
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n💾 保存 session...")
                result = await browser.save_session()
                print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save session
    elif args.save_session:
        result = await browser.save_session()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # List sessions
    elif args.sessions:
        sessions = browser.get_sessions()
        print(f"Sessions: {sessions}")
    
    # Execute commands
    elif args.navigate:
        result = await browser.navigate(args.navigate)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.act:
        result = await browser.act(args.act)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.extract:
        result = await browser.extract(args.extract)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.observe:
        result = await browser.observe(args.observe)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
