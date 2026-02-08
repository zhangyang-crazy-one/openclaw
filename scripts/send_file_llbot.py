#!/usr/bin/env python3
"""
发送文件到QQ（通过 llbot HTTP API）
"""
import sys
import os
import subprocess
import threading
import http.server
import socketserver
import socket
import json
from pathlib import Path

# llbot HTTP API 地址
LLBOT_API = "http://127.0.0.1:3006"

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_http_server(port: int, directory: str):
    """启动临时HTTP服务器"""
    os.chdir(directory)
    try:
        with socketserver.TCPServer(("", port), QuietHTTPHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"HTTP server error: {e}")

def send_via_llbot_api(target: str, message: str) -> bool:
    """通过 llbot HTTP API 发送消息"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{LLBOT_API}/send_msg",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "user_id": target if target.isdigit() else None,
                "group_id": target if not target.isdigit() else None,
                "message": message
            }, ensure_ascii=False)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "ok":
                msg_id = data.get("data", {}).get("message_id", 0)
                print(f"✅ 消息已发送! ID: {msg_id}")
                return True
        
        print(f"❌ 发送失败: {result.stderr or result.stdout}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def send_file_via_llbot(target: str, file_path: str, port: int = 8888, caption: str = ""):
    """发送文件到QQ（通过HTTP URL + llbot API）"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    directory = os.path.dirname(file_path) or "."
    
    # 获取本机IP
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"
    
    # 启动HTTP服务器
    print(f"📡 启动HTTP服务器 (端口 {port})...")
    server_thread = threading.Thread(
        target=start_http_server,
        args=(port, directory),
        daemon=True
    )
    server_thread.start()
    
    import time
    time.sleep(1)
    
    # 构建URL
    file_url = f"http://{local_ip}:{port}/{file_name}"
    
    # 构建消息
    message = f"📎 {file_name}\n"
    message += f"📊 大小: {file_size:,} bytes\n"
    message += f"🔗 {file_url}\n"
    if caption:
        message += f"\n{caption}"
    
    print(f"📤 通过 llbot API 发送...")
    
    # 发送消息
    success = send_via_llbot_api(target, message)
    
    if success:
        print(f"\n💡 HTTP服务器仍在运行 (端口 {port})")
        print(f"   按 Ctrl+C 停止服务器")
    
    return success

def main():
    if len(sys.argv) < 3:
        print("用法: python3 send_file_llbot.py <target> <file_path> [port] [caption]")
        print()
        print("示例:")
        print("  python3 send_file_llbot.py 740884666 /home/liujerry/金融数据/stocks/600519.csv 8888")
        print("  python3 send_file_llbot.py 740884666 /home/liujerry/图片/test.jpg 8888 图片")
        sys.exit(1)
    
    target = sys.argv[1]
    file_path = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8888
    caption = sys.argv[4] if len(sys.argv) > 4 else ""
    
    success = send_file_via_llbot(target, file_path, port, caption)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
