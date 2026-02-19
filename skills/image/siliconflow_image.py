#!/usr/bin/env python3
"""
硅基流动图像生成技能
免费API: 100积分/天
模型: FLUX.1-schnell
"""
import requests
import os
from pathlib import Path

API_KEY = "sk-woldpaxrysndanfnlwqshegwtazopisynfwpgbmewijhevyu"
OUTPUT_DIR = Path.home() / ".logs" / "images"

def generate_image(prompt: str, model: str = "black-forest-labs/FLUX.1-schnell") -> str:
    """
    生成图像
    
    Args:
        prompt: 图像描述
        model: 模型名称
    
    Returns:
        生成的图片路径
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    url = "https://api.siliconflow.cn/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "image_size": "1024x1024",
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    
    if resp.status_code != 200:
        raise Exception(f"API错误: {resp.text}")
    
    data = resp.json()
    image_url = data['images'][0]['url']
    
    # 下载图片
    img_resp = requests.get(image_url, timeout=60)
    
    # 保存
    import time
    filename = f"img_{int(time.time())}.png"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "wb") as f:
        f.write(img_resp.content)
    
    return str(filepath)

def generate_image_simple(prompt: str) -> str:
    """简单版本"""
    return generate_image(prompt)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "A cute orange cat sitting on a sofa, photorealistic"
    
    print(f"生成图像: {prompt}")
    filepath = generate_image(prompt)
    print(f"✅ 已保存: {filepath}")
    print(f"   大小: {os.path.getsize(filepath)} bytes")
