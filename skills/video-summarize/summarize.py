#!/usr/bin/env python3
"""
视频内容总结工具 - 使用 Minimax API
支持：Bilibili, YouTube, 网页视频
"""
import requests
import json
import os
import sys
import re
from pathlib import Path

# API 配置
API_KEY = "sk-cp-20ztK_oBN7-yN5bpTFfKzQ2SY7Ov8mhsy4Urg2yZArcPECfwI8_3TaSdtbIJXHCDcCQbdvwt_j6hsGTPzJHgOr_dFYCqWesrQ-d1Z5pGANr5w7S_PUqKPuw"
BASE_URL = "https://api.minimaxi.com/anthropic/v1/messages"

def extract_video_info(url):
    """从URL提取视频信息"""
    # B站视频
    if 'bilibili.com' in url or 'b23.tv' in url:
        return extract_bilibili(url)
    # YouTube
    elif 'youtube.com' in url or 'youtu.be' in url:
        return extract_youtube(url)
    else:
        return {"title": "网页视频", "up": "未知", "desc": "通用网页视频内容"}

def extract_bilibili(url):
    """提取B站视频信息"""
    # 获取重定向后的URL
    try:
        resp = requests.head(url, allow_redirects=True, timeout=10)
        real_url = resp.url
    except:
        real_url = url
    
    # 提取BV号
    bv_match = re.search(r'BV\w+', real_url)
    if not bv_match:
        return {"title": "B站视频", "up": "未知", "desc": "无法获取视频信息"}
    
    bv_id = bv_match.group()
    
    # 调用B站API
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        api_resp = requests.get(api_url, headers=headers, timeout=10)
        data = api_resp.json()
        
        if data.get('code') == 0:
            info = data['data']
            return {
                "title": info.get('title', '未知'),
                "up": info.get('owner', {}).get('name', '未知'),
                "desc": info.get('desc', '无')[:500]
            }
    except Exception as e:
        print(f"Warning: 获取B站信息失败: {e}")
    
    return {"title": "B站视频", "up": "未知", "desc": "获取信息失败"}

def extract_youtube(url):
    """提取YouTube视频信息"""
    # 提取视频ID
    match = re.search(r'(?:v=|youtu\.be/)([\w-]+)', url)
    video_id = match.group(1) if match else "未知"
    
    return {
        "title": "YouTube视频",
        "up": "YouTube创作者",
        "desc": f"视频ID: {video_id}"
    }

def summarize_video(url):
    """总结视频内容"""
    
    # 获取视频信息
    info = extract_video_info(url)
    
    print(f"视频标题: {info.get('title')}")
    print(f"UP主: {info.get('up')}")
    print(f"简介: {info.get('desc', '无')[:100]}...")
    print()
    
    # 构建提示词
    prompt = f"""你是一个专业的视频内容总结助手。请用简洁易懂的语言总结以下视频的主要内容，
包括：
1. 视频主题（一句话概括）
2. 主要内容/步骤（2-3点）
3. 适合谁观看
4. 有什么亮点或价值

请用中文回复，300字以内。"""

    content = f"""视频标题: {info.get('title', '未知')}
UP主/作者: {info.get('up', '未知')}
简介: {info.get('desc', '无')}

请根据以上信息总结视频内容。"""

    # 调用 API
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "MiniMax-M2.5",
        "max_tokens": 600,
        "messages": [{"role": "user", "content": f"{prompt}\n\n{content}"}]
    }
    
    try:
        resp = requests.post(BASE_URL, headers=headers, json=data, timeout=60)
        result = resp.json()
        
        if 'content' in result:
            for c in result['content']:
                if c.get('type') == 'text':
                    return c['text']
        return f"Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <video_url>")
        print("Example: python summarize.py https://b23.tv/xxx")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("="*50)
    print("🎬 视频内容总结")
    print("="*50)
    print(f"URL: {url}")
    print()
    
    result = summarize_video(url)
    print("="*50)
    print("总结结果:")
    print("="*50)
    print(result)

if __name__ == "__main__":
    main()
