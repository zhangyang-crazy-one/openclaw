#!/usr/bin/env python3
"""
发送本地文件到QQ
"""
import sys
import os
import subprocess
from pathlib import Path

def send_file_to_qq(target: str, file_path: str, caption: str = ""):
    """发送本地文件到QQ"""
    
    # 验证文件存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 获取文件信息
    ext = Path(file_path).suffix.lower()
    
    # 确定媒体类型
    image_ext = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
    audio_ext = {'.mp3', '.wav', '.ogg', '.flac', '.silk', '.m4a'}
    video_ext = {'.mp4', '.mov', '.webm', '.mkv', '.avi'}
    
    if ext in image_ext:
        media_type = "image"
    elif ext in audio_ext:
        media_type = "record"
    elif ext in video_ext:
        media_type = "video"
    else:
        media_type = "file"
    
    # 构建消息
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    message = f"📎 {file_name}\n"
    message += f"📊 大小: {file_size:,} bytes\n"
    message += f"📁 类型: {ext}\n"
    if caption:
        message += f"\n{caption}"
    
    print(f"📎 准备发送文件:")
    print(f"   文件: {file_name}")
    print(f"   路径: {file_path}")
    print(f"   大小: {file_size:,} bytes")
    print(f"   类型: {media_type}")
    print(f"   目标: {target}")
    
    # 使用 OpenClaw 发送
    openclaw_cmd = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"
    
    try:
        result = subprocess.run(
            [openclaw_cmd, "message", "send", "--target", target, "--message", message],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ 消息已发送!")
            print(result.stdout)
            return True
        else:
            print(f"\n❌ 发送失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("用法: python3 send_file.py <target> <file_path> [caption]")
        print("示例: python3 send_file.py 740884666 /path/to/file.pdf 报告")
        sys.exit(1)
    
    target = sys.argv[1]
    file_path = sys.argv[2]
    caption = sys.argv[3] if len(sys.argv) > 3 else ""
    
    success = send_file_to_qq(target, file_path, caption)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
