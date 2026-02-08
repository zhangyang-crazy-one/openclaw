#!/usr/bin/env python3
"""
下载QQ图片并保存
"""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def download_qq_image(url: str, save_dir: str = "/home/liujerry/图片/qq") -> str:
    """下载QQ图片"""
    
    # 创建保存目录
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".jpg"  # QQ图片通常是jpg
    filename = f"qq_{timestamp}{ext}"
    save_path = os.path.join(save_dir, filename)
    
    print(f"📥 下载QQ图片...")
    print(f"   URL: {url[:80]}...")
    print(f"   保存到: {save_path}")
    
    # 下载图片
    result = subprocess.run(
        ["curl", "-L", "-o", save_path, url],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # 检查文件
        if os.path.exists(save_path):
            size = os.path.getsize(save_path)
            print(f"\n✅ 下载成功!")
            print(f"   文件: {save_path}")
            print(f"   大小: {size:,} bytes")
            return save_path
        else:
            print(f"\n❌ 文件不存在")
            return ""
    else:
        print(f"\n❌ 下载失败: {result.stderr}")
        return ""


def download_and_forward(url: str, target: str = "740884666"):
    """下载QQ图片并转发"""
    save_path = download_qq_image(url)
    
    if save_path:
        # 发送成功消息
        file_name = os.path.basename(save_path)
        size = os.path.getsize(save_path)
        
        message = f"📥 图片已保存\n📁 {file_name}\n📊 {size:,} bytes\n💾 {save_path}"
        
        # 发送到QQ
        openclaw_cmd = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"
        
        result = subprocess.run(
            [openclaw_cmd, "message", "send", "--target", target, "--message", message],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ 通知已发送!")
        else:
            print(f"\n❌ 通知发送失败: {result.stderr}")
    
    return save_path


def main():
    if len(sys.argv) < 2:
        print("用法: python3 download_qq_image.py <url> [target]")
        print("示例: python3 download_qq_image.py 'https://multimedia.nt.qq.com.cn/...'")
        sys.exit(1)
    
    url = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "740884666"
    
    save_path = download_and_forward(url, target)


if __name__ == "__main__":
    main()
