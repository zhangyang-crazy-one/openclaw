#!/usr/bin/env python3
"""
淘宝 32G 服务器内存 - 点击采集器

只采集：有完整标题 + 有准确价格 的商品
"""

import asyncio
import pandas as pd
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def click_collect():
    print("=" * 80)
    print("💰 淘宝 32G 服务器内存 - 精准采集")
    print("=" * 80)
    print("\n策略: 只提取有完整标题和准确价格的商品\n")
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开\n")
    
    # 1. 访问搜索
    await browser.navigate("https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall")
    await asyncio.sleep(5)
    
    # 2. 滚动
    for _ in range(6):
        await browser.page.evaluate("window.scrollBy(0, 600)")
        await asyncio.sleep(0.5)
    
    await asyncio.sleep(2)
    
    # 3. 获取有完整标题的商品
    print("🔍 提取有完整标题的商品...\n")
    
    products = await browser.page.evaluate("""
        () => {
            const items = [];
            document.querySelectorAll('.ctx-box, .item').forEach(el => {
                const text = el.innerText;
                const lines = text.split('\\n').filter(l => l.trim());
                
                // 检查是否有完整标题
                let title = '';
                let price = '';
                let sales = '';
                
                // 找标题 (第一行，通常包含32G)
                for (let i = 0; i < Math.min(lines.length, 5); i++) {
                    const l = lines[i].trim();
                    if (l.length > 15 && l.length < 80 && 
                        (l.includes('32G') || l.includes('32g'))) {
                        title = l;
                        break;
                    }
                }
                
                // 找价格 (通常在标题附近)
                for (let i = 0; i < lines.length; i++) {
                    const match = lines[i].match(/[¥￥]s*([d,.]+)/);
                    if (match && !price) {
                        price = match[1];
                    }
                }
                
                // 找销量
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].includes('人付款')) {
                        sales = lines[i].trim();
                        break;
                    }
                }
                
                // 只有完整标题才提取
                if (title && price && title.includes('32G')) {
                    items.push({ title, price, sales });
                }
            });
            return items.slice(0, 20);
        }
    """)
    
    print(f"📊 找到 {len(products)} 个有完整标题的商品\n")
    
    # 显示结果
    print("📋 商品列表:")
    for i, p in enumerate(products, 1):
        print(f"   {i}. ¥{p['price']} - {p['title'][:40]}... ({p['sales']})")
    
    # 4. 保存
    if products:
        df = pd.DataFrame(products)
        df.columns = ['商品名称', '价格(¥)', '销量']
        df['采集时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 排序
        df['价格数值'] = df['价格(¥)'].apply(lambda x: float(str(x).replace(',', '')))
        df = df.sort_values('价格数值')
        df = df.drop('价格数值', axis=1)
        
        path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_click_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(path, index=False, engine='openpyxl')
        
        print(f"\n✅ 保存 {len(df)} 个商品到:")
        print(f"   {path}")
        
        prices = df['价格(¥)'].apply(lambda x: float(str(x).replace(',', '')))
        print(f"\n💰 价格: ¥{prices.min():.0f} - ¥{prices.max():.0f}")
    
    await browser.save_session()
    await browser.close()


if __name__ == "__main__":
    asyncio.run(click_collect())
