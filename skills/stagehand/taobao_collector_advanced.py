#!/usr/bin/env python3
"""
淘宝 32G 服务器内存采集器 - 高级版

应对反爬虫策略:
1. 等待页面完全渲染
2. 监听网络请求获取 API 数据
3. 截图 + OCR 识别备用
"""

import asyncio
import json
import re
import base64
from datetime import datetime
from PIL import Image
import pytesseract
from scripts.browser_interactive import MiniMaxBrowserInteractive


async def collect_taobao_advanced():
    print("=" * 80)
    print("💰 淘宝 32G 服务器内存采集器 - 高级版")
    print("=" * 80)
    
    browser = MiniMaxBrowserInteractive(headless=False, session_name="main")
    await browser.initialize(load_cookies=True)
    print("✅ 浏览器已打开")
    
    # 策略1: 等待页面渲染
    print("\n🔄 策略1: 等待页面完全渲染...")
    search_url = "https://s.taobao.com/search?q=32G%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%86%85%E5%AD%98&tab=mall"
    await browser.navigate(search_url)
    
    # 等待内容加载
    await asyncio.sleep(10)  # 等待更长时间
    
    # 策略2: 监听网络请求
    print("\n🔄 策略2: 监听网络请求...")
    
    # 获取页面内容
    page_html = await browser.page.content()
    
    # 查找 API URL 模式
    api_patterns = [
        r'"api":"([^"]+item_detail[^"]+)"',
        r'"url":"([^"]+taobao[^"]+json[^"]+)"',
    ]
    
    api_urls = []
    for pattern in api_patterns:
        matches = re.findall(pattern, page_html)
        api_urls.extend(matches)
    
    print(f"   发现 {len(api_urls)} 个 API URL")
    
    # 策略3: 提取动态内容
    print("\n🔄 策略3: 提取动态渲染内容...")
    
    # 执行页面 JS 获取渲染后的数据
    dynamic_data = await browser.page.evaluate("""
        () => {
            // 尝试获取淘宝商品数据
            const data = [];
            
            // 方法1: 查找全局变量
            if (window.data) {
                try {
                    data.push(...JSON.parse(JSON.stringify(window.data)));
                } catch(e) {}
            }
            
            // 方法2: 查找商品容器
            const items = document.querySelectorAll('.item, .ctx-box, .grid-item, [class*="item"]');
            
            items.forEach((el, i) => {
                if (i >= 20) return;
                
                const text = el.innerText;
                if (text.length > 50) {
                    data.push({
                        index: i,
                        text: text.substring(0, 300)
                    });
                }
            });
            
            // 方法3: 查找价格
            const prices = [];
            document.querySelectorAll('[class*="price"], [class*="Price"]').forEach(el => {
                const text = el.innerText;
                if (/[¥￥]/.test(text)) {
                    prices.push(text.substring(0, 20));
                }
            });
            
            return {
                items: data.slice(0, 15),
                prices: [...new Set(prices)].slice(0, 20),
                rawHtml: document.body.innerText.substring(0, 5000)
            };
        }
    """)
    
    print(f"   提取到 {len(dynamic_data.get('items', []))} 个元素")
    print(f"   发现 {len(dynamic_data.get('prices', []))} 个价格")
    
    # 策略4: 截图 + OCR
    print("\n🔄 策略4: OCR 识别价格...")
    
    screenshot_path = f"~/stagehand_data/screenshots/taobao_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await browser.page.screenshot(path=screenshot_path, full_page=True)
    print(f"   📸 截图已保存")
    
    # 尝试 OCR
    try:
        img = Image.open(screenshot_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        
        # 提取价格
        price_pattern = r'[¥￥]?\s*(\d{2,4}[,.]\d{2}?)'
        prices = re.findall(price_pattern, text)
        
        # 过滤合理价格 (32G内存通常 100-2000元)
        valid_prices = [float(p.replace(',', '.')) for p in prices if 50 < float(p.replace(',', '.')) < 5000]
        
        print(f"   🔍 OCR 识别到 {len(valid_prices)} 个有效价格")
        
        # 统计价格分布
        if valid_prices:
            print(f"\n   💰 价格分布:")
            print(f"      最低: ¥{min(valid_prices):.0f}")
            print(f"      最高: ¥{max(valid_prices):.0f}")
            print(f"      平均: ¥{sum(valid_prices)/len(valid_prices):.0f}")
            
    except Exception as e:
        print(f"   ⚠️ OCR 失败: {str(e)[:50]}")
        valid_prices = []
    
    # 保存结果
    print("\n💾 保存结果...")
    result = {
        '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '搜索关键词': '32G 服务器内存',
        'URL': search_url,
        '价格列表': valid_prices[:30],
        '价格分布': {
            '最低': min(valid_prices) if valid_prices else None,
            '最高': max(valid_prices) if valid_prices else None,
            '平均': sum(valid_prices)/len(valid_prices) if valid_prices else None,
        },
        '动态数据': dynamic_data,
        'API_URLs': api_urls[:5],
        '截图': screenshot_path
    }
    
    result_path = f"~/stagehand_data/taobao/taobao_32g_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 结果已保存: {result_path}")
    
    # 生成简单报告
    print(f"\n" + "=" * 80)
    print("📊 采集报告")
    print("=" * 80)
    print(f"\n✅ 页面访问: 成功")
    print(f"📸 截图: {screenshot_path}")
    print(f"💰 价格样本: {len(valid_prices)} 个")
    
    if valid_prices:
        print(f"\n💵 价格区间:")
        print(f"   ¥{min(valid_prices):.0f} - ¥{max(valid_prices):.0f}")
        print(f"\n📋 部分价格:")
        for p in sorted(valid_prices)[:10]:
            print(f"   ¥{p:.0f}")
    
    await browser.save_session()
    await browser.close()
    
    return result


if __name__ == "__main__":
    asyncio.run(collect_taobao_advanced())
