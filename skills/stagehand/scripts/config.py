#!/usr/bin/env python3
"""
MiniMax API Key 配置工具

支持从多个来源读取配置:
1. 环境变量
2. ~/.minimax_config 文件
3. 交互式输入
"""

import os
import json
from pathlib import Path


def get_api_config():
    """获取 MiniMax API 配置."""
    
    # 1. 优先从环境变量读取
    api_key = os.getenv("MINIMAX_API_KEY")
    api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")
    
    if api_key:
        return {"api_key": api_key, "api_base": api_base, "source": "env"}
    
    # 2. 从配置文件读取
    config_file = Path.home() / ".minimax_config"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if config.get("api_key"):
                    return {
                        "api_key": config["api_key"],
                        "api_base": config.get("api_base", "https://api.minimaxi.com/v1"),
                        "source": "file"
                    }
        except Exception:
            pass
    
    # 3. 提示用户输入
    print("未找到 MiniMax API 配置")
    print("\n请选择配置方式:")
    print("1. 输入 API Key")
    print("2. 创建配置文件")
    
    choice = input("选择 (1/2): ").strip()
    
    if choice == "1":
        api_key = input("输入 MiniMax API Key: ").strip()
        if api_key:
            return {"api_key": api_key, "api_base": api_base, "source": "input"}
    elif choice == "2":
        api_key = input("输入 MiniMax API Key: ").strip()
        if api_key:
            config_file.write_text(json.dumps({"api_key": api_key, "api_base": api_base}, indent=2))
            print(f"✅ 配置已保存到 {config_file}")
            return {"api_key": api_key, "api_base": api_base, "source": "file_created"}
    
    return None


def save_api_key(api_key: str, api_base: str = "https://api.minimaxi.com/v1"):
    """保存 API Key 到配置文件."""
    config_file = Path.home() / ".minimax_config"
    
    config = {
        "api_key": api_key,
        "api_base": api_base
    }
    
    config_file.write_text(json.dumps(config, indent=2))
    print(f"✅ API Key 已保存到 {config_file}")
    return config


if __name__ == "__main__":
    print("=== MiniMax API 配置工具 ===\n")
    
    config = get_api_config()
    
    if config:
        print(f"\n✅ 配置来源: {config['source']}")
        print(f"API Key: {config['api_key'][:15]}...")
        print(f"API Base: {config['api_base']}")
    else:
        print("\n❌ 无法获取配置")
