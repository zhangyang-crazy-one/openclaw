#!/usr/bin/env python3
"""
淘宝 32G 服务器内存 - 详情页采集器

策略：
1. 获取商品链接
2. 进入每个商品详情页
3. 获取准确的 32G 价格
4. 目标：采集100个准确价格
"""

import asyncio
import json
import re
import pandas as pd
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def collect_detail_pages():
    print("=" * 80)
    print("💰 淘宝 32G 服务器内存 - 详情页精准采集")
    print("=" * 80)
    print("\n目标: 进入详情页获取准确的32G价格\n")
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开\n")
    
    # 1. 访问淘宝搜索
    print("🔄 Step 1: 访问淘宝搜索...")
    search_url = "https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall&sort=price-asc"
    await browser.navigate(search_url)
    await asyncio.sleep(5)
    print(f"   ✅ {browser.page.url}\n")
    
    # 2. 滚动加载更多
    print("🔄 Step 2: 滚动加载更多商品...")
    for i in range(8):
        await browser.page.evaluate("window.scrollBy(0, 700)")
        await asyncio.sleep(0.5)
        print(f"   滚动 {i+1}/8")
    
    await asyncio.sleep(3)
    
    # 3. 获取所有商品链接
    print("\n🔄 Step 3: 获取商品链接...")
    
    all_links = await browser.page.evaluate("""
        () => {
            const links = [];
            document.querySelectorAll('a[href*="taobao.com/item"]').forEach(a => {
                const href = a.href;
                if (href.includes('taobao.com/item') && !links.find(l => l === href)) {
                    links.push(href);
                }
            });
            return links.slice(0, 30);  // 最多30个
        }
    """)
    
    print(f"   📊 找到 {len(all_links)} 个商品链接\n")
    
    # 4. 进入每个详情页获取准确价格
    print("🔄 Step 4: 进入详情页获取准确价格...")
    
    accurate_products = []
    
    for i, link in enumerate(all_links[:20]):  # 先采集20个
        try:
            print(f"   [{i+1}/{min(len(all_links), 20)}] 访问详情页...")
            
            await browser.page.goto(link, timeout=20000)
            await asyncio.sleep(4)  # 等待页面完全加载
            
            # 获取页面数据
            page_data = await browser.page.evaluate("""
                () => {
                    const data = {
                        title: '',
                        prices: [],
                        shop: '',
                        url: window.location.href
                    };
                    
                    // 获取页面所有文本
                    const text = document.body.innerText;
                    
                    // 提取价格
                    const priceMatches = text.match(/[¥￥]s*([d,.]+)/g);
                    if (priceMatches) {
                        data.prices = priceMatches.map(p => p.replace(/[¥￥s]/g, '')).slice(0, 20);
                    }
                    
                    // 提取标题
                    const titleMatch = text.match(/([A-Za-z0-9u4e00-u9fa5]{10,100}32G[A-Za-z0-9u4e00-u9fa5]{10,100})/);
                    if (titleMatch) {
                        data.title = titleMatch[1].trim();
                    }
                    
                    // 店铺
                    const shopMatch = text.match(/(旗舰店|专营店|专卖店|企业店)/);
                    if (shopMatch) {
                        data.shop = shopMatch[1];
                    }
                    
                    return data;
                }
            """)
            
            title = page_data.get('title', '')[:50] or '未识别标题'
            print(f"      标题: {title}...")
            
            # 提取32G价格
            prices = page_data.get('prices', [])
            price_32g = ''
            
            for price in prices:
                try:
                    p = float(price.replace(',', ''))
                    if 100 < p < 10000:  # 合理价格范围
                        price_32g = str(p)
                        break
                except:
                    pass
            
            if price_32g:
                accurate_products.append({
                    '商品名称': page_data.get('title', '')[:80],
                    '价格(¥)': price_32g,
                    '店铺': page_data.get('shop', '')[:30],
                    '规格': '',
                    '链接': link,
                    '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"      ✅ 价格: ¥{price_32g}")
            else:
                print(f"      ⚠️ 未找到合理价格 (prices: {prices[:3]})")
            
            # 返回搜索页
            await browser.navigate(search_url)
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"      ❌ 错误: {str(e)[:50]}")
    
    # 5. 保存结果
    print("\n" + "=" * 80)
    print("📊 采集完成!")
    print("=" * 80)
    
    if accurate_products:
        df = pd.DataFrame(accurate_products)
        
        # 清洗价格
        def parse_price(p):
            try:
                return float(str(p).replace(',', ''))
            except:
                return 0
        
        df['价格数值'] = df['价格(¥)'].apply(parse_price)
        df = df[df['价格数值'] > 100]
        df = df[df['价格数值'] < 10000]
        df = df.drop('价格数值', axis=1)
        df = df.sort_values('价格(¥)', key=lambda x: x.apply(parse_price))
        
        excel_path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_detail_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print(f"\n✅ 保存 {len(df)} 个商品到:")
        print(f"   {excel_path}")
        
        prices = df['价格(¥)'].apply(parse_price)
        print(f"\n💰 价格统计:")
        print(f"   最低: ¥{prices.min():.0f}")
        print(f"   最高: ¥{prices.max():.0f}")
        print(f"   平均: ¥{prices.mean():.0f}")
        print(f"   中位数: ¥{prices.median():.0f}")
        
        print(f"\n📋 商品列表:")
        for i, row in df.head(20).iterrows():
            price = parse_price(row['价格(¥)'])
            print(f"   {i+1}. ¥{price:5.0f}  {row['商品名称'][:40]}...")
    else:
        print("\n⚠️ 未采集到有效商品")
    
    await browser.save_session()
    await browser.close()


if __name__ == "__main__":
    asyncio.run(collect_detail_pages())
