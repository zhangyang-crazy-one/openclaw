import asyncio
from scripts.minimax_browser_v2 import MiniMaxBrowser

async def test():
    print("=" * 60)
    print("MiniMax Browser Test")
    print("=" * 60)
    
    browser = MiniMaxBrowser(headless=True)
    
    # 设置 Chrome 路径
    import os
    os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = '/usr/bin/google-chrome'
    
    # Init
    result = await browser.initialize()
    print("Init:", result.get('message'))
    
    if result.get('success'):
        # Navigate
        result = await browser.navigate('https://example.com')
        print("Title:", result.get('title'))
        
        # Observe
        result = await browser.observe('find links and buttons')
        print("Elements found:", result.get('count', 0))
    
    await browser.close()
    print("Done!")

asyncio.run(test())
