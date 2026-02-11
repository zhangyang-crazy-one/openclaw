#!/usr/bin/env python3
"""
淘宝 32G 服务器内存完整采集器

策略：
1. 滚动加载更多商品
2. 点击进入每个商品详情页
3. 获取准确的32G规格价格
4. 收集100个商品
"""

import asyncio
import json
import pandas as pd
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def collect_full_data():
    print("=" * 80)
    print("💰 淘宝 32G 服务器内存 - 完整采集")
    print("=" * 80)
    print("\n目标: 收集100个商品的准确价格")
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开")
    
    # 1. 访问淘宝搜索页
    print("\n🔄 Step 1: 访问搜索页面...")
    search_url = "https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall&sort=price-asc"
    await browser.navigate(search_url)
    print(f"✅ 已访问: {browser.page.url}")
    
    await asyncio.sleep(5)
    
    # 2. 滚动加载更多商品
    print("\n🔄 Step 2: 滚动加载更多商品...")
    
    for i in range(10):  # 滚动10次
        await browser.page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(1)
        print(f"   滚动 {i+1}/10")
    
    # 截图
    screenshot_path = f"/home/liujerry/stagehand_data/screenshots/taobao_full_scroll_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await browser.page.screenshot(path=screenshot_path)
    print(f"📸 截图: {screenshot_path}")
    
    # 3. 获取所有商品链接
    print("\n🔄 Step 3: 获取商品链接...")
    
    product_links = await browser.page.evaluate("""
        () => {
            const links = [];
            document.querySelectorAll('a[href*="item.htm"], a[href*="taobao.com\\/item"]').forEach(a => {
                const href = a.href;
                if (href && !links.find(l => l === href)) {
                    links.push(href);
                }
            });
            return links.slice(0, 100);  // 最多100个
        }
    """)
    
    print(f"📊 找到 {len(product_links)} 个商品链接")
    
    # 4. 采集每个商品的价格
    print("\n🔄 Step 4: 进入商品页面获取准确价格...")
    
    products = []
    
    for i, link in enumerate(product_links[:50]):  # 先采集50个
        try:
            print(f"   [{i+1}/{min(len(product_links), 50)}] 访问商品...")
            
            await browser.page.goto(link, timeout=15000)
            await asyncio.sleep(3)  # 等待页面加载
            
            # 获取页面数据
            page_data = await browser.page.evaluate("""
                () => {
                    const data = {
                        title: '',
                        price: '',
                        shop: '',
                        specs: []
                    };
                    
                    // 标题
                    const titleEl = document.querySelector('.tb-title, h1, [class*="title"]');
                    data.title = titleEl ? titleEl.innerText.trim() : '';
                    
                    // 价格
                    const priceEl = document.querySelector('.tm-price, .price', [class*="price"]);
                    if (!priceEl) {
                        const text = document.body.innerText;
                        const match = text.match(/[¥￥]\\s*([\\d.]+)/);
                        if (match) data.price = match[1];
                    } else {
                        data.price = priceEl.innerText.trim();
                    }
                    
                    // 店铺
                    const shopEl = document.querySelector('.shop-name, .tm-shop', [class*="shop"]);
                    data.shop = shopEl ? shopEl.innerText.trim() : '';
                    
                    // 规格选项
                    document.querySelectorAll('[class*="sku"], [class*="prop"]').forEach(el => {
                        const text = el.innerText;
                        if (text.includes('32G') || text.includes('32g')) {
                            data.specs.push(text.substring(0, 100));
                        }
                    });
                    
                    return data;
                }
            """)
            
            if page_data.get('price'):
                products.append({
                    '商品名称': page_data.get('title', '')[:80],
                    '价格(¥)': page_data.get('price', ''),
                    '店铺': page_data.get('shop', ''),
                    '规格': ', '.join(page_data.get('specs', []))[:50],
                    '链接': link,
                    '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"      ✅ ¥{page_data.get('price')} - {page_data.get('title', '')[:30]}...")
            
        except Exception as e:
            print(f"      ❌ 错误: {str(e)[:30]}")
        
        # 每采集5个保存一次
        if (i+1) % 5 == 0:
            save_partial(products)
    
    # 5. 返回搜索页继续
    await browser.navigate(search_url)
    await asyncio.sleep(3)
    
    # 保存完整结果
    save_complete(products)
    
    await browser.save_session()
    await browser.close()
    
    return products


def save_partial(products):
    """保存部分结果"""
    df = pd.DataFrame(products)
    path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(path, index=False, engine='openpyxl')
    print(f"   💾 临时保存: {len(products)} 个商品")


def save_complete(products):
    """保存完整结果"""
    df = pd.DataFrame(products)
    
    # 按价格排序
    df['价格(¥)'] = pd.to_numeric(df['价格(¥)'], errors='coerce')
    df = df.sort_values('价格(¥)')
    
    # 保存
    path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(path, index=False, engine='openpyxl')
    
    print(f"\n✅ 完整采集完成!")
    print(f"   文件: {path}")
    print(f"   商品: {len(products)} 个")
    
    if not df.empty:
        prices = df['价格(¥)'].dropna()
        print(f"\n💰 价格统计:")
        print(f"   最低: ¥{prices.min():.0f}")
        print(f"   最高: ¥{prices.max():.0f}")
        print(f"   平均: ¥{prices.mean():.0f}")


if __name__ == "__main__":
    asyncio.run(collect_full_data())
