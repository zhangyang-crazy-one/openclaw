import asyncio
import json
import os
from scripts.minimax_browser_v3 import MiniMaxBrowserV3

async def test():
    print("=" * 60)
    print("MiniMax Browser V3 Test")
    print("=" * 60)
    
    # 从环境变量读取
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("\nPlease set MINIMAX_API_KEY")
        print('export MINIMAX_API_KEY="your-key"')
        return
    
    browser = MiniMaxBrowserV3()
    
    # 1. Init
    print("\n1. Initialize...")
    result = await browser.initialize()
    print(f"   {result.get('message')}")
    
    if not result.get('success'):
        print("   Failed!")
        return
    
    # 2. Navigate
    print("\n2. Navigate to example.com...")
    result = await browser.navigate("https://example.com")
    print(f"   Title: {result.get('title')}")
    
    # 3. Get A11y Tree
    print("\n3. Get Accessibility Tree...")
    tree = await browser._get_accessibility_tree()
    lines = tree.split("\n")
    print(f"   Elements: {len(lines)}")
    
    # 4. Test observe
    print("\n4. Test observe...")
    result = await browser.observe("find links and buttons")
    print(f"   Elements found: {result.get('element_count', 0)}")
    
    # 5. Test extract
    print("\n5. Test extract...")
    result = await browser.extract("what is this page about")
    print(f"   Extracted: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)[:200]}")
    
    await browser.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(test())
