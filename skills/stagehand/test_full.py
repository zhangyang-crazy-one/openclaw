import asyncio
import json
from scripts.minimax_browser_v2 import MiniMaxBrowser

async def test():
    print("=" * 60)
    print("MiniMax Browser Full Test")
    print("=" * 60)
    
    browser = MiniMaxBrowser(headless=True)
    
    # Init
    result = await browser.initialize()
    print("\n1. Init:", result.get('message'))
    
    if not result.get('success'):
        print("Init failed!")
        return
    
    # Navigate to a more complex page
    print("\n2. Navigate to GitHub...")
    result = await browser.navigate('https://github.com')
    print("   Title:", result.get('title'))
    
    # Extract content
    print("\n3. Extract page content...")
    result = await browser.extract("extract the page title and main heading")
    print("   Data:", json.dumps(result.get('data', {}), ensure_ascii=False, indent=4)[:200])
    
    # Test act
    print("\n4. Test act (scroll)...")
    result = await browser.act("scroll down the page")
    print("   Action:", result.get('action'))
    
    # Close
    await browser.close()
    print("\n5. Browser closed")
    print("\n🎉 Full test completed!")

asyncio.run(test())
