import asyncio
import json
from scripts.minimax_browser_v3 import MiniMaxBrowserV3

async def test():
    print("=" * 70)
    print("GitHub Test - Stagehand V3")
    print("=" * 70)
    
    b = MiniMaxBrowserV3()
    await b.initialize()
    print("\n1. Init: OK")
    
    await b.navigate("https://github.com")
    print("2. Title:", await b.page.title())
    
    # Get A11y tree
    tree = await b._get_accessibility_tree()
    lines = tree.split("\n")
    print("3. A11y Elements:", len(lines))
    print("   First 3:")
    for line in lines[:3]:
        print("     ", line[:60])
    
    # Observe
    r = await b.observe("find Sign in and Sign up buttons")
    print("\n4. Observe:", r.get("element_count", 0), "elements")
    
    # Extract
    r = await b.extract("what is GitHub about")
    print("5. Extract:", json.dumps(r.get("data", {}), ensure_ascii=False, indent=2)[:300])
    
    await b.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(test())
