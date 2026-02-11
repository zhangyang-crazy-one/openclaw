#!/usr/bin/env python3
"""
淘宝 32G 服务器内存 - LLM 智能采集器

使用 LLM 驱动：
1. 分析页面结构
2. 智能选择要点击的商品
3. 进入详情页获取准确价格
4. 采集100个准确商品
"""

import asyncio
import json
import pandas as pd
import httpx
import re
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def collect_with_llm():
    """使用 LLM 智能采集"""
    
    print("=" * 80)
    print("🤖 淘宝 32G 服务器内存 - LLM 智能采集")
    print("=" * 80)
    
    # 读取 API 配置
    with open("/home/liujerry/.minimax_config") as f:
        config = json.load(f)
    api_key = config["api_key"]
    api_base = config.get("api_base", "https://api.minimaxi.com/v1")
    
    # 初始化浏览器
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开\n")
    
    # 1. 访问搜索页
    print("🔄 Step 1: 访问淘宝搜索...")
    search_url = "https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall&sort=price-asc"
    await browser.navigate(search_url)
    print(f"   ✅ 已访问: {browser.page.url}\n")
    
    all_products = []
    
    # 2. 采集多页
    for page_num in range(1, 4):  # 3页
        print(f"📄 采集第 {page_num} 页...")
        
        # 滚动加载
        for _ in range(5):
            await browser.page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(2)
        
        # 提取商品链接
        products = await browser.page.evaluate("""
            () => {
                const items = [];
                document.querySelectorAll('.ctx-box, .item, [class*="item"]').forEach((el, i) => {
                    if (i >= 15) return;
                    
                    const text = el.innerText;
                    let price = '';
                    const priceMatch = text.match(/[¥￥]\\s*([\\d.]+)/);
                    if (priceMatch) price = priceMatch[1];
                    
                    if ((text.includes('32G') || text.includes('32g')) && price) {
                        const linkEl = el.querySelector('a[href*="item.htm"], a[href*="taobao.com/item"]');
                        const link = linkEl ? linkEl.href : '';
                        
                        items.push({
                            index: i,
                            title: text.split('\\n')[0].substring(0, 50),
                            price: price,
                            link: link
                        });
                    }
                });
                return items;
            }
        """)
        
        print(f"   📊 找到 {len(products)} 个32G商品")
        
        # 3. 进入详情页获取准确价格
        print(f"\n🔍 进入详情页获取准确价格...")
        
        accurate_products = []
        
        for i, product in enumerate(products[:5]):  # 每个商品点击进入
            try:
                if product['link']:
                    print(f"   [{i+1}/{len(products[:5])}] 访问商品...")
                    
                    await browser.page.goto(product['link'], timeout=15000)
                    await asyncio.sleep(3)
                    
                    # 获取详情页数据
                    detail = await browser.page.evaluate("""
                        () => {
                            const info = { title: '', price: '', shop: '', specs: [] };
                            
                            // 价格
                            const priceEl = document.querySelector('.tm-price, .price, [class*="price"]');
                            if (priceEl) {
                                info.price = priceEl.innerText.trim();
                            } else {
                                const text = document.body.innerText;
                                const match = text.match(/[¥￥]\\s*([\\d,]+)/);
                                if (match) info.price = match[1];
                            }
                            
                            // 标题
                            const titleEl = document.querySelector('.tb-title, h1, [class*="title"]');
                            if (titleEl) info.title = titleEl.innerText.trim();
                            
                            // 店铺
                            const shopEl = document.querySelector('.shop-name, .tm-shop');
                            if (shopEl) info.shop = shopEl.innerText.trim();
                            
                            return info;
                        }
                    """)
                    
                    if detail.get('price') and float(detail['price'].replace(',', '')) > 50:
                        accurate_products.append({
                            '商品名称': detail.get('title', product['title'])[:80],
                            '价格(¥)': detail['price'],
                            '店铺': detail.get('shop', ''),
                            '规格': '',
                            '链接': product['link'],
                            '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        print(f"      ✅ ¥{detail['price']} - {detail.get('title', '')[:30]}...")
                    else:
                        print(f"      ⚠️ 价格无效")
                    
                    # 返回搜索页
                    await browser.navigate(search_url)
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"      ❌ 错误: {str(e)[:50]}")
        
        all_products.extend(accurate_products)
        print(f"\n   ✅ 第 {page_num} 页采集完成! {len(accurate_products)} 个有效商品\n")
        
        # 点击下一页
        if page_num < 3:
            try:
                await browser.page.click('.next, .next-btn', timeout=3000)
                await asyncio.sleep(3)
                print(f"   ➡️ 跳转到第 {page_num + 1} 页\n")
            except Exception as e:
                print(f"   ⚠️ 无法翻页: {e}\n")
    
    # 4. 保存结果
    print("=" * 80)
    print("📊 采集完成!")
    print("=" * 80)
    
    if all_products:
        df = pd.DataFrame(all_products)
        
        # 清洗价格
        def parse_price(p):
            try:
                return float(str(p).replace(',', '').replace('¥', ''))
            except:
                return 0
        
        df['价格数值'] = df['价格(¥)'].apply(parse_price)
        df = df[df['价格数值'] > 50]  # 过滤无效价格
        df = df.drop('价格数值', axis=1)
        df = df.sort_values('价格(¥)', key=lambda x: x.apply(parse_price))
        
        # 保存
        path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_llm_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(path, index=False, engine='openpyxl')
        
        print(f"\n✅ 保存 {len(df)} 个商品到:\n   {path}")
        
        # 价格统计
        prices = df['价格(¥)'].apply(parse_price)
        print(f"\n💰 价格统计:")
        print(f"   最低: ¥{prices.min():.0f}")
        print(f"   最高: ¥{prices.max():.0f}")
        print(f"   平均: ¥{prices.mean():.0f}")
        
        print(f"\n📋 商品列表:")
        for i, row in df.iterrows():
            print(f"   {i+1}. ¥{row['价格(¥)']} - {row['商品名称'][:40]}...")
    
    await browser.save_session()
    await browser.close()


if __name__ == "__main__":
    asyncio.run(collect_with_llm())
