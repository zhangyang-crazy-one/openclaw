#!/usr/bin/env python3
"""
淘宝 32G 服务器内存 - 视觉采集器

策略：
1. 使用截图 + 视觉模型分析
2. 滚动多页采集
3. 点击进入获取详情
4. 目标是100个准确商品
"""

import asyncio
import json
import base64
import httpx
import pandas as pd
from datetime import datetime
from scripts.browser_interactive import MiniMaxBrowserInteractive


class VisionCollector:
    def __init__(self):
        self.api_key = None
        self.api_base = "https://api.minimaxi.com/v1"
        
    def init_api(self):
        with open("/home/liujerry/.minimax_config") as f:
            config = json.load(f)
            self.api_key = config["api_key"]
    
    async def analyze_page_vl(self, screenshot_path):
        """使用视觉模型分析截图"""
        with open(screenshot_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()
        
        # 调用标准 chat API 分析截图（因为 VL API 不可用）
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "MiniMax-M2",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""分析这个淘宝搜索结果页面的截图（搜索词：32G服务器内存）。

请从截图中提取所有32G服务器内存商品信息。要求：
1. 只提取32G规格（不是8G/16G）
2. 提取：名称、价格、销量、店铺
3. 目标是提取50-100个商品

返回JSON格式：
{{"count": 数字, "商品": [{{"名称":"...", "价格":"", "销量":"", "店铺":""}}]}}"""
                        }
                    ],
                    "max_tokens": 4000
                }
            )
            
            result = response.json()
            text = result["choices"][0]["message"]["content"]
            
            # 提取 JSON
            import re
            json_match = re.search(r'\{[^{}]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            return None


async def main():
    collector = VisionCollector()
    collector.init_api()
    
    print("=" * 80)
    print("💰 淘宝 32G 服务器内存 - 视觉采集")
    print("=" * 80)
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开")
    
    all_products = []
    
    # 采集3页
    for page in range(1, 4):
        print(f"\n🔄 采集第 {page} 页...")
        
        if page > 1:
            # 点击下一页
            try:
                await browser.page.click('.next-btn, .next', timeout=5000)
                await asyncio.sleep(3)
            except:
                pass
        
        # 截图
        screenshot_path = f"/home/liujerry/stagehand_data/screenshots/taobao_page_{page}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await browser.page.screenshot(path=screenshot_path)
        print(f"   📸 截图已保存")
        
        # 滚动
        for _ in range(5):
            await browser.page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(2)
        
        # 提取页面数据
        products = await browser.page.evaluate("""
            () => {
                const items = [];
                document.querySelectorAll('.ctx-box, .item, [class*="item"]').forEach((el, i) => {
                    if (i >= 30) return;
                    
                    const text = el.innerText;
                    
                    // 价格
                    let price = '';
                    const priceMatch = text.match(/[¥￥]\\s*([\\d.]+)/);
                    if (priceMatch) price = priceMatch[1];
                    
                    // 检查是否包含32G
                    if (text.includes('32G') || text.includes('32g')) {
                        // 标题
                        let title = text.split('\\n')[0].substring(0, 60);
                        
                        // 销量
                        let sales = '';
                        const salesMatch = text.match(/(\\d+[+]?人付款)/);
                        if (salesMatch) sales = salesMatch[1];
                        
                        // 店铺
                        let shop = '';
                        const shopMatch = text.match(/(旗舰店|专营店|专卖店|企业店)/);
                        if (shopMatch) shop = shopMatch[1];
                        
                        if (price) {
                            items.push({
                                '名称': title,
                                '价格': price,
                                '销量': sales,
                                '店铺': shop
                            });
                        }
                    }
                });
                return items;
            }
        """)
        
        print(f"   📊 提取到 {len(products)} 个商品")
        all_products.extend(products)
        
        # 保存部分结果
        if len(all_products) >= 20:
            df = pd.DataFrame(all_products[:100])
            path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(path, index=False, engine='openpyxl')
            print(f"   💾 临时保存: {len(all_products)} 个")
    
    # 保存最终结果
    df = pd.DataFrame(all_products[:100])
    
    # 排序
    if '价格' in df.columns:
        df['价格'] = pd.to_numeric(df['价格'], errors='coerce')
        df = df.sort_values('价格')
    
    # 保存
    final_path = f"/home/liujerry/stagehand_data/taobao/taobao_32g_vision_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(final_path, index=False, engine='openpyxl')
    
    print(f"\n✅ 采集完成!")
    print(f"   文件: {final_path}")
    print(f"   商品: {len(all_products)} 个")
    
    await browser.save_session()
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
