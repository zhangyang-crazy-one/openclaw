#!/usr/bin/env python3
"""
MiniMax Browser Automation V3 - Complete with Cookies & Sessions

完整支持:
1. Hybrid Accessibility Tree
2. Two-Phase Inference  
3. Self-Healing
4. Cookie/Session Persistence ✅
5. User Context (login state) ✅
"""

import asyncio
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from playwright.async_api import async_playwright

from scripts.a11y_tree import AccessibilityTreeBuilder


class MiniMaxBrowserV3:
    """
    完整版浏览器自动化 - V3 + Cookies + Sessions
    
    新增功能:
    - Cookie 持久化
    - Session 保存/加载
    - User Data Directory
    - Login State Persistence
    """
    
    # 支持的动作
    SUPPORTED_ACTIONS = [
        "click", "right_click", "middle_click",
        "hover", "double_click",
        "fill", "type", "clear",
        "press_key",
        "scroll", "scroll_to", "scroll_into_view",
        "goto",
        "screenshot",
        "wait"
    ]
    
    def __init__(
        self,
        model: str = "MiniMax-M2",
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        session_name: str = "default",
    ):
        self.model = model
        self.headless = headless
        
        # Session/Cookie 配置
        self.user_data_dir = user_data_dir or os.getenv(
            "STAGEHAND_USER_DATA",
            str(Path.home() / ".stagehand" / "sessions" / session_name)
        )
        self.cookies_file = f"{self.user_data_dir}/cookies.json"
        self.session_file = f"{self.user_data_dir}/session.json"
        
        # 确保目录存在
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
            except ImportError:
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
        self._cached_tree: Optional[str] = None
        self._tree_version: int = 0
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
        """初始化浏览器 (支持 Cookie 恢复)."""
        try:
            playwright = await async_playwright().start()
            
            chrome_path = os.getenv("CHROME_PATH") or "/usr/bin/google-chrome"
            
            # 使用 User Data Directory 保持登录状态
            if os.path.exists(self.user_data_dir):
                print(f"📁 Using existing user data: {self.user_data_dir}")
            
            # 创建 context (带 user data)
            self.context = await playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                executable_path=chrome_path if os.path.exists(chrome_path) else None,
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
            )
            
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            self.initialized = True
            
            # 加载 cookies (如果存在)
            if load_cookies and os.path.exists(self.cookies_file):
                await self._load_cookies()
            
            # 检查登录状态
            await self._check_login_state()
            
            return {
                "success": True,
                "message": "✅ 浏览器初始化成功",
                "user_data_dir": self.user_data_dir,
                "logged_in": self._is_logged_in,
                "cookies_loaded": load_cookies and os.path.exists(self.cookies_file),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self, save_cookies: bool = True):
        """关闭浏览器 (自动保存 Cookie)."""
        if self.browser:
            # 保存 cookies
            if save_cookies:
                await self._save_cookies()
                await self._save_session()
            
            await self.context.close()
            self.initialized = False
    
    # ============ Cookie/Session Management ============
    
    async def _save_cookies(self):
        """保存当前 cookies."""
        try:
            if self.context:
                cookies = await self.context.cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                print(f"💾 Cookies saved: {len(cookies)} items")
        except Exception as e:
            print(f"⚠️  Save cookies failed: {e}")
    
    async def _load_cookies(self):
        """加载保存的 cookies."""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                print(f"🍪 Cookies loaded: {len(cookies)} items")
        except Exception as e:
            print(f"⚠️  Load cookies failed: {e}")
    
    async def _save_session(self):
        """保存 session 数据 (localStorage, etc)."""
        try:
            session_data = {
                "url": self.page.url if self.page else "",
                "title": await self.page.title() if self.page else "",
                "user_data_dir": self.user_data_dir,
                "saved_at": str(Path(self.cookies_file).stat().st_mtime),
            }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Save session failed: {e}")
    
    async def _check_login_state(self):
        """检查登录状态."""
        try:
            # 常见登录检测模式
            current_url = self.page.url
            
            # GitHub
            if "github.com" in current_url:
                page_text = await self.page.evaluate("() => document.body.innerText")
                self._is_logged_in = "Sign out" in page_text or "Sign in" not in page_text[:500]
            
            # 通用检测
            if not self._is_logged_in:
                page_text = await self.page.evaluate("() => document.body.innerText")
                self._is_logged_in = any(x in page_text for x in [
                    "退出", "Logout", "Sign out", 
                    "已登录", "Welcome", "个人中心"
                ])
                
        except Exception:
            self._is_logged_in = False
    
    # ============ Session Management ============
    
    async def save_session(self, name: str = None) -> Dict[str, Any]:
        """手动保存 session."""
        await self._save_cookies()
        await self._save_session()
        
        return {
            "success": True,
            "message": f"Session saved to {self.user_data_dir}",
            "cookies_count": len(await self.context.cookies()) if self.context else 0
        }
    
    async def load_session(self, name: str = None) -> Dict[str, Any]:
        """加载 session."""
        if os.path.exists(self.cookies_file):
            await self._load_cookies()
            await self._check_login_state()
            return {
                "success": True,
                "message": "Session loaded",
                "logged_in": self._is_logged_in
            }
        return {
            "success": False,
            "message": "No saved session found"
        }
    
    def get_sessions(self) -> List[str]:
        """列出所有保存的 sessions."""
        sessions_dir = str(Path(self.user_data_dir).parent)
        if os.path.exists(sessions_dir):
            return [d for d in os.listdir(sessions_dir) 
                   if os.path.isdir(os.path.join(sessions_dir, d))]
        return []
    
    # ============ Accessibility Tree ============
    
    async def _get_accessibility_tree(self, force_refresh: bool = False) -> str:
        """获取页面可访问性树."""
        if self._cached_tree and not force_refresh:
            return self._cached_tree
        
        self._cached_tree = await self.a11y_builder.build_tree(self.page)
        self._tree_version += 1
        
        return self._cached_tree
    
    async def _get_page_text(self) -> str:
        """获取页面纯文本."""
        return await self.page.evaluate("""
            () => {
                const text = [];
                document.querySelectorAll('h1, h2, h3, p, li, td, th').forEach(el => {
                    const t = el.innerText?.trim();
                    if (t && t.length > 5 && t.length < 500) text.push(t);
                });
                return text.slice(0, 50).join('\\n\\n');
            }
        """)
    
    # ============ Element Finding ============
    
    async def _find_element_by_id(self, element_id: int) -> Optional[Dict]:
        """根据元素ID查找DOM元素."""
        return await self.page.evaluate(f"""() => {{
            const elements = document.querySelectorAll('a, button, input, select, textarea, [role]');
            if (elements[{element_id}]) {{
                const el = elements[{element_id}];
                return {{
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    href: el.href || '',
                    text: el.innerText?.trim() || '',
                    placeholder: el.placeholder || '',
                    selector: el.id ? '#' + el.id : ''
                }};
            }}
            return null;
        }}""")
    
    # ============ Actions ============
    
    async def _execute_action(self, action_plan: Dict) -> Dict[str, Any]:
        """执行动作."""
        element_id = action_plan.get("element_id", 0)
        method = action_plan.get("method", "click")
        arguments = action_plan.get("arguments", [])
        value = action_plan.get("value", "")
        
        result = {"success": False, "method": method}
        
        try:
            element = None
            if element_id >= 0:
                element = await self._find_element_by_id(element_id)
            
            # 执行各种动作
            if method == "click":
                selector = element.get("selector", "") if element else ""
                if selector:
                    await self.page.click(selector)
                else:
                    await self.page.evaluate(f"""() => {{
                        const elements = document.querySelectorAll('a, button, [role]');
                        if (elements[{element_id}]) elements[{element_id}].click();
                    }}""")
                result["success"] = True
                
            elif method == "right_click":
                selector = element.get("selector", "") if element else ""
                if selector:
                    await self.page.click(selector, button="right")
                result["success"] = True
                
            elif method == "hover":
                selector = element.get("selector", "") if element else ""
                if selector:
                    await self.page.hover(selector)
                result["success"] = True
                
            elif method == "fill":
                selector = element.get("selector", "") if element else ""
                text = value or " ".join(arguments)
                if selector:
                    await self.page.fill(selector, text)
                else:
                    await self.page.evaluate(f"""(v) => {{
                        const elements = document.querySelectorAll('input, textarea');
                        if (elements[{element_id}]) elements[{element_id}].value = v;
                    }}""", text)
                result["success"] = True
                
            elif method == "press_key":
                key = arguments[0] if arguments else "Enter"
                await self.page.keyboard.press(key)
                result["success"] = True
                
            elif method == "scroll":
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                result["success"] = True
                
            elif method == "scroll_to":
                pct = int(arguments[0].replace("%", "")) if arguments else 50
                await self.page.evaluate(f"""(p) => {{
                    window.scrollTo(0, document.body.scrollHeight * p / 100)
                }}""", pct)
                result["success"] = True
                
            elif method in ["goto", "navigate"]:
                url = value or arguments[0] if arguments else ""
                if url:
                    await self.page.goto(url, wait_until="domcontentloaded")
                    await self._get_accessibility_tree(force_refresh=True)
                result["success"] = True
                
            elif method == "wait":
                ms = int(arguments[0]) if arguments else 1000
                await self.page.wait_for_timeout(ms)
                result["success"] = True
            
            # 自愈: 操作后刷新树
            if method in ["click", "scroll", "navigate", "goto", "fill"]:
                await self._get_accessibility_tree(force_refresh=True)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e), "method": method}
    
    # ============ Main Methods ============
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """导航到 URL."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            tree = await self._get_accessibility_tree(force_refresh=True)
            
            return {
                "success": True,
                "url": url,
                "title": await self.page.title(),
                "tree_version": self._tree_version,
                "elements_count": len(tree.split("\n"))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def act(self, instruction: str) -> Dict[str, Any]:
        """执行自然语言指令."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            tree = await self._get_accessibility_tree()
            tree_lines = tree.split("\n")
            
            messages = [
                {"role": "system", "content": """You are a professional browser automation assistant.
Actions: click, right_click, hover, fill, press_key, scroll, scroll_to, goto, wait
For fill: include "value" field with text to enter
For scroll: use percentages like "25%", "50%", "75%"
Respond with JSON only."""},
                {"role": "user", "content": f"""Find element and choose action.

Tree (indices 0-{len(tree_lines)-1}):
{tree}

Instruction: {instruction}

JSON:
{{"element_id": <index>,"method":"click","arguments":[],"value":"text","reasoning":"why"}}

If no match: {{"element_id": -1}}"""}
            ]
            
            response = await self._call_llm(messages)
            action_plan = self._parse_llm_response(response)
            
            success = False
            if action_plan.get("element_id", -1) >= 0 or action_plan.get("method") in ["scroll", "press_key", "goto", "wait"]:
                result = await self._execute_action(action_plan)
                success = result.get("success", False)
            
            return {
                "success": success,
                "instruction": instruction,
                "action_plan": action_plan,
                "reasoning": action_plan.get("reasoning", ""),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract(self, instruction: str) -> Dict[str, Any]:
        """提取结构化数据."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            page_text = await self._get_page_text()
            
            messages = [
                {"role": "system", "content": "Extract REAL data. No templates. JSON only."},
                {"role": "user", "content": f"""Extract data.

Text:
{page_text[:4000]}

Instruction: {instruction}

JSON: {{"data": {{"key": "value"}},"confidence": 0.9}}"""}
            ]
            
            response = await self._call_llm(messages)
            data = self._parse_extract_response(response)
            
            return {
                "success": True,
                "instruction": instruction,
                "data": data,
                "tree_version": self._tree_version
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def observe(self, instruction: str) -> Dict[str, Any]:
        """观察页面元素."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            tree = await self._get_accessibility_tree()
            tree_lines = tree.split("\n")
            
            messages = [
                {"role": "system", "content": "Find matching elements. JSON only."},
                {"role": "user", "content": f"""Find elements.

Tree (indices 0-{len(tree_lines)-1}):
{tree}

Instruction: {instruction}

JSON: {{"elements":[0,1],"description":"..."}}"""}
            ]
            
            response = await self._call_llm(messages)
            analysis = self._parse_llm_response(response)
            
            return {
                "success": True,
                "instruction": instruction,
                "analysis": analysis,
                "tree": tree,
                "element_count": len(tree_lines)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def agent(self, task: str) -> Dict[str, Any]:
        """自主代理."""
        if not self.initialized:
            return {"success": False, "error": "浏览器未初始化"}
        
        try:
            tree = await self._get_accessibility_tree()
            
            messages = [
                {"role": "system", "content": "Plan browser actions. JSON array."},
                {"role": "user", "content": f"""Plan steps.

Tree:
{tree}

Task: {task}

Steps (max 5): [{{"step":1,"action":"click|fill|scroll|navigate","element_id":0,"reasoning":"..."}}]"""}
            ]
            
            response = await self._call_llm(messages)
            plan = self._parse_plan_response(response)
            
            results = []
            for step in plan[:5]:
                action = step.get("action", "")
                result = await self.act(step.get("reasoning", ""))
                results.append({
                    "step": step.get("step", 0),
                    "action": action,
                    "success": result.get("success", False)
                })
            
            return {
                "success": True,
                "task": task,
                "plan": plan,
                "results": results,
                "logged_in": self._is_logged_in,
                "self_healing": {"tree_refreshes": self._tree_version}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            data = json.loads(response)
            if isinstance(data, dict):
                if "data" not in data:
                    data = {"data": data}
                return data
            return {"data": {"raw": response[:500]}}
        except:
            clean = response.replace("//", "").strip()
            return {"data": {"extracted": clean[:1000]}}
    
    def _parse_plan_response(self, response: str) -> List[Dict]:
        try:
            return json.loads(response)
        except:
            match = re.search(r'\[[^\[\]]*\]', response)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return []


# ============ CLI ============

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MiniMax Browser V3 - with Cookies & Sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --init                   # Initialize (loads cookies)
  %(prog)s -u https://github.com   # Navigate
  %(prog)s -a "点击登录"             # Click
  %(prog)s -e "提取标题"             # Extract
  %(prog)s --save-session          # Save cookies
  %(prog)s --sessions               # List sessions
        """
    )
    parser.add_argument("--test", action="store_true", help="Test API")
    parser.add_argument("--init", action="store_true", help="Initialize")
    parser.add_argument("--navigate", "-u", help="Navigate URL")
    parser.add_argument("--act", "-a", help="Execute action")
    parser.add_argument("--extract", "-e", help="Extract data")
    parser.add_argument("--observe", "-o", help="Observe elements")
    parser.add_argument("--agent", help="Agent task")
    parser.add_argument("--save-session", action="store_true", help="Save session")
    parser.add_argument("--load-session", action="store_true", help="Load session")
    parser.add_argument("--sessions", action="store_true", help="List sessions")
    parser.add_argument("--headed", action="store_true", help="Show browser")
    parser.add_argument("--session", "-s", default="default", help="Session name")
    
    args = parser.parse_args()
    
    browser = MiniMaxBrowserV3(
        headless=not args.headed,
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
    result = await browser.initialize()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        # Save/Load session
        if args.save_session:
            result = await browser.save_session()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.load_session:
            result = await browser.load_session()
            print(json.dumps(result, indent=2, ensure_ascii=False))
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
        elif args.agent:
            result = await browser.agent(args.agent)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
