#!/usr/bin/env python3
"""
发送文件到QQ（通过HTTP URL）
"""
import sys
import os
import subprocess
import threading
import http.server
import socketserver
from pathlib import Path

LLBOT_CMD = "/home/liujerry/文档/programs/openclaw/extensions/qq/node_modules/.bin/openclaw"

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 抑制日志

def start_http_server(port: int, directory: str):
    """启动临时HTTP服务器"""
    os.chdir(directory)
    with socketserver.TCPServer(("", port), QuietHTTPHandler) as httpd:
        httpd.serve_forever()

def send_file_via_url(target: str, file_path: str, port: int = 8888, caption: str = ""):
    """发送文件URL到QQ"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    directory = os.path.dirname(file_path) or "."
    
    # 获取本机IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # 启动HTTP服务器（后台线程）
    print(f"📡 启动HTTP服务器...")
    server_thread = threading.Thread(
        target=start_http_server,
        args=(port, directory),
        daemon=True
    )
    server_thread.start()
    
    # 等待服务器启动
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
    
    print(f"📤 发送消息...")
    
    # 发送消息
    result = subprocess.run(
        [LLBOT_CMD, "message", "send", "--target", target, "--message", message],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 消息已发送!")
        print(f"   文件: {file_name}")
        print(f"   URL: {file_url}")
        print(f"\n💡 HTTP服务器仍在运行 (端口 {port})")
        print(f"   按 Ctrl+C 停止")
        return True
    else:
        print(f"❌ 发送失败: {result.stderr}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python3 send_file_http.py <target> <file_path> [port] [caption]")
        print()
        print("示例:")
        print("  python3 send_file_http.py 740884666 /home/liujerry/金融数据/stocks/600519.csv 8888")
        print("  python3 send_file_http.py 740884666 /home/liujerry/图片/qq/test.jpg 8888")
        sys.exit(1)
    
    target = sys.argv[1]
    file_path = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8888
    caption = sys.argv[4] if len(sys.argv) > 4 else ""
    
    success = send_file_via_url(target, file_path, port, caption)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
