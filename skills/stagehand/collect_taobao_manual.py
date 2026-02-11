#!/usr/bin/env python3
"""
淘宝商品手动收集工具

由于淘宝反爬虫机制较强，使用此工具：
1. 打开浏览器访问淘宝
2. 你手动复制商品信息
3. 粘贴到这里生成 Excel
"""

import pandas as pd
from openpyxl import Workbook
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def manual_collect():
    print("=" * 80)
    print("📝 淘宝商品手动收集工具")
    print("=" * 80)
    print()
    print("💡 使用方法:")
    print("   1. 浏览器会打开淘宝搜索结果")
    print("   2. 你手动复制商品信息 (名称和价格)")
    print("   3. 粘贴到终端")
    print("   4. 输入 'done' 完成")
    print("   5. 自动生成 Excel")
    print()
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开")
    
    # 访问淘宝
    search_url = "https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall"
    await browser.navigate(search_url)
    print(f"✅ 已访问淘宝搜索")
    
    print()
    print("=" * 80)
    print("📋 开始收集")
    print("=" * 80)
    
    products = []
    
    while True:
        print("\n📝 输入商品信息 (格式: 名称,价格)")
        print("   例如: DDR4 32G 服务器内存条 ECC,288")
        print("   输入 'done' 完成")
        
        user_input = input("\n> ").strip()
        
        if user_input.lower() == 'done':
            break
        
        if ',' in user_input:
            parts = user_input.split(',', 1)
            products.append({
                '商品名称': parts[0].strip(),
                '价格(¥)': parts[1].strip(),
                '店铺': '',
                '销量': '',
                '链接': '',
                '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            print(f"   ✅ 已添加 ({len(products)} 个)")
        else:
            print("   ⚠️ 格式错误，请使用: 名称,价格")
    
    # 保存
    if products:
        df = pd.DataFrame(products)
        excel_path = f"/home/liujerry/taobao_32g_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print()
        print("=" * 80)
        print(f"✅ Excel 已保存: {excel_path}")
        print(f"📊 共 {len(products)} 个商品")
        print("=" * 80)
    else:
        print("\n⚠️ 未收集到任何商品")
    
    await browser.save_session()
    await browser.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(manual_collect())
