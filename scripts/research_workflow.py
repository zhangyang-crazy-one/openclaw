#!/usr/bin/env python3
"""
FARS 研究工作流脚本
统一的入口点
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path("/home/liujerry/moltbot/scripts")


def run_command(cmd: list) -> int:
    """运行命令"""
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(description="FARS研究工作流")
    parser.add_argument("--topic", type=str, default="AI量化投资", help="研究主题")
    parser.add_argument("--full", action="store_true", help="完整研究流程")
    parser.add_argument("--latest", action="store_true", help="使用最新主题")
    parser.add_argument("--count", type=int, default=10, help="假设数量")
    
    args = parser.parse_args()
    
    if args.full:
        # 运行完整FARS系统
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "fars_system.py"),
            "--topic", args.topic,
            "--count", str(args.count)
        ]
        return run_command(cmd)
    else:
        # 运行假设生成
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "hypothesis_generator.py"),
            "--latest",
            "--count", str(args.count),
            "--report"
        ]
        return run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())
