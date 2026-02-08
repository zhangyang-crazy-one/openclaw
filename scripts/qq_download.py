#!/usr/bin/env python3
"""
从文本中提取并下载QQ图片
"""
import sys
import re
import os
import subprocess
from pathlib import Path
from datetime import datetime

def extract_qq_image_urls(text: str) -> list:
    """从文本中提取QQ图片URL"""
    # QQ图片下载链接模式
    patterns = [
        r'https://multimedia\.nt\.qq\.com\.cn/download\?[^"\s]+',
        r'https://[^"\s]*\.nt\.qq\.com\.cn[^"\s]*',
        r'https://[^"\s]*fileapi[^"\s]*',
    ]
    
    urls = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        urls.extend(found)
    
    # 去重
    return list(set(urls))


def download_qq_image(url: str, save_dir: str = "/home/liujerry/图片/qq") -> str:
    """下载QQ图片"""
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"qq_{timestamp}.jpg"
    save_path = os.path.join(save_dir, filename)
    
    print(f"📥 下载: {url[:60]}...")
    print(f"   → {save_path}")
    
    result = subprocess.run(
        ["curl", "-L", "-o", save_path, url],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and os.path.exists(save_path):
        size = os.path.getsize(save_path)
        print(f"   ✅ {size:,} bytes")
        return save_path
    
    print(f"   ❌ 下载失败")
    return ""


def process_qq_message(text: str, target: str = "740884666"):
    """处理QQ消息中的图片"""
    urls = extract_qq_image_urls(text)
    
    if not urls:
        print("❌ 未找到QQ图片URL")
        return []
    
    print(f"📊 找到 {len(urls)} 个图片URL")
    
    saved = []
    for url in urls:
        save_path = download_qq_image(url)
        if save_path:
            saved.append(save_path)
    
    if saved:
        # 发送通知
        message = f"📥 已下载 {len(saved)} 张图片\n"
        for path in saved:
            message += f"📁 {os.path.basename(path)}\n"
        
        openclaw_cmd = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"
        subprocess.run(
            [openclaw_cmd, "message", "send", "--target", target, "--message", message],
            capture_output=True,
            text=True
        )
        print("\n✅ 通知已发送")
    
    return saved


def main():
    if len(sys.argv) > 1:
        # 从参数读取
        text = " ".join(sys.argv[1:])
    else:
        # 从标准输入读取
        text = sys.stdin.read()
    
    if not text:
        print("用法: python3 qq_download.py <消息文本>")
        print("或: echo '<消息>' | python3 qq_download.py")
        print("")
        print("示例:")
        print("  qq_download.py 'Attachment: https://multimedia.nt.qq.com.cn/...'")
        echo "https://multimedia.nt.qq.com.cn/download?..." | qq_download.py
        sys.exit(1)
    
    process_qq_message(text)


if __name__ == "__main__":
    main()
