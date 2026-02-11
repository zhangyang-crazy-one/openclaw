#!/usr/bin/env python3
"""
淘宝 32G 服务器内存 - 简单采集

策略：
1. 访问搜索页
2. 获取页面所有文本
3. 提取 32G + 服务器 + 价格 的商品
4. 保存结果
"""

import asyncio
import pandas as pd
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def simple_collect():
    print("=" * 80)
    print("💰 淘宝 32G 服务器内存 - 简单采集")
    print("=" * 80)
    print("\n策略: 从页面文本中提取所有32G服务器内存商品\n")
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开\n")
    
    # 1. 访问搜索页
    print("🔄 Step 1: 访问淘宝搜索...")
    search_url = "https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall&sort=price-asc"
    await browser.navigate(search_url)
    await asyncio.sleep(5)
    print(f"   ✅ {browser.page.url}\n")
    
    # 2. 滚动加载更多
    print("🔄 Step 2: 滚动加载...")
    for i in range(10):
        await browser.page.evaluate("window.scrollBy(0, 500)")
        await asyncio.sleep(0.3)
    await asyncio.sleep(3)
    
    # 3. 获取所有文本
    print("🔄 Step 3: 提取页面文本...\n")
    
    page_text = await browser.page.evaluate("""
        () => document.body.innerText
    """)
    
    lines = page_text.split('\n')
    lines = [l.strip() for l in lines if l.strip()]
    
    print(f"   📊 获取到 {len(lines)} 行文本\n")
    
    # 4. 提取商品信息
    print("🔄 Step 4: 分析商品信息...")
    
    products = []
    seen_prices = set()
    
    import re
    
    for line in lines:
        # 检查是否包含32G和价格
        if ('32G' in line or '32g' in line) and ('服务器' in line or 'Server' in line or '工作站' in line):
            # 提取价格
            price_match = re.search(r'[¥￥]\s*([\d,.]+)', line)
            if price_match:
                price = price_match.group(1).replace(',', '')
                try:
                    price_val = float(price)
                    if 100 < price_val < 10000 and price not in seen_prices:
                        seen_prices.add(price)
                        
                        # 提取标题（取第一部分）
                        title = line.split(' ')[0][:60]
                        
                        # 提取销量
                        sales_match = re.search(r'(\d+[+]?\s*人付款)', line)
                        sales = sales_match.group(1) if sales_match else ''
                        
                        # 提取店铺
                        shop_match = re.search(r'(旗舰店|专营店|专卖店|企业店)', line)
                        shop = shop_match.group(1) if shop_match else ''
                        
                        products.append({
                            '商品名称': title,
                            '价格(¥)': price_val,
                            '销量': sales,
                            '店铺': shop,
                            '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except:
                    pass
    
    print(f"\n📊 提取到 {len(products)} 个商品\n")
    
    # 5. 去重并排序
    df = pd.DataFrame(products)
    if not df.empty:
        df = df.drop_duplicates(subset=['价格(¥)'])
        df = df.sort_values('价格(¥)')
    
    # 6. 保存
    if not df.empty:
        excel_path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print("=" * 80)
        print("✅ 采集完成!")
        print("=" * 80)
        print(f"\n📁 文件: {excel_path}")
        print(f"📊 商品: {len(df)} 个")
        
        if not df.empty:
            prices = df['价格(¥)']
            print(f"\n💰 价格统计:")
            print(f"   最低: ¥{prices.min():.0f}")
            print(f"   最高: ¥{prices.max():.0f}")
            print(f"   平均: ¥{prices.mean():.0f}")
            
            print(f"\n📋 商品列表:")
            for i, row in df.head(20).iterrows():
                print(f"   {i+1}. ¥{row['价格(¥)']:5.0f}  {row['商品名称'][:40]}...")
    else:
        print("\n⚠️ 未提取到商品")
    
    await browser.save_session()
    await browser.close()


if __name__ == "__main__":
    asyncio.run(simple_collect())
