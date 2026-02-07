#!/usr/bin/env python3
"""
通过 llbot 发送文件到QQ
需要先启用 llbot 的 HTTP API
"""
import subprocess
import json
import sys
import os

LLBOT_CONFIG_DIR = os.path.expanduser("~/.config/QQ/LLBot")
LLBOT_CONFIG_FILE = os.path.join(LLBOT_CONFIG_DIR, "config.json")


def enable_http_api():
    """启用 llbot HTTP API"""
    print("🔧 启用 llbot HTTP API...")
    
    # 创建配置目录
    os.makedirs(LLBOT_CONFIG_DIR, exist_ok=True)
    
    # 读取默认配置
    default_config = {
        "webui": {"enable": True, "host": "127.0.0.1", "port": 3080},
        "ob11": {
            "enable": True,
            "connect": [
                {
                    "type": "http",
                    "enable": True,  # 启用 HTTP API
                    "host": "127.0.0.1",
                    "port": 3000,
                    "token": "",
                    "reportSelfMessage": False,
                    "reportOfflineMessage": False,
                    "messageFormat": "array",
                    "debug": False
                }
            ]
        },
        "enableLocalFile2Url": False,
        "autoDeleteFile": False,
    }
    
    # 写入配置
    with open(LLBOT_CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"✅ 配置已写入: {LLBOT_CONFIG_FILE}")
    print("⚠️  需要重启 llbot 使配置生效")


def send_via_http(peer_id: str, message: str = "", file_path: str = None):
    """通过 HTTP API 发送消息"""
    url = "http://127.0.0.1:3000/send_msg"
    
    payload = {
        "peer_id": peer_id,
        "message": message,
    }
    
    if file_path:
        payload["file"] = file_path
    
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", url,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True,
        text=True
    )
    
    return result.stdout, result.stderr


def send_via_subcmd(target: str, file_path: str, caption: str = ""):
    """通过子命令发送文件"""
    print(f"📤 通过 llbot 发送文件...")
    print(f"   目标: {target}")
    print(f"   文件: {file_path}")
    
    # 获取文件名
    file_name = os.path.basename(file_path)
    
    # 通过 curl 调用 WebSocket API (如果启用)
    # 或者使用其他方式
    
    return None, None


def main():
    if len(sys.argv) < 3:
        print("用法: python3 llbot_send.py <target> <file_path> [caption]")
        print()
        print("示例:")
        print("  python3 llbot_send.py 740884666 /home/liujerry/金融数据/stocks/600519.csv")
        print()
        print("注意: 需要先启用 llbot HTTP API")
        print("  1. 编辑 ~/.config/QQ/LLBot/config.json")
        print("  2. 设置 ob11.connect.http.enable = true")
        print("  3. 重启 llbot")
        sys.exit(1)
    
    target = sys.argv[1]
    file_path = sys.argv[2]
    caption = sys.argv[3] if len(sys.argv) > 3 else ""
    
    # 检查配置文件
    if not os.path.exists(LLBOT_CONFIG_FILE):
        print(f"⚠️  配置文件不存在: {LLBOT_CONFIG_FILE}")
        enable = input("是否创建配置并启用 HTTP API? (y/n): ")
        if enable.lower() == 'y':
            enable_http_api()
            print("\n⚠️  请重启 llbot 后再试")
            sys.exit(0)
    
    print(f"📁 文件: {file_path}")
    print(f"👤 目标: {target}")
    
    # 尝试发送
    stdout, stderr = send_via_http(target, caption, file_path)
    
    if stdout:
        print(f"\n✅ 发送成功: {stdout}")
    elif stderr:
        print(f"\n❌ 发送失败: {stderr}")
    else:
        print("\n⚠️  HTTP API 未启用或无法连接")
        print("请检查 llbot 配置并重启")


if __name__ == "__main__":
    main()
