import asyncio
import json
from scripts.minimax_browser_v2 import MiniMaxBrowser

async def test():
    print("=" * 60)
    print("MiniMax API Test")
    print("=" * 60)
    
    browser = MiniMaxBrowser(headless=True)
    
    # Init
    result = await browser.initialize()
    print("\n1. Init:", result.get('message'))
    
    # Test direct API call
    print("\n2. Test direct MiniMax API call...")
    messages = [
        {"role": "user", "content": "Hello! Please respond with a short JSON: {\"greeting\": \"hi\"}"}
    ]
    response = await browser._call_minimax(messages)
    print("   Response:", response[:200])
    
    # Navigate
    print("\n3. Navigate...")
    result = await browser.navigate('https://example.com')
    print("   Title:", result.get('title'))
    
    # Get page content directly
    print("\n4. Get page HTML...")
    content = await browser.page.content()
    print("   Content length:", len(content))
    print("   First 200 chars:", content[:200])
    
    await browser.close()
    print("\nDone!")

asyncio.run(test())
